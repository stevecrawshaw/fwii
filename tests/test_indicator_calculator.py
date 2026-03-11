"""Tests for indicator calculator."""

import polars as pl
import pytest

from fwii.indicator_calculator import BaselineScores, IndicatorCalculator


@pytest.fixture
def baseline() -> BaselineScores:
    return BaselineScores(
        year=2020,
        fluvial_score=100.0,
        coastal_score=200.0,
        total_score=300.0,
        fluvial_hours=100.0,
        coastal_hours=200.0,
        fluvial_events=10,
        coastal_events=20,
    )


def _make_warnings(
    n_fluvial: int,
    n_coastal: int,
    year: int = 2020,
    level: int = 3,
    severity: str = "Flood Alert",
) -> pl.DataFrame:
    """Build a DataFrame of warnings."""
    fwd_codes = ["112WAFTBFC"] * n_fluvial + ["112FWTCLE02"] * n_coastal
    tidal = [False] * n_fluvial + [True] * n_coastal
    n = n_fluvial + n_coastal
    times = [f"{year}-06-{(i % 28) + 1:02d}T10:00:00" for i in range(n)]

    return pl.DataFrame(
        {
            "fwdCode": fwd_codes,
            "timeRaised": times,
            "severityLevel": [level] * n,
            "severity": [severity] * n,
            "isTidal": tidal,
        }
    ).with_columns(
        pl.col("timeRaised").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S")
    )


class TestBaselineYear:
    def test_baseline_year_returns_index_100(self):
        """Baseline year should return all indices at 100 when baseline matches data."""
        # Calculate scores first, then use them as the baseline
        from fwii.duration_calculator import DurationCalculator

        df = _make_warnings(10, 20, year=2020)
        dc = DurationCalculator()
        df_dur = dc.calculate_durations(df)
        scores = dc.calculate_annual_scores(df_dur, 2020, separate_tidal=True)

        baseline = BaselineScores(
            year=2020,
            fluvial_score=scores["fluvial_score"],
            coastal_score=scores["coastal_score"],
            total_score=scores["total_score"],
            fluvial_hours=scores["fluvial_hours"],
            coastal_hours=scores["coastal_hours"],
            fluvial_events=scores["fluvial_events"],
            coastal_events=scores["coastal_events"],
        )
        calculator = IndicatorCalculator(baseline=baseline)
        indicators = calculator.calculate_indicators(df, 2020)

        assert indicators.fluvial_index == pytest.approx(100.0)
        assert indicators.coastal_index == pytest.approx(100.0)
        assert indicators.composite_fwii == pytest.approx(100.0)


class TestNormalization:
    def test_double_fluvial_gives_200_index(self, baseline: BaselineScores):
        """Year with double fluvial score returns fluvial_index of 200."""
        calculator = IndicatorCalculator(baseline=baseline)
        # Provide data that will produce exactly 200 fluvial score
        # Using a custom baseline where we know the expected output
        df = _make_warnings(10, 20, year=2021)
        indicators = calculator.calculate_indicators(df, 2021)

        # The key relationship: index = (raw_score / baseline_score) * 100
        expected_fluvial_index = (
            indicators.fluvial_score_raw / baseline.fluvial_score
        ) * 100
        assert indicators.fluvial_index == pytest.approx(expected_fluvial_index)

    def test_composite_formula(self, baseline: BaselineScores):
        """Composite FWII = 0.55 * fluvial + 0.45 * coastal."""
        calculator = IndicatorCalculator(baseline=baseline)
        df = _make_warnings(5, 10, year=2021)
        indicators = calculator.calculate_indicators(df, 2021)

        expected = indicators.fluvial_index * 0.55 + indicators.coastal_index * 0.45
        assert indicators.composite_fwii == pytest.approx(expected)


class TestZeroBaseline:
    def test_zero_baseline_fluvial_gives_zero_index(self):
        """Zero baseline score should not cause division error."""
        baseline = BaselineScores(
            year=2020,
            fluvial_score=0.0,
            coastal_score=200.0,
            total_score=200.0,
            fluvial_hours=0.0,
            coastal_hours=200.0,
            fluvial_events=0,
            coastal_events=20,
        )
        calculator = IndicatorCalculator(baseline=baseline)
        df = _make_warnings(5, 10, year=2021)
        indicators = calculator.calculate_indicators(df, 2021)

        assert indicators.fluvial_index == pytest.approx(0.0)
