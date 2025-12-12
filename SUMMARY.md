# West of England Flood Warning Intensity Index (FWII)

## Technical Summary Report

**Version:** 1.0
**Date:** December 2024
**Period Covered:** 2020-2024
**Geographic Scope:** Bristol, Bath and North East Somerset, South Gloucestershire, North Somerset

---

## Executive Summary

The **Flood Warning Intensity Index (FWII)** is a duration-weighted composite indicator that tracks flood warning activity as a proxy for flooding events in the West of England. It provides annual monitoring to support climate resilience reporting to government under the West of England outcomes framework.

### Key Definition

**FWII measures the intensity of flood warning activity** by combining:

- **55% River (Fluvial) Flood Warnings** - Duration-weighted flood alerts and warnings for river flooding
- **45% Coastal/Tidal Flood Warnings** - Duration-weighted alerts and warnings for tidal/coastal flooding
- **Baseline normalization to 2020 = 100** - Enables year-on-year comparability

### Key Finding (2020-2024)

**The FWII increased by 67% from 2020 to 2024** (100.0 → 167.0), driven entirely by a 153% increase in river flooding warnings. This represents the highest flood warning intensity on record for the region, with a notable pattern shift from coastal-dominated flooding (2020) to fluvial-dominated flooding (2024).

---

## 1. Indicator Selection Rationale

### Why Flood Warning Activity?

The FWII was designed to measure **actual flooding events** (not risk assessments or near-misses) using Environment Agency flood warning data as a proxy. This approach was selected for several key advantages:

#### Advantages of Warning-Based Indicator

1. **Rigorous Monitoring**: Environment Agency operates a comprehensive, continuously monitored flood warning system covering defined geographic areas with established protocols

2. **Open Data**: Complete historical dataset available under Open Government Licence v3.0, ensuring transparency and reproducibility

3. **Annual Comparability**: Consistent methodology and warning area definitions enable robust year-on-year comparison

4. **Meaningful to Decision-Makers**: Flood warnings are familiar to the public and policymakers, making the indicator interpretable and actionable

5. **Real-Time Availability**: Quarterly dataset updates enable timely annual reporting

#### Alignment with National Framework

The FWII aligns with the DEFRA Outcome Indicator Framework for climate resilience:

- **F1: Disruption from Flooding** - Tracks flood events that cause community disruption
- **F2: Communities Resilient to Flooding** - Supports assessment of flood preparedness and response

By measuring warning activity, the FWII provides an objective, data-driven indicator of changing flood patterns in the West of England that complements national-level assessments.

#### Baseline Period Selection: 2020

**2020 was selected as the baseline year** for several reasons:

1. **Recent Baseline**: Reflects contemporary climate conditions and flood risk patterns
2. **Data Availability**: Complete, quality-checked dataset available from 2020 onwards
3. **System Stability**: Post-2017 Flood Warning System (unified system replacing legacy Floodline Warnings Direct)
4. **Normalization to 100**: Setting 2020 = 100 enables intuitive interpretation (e.g., 167.0 in 2024 = 67% increase)

### Surface Water Exclusion

**Surface water flooding is NOT included** in the FWII due to a fundamental technical limitation: the Environment Agency does not operate a surface water flood warning system.

**Why Surface Water Cannot Be Measured:**

- Surface water flooding is sporadic and unpredictable (caused by intense, localized rainfall)
- Insufficient lead time for effective warning systems
- Affects more properties nationally (3.4 million) than river and coastal flooding combined (2.7 million)

**Alternative Data Source**: Section 19 flood investigation reports from Lead Local Flood Authorities (LLFAs) provide local records of significant surface water events, but are not systematically tracked or quantified.

**Impact on Indicator**: The FWII understates total flood risk in the region. An increase in FWII does not mean surface water flooding has decreased, and a decrease does not mean total flooding has improved.

---

## 2. Weighting Methodology & Rationale

### Composite Formula

The FWII combines fluvial (river) and coastal (tidal) sub-indicators using weighted averaging:

```
FWII = (Fluvial Index × 0.55) + (Coastal Index × 0.45)
```

### Weighting Rationale

#### Fluvial (River) Flooding: 55% Weight

- **Rationale**: Based on relative **properties at risk** from river flooding in the West of England
- The Bristol Avon catchment and North Somerset rivers pose the dominant inland flood risk
- Major urban areas (Bristol, Bath) are adjacent to river systems
- Historical flood events (e.g., Bath 2012, Bristol 2014) demonstrate significant river flood impact

#### Coastal (Tidal) Flooding: 45% Weight

- **Rationale**: Reflects coastal and tidal flood risk along the **Severn Estuary and Bristol Channel**
- Low-lying coastal areas (Avonmouth, Severn Beach, North Somerset coast) vulnerable to tidal surges
- Storm surge risk amplified by high astronomical tides and climate change
- Industrial/commercial assets concentrated in coastal areas

#### Weight Refinement

The 55/45 split is based on expert assessment of regional flood risk. These weights **may be refined** using data from:

- **NaFRA (National Assessment of Flood and Coastal Erosion Risk)** - Provides regional breakdowns of properties at risk by flood source
- **Section 19 Flood Investigation Reports** - Local evidence of actual flood impacts
- **Long-term FWII trends** - If one component consistently dominates, weights may be adjusted

### Duration-Weighted Scoring

Warnings are scored based on **severity × duration** to reflect both intensity and persistence of flood risk:

#### Severity Weights

| Severity Level | Type | Weight | Rationale |
|----------------|------|--------|-----------|
| Level 1 | Severe Flood Warning | ×3 | Danger to life, immediate evacuation required |
| Level 2 | Flood Warning | ×2 | Flooding expected, immediate action needed |
| Level 3 | Flood Alert | ×1 | Flooding possible, be prepared |
| Level 4 | Warning No Longer in Force | ×0 | Excluded from calculation |

#### Calculation Formula

For each warning event:

```
Warning Score = Duration (hours) × Severity Weight
```

Annual sub-indicators:

```
Fluvial Score = Σ (warning_score for all fluvial warnings in year)
Coastal Score = Σ (warning_score for all coastal warnings in year)
```

**Example**: A Flood Warning (level 2) lasting 24 hours scores **24 × 2 = 48 points**. A Severe Flood Warning (level 1) lasting 12 hours scores **12 × 3 = 36 points**.

### Baseline Normalization

Each sub-indicator is normalized to the 2020 baseline:

```
Fluvial Index = (Fluvial Score / Baseline Fluvial Score 2020) × 100
Coastal Index = (Coastal Score / Baseline Coastal Score 2020) × 100
```

**2020 Baseline Scores:**

- Fluvial: 1,051.65 weighted hours
- Coastal: 2,410.57 weighted hours
- Total: 3,462.22 weighted hours

This normalization ensures that:

- 2020 indices = 100.0 for both fluvial and coastal
- Values > 100 indicate higher warning activity than baseline
- Values < 100 indicate lower warning activity than baseline

---

## 3. Implementation Overview

### Code Architecture

The FWII is implemented in **Python 3.13** with a modular architecture totaling **2,522 lines of code** across 8 core modules.

#### Core Modules

| Module | Lines | Purpose |
|--------|-------|---------|
| `indicator_calculator.py` | 252 | Main FWII calculation engine, baseline normalization |
| `duration_calculator.py` | 288 | Warning duration calculation using heuristic approach |
| `data_loader.py` | 446 | Historic warnings data loading, schema normalization |
| `db_storage.py` | 470 | DuckDB storage layer for processed warnings |
| `validators.py` | 420 | Data quality validation and reporting |
| `data_fetcher.py` | 249 | Environment Agency API data fetching |
| `api_client.py` | 215 | HTTP client for flood monitoring API |
| `config.py` | 174 | Configuration management (YAML) |

#### Technology Stack

- **Language**: Python 3.13
- **Data Processing**: Polars (high-performance DataFrame library, preferred over Pandas)
- **Storage**: DuckDB (embedded analytical database)
- **HTTP Client**: httpx (async-capable HTTP library)
- **Configuration**: PyYAML
- **Package Management**: uv (fast Python package installer)

### Calculation Pipeline

The FWII is calculated through a **6-stage pipeline**:

```
1. DOWNLOAD
   ├─ Fetch Historic Flood Warnings Dataset from EA API
   └─ Extract to data/raw/

2. LOAD & NORMALIZE
   ├─ Read CSV/JSON/ODS files
   ├─ Normalize schema variations (DATE→timeRaised, CODE→fwdCode, TYPE→severity)
   ├─ Parse ISO 8601 timestamps to UTC
   └─ Filter to West of England areas only (18 warning areas)

3. VALIDATE
   ├─ Check for missing timestamps
   ├─ Validate severity levels (1-4 range)
   ├─ Verify geographic boundaries
   └─ Generate quality report (data_quality_report_{year}.json)

4. STORE
   ├─ Initialize DuckDB database schema
   └─ Insert warnings into flood_warnings table

5. CALCULATE DURATIONS & SCORES
   ├─ Load warnings for specific year
   ├─ Join with warning_areas.yaml for isTidal classification
   ├─ Calculate durations using heuristic approach
   ├─ Apply severity weights
   └─ Sum scores by fluvial/coastal

6. NORMALIZE & COMPOSE
   ├─ Normalize to 2020 baseline (→ indices)
   ├─ Calculate composite FWII (55% fluvial + 45% coastal)
   └─ Export results (CSV, JSON, console report)
```

### Duration Calculation Logic

**Challenge**: The EA dataset does not provide explicit warning end times, only timestamps when warnings are raised or updated.

**Solution**: A heuristic approach estimates duration based on warning gaps and default durations:

#### Configuration

```python
Default Durations (hours):
  - Severe Flood Warning (level 1): 12 hours
  - Flood Warning (level 2): 24 hours
  - Flood Alert (level 3): 48 hours

Maximum Gap Threshold: 72 hours (to separate distinct events)
```

#### Algorithm

For each warning area (`fwdCode`):

1. **Sort warnings chronologically** by `timeRaised`
2. **Calculate gap to next warning** in same area
3. **Estimate duration**:
   - If gap < max_gap (72h): `duration = min(gap, default_duration)`
   - If gap > max_gap: `duration = default_duration` (treat as separate event)
   - If message type is "Update": `duration = gap` (continuation of same event)
   - If no next warning: `duration = default_duration`

4. **Handle severity escalation**: If a warning escalates (Alert → Warning → Severe), each severity level is scored separately based on time at that level

**Example**:

```
09:00 - Alert raised (level 3)
14:00 - Escalated to Warning (level 2)
18:00 - Escalated to Severe (level 1)
22:00 - De-escalated to Warning (level 2)
06:00 - De-escalated to Alert (level 3)
12:00 - Warning removed (level 4)

Calculation:
- Alert hours: 5h (09:00-14:00) + 6h (06:00-12:00) = 11h × 1 = 11 points
- Warning hours: 4h (14:00-18:00) + 8h (22:00-06:00) = 12h × 2 = 24 points
- Severe hours: 4h (18:00-22:00) = 4h × 3 = 12 points
Total score: 47 points
```

### Baseline Normalization Implementation

The system loads baseline scores from `config/baseline_2020.yaml`:

```yaml
year: 2020
fluvial_score: 1051.65
coastal_score: 2410.57
total_score: 3462.22
fluvial_hours: 1051.65
coastal_hours: 2338.57
fluvial_events: 23
coastal_events: 72
```

Normalization formula (in `indicator_calculator.py`):

```python
fluvial_index = (fluvial_score / baseline.fluvial_score) * 100
coastal_index = (coastal_score / baseline.coastal_score) * 100
composite_fwii = (fluvial_index * 0.55) + (coastal_index * 0.45)
```

### Data Structures

**NormalizedIndicators** dataclass (returned by `calculate_indicators()`):

```python
@dataclass
class NormalizedIndicators:
    year: int
    fluvial_score_raw: float        # Unweighted fluvial score
    coastal_score_raw: float        # Unweighted coastal score
    total_score_raw: float          # Total unweighted score
    fluvial_index: float            # Normalized to 2020 baseline
    coastal_index: float            # Normalized to 2020 baseline
    composite_fwii: float           # Weighted composite (55/45)
    fluvial_hours: float            # Total fluvial warning hours
    coastal_hours: float            # Total coastal warning hours
    fluvial_events: int             # Count of fluvial warnings
    coastal_events: int             # Count of coastal warnings
    total_events: int               # Total warning count
    severe_warnings: int            # Count of level 1 warnings
    flood_warnings: int             # Count of level 2 warnings
    flood_alerts: int               # Count of level 3 warnings
```

---

## 4. Source Data & Geographic Coverage

### Primary Data Source

**Environment Agency Historic Flood Warnings Dataset**

- **URL**: <https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590>
- **Description**: Complete record of all Flood Alerts, Flood Warnings, and Severe Flood Warnings issued by the Environment Agency
- **Coverage**: January 2006 to present
- **Update Frequency**: Quarterly
- **Format**: Downloadable ZIP files containing CSV/JSON
- **Licence**: Open Government Licence v3.0

**Key Data Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `fwdCode` | String | Flood warning area identifier (e.g., 112WAFTLBA) |
| `severityLevel` | Integer | 1=Severe, 2=Warning, 3=Alert, 4=No Longer in Force |
| `severity` | String | Human-readable severity description |
| `timeRaised` | ISO 8601 | UTC timestamp when warning was issued |
| `timeSeverityChanged` | ISO 8601 | Timestamp when severity changed (optional) |
| `isTidal` | Boolean | true=coastal/tidal, false=fluvial/river |
| `label` | String | Human-readable warning area name |
| `county` | String | County name(s) |
| `riverOrSea` | String | River or sea name |

**Important Notes**:

- Dataset bridges two systems: Floodline Warnings Direct (2006-2017) and current Flood Warning System (2017-present)
- Schema variations exist across years, requiring normalization
- Surface water warnings are NOT included (EA does not provide surface water warnings)

### West of England Warning Areas

The FWII tracks **18 flood warning areas** covering the West of England region, configured in `config/warning_areas.yaml`.

#### Geographic Distribution

| Local Authority | Warning Areas | Fluvial | Coastal |
|-----------------|---------------|---------|---------|
| Bristol | 5 | 3 | 2 |
| Bath and North East Somerset | 5 | 5 | 0 |
| South Gloucestershire | 6 | 3 | 3 |
| North Somerset | 8 | 4 | 4 |
| **Total** | **18** | **9** | **9** |

**Note**: Some warning areas span multiple counties (e.g., Lower Bristol Avon area covers Bristol, Bath & NES, South Gloucestershire, and North Somerset).

#### Fluvial (River) Warning Areas (9 areas)

All fluvial areas have `isTidal: false` in configuration:

1. **Bristol Frome catchment** (`112WAFTBFC`)
   - Rivers: Bristol Frome, Ladden Brook, River Trym
   - Coverage: Chipping Sodbury to Bristol Floating Harbour

2. **Lower Bristol Avon area** (`112WAFTLBA`)
   - Rivers: Bristol Avon, River Boyd, By Brook, Brislington Brook
   - Coverage: Multi-county (Bristol, Bath & NES, North Somerset, South Glos, Wiltshire)

3. **Upper Bristol Avon area** (`112WAFTUBA`)
   - River: Bristol Avon and tributaries
   - Coverage: Malmesbury, Dauntsey, Chippenham, Calne

4. **Midford Brook catchment** (`112WAFTMBC`)
   - Rivers: River Cam, Wellow Brook, Midford Brook
   - Coverage: Bath and North East Somerset

5. **Wellow Brook and River Somer** (`112FWFWEL11A`)
   - Rivers: Wellow Brook, River Somer
   - Coverage: Midsomer Norton, Radstock

6. **Bristol Frome (Stapleton to Floating Harbour)** (`112FWFBFR20C`)
   - River: Bristol Frome
   - Coverage: Eastville, Baptist Mills

7. **Brislington Brook** (`112FWFBRI10C`)
   - River: Brislington Brook
   - Coverage: Bristol urban area

8. **North Somerset area** (`112WAFTNSA`)
   - Rivers: Congresbury Yeo, Cheddar Yeo, Axe, Banwell
   - Coverage: North Somerset rivers

9. **Somerset Frome area** (`112WAFTSFA`)
   - Rivers: Somerset Frome, Mells, Whatley Brook, Nunney Brook
   - Coverage: Bath & NES, Somerset border

#### Coastal/Tidal Warning Areas (9 areas)

All coastal areas have `isTidal: true` in configuration:

1. **Severn Estuary at Severn Beach and Pilning** (`112FWTSEV03`)
   - Sea: Severn Estuary
   - Coverage: Redwick, Pilning, Avonmouth, Western Approach Distribution Centres

2. **Severn Estuary at Severn Beach** (`112WATSVN1`)
   - Sea: Severn Estuary
   - Coverage: Severn Beach, New Passage, Pilning

3. **Severn Estuary at Oldbury-on-Severn, Northwick and Avonmouth** (`112WATSVN2`)
   - Sea: Severn Estuary
   - Coverage: Oldbury-on-Severn, Northwick, Avonmouth, Aust

4. **Somerset coast at Clevedon** (`112FWTCLE02`)
   - Sea: Bristol Channel
   - Coverage: Marshalls Field area, Clevedon

5. **Somerset coast at Clevedon (Alert)** (`112WATSOM4`)
   - Sea: Bristol Channel
   - Coverage: Gullhouse Point to Marine Parade

6. **Somerset coast at Kewstoke and Sand Bay** (`112FWTKEW02`)
   - Sea: Bristol Channel
   - Coverage: Beach Road area, Kewstoke, Sand Point

7. **Somerset coast at Kingston Seymour** (`112FWTKIN01`)
   - Sea: Bristol Channel
   - Coverage: Sand Point to Gullhouse Point, Ham Lane

8. **Somerset coast at Dunster Beaches, Blue Anchor, Steart, Stolford and Brean** (`112WATSOM2`)
   - Sea: Bristol Channel
   - Coverage: Multiple coastal areas (Note: Some locations outside core West of England)

9. **Somerset coast at Minehead, Bridgwater, Burnham-on-Sea and Uphill to Kingston Seymour** (`112WATSOM3`)
   - Sea: Bristol Channel
   - Coverage: Extensive coastal coverage (Note: Some locations outside core West of England)

#### Area Type Prefixes

All warning areas use the **Wessex region prefix: 112**

- **WAT**: Flood Alert Areas (early notification - flooding possible)
- **FW / FWT**: Flood Warning Areas (immediate action - flooding expected)

**Example fwdCode breakdown**: `112WAFTLBA`

- `112` = Wessex region
- `WAF` = Flood Alert
- `T` = River/Tidal designation
- `LBA` = Lower Bristol Avon area

---

## 5. How to Run the Code

### Prerequisites

**System Requirements**:

- Python 3.13 or higher
- `uv` package manager (fast Python package installer and resolver)
- Git

**Install uv** (if not already installed):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Initial Setup

Clone the repository and install dependencies:

```bash
# Clone repository
git clone <repository-url>
cd fwii

# Install dependencies using uv
uv sync
```

This creates a virtual environment and installs:

- polars (data processing)
- httpx (HTTP client)
- pyyaml (configuration)
- duckdb (database)
- odfpy (ODS file support)

### Step 1: Fetch Flood Warning Areas (One-Time Setup)

Populate `config/warning_areas.yaml` with the 18 West of England warning areas:

```bash
uv run python scripts/fetch_warning_areas.py
```

**Output**:

```
Fetching flood warning areas for West of England...
  ✓ City of Bristol: 5 areas
  ✓ Bath and North East Somerset: 5 areas
  ✓ South Gloucestershire: 6 areas
  ✓ North Somerset: 8 areas

Total areas: 18 (9 fluvial, 9 coastal)
Saved to: config/warning_areas.yaml
```

### Step 2: Download & Process Historical Data

Download flood warnings from Environment Agency Historic Warnings Dataset:

```bash
# Download data for a specific year
uv run python scripts/download_historic_data.py 2024

# Download a range of years
uv run python scripts/download_historic_data.py 2020 2024

# Force re-download (bypass cache)
uv run python scripts/download_historic_data.py 2024 --force
```

**This script performs 4 stages**:

1. **Download**: Fetches Historic Flood Warnings ZIP from EA API → `data/raw/`
2. **Load**: Extracts and normalizes CSV/JSON/ODS files, filters to West of England areas
3. **Validate**: Runs quality checks, generates `data_quality_report_{year}.json`
4. **Store**: Saves processed warnings to DuckDB (`data/fwii.duckdb`) and CSV (`data/processed/warnings_{year}.csv`)

**Example output**:

```
====================================================================================================
STAGE 1: DOWNLOADING HISTORIC FLOOD WARNINGS FOR 2024
====================================================================================================
Downloading from: https://environment.data.gov.uk/...
Downloaded: 45.2 MB
Extracted to: data/raw/2024/

====================================================================================================
STAGE 2: LOADING AND FILTERING DATA
====================================================================================================
Loading warnings from: data/raw/2024/HistoricFloodWarnings.csv
Filtering to West of England (18 warning areas)...
  Total warnings: 12,456
  West of England: 99 (0.8%)

====================================================================================================
STAGE 3: VALIDATING DATA QUALITY
====================================================================================================
Running validation checks...
  ✓ Schema validation: PASSED
  ✓ Timestamp completeness: PASSED
  ✓ Severity levels: PASSED
  ✓ Geographic boundaries: PASSED
Quality report saved: data/processed/data_quality_report_2024.json

====================================================================================================
STAGE 4: STORING PROCESSED DATA
====================================================================================================
Saving to DuckDB: data/fwii.duckdb
Saving to CSV: data/processed/warnings_2024.csv
  Records stored: 99

Pipeline complete for 2024
```

### Step 3: Calculate FWII for a Year

Calculate the FWII for a specific year (normalized to 2020 baseline):

```bash
# Calculate FWII for 2024
uv run python scripts/calculate_fwii.py 2024

# Recalculate and save 2020 baseline (if needed)
uv run python scripts/calculate_fwii.py 2020 --save-baseline
```

**Example output**:

```
====================================================================================================
CALCULATING FLOOD WARNING INTENSITY INDEX (FWII) FOR 2024
====================================================================================================

Loading warning data for 2024...
  Loaded: 99 warnings
  Fluvial (isTidal=false): 56
  Coastal (isTidal=true): 43

Calculating indicators...

====================================================================================================
RESULTS FOR 2024
====================================================================================================

RAW SCORES (Duration-Weighted)
----------------------------------------------------------------------------------------------------
  Fluvial Score:      2663.0  (56 events, 2663.0 hours)
  Coastal Score:      1487.5  (43 events, 1443.5 hours)
  Total Score:        4150.5  (99 events)

NORMALIZED INDICATORS (Baseline 2020 = 100)
----------------------------------------------------------------------------------------------------
  Fluvial Index:       253.2
  Coastal Index:        61.7

  COMPOSITE FWII:      167.0  (55% fluvial + 45% coastal)

WARNING COUNTS BY SEVERITY
----------------------------------------------------------------------------------------------------
  Severe Flood Warnings (Level 1):  0
  Flood Warnings (Level 2):         4
  Flood Alerts (Level 3):           95

INTERPRETATION
----------------------------------------------------------------------------------------------------
  2024 shows 67.0% HIGHER flood warning activity than 2020 baseline.
  This is driven by a 153.2% increase in fluvial warnings.
  Coastal warnings decreased by 38.3%.

====================================================================================================
CALCULATION COMPLETE
====================================================================================================
```

### Step 4: Generate Trend Report (2020-2024)

Generate a comprehensive 5-year comparison report:

```bash
uv run python scripts/generate_trend_report.py
```

**Output**: Console report + CSV export

**Console output (excerpt)**:

```
====================================================================================================
WEST OF ENGLAND FLOOD WARNING INTENSITY INDEX (FWII)
TREND REPORT 2020-2024
====================================================================================================

ANNUAL SUMMARY
----------------------------------------------------------------------------------------------------
┌──────┬───────────────┬───────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ year ┆ total_warning ┆ fluvial_warni ┆ coastal_warn ┆ fluvial_inde ┆ coastal_inde ┆ composite_fw │
│      ┆ s             ┆ ngs           ┆ ings         ┆ x            ┆ x            ┆ ii           │
├──────┼───────────────┼───────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ 2020 ┆ 95            ┆ 23            ┆ 72           ┆ 100.0        ┆ 100.0        ┆ 100.0        │
│ 2021 ┆ 28            ┆ 10            ┆ 18           ┆ 44.6         ┆ 33.5         ┆ 39.6         │
│ 2022 ┆ 23            ┆ 7             ┆ 16           ┆ 31.9         ┆ 26.1         ┆ 29.3         │
│ 2023 ┆ 54            ┆ 33            ┆ 21           ┆ 150.6        ┆ 40.8         ┆ 101.2        │
│ 2024 ┆ 99            ┆ 56            ┆ 43           ┆ 253.2        ┆ 61.7         ┆ 167.0        │
└──────┴───────────────┴───────────────┴──────────────┴──────────────┴──────────────┴──────────────┘

TRENDS & INSIGHTS
----------------------------------------------------------------------------------------------------

Year-on-Year Changes in Composite FWII:
  2020 → 2021: ↓  60.4 points ( -60.4%)
  2021 → 2022: ↓  10.3 points ( -26.0%)
  2022 → 2023: ↑  71.9 points (+245.4%)
  2023 → 2024: ↑  65.8 points ( +65.0%)

5-Year Statistics:
  Average FWII: 87.4
  Median FWII: 100.0
  Range: 29.3 - 167.0
  Coefficient of Variation: 59.8%
```

**CSV output**: `data/outputs/fwii_timeseries.csv`

```csv
year,total_warnings,fluvial_warnings,coastal_warnings,fluvial_index,coastal_index,composite_fwii
2020,95,23,72,100.0,100.0,100.0
2021,28,10,18,44.6,33.5,39.6
2022,23,7,16,31.9,26.1,29.3
2023,54,33,21,150.6,40.8,101.2
2024,99,56,43,253.2,61.7,167.0
```

### File Outputs

After running the pipeline, the following files are generated:

**Configuration**:

- `config/warning_areas.yaml` - 18 West of England warning areas
- `config/baseline_2020.yaml` - Baseline scores for normalization

**Raw Data**:

- `data/raw/{year}/` - Downloaded EA Historic Warnings ZIP extracts

**Processed Data**:

- `data/processed/warnings_{year}.csv` - Cleaned, filtered warnings for West of England
- `data/processed/data_quality_report_{year}.json` - Validation results

**Database**:

- `data/fwii.duckdb` - DuckDB database with `flood_warnings` table

**Outputs**:

- `data/outputs/fwii_timeseries.csv` - Multi-year time series (importable to spreadsheets)
- Console output - Detailed annual reports

### Validation & Quality Assurance

Run the comprehensive validation suite:

```bash
# Run all validation phases
uv run /validate
```

This runs 9 validation phases:

1. Code quality & linting (Ruff)
2. Code formatting check
3. Configuration validation
4. API connectivity test
5. Data presence & integrity
6. End-to-end pipeline test
7. Calculation accuracy verification
8. Cross-year consistency
9. Data quality checks

---

## 6. Results Summary (2020-2024)

### FWII Time Series

| Year | Composite FWII | Fluvial Index | Coastal Index | Total Warnings | Fluvial Warnings | Coastal Warnings |
|------|----------------|---------------|---------------|----------------|------------------|------------------|
| 2020 | **100.0** (baseline) | 100.0 | 100.0 | 95 | 23 | 72 |
| 2021 | **39.6** (-60.4%) | 44.6 | 33.5 | 28 | 10 | 18 |
| 2022 | **29.3** (-26.1%) | 31.9 | 26.1 | 23 | 7 | 16 |
| 2023 | **101.2** (+245%) | 150.6 | 40.8 | 54 | 33 | 21 |
| 2024 | **167.0** (+65.0%) | 253.2 | 61.7 | 99 | 56 | 43 |

### Key Findings

#### 1. Overall 5-Year Trend: Significant Increase

**FWII increased by 67.0 points (+67%) from 2020 to 2024**, indicating substantially higher flood warning activity than the baseline year.

- **2020 (Baseline)**: 100.0 - High warning activity (95 warnings, coastal-dominated)
- **2021-2022**: Sharp decline to lowest recorded levels (29.3 in 2022)
- **2023-2024**: Dramatic spike to highest recorded levels (167.0 in 2024)

**5-Year Statistics**:

- Average FWII: 87.4
- Median FWII: 100.0
- Range: 29.3 - 167.0
- Coefficient of Variation: 59.8% (high year-to-year variability)

#### 2. Pattern Shift: Coastal to Fluvial Dominance

**2020 (Baseline)**: Coastal-dominated

- 72 coastal warnings (76% of total)
- 23 fluvial warnings (24% of total)
- Coastal score 2.3× higher than fluvial

**2024**: Fluvial-dominated

- 56 fluvial warnings (57% of total)
- 43 coastal warnings (43% of total)
- Fluvial score 1.8× higher than coastal

This represents a **fundamental shift in flood risk patterns** from tidal/coastal sources to inland river sources in the West of England.

#### 3. Component Analysis

**Fluvial (River) Flooding**:

- 2024 index: **253.2** (153% above baseline)
- **Highest fluvial activity on record**
- Progressive increase from 2022 low (31.9) through 2023 (150.6) to 2024 (253.2)
- Suggests persistent or increasing river flood risk driven by:
  - Increased winter rainfall
  - Saturated catchments
  - Climate change impacts on river systems

**Coastal (Tidal) Flooding**:

- 2024 index: **61.7** (38% below baseline)
- **Remained below baseline every year 2021-2024**
- 2020 was an anomalous high-coastal-activity year
- 2024 shows partial recovery from 2022 low (26.1)
- Lower coastal activity may reflect:
  - Fewer severe storm surge events
  - Timing of astronomical tides
  - Improved coastal flood defenses

#### 4. Year-on-Year Changes

| Period | Change | Interpretation |
|--------|--------|----------------|
| 2020 → 2021 | -60.4 points (-60%) | Sharp decline following high-activity baseline year |
| 2021 → 2022 | -10.3 points (-26%) | Continued low activity, lowest year on record |
| 2022 → 2023 | +71.9 points (+245%) | Dramatic spike, driven by 150% increase in fluvial warnings |
| 2023 → 2024 | +65.8 points (+65%) | Continued increase, highest year on record |

The **2023-2024 upward trend** is notable and warrants ongoing monitoring to determine if this represents:

- A new higher baseline (climate change signal)
- Short-term variability (weather patterns)
- Multi-year cycle (requires longer time series to assess)

#### 5. Warning Severity Distribution

Across all years, **Flood Alerts (level 3) dominate**:

- 2020: 92 Alerts, 3 Warnings, 0 Severe (97% Alerts)
- 2024: 95 Alerts, 4 Warnings, 0 Severe (96% Alerts)

**No Severe Flood Warnings (level 1)** were issued in the West of England 2020-2024.

This suggests:

- Most events were managed at Alert/Warning levels
- Flood defenses and warning systems effectively limited escalation to Severe level
- The region has not experienced catastrophic flooding requiring evacuations

### Interpretation Guidance

**FWII Value Ranges**:

| FWII Range | Interpretation | Example Years |
|------------|----------------|---------------|
| < 50 | Very low flood warning activity (< half of baseline) | 2021 (39.6), 2022 (29.3) |
| 50-80 | Low flood warning activity | - |
| 80-120 | Similar to baseline (within ±20%) | 2020 (100.0), 2023 (101.2) |
| 120-150 | Elevated flood warning activity | - |
| 150-200 | High flood warning activity (50-100% above baseline) | 2024 (167.0) |
| > 200 | Very high flood warning activity (> double baseline) | - |

**Recommended Trend Analysis**:

- **5-year rolling average**: Smooths year-to-year variability to identify long-term trends
- **Year-on-year ±30% variability is expected** due to weather patterns
- **Consistent multi-year increases** (e.g., 2022→2023→2024) may indicate systematic change
- **Component analysis** (fluvial vs coastal) helps identify specific flood source changes

**2024 Interpretation**:

> The 2024 FWII of 167.0 indicates flood warning activity **67% higher than the 2020 baseline**, predominantly driven by a 153% increase in river (fluvial) flooding warnings while coastal warnings remained 38% below baseline. This represents the highest flood warning intensity recorded in the West of England since baseline establishment, with a notable pattern shift from coastal-dominated (2020) to fluvial-dominated (2024) flooding. This trend warrants continued monitoring to assess whether it represents a new climate-driven baseline or short-term meteorological variability.

---

## 7. Caveats & Limitations

### What the FWII Measures vs. What It Does NOT Measure

**The FWII measures:**

- ✅ **Flood warning activity** issued by the Environment Agency
- ✅ **Duration and severity** of flood warnings in defined warning areas
- ✅ **Fluvial (river)** and **coastal (tidal)** flood warning events
- ✅ **Year-on-year trends** in warning activity since 2020

**The FWII does NOT measure:**

- ❌ **Actual flooding** (warnings may not result in flooding, or flooding may occur without warnings)
- ❌ **Flood damage or losses** (economic impacts, property damage)
- ❌ **Surface water flooding** (affects more properties nationally than river+coastal combined)
- ❌ **Groundwater flooding** (slow-onset flooding from rising groundwater)
- ❌ **Flooding outside warning areas** (unmapped or unmonitored areas)
- ❌ **Flood risk** (forward-looking probability, only historical warning activity)

### Critical Limitations

#### 1. Warning Activity ≠ Actual Flooding

**An increase in FWII does NOT necessarily mean more actual flooding occurred.**

- Warnings are precautionary (issued when flooding is possible/expected)
- Flood defenses may prevent flooding despite warnings
- Warning thresholds may change over time
- Conversely, **flooding may occur without warnings** (flash floods, defense failures, areas outside warning zones)

**Implication**: FWII should be interpreted as a **proxy indicator** of flood hazard, not a direct measure of flood impacts.

#### 2. Surface Water Flooding Exclusion

**Surface water flooding is the most significant omission.**

- Nationally, **3.4 million properties** are at risk from surface water flooding
- Only **2.7 million properties** are at risk from river and coastal flooding combined
- The Environment Agency **does not issue surface water flood warnings** (too sporadic and unpredictable)

**Alternative Data Source**: Section 19 flood investigation reports from Lead Local Flood Authorities (LLFAs) provide local records, but are not systematically quantified or incorporated into FWII.

**Implication**: **A low FWII does not mean low total flood risk.** Surface water flooding may be significant even in years with low river/coastal warning activity.

#### 3. Geographic Boundaries

**Flooding may occur outside the 18 monitored warning areas.**

- Warning areas cover major rivers and coastal zones but not all flood-prone areas
- Small watercourses, minor tributaries, and localized flood points may not have designated warning areas
- Urban flooding from drainage overwhelm is not captured

**Implication**: FWII understates total flood events in the region.

#### 4. Warning Area Boundary Changes

**The Environment Agency updates warning area boundaries quarterly.**

- New areas may be added or removed
- Boundary adjustments may affect warning counts
- Historical comparisons assume stable area definitions

**Mitigation**: The `config/warning_areas.yaml` maintains a version history. Future refinements may track which areas were active in each reporting year.

#### 5. Duration Estimation Uncertainty

**Warning end times are not provided in the dataset, requiring heuristic estimation.**

- Default durations (Severe: 12h, Warning: 24h, Alert: 48h) may over- or underestimate actual warning periods
- Gaps between warnings used to infer event separation (72-hour threshold) may misclassify continuous vs. separate events
- "Update" messages assumed to represent event continuations may occasionally be new events

**Mitigation**: Default durations based on expert judgment and EA guidance. Sensitivity analysis could test alternative duration assumptions.

#### 6. Data Quality & Completeness

**The EA dataset has known quality issues:**

- Missing timestamps (particularly `timeSeverityChanged`)
- Schema variations across years (pre-2017 vs. post-2017 systems)
- Occasional duplicate records or inconsistent severity classifications

**Mitigation**: Comprehensive validation (Phase 3 of pipeline) identifies and reports data quality issues. Records with critical missing fields (e.g., `timeRaised`, `fwdCode`) are excluded.

### Standard Disclaimer

Include this caveat in all published FWII reports:

> **FWII Interpretation Disclaimer**
>
> This indicator measures flood warning activity as a proxy for actual flooding. It does NOT include surface water flooding, which affects more properties nationally than river and coastal flooding combined. An increase in FWII indicates more flood warning activity, not necessarily more actual flooding. Conversely, low FWII values do not mean flooding did not occur—surface water events and unreported flooding are not captured.
>
> The indicator is based on Environment Agency flood warnings issued for defined warning areas. Flooding may occur outside these areas or without a warning being issued. Warning area boundaries are subject to periodic revision.

### Complementary Data Sources

To provide a fuller picture of flood risk in the West of England, the FWII should be used alongside:

1. **Section 19 Flood Investigation Reports** (LLFAs) - Local evidence of significant flooding, including surface water events
2. **Recorded Flood Outlines** (EA dataset) - GIS polygons of verified historic flooding from all sources
3. **National Flood Risk Assessment (NaFRA)** - Properties at risk assessments by flood source
4. **Insurance claims data** - Actual flood damage evidence (if accessible)
5. **Local knowledge & media reports** - Community-reported flooding events

---

## 8. References

### Data Sources

1. **Environment Agency Real-Time Flood Monitoring API**
   <https://environment.data.gov.uk/flood-monitoring/doc/reference>

2. **Historic Flood Warnings Dataset** (Primary data source)
   <https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590>

3. **Flood Warning Areas Dataset**
   <https://environment.data.gov.uk/dataset/87e5d78f-d465-11e4-9343-f0def148f590>

4. **Recorded Flood Outlines** (Supplementary validation)
   <https://environment.data.gov.uk/dataset/8c75e700-d465-11e4-8b5b-f0def148f590>

### Policy & Governance

5. **DEFRA Outcome Indicator Framework - F1: Disruption from Flooding**
   <https://oifdata.defra.gov.uk/themes/resilience/F1/>

6. **DEFRA Outcome Indicator Framework - F2: Communities Resilient to Flooding**
   <https://oifdata.defra.gov.uk/themes/resilience/F2/>

7. **Flood and Water Management Act 2010, Section 19**
   <https://www.legislation.gov.uk/ukpga/2010/29/section/19>

### Risk Assessment

8. **National Assessment of Flood and Coastal Erosion Risk (NaFRA) 2024**
   <https://www.gov.uk/government/publications/national-assessment-of-flood-and-coastal-erosion-risk-in-england-2024>

9. **Measuring Resilience to Flooding and Coastal Change** (EA Research)
   <https://www.gov.uk/flood-and-coastal-erosion-risk-management-research-reports/measuring-resilience-to-flooding-and-coastal-change>

### Technical Documentation

10. **Project Technical Specification (CLAUDE.md)**
    <https://github.com/><repository>/blob/main/CLAUDE.md

11. **User Guide (README.md)**
    <https://github.com/><repository>/blob/main/README.md

---

## 9. Licensing & Contact

### Code Licence

**MIT License**

Copyright (c) 2024 [Project Owner]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

### Data Licence

**Open Government Licence v3.0**

All Environment Agency data used in this indicator is licenced under the Open Government Licence v3.0:
<https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>

You are free to:

- Copy, publish, distribute and transmit the data
- Adapt the data
- Exploit the data commercially

Subject to acknowledgement of the source.

### Contact Information

**Environment Agency**
National Customer Contact Centre
Telephone: 03708 506 506
Email: <enquiries@environment-agency.gov.uk>
Website: <https://www.gov.uk/government/organisations/environment-agency>

**Indicator Owner**
[To be completed - West of England Combined Authority or relevant governance body]

**Technical Queries**
For questions about the FWII implementation, calculation methodology, or data processing:
[Repository Issues](https://github.com/<repository>/issues)

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | December 2024 | Initial summary report covering 2020-2024 baseline period |

---

## Appendix A: Quick Reference

### Glossary

| Term | Definition |
|------|------------|
| **FWII** | Flood Warning Intensity Index - Composite indicator of flood warning activity |
| **Fluvial** | River flooding (from watercourses overtopping banks) |
| **Coastal/Tidal** | Flooding from sea/estuary tidal surges or high tides |
| **Surface Water** | Flooding from intense rainfall overwhelming drainage (not included in FWII) |
| **Severity Level** | 1=Severe (danger to life), 2=Warning (flooding expected), 3=Alert (flooding possible), 4=No longer in force |
| **fwdCode** | Flood Warning Descriptor Code - Unique identifier for warning areas (e.g., 112WAFTLBA) |
| **Baseline** | Reference year (2020) normalized to index value 100 for comparisons |
| **Duration-Weighted** | Scoring approach multiplying warning duration (hours) by severity weight |
| **NaFRA** | National Assessment of Flood and Coastal Erosion Risk |
| **EA** | Environment Agency |
| **LLFA** | Lead Local Flood Authority (local councils responsible for surface water flooding) |

### Key Formulas

**Warning Score**:

```
Warning Score = Duration (hours) × Severity Weight

Where Severity Weights:
  - Severe (level 1): ×3
  - Warning (level 2): ×2
  - Alert (level 3): ×1
```

**Annual Sub-Indicators**:

```
Fluvial Score = Σ (warning scores for all fluvial warnings)
Coastal Score = Σ (warning scores for all coastal warnings)
```

**Normalization**:

```
Fluvial Index = (Fluvial Score / Baseline Fluvial 2020) × 100
Coastal Index = (Coastal Score / Baseline Coastal 2020) × 100
```

**Composite FWII**:

```
FWII = (Fluvial Index × 0.55) + (Coastal Index × 0.45)
```

### 2020 Baseline Values

| Component | Score | Events | Hours |
|-----------|-------|--------|-------|
| Fluvial | 1,051.65 | 23 | 1,051.65 |
| Coastal | 2,410.57 | 72 | 2,338.57 |
| **Total** | **3,462.22** | **95** | **3,390.22** |

### Configuration Files

| File | Purpose |
|------|---------|
| `config/settings.yaml` | API endpoints, weights, thresholds, counties |
| `config/warning_areas.yaml` | 18 West of England warning areas with metadata |
| `config/baseline_2020.yaml` | Baseline scores for normalization |

### Data Files

| Location | Contents |
|----------|----------|
| `data/raw/` | Downloaded EA Historic Warnings ZIP extracts |
| `data/processed/warnings_{year}.csv` | Cleaned warnings for West of England |
| `data/processed/data_quality_report_{year}.json` | Validation results |
| `data/fwii.duckdb` | DuckDB database (flood_warnings table) |
| `data/outputs/fwii_timeseries.csv` | Multi-year FWII time series |

---

**END OF SUMMARY REPORT**
