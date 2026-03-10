"""
Test script for duration calculator.

Loads 2020 warning data from CSV and tests the vectorised duration calculator.
"""

import sys

import polars as pl

from fwii.config import Config
from fwii.duration_calculator import DurationCalculator, DurationConfig


def main():
    config = Config()
    csv_path = config.data_processed_path / "warnings_2020.csv"

    if not csv_path.exists():
        print(f"Error: Data file not found: {csv_path}")
        print("Run: uv run python scripts/download_historic_data.py 2020")
        return 1

    print(f"Loading data from CSV: {csv_path}")
    df = pl.read_csv(csv_path, try_parse_dates=True)

    print(f"Loaded {df.height} warnings from 2020")
    print(f"Date range: {df['timeRaised'].min()} to {df['timeRaised'].max()}")
    print(f"  Fluvial (isTidal=false): {df.filter(pl.col('isTidal') == False).height}")
    print(f"  Coastal (isTidal=true): {df.filter(pl.col('isTidal') == True).height}")
    print(f"  Unknown: {df.filter(pl.col('isTidal').is_null()).height}")
    print()

    # Initialise calculator
    dur_config = DurationConfig()
    calculator = DurationCalculator(dur_config)

    # Calculate durations (vectorised)
    print("Calculating durations...")
    result_df = calculator.calculate_durations(df)

    print(f"Calculated durations for {result_df.height} events")
    print()

    # Show sample events
    print("Sample warning events:")
    print("-" * 100)
    sample = result_df.head(10)
    for row in sample.iter_rows(named=True):
        update_str = "(UPDATE)" if row["is_update"] else ""
        print(
            f"{row['fwdCode']:15s} {row['timeRaised']} "
            f"Level {row['severityLevel']} {update_str:<10s} "
            f"Duration: {row['duration_hours']:6.2f}h"
        )
    print()

    # Calculate annual scores
    print("Calculating annual scores for 2020...")
    scores = calculator.calculate_annual_scores(result_df, 2020, separate_tidal=True)

    print("=" * 100)
    print("2020 FLOOD WARNING INTENSITY SCORES")
    print("=" * 100)
    print()
    print(f"Total Events: {scores['total_events']}")
    print(f"  Fluvial: {scores['fluvial_events']}")
    print(f"  Coastal: {scores['coastal_events']}")
    print(f"  Other: {scores['other_events']}")
    print()
    print(
        f"Total Warning Hours (unweighted): {scores['fluvial_hours'] + scores['coastal_hours']:.1f}"
    )
    print(f"  Fluvial: {scores['fluvial_hours']:.1f} hours")
    print(f"  Coastal: {scores['coastal_hours']:.1f} hours")
    print(f"  Other: {scores['other_hours']:.1f} hours")
    print()
    print("Weighted Scores:")
    print(f"  Fluvial Score: {scores['fluvial_score']:.1f}")
    print(f"  Coastal Score: {scores['coastal_score']:.1f}")
    print(f"  Other Score: {scores['other_score']:.1f}")
    print(f"  TOTAL SCORE: {scores['total_score']:.1f}")
    print()

    # Show breakdown by severity
    print("Breakdown by Severity (Total):")
    print("-" * 100)
    for level in [1, 2, 3]:
        level_name = {1: "Severe", 2: "Warning", 3: "Alert"}[level]
        data = scores["by_severity"]["total"][level]
        print(
            f"  Level {level} ({level_name}): "
            f"{data['count']} events, "
            f"{data['total_hours']:.1f} hours, "
            f"weighted score: {data['weighted_score']:.1f}"
        )
    print()

    print("=" * 100)
    print("Note: These are 2020 BASELINE scores. The normalised indicator will be 100.")
    print("=" * 100)

    return 0


if __name__ == "__main__":
    sys.exit(main())
