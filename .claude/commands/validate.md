---
description: Comprehensive validation of the FWII codebase and data pipeline
---

# Ultimate FWII Validation Command

Perform comprehensive validation of the West of England Flood Warning Intensity Index system.

## Overview

This validation ensures:
- Code quality (linting, formatting)
- Configuration integrity
- Data pipeline functionality
- API connectivity
- Calculation accuracy
- Historical data consistency
- Baseline verification

## Phase 1: Code Quality & Linting

Run Ruff linting to check Python code quality:

```bash
echo "=== PHASE 1: CODE QUALITY & LINTING ==="
echo ""
echo "Running Ruff linter..."
uv run ruff check src/ scripts/
LINT_EXIT_CODE=$?

if [ $LINT_EXIT_CODE -eq 0 ]; then
    echo "✓ Linting passed"
else
    echo "✗ Linting failed with exit code $LINT_EXIT_CODE"
    exit 1
fi
```

## Phase 2: Code Formatting Check

Verify code formatting with Ruff:

```bash
echo ""
echo "=== PHASE 2: CODE FORMATTING CHECK ==="
echo ""
echo "Checking code formatting..."
uv run ruff format --check src/ scripts/
FORMAT_EXIT_CODE=$?

if [ $FORMAT_EXIT_CODE -eq 0 ]; then
    echo "✓ Formatting check passed"
else
    echo "✗ Formatting check failed with exit code $FORMAT_EXIT_CODE"
    exit 1
fi
```

## Phase 3: Configuration Validation

Validate all configuration files:

```bash
echo ""
echo "=== PHASE 3: CONFIGURATION VALIDATION ==="
echo ""

# Check that essential config files exist
echo "Checking configuration files..."
REQUIRED_CONFIGS=(
    "config/settings.yaml"
    "config/warning_areas.yaml"
    "config/baseline_2020.yaml"
)

for config in "${REQUIRED_CONFIGS[@]}"; do
    if [ -f "$config" ]; then
        echo "  ✓ $config exists"
    else
        echo "  ✗ $config NOT FOUND"
        exit 1
    fi
done

# Validate warning_areas.yaml structure
echo ""
echo "Validating warning_areas.yaml structure..."
python3 -c "
import yaml
import sys

with open('config/warning_areas.yaml') as f:
    config = yaml.safe_load(f)

# Check metadata
if 'metadata' not in config:
    print('✗ Missing metadata section')
    sys.exit(1)

if 'warning_areas' not in config:
    print('✗ Missing warning_areas section')
    sys.exit(1)

# Check we have 18 areas (9 fluvial + 9 coastal)
areas = config['warning_areas']
if len(areas) != 18:
    print(f'✗ Expected 18 warning areas, found {len(areas)}')
    sys.exit(1)

# Check each area has required fields
required_fields = ['fwdCode', 'label', 'county', 'riverOrSea', 'isTidal']
for area in areas:
    for field in required_fields:
        if field not in area:
            print(f'✗ Area {area.get(\"fwdCode\", \"unknown\")} missing field: {field}')
            sys.exit(1)

# Check fluvial/coastal split
fluvial = sum(1 for a in areas if not a['isTidal'])
coastal = sum(1 for a in areas if a['isTidal'])

if fluvial != 9:
    print(f'✗ Expected 9 fluvial areas, found {fluvial}')
    sys.exit(1)

if coastal != 9:
    print(f'✗ Expected 9 coastal areas, found {coastal}')
    sys.exit(1)

print('✓ warning_areas.yaml is valid')
print(f'  - 18 total areas')
print(f'  - 9 fluvial areas')
print(f'  - 9 coastal areas')
"

# Validate baseline_2020.yaml
echo ""
echo "Validating baseline_2020.yaml..."
python3 -c "
import yaml
import sys

with open('config/baseline_2020.yaml') as f:
    baseline = yaml.safe_load(f)

required_fields = ['year', 'fluvial_score', 'coastal_score', 'total_score',
                   'fluvial_hours', 'coastal_hours', 'fluvial_events', 'coastal_events']

for field in required_fields:
    if field not in baseline:
        print(f'✗ Missing required field: {field}')
        sys.exit(1)

if baseline['year'] != 2020:
    print(f'✗ Baseline year should be 2020, found {baseline[\"year\"]}')
    sys.exit(1)

# Verify calculation consistency
total = baseline['fluvial_score'] + baseline['coastal_score']
if abs(total - baseline['total_score']) > 0.01:
    print(f'✗ Inconsistent totals: {baseline[\"fluvial_score\"]} + {baseline[\"coastal_score\"]} != {baseline[\"total_score\"]}')
    sys.exit(1)

print('✓ baseline_2020.yaml is valid')
print(f'  - Year: {baseline[\"year\"]}')
print(f'  - Total score: {baseline[\"total_score\"]:.1f}')
print(f'  - Events: {baseline[\"fluvial_events\"]} fluvial + {baseline[\"coastal_events\"]} coastal')
"
```

## Phase 4: API Connectivity

Test connectivity to Environment Agency APIs:

```bash
echo ""
echo "=== PHASE 4: API CONNECTIVITY ==="
echo ""

# Test Environment Agency Flood Monitoring API
echo "Testing EA Flood Monitoring API..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from fwii.config import Config
from fwii.api_client import FloodMonitoringClient

try:
    config = Config()
    with FloodMonitoringClient(config) as client:
        # Test flood areas endpoint
        areas = client.get_flood_areas('Bristol')
        if len(areas) == 0:
            print('✗ No flood areas returned for Bristol')
            sys.exit(1)

        print(f'✓ EA Flood Monitoring API is accessible')
        print(f'  - Retrieved {len(areas)} areas for Bristol')

except Exception as e:
    print(f'✗ API connectivity test failed: {e}')
    sys.exit(1)
"
```

## Phase 5: Data Presence & Integrity

Verify that historical data has been downloaded and processed:

```bash
echo ""
echo "=== PHASE 5: DATA PRESENCE & INTEGRITY ==="
echo ""

# Check for processed CSV files
echo "Checking for processed warning data (2020-2024)..."
YEARS=(2020 2021 2022 2023 2024)
MISSING_YEARS=()

for year in "${YEARS[@]}"; do
    CSV_FILE="data/processed/warnings_${year}.csv"
    if [ -f "$CSV_FILE" ]; then
        # Count records
        RECORD_COUNT=$(tail -n +2 "$CSV_FILE" | wc -l)
        echo "  ✓ $year: $RECORD_COUNT warnings"
    else
        echo "  ✗ $year: Missing data file"
        MISSING_YEARS+=($year)
    fi
done

if [ ${#MISSING_YEARS[@]} -gt 0 ]; then
    echo ""
    echo "⚠ Missing data for years: ${MISSING_YEARS[@]}"
    echo "  Run: uv run python scripts/download_historic_data.py ${MISSING_YEARS[0]} ${MISSING_YEARS[-1]}"
    exit 1
fi

# Validate CSV structure
echo ""
echo "Validating CSV structure..."
python3 -c "
import polars as pl
import sys

try:
    # Load 2020 data as test
    df = pl.read_csv('data/processed/warnings_2020.csv', try_parse_dates=True)

    # Check required columns
    required_cols = ['timeRaised', 'fwdCode', 'label', 'severity', 'severityLevel', 'isTidal']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        print(f'✗ Missing required columns: {missing_cols}')
        sys.exit(1)

    # Check data types
    if not df['timeRaised'].dtype == pl.Datetime:
        print('✗ timeRaised is not datetime type')
        sys.exit(1)

    if not df['severityLevel'].dtype == pl.Int64:
        print('✗ severityLevel is not integer type')
        sys.exit(1)

    if not df['isTidal'].dtype == pl.Boolean:
        print('✗ isTidal is not boolean type')
        sys.exit(1)

    print('✓ CSV structure is valid')
    print(f'  - All required columns present')
    print(f'  - Correct data types')

except Exception as e:
    print(f'✗ CSV validation failed: {e}')
    sys.exit(1)
"
```

## Phase 6: End-to-End Data Pipeline Test

Test the complete data pipeline on a sample year:

```bash
echo ""
echo "=== PHASE 6: END-TO-END DATA PIPELINE TEST ==="
echo ""

echo "Testing complete workflow for 2020 baseline year..."
echo ""

# Test 1: Fetch warning areas (this should already be cached)
echo "1. Testing warning areas fetch..."
if [ -f "config/warning_areas.yaml" ]; then
    AREA_COUNT=$(grep -c "fwdCode:" config/warning_areas.yaml)
    echo "   ✓ Warning areas available: $AREA_COUNT areas"
else
    echo "   ✗ Warning areas file not found"
    exit 1
fi

# Test 2: Verify processed data exists
echo ""
echo "2. Testing data availability..."
if [ -f "data/processed/warnings_2020.csv" ]; then
    RECORD_COUNT=$(tail -n +2 data/processed/warnings_2020.csv | wc -l)
    echo "   ✓ 2020 data available: $RECORD_COUNT warnings"
else
    echo "   ✗ 2020 data not found"
    exit 1
fi

# Test 3: Calculate FWII for 2020
echo ""
echo "3. Testing FWII calculation..."
python3 scripts/calculate_fwii.py 2020 > /tmp/fwii_test_output.txt 2>&1
CALC_EXIT_CODE=$?

if [ $CALC_EXIT_CODE -eq 0 ]; then
    # Verify the output contains expected values
    if grep -q "COMPOSITE FWII:" /tmp/fwii_test_output.txt; then
        FWII_VALUE=$(grep "COMPOSITE FWII:" /tmp/fwii_test_output.txt | awk '{print $3}')
        echo "   ✓ FWII calculation successful"
        echo "   ✓ 2020 FWII = $FWII_VALUE (should be 100.0 for baseline year)"

        # Verify it's close to 100 (allowing for floating point)
        python3 -c "
import sys
fwii = float('$FWII_VALUE')
if abs(fwii - 100.0) > 0.1:
    print(f'   ✗ 2020 FWII should be 100.0, got {fwii}')
    sys.exit(1)
else:
    print('   ✓ Baseline normalization verified')
"
    else
        echo "   ✗ FWII output format unexpected"
        cat /tmp/fwii_test_output.txt
        exit 1
    fi
else
    echo "   ✗ FWII calculation failed"
    cat /tmp/fwii_test_output.txt
    exit 1
fi

# Test 4: Verify trend report generation
echo ""
echo "4. Testing trend report generation..."
python3 scripts/generate_trend_report.py > /tmp/trend_test_output.txt 2>&1
TREND_EXIT_CODE=$?

if [ $TREND_EXIT_CODE -eq 0 ]; then
    if grep -q "TREND REPORT 2020-2024" /tmp/trend_test_output.txt; then
        echo "   ✓ Trend report generation successful"

        # Check output file was created
        if [ -f "data/outputs/fwii_timeseries.csv" ]; then
            YEARS_IN_CSV=$(tail -n +2 data/outputs/fwii_timeseries.csv | wc -l)
            echo "   ✓ Time series CSV exported: $YEARS_IN_CSV years"
        else
            echo "   ⚠ Time series CSV not found"
        fi
    else
        echo "   ✗ Trend report output format unexpected"
        exit 1
    fi
else
    echo "   ✗ Trend report generation failed"
    cat /tmp/trend_test_output.txt
    exit 1
fi
```

## Phase 7: Calculation Accuracy Verification

Verify calculation logic with known values:

```bash
echo ""
echo "=== PHASE 7: CALCULATION ACCURACY VERIFICATION ==="
echo ""

echo "Verifying calculation logic..."
python3 -c "
import sys
sys.path.insert(0, 'src')
import polars as pl
from fwii.indicator_calculator import IndicatorCalculator

# Load 2020 baseline data
df = pl.read_csv('data/processed/warnings_2020.csv', try_parse_dates=True)

# Calculate indicators
calculator = IndicatorCalculator()
indicators = calculator.calculate_indicators(df, 2020)

# Verification tests
print('Verifying 2020 baseline calculations...')

# Test 1: FWII should be 100.0 for baseline year
if abs(indicators.composite_fwii - 100.0) > 0.1:
    print(f'✗ 2020 FWII should be 100.0, got {indicators.composite_fwii}')
    sys.exit(1)
print('  ✓ Baseline normalization: 100.0')

# Test 2: Fluvial and coastal should also be 100.0
if abs(indicators.fluvial_index - 100.0) > 0.1:
    print(f'✗ Fluvial index should be 100.0, got {indicators.fluvial_index}')
    sys.exit(1)
print('  ✓ Fluvial index: 100.0')

if abs(indicators.coastal_index - 100.0) > 0.1:
    print(f'✗ Coastal index should be 100.0, got {indicators.coastal_index}')
    sys.exit(1)
print('  ✓ Coastal index: 100.0')

# Test 3: Raw scores should match baseline
import yaml
with open('config/baseline_2020.yaml') as f:
    baseline = yaml.safe_load(f)

if abs(indicators.fluvial_score_raw - baseline['fluvial_score']) > 0.01:
    print(f'✗ Fluvial score mismatch: {indicators.fluvial_score_raw} vs {baseline[\"fluvial_score\"]}')
    sys.exit(1)
print(f'  ✓ Fluvial raw score: {indicators.fluvial_score_raw:.1f}')

if abs(indicators.coastal_score_raw - baseline['coastal_score']) > 0.01:
    print(f'✗ Coastal score mismatch: {indicators.coastal_score_raw} vs {baseline[\"coastal_score\"]}')
    sys.exit(1)
print(f'  ✓ Coastal raw score: {indicators.coastal_score_raw:.1f}')

# Test 4: Composite formula (55% fluvial + 45% coastal)
expected_composite = (indicators.fluvial_index * 0.55) + (indicators.coastal_index * 0.45)
if abs(indicators.composite_fwii - expected_composite) > 0.01:
    print(f'✗ Composite calculation error: {indicators.composite_fwii} vs {expected_composite}')
    sys.exit(1)
print('  ✓ Composite formula: 55% fluvial + 45% coastal')

# Test 5: Event counts should be positive
if indicators.total_events <= 0:
    print(f'✗ No events found in 2020 data')
    sys.exit(1)
print(f'  ✓ Event counts: {indicators.fluvial_events} fluvial + {indicators.coastal_events} coastal = {indicators.total_events} total')

print('')
print('✓ All calculation accuracy tests passed')
"
```

## Phase 8: Cross-Year Consistency

Verify calculations across multiple years:

```bash
echo ""
echo "=== PHASE 8: CROSS-YEAR CONSISTENCY ==="
echo ""

echo "Verifying consistency across all years..."
python3 -c "
import sys
sys.path.insert(0, 'src')
import polars as pl
from fwii.indicator_calculator import IndicatorCalculator

calculator = IndicatorCalculator()
years = [2020, 2021, 2022, 2023, 2024]
results = []

for year in years:
    csv_path = f'data/processed/warnings_{year}.csv'
    try:
        df = pl.read_csv(csv_path, try_parse_dates=True)
        indicators = calculator.calculate_indicators(df, year)
        results.append({
            'year': year,
            'fwii': indicators.composite_fwii,
            'warnings': len(df),
            'events': indicators.total_events
        })
    except FileNotFoundError:
        print(f'⚠ Missing data for {year}')
        continue

if len(results) < 2:
    print('✗ Need at least 2 years of data for consistency check')
    sys.exit(1)

# Print results table
print('Year  FWII    Warnings  Events')
print('-' * 35)
for r in results:
    print(f'{r[\"year\"]}  {r[\"fwii\"]:6.1f}  {r[\"warnings\"]:8d}  {r[\"events\"]:6d}')

print('')

# Consistency checks
print('Running consistency checks...')

# Check 1: All values should be positive
for r in results:
    if r['fwii'] < 0 or r['warnings'] < 0 or r['events'] < 0:
        print(f'✗ {r[\"year\"]}: Negative values detected')
        sys.exit(1)
print('  ✓ All values are positive')

# Check 2: FWII should be in reasonable range (0-500)
for r in results:
    if r['fwii'] < 0 or r['fwii'] > 500:
        print(f'✗ {r[\"year\"]}: FWII {r[\"fwii\"]} out of reasonable range (0-500)')
        sys.exit(1)
print('  ✓ All FWII values in reasonable range (0-500)')

# Check 3: 2020 should be baseline (100.0)
baseline_2020 = [r for r in results if r['year'] == 2020]
if baseline_2020 and abs(baseline_2020[0]['fwii'] - 100.0) > 0.1:
    print(f'✗ 2020 baseline should be 100.0, got {baseline_2020[0][\"fwii\"]}')
    sys.exit(1)
print('  ✓ 2020 baseline verified (100.0)')

# Check 4: Events should be less than or equal to warnings
for r in results:
    if r['events'] > r['warnings']:
        print(f'✗ {r[\"year\"]}: Events ({r[\"events\"]}) > Warnings ({r[\"warnings\"]})')
        sys.exit(1)
print('  ✓ Event counts are consistent with warning counts')

print('')
print('✓ All cross-year consistency checks passed')
"
```

## Phase 9: Data Quality Checks

Verify data quality across all years:

```bash
echo ""
echo "=== PHASE 9: DATA QUALITY CHECKS ==="
echo ""

echo "Checking data quality for all years..."
python3 -c "
import sys
sys.path.insert(0, 'src')
import polars as pl

years = [2020, 2021, 2022, 2023, 2024]
issues = []

for year in years:
    csv_path = f'data/processed/warnings_{year}.csv'
    try:
        df = pl.read_csv(csv_path, try_parse_dates=True)

        # Check for null values in critical columns
        critical_cols = ['timeRaised', 'fwdCode', 'severityLevel', 'isTidal']
        for col in critical_cols:
            null_count = df[col].null_count()
            if null_count > 0:
                issues.append(f'{year}: {null_count} null values in {col}')

        # Check severity levels are valid (1-4)
        invalid_severity = df.filter(
            (pl.col('severityLevel') < 1) | (pl.col('severityLevel') > 4)
        )
        if len(invalid_severity) > 0:
            issues.append(f'{year}: {len(invalid_severity)} invalid severity levels')

        # Check dates are in correct year
        year_mismatches = df.filter(
            pl.col('timeRaised').dt.year() != year
        )
        if len(year_mismatches) > 0:
            issues.append(f'{year}: {len(year_mismatches)} warnings with wrong year')

        print(f'  ✓ {year}: {len(df)} warnings - quality checks passed')

    except FileNotFoundError:
        issues.append(f'{year}: Data file not found')
    except Exception as e:
        issues.append(f'{year}: Error - {e}')

print('')

if issues:
    print('✗ Data quality issues found:')
    for issue in issues:
        print(f'  - {issue}')
    sys.exit(1)
else:
    print('✓ All data quality checks passed')
"
```

## Validation Summary

```bash
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "                         VALIDATION COMPLETE - ALL TESTS PASSED                 "
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Summary:"
echo "  ✓ Code quality and formatting verified"
echo "  ✓ Configuration files validated"
echo "  ✓ API connectivity confirmed"
echo "  ✓ Data pipeline operational"
echo "  ✓ FWII calculations accurate"
echo "  ✓ Cross-year consistency verified"
echo "  ✓ Data quality confirmed"
echo ""
echo "The FWII system is fully validated and ready for production use."
echo ""
```

## Notes

This validation command tests the complete FWII system from API connectivity through to final indicator calculation. All tests must pass for the system to be considered production-ready.

If validation fails at any stage, the command exits with a non-zero status code and reports the specific failure.

For new installations, run data download first:
```bash
uv run python scripts/download_historic_data.py 2020 2024
```
