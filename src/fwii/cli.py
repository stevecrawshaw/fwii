"""CLI entry points for FWII pipeline."""

import sys


def main_pipeline() -> None:
    """Unified pipeline entry point (fwii-pipeline)."""
    from scripts.run_pipeline import main

    sys.exit(main())


def main_calculate() -> None:
    """Calculate FWII entry point (fwii-calculate)."""
    from scripts.calculate_fwii import main

    sys.exit(main())


def main_trend() -> None:
    """Trend report entry point (fwii-trend)."""
    from scripts.generate_trend_report import main

    main()
