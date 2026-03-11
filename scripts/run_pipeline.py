"""Unified FWII pipeline.

Usage:
    python scripts/run_pipeline.py 2024              # Single year
    python scripts/run_pipeline.py 2020 2024         # Range
    python scripts/run_pipeline.py 2020 2024 --full  # Download + calculate + trend
"""

import argparse
import sys

import polars as pl

from fwii.config import Config
from fwii.indicator_calculator import IndicatorCalculator


def run_calculate(config: Config, years: list[int]) -> None:
    """Calculate FWII for each year."""
    calculator = IndicatorCalculator()

    for year in years:
        csv_path = config.data_processed_path / f"warnings_{year}.csv"
        if not csv_path.exists():
            print(f"Skipping {year}: no data at {csv_path}")
            continue

        df = pl.read_csv(csv_path, try_parse_dates=True)
        indicators = calculator.calculate_indicators(df, year)

        print(
            f"  {year}: FWII={indicators.composite_fwii:6.1f}  "
            f"(fluvial={indicators.fluvial_index:6.1f}, "
            f"coastal={indicators.coastal_index:6.1f})"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified FWII pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("start_year", type=int, help="Year or start of range")
    parser.add_argument("end_year", type=int, nargs="?", help="End year (optional)")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full pipeline: download + calculate + trend",
    )
    parser.add_argument("-f", "--force", action="store_true", help="Force re-download")

    args = parser.parse_args()
    config = Config()

    start = args.start_year
    end = args.end_year or start
    years = list(range(start, end + 1))

    print("=" * 80)
    print(f"FWII PIPELINE: {start}" + (f"-{end}" if end != start else ""))
    print("=" * 80)

    import subprocess

    scripts_dir = config.project_root / "scripts"

    # Step 1: Download if --full
    if args.full:
        print("\n[1] Downloading data...")
        cmd = [
            sys.executable,
            str(scripts_dir / "download_historic_data.py"),
            str(start),
            str(end),
        ]
        if args.force:
            cmd.append("--force")
        result = subprocess.run(cmd)  # noqa: S603
        if result.returncode != 0:
            print("Download had failures. Check logs.")
            return 1
    else:
        print("\n[1] Skipping download (use --full to include)")

    # Step 2: Calculate FWII
    print("\n[2] Calculating FWII...")
    run_calculate(config, years)

    # Step 3: Trend report if range or --full
    if len(years) > 1 or args.full:
        print("\n[3] Generating trend report...")
        subprocess.run(  # noqa: S603
            [sys.executable, str(scripts_dir / "generate_trend_report.py")]
        )
    else:
        print("\n[3] Skipping trend report (single year)")

    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
