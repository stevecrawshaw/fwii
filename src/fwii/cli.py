"""CLI entry points for FWII pipeline."""

import runpy
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"


def main_pipeline() -> None:
    """Unified pipeline entry point (fwii-pipeline)."""
    script = SCRIPTS_DIR / "run_pipeline.py"
    sys.argv[0] = str(script)
    runpy.run_path(str(script), run_name="__main__")


def main_calculate() -> None:
    """Calculate FWII entry point (fwii-calculate)."""
    script = SCRIPTS_DIR / "calculate_fwii.py"
    sys.argv[0] = str(script)
    runpy.run_path(str(script), run_name="__main__")


def main_trend() -> None:
    """Trend report entry point (fwii-trend)."""
    script = SCRIPTS_DIR / "generate_trend_report.py"
    sys.argv[0] = str(script)
    runpy.run_path(str(script), run_name="__main__")
