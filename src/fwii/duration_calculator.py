"""
Duration calculator for flood warnings (vectorised).

Calculates warning durations using Polars expressions instead of row-by-row
iteration. The heuristic approach is unchanged:

1. Group warnings by fwdCode (warning area)
2. Sort chronologically within each area
3. Calculate duration based on gap to next warning vs default duration
4. Special handling for "Update" messages

Default Durations:
- Severe Flood Warning (level 1): 12 hours
- Flood Warning (level 2): 24 hours
- Flood Alert (level 3): 48 hours

Maximum Gap: 72 hours (treat as separate events if exceeded)
"""

from dataclasses import dataclass

import polars as pl


@dataclass
class DurationConfig:
    """Configuration for duration calculations."""

    default_durations: dict[int, float] = None
    max_gap_hours: float = 72.0
    severity_weights: dict[int, float] = None

    def __post_init__(self):
        if self.default_durations is None:
            self.default_durations = {
                1: 12.0,  # Severe Flood Warning
                2: 24.0,  # Flood Warning
                3: 48.0,  # Flood Alert
                4: 0.0,   # Warning No Longer in Force
            }

        if self.severity_weights is None:
            self.severity_weights = {
                1: 3.0,  # Severe x 3
                2: 2.0,  # Warning x 2
                3: 1.0,  # Alert x 1
                4: 0.0,  # No longer in force x 0
            }


class DurationCalculator:
    """Calculate warning durations from historic flood warning data."""

    def __init__(self, config: DurationConfig | None = None):
        self.config = config or DurationConfig()

    def calculate_durations(self, df: pl.DataFrame) -> pl.DataFrame:
        """Calculate durations for all warnings using vectorised Polars expressions.

        Args:
            df: DataFrame with columns: fwdCode, timeRaised, severityLevel, severity.
                Optional: isTidal.

        Returns:
            DataFrame with added columns: is_update, gap_to_next_hours,
            duration_hours, weight, score.
        """
        if df.height == 0:
            return df.with_columns(
                pl.lit(False).alias("is_update"),
                pl.lit(None, dtype=pl.Float64).alias("gap_to_next_hours"),
                pl.lit(0.0).alias("duration_hours"),
                pl.lit(0.0).alias("weight"),
                pl.lit(0.0).alias("score"),
            )

        required = ["fwdCode", "timeRaised", "severityLevel", "severity"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Sort by area and time
        df = df.sort(["fwdCode", "timeRaised"])

        # Add update flag and gap to next warning
        df = df.with_columns(
            pl.col("severity").str.contains("(?i)update").alias("is_update"),
            (
                (
                    pl.col("timeRaised").shift(-1).over("fwdCode")
                    - pl.col("timeRaised")
                ).dt.total_seconds()
                / 3600.0
            ).alias("gap_to_next_hours"),
        )

        # Map severity level to default duration
        default_dur = pl.col("severityLevel").replace_strict(
            self.config.default_durations,
            default=24.0,
            return_dtype=pl.Float64,
        )

        max_gap = self.config.max_gap_hours

        # Vectorised duration calculation matching the original heuristic:
        # if gap is null -> default_duration
        # elif gap > max_gap -> default_duration
        # elif is_update -> gap
        # else -> min(gap, default_duration)
        duration = (
            pl.when(pl.col("gap_to_next_hours").is_null())
            .then(default_dur)
            .when(pl.col("gap_to_next_hours") > max_gap)
            .then(default_dur)
            .when(pl.col("is_update"))
            .then(pl.col("gap_to_next_hours"))
            .otherwise(pl.min_horizontal("gap_to_next_hours", default_dur))
        )

        # Map severity to weight
        weight = pl.col("severityLevel").replace_strict(
            self.config.severity_weights,
            default=0.0,
            return_dtype=pl.Float64,
        )

        df = df.with_columns(
            duration.alias("duration_hours"),
            weight.alias("weight"),
        )

        df = df.with_columns(
            (pl.col("duration_hours") * pl.col("weight")).alias("score"),
        )

        return df

    def calculate_annual_scores(
        self, df: pl.DataFrame, year: int, separate_tidal: bool = True
    ) -> dict:
        """Calculate annual scores from a DataFrame with duration/score columns.

        Args:
            df: DataFrame from calculate_durations() (must have duration_hours,
                score, weight columns).
            year: Year to calculate for.
            separate_tidal: If True, separate fluvial and coastal scores.

        Returns:
            Dictionary with score breakdown.
        """
        # Filter to year
        year_df = df.filter(pl.col("timeRaised").dt.year() == year)

        has_tidal = "isTidal" in year_df.columns and separate_tidal

        if not has_tidal:
            total_score = year_df["score"].sum()
            return {
                "year": year,
                "total_score": total_score,
                "total_events": len(year_df),
                "total_hours": year_df["duration_hours"].sum(),
                "by_severity": self._breakdown_by_severity(year_df),
            }

        # Separate by tidal status
        fluvial = year_df.filter(pl.col("isTidal") == False)  # noqa: E712
        coastal = year_df.filter(pl.col("isTidal") == True)   # noqa: E712
        other = year_df.filter(pl.col("isTidal").is_null())

        fluvial_score = fluvial["score"].sum()
        coastal_score = coastal["score"].sum()
        other_score = other["score"].sum()

        return {
            "year": year,
            "fluvial_score": fluvial_score,
            "coastal_score": coastal_score,
            "other_score": other_score,
            "total_score": fluvial_score + coastal_score + other_score,
            "fluvial_events": len(fluvial),
            "coastal_events": len(coastal),
            "other_events": len(other),
            "total_events": len(year_df),
            "fluvial_hours": fluvial["duration_hours"].sum(),
            "coastal_hours": coastal["duration_hours"].sum(),
            "other_hours": other["duration_hours"].sum(),
            "by_severity": {
                "fluvial": self._breakdown_by_severity(fluvial),
                "coastal": self._breakdown_by_severity(coastal),
                "other": self._breakdown_by_severity(other),
                "total": self._breakdown_by_severity(year_df),
            },
        }

    def _breakdown_by_severity(self, df: pl.DataFrame) -> dict:
        """Create breakdown of events by severity level."""
        breakdown = {}
        for level in [1, 2, 3]:
            level_df = df.filter(pl.col("severityLevel") == level)
            hours = level_df["duration_hours"].sum() if len(level_df) else 0.0
            score = level_df["score"].sum() if len(level_df) else 0.0
            breakdown[level] = {
                "count": len(level_df),
                "total_hours": hours,
                "weighted_score": score,
            }
        return breakdown
