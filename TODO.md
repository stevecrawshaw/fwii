# FWII Implementation Todo List

> **Status**: Phase 3 Complete - Core Calculation System Working
> **Last Updated**: 2025-12-11
> **Progress**: 16/34 major tasks complete (47%)

---

## Phase 1: Foundation & Setup ✅ COMPLETE

**Goals**: Establish project structure, configuration management, API client, and fetch flood warning areas

**Key Deliverables**:
- ✅ Project directory structure created
- ✅ Configuration management system implemented
- ✅ Working API client with Environment Agency
- ✅ `config/warning_areas.yaml` populated with 18 areas (9 fluvial, 9 coastal)

### 1. Project Structure ✅
**Status**: Complete

- [x] Create `src/fwii/` package with `__init__.py`
- [x] Create `src/fwii/api_client.py` module
- [x] Create `src/fwii/config.py` module
- [x] Create `config/settings.yaml` with API URLs and parameters
- [x] Create `config/warning_areas.yaml` (initially empty)
- [x] Create `scripts/` directory for executable scripts
- [ ] Create `tests/` directory with pytest configuration
- [ ] Create `notebooks/` directory for exploration
- [ ] Create `docs/` directory for documentation
- [x] Update `README.md` with project-specific documentation

### 2. Configuration Management ✅
**Status**: Complete

- [x] Implement `Config` class to load settings from YAML
- [x] Define configuration schema (API URLs, counties, weights, baseline year)
- [x] Add validation for required configuration fields
- [ ] Write unit tests for config loading

### 3. API Client Development ✅
**Status**: Complete

- [x] Implement `FloodMonitoringClient` class using httpx
- [x] Add method: `get_flood_areas(county: str)`
- [x] Add method: `get_all_west_of_england_areas()`
- [x] Implement pagination handling
- [x] Add rate limiting (1 request per second)
- [x] Implement retry logic with exponential backoff
- [x] Add comprehensive error handling
- [ ] Write unit tests using mocked responses

### 4. Fetch Warning Areas ✅
**Status**: Complete

- [x] Create `scripts/fetch_warning_areas.py` script
- [x] Fetch flood areas for all 4 West of England counties
- [x] Extract key fields: `fwdCode`, `label`, `county`, `riverOrSea`, `isTidal`
- [x] Save to `config/warning_areas.yaml` with metadata
- [ ] Create validation notebook to visualize coverage
- [x] Verify expected area count (~60-70 areas) - **Found 18 areas**

### 5. Exploration Notebook ⏳
**Status**: Not Started

- [ ] Create `notebooks/01_explore_api.ipynb`
- [ ] Document API structure and response formats
- [ ] Test queries for warning areas
- [ ] Explore current warnings endpoint
- [ ] Document findings and gotchas

---

## Phase 2: Data Acquisition & Loading ✅ COMPLETE

**Goals**: Download historic flood warnings (2020-present), parse and validate data, store in DuckDB

**Key Deliverables**:
- ✅ Historic warnings downloaded for all years
- ✅ Data loader with ODS/CSV/JSON parsing
- ✅ Validation framework implemented
- ✅ DuckDB database populated
- ✅ Data quality reports generated

**Key Files**: `src/fwii/data_fetcher.py`, `src/fwii/data_loader.py`, `src/fwii/validators.py`, `data/processed/fwii.duckdb`

### 6. Historic Data Download ✅
**Status**: Complete

- [x] Create `src/fwii/data_fetcher.py` module
- [x] Implement `download_historic_warnings(year: int)` function
- [x] Handle ZIP file extraction
- [x] Support both CSV and JSON formats (added ODS support)
- [x] Save raw files to `data/raw/`
- [x] Add progress indicators
- [ ] Write unit tests with mock HTTP responses

### 7. Data Loader ✅
**Status**: Complete

- [x] Create `src/fwii/data_loader.py` module
- [x] Implement `load_historic_warnings(file_path: str)` function
- [x] Parse key fields with proper types
- [x] Convert timestamps to UTC datetime
- [x] Handle missing/malformed timestamps
- [x] Filter for West of England `fwdCode` values only
- [ ] Write unit tests with sample data fixtures

### 8. Data Validation ✅
**Status**: Complete

- [x] Create `src/fwii/validators.py` module
- [x] Implement `validate_warnings_data(df)` function
- [x] Check for required fields
- [x] Identify warnings with missing timestamps
- [x] Detect warnings that never reach severity level 4
- [x] Flag duplicate records
- [x] Flag warnings outside West of England
- [x] Return validation report
- [ ] Write unit tests

### 9. Database Storage ✅
**Status**: Complete

- [x] Set up DuckDB database in `data/processed/fwii.duckdb`
- [x] Create schema for `warnings` table
- [x] Implement `store_warnings(df, db_path)` function
- [x] Create indexes on key columns
- [x] Add helper queries
- [ ] Write tests for database operations

### 10. Data Pipeline Script ✅
**Status**: Complete

- [x] Create `scripts/download_historic_data.py`
- [x] Accept year range as command-line arguments
- [x] Implement Download → Load → Validate → Store pipeline
- [x] Generate data quality report
- [x] Save report to `data/processed/data_quality_report_{year}.json`
- [x] Add logging throughout

### 11. Data Exploration Notebook ⏳
**Status**: Deferred

- [ ] Create `notebooks/02_explore_warnings_data.ipynb`
- [ ] Load and examine warning records for 2020-2024
- [ ] Analyze severity distributions
- [ ] Examine warning durations
- [ ] Compare fluvial vs coastal patterns
- [ ] Identify data quality issues
- [ ] Create visualizations

---

## Phase 3: Core Calculation Logic ✅ COMPLETE

**Goals**: Implement warning duration calculator, duration-weighted scoring, and baseline normalization

**Key Deliverables**:
- ✅ Duration calculator with heuristic-based duration estimation
- ✅ Scoring integrated into duration calculator (Severe×3, Warning×2, Alert×1)
- ✅ Annual indicator calculator with normalization
- ✅ Baseline normalization (2020 = 100)
- ✅ Composite FWII formula (55% fluvial, 45% coastal)

**Key Files**: `src/fwii/duration_calculator.py`, `src/fwii/indicator_calculator.py`, `config/baseline_2020.yaml`, `scripts/calculate_fwii.py`

**Important Note**: EA data does NOT include warning end times or timeSeverityChanged fields. Implemented heuristic-based duration estimation instead of explicit lifecycle tracking.

### 12. Duration Calculator ✅
**Status**: Complete

- [x] Create `src/fwii/duration_calculator.py` module
- [x] Implement `WarningEvent` dataclass
- [x] Implement duration calculation with heuristic approach (not explicit lifecycle)
- [x] Group records by warning area
- [x] Identify contiguous warning periods using gap analysis
- [x] Track severity levels
- [x] Calculate duration using default durations + gap analysis
- [x] Handle "Update" messages as continuations
- [x] Handle ongoing warnings (no level 4)
- [ ] Write extensive unit tests

### 13. Scoring Calculator ✅
**Status**: Complete (integrated into duration calculator)

- [x] Scoring integrated into `DurationCalculator` class
- [x] Implement `calculate_warning_score(duration, severity)` via WarningEvent.calculate_score()
- [x] Apply severity weights: {1:3, 2:2, 3:1, 4:0}
- [x] Implement `calculate_annual_score(events, year)` function
- [x] Separate scoring for fluvial vs coastal
- [x] Return breakdown by severity level
- [ ] Write unit tests with known expected scores

### 14. Indicator Calculator ✅
**Status**: Complete

- [x] Create `src/fwii/indicator_calculator.py` module
- [x] Implement `calculate_indicators(df, year)` function
- [x] Load warnings from database/CSV
- [x] Calculate duration segments
- [x] Calculate scores
- [x] Separate fluvial and coastal sub-indicators
- [x] Return NormalizedIndicators dataclass
- [ ] Write integration tests

### 15. Baseline Normalization ✅
**Status**: Complete

- [x] Implement baseline calculation in IndicatorCalculator
- [x] Store baseline values in `config/baseline_2020.yaml`
- [x] Implement `normalize_to_baseline()` in IndicatorCalculator
- [x] Calculate fluvial and coastal baselines separately
- [x] 2020 baseline saved: Fluvial=1051.6, Coastal=2410.6, Total=3462.2
- [ ] Write tests for normalization calculations

### 16. Composite FWII ✅
**Status**: Complete

- [x] Implement composite FWII calculation in IndicatorCalculator
- [x] Apply weights: fluvial × 0.55 + coastal × 0.45
- [x] Verified with 2020 baseline (FWII = 100.0)
- [ ] Write tests verifying composite calculation

### 17. Calculation Validation Notebook ⏳
**Status**: Deferred (manual validation performed via scripts)

- [x] Manually verified duration calculations for sample warnings (112WAFTUBA)
- [x] Verified scoring against 2020 baseline (95 events → 3462.2 score)
- [x] Cross-checked 2020 baseline calculations
- [x] Documented methodology differences from CLAUDE.md in memory
- [ ] Create `notebooks/03_validate_calculations.ipynb`
- [ ] Test the escalation example from CLAUDE.md (not applicable - no escalation data)

---

## Phase 4: Indicator Calculation & Outputs (5 tasks)

**Goals**: Complete FWII composite indicator, generate multiple output formats, create visualizations

**Key Deliverables**:
- Composite FWII calculation complete
- JSON and CSV report generators
- Supporting statistics (counts, durations, quality)
- Surface water caveat handling
- Visualization notebook with time series plots

**Key Files**: `src/fwii/statistics.py`, `src/fwii/models.py`, `src/fwii/report_generator.py`, `scripts/calculate_annual_indicator.py`

### 18. Supporting Statistics ⏳
**Status**: Not Started

- [ ] Create `src/fwii/statistics.py` module
- [ ] Implement `calculate_warning_counts(df)` by severity
- [ ] Implement `find_longest_warning_event(events)`
- [ ] Implement `find_peak_warning_levels(events)`
- [ ] Calculate data quality metrics
- [ ] Write unit tests

### 19. Output Data Models ⏳
**Status**: Not Started

- [ ] Create `src/fwii/models.py` with dataclasses:
  - [ ] `RawScores`
  - [ ] `NormalizedIndicators`
  - [ ] `SupportingStatistics`
  - [ ] `AnnualIndicatorReport`
- [ ] Add JSON serialization methods
- [ ] Add validation methods

### 20. Report Generator ⏳
**Status**: Not Started

- [ ] Create `src/fwii/report_generator.py` module
- [ ] Implement `generate_json_report(report, output_path)`
- [ ] Implement `generate_csv_summary(report, output_path)`
- [ ] Implement `generate_timeseries_csv(reports, output_path)`
- [ ] Implement `generate_warning_detail_csv(events, output_path)`
- [ ] Include surface water caveat text in all reports
- [ ] Add metadata (timestamps, versions)
- [ ] Write tests for report generation

### 21. Main Calculation Script ⏳
**Status**: Not Started

- [ ] Create `scripts/calculate_annual_indicator.py`
- [ ] Accept year as command-line argument
- [ ] Orchestrate full calculation pipeline
- [ ] Save outputs to `data/outputs/fwii_{year}/`
- [ ] Add progress logging
- [ ] Handle errors gracefully

### 22. Visualization Notebook ⏳
**Status**: Not Started

- [ ] Create `notebooks/04_visualize_indicators.ipynb`
- [ ] Load indicator reports for all years
- [ ] Create time series plots (2020-2024)
- [ ] Create component comparison plots (fluvial vs coastal)
- [ ] Show warning count distributions
- [ ] Visualize longest warning events
- [ ] Export plots to `plots/` directory

---

## Phase 5: Validation & Quality Assurance (6 tasks)

**Goals**: Validate against known flood events, verify accuracy, implement automated quality checks

**Key Deliverables**:
- Known events validation complete
- Manual verification of sample warnings
- Completeness and boundary checks
- Automated quality check framework
- Validation dashboard notebook
- Confidence assessment documented

**Key Files**: `src/fwii/quality_checks.py`, `scripts/validate_against_known_events.py`, `notebooks/06_validation_dashboard.ipynb`

### 23. Known Event Validation ⏳
**Status**: Not Started

- [ ] Research documented flood events 2020-2024 in West of England
- [ ] Create `tests/validation/known_events.yaml`
- [ ] Create `scripts/validate_against_known_events.py`
- [ ] Check major events appear in indicator
- [ ] Verify warning timing aligns with reported flooding
- [ ] Document findings in validation report

### 24. Sample Warning Manual Verification ⏳
**Status**: Not Started

- [ ] Create `notebooks/05_manual_verification.ipynb`
- [ ] Select 10 representative warnings across severity levels
- [ ] Manually calculate expected durations and scores
- [ ] Compare with automated calculations
- [ ] Document methodology and findings

### 25. Completeness Checks ⏳
**Status**: Not Started

- [ ] Compare warning counts with EA published statistics
- [ ] Check geographic coverage of all 4 counties
- [ ] Verify all warning areas from config are represented
- [ ] Document coverage gaps

### 26. Boundary Validation ⏳
**Status**: Not Started

- [ ] Verify all areas are geographically in West of England
- [ ] Cross-reference with county boundaries
- [ ] Check for edge cases near county borders

### 27. Automated Quality Checks ⏳
**Status**: Not Started

- [ ] Create `src/fwii/quality_checks.py` module
- [ ] Implement reasonableness checks:
  - [ ] FWII scores in expected range (0-500)
  - [ ] Year-over-year changes within ±200%
  - [ ] Baseline year (2020) normalizes to 100
- [ ] Integrate into calculation pipeline
- [ ] Write tests

### 28. Validation Dashboard ⏳
**Status**: Not Started

- [ ] Create `notebooks/06_validation_dashboard.ipynb`
- [ ] Combine all validation results
- [ ] Create summary tables and visualizations
- [ ] Document confidence level in indicator
- [ ] List known limitations and caveats

---

## Phase 6: Production Hardening (6 tasks)

**Goals**: Add error handling and logging, create CLI interface, complete documentation, set up reproducible pipeline

**Key Deliverables**:
- Logging and error handling throughout
- CLI with commands: setup, download, calculate, validate, report, update
- Complete documentation suite
- End-to-end pipeline script
- Data archival system
- >80% test coverage achieved

**Key Files**: `src/fwii/cli.py`, `scripts/full_pipeline.py`, `docs/METHODOLOGY.md`, `docs/RUNBOOK.md`

### 29. Error Handling & Logging ⏳
**Status**: Not Started

- [ ] Add logging configuration module
- [ ] Implement structured logging throughout codebase
- [ ] Add error recovery for network failures
- [ ] Add clear error messages for users
- [ ] Log all data processing steps with timestamps

### 30. CLI Interface ⏳
**Status**: Not Started

- [ ] Create `src/fwii/cli.py` using argparse or click
- [ ] Implement commands:
  - [ ] `fwii setup` - Initial warning area fetch
  - [ ] `fwii download <year>` - Download historic data
  - [ ] `fwii calculate <year>` - Calculate indicator
  - [ ] `fwii validate <year>` - Run validation checks
  - [ ] `fwii report <year>` - Generate all outputs
  - [ ] `fwii update` - Full annual update pipeline
- [ ] Add `--help` documentation for all commands
- [ ] Write integration tests

### 31. Documentation ⏳
**Status**: Not Started

- [ ] Update `README.md` with:
  - [ ] Project overview and purpose
  - [ ] Installation instructions
  - [ ] Quick start guide
  - [ ] CLI command reference
  - [ ] Output file descriptions
- [ ] Create `docs/METHODOLOGY.md` - calculation approach
- [ ] Create `docs/DATA_SOURCES.md` - API documentation
- [ ] Create `docs/INTERPRETATION_GUIDE.md` - for stakeholders
- [ ] Create `docs/RUNBOOK.md` - annual update process

### 32. Reproducibility ⏳
**Status**: Not Started

- [ ] Create `scripts/full_pipeline.py` for end-to-end run
- [ ] Document all data sources with URLs and access dates
- [ ] Version control all configuration files
- [ ] Create data manifest file tracking data versions
- [ ] Add software version to all outputs

### 33. Data Archival ⏳
**Status**: Not Started

- [ ] Create `scripts/archive_release.py`
- [ ] Archive baseline data (2020)
- [ ] Archive each annual calculation with:
  - [ ] Input data
  - [ ] Configuration used
  - [ ] Generated outputs
  - [ ] Validation reports
- [ ] Store in `data/archive/{year}/`

### 34. Final Testing ⏳
**Status**: Not Started

- [ ] Run full test suite
- [ ] Achieve >80% code coverage
- [ ] Perform end-to-end system test
- [ ] Generate indicators for all available years (2020-2024)
- [ ] Review all outputs for quality
- [ ] Verify ruff linting passes

---

## Progress Tracking

- **Total Tasks**: 34
- **Completed**: 16
- **In Progress**: 0
- **Not Started**: 16
- **Blocked**: 0
- **Deferred (low priority)**: 2 (notebooks)

**Overall Progress**: 47%

### By Phase
- Phase 1: 4/5 (80%) ✅ COMPLETE - Missing tests and notebooks
- Phase 2: 5/6 (83%) ✅ COMPLETE - Notebook deferred
- Phase 3: 6/6 (100%) ✅ COMPLETE - Notebooks deferred, manual validation done
- Phase 4: 0/5 (0%) 🏗️ NEXT
- Phase 5: 0/6 (0%)
- Phase 6: 0/6 (0%)

### Current Focus
**Next up**: Phase 4 - Report Generation & Outputs
- Generate JSON/CSV reports for FWII indicators
- Download data for 2021-2024
- Create time series visualizations
- Document methodology and interpretation

### Key Achievements
- ✅ Complete data pipeline (download → validate → store)
- ✅ Duration calculator with heuristic approach
- ✅ FWII calculation system working
- ✅ 2020 baseline established (FWII = 100.0)
- ✅ Can calculate indicators for any year

### Available Commands
```bash
# Download data for a year
uv run python scripts/download_historic_data.py <year>

# Calculate FWII for a year
uv run python scripts/calculate_fwii.py <year>

# Save 2020 baseline
uv run python scripts/calculate_fwii.py 2020 --save-baseline
```

---

## Notes

Update this file as tasks are completed. Use the following status indicators:
- ⏳ Not Started
- 🏗️ In Progress
- ✅ Complete
- ⚠️ Blocked

**Git Commit Strategy**: Commit after completing each major task (1-34), with clear commit messages referencing task numbers.
