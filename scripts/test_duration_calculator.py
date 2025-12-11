"""
Test script for duration calculator.

This script loads 2020 warning data from DuckDB and tests the duration calculator.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import duckdb
import polars as pl
import yaml

from fwii.duration_calculator import DurationCalculator, DurationConfig


def main():
    # Try to load from CSV export first (avoids database lock issues)
    csv_path = Path(__file__).parent.parent / "data" / "processed" / "warnings_2020.csv"

    if csv_path.exists():
        print(f"Loading data from CSV export: {csv_path}")
        df = pl.read_csv(csv_path, try_parse_dates=True)
    else:
        db_path = Path(__file__).parent.parent / "data" / "processed" / "fwii.duckdb"
        if not db_path.exists():
            print(f"Error: Database not found at {db_path}")
            print("Run: uv run python scripts/download_historic_data.py 2020")
            return 1

        # Connect to database
        conn = duckdb.connect(str(db_path), read_only=True)

        # Load 2020 warnings
        df = conn.execute("""
            SELECT fwdCode, timeRaised, severityLevel, severity, isTidal
            FROM warnings
            WHERE year = 2020
            ORDER BY fwdCode, timeRaised
        """).pl()

        conn.close()

    print(f"Loaded {df.height} warnings from 2020")
    print(f"Date range: {df['timeRaised'].min()} to {df['timeRaised'].max()}")
    print()

    # Load warning areas to get isTidal information
    config_path = Path(__file__).parent.parent / "config" / "warning_areas.yaml"
    with open(config_path) as f:
        areas_config = yaml.safe_load(f)

    # Create lookup DataFrame for isTidal
    areas_list = []
    for area in areas_config["warning_areas"]:
        areas_list.append(
            {"fwdCode": area["fwdCode"], "isTidal": area.get("isTidal", None)}
        )

    areas_df = pl.DataFrame(areas_list)

    # Join to add isTidal information
    df = df.drop("isTidal").join(areas_df, on="fwdCode", how="left")

    print("Joined with warning areas configuration")
    print(f"  Fluvial (isTidal=false): {df.filter(pl.col('isTidal') == False).height}")
    print(f"  Coastal (isTidal=true): {df.filter(pl.col('isTidal') == True).height}")
    print(f"  Unknown: {df.filter(pl.col('isTidal').is_null()).height}")
    print()

    # Initialize calculator
    config = DurationConfig()
    calculator = DurationCalculator(config)

    # Calculate durations
    print("Calculating durations...")
    events = calculator.calculate_durations(df)

    print(f"Calculated durations for {len(events)} events")
    print()

    # Show sample events
    print("Sample warning events:")
    print("-" * 100)
    for event in events[:10]:
        print(
            f"{event.fwdCode:15s} {event.timeRaised} "
            f"Level {event.severityLevel} {'(UPDATE)' if event.is_update else '':<10s} "
            f"Duration: {event.duration_hours:6.2f}h"
        )
    print()

    # Calculate annual scores
    print("Calculating annual scores for 2020...")
    scores = calculator.calculate_annual_scores(events, 2020, separate_tidal=True)

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

    # Show fluvial breakdown
    print("Fluvial Breakdown by Severity:")
    print("-" * 100)
    for level in [1, 2, 3]:
        level_name = {1: "Severe", 2: "Warning", 3: "Alert"}[level]
        data = scores["by_severity"]["fluvial"][level]
        if data["count"] > 0:
            print(
                f"  Level {level} ({level_name}): "
                f"{data['count']} events, "
                f"{data['total_hours']:.1f} hours, "
                f"weighted score: {data['weighted_score']:.1f}"
            )
    print()

    # Show coastal breakdown
    print("Coastal Breakdown by Severity:")
    print("-" * 100)
    for level in [1, 2, 3]:
        level_name = {1: "Severe", 2: "Warning", 3: "Alert"}[level]
        data = scores["by_severity"]["coastal"][level]
        if data["count"] > 0:
            print(
                f"  Level {level} ({level_name}): "
                f"{data['count']} events, "
                f"{data['total_hours']:.1f} hours, "
                f"weighted score: {data['weighted_score']:.1f}"
            )
    print()

    print("=" * 100)
    print("Note: These are 2020 BASELINE scores. The normalized indicator will be 100.")
    print("=" * 100)

    return 0


if __name__ == "__main__":
    sys.exit(main())
