"""
Duration calculator for flood warnings.

This module handles the complex task of calculating warning durations given that
the Environment Agency historic data does NOT include end times (severity level 4)
for warnings.

Approach:
---------
Since each record represents a warning issuance without explicit end times, we use
the following heuristic approach:

1. Group warnings by fwdCode (warning area)
2. For each area, sort warnings chronologically
3. Calculate duration based on:
   - Time until next warning for same area (if within max_gap)
   - Default duration for that severity level
   - Whichever is SMALLER (to avoid unrealistic long durations)

4. Special handling for "Update" messages:
   - These extend/continue previous warnings
   - Don't start new warning periods

Default Durations (configurable):
---------------------------------
- Severe Flood Warning (level 1): 12 hours
- Flood Warning (level 2): 24 hours
- Flood Alert (level 3): 48 hours

Maximum Gap (configurable):
---------------------------
- If gap between warnings > max_gap (default 72 hours), treat as separate events
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

import polars as pl


@dataclass
class WarningEvent:
    """Represents a single warning event with calculated duration."""

    fwdCode: str
    timeRaised: datetime
    severityLevel: int
    severity: str
    duration_hours: float
    is_update: bool
    isTidal: Optional[bool] = None

    def calculate_score(self, severity_weights: dict[int, float]) -> float:
        """Calculate weighted score for this warning event."""
        weight = severity_weights.get(self.severityLevel, 0.0)
        return self.duration_hours * weight


@dataclass
class DurationConfig:
    """Configuration for duration calculations."""

    # Default durations by severity level (in hours)
    default_durations: dict[int, float] = None

    # Maximum gap between warnings to consider them part of same event
    max_gap_hours: float = 72.0

    # Severity weights for scoring
    severity_weights: dict[int, float] = None

    def __post_init__(self):
        if self.default_durations is None:
            self.default_durations = {
                1: 12.0,  # Severe Flood Warning
                2: 24.0,  # Flood Warning
                3: 48.0,  # Flood Alert
                4: 0.0,   # Warning No Longer in Force (not used)
            }

        if self.severity_weights is None:
            self.severity_weights = {
                1: 3.0,  # Severe × 3
                2: 2.0,  # Warning × 2
                3: 1.0,  # Alert × 1
                4: 0.0,  # No longer in force × 0
            }


class DurationCalculator:
    """Calculate warning durations from historic flood warning data."""

    def __init__(self, config: Optional[DurationConfig] = None):
        """
        Initialize calculator with configuration.

        Args:
            config: Configuration for duration calculations.
                   If None, uses default configuration.
        """
        self.config = config or DurationConfig()

    def calculate_durations(self, df: pl.DataFrame) -> List[WarningEvent]:
        """
        Calculate durations for all warnings in the dataset.

        Args:
            df: Polars DataFrame with columns:
                - fwdCode: Warning area code
                - timeRaised: Timestamp of warning
                - severityLevel: 1=Severe, 2=Warning, 3=Alert, 4=No longer in force
                - severity: Text description
                - isTidal: Boolean (optional)

        Returns:
            List of WarningEvent objects with calculated durations
        """
        if df.height == 0:
            return []

        # Ensure required columns exist
        required = ['fwdCode', 'timeRaised', 'severityLevel', 'severity']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Sort by area and time
        df = df.sort(['fwdCode', 'timeRaised'])

        # Add flag for "Update" messages
        df = df.with_columns([
            pl.col('severity').str.contains('(?i)update').alias('is_update')
        ])

        # Calculate time to next warning for same area
        df = df.with_columns([
            pl.col('timeRaised')
              .shift(-1)
              .over('fwdCode')
              .alias('next_time')
        ])

        # Calculate gap in hours to next warning
        df = df.with_columns([
            ((pl.col('next_time') - pl.col('timeRaised'))
             .dt.total_seconds() / 3600.0)
            .alias('gap_to_next_hours')
        ])

        # Calculate duration using heuristic
        events = []

        for row in df.iter_rows(named=True):
            duration_hours = self._calculate_single_duration(
                severity_level=row['severityLevel'],
                gap_to_next=row.get('gap_to_next_hours'),
                is_update=row['is_update']
            )

            events.append(WarningEvent(
                fwdCode=row['fwdCode'],
                timeRaised=row['timeRaised'],
                severityLevel=row['severityLevel'],
                severity=row['severity'],
                duration_hours=duration_hours,
                is_update=row['is_update'],
                isTidal=row.get('isTidal')
            ))

        return events

    def _calculate_single_duration(
        self,
        severity_level: int,
        gap_to_next: Optional[float],
        is_update: bool
    ) -> float:
        """
        Calculate duration for a single warning.

        Args:
            severity_level: 1=Severe, 2=Warning, 3=Alert
            gap_to_next: Hours until next warning for same area (or None)
            is_update: Whether this is an "Update" message

        Returns:
            Duration in hours
        """
        default_duration = self.config.default_durations.get(severity_level, 24.0)
        max_gap = self.config.max_gap_hours

        # If no next warning, use default duration
        if gap_to_next is None:
            return default_duration

        # If gap is very large, treat as separate event
        if gap_to_next > max_gap:
            return default_duration

        # For updates, use the gap (they continue existing warnings)
        if is_update:
            return gap_to_next

        # For new warnings, use minimum of gap and default
        return min(gap_to_next, default_duration)

    def calculate_annual_scores(
        self,
        events: List[WarningEvent],
        year: int,
        separate_tidal: bool = True
    ) -> dict:
        """
        Calculate annual scores from warning events.

        Args:
            events: List of WarningEvent objects
            year: Year to calculate for (filters events)
            separate_tidal: If True, separate fluvial and coastal scores

        Returns:
            Dictionary with score breakdown
        """
        # Filter to specified year
        year_events = [
            e for e in events
            if e.timeRaised.year == year
        ]

        if not separate_tidal or not any(e.isTidal is not None for e in year_events):
            # Calculate total score without separation
            total_score = sum(
                e.calculate_score(self.config.severity_weights)
                for e in year_events
            )

            return {
                'year': year,
                'total_score': total_score,
                'total_events': len(year_events),
                'total_hours': sum(e.duration_hours for e in year_events),
                'by_severity': self._breakdown_by_severity(year_events),
            }

        # Separate fluvial and coastal
        fluvial_events = [e for e in year_events if e.isTidal is False]
        coastal_events = [e for e in year_events if e.isTidal is True]
        other_events = [e for e in year_events if e.isTidal is None]

        fluvial_score = sum(
            e.calculate_score(self.config.severity_weights)
            for e in fluvial_events
        )
        coastal_score = sum(
            e.calculate_score(self.config.severity_weights)
            for e in coastal_events
        )
        other_score = sum(
            e.calculate_score(self.config.severity_weights)
            for e in other_events
        )

        return {
            'year': year,
            'fluvial_score': fluvial_score,
            'coastal_score': coastal_score,
            'other_score': other_score,  # Warnings with unknown tidal status
            'total_score': fluvial_score + coastal_score + other_score,
            'fluvial_events': len(fluvial_events),
            'coastal_events': len(coastal_events),
            'other_events': len(other_events),
            'total_events': len(year_events),
            'fluvial_hours': sum(e.duration_hours for e in fluvial_events),
            'coastal_hours': sum(e.duration_hours for e in coastal_events),
            'other_hours': sum(e.duration_hours for e in other_events),
            'by_severity': {
                'fluvial': self._breakdown_by_severity(fluvial_events),
                'coastal': self._breakdown_by_severity(coastal_events),
                'other': self._breakdown_by_severity(other_events),
                'total': self._breakdown_by_severity(year_events),
            }
        }

    def _breakdown_by_severity(self, events: List[WarningEvent]) -> dict:
        """Create breakdown of events by severity level."""
        breakdown = {}

        for level in [1, 2, 3]:
            level_events = [e for e in events if e.severityLevel == level]
            breakdown[level] = {
                'count': len(level_events),
                'total_hours': sum(e.duration_hours for e in level_events),
                'weighted_score': sum(
                    e.calculate_score(self.config.severity_weights)
                    for e in level_events
                ),
            }

        return breakdown
