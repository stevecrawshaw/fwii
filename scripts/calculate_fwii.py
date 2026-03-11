"""
Calculate Flood Warning Intensity Index (FWII) for a given year.

This script calculates the complete FWII indicator with baseline normalisation.
"""

import argparse
import sys

import polars as pl

from fwii.config import Config
from fwii.indicator_calculator import IndicatorCalculator


def load_warnings(config: Config, year: int) -> pl.DataFrame | None:
    """Load warnings CSV for a year (isTidal already present from pipeline)."""
    csv_path = config.data_processed_path / f"warnings_{year}.csv"

    if not csv_path.exists():
        print(f"Error: Data file not found: {csv_path}")
        print(f"Run: uv run python scripts/download_historic_data.py {year}")
        return None

    return pl.read_csv(csv_path, try_parse_dates=True)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate Flood Warning Intensity Index (FWII) for a given year",
    )
    parser.add_argument("year", type=int, help="Year to calculate FWII for")
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save 2020 scores as baseline (only valid for year 2020)",
    )

    args = parser.parse_args()
    year = args.year
    save_baseline = args.save_baseline

    print("=" * 100)
    print(f"CALCULATING FLOOD WARNING INTENSITY INDEX (FWII) FOR {year}")
    print("=" * 100)
    print()

    config = Config()

    # Load data
    print(f"Loading warning data for {year}...")
    df = load_warnings(config, year)

    if df is None:
        return 1

    print(f"  Loaded: {df.height} warnings")
    fluvial_count = df.filter(~pl.col("isTidal")).height
    coastal_count = df.filter(pl.col("isTidal")).height
    print(f"  Fluvial (isTidal=false): {fluvial_count}")
    print(f"  Coastal (isTidal=true): {coastal_count}")
    print()

    # Initialise calculator
    calculator = IndicatorCalculator()

    # Calculate indicators
    print("Calculating indicators...")
    indicators = calculator.calculate_indicators(df, year)

    # Display results
    print()
    print("=" * 100)
    print(f"RESULTS FOR {year}")
    print("=" * 100)
    print()

    print("RAW SCORES (Duration-Weighted)")
    print("-" * 80)
    i = indicators
    print(
        f"  Fluvial Score:  {i.fluvial_score_raw:8.1f}"
        f"  ({i.fluvial_events} events, {i.fluvial_hours:.1f} hours)"
    )
    print(
        f"  Coastal Score:  {i.coastal_score_raw:8.1f}"
        f"  ({i.coastal_events} events, {i.coastal_hours:.1f} hours)"
    )
    print(
        f"  Total Score:    {i.total_score_raw:8.1f}"
        f"  ({i.total_events} events)"
    )
    print()

    print("NORMALISED INDICATORS (Baseline 2020 = 100)")
    print("-" * 80)
    print(f"  Fluvial Index:  {i.fluvial_index:8.1f}")
    print(f"  Coastal Index:  {i.coastal_index:8.1f}")
    print()
    print(
        f"  COMPOSITE FWII: {i.composite_fwii:8.1f}"
        f"  (55% fluvial + 45% coastal)"
    )
    print()

    print("WARNING COUNTS BY SEVERITY")
    print("-" * 80)
    print(f"  Severe Flood Warnings (Level 1):  {i.severe_warnings}")
    print(f"  Flood Warnings (Level 2):         {i.flood_warnings}")
    print(f"  Flood Alerts (Level 3):           {i.flood_alerts}")
    print()

    # Interpretation
    print("INTERPRETATION")
    print("-" * 80)
    if year == 2020:
        print("  This is the BASELINE year. All indices normalised to 100.")
    else:
        if i.composite_fwii > 100:
            pct = i.composite_fwii - 100
            print(f"  {pct:.1f}% HIGHER than 2020 baseline")
        elif i.composite_fwii < 100:
            pct = 100 - i.composite_fwii
            print(f"  {pct:.1f}% LOWER than 2020 baseline")
        else:
            print("  Same as 2020 baseline")

        print()
        print("  Component changes from baseline:")
        if i.fluvial_index > 100:
            print(f"    - Fluvial: {i.fluvial_index - 100:.1f}% increase")
        else:
            print(f"    - Fluvial: {100 - i.fluvial_index:.1f}% decrease")

        if i.coastal_index > 100:
            print(f"    - Coastal: {i.coastal_index - 100:.1f}% increase")
        else:
            print(f"    - Coastal: {100 - i.coastal_index:.1f}% decrease")

    print()

    # Save baseline if requested
    if save_baseline and year == 2020:
        from fwii.indicator_calculator import BaselineScores

        baseline = BaselineScores(
            year=year,
            fluvial_score=indicators.fluvial_score_raw,
            coastal_score=indicators.coastal_score_raw,
            total_score=indicators.total_score_raw,
            fluvial_hours=indicators.fluvial_hours,
            coastal_hours=indicators.coastal_hours,
            fluvial_events=indicators.fluvial_events,
            coastal_events=indicators.coastal_events,
        )

        calculator.save_baseline(baseline)
        print("=" * 100)
        print("BASELINE SAVED: config/baseline_2020.yaml")
        print("=" * 100)
        print()

    print("=" * 100)
    print("CALCULATION COMPLETE")
    print("=" * 100)

    return 0


if __name__ == "__main__":
    sys.exit(main())
