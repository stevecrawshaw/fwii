"""CLI entry points for FWII pipeline."""

import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"


def _import_script(name: str):
    """Import a script module by file path."""
    script_path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main_pipeline() -> None:
    """Unified pipeline entry point (fwii-pipeline)."""
    module = _import_script("run_pipeline")
    sys.exit(module.main())


def main_calculate() -> None:
    """Calculate FWII entry point (fwii-calculate)."""
    module = _import_script("calculate_fwii")
    sys.exit(module.main())


def main_trend() -> None:
    """Trend report entry point (fwii-trend)."""
    module = _import_script("generate_trend_report")
    module.main()
