"""Tests for data loader: severity mapping and isTidal join."""

import polars as pl
import pytest

from fwii.data_loader import HistoricWarningsLoader


class TestSeverityMapping:
    """Test exact string severity mapping."""

    @pytest.fixture
    def loader(self) -> HistoricWarningsLoader:
        return HistoricWarningsLoader()

    def _make_raw_df(self, severity_values: list[str]) -> pl.DataFrame:
        """Build a raw DataFrame with EA column names."""
        return pl.DataFrame(
            {
                "DATE": ["2020-01-01T10:00:00"] * len(severity_values),
                "CODE": ["112WAFTBFC"] * len(severity_values),
                "TYPE": severity_values,
            }
        )

    def test_severe_flood_warning_maps_to_1(self, loader: HistoricWarningsLoader):
        df = self._make_raw_df(["Severe Flood Warning"])
        result = loader._normalize_schema(df)
        assert result["severityLevel"][0] == 1

    def test_flood_warning_maps_to_2(self, loader: HistoricWarningsLoader):
        df = self._make_raw_df(["Flood Warning"])
        result = loader._normalize_schema(df)
        assert result["severityLevel"][0] == 2

    def test_flood_alert_maps_to_3(self, loader: HistoricWarningsLoader):
        df = self._make_raw_df(["Flood Alert"])
        result = loader._normalize_schema(df)
        assert result["severityLevel"][0] == 3

    def test_no_longer_in_force_maps_to_4(self, loader: HistoricWarningsLoader):
        df = self._make_raw_df(["Warning No Longer in Force"])
        result = loader._normalize_schema(df)
        assert result["severityLevel"][0] == 4

    def test_unknown_severity_maps_to_null(self, loader: HistoricWarningsLoader):
        df = self._make_raw_df(["Something Unknown"])
        result = loader._normalize_schema(df)
        assert result["severityLevel"][0] is None


class TestIsTidalJoin:
    """Test that isTidal is correctly joined during filtering."""

    @pytest.fixture
    def loader(self) -> HistoricWarningsLoader:
        return HistoricWarningsLoader()

    def test_fluvial_area_gets_false(self, loader: HistoricWarningsLoader):
        """Known fluvial area code gets isTidal=False."""
        df = pl.DataFrame(
            {
                "fwdCode": ["112WAFTBFC"],  # Bristol Frome - fluvial
                "severityLevel": [3],
                "timeRaised": ["2020-01-01T10:00:00"],
                "severity": ["Flood Alert"],
            }
        ).with_columns(
            pl.col("timeRaised").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S")
        )

        result = loader._filter_west_of_england(df)
        assert result["isTidal"][0] is False

    def test_coastal_area_gets_true(self, loader: HistoricWarningsLoader):
        """Known coastal area code gets isTidal=True."""
        df = pl.DataFrame(
            {
                "fwdCode": ["112FWTCLE02"],  # Clevedon coast - tidal
                "severityLevel": [2],
                "timeRaised": ["2020-01-01T10:00:00"],
                "severity": ["Flood Warning"],
            }
        ).with_columns(
            pl.col("timeRaised").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S")
        )

        result = loader._filter_west_of_england(df)
        assert result["isTidal"][0] is True

    def test_unknown_area_filtered_out(self, loader: HistoricWarningsLoader):
        """Unknown area codes are filtered out entirely."""
        df = pl.DataFrame(
            {
                "fwdCode": ["999UNKNOWN"],
                "severityLevel": [3],
                "timeRaised": ["2020-01-01T10:00:00"],
                "severity": ["Flood Alert"],
            }
        ).with_columns(
            pl.col("timeRaised").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S")
        )

        result = loader._filter_west_of_england(df)
        assert result.height == 0
