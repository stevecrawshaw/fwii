"""Data loader for historic flood warnings.

Loads and parses historic flood warning data from CSV/JSON files,
filtering for West of England areas and normalising timestamps.
"""

import logging
from pathlib import Path
from typing import Literal

import polars as pl

from fwii.config import Config

logger = logging.getLogger(__name__)


class DataLoadError(Exception):
    """Raised when data loading fails."""


class HistoricWarningsLoader:
    """Loads and processes historic flood warning data.

    Handles CSV and JSON formats, filters for West of England warning areas,
    and normalises timestamps to UTC.
    """

    def __init__(self, config: Config | None = None):
        """Initialise the loader.

        Args:
            config: Configuration object. If None, loads from default location.
        """
        self.config = config or Config()

        # Load West of England warning area codes
        self.west_of_england_codes = self._load_warning_area_codes()
        logger.info(
            f"Loaded {len(self.west_of_england_codes)} "
            "West of England warning area codes"
        )

    def _load_warning_area_codes(self) -> set[str]:
        """Load the list of West of England warning area codes from config.

        Returns:
            Set of fwdCode strings for West of England

        Raises:
            DataLoadError: If warning areas config cannot be loaded
        """
        try:
            codes = self.config.warning_area_codes

            if not codes:
                msg = "No warning area codes found in config"
                raise DataLoadError(msg)

            return codes

        except DataLoadError:
            raise
        except Exception as e:
            msg = f"Error loading warning area codes: {e}"
            logger.error(msg)
            raise DataLoadError(msg) from e

    def load_historic_warnings(
        self,
        file_path: str | Path,
        format: Literal["csv", "json", "ods"] | None = None,
        filter_west_of_england: bool = True,
    ) -> pl.DataFrame:
        """Load historic flood warnings from a file.

        Args:
            file_path: Path to CSV, JSON, or ODS file
            format: File format. If None, infers from extension
            filter_west_of_england: If True, filter for West of England areas only

        Returns:
            Polars DataFrame with normalised flood warning data

        Raises:
            DataLoadError: If file cannot be loaded or parsed
            FileNotFoundError: If file does not exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        # Infer format from extension if not provided
        if format is None:
            suffix = file_path.suffix.lower()
            if suffix == ".csv":
                format = "csv"
            elif suffix == ".json":
                format = "json"
            elif suffix == ".ods":
                format = "ods"
            else:
                msg = f"Cannot infer format from extension: {file_path.suffix}"
                raise DataLoadError(msg)

        logger.info(f"Loading {format.upper()} data from {file_path}")

        try:
            # Load the raw data
            if format == "csv":
                df = self._load_csv(file_path)
            elif format == "json":
                df = self._load_json(file_path)
            elif format == "ods":
                df = self._load_ods(file_path)
            else:
                msg = f"Unsupported format: {format}"
                raise DataLoadError(msg)

            logger.info(f"Loaded {len(df)} records from {file_path}")

            # Process the data
            df = self._normalize_schema(df)
            df = self._parse_timestamps(df)

            # Filter for West of England if requested
            if filter_west_of_england:
                original_count = len(df)
                df = self._filter_west_of_england(df)
                filtered_count = len(df)
                logger.info(
                    f"Filtered to {filtered_count} West of England records "
                    f"({original_count - filtered_count} excluded)"
                )

            return df

        except Exception as e:
            msg = f"Error loading data from {file_path}: {e}"
            logger.error(msg)
            raise DataLoadError(msg) from e

    def _load_csv(self, file_path: Path) -> pl.DataFrame:
        """Load data from CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            Polars DataFrame with raw data
        """
        # Load CSV with automatic type inference
        # Set all timestamp columns as strings initially for consistent parsing
        return pl.read_csv(
            file_path,
            try_parse_dates=False,  # We'll parse dates manually
            null_values=["", "null", "NULL", "None"],
            infer_schema_length=10000,  # Sample more rows for schema inference
        )

    def _load_json(self, file_path: Path) -> pl.DataFrame:
        """Load data from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Polars DataFrame with raw data
        """
        return pl.read_json(file_path)

    def _load_ods(self, file_path: Path) -> pl.DataFrame:
        """Load data from ODS (Open Document Spreadsheet) file.

        Args:
            file_path: Path to ODS file

        Returns:
            Polars DataFrame with raw data
        """
        try:
            # Polars can read ODS files via pandas
            import pandas as pd

            # Read ODS file using pandas (odfpy required)
            pdf = pd.read_excel(file_path, engine="odf")

            # Convert to Polars DataFrame
            return pl.from_pandas(pdf)
        except ImportError as e:
            msg = (
                "ODS support requires additional dependencies. "
                "Install with: uv add odfpy pandas"
            )
            logger.error(msg)
            raise DataLoadError(msg) from e
        except Exception as e:
            msg = f"Error reading ODS file: {e}"
            logger.error(msg)
            raise DataLoadError(msg) from e

    def _normalize_schema(self, df: pl.DataFrame) -> pl.DataFrame:
        """Normalise column names and ensure required fields exist.

        Maps EA column names to our expected schema:
        - DATE -> timeRaised
        - CODE -> fwdCode
        - TYPE -> severity (text description)

        Args:
            df: Raw DataFrame

        Returns:
            DataFrame with normalised schema

        Raises:
            DataLoadError: If required fields are missing
        """
        # EA column name mappings
        column_mappings = {
            "DATE": "timeRaised",
            "CODE": "fwdCode",
            "TYPE": "severity",
            "WARNING / ALERT AREA NAME": "label",
            "AREA": "area_ref",  # Keep for reference
        }

        # Apply column renames
        for old_name, new_name in column_mappings.items():
            if old_name in df.columns:
                df = df.rename({old_name: new_name})

        # Map severity text to severity levels
        # Case-insensitive, strips "Update " prefix, maps legacy "Flood Watch" to Alert
        SEVERITY_MAP = {
            "severe flood warning": 1,
            "flood warning": 2,
            "flood alert": 3,
            "flood watch": 3,  # Pre-2011 equivalent of Flood Alert
            "warning no longer in force": 4,
        }

        if "severity" in df.columns:
            df = df.with_columns(
                pl.col("severity")
                .str.strip_chars()
                .str.replace(r"(?i)^Update\s+", "")
                .str.to_lowercase()
                .replace_strict(SEVERITY_MAP, default=None, return_dtype=pl.Int64)
                .alias("severityLevel")
            )

            # Log any unmapped severity values
            unmapped = df.filter(
                pl.col("severityLevel").is_null() & pl.col("severity").is_not_null()
            )
            if len(unmapped) > 0:
                unknown_values = unmapped["severity"].unique().to_list()
                logger.warning(
                    f"{len(unmapped)} unmapped severity values: {unknown_values}"
                )

        # Required fields after mapping
        required_fields = {
            "fwdCode",
            "severityLevel",
            "timeRaised",
        }

        # Check for required fields
        missing_fields = required_fields - set(df.columns)
        if missing_fields:
            logger.error(f"Available columns: {df.columns}")
            msg = f"Missing required fields after mapping: {missing_fields}"
            raise DataLoadError(msg)

        logger.debug(f"Schema normalized. Columns: {df.columns}")

        return df

    def _parse_timestamps(self, df: pl.DataFrame) -> pl.DataFrame:
        """Parse timestamp columns to datetime, handling malformed values.

        Args:
            df: DataFrame with string or datetime timestamp columns

        Returns:
            DataFrame with parsed datetime columns
        """
        timestamp_columns = [
            "timeRaised",
            "timeSeverityChanged",
            "timeMessageChanged",
        ]

        for col in timestamp_columns:
            if col in df.columns:
                # Check if already datetime type
                if df[col].dtype in [
                    pl.Datetime,
                    pl.Datetime("ms"),
                    pl.Datetime("us"),
                    pl.Datetime("ns"),
                ]:
                    logger.debug(f"{col} already in datetime format")
                    continue

                # Parse ISO 8601 timestamps, setting invalid ones to null
                df = df.with_columns(
                    pl.col(col)
                    .str.strptime(pl.Datetime, format="%+", strict=False)
                    .alias(col)
                )

                # Count and log missing timestamps
                null_count = df.filter(pl.col(col).is_null()).height
                if null_count > 0:
                    logger.warning(f"{null_count} records have missing/invalid {col}")

        return df

    def _filter_west_of_england(self, df: pl.DataFrame) -> pl.DataFrame:
        """Filter for West of England warning areas and join isTidal.

        Args:
            df: DataFrame with all warning records

        Returns:
            DataFrame filtered to West of England areas with isTidal column
        """
        df = df.filter(pl.col("fwdCode").is_in(self.west_of_england_codes))

        # Build isTidal lookup from config and join
        areas_df = pl.DataFrame(
            [
                {"fwdCode": area["fwdCode"], "isTidal": area.get("isTidal", None)}
                for area in self.config.warning_areas
            ]
        )

        if "isTidal" in df.columns:
            df = df.drop("isTidal")

        return df.join(areas_df, on="fwdCode", how="left")

    def load_directory(
        self,
        directory: str | Path,
        pattern: str = "*.csv",
        filter_west_of_england: bool = True,
    ) -> pl.DataFrame:
        """Load and combine all matching files in a directory.

        Args:
            directory: Directory containing data files
            pattern: Glob pattern to match files (default: "*.csv")
            filter_west_of_england: If True, filter for West of England areas

        Returns:
            Combined Polars DataFrame

        Raises:
            DataLoadError: If no files found or loading fails
        """
        directory = Path(directory)

        if not directory.exists():
            msg = f"Directory not found: {directory}"
            raise FileNotFoundError(msg)

        # Find all matching files
        files = list(directory.glob(pattern))

        if not files:
            msg = f"No files matching '{pattern}' found in {directory}"
            raise DataLoadError(msg)

        logger.info(f"Found {len(files)} files matching '{pattern}'")

        # Load and combine all files
        dfs = []
        for file_path in files:
            try:
                df = self.load_historic_warnings(
                    file_path=file_path,
                    filter_west_of_england=filter_west_of_england,
                )
                dfs.append(df)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                continue

        if not dfs:
            msg = "Failed to load any files"
            raise DataLoadError(msg)

        # Combine all DataFrames
        combined_df = pl.concat(dfs, how="vertical")

        logger.info(f"Combined {len(dfs)} files into {len(combined_df)} total records")

        return combined_df

    def filter_by_year(self, df: pl.DataFrame, year: int) -> pl.DataFrame:
        """Filter DataFrame to a specific year.

        Args:
            df: DataFrame with flood warning records
            year: Year to filter for

        Returns:
            Filtered DataFrame containing only records from the specified year
        """
        original_count = len(df)

        # Extract year from timeRaised and filter
        df_filtered = df.filter(pl.col("timeRaised").dt.year() == year)

        filtered_count = len(df_filtered)
        logger.info(
            f"Filtered to year {year}: {filtered_count:,} records "
            f"({original_count - filtered_count:,} excluded)"
        )

        return df_filtered

    def get_data_summary(self, df: pl.DataFrame) -> dict:
        """Generate summary statistics for loaded data.

        Args:
            df: DataFrame to summarise

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "total_records": len(df),
            "unique_warning_areas": df["fwdCode"].n_unique(),
            "date_range": {
                "earliest": df["timeRaised"].min(),
                "latest": df["timeRaised"].max(),
            },
            "severity_distribution": (
                df.group_by("severityLevel")
                .agg(pl.len().alias("count"))
                .sort("severityLevel")
                .to_dicts()
            ),
            "missing_timestamps": {
                col: df.filter(pl.col(col).is_null()).height
                for col in ["timeRaised", "timeSeverityChanged", "timeMessageChanged"]
                if col in df.columns
            },
        }

        # Add tidal/fluvial breakdown if available
        if "isTidal" in df.columns:
            summary["tidal_distribution"] = (
                df.group_by("isTidal").agg(pl.len().alias("count")).to_dicts()
            )

        return summary
