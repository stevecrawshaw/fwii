"""Generate comprehensive FWII trend report for 2020-2024."""

import sys
from pathlib import Path
import yaml
import polars as pl

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fwii.duration_calculator import DurationCalculator
from fwii.indicator_calculator import IndicatorCalculator


def main():
    """Generate trend report."""
    print("=" * 100)
    print("WEST OF ENGLAND FLOOD WARNING INTENSITY INDEX (FWII)")
    print("TREND REPORT 2020-2024")
    print("=" * 100)
    print()

    # Load config
    config_path = Path(__file__).parent.parent / "config" / "warning_areas.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Create calculator (will auto-load baseline from default location)
    calculator = IndicatorCalculator()
    duration_calc = DurationCalculator()

    # Results storage
    results = []

    # Process each year
    data_dir = Path(__file__).parent.parent / "data" / "processed"
    for year in [2020, 2021, 2022, 2023, 2024]:
        csv_path = data_dir / f"warnings_{year}.csv"

        if not csv_path.exists():
            print(f"⚠ Warning: No data for {year}")
            continue

        # Load data
        df = pl.read_csv(csv_path, try_parse_dates=True)

        # Calculate indicators
        indicators = calculator.calculate_indicators(df, year)

        # Count warnings by type
        fluvial_count = len(df.filter(pl.col("isTidal") == False))
        coastal_count = len(df.filter(pl.col("isTidal") == True))

        results.append({
            "year": year,
            "total_warnings": len(df),
            "fluvial_warnings": fluvial_count,
            "coastal_warnings": coastal_count,
            "fluvial_index": round(indicators.fluvial_index, 1),
            "coastal_index": round(indicators.coastal_index, 1),
            "composite_fwii": round(indicators.composite_fwii, 1),
        })

    # Create summary table
    summary_df = pl.DataFrame(results)

    print("ANNUAL SUMMARY")
    print("-" * 100)
    print(summary_df)
    print()

    # Calculate trends
    print("TRENDS & INSIGHTS")
    print("-" * 100)
    print()

    # Year-on-year changes
    print("Year-on-Year Changes in Composite FWII:")
    for i in range(1, len(results)):
        prev = results[i-1]
        curr = results[i]
        change = curr["composite_fwii"] - prev["composite_fwii"]
        pct_change = ((curr["composite_fwii"] / prev["composite_fwii"]) - 1) * 100

        arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
        print(f"  {prev['year']} → {curr['year']}: {arrow} {abs(change):5.1f} points ({pct_change:+6.1f}%)")

    print()

    # Overall trend
    print("Overall Trend (2020-2024):")
    baseline = results[0]["composite_fwii"]
    latest = results[-1]["composite_fwii"]
    overall_change = latest - baseline
    overall_pct = ((latest / baseline) - 1) * 100

    arrow = "↑" if overall_change > 0 else "↓" if overall_change < 0 else "→"
    print(f"  {arrow} {abs(overall_change):5.1f} points ({overall_pct:+6.1f}%) from baseline")
    print()

    # Component analysis
    print("Component Trends:")
    print()
    print("Fluvial (River) Flooding:")
    for result in results:
        bar_length = int(result["fluvial_index"] / 5)
        bar = "█" * bar_length
        print(f"  {result['year']}: {result['fluvial_index']:6.1f} {bar}")

    print()
    print("Coastal/Tidal Flooding:")
    for result in results:
        bar_length = int(result["coastal_index"] / 5)
        bar = "█" * bar_length
        print(f"  {result['year']}: {result['coastal_index']:6.1f} {bar}")

    print()

    # Key findings
    print("KEY FINDINGS")
    print("-" * 100)
    print()

    # Find min/max years
    min_year = min(results, key=lambda x: x["composite_fwii"])
    max_year = max(results, key=lambda x: x["composite_fwii"])

    print(f"• Lowest Activity: {min_year['year']} (FWII = {min_year['composite_fwii']})")
    print(f"• Highest Activity: {max_year['year']} (FWII = {max_year['composite_fwii']})")
    print()

    # Fluvial vs Coastal trends
    fluvial_trend = results[-1]["fluvial_index"] - results[0]["fluvial_index"]
    coastal_trend = results[-1]["coastal_index"] - results[0]["coastal_index"]

    if fluvial_trend > 0:
        print(f"• Fluvial flooding warnings have INCREASED by {fluvial_trend:.1f} points (+{fluvial_trend:.0f}%)")
    else:
        print(f"• Fluvial flooding warnings have DECREASED by {abs(fluvial_trend):.1f} points ({fluvial_trend:.0f}%)")

    if coastal_trend > 0:
        print(f"• Coastal flooding warnings have INCREASED by {coastal_trend:.1f} points (+{coastal_trend:.0f}%)")
    else:
        print(f"• Coastal flooding warnings have DECREASED by {abs(coastal_trend):.1f} points ({coastal_trend:.0f}%)")

    print()

    # Warning counts trend
    total_warnings = sum(r["total_warnings"] for r in results)
    avg_warnings_per_year = total_warnings / len(results)

    print(f"• Total warnings (2020-2024): {total_warnings}")
    print(f"• Average warnings per year: {avg_warnings_per_year:.0f}")
    print()

    # Export CSV
    output_path = Path(__file__).parent.parent / "data" / "outputs" / "fwii_timeseries.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_df.write_csv(output_path)
    print(f"✓ Time series data exported to: {output_path}")
    print()

    print("=" * 100)
    print("REPORT COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
