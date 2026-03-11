"""Generate comprehensive FWII trend report for 2020-2024."""

import polars as pl

from fwii.config import Config
from fwii.indicator_calculator import IndicatorCalculator


def main():
    """Generate trend report."""
    print("=" * 80)
    print("WEST OF ENGLAND FLOOD WARNING INTENSITY INDEX (FWII)")
    print("TREND REPORT")
    print("=" * 80)
    print()

    config = Config()

    # Create calculator (will auto-load baseline from config)
    calculator = IndicatorCalculator()

    # Results storage
    results = []

    # Process each year -- discover from available CSV files, baseline period only
    data_dir = config.data_processed_path
    years = sorted(
        int(p.stem.split("_")[1])
        for p in data_dir.glob("warnings_*.csv")
        if int(p.stem.split("_")[1]) >= 2020
    )
    for year in years:
        csv_path = data_dir / f"warnings_{year}.csv"

        if not csv_path.exists():
            print(f"Warning: No data for {year}")
            continue

        # Load data
        df = pl.read_csv(csv_path, try_parse_dates=True)

        # Calculate indicators
        indicators = calculator.calculate_indicators(df, year)

        # Count warnings by type
        fluvial_count = len(df.filter(~pl.col("isTidal")))
        coastal_count = len(df.filter(pl.col("isTidal")))

        results.append(
            {
                "year": year,
                "total_warnings": len(df),
                "fluvial_warnings": fluvial_count,
                "coastal_warnings": coastal_count,
                "fluvial_index": round(indicators.fluvial_index, 1),
                "coastal_index": round(indicators.coastal_index, 1),
                "composite_fwii": round(indicators.composite_fwii, 1),
            }
        )

    # Create summary table
    summary_df = pl.DataFrame(results)

    print("ANNUAL SUMMARY")
    print("-" * 80)
    print(summary_df)
    print()

    # Calculate trends
    print("TRENDS & INSIGHTS")
    print("-" * 80)
    print()

    # Year-on-year changes
    print("Year-on-Year Changes in Composite FWII:")
    for idx in range(1, len(results)):
        prev = results[idx - 1]
        curr = results[idx]
        change = curr["composite_fwii"] - prev["composite_fwii"]
        if prev["composite_fwii"] != 0:
            ratio = curr["composite_fwii"] / prev["composite_fwii"]
            pct_str = f"({(ratio - 1) * 100:+6.1f}%)"
        else:
            pct_str = "(n/a)"

        arrow = "^" if change > 0 else "v" if change < 0 else "-"
        print(
            f"  {prev['year']} -> {curr['year']}: "
            f"{arrow} {abs(change):5.1f} pts {pct_str}"
        )

    print()

    # Overall trend
    first_yr = results[0]["year"]
    last_yr = results[-1]["year"]
    print(f"Overall Trend ({first_yr}-{last_yr}):")
    baseline = results[0]["composite_fwii"]
    latest = results[-1]["composite_fwii"]
    overall_change = latest - baseline
    overall_pct = ((latest / baseline) - 1) * 100

    arrow = "^" if overall_change > 0 else "v" if overall_change < 0 else "-"
    print(
        f"  {arrow} {abs(overall_change):5.1f} pts "
        f"({overall_pct:+6.1f}%) from baseline"
    )
    print()

    # Component analysis
    print("Component Trends:")
    print()
    print("Fluvial (River) Flooding:")
    for result in results:
        bar_length = int(result["fluvial_index"] / 5)
        bar = "#" * bar_length
        print(f"  {result['year']}: {result['fluvial_index']:6.1f} {bar}")

    print()
    print("Coastal/Tidal Flooding:")
    for result in results:
        bar_length = int(result["coastal_index"] / 5)
        bar = "#" * bar_length
        print(f"  {result['year']}: {result['coastal_index']:6.1f} {bar}")

    print()

    # Key findings
    print("KEY FINDINGS")
    print("-" * 80)
    print()

    # Find min/max years
    min_year = min(results, key=lambda x: x["composite_fwii"])
    max_year = max(results, key=lambda x: x["composite_fwii"])

    print(
        f"  Lowest Activity: {min_year['year']} "
        f"(FWII = {min_year['composite_fwii']})"
    )
    print(
        f"  Highest Activity: {max_year['year']} "
        f"(FWII = {max_year['composite_fwii']})"
    )
    print()

    # Fluvial vs Coastal trends
    fluvial_trend = results[-1]["fluvial_index"] - results[0]["fluvial_index"]
    coastal_trend = results[-1]["coastal_index"] - results[0]["coastal_index"]

    if fluvial_trend > 0:
        print(
            f"  Fluvial: INCREASED by {fluvial_trend:.1f} pts"
            f" (+{fluvial_trend:.0f}%)"
        )
    else:
        print(
            f"  Fluvial: DECREASED by {abs(fluvial_trend):.1f} pts"
            f" ({fluvial_trend:.0f}%)"
        )

    if coastal_trend > 0:
        print(
            f"  Coastal: INCREASED by {coastal_trend:.1f} pts"
            f" (+{coastal_trend:.0f}%)"
        )
    else:
        print(
            f"  Coastal: DECREASED by {abs(coastal_trend):.1f} pts"
            f" ({coastal_trend:.0f}%)"
        )

    print()

    # Warning counts trend
    total_warnings = sum(r["total_warnings"] for r in results)
    avg_warnings_per_year = total_warnings / len(results)

    print(f"  Total warnings ({first_yr}-{last_yr}): {total_warnings}")
    print(f"  Average warnings per year: {avg_warnings_per_year:.0f}")
    print()

    # Export CSV
    output_path = config.data_outputs_path / "fwii_timeseries.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_df.write_csv(output_path)
    print(f"Time series data exported to: {output_path}")
    print()

    print("=" * 80)
    print("REPORT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
