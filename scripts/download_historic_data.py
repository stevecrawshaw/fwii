"""Download and process historic flood warnings data.

Complete pipeline script that:
1. Downloads historic flood warnings for specified years
2. Loads and parses the CSV/JSON data
3. Validates data quality
4. Stores in DuckDB database
5. Generates quality reports

Usage:
    python scripts/download_historic_data.py 2020
    python scripts/download_historic_data.py 2020 2024
    python scripts/download_historic_data.py --year 2020 --force
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path to import fwii modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fwii.config import Config
from fwii.data_fetcher import HistoricWarningsFetcher
from fwii.data_loader import HistoricWarningsLoader
from fwii.db_storage import FloodWarningsDatabase
from fwii.validators import HistoricWarningsValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/processed/pipeline.log"),
    ],
)

logger = logging.getLogger(__name__)


def setup_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        "data/raw",
        "data/processed",
        "data/outputs",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def process_single_year(
    year: int,
    force_download: bool = False,
    skip_validation: bool = False,
    data_dir: Path | None = None,
) -> dict:
    """Process data for a single year through the complete pipeline.

    Args:
        year: Year to process
        force_download: If True, re-download even if data exists
        skip_validation: If True, skip validation step
        data_dir: Pre-downloaded data directory (optional, to avoid re-downloading)

    Returns:
        Dictionary with processing results and statistics
    """
    logger.info(f"{'=' * 80}")
    logger.info(f"PROCESSING YEAR: {year}")
    logger.info(f"{'=' * 80}")

    results = {
        "year": year,
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "stages": {},
        "errors": [],
    }

    config = Config()

    # Stage 1: Download (only if not already provided)
    if data_dir is None:
        logger.info("\n[1/4] DOWNLOADING DATA")
        try:
            with HistoricWarningsFetcher(config=config) as fetcher:
                data_dir = fetcher.download_complete_dataset(
                    force_download=force_download,
                    extract=True,
                )

                results["stages"]["download"] = {
                    "status": "success",
                    "data_directory": str(data_dir),
                }

                logger.info(f"[OK] Download complete: {data_dir}")

        except Exception as e:
            logger.error(f"[ERROR] Download failed: {e}")
            results["errors"].append({"stage": "download", "error": str(e)})
            return results
    else:
        logger.info(f"\n[1/4] USING CACHED DATA: {data_dir}")
        results["stages"]["download"] = {
            "status": "cached",
            "data_directory": str(data_dir),
        }

    # Stage 2: Load
    logger.info(f"\n[2/4] LOADING DATA FOR YEAR {year}")
    try:
        loader = HistoricWarningsLoader(config=config)

        # Find CSV or ODS files in the extracted directory
        csv_files = list(data_dir.glob("*.csv"))
        ods_files = list(data_dir.glob("*.ods"))

        if not csv_files and not ods_files:
            raise FileNotFoundError(f"No CSV or ODS files found in {data_dir}")

        logger.info(f"Found {len(csv_files)} CSV file(s), {len(ods_files)} ODS file(s)")

        # Load all data first
        df = loader.load_directory(
            directory=data_dir,
            pattern="*.csv" if csv_files else "*.ods",
            filter_west_of_england=True,
        )

        logger.info(f"Loaded {len(df):,} total West of England records")

        # Filter to specific year
        df = loader.filter_by_year(df, year)

        results["stages"]["load"] = {
            "status": "success",
            "records_loaded": len(df),
            "files_processed": len(csv_files),
        }

        # Get data summary
        summary = loader.get_data_summary(df)
        results["stages"]["load"]["summary"] = summary

        logger.info(f"[OK] Loaded {len(df):,} records")
        logger.info(f"  Unique warning areas: {summary['unique_warning_areas']}")
        logger.info(f"  Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")

    except Exception as e:
        logger.error(f"[ERROR] Load failed: {e}")
        results["errors"].append({"stage": "load", "error": str(e)})
        return results

    # Stage 3: Validate
    if not skip_validation:
        logger.info("\n[3/4] VALIDATING DATA")
        try:
            validator = HistoricWarningsValidator(config=config)

            # Run validation
            validation_report = validator.validate_warnings_data(df)

            # Print report to console
            validation_report.print_report()

            # Add to results
            results["stages"]["validation"] = {
                "status": "success",
                "passed": validation_report.passed,
                "summary": validation_report.get_summary(),
            }

            # Save validation report
            report_path = Path(f"data/processed/data_quality_report_{year}.json")
            with open(report_path, "w") as f:
                json.dump(validation_report.get_summary(), f, indent=2, default=str)

            logger.info(f"[OK] Validation complete: {report_path}")

        except Exception as e:
            logger.error(f"[ERROR] Validation failed: {e}")
            results["errors"].append({"stage": "validation", "error": str(e)})
            # Continue to storage even if validation fails

    # Stage 4: Store
    logger.info("\n[4/4] STORING IN DATABASE")
    try:
        with FloodWarningsDatabase(config=config) as db:
            # Initialize schema if first run
            db.initialize_schema(drop_existing=False)

            # Store data
            records_stored = db.store_warnings(
                df=df,
                source_file=str(data_dir),
                replace=False,  # Append mode
            )

            results["stages"]["storage"] = {
                "status": "success",
                "records_stored": records_stored,
            }

            # Get database info
            db_info = db.get_database_info()
            results["stages"]["storage"]["database_info"] = db_info

            logger.info(f"[OK] Stored {records_stored:,} records")
            logger.info(f"  Database total: {db_info['total_records']:,} records")
            logger.info(f"  Years covered: {db_info['years_covered']}")

    except Exception as e:
        logger.error(f"[ERROR] Storage failed: {e}")
        results["errors"].append({"stage": "storage", "error": str(e)})
        return results

    # Success!
    results["success"] = True
    logger.info(f"\n{'=' * 80}")
    logger.info(f"[OK] PIPELINE COMPLETE FOR {year}")
    logger.info(f"{'=' * 80}\n")

    return results


def process_multiple_years(
    start_year: int,
    end_year: int,
    force_download: bool = False,
    skip_validation: bool = False,
) -> dict:
    """Process multiple years through the pipeline.

    Downloads the complete dataset once, then processes each year separately.

    Args:
        start_year: First year to process (inclusive)
        end_year: Last year to process (inclusive)
        force_download: If True, re-download existing files
        skip_validation: If True, skip validation step

    Returns:
        Dictionary with combined results
    """
    all_results = {
        "start_year": start_year,
        "end_year": end_year,
        "timestamp": datetime.now().isoformat(),
        "years_processed": [],
        "summary": {},
    }

    total_years = end_year - start_year + 1
    successful = 0
    failed = 0

    # Download the complete dataset once
    logger.info(f"\n{'=' * 80}")
    logger.info(f"DOWNLOADING COMPLETE DATASET (2006-PRESENT)")
    logger.info(f"{'=' * 80}\n")

    config = Config()
    data_dir = None

    try:
        with HistoricWarningsFetcher(config=config) as fetcher:
            data_dir = fetcher.download_complete_dataset(
                force_download=force_download,
                extract=True,
            )
            logger.info(f"[OK] Dataset downloaded and ready: {data_dir}\n")
    except Exception as e:
        logger.error(f"[ERROR] Failed to download dataset: {e}")
        all_results["summary"] = {
            "total_years": total_years,
            "successful": 0,
            "failed": total_years,
            "error": f"Download failed: {e}",
        }
        return all_results

    # Process each year using the downloaded data
    for year in range(start_year, end_year + 1):
        logger.info(f"\n\nProcessing year {year} ({year - start_year + 1}/{total_years})\n")

        result = process_single_year(
            year=year,
            force_download=False,  # Already downloaded
            skip_validation=skip_validation,
            data_dir=data_dir,  # Reuse downloaded data
        )

        all_results["years_processed"].append(result)

        if result["success"]:
            successful += 1
        else:
            failed += 1

    # Summary
    all_results["summary"] = {
        "total_years": total_years,
        "successful": successful,
        "failed": failed,
        "success_rate": f"{(successful / total_years) * 100:.1f}%",
    }

    # Save combined results
    results_path = Path(
        f"data/processed/pipeline_results_{start_year}_{end_year}.json"
    )
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    logger.info(f"\n{'=' * 80}")
    logger.info(f"PIPELINE COMPLETE")
    logger.info(f"{'=' * 80}")
    logger.info(f"Successful: {successful}/{total_years}")
    logger.info(f"Failed: {failed}/{total_years}")
    logger.info(f"Results saved to: {results_path}")
    logger.info(f"{'=' * 80}\n")

    return all_results


def main():
    """Main entry point for the pipeline script."""
    parser = argparse.ArgumentParser(
        description="Download and process historic flood warnings data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single year
  python scripts/download_historic_data.py 2020

  # Process multiple years
  python scripts/download_historic_data.py 2020 2024

  # Force re-download
  python scripts/download_historic_data.py 2020 --force

  # Skip validation
  python scripts/download_historic_data.py 2020 --skip-validation
        """,
    )

    parser.add_argument(
        "start_year",
        type=int,
        help="Year to process (or start year if end_year provided)",
    )

    parser.add_argument(
        "end_year",
        type=int,
        nargs="?",
        help="End year (optional, for processing multiple years)",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force re-download even if data exists",
    )

    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip data validation step",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Setup directories
    setup_directories()

    # Process years
    if args.end_year:
        # Multiple years
        if args.start_year > args.end_year:
            logger.error("start_year must be <= end_year")
            sys.exit(1)

        results = process_multiple_years(
            start_year=args.start_year,
            end_year=args.end_year,
            force_download=args.force,
            skip_validation=args.skip_validation,
        )

        # Exit with error if any year failed
        if results["summary"]["failed"] > 0:
            sys.exit(1)

    else:
        # Single year
        results = process_single_year(
            year=args.start_year,
            force_download=args.force,
            skip_validation=args.skip_validation,
        )

        # Exit with error if failed
        if not results["success"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
