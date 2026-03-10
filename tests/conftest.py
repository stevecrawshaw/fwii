"""Shared test fixtures."""

import polars as pl
import pytest

from fwii.config import Config


@pytest.fixture
def config() -> Config:
    """Provide a Config instance using default project paths."""
    return Config()


@pytest.fixture
def sample_warnings() -> pl.DataFrame:
    """Minimal warning DataFrame for testing."""
    return pl.DataFrame(
        {
            "fwdCode": [
                "112WAFTBFC",
                "112WAFTBFC",
                "112WAFTBFC",
                "112FWTCLE02",
                "112FWTCLE02",
            ],
            "timeRaised": [
                "2020-02-15T10:00:00",
                "2020-02-15T20:00:00",
                "2020-02-16T06:00:00",
                "2020-03-11T15:00:00",
                "2020-03-11T18:00:00",
            ],
            "severityLevel": [3, 3, 3, 2, 2],
            "severity": [
                "Flood Alert",
                "Flood Alert",
                "Flood Alert",
                "Flood Warning",
                "Flood Warning",
            ],
            "isTidal": [False, False, False, True, True],
        }
    ).with_columns(
        pl.col("timeRaised").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S")
    )
