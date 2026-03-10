"""Configuration management for FWII project."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from fwii.indicator_calculator import BaselineScores


class Config:
    """Load and manage FWII configuration from YAML files."""

    def __init__(self, config_path: str | Path | None = None):
        """Initialise configuration.

        Args:
            config_path: Path to settings.yaml. If None, uses default location.
        """
        if config_path is None:
            # Default to config/settings.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "settings.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path) as f:
            self._config = yaml.safe_load(f)

        self.config_path = config_path
        self.project_root = config_path.parent.parent

    @property
    def api_base_url(self) -> str:
        """Get the flood monitoring API base URL."""
        return self._config["api"]["flood_monitoring_base_url"]

    @property
    def flood_areas_url(self) -> str:
        """Get the full flood areas endpoint URL."""
        base = self._config["api"]["flood_monitoring_base_url"]
        endpoint = self._config["api"]["flood_areas_endpoint"]
        return f"{base}{endpoint}"

    @property
    def floods_url(self) -> str:
        """Get the full current floods endpoint URL."""
        base = self._config["api"]["flood_monitoring_base_url"]
        endpoint = self._config["api"]["floods_endpoint"]
        return f"{base}{endpoint}"

    @property
    def stations_url(self) -> str:
        """Get the full stations endpoint URL."""
        base = self._config["api"]["flood_monitoring_base_url"]
        endpoint = self._config["api"]["stations_endpoint"]
        return f"{base}{endpoint}"

    @property
    def rate_limit_delay(self) -> float:
        """Get the rate limit delay in seconds."""
        return self._config["api"]["rate_limit_delay"]

    @property
    def timeout(self) -> int:
        """Get the API request timeout in seconds."""
        return self._config["api"]["timeout"]

    @property
    def max_retries(self) -> int:
        """Get the maximum number of retry attempts."""
        return self._config["api"]["max_retries"]

    @property
    def retry_delay(self) -> int:
        """Get the retry delay in seconds."""
        return self._config["api"]["retry_delay"]

    @property
    def counties(self) -> list[str]:
        """Get the list of West of England counties."""
        return self._config["geography"]["counties"]

    @property
    def region_name(self) -> str:
        """Get the region name."""
        return self._config["geography"]["region_name"]

    @property
    def wessex_region_code(self) -> str:
        """Get the Wessex region code prefix."""
        return self._config["geography"]["wessex_region_code"]

    @property
    def baseline_year(self) -> int:
        """Get the baseline year for normalisation."""
        return self._config["indicator"]["baseline_year"]

    @property
    def severity_weights(self) -> dict[int, int]:
        """Get the severity level weights."""
        return self._config["indicator"]["severity_weights"]

    @property
    def composite_weights(self) -> dict[str, float]:
        """Get the composite indicator weights."""
        return self._config["indicator"]["composite_weights"]

    @property
    def surface_water_caveat(self) -> str:
        """Get the surface water caveat text."""
        return self._config["output"]["surface_water_caveat"]

    @property
    def output_precision(self) -> int:
        """Get the decimal precision for outputs."""
        return self._config["output"]["precision"]

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key.

        Args:
            key: Configuration key in dot notation (e.g., 'api.timeout')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config.get("api.timeout")
            30
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    @property
    def warning_areas(self) -> list[dict]:
        """Get the parsed list of warning area dicts from warning_areas.yaml."""
        with open(self.warning_areas_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("warning_areas", [])

    @property
    def warning_area_codes(self) -> set[str]:
        """Get set of fwdCode strings for West of England."""
        return {area["fwdCode"] for area in self.warning_areas}

    @property
    def baseline(self) -> BaselineScores | None:
        """Load and return BaselineScores from config, or None if not found."""
        if not self.baseline_path.exists():
            return None
        from fwii.indicator_calculator import BaselineScores

        with open(self.baseline_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return BaselineScores(
            year=data["year"],
            fluvial_score=data["fluvial_score"],
            coastal_score=data["coastal_score"],
            total_score=data["total_score"],
            fluvial_hours=data.get("fluvial_hours", 0.0),
            coastal_hours=data.get("coastal_hours", 0.0),
            fluvial_events=data.get("fluvial_events", 0),
            coastal_events=data.get("coastal_events", 0),
        )

    def save_baseline(self, baseline: BaselineScores) -> None:
        """Save baseline scores to config/baseline_2020.yaml."""
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "year": baseline.year,
            "fluvial_score": baseline.fluvial_score,
            "coastal_score": baseline.coastal_score,
            "total_score": baseline.total_score,
            "fluvial_hours": baseline.fluvial_hours,
            "coastal_hours": baseline.coastal_hours,
            "fluvial_events": baseline.fluvial_events,
            "coastal_events": baseline.coastal_events,
            "description": f"Baseline scores for {baseline.year} (normalised to 100)",
        }
        with open(self.baseline_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @property
    def warning_areas_path(self) -> Path:
        """Get the path to warning_areas.yaml."""
        return self.project_root / "config" / "warning_areas.yaml"

    @property
    def baseline_path(self) -> Path:
        """Get the path to baseline_2020.yaml."""
        return self.project_root / "config" / "baseline_2020.yaml"

    @property
    def data_raw_path(self) -> Path:
        """Get the path to raw data directory."""
        return self.project_root / "data" / "raw"

    @property
    def data_processed_path(self) -> Path:
        """Get the path to processed data directory."""
        return self.project_root / "data" / "processed"

    @property
    def data_outputs_path(self) -> Path:
        """Get the path to outputs directory."""
        return self.project_root / "data" / "outputs"

    def __repr__(self) -> str:
        """String representation of Config."""
        return f"Config(config_path='{self.config_path}')"
