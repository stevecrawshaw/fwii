# West of England Flood Warning Intensity Index (FWII)

A duration-weighted composite indicator tracking flood warning activity across the West of England (Bristol, Bath & North East Somerset, South Gloucestershire, North Somerset). Provides annual monitoring to support climate resilience reporting under the West of England outcomes framework.

## What FWII Measures

The FWII combines two sub-indicators into a single index normalised to a 2020 baseline of 100:

| Component | Weight | Source |
|-----------|--------|--------|
| Fluvial (river) flood warnings | 55% | Environment Agency warning areas on Bristol Avon, Frome, North Somerset rivers |
| Coastal/tidal flood warnings | 45% | Severn Estuary and Bristol Channel warning areas |

Each warning is scored by **duration (hours) x severity weight** (Severe=3, Warning=2, Alert=1), then normalised against the 2020 baseline year.

**Surface water flooding is not included** -- the Environment Agency does not operate a surface water warning system.

## Results (2020--2025)

| Year | Composite FWII | Fluvial Index | Coastal Index | Total Warnings |
|------|----------------|---------------|---------------|----------------|
| 2020 | **100.0** (baseline) | 100.0 | 100.0 | 95 |
| 2021 | **39.6** | 44.6 | 33.5 | 28 |
| 2022 | **29.3** | 31.9 | 26.1 | 23 |
| 2023 | **101.2** | 150.6 | 40.8 | 54 |
| 2024 | **167.0** | 253.2 | 61.7 | 99 |
| 2025 | **69.6** | 105.0 | 26.4 | 37 |

The FWII peaked at 167.0 in 2024, driven by a 153% rise in river flooding warnings while coastal warnings remained below baseline. By 2025 activity fell back to 69.6, below the 2020 baseline. The overall pattern shows a shift from coastal-dominated (2020) to fluvial-dominated (2023--2025) flood warning activity.

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Install

```bash
git clone <repository-url>
cd fwii
uv sync
```

### Full Pipeline (download, calculate, report)

```bash
# Run everything for 2020-2024
uv run fwii-pipeline 2020 2024 --full

# Single year
uv run fwii-pipeline 2024 --full

# Force re-download
uv run fwii-pipeline 2020 2024 --full --force
```

### Individual Steps

```bash
# 1. Fetch warning area definitions (one-time setup)
uv run python scripts/fetch_warning_areas.py

# 2. Download and process historic warnings
uv run python scripts/download_historic_data.py 2024          # Single year
uv run python scripts/download_historic_data.py 2020 2024     # Range

# 3. Calculate FWII for a year
uv run python scripts/calculate_fwii.py 2024
uv run python scripts/calculate_fwii.py 2020 --save-baseline  # Recalculate baseline

# 4. Generate trend report (all available years from 2020)
uv run python scripts/generate_trend_report.py
```

### CLI Commands

Three entry points are available after `uv sync`:

| Command | Description |
|---------|-------------|
| `uv run fwii-pipeline` | Unified pipeline (download + calculate + trend) |
| `uv run fwii-calculate` | Calculate FWII for a year |
| `uv run fwii-trend` | Generate trend report |

## Project Structure

```
fwii/
  config/
    settings.yaml            # API endpoints, weights, thresholds
    warning_areas.yaml        # 18 West of England flood areas (9 fluvial, 9 coastal)
    baseline_2020.yaml        # Baseline scores for normalisation
  src/fwii/
    cli.py                    # CLI entry points
    config.py                 # Configuration management
    api_client.py             # EA API client
    data_fetcher.py           # Historic warnings download
    data_loader.py            # Data loading and schema normalisation
    validators.py             # Data quality validation
    duration_calculator.py    # Warning duration estimation
    indicator_calculator.py   # FWII calculation and baseline normalisation
  scripts/
    fetch_warning_areas.py    # One-time: populate warning_areas.yaml
    download_historic_data.py # Download, load, validate, store warnings
    calculate_fwii.py         # Calculate FWII for a year
    generate_trend_report.py  # Multi-year trend analysis
    run_pipeline.py           # Unified pipeline
  data/
    raw/                      # Downloaded EA Historic Warnings extracts
    processed/                # Per-year cleaned warnings CSVs
    outputs/                  # fwii_timeseries.csv
```

## Calculation Method

### Pipeline Stages

1. **Download** -- Fetch Historic Flood Warnings ZIP from EA API
2. **Load** -- Extract CSV/JSON/ODS, normalise schema, filter to 18 West of England warning areas
3. **Validate** -- Check timestamps, severity levels, geographic boundaries
4. **Calculate** -- Estimate warning durations, apply severity weights, sum by fluvial/coastal
5. **Normalise** -- Divide by 2020 baseline scores, multiply by 100
6. **Compose** -- FWII = (Fluvial Index x 0.55) + (Coastal Index x 0.45)

### Severity Weights

| Level | Type | Weight |
|-------|------|--------|
| 1 | Severe Flood Warning | x3 |
| 2 | Flood Warning | x2 |
| 3 | Flood Alert | x1 |
| 4 | No Longer in Force | x0 (excluded) |

### Duration Estimation

The EA dataset does not provide warning end times. Durations are estimated using default durations (Severe: 12h, Warning: 24h, Alert: 48h) and a 72-hour gap threshold to separate distinct events.

### 2020 Baseline

| Component | Score | Events |
|-----------|-------|--------|
| Fluvial | 1,051.65 | 23 |
| Coastal | 2,410.57 | 72 |

## Data Source

**Environment Agency Historic Flood Warnings Dataset**
- URL: https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590
- Coverage: January 2006 to present
- Updates: Quarterly
- Licence: [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)

The dataset tracks 18 flood warning areas across the West of England (Wessex region prefix 112), comprising 9 fluvial and 9 coastal areas.

## Caveats

- **Warning activity, not actual flooding.** Warnings are precautionary; flood defences may prevent flooding despite warnings. Flooding may also occur without warnings.
- **No surface water flooding.** Surface water affects more properties nationally (3.4 million) than river and coastal combined (2.7 million). The EA does not issue surface water warnings.
- **No groundwater flooding.**
- **Geographic gaps.** Only 18 defined warning areas are monitored. Flooding outside these areas is not captured.
- **Duration estimates are heuristic.** Default durations and gap thresholds may over- or underestimate actual warning periods.
- **Warning area boundaries change.** The EA updates boundaries quarterly, which may affect comparisons.

## Technology

- **Python 3.13** with Polars for data processing
- **httpx** for EA API calls
- **PyYAML** for configuration
- **uv** for package management

## Licence

- Code: MIT Licence
- Data: [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)

## References

1. [EA Real-Time Flood Monitoring API](https://environment.data.gov.uk/flood-monitoring/doc/reference)
2. [Historic Flood Warnings Dataset](https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590)
3. [Flood Warning Areas Dataset](https://environment.data.gov.uk/dataset/87e5d78f-d465-11e4-9343-f0def148f590)
4. [DEFRA Outcome Indicator Framework -- F1: Disruption from Flooding](https://oifdata.defra.gov.uk/themes/resilience/F1/)
5. [National Assessment of Flood and Coastal Erosion Risk (NaFRA) 2024](https://www.gov.uk/government/publications/national-assessment-of-flood-and-coastal-erosion-risk-in-england-2024)
