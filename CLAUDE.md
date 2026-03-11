# West of England Flood Warning Intensity Index (FWII)

## Project Overview

Regional Flood Warning Intensity Index for the West of England (Bristol, B&NES, South Gloucestershire, North Somerset). Supports annual climate resilience reporting. Geographic scope: Bristol Avon catchment, North Somerset rivers, Severn Estuary coastal areas.

### Indicator Structure

- **Fluvial (River) Sub-indicator** -- duration-weighted flood warning days for river flooding
- **Coastal/Tidal Sub-indicator** -- duration-weighted flood warning days for tidal flooding
- **Composite FWII** = (Fluvial Index x 0.55) + (Coastal Index x 0.45), normalised to 2020 baseline = 100
- **Surface water flooding** -- reported as "not measurable" (EA does not issue surface water warnings)

---

## Data Source

**Environment Agency Historic Flood Warnings Dataset**
- URL: <https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590>
- Complete record of all Flood Alerts, Flood Warnings, and Severe Flood Warnings from January 2006 to present
- Updated quarterly as downloadable ZIP files (CSV/JSON/ODS)
- Licence: Open Government Licence v3.0

**Key fields**: `fwdCode` (warning area ID), `severityLevel` (1-4), `timeRaised` (ISO 8601), `timeSeverityChanged`, `isTidal` (boolean)

**Real-Time API**: <https://environment.data.gov.uk/flood-monitoring/> -- used by `api_client.py` and `fetch_warning_areas.py` to retrieve flood area definitions. No auth required; 1 req/sec recommended.

---

## Calculation Methodology

### Severity Weights

| Level | Type | Weight |
|-------|------|--------|
| 1 | Severe Flood Warning | x3 |
| 2 | Flood Warning | x2 |
| 3 | Flood Alert | x1 |
| 4 | No Longer in Force | x0 (excluded) |

### Scoring

```
warning_score = duration_hours x severity_weight
Annual_Score  = sum(warning_score) per fluvial/coastal
Normalised    = (Raw_Score / Baseline_2020_Score) x 100
```

### Duration Estimation

The dataset does not provide warning end times. Durations are estimated using default durations (Severe: 12h, Warning: 24h, Alert: 48h) and a 72-hour gap threshold to separate distinct events. See `duration_calculator.py`.

### Severity Mapping

The `data_loader.py` `_normalize_schema` method maps TYPE text to severityLevel using case-insensitive matching. It strips "Update " prefixes and maps legacy "Flood Watch" (pre-2011) to severity 3.

---

## Project Structure

```
fwii/
  config/
    settings.yaml            # API endpoints, weights, thresholds
    warning_areas.yaml        # 18 West of England flood areas (9 fluvial, 9 coastal)
    baseline_2020.yaml        # Baseline scores for normalisation
  src/fwii/
    cli.py                    # CLI entry points (fwii-pipeline, fwii-calculate, fwii-trend)
    config.py                 # Configuration management
    api_client.py             # EA Real-Time API client
    data_fetcher.py           # Historic warnings ZIP download and extraction
    data_loader.py            # Data loading, schema normalisation, WoE filtering
    validators.py             # Data quality validation
    duration_calculator.py    # Warning duration estimation
    indicator_calculator.py   # FWII calculation and baseline normalisation
  scripts/
    fetch_warning_areas.py    # One-time: populate warning_areas.yaml from API
    download_historic_data.py # Download, load, validate, export per-year CSVs
    calculate_fwii.py         # Calculate FWII for a year
    generate_trend_report.py  # Multi-year trend analysis
    run_pipeline.py           # Unified pipeline orchestration
  tests/
    conftest.py
    test_config.py
    test_data_loader.py
    test_duration_calculator.py
    test_indicator_calculator.py
  data/
    raw/                      # Downloaded EA Historic Warnings extracts (ODS/CSV)
    processed/                # Per-year cleaned warnings CSVs
    outputs/                  # fwii_timeseries.csv, JSON results
```

### CLI Entry Points

| Command | Description |
|---------|-------------|
| `uv run fwii-pipeline` | Unified pipeline (download + calculate + trend) |
| `uv run fwii-calculate` | Calculate FWII for a year |
| `uv run fwii-trend` | Generate trend report |

---

## Implementation Notes

- **Timezone handling**: All EA timestamps are UTC. Maintained as UTC internally.
- **Warning area filtering**: `config/warning_areas.yaml` holds the master list of 18 `fwdCode` values. `data_loader.py` filters to these and joins `isTidal` from the config.
- **Duplicate ODS files**: `download_historic_data.py` selects only the latest ODS file (by YYYYMM filename prefix) when multiple exist in `data/raw/`.
- **Data bridges two EA systems**: Floodline Warnings Direct (Jan 2006 -- Apr 2017) and current Flood Warning System (Apr 2017 onwards).

---

## Tool Preferences

- **Package manager**: `uv` exclusively
- **MCP**: context7 for polars syntax reference; MotherDuck for DuckDB queries
- **Linting**: `ruff` per `ruff.toml`
- **Search**: ripgrep (`rg`)
- **Dependencies**: `uv add`/`uv sync` (never edit `pyproject.toml` directly)

---

## References

1. [EA Real-Time Flood Monitoring API](https://environment.data.gov.uk/flood-monitoring/doc/reference)
2. [Historic Flood Warnings Dataset](https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590)
3. [Flood Warning Areas Dataset](https://environment.data.gov.uk/dataset/87e5d78f-d465-11e4-9343-f0def148f590)
4. [DEFRA Outcome Indicator Framework -- F1](https://oifdata.defra.gov.uk/themes/resilience/F1/)
5. [NaFRA 2024](https://www.gov.uk/government/publications/national-assessment-of-flood-and-coastal-erosion-risk-in-england-2024)

# currentDate
Today's date is 2026-03-11.
