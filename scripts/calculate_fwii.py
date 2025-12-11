"""
Calculate Flood Warning Intensity Index (FWII) for a given year.

This script calculates the complete FWII indicator with baseline normalization.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import polars as pl
import yaml

from fwii.indicator_calculator import IndicatorCalculator


def load_warnings_with_tidal(year: int) -> pl.DataFrame:
    """Load warnings for a year and join with warning areas for isTidal info."""
    # Load from CSV export
    csv_path = Path(__file__).parent.parent / 'data' / 'processed' / f'warnings_{year}.csv'

    if not csv_path.exists():
        print(f"Error: Data file not found: {csv_path}")
        print(f"Run: uv run python scripts/download_historic_data.py {year}")
        return None

    df = pl.read_csv(csv_path, try_parse_dates=True)

    # Load warning areas to get isTidal information
    config_path = Path(__file__).parent.parent / 'config' / 'warning_areas.yaml'
    with open(config_path, 'r') as f:
        areas_config = yaml.safe_load(f)

    # Create lookup DataFrame for isTidal
    areas_list = []
    for area in areas_config['warning_areas']:
        areas_list.append({
            'fwdCode': area['fwdCode'],
            'isTidal': area.get('isTidal', None)
        })

    areas_df = pl.DataFrame(areas_list)

    # Join to add isTidal information
    if 'isTidal' in df.columns:
        df = df.drop('isTidal')

    df = df.join(areas_df, on='fwdCode', how='left')

    return df


def main():
    if len(sys.argv) < 2:
        print("Usage: python calculate_fwii.py <year> [--save-baseline]")
        print("\nExamples:")
        print("  python calculate_fwii.py 2020 --save-baseline  # Calculate and save 2020 baseline")
        print("  python calculate_fwii.py 2024                  # Calculate 2024 normalized to 2020")
        return 1

    year = int(sys.argv[1])
    save_baseline = '--save-baseline' in sys.argv

    print("=" * 100)
    print(f"CALCULATING FLOOD WARNING INTENSITY INDEX (FWII) FOR {year}")
    print("=" * 100)
    print()

    # Load data
    print(f"Loading warning data for {year}...")
    df = load_warnings_with_tidal(year)

    if df is None:
        return 1

    print(f"  Loaded: {df.height} warnings")
    print(f"  Fluvial (isTidal=false): {df.filter(pl.col('isTidal') == False).height}")
    print(f"  Coastal (isTidal=true): {df.filter(pl.col('isTidal') == True).height}")
    print()

    # Initialize calculator
    calculator = IndicatorCalculator()

    # Calculate indicators
    print(f"Calculating indicators...")
    indicators = calculator.calculate_indicators(df, year)

    # Display results
    print()
    print("=" * 100)
    print(f"RESULTS FOR {year}")
    print("=" * 100)
    print()

    print("RAW SCORES (Duration-Weighted)")
    print("-" * 100)
    print(f"  Fluvial Score:    {indicators.fluvial_score_raw:8.1f}  ({indicators.fluvial_events} events, {indicators.fluvial_hours:.1f} hours)")
    print(f"  Coastal Score:    {indicators.coastal_score_raw:8.1f}  ({indicators.coastal_events} events, {indicators.coastal_hours:.1f} hours)")
    print(f"  Total Score:      {indicators.total_score_raw:8.1f}  ({indicators.total_events} events)")
    print()

    print("NORMALIZED INDICATORS (Baseline 2020 = 100)")
    print("-" * 100)
    print(f"  Fluvial Index:    {indicators.fluvial_index:8.1f}")
    print(f"  Coastal Index:    {indicators.coastal_index:8.1f}")
    print()
    print(f"  COMPOSITE FWII:   {indicators.composite_fwii:8.1f}  (55% fluvial + 45% coastal)")
    print()

    print("WARNING COUNTS BY SEVERITY")
    print("-" * 100)
    print(f"  Severe Flood Warnings (Level 1):  {indicators.severe_warnings}")
    print(f"  Flood Warnings (Level 2):         {indicators.flood_warnings}")
    print(f"  Flood Alerts (Level 3):           {indicators.flood_alerts}")
    print()

    # Interpretation
    print("INTERPRETATION")
    print("-" * 100)
    if year == 2020:
        print("  This is the BASELINE year. All indices normalized to 100.")
    else:
        if indicators.composite_fwii > 100:
            pct = indicators.composite_fwii - 100
            print(f"  {pct:.1f}% HIGHER flood warning activity than 2020 baseline")
        elif indicators.composite_fwii < 100:
            pct = 100 - indicators.composite_fwii
            print(f"  {pct:.1f}% LOWER flood warning activity than 2020 baseline")
        else:
            print("  Same flood warning activity as 2020 baseline")

        print()
        print("  Component changes from baseline:")
        if indicators.fluvial_index > 100:
            print(f"    - Fluvial: {indicators.fluvial_index - 100:.1f}% increase")
        else:
            print(f"    - Fluvial: {100 - indicators.fluvial_index:.1f}% decrease")

        if indicators.coastal_index > 100:
            print(f"    - Coastal: {indicators.coastal_index - 100:.1f}% increase")
        else:
            print(f"    - Coastal: {100 - indicators.coastal_index:.1f}% decrease")

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
        print(f"BASELINE SAVED: config/baseline_2020.yaml")
        print("=" * 100)
        print()

    print("=" * 100)
    print("CALCULATION COMPLETE")
    print("=" * 100)

    return 0


if __name__ == '__main__':
    sys.exit(main())
