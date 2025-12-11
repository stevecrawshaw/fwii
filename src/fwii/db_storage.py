"""Database storage for historic flood warnings using DuckDB.

Provides schema management, data storage, and query helpers for
flood warning data in DuckDB.
"""

import logging
from pathlib import Path
from typing import Any

import duckdb
import polars as pl

from fwii.config import Config

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Raised when database operations fail."""


class FloodWarningsDatabase:
    """Manages flood warnings data in DuckDB.

    Provides methods for:
    - Database initialization and schema creation
    - Storing warning data
    - Querying and aggregating data
    - Maintaining indexes
    """

    WARNINGS_TABLE = "warnings"
    METADATA_TABLE = "metadata"

    def __init__(
        self,
        db_path: str | Path | None = None,
        config: Config | None = None,
    ):
        """Initialize the database connection.

        Args:
            db_path: Path to DuckDB database file. If None, uses data/processed/fwii.duckdb
            config: Configuration object. If None, loads from default location.
        """
        self.config = config or Config()

        if db_path is None:
            db_path = Path("data/processed/fwii.duckdb")
        else:
            db_path = Path(db_path)

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn: duckdb.DuckDBPyConnection | None = None

        logger.info(f"Database initialized at {self.db_path}")

    def connect(self):
        """Open database connection."""
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path))
            logger.debug("Database connection opened")

    def close(self):
        """Close database connection."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
            logger.debug("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def initialize_schema(self, drop_existing: bool = False):
        """Initialize database schema.

        Creates the warnings table and indexes if they don't exist.

        Args:
            drop_existing: If True, drop and recreate existing tables

        Raises:
            DatabaseError: If schema creation fails
        """
        self.connect()

        try:
            if drop_existing:
                logger.warning("Dropping existing tables")
                self.conn.execute(f"DROP TABLE IF EXISTS {self.WARNINGS_TABLE}")
                self.conn.execute(f"DROP TABLE IF EXISTS {self.METADATA_TABLE}")

            # Create warnings table
            # Note: Using row_number() in queries instead of explicit ID column
            self.conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.WARNINGS_TABLE} (
                    fwdCode VARCHAR NOT NULL,
                    severityLevel INTEGER NOT NULL,
                    timeRaised TIMESTAMP NOT NULL,
                    timeSeverityChanged TIMESTAMP,
                    timeMessageChanged TIMESTAMP,
                    isTidal BOOLEAN,
                    message TEXT,
                    severity VARCHAR,
                    year INTEGER GENERATED ALWAYS AS (EXTRACT(YEAR FROM timeRaised)) VIRTUAL,
                    CONSTRAINT valid_severity CHECK (severityLevel IN (1, 2, 3, 4))
                )
            """)

            # Create metadata table for tracking data loads
            self.conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.METADATA_TABLE} (
                    load_timestamp TIMESTAMP NOT NULL,
                    data_year INTEGER,
                    records_loaded INTEGER NOT NULL,
                    source_file VARCHAR,
                    notes TEXT
                )
            """)

            # Create indexes for common query patterns
            self._create_indexes()

            logger.info("Database schema initialized successfully")

        except Exception as e:
            msg = f"Error initializing schema: {e}"
            logger.error(msg)
            raise DatabaseError(msg) from e

    def _create_indexes(self):
        """Create indexes on commonly queried columns."""
        indexes = [
            # Index on warning area code (most common filter)
            f"CREATE INDEX IF NOT EXISTS idx_fwdcode ON {self.WARNINGS_TABLE}(fwdCode)",
            # Index on time for date range queries
            f"CREATE INDEX IF NOT EXISTS idx_timeraised ON {self.WARNINGS_TABLE}(timeRaised)",
            # Index on severity level for filtering
            f"CREATE INDEX IF NOT EXISTS idx_severity ON {self.WARNINGS_TABLE}(severityLevel)",
            # Composite index for year-based queries
            f"CREATE INDEX IF NOT EXISTS idx_year_fwdcode ON {self.WARNINGS_TABLE}(year, fwdCode)",
        ]

        for index_sql in indexes:
            try:
                self.conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Error creating index: {e}")

        logger.debug(f"Created {len(indexes)} indexes")

    def store_warnings(
        self,
        df: pl.DataFrame,
        source_file: str | None = None,
        replace: bool = False,
    ) -> int:
        """Store flood warnings data in the database.

        Args:
            df: Polars DataFrame containing flood warning records
            source_file: Optional source file path for metadata tracking
            replace: If True, replace existing data. If False, append.

        Returns:
            Number of records inserted

        Raises:
            DatabaseError: If storage fails
        """
        self.connect()

        if len(df) == 0:
            logger.warning("No records to store")
            return 0

        try:
            # Ensure required columns exist
            required_cols = {"fwdCode", "severityLevel", "timeRaised"}
            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                msg = f"Missing required columns: {missing_cols}"
                raise DatabaseError(msg)

            # Select only columns that exist in the table (excluding auto-generated ones)
            # The table has: id (auto), year (generated), plus the data columns
            table_data_cols = [
                "fwdCode",
                "severityLevel",
                "timeRaised",
                "timeSeverityChanged",
                "timeMessageChanged",
                "isTidal",
                "message",
                "severity",
            ]

            # Select only columns that exist in the DataFrame
            cols_to_insert = [col for col in table_data_cols if col in df.columns]
            df_filtered = df.select(cols_to_insert)

            # If replace mode, clear existing data
            if replace:
                logger.warning(f"Replacing all data in {self.WARNINGS_TABLE}")
                self.conn.execute(f"DELETE FROM {self.WARNINGS_TABLE}")

            # Build INSERT statement with explicit column list
            col_list = ", ".join(cols_to_insert)

            # Store the data using DuckDB's native Polars integration
            self.conn.execute(
                f"INSERT INTO {self.WARNINGS_TABLE} ({col_list}) "
                f"SELECT {col_list} FROM df_filtered"
            )

            record_count = len(df_filtered)

            # Record metadata
            data_year = None
            if "timeRaised" in df_filtered.columns:
                # Determine year from data
                years = df_filtered.select(
                    pl.col("timeRaised").dt.year().unique()
                ).to_series().to_list()
                if len(years) == 1:
                    data_year = years[0]

            self._record_load_metadata(
                records_loaded=record_count,
                data_year=data_year,
                source_file=source_file,
            )

            logger.info(f"Stored {record_count:,} records in database")
            return record_count

        except Exception as e:
            msg = f"Error storing warnings data: {e}"
            logger.error(msg)
            raise DatabaseError(msg) from e

    def _record_load_metadata(
        self,
        records_loaded: int,
        data_year: int | None = None,
        source_file: str | None = None,
        notes: str | None = None,
    ):
        """Record metadata about a data load operation."""
        self.conn.execute(
            f"""
            INSERT INTO {self.METADATA_TABLE}
            (load_timestamp, data_year, records_loaded, source_file, notes)
            VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?)
            """,
            [data_year, records_loaded, source_file, notes],
        )

    def get_warnings(
        self,
        fwd_codes: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        severity_levels: list[int] | None = None,
        year: int | None = None,
    ) -> pl.DataFrame:
        """Query flood warnings with filters.

        Args:
            fwd_codes: Filter by warning area codes
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            severity_levels: Filter by severity levels
            year: Filter by year

        Returns:
            Polars DataFrame with filtered warnings
        """
        self.connect()

        # Build query with filters
        query = f"SELECT * FROM {self.WARNINGS_TABLE} WHERE 1=1"
        params = []

        if fwd_codes:
            placeholders = ",".join("?" * len(fwd_codes))
            query += f" AND fwdCode IN ({placeholders})"
            params.extend(fwd_codes)

        if start_date:
            query += " AND timeRaised >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timeRaised <= ?"
            params.append(end_date)

        if severity_levels:
            placeholders = ",".join("?" * len(severity_levels))
            query += f" AND severityLevel IN ({placeholders})"
            params.extend(severity_levels)

        if year:
            query += " AND year = ?"
            params.append(year)

        query += " ORDER BY timeRaised"

        # Execute and convert to Polars
        result = self.conn.execute(query, params).pl()

        logger.debug(f"Retrieved {len(result):,} records")
        return result

    def get_annual_summary(self, year: int) -> dict[str, Any]:
        """Get summary statistics for a specific year.

        Args:
            year: Year to summarize

        Returns:
            Dictionary with annual statistics
        """
        self.connect()

        # Total warnings by severity
        severity_counts = self.conn.execute(
            f"""
            SELECT severityLevel, COUNT(*) as count
            FROM {self.WARNINGS_TABLE}
            WHERE year = ?
            GROUP BY severityLevel
            ORDER BY severityLevel
            """,
            [year],
        ).fetchall()

        # Unique warning areas
        unique_areas = self.conn.execute(
            f"""
            SELECT COUNT(DISTINCT fwdCode) as count
            FROM {self.WARNINGS_TABLE}
            WHERE year = ?
            """,
            [year],
        ).fetchone()[0]

        # Fluvial vs Tidal (if isTidal field exists)
        tidal_counts = {}
        try:
            tidal_result = self.conn.execute(
                f"""
                SELECT isTidal, COUNT(*) as count
                FROM {self.WARNINGS_TABLE}
                WHERE year = ? AND isTidal IS NOT NULL
                GROUP BY isTidal
                """,
                [year],
            ).fetchall()
            tidal_counts = {row[0]: row[1] for row in tidal_result}
        except Exception:
            pass

        return {
            "year": year,
            "total_warnings": sum(count for _, count in severity_counts),
            "severity_counts": dict(severity_counts),
            "unique_warning_areas": unique_areas,
            "tidal_counts": tidal_counts,
        }

    def get_warning_area_stats(self, fwd_code: str) -> dict[str, Any]:
        """Get statistics for a specific warning area.

        Args:
            fwd_code: Warning area code

        Returns:
            Dictionary with area statistics
        """
        self.connect()

        stats = self.conn.execute(
            f"""
            SELECT
                COUNT(*) as total_warnings,
                MIN(timeRaised) as first_warning,
                MAX(timeRaised) as last_warning,
                COUNT(DISTINCT severityLevel) as severity_levels_used
            FROM {self.WARNINGS_TABLE}
            WHERE fwdCode = ?
            """,
            [fwd_code],
        ).fetchone()

        return {
            "fwdCode": fwd_code,
            "total_warnings": stats[0],
            "first_warning": stats[1],
            "last_warning": stats[2],
            "severity_levels_used": stats[3],
        }

    def get_database_info(self) -> dict[str, Any]:
        """Get information about the database contents.

        Returns:
            Dictionary with database statistics
        """
        self.connect()

        # Total records
        total = self.conn.execute(
            f"SELECT COUNT(*) FROM {self.WARNINGS_TABLE}"
        ).fetchone()[0]

        # Date range
        date_range = self.conn.execute(
            f"""
            SELECT
                MIN(timeRaised) as earliest,
                MAX(timeRaised) as latest
            FROM {self.WARNINGS_TABLE}
            """
        ).fetchone()

        # Unique warning areas
        areas = self.conn.execute(
            f"SELECT COUNT(DISTINCT fwdCode) FROM {self.WARNINGS_TABLE}"
        ).fetchone()[0]

        # Years covered
        years = self.conn.execute(
            f"""
            SELECT DISTINCT year
            FROM {self.WARNINGS_TABLE}
            ORDER BY year
            """
        ).fetchall()
        years_list = [y[0] for y in years]

        # Load history
        load_history = self.conn.execute(
            f"""
            SELECT * FROM {self.METADATA_TABLE}
            ORDER BY load_timestamp DESC
            LIMIT 10
            """
        ).pl()

        return {
            "database_path": str(self.db_path),
            "total_records": total,
            "date_range": {"earliest": date_range[0], "latest": date_range[1]},
            "unique_warning_areas": areas,
            "years_covered": years_list,
            "load_history": load_history.to_dicts() if len(load_history) > 0 else [],
        }
