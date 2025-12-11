"""
Flood Warning Intensity Index (FWII) calculator.

This module calculates normalized indicators and the composite FWII score
based on baseline year (2020) normalization.
"""

from dataclasses import dataclass
from pathlib import Path

import polars as pl
import yaml

from .duration_calculator import DurationCalculator, DurationConfig


@dataclass
class BaselineScores:
    """Baseline scores for normalization."""

    year: int
    fluvial_score: float
    coastal_score: float
    total_score: float
    fluvial_hours: float
    coastal_hours: float
    fluvial_events: int
    coastal_events: int


@dataclass
class NormalizedIndicators:
    """Normalized flood warning intensity indicators."""

    year: int

    # Raw scores (weighted durations)
    fluvial_score_raw: float
    coastal_score_raw: float
    total_score_raw: float

    # Normalized indicators (baseline year = 100)
    fluvial_index: float
    coastal_index: float
    composite_fwii: float

    # Supporting metrics
    fluvial_hours: float
    coastal_hours: float
    fluvial_events: int
    coastal_events: int
    total_events: int

    # Severity breakdown
    severe_warnings: int = 0
    flood_warnings: int = 0
    flood_alerts: int = 0


class IndicatorCalculator:
    """
    Calculate Flood Warning Intensity Index with baseline normalization.

    The composite FWII combines fluvial and coastal sub-indicators:
    FWII = (fluvial_index × 0.55) + (coastal_index × 0.45)
    """

    def __init__(
        self,
        baseline: BaselineScores | None = None,
        duration_config: DurationConfig | None = None,
        fluvial_weight: float = 0.55,
        coastal_weight: float = 0.45,
    ):
        """
        Initialize indicator calculator.

        Args:
            baseline: Baseline scores for normalization. If None, will be loaded
                     from config/baseline_2020.yaml
            duration_config: Configuration for duration calculations
            fluvial_weight: Weight for fluvial component in composite (default 0.55)
            coastal_weight: Weight for coastal component in composite (default 0.45)
        """
        if fluvial_weight + coastal_weight != 1.0:
            raise ValueError(
                f"Weights must sum to 1.0, got {fluvial_weight + coastal_weight}"
            )

        self.duration_calculator = DurationCalculator(duration_config)
        self.fluvial_weight = fluvial_weight
        self.coastal_weight = coastal_weight

        # Load or set baseline
        if baseline is None:
            self.baseline = self._load_baseline()
        else:
            self.baseline = baseline

    def _load_baseline(self) -> BaselineScores | None:
        """Load baseline scores from configuration file."""
        baseline_path = (
            Path(__file__).parent.parent.parent / "config" / "baseline_2020.yaml"
        )

        if not baseline_path.exists():
            # No baseline file exists yet
            return None

        with open(baseline_path) as f:
            data = yaml.safe_load(f)

        return BaselineScores(
            year=data["year"],
            fluvial_score=data["fluvial_score"],
            coastal_score=data["coastal_score"],
            total_score=data["total_score"],
            fluvial_hours=data.get("fluvial_hours", 0.0),
            coastal_hours=data.get("coastal_hours", 0.0),
            fluvial_events=data.get("fluvial_events", 0),
            coastal_events=data.get("coastal_events", 0),
        )

    def save_baseline(self, baseline: BaselineScores, output_path: Path | None = None):
        """
        Save baseline scores to configuration file.

        Args:
            baseline: Baseline scores to save
            output_path: Path to save to (default: config/baseline_2020.yaml)
        """
        if output_path is None:
            output_path = (
                Path(__file__).parent.parent.parent / "config" / "baseline_2020.yaml"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "year": baseline.year,
            "fluvial_score": baseline.fluvial_score,
            "coastal_score": baseline.coastal_score,
            "total_score": baseline.total_score,
            "fluvial_hours": baseline.fluvial_hours,
            "coastal_hours": baseline.coastal_hours,
            "fluvial_events": baseline.fluvial_events,
            "coastal_events": baseline.coastal_events,
            "description": f"Baseline scores for {baseline.year} (normalized to 100)",
            "created_at": str(
                Path(__file__).parent.parent.parent / "config" / "baseline_2020.yaml"
            ),
        }

        with open(output_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def calculate_indicators(self, df: pl.DataFrame, year: int) -> NormalizedIndicators:
        """
        Calculate flood warning intensity indicators for a given year.

        Args:
            df: DataFrame with warnings (requires: fwdCode, timeRaised, severityLevel,
                severity, isTidal)
            year: Year to calculate for

        Returns:
            NormalizedIndicators with calculated values

        Raises:
            ValueError: If baseline is not set when trying to normalize
        """
        # Calculate durations
        events = self.duration_calculator.calculate_durations(df)

        # Calculate annual scores
        scores = self.duration_calculator.calculate_annual_scores(
            events, year, separate_tidal=True
        )

        # If this is the baseline year, save it
        if self.baseline is None or year == self.baseline.year:
            baseline = BaselineScores(
                year=year,
                fluvial_score=scores["fluvial_score"],
                coastal_score=scores["coastal_score"],
                total_score=scores["total_score"],
                fluvial_hours=scores["fluvial_hours"],
                coastal_hours=scores["coastal_hours"],
                fluvial_events=scores["fluvial_events"],
                coastal_events=scores["coastal_events"],
            )

            if self.baseline is None:
                self.baseline = baseline

            return NormalizedIndicators(
                year=year,
                fluvial_score_raw=scores["fluvial_score"],
                coastal_score_raw=scores["coastal_score"],
                total_score_raw=scores["total_score"],
                fluvial_index=100.0,
                coastal_index=100.0,
                composite_fwii=100.0,
                fluvial_hours=scores["fluvial_hours"],
                coastal_hours=scores["coastal_hours"],
                fluvial_events=scores["fluvial_events"],
                coastal_events=scores["coastal_events"],
                total_events=scores["total_events"],
                severe_warnings=scores["by_severity"]["total"][1]["count"],
                flood_warnings=scores["by_severity"]["total"][2]["count"],
                flood_alerts=scores["by_severity"]["total"][3]["count"],
            )

        # Normalize against baseline
        if self.baseline is None:
            raise ValueError(
                "Baseline scores not set. Calculate baseline year first or load from config."
            )

        fluvial_index = (
            (scores["fluvial_score"] / self.baseline.fluvial_score) * 100.0
            if self.baseline.fluvial_score > 0
            else 0.0
        )

        coastal_index = (
            (scores["coastal_score"] / self.baseline.coastal_score) * 100.0
            if self.baseline.coastal_score > 0
            else 0.0
        )

        composite_fwii = (
            fluvial_index * self.fluvial_weight + coastal_index * self.coastal_weight
        )

        return NormalizedIndicators(
            year=year,
            fluvial_score_raw=scores["fluvial_score"],
            coastal_score_raw=scores["coastal_score"],
            total_score_raw=scores["total_score"],
            fluvial_index=fluvial_index,
            coastal_index=coastal_index,
            composite_fwii=composite_fwii,
            fluvial_hours=scores["fluvial_hours"],
            coastal_hours=scores["coastal_hours"],
            fluvial_events=scores["fluvial_events"],
            coastal_events=scores["coastal_events"],
            total_events=scores["total_events"],
            severe_warnings=scores["by_severity"]["total"][1]["count"],
            flood_warnings=scores["by_severity"]["total"][2]["count"],
            flood_alerts=scores["by_severity"]["total"][3]["count"],
        )
