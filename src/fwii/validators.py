"""Data validation for historic flood warnings.

Validates data quality, identifies issues, and generates validation reports.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import polars as pl

from fwii.config import Config

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""

    severity: str  # 'error', 'warning', 'info'
    category: str  # Type of issue
    message: str  # Description
    count: int = 0  # Number of affected records
    examples: list[dict[str, Any]] = field(default_factory=list)  # Sample records


@dataclass
class ValidationReport:
    """Comprehensive validation report for flood warning data."""

    total_records: int
    valid_records: int
    issues: list[ValidationIssue] = field(default_factory=list)
    passed: bool = True  # Overall validation status

    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue to the report."""
        self.issues.append(issue)
        if issue.severity == "error":
            self.passed = False

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the validation report."""
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "passed": self.passed,
            "error_count": sum(1 for i in self.issues if i.severity == "error"),
            "warning_count": sum(1 for i in self.issues if i.severity == "warning"),
            "info_count": sum(1 for i in self.issues if i.severity == "info"),
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "count": i.count,
                }
                for i in self.issues
            ],
        }

    def print_report(self):
        """Print a formatted validation report to the console."""
        print("\n" + "=" * 80)
        print("FLOOD WARNING DATA VALIDATION REPORT")
        print("=" * 80)
        print(f"\nTotal Records: {self.total_records:,}")
        print(f"Valid Records: {self.valid_records:,}")
        print(f"Overall Status: {'[OK] PASSED' if self.passed else '[X] FAILED'}")

        if not self.issues:
            print("\n[OK] No validation issues found")
            return

        # Group issues by severity
        errors = [i for i in self.issues if i.severity == "error"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        info = [i for i in self.issues if i.severity == "info"]

        if errors:
            print(f"\n{'=' * 80}")
            print(f"ERRORS ({len(errors)})")
            print("=" * 80)
            for issue in errors:
                print(f"\n[X] {issue.category}")
                print(f"  {issue.message}")
                print(f"  Affected records: {issue.count:,}")

        if warnings:
            print(f"\n{'=' * 80}")
            print(f"WARNINGS ({len(warnings)})")
            print("=" * 80)
            for issue in warnings:
                print(f"\n[!] {issue.category}")
                print(f"  {issue.message}")
                print(f"  Affected records: {issue.count:,}")

        if info:
            print(f"\n{'=' * 80}")
            print(f"INFORMATION ({len(info)})")
            print("=" * 80)
            for issue in info:
                print(f"\n[i] {issue.category}")
                print(f"  {issue.message}")
                print(f"  Count: {issue.count:,}")

        print("\n" + "=" * 80 + "\n")


class HistoricWarningsValidator:
    """Validates historic flood warning data quality.

    Performs comprehensive validation checks including:
    - Required field presence
    - Missing/invalid timestamps
    - Duplicate records
    - Incomplete warning lifecycles
    - Data consistency
    """

    def __init__(self, config: Config | None = None):
        """Initialize the validator.

        Args:
            config: Configuration object. If None, loads from default location.
        """
        self.config = config or Config()

        # Quality thresholds from config
        self.max_warning_duration_days = self.config.get(
            "indicator.quality.max_warning_duration_days", 14
        )

    def validate_warnings_data(
        self, df: pl.DataFrame, strict: bool = False
    ) -> ValidationReport:
        """Validate flood warnings data.

        Args:
            df: DataFrame containing flood warning records
            strict: If True, treat warnings as errors

        Returns:
            ValidationReport with identified issues
        """
        logger.info(f"Validating {len(df):,} flood warning records")

        report = ValidationReport(
            total_records=len(df),
            valid_records=len(df),  # Will be adjusted as issues are found
        )

        # Run all validation checks
        self._check_required_fields(df, report)
        self._check_missing_timestamps(df, report)
        self._check_invalid_severity_levels(df, report)
        self._check_duplicate_records(df, report)
        self._check_incomplete_warnings(df, report)
        self._check_unusually_long_warnings(df, report)
        self._check_timestamp_consistency(df, report)
        self._check_data_completeness(df, report)

        logger.info(
            f"Validation complete: "
            f"{report.total_records - report.valid_records:,} issues found"
        )

        return report

    def _check_required_fields(self, df: pl.DataFrame, report: ValidationReport):
        """Check that all required fields are present."""
        required_fields = {"fwdCode", "severityLevel", "timeRaised"}
        missing_fields = required_fields - set(df.columns)

        if missing_fields:
            report.add_issue(
                ValidationIssue(
                    severity="error",
                    category="Missing Required Fields",
                    message=f"Required fields are missing: {missing_fields}",
                    count=len(df),
                )
            )

    def _check_missing_timestamps(self, df: pl.DataFrame, report: ValidationReport):
        """Identify records with missing critical timestamps."""
        # Check for missing timeRaised
        missing_raised = df.filter(pl.col("timeRaised").is_null())
        if len(missing_raised) > 0:
            report.add_issue(
                ValidationIssue(
                    severity="error",
                    category="Missing timeRaised",
                    message="Records have missing or invalid timeRaised timestamps",
                    count=len(missing_raised),
                    examples=missing_raised.head(3).to_dicts(),
                )
            )
            report.valid_records -= len(missing_raised)

        # Check for missing timeSeverityChanged (warning only)
        if "timeSeverityChanged" in df.columns:
            missing_severity_changed = df.filter(
                pl.col("timeSeverityChanged").is_null()
            )
            if len(missing_severity_changed) > 0:
                report.add_issue(
                    ValidationIssue(
                        severity="warning",
                        category="Missing timeSeverityChanged",
                        message="Records have missing timeSeverityChanged timestamps",
                        count=len(missing_severity_changed),
                    )
                )

    def _check_invalid_severity_levels(
        self, df: pl.DataFrame, report: ValidationReport
    ):
        """Check for invalid severity level values."""
        valid_levels = {1, 2, 3, 4}
        invalid = df.filter(~pl.col("severityLevel").is_in(valid_levels))

        if len(invalid) > 0:
            report.add_issue(
                ValidationIssue(
                    severity="error",
                    category="Invalid Severity Levels",
                    message=f"Records have severity levels outside valid range {valid_levels}",
                    count=len(invalid),
                    examples=invalid.head(3).to_dicts(),
                )
            )
            report.valid_records -= len(invalid)

    def _check_duplicate_records(self, df: pl.DataFrame, report: ValidationReport):
        """Identify duplicate records."""
        # Check for exact duplicates across key fields
        key_fields = ["fwdCode", "severityLevel", "timeRaised"]

        # Only check if all key fields exist
        if not all(field in df.columns for field in key_fields):
            return

        duplicates = (
            df.group_by(key_fields)
            .agg(pl.len().alias("count"))
            .filter(pl.col("count") > 1)
        )

        if len(duplicates) > 0:
            total_duplicate_records = duplicates["count"].sum() - len(duplicates)
            report.add_issue(
                ValidationIssue(
                    severity="warning",
                    category="Duplicate Records",
                    message="Duplicate records found with identical key fields",
                    count=total_duplicate_records,
                    examples=duplicates.head(3).to_dicts(),
                )
            )

    def _check_incomplete_warnings(self, df: pl.DataFrame, report: ValidationReport):
        """Identify warnings that never reach severity level 4 (ongoing warnings)."""
        # Group by warning area and find those without a level 4 record
        warning_lifecycle = (
            df.group_by("fwdCode")
            .agg(
                pl.col("severityLevel").min().alias("min_severity"),
                pl.col("severityLevel").max().alias("max_severity"),
                (pl.col("severityLevel") == 4).any().alias("has_level_4"),
            )
            .filter(~pl.col("has_level_4"))
        )

        if len(warning_lifecycle) > 0:
            # Count total records for these warning areas
            incomplete_areas = set(warning_lifecycle["fwdCode"].to_list())
            incomplete_records = df.filter(pl.col("fwdCode").is_in(incomplete_areas))

            report.add_issue(
                ValidationIssue(
                    severity="info",
                    category="Incomplete Warning Lifecycles",
                    message=(
                        "Warning areas have no severity level 4 records "
                        "(may indicate ongoing warnings or data truncation)"
                    ),
                    count=len(incomplete_records),
                    examples=warning_lifecycle.head(3).to_dicts(),
                )
            )

    def _check_unusually_long_warnings(
        self, df: pl.DataFrame, report: ValidationReport
    ):
        """Identify warnings with unusually long durations."""
        # Calculate duration for records with both timeRaised and timeSeverityChanged
        if "timeSeverityChanged" not in df.columns:
            return

        df_with_duration = df.filter(
            pl.col("timeRaised").is_not_null()
            & pl.col("timeSeverityChanged").is_not_null()
        ).with_columns(
            (pl.col("timeSeverityChanged") - pl.col("timeRaised"))
            .dt.total_days()
            .alias("duration_days")
        )

        # Find warnings exceeding maximum expected duration
        long_warnings = df_with_duration.filter(
            pl.col("duration_days") > self.max_warning_duration_days
        )

        if len(long_warnings) > 0:
            max_duration = long_warnings["duration_days"].max()
            report.add_issue(
                ValidationIssue(
                    severity="warning",
                    category="Unusually Long Warnings",
                    message=(
                        f"Warnings exceed maximum expected duration "
                        f"({self.max_warning_duration_days} days). "
                        f"Longest: {max_duration:.1f} days"
                    ),
                    count=len(long_warnings),
                )
            )

    def _check_timestamp_consistency(
        self, df: pl.DataFrame, report: ValidationReport
    ):
        """Check for timestamp consistency issues."""
        if "timeSeverityChanged" not in df.columns:
            return

        # Check for timeSeverityChanged before timeRaised
        inconsistent = df.filter(
            pl.col("timeRaised").is_not_null()
            & pl.col("timeSeverityChanged").is_not_null()
            & (pl.col("timeSeverityChanged") < pl.col("timeRaised"))
        )

        if len(inconsistent) > 0:
            report.add_issue(
                ValidationIssue(
                    severity="error",
                    category="Timestamp Inconsistency",
                    message="Records have timeSeverityChanged before timeRaised",
                    count=len(inconsistent),
                    examples=inconsistent.head(3).to_dicts(),
                )
            )
            report.valid_records -= len(inconsistent)

    def _check_data_completeness(self, df: pl.DataFrame, report: ValidationReport):
        """Check overall data completeness and provide statistics."""
        # Calculate completeness for each optional field
        optional_fields = ["timeSeverityChanged", "timeMessageChanged", "isTidal"]

        for field in optional_fields:
            if field in df.columns:
                non_null = df.filter(pl.col(field).is_not_null()).height
                completeness_pct = (non_null / len(df)) * 100

                severity = "warning" if completeness_pct < 50 else "info"

                report.add_issue(
                    ValidationIssue(
                        severity=severity,
                        category=f"Field Completeness: {field}",
                        message=f"Field is {completeness_pct:.1f}% complete",
                        count=len(df) - non_null,
                    )
                )

    def validate_warning_area_coverage(
        self, df: pl.DataFrame, expected_areas: set[str]
    ) -> ValidationReport:
        """Validate that expected warning areas are present in the data.

        Args:
            df: DataFrame containing flood warning records
            expected_areas: Set of expected fwdCode values

        Returns:
            ValidationReport with coverage analysis
        """
        report = ValidationReport(
            total_records=len(df), valid_records=len(df)
        )

        # Get actual warning areas in the data
        actual_areas = set(df["fwdCode"].unique().to_list())

        # Find missing and unexpected areas
        missing_areas = expected_areas - actual_areas
        unexpected_areas = actual_areas - expected_areas

        if missing_areas:
            report.add_issue(
                ValidationIssue(
                    severity="warning",
                    category="Missing Warning Areas",
                    message=f"{len(missing_areas)} expected areas have no data",
                    count=len(missing_areas),
                    examples=[{"fwdCode": code} for code in list(missing_areas)[:5]],
                )
            )

        if unexpected_areas:
            unexpected_records = df.filter(pl.col("fwdCode").is_in(unexpected_areas))
            report.add_issue(
                ValidationIssue(
                    severity="warning",
                    category="Unexpected Warning Areas",
                    message=f"{len(unexpected_areas)} areas not in expected set",
                    count=len(unexpected_records),
                    examples=[{"fwdCode": code} for code in list(unexpected_areas)[:5]],
                )
            )

        return report
