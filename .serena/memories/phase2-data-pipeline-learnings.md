# Phase 2: Data Pipeline Implementation Learnings

**Date**: 2025-12-11  
**Status**: Complete  
**Phase**: Data Acquisition & Loading

## Overview

Successfully implemented the complete data acquisition pipeline for historic flood warnings from the Environment Agency. Pipeline downloads, validates, and stores data in DuckDB for further processing.

## Key Discoveries About EA Data

### 1. Data Format & Structure

**Actual Format**: ODS (Open Document Spreadsheet), NOT CSV as initially assumed
- File: `202510 Historic Flood Warnings – EA.ods`
- Size: ~3.14 MB uncompressed, 3.3 MB in ZIP
- Total Records: 81,889 (Jan 2006 - Sep 2025)
- Update Frequency: Quarterly

**Required Dependencies**:
```bash
uv add odfpy pandas  # Required for ODS file reading
```

### 2. Column Name Mappings

EA uses different column names than documented in API references:

| EA Column Name | Our Schema | Description |
|----------------|------------|-------------|
| `DATE` | `timeRaised` | Timestamp when warning raised |
| `CODE` | `fwdCode` | Flood warning area code |
| `TYPE` | `severity` (text) → `severityLevel` (int) | Warning type description |
| `WARNING / ALERT AREA NAME` | `label` | Human-readable area name |
| `AREA` | `area_ref` | Area reference |

**Severity Level Mapping**:
- Text contains "Severe" → `severityLevel = 1`
- Text contains "Warning" → `severityLevel = 2`
- Text contains "Alert" → `severityLevel = 3`
- Text contains "No Longer" → `severityLevel = 4`

### 3. Download URL Discovery

**Initial URL (Failed - 401 Access Denied)**:
```
https://api.agrimetrics.co.uk/file-management/data-sets/766cb094-b392-4bd6-a02e-f60e143f3213/files/Historic_Flood_Warnings.zip
```

**Working Public URL**:
```
https://environment.data.gov.uk/api/file/download?fileDataSetId=766cb094-b392-4bd6-a02e-f60e143f3213&fileName=Historic_Flood_Warnings.zip
```

Key difference: Use the official `environment.data.gov.uk` API endpoint, not the agrimetrics mirror.

### 4. Data Architecture

**Single Dataset Approach**:
- EA provides ONE ZIP file with ALL historic data (2006-present)
- NOT separate files per year as initially designed
- Filter by year happens during loading phase, not download phase

**Pipeline Flow**:
1. Download complete dataset once (cached for subsequent runs)
2. Extract ODS file from ZIP
3. Load entire dataset into Polars DataFrame
4. Filter to West of England warning areas (18 configured areas)
5. Filter to specific year for processing
6. Validate data quality
7. Store in DuckDB

## West of England Data Statistics (2020 Baseline)

- **Total EA Records**: 81,889
- **West of England Filter**: 968 records (all years)
- **2020 Records**: 95 warnings
- **Active Warning Areas**: 14 (of 18 configured)
- **Date Range**: 2020-01-02 to 2020-12-26
- **Data Quality**: 100% valid, 1 info note about incomplete lifecycles

## Technical Implementation Details

### Database Schema (DuckDB)

**Simplified Schema** (no auto-increment ID due to DuckDB constraints):
```sql
CREATE TABLE warnings (
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
```

**Indexes Created**:
- `idx_fwdcode` - Warning area code
- `idx_timeraised` - Timestamp for date range queries
- `idx_severity` - Severity level filtering
- `idx_year_fwdcode` - Composite for year-based queries

### Timestamp Handling

**Important**: ODS files loaded via pandas return datetime objects directly
- Don't try to parse with `str.strptime()` on datetime columns
- Check dtype before parsing: `if df[col].dtype in [pl.Datetime, ...]`
- EA timestamps are already in proper datetime format

### Unicode Handling on Windows

**Issue**: Windows console (cp1252) cannot display Unicode symbols
```python
# AVOID: ✓ ✗ ⚠ ℹ
# USE: [OK] [ERROR] [!] [i]
```

Replace all Unicode symbols with ASCII equivalents in logging and validation reports.

## Module Architecture

### 1. data_fetcher.py
- `HistoricWarningsFetcher` class
- Downloads complete dataset (2006-present)
- Handles ZIP extraction
- Progress logging for downloads
- Context manager support

### 2. data_loader.py
- `HistoricWarningsLoader` class
- Supports CSV, JSON, ODS formats
- Column name normalization
- Severity level mapping (text → integer)
- West of England filtering (18 configured areas)
- Year filtering capability
- Timestamp parsing with dtype checking

### 3. validators.py
- `HistoricWarningsValidator` class
- `ValidationReport` and `ValidationIssue` dataclasses
- Comprehensive validation checks:
  - Required fields presence
  - Missing timestamps
  - Invalid severity levels
  - Duplicate records
  - Incomplete warning lifecycles
  - Unusually long warnings (>14 days)
  - Timestamp consistency
  - Field completeness statistics

### 4. db_storage.py
- `FloodWarningsDatabase` class
- DuckDB connection management
- Schema initialization with indexes
- Metadata tracking for data loads
- Query helpers (annual summaries, area stats)
- Handles partial column inserts (only available fields)

### 5. download_historic_data.py
- Complete pipeline orchestration
- Single or multi-year processing
- 4-stage pipeline:
  1. Download (cached)
  2. Load & Filter
  3. Validate
  4. Store
- Comprehensive logging
- Error handling and recovery
- Quality report generation

## Configuration Dependencies

### Required Config Files

1. **config/warning_areas.yaml**
   - 18 West of England warning area codes
   - Loaded by data_loader to filter records

2. **config/settings.yaml**
   - API timeouts and rate limits
   - Severity weights
   - Quality thresholds
   - Baseline year (2020)

## Common Issues & Solutions

### Issue 1: "Cannot infer format from extension: .ods"
**Solution**: Add ODS format support to `load_historic_warnings()` method

### Issue 2: "Missing required fields: {'severityLevel', 'timeRaised', 'fwdCode'}"
**Solution**: Implement column name mapping in `_normalize_schema()`

### Issue 3: "invalid series dtype: expected `String`, got `datetime[ns]`"
**Solution**: Check dtype before attempting string parsing in `_parse_timestamps()`

### Issue 4: "Constraint Error: NOT NULL constraint failed: warnings.id"
**Solution**: Remove auto-increment ID column from schema, use simple table structure

### Issue 5: Unicode encode errors on Windows console
**Solution**: Replace Unicode symbols (✓✗⚠ℹ) with ASCII ([OK][ERROR][!][i])

## Performance Metrics

**Pipeline Execution Time (2020, Cached Download)**:
- Download: <1s (cached)
- Load ODS: ~18s (81,889 records)
- Filter to WoE: <1s (968 records)
- Filter to 2020: <1s (95 records)
- Validate: <1s
- Store in DuckDB: <1s
- **Total**: ~20 seconds

**Memory Usage**:
- Polars handles 81K records efficiently
- Peak memory during ODS load via pandas
- Recommend 1GB+ RAM for safe operation

## Data Quality Findings

### Validation Results (2020)
- ✅ All required fields present
- ✅ All timestamps valid and parseable
- ✅ All severity levels valid (1-4)
- ✅ No duplicate records
- ✅ No timestamp inconsistencies
- ℹ️ 95 warnings have no "level 4" (No Longer in Force) records
  - Interpretation: Either ongoing warnings or data truncation at year boundary

### Missing Data Patterns
- No `isTidal` field in EA ODS file (column doesn't exist)
- No `timeSeverityChanged` or `timeMessageChanged` in ODS
- Only basic fields available: DATE, CODE, TYPE, AREA NAME, AREA

**Impact**: Will need to derive warning lifecycle from sequence of warning records, as individual escalation timestamps are not provided.

## Next Steps for Phase 3

With data successfully loaded, Phase 3 (Core Calculation Logic) requires:

1. **Duration Calculator** - Group records by fwdCode and calculate warning periods
2. **Lifecycle Analysis** - Since we don't have timeSeverityChanged, infer from record sequences
3. **Scoring Logic** - Apply severity weights (Severe×3, Warning×2, Alert×1)
4. **Baseline Calculation** - Compute 2020 baseline for normalization

## Useful Commands

```bash
# Run pipeline for single year
uv run python scripts/download_historic_data.py 2020

# Run pipeline for multiple years
uv run python scripts/download_historic_data.py 2020 2024

# Force re-download
uv run python scripts/download_historic_data.py 2020 --force

# Skip validation
uv run python scripts/download_historic_data.py 2020 --skip-validation

# Verbose logging
uv run python scripts/download_historic_data.py 2020 --verbose
```

## References

- EA Dataset: https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590
- Data.gov.uk Mirror: https://www.data.gov.uk/dataset/d4fb2591-f4dd-4e7f-9aaf-49af94437b36/historic-flood-warnings2
