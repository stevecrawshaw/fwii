"""
Flood Warning Intensity Index (FWII) calculator.

This module calculates normalised indicators and the composite FWII score
based on baseline year (2020) normalisation.
"""

import math
from dataclasses import dataclass

import polars as pl

from .config import Config
from .duration_calculator import DurationCalculator, DurationConfig


@dataclass
class BaselineScores:
    """Baseline scores for normalisation."""

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
    """Normalised flood warning intensity indicators."""

    year: int

    # Raw scores (weighted durations)
    fluvial_score_raw: float
    coastal_score_raw: float
    total_score_raw: float

    # Normalised indicators (baseline year = 100)
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
    Calculate Flood Warning Intensity Index with baseline normalisation.

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
        Initialise indicator calculator.

        Args:
            baseline: Baseline scores for normalisation. If None, will be loaded
                     from config/baseline_2020.yaml
            duration_config: Configuration for duration calculations
            fluvial_weight: Weight for fluvial component in composite (default 0.55)
            coastal_weight: Weight for coastal component in composite (default 0.45)
        """
        if not math.isclose(fluvial_weight + coastal_weight, 1.0):
            raise ValueError(
                f"Weights must sum to 1.0, got {fluvial_weight + coastal_weight}"
            )

        self.config = Config()
        self.duration_calculator = DurationCalculator(duration_config)
        self.fluvial_weight = fluvial_weight
        self.coastal_weight = coastal_weight

        # Load or set baseline
        if baseline is None:
            self.baseline = self.config.baseline
        else:
            self.baseline = baseline

    def save_baseline(self, baseline: BaselineScores) -> None:
        """Save baseline scores to configuration file."""
        self.config.save_baseline(baseline)

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
            ValueError: If baseline is not set when trying to normalise
        """
        # Calculate durations (returns DataFrame with score columns)
        df_with_durations = self.duration_calculator.calculate_durations(df)

        # Calculate annual scores
        scores = self.duration_calculator.calculate_annual_scores(
            df_with_durations, year, separate_tidal=True
        )

        # If no baseline exists, use this year's scores as the baseline
        if self.baseline is None:
            self.baseline = BaselineScores(
                year=year,
                fluvial_score=scores["fluvial_score"],
                coastal_score=scores["coastal_score"],
                total_score=scores["total_score"],
                fluvial_hours=scores["fluvial_hours"],
                coastal_hours=scores["coastal_hours"],
                fluvial_events=scores["fluvial_events"],
                coastal_events=scores["coastal_events"],
            )

        # Normalise against baseline (baseline year will naturally produce 100.0)
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
