"""Tests for vectorised duration calculator."""

import polars as pl
import pytest

from fwii.duration_calculator import DurationCalculator


@pytest.fixture
def calculator() -> DurationCalculator:
    return DurationCalculator()


def _make_df(
    fwd_codes: list[str],
    times: list[str],
    levels: list[int],
    severities: list[str],
    tidal: list[bool | None] | None = None,
) -> pl.DataFrame:
    """Helper to build a warning DataFrame."""
    data = {
        "fwdCode": fwd_codes,
        "timeRaised": times,
        "severityLevel": levels,
        "severity": severities,
    }
    if tidal is not None:
        data["isTidal"] = tidal

    return pl.DataFrame(data).with_columns(
        pl.col("timeRaised").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S")
    )


class TestCalculateDurations:
    def test_single_warning_gets_default_duration(self, calculator: DurationCalculator):
        """Single warning with no next warning gets default duration."""
        df = _make_df(
            ["112A"], ["2020-01-01T10:00:00"], [3], ["Flood Alert"]
        )
        result = calculator.calculate_durations(df)
        assert result["duration_hours"][0] == pytest.approx(48.0)

    def test_two_warnings_within_max_gap(self, calculator: DurationCalculator):
        """First warning gets min(gap, default), not full default."""
        df = _make_df(
            ["112A", "112A"],
            ["2020-01-01T10:00:00", "2020-01-01T20:00:00"],
            [3, 3],
            ["Flood Alert", "Flood Alert"],
        )
        result = calculator.calculate_durations(df)
        # Gap is 10 hours, default for Alert is 48h, so min(10, 48) = 10
        assert result["duration_hours"][0] == pytest.approx(10.0)
        # Last warning gets default
        assert result["duration_hours"][1] == pytest.approx(48.0)

    def test_two_warnings_beyond_max_gap(self, calculator: DurationCalculator):
        """First warning gets default duration when gap exceeds max."""
        df = _make_df(
            ["112A", "112A"],
            ["2020-01-01T10:00:00", "2020-01-05T10:00:00"],  # 96h gap
            [3, 3],
            ["Flood Alert", "Flood Alert"],
        )
        result = calculator.calculate_durations(df)
        # Gap is 96h > 72h max, so default 48h
        assert result["duration_hours"][0] == pytest.approx(48.0)

    def test_update_gets_full_gap(self, calculator: DurationCalculator):
        """Update messages get the full gap duration."""
        df = _make_df(
            ["112A", "112A"],
            ["2020-01-01T10:00:00", "2020-01-02T10:00:00"],
            [3, 3],
            ["Flood Alert Update", "Flood Alert"],
        )
        result = calculator.calculate_durations(df)
        # Update: gap is 24h, uses full gap (not min with default)
        assert result["duration_hours"][0] == pytest.approx(24.0)

    def test_level_4_gets_zero_score(self, calculator: DurationCalculator):
        """Level 4 (Warning No Longer in Force) gets weight 0."""
        df = _make_df(
            ["112A"],
            ["2020-01-01T10:00:00"],
            [4],
            ["Warning No Longer in Force"],
        )
        result = calculator.calculate_durations(df)
        assert result["score"][0] == pytest.approx(0.0)

    def test_empty_dataframe(self, calculator: DurationCalculator):
        """Empty DataFrame returns empty result with expected columns."""
        df = pl.DataFrame(
            {
                "fwdCode": [],
                "timeRaised": [],
                "severityLevel": [],
                "severity": [],
            },
            schema={
                "fwdCode": pl.Utf8,
                "timeRaised": pl.Datetime,
                "severityLevel": pl.Int64,
                "severity": pl.Utf8,
            },
        )
        result = calculator.calculate_durations(df)
        assert result.height == 0
        assert "duration_hours" in result.columns
        assert "score" in result.columns

    def test_severity_weights_applied_correctly(self, calculator: DurationCalculator):
        """Verify correct weights for each severity level."""
        df = _make_df(
            ["112A", "112B", "112C"],
            ["2020-01-01T10:00:00", "2020-01-01T10:00:00", "2020-01-01T10:00:00"],
            [1, 2, 3],
            ["Severe Flood Warning", "Flood Warning", "Flood Alert"],
        )
        result = calculator.calculate_durations(df)
        # Level 1: 12h * 3 = 36, Level 2: 24h * 2 = 48, Level 3: 48h * 1 = 48
        scores = result.sort("severityLevel")["score"].to_list()
        assert scores[0] == pytest.approx(36.0)  # Severe
        assert scores[1] == pytest.approx(48.0)  # Warning
        assert scores[2] == pytest.approx(48.0)  # Alert


class TestCalculateAnnualScores:
    def test_separates_fluvial_and_coastal(self, calculator: DurationCalculator):
        """Scores are correctly separated by isTidal."""
        df = _make_df(
            ["112A", "112B"],
            ["2020-01-01T10:00:00", "2020-01-01T10:00:00"],
            [3, 3],
            ["Flood Alert", "Flood Alert"],
            tidal=[False, True],
        )
        result_df = calculator.calculate_durations(df)
        scores = calculator.calculate_annual_scores(result_df, 2020)

        assert scores["fluvial_events"] == 1
        assert scores["coastal_events"] == 1
        assert scores["fluvial_score"] == pytest.approx(48.0)
        assert scores["coastal_score"] == pytest.approx(48.0)

    def test_filters_by_year(self, calculator: DurationCalculator):
        """Only events from the requested year are included."""
        df = _make_df(
            ["112A", "112A"],
            ["2020-01-01T10:00:00", "2021-01-01T10:00:00"],
            [3, 3],
            ["Flood Alert", "Flood Alert"],
        )
        result_df = calculator.calculate_durations(df)
        scores = calculator.calculate_annual_scores(
            result_df, 2020, separate_tidal=False
        )

        assert scores["total_events"] == 1

    def test_severity_breakdown(self, calculator: DurationCalculator):
        """Breakdown by severity is correct."""
        df = _make_df(
            ["112A", "112B"],
            ["2020-01-01T10:00:00", "2020-01-01T10:00:00"],
            [1, 3],
            ["Severe Flood Warning", "Flood Alert"],
        )
        result_df = calculator.calculate_durations(df)
        scores = calculator.calculate_annual_scores(
            result_df, 2020, separate_tidal=False
        )

        assert scores["by_severity"][1]["count"] == 1
        assert scores["by_severity"][3]["count"] == 1
        assert scores["by_severity"][2]["count"] == 0
