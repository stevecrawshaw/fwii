# Phase 3: Core Calculation Logic - COMPLETE

**Date**: 2025-12-11  
**Status**: Complete  
**Phase**: Core Indicator Calculation

## Overview

Successfully implemented the complete Flood Warning Intensity Index (FWII) calculation system, including duration calculation, scoring, and baseline normalization. The system is now functional and has calculated the 2020 baseline.

## Key Accomplishments

### 1. Duration Calculator Implementation

**File**: `src/fwii/duration_calculator.py`

**Key Discovery**: The EA historic data does NOT include warning end times (severity level 4 records). This required a different approach than originally specified in CLAUDE.md.

**Heuristic Approach Implemented**:
- Group warnings by `fwdCode` (warning area)
- Sort chronologically
- Calculate duration based on:
  - Time until next warning for same area (if within max_gap)
  - Default duration for that severity level
  - Use MINIMUM of the two (avoids unrealistic long durations)

**Default Durations** (configurable via `DurationConfig`):
- Severe Flood Warning (level 1): 12 hours
- Flood Warning (level 2): 24 hours  
- Flood Alert (level 3): 48 hours
- Max gap between warnings: 72 hours

**Special Handling for "Update" Messages**:
- Identified via regex: `severity.str.contains('(?i)update')`
- Updates extend/continue previous warnings
- Duration = gap to next warning (don't cap at default)

**Features**:
- `WarningEvent` dataclass with calculated durations
- `DurationConfig` dataclass for configuration
- `calculate_durations()` - processes entire dataset
- `calculate_annual_scores()` - aggregates by year with fluvial/coastal separation
- Severity weights applied: Severe×3, Warning×2, Alert×1

### 2. Indicator Calculator Implementation

**File**: `src/fwii/indicator_calculator.py`

**Features**:
- `BaselineScores` dataclass for baseline storage
- `NormalizedIndicators` dataclass for results
- `IndicatorCalculator` class with baseline normalization
- Composite FWII formula: (fluvial_index × 0.55) + (coastal_index × 0.45)
- Baseline save/load from `config/baseline_2020.yaml`

**Calculation Flow**:
1. Load warnings DataFrame with `isTidal` flag
2. Calculate durations using `DurationCalculator`
3. Compute raw weighted scores (duration × severity_weight)
4. Normalize against baseline (baseline year = 100)
5. Calculate composite FWII from weighted components

**Normalization Formula**:
```
fluvial_index = (fluvial_score_raw / baseline_fluvial_score) × 100
coastal_index = (coastal_score_raw / baseline_coastal_score) × 100
composite_fwii = (fluvial_index × 0.55) + (coastal_index × 0.45)
```

### 3. isTidal Data Challenge & Solution

**Problem**: Historic warnings data does NOT include `isTidal` field.

**Solution**: Join with `config/warning_areas.yaml` which has `isTidal` for each `fwdCode`.

**Implementation**:
```python
# Load warning areas config
with open('config/warning_areas.yaml', 'r') as f:
    areas_config = yaml.safe_load(f)

# Create lookup DataFrame
areas_list = [
    {'fwdCode': area['fwdCode'], 'isTidal': area.get('isTidal', None)}
    for area in areas_config['warning_areas']
]
areas_df = pl.DataFrame(areas_list)

# Join with warnings
df = df.drop('isTidal').join(areas_df, on='fwdCode', how='left')
```

This approach used in both test scripts.

### 4. Scripts Created

#### `scripts/test_duration_calculator.py`
- Tests duration calculator in isolation
- Shows sample warning events with durations
- Displays severity breakdown
- Demonstrates annual score calculation

#### `scripts/calculate_fwii.py`
- Complete FWII calculation for any year
- Loads data with isTidal join
- Calculates and displays all indicators
- Optional `--save-baseline` flag for 2020
- Provides interpretation of results

**Usage**:
```bash
# Calculate and save 2020 baseline
uv run python scripts/calculate_fwii.py 2020 --save-baseline

# Calculate normalized indicators for other years
uv run python scripts/calculate_fwii.py 2024
```

## 2020 Baseline Results

**Saved to**: `config/baseline_2020.yaml`

### Raw Scores (Duration-Weighted)
- **Fluvial Score**: 1,051.6
  - 23 events
  - 1,051.6 hours total
  - All Level 3 (Flood Alerts)
  
- **Coastal Score**: 2,410.6
  - 72 events  
  - 2,338.6 hours total
  - 3 Level 2 (Flood Warnings): 72 hours, weighted score 144.0
  - 69 Level 3 (Flood Alerts): 2,266.6 hours, weighted score 2,266.6

- **Total Score**: 3,462.2
  - 95 total events
  - 3,390.2 total hours
  - 0 Severe Flood Warnings (Level 1)
  - 3 Flood Warnings (Level 2)
  - 92 Flood Alerts (Level 3)

### Normalized Indicators (Baseline Year)
- Fluvial Index: 100.0
- Coastal Index: 100.0
- Composite FWII: 100.0

### Data Characteristics
- **Date Range**: 2020-01-02 to 2020-12-26
- **Active Warning Areas**: 14 out of 18 configured
- **Most Active Areas**:
  - 112WATSOM4: 18 warnings (coastal)
  - 112WATSOM3: 17 warnings (coastal)
  - 112WATSOM2: 14 warnings (coastal)
  - 112WAFTUBA: 13 warnings (fluvial)

## Technical Implementation Details

### Polars DataFrame Usage

All data processing uses Polars for efficiency:
- `pl.col('severity').str.contains('(?i)update')` for update detection
- `pl.col('timeRaised').shift(-1).over('fwdCode')` for next warning time
- Window functions for gap calculations
- Date/time operations via `.dt.total_seconds()`

### DuckDB Export for Testing

Due to database locking issues during development, implemented CSV export:
```sql
COPY (SELECT * FROM warnings WHERE year = 2020) 
TO 'data/processed/warnings_2020.csv' (HEADER, DELIMITER ',');
```

Scripts check for CSV first, fall back to DuckDB if not found.

### Configuration Files

**Created**:
- `config/baseline_2020.yaml` - Baseline scores for normalization

**Required** (already exists):
- `config/warning_areas.yaml` - 18 West of England areas with isTidal flags
- `config/settings.yaml` - API URLs and parameters

## Data Quality Observations

### Warning Duration Patterns

From 2020 data analysis:
- Most warnings are single events (not part of escalation chains)
- Large gaps between warnings suggest separate flood events
- Coastal warnings more frequent than fluvial (72 vs 23)
- No Severe Flood Warnings in 2020 baseline year
- Only 3 Flood Warnings (all coastal, likely tidal flooding events)

### Typical Warning Sequences

Example from 112WAFTUBA (Upper Bristol Avon):
- Multiple discrete Flood Alert events throughout year
- Gaps range from 24 hours to 6,354 hours (9 months)
- Mix of "Flood Alert" and "Update Flood Alert" messages
- No escalations to higher severity levels

## Comparison to Original Specification

### Differences from CLAUDE.md

**Original Spec Assumption**:
- Data includes `timeSeverityChanged` timestamps
- Warnings have explicit end times (severity level 4)
- Can track escalation/de-escalation through severity levels
- Example given: Alert → Warning → Severe → Warning → Alert → Removed

**Actual EA Data Reality**:
- NO `timeSeverityChanged` field
- NO severity level 4 (Warning No Longer in Force) records
- Each record is an independent warning issuance
- Cannot track explicit escalations

**Our Solution**:
- Heuristic-based duration estimation
- Conservative defaults to avoid over-counting
- Gap-based continuation for "Update" messages
- Validated approach produces reasonable results

### Methodology Adjustments

**Documented Changes**:
1. Duration calculation uses heuristics, not explicit lifecycle tracking
2. Default durations act as upper bounds
3. Separate events detected via 72-hour max gap threshold
4. "Update" messages treated as continuations

**Rationale**:
- Produces consistent, reproducible results
- Conservative approach avoids inflating scores
- Captures major flood events while handling data limitations
- Baseline year (2020) shows reasonable activity levels

## Next Steps

### Immediate (Phase 4)
1. Download data for 2021-2024 years
2. Calculate FWII trends over time
3. Implement report generator for official outputs (JSON/CSV)
4. Create time series visualizations

### Near-term (Phase 5)
1. Validate against known flood events in West of England
2. Cross-reference with EA published statistics
3. Document methodology deviations from original spec
4. Create validation dashboard

### Medium-term (Phase 6)
1. Create CLI interface
2. Add automated quality checks
3. Generate annual reports
4. Archive baseline data

## Known Limitations

1. **Duration Estimation**: Heuristic-based, not exact warning lifecycles
2. **Missing End Times**: Cannot calculate precise warning durations
3. **No Escalation Tracking**: Cannot verify if warnings escalated through levels
4. **Default Duration Dependency**: Results sensitive to configured defaults
5. **Gap Threshold**: 72-hour max gap is configurable but somewhat arbitrary

## Files Modified/Created in This Phase

**Created**:
- `src/fwii/duration_calculator.py` (301 lines)
- `src/fwii/indicator_calculator.py` (236 lines)
- `scripts/test_duration_calculator.py` (141 lines)
- `scripts/calculate_fwii.py` (150 lines)
- `config/baseline_2020.yaml` (11 lines)
- `data/processed/warnings_2020.csv` (96 lines - exported for testing)

**Dependencies** (already in pyproject.toml):
- polars (DataFrame operations)
- pyyaml (config file handling)
- duckdb (database queries)

## Validation & Testing

### Manual Validation Performed

1. **Sample Event Inspection**: Reviewed 112WAFTUBA warning sequence
2. **Duration Reasonableness**: Confirmed durations align with defaults/gaps
3. **Score Calculation**: Manually verified severity weighting
4. **Baseline Normalization**: Confirmed 2020 baseline = 100.0
5. **Component Separation**: Verified fluvial vs coastal split (23 vs 72)

### Test Results
- ✅ Duration calculator handles 95 events correctly
- ✅ Severity weighting applied correctly
- ✅ Baseline normalization produces expected 100.0
- ✅ isTidal join successful (0 unmatched records)
- ✅ Composite FWII formula verified

## Performance

**Processing Speed** (2020 data, 95 warnings):
- Load from CSV: <1 second
- Join with warning areas: <1 second  
- Calculate durations: <1 second
- Calculate indicators: <1 second
- **Total**: ~1-2 seconds

Memory efficient - Polars handles dataset entirely in memory.

## Reproducibility

All calculations are deterministic and reproducible:
1. Fixed baseline in `config/baseline_2020.yaml`
2. Fixed warning area configurations
3. Fixed severity weights and default durations
4. No randomness or manual interventions
5. Source data archived in DuckDB

## References

- Original specification: `CLAUDE.md`
- Phase 2 learnings: `.serena/memories/phase2-data-pipeline-learnings`
- EA data: `data/raw/historic_flood_warnings/202510 Historic Flood Warnings – EA.ods`
- Database: `data/processed/fwii.duckdb`
