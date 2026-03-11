# Code Review: Remaining Items

Tracked from critical code review on 2026-03-11.
Blocking issues (#1-5) already fixed in commit `12ca72f`.
Items #6-15, #17 fixed in follow-up commit (see below).

## Required Changes

### #6 Missing encoding='utf-8' in scripts -- DONE

**Files:**
- `scripts/download_historic_data.py:192` -- JSON write (validation report)
- `scripts/download_historic_data.py:319` -- JSON write (pipeline results)
- `scripts/fetch_warning_areas.py:103` -- YAML write (warning areas)

**Fix:** Added `encoding='utf-8'` to all three `open()` calls.

---

### #7 DurationConfig type hints -- DONE

**File:** `src/fwii/duration_calculator.py:29-30`

**Fix:** Changed to `dict[int, float] | None = None` for both fields.

---

### #8 Trend report subprocess failure swallowed -- DONE

**File:** `scripts/run_pipeline.py:93`

**Fix:** Captured return value and check `result.returncode`, returning 1 on failure.

---

### #9 cli.py uses runpy instead of direct imports -- DONE

**File:** `src/fwii/cli.py`

**Fix:** Replaced `runpy.run_path` with `importlib.util` to import script modules by path. Each entry point calls `module.main()` and passes the return code to `sys.exit()`.

---

### #10 DataLoadError re-wrapping -- DONE

**File:** `src/fwii/data_loader.py:140-143`

**Fix:** Added `except DataLoadError: raise` before the generic `except Exception` catch.

---

### #11 Silent file-load failures in load_directory -- DONE

**File:** `src/fwii/data_loader.py:391`

**Fix:** Tracked failures in a list and log a warning with failed file names after processing all files.

---

### #12 ValueError on malformed CSV filenames -- DONE

**File:** `scripts/generate_trend_report.py:28-30`

**Fix:** Replaced generator expression with explicit loop using try/except around `int()` conversion.

---

### #13 Manual sys.argv parsing in calculate_fwii.py -- DONE

**File:** `scripts/calculate_fwii.py:28-36`

**Fix:** Replaced manual `sys.argv` parsing with `argparse`, matching the pattern in other scripts.

---

## Suggestions (Lower Priority)

### #14 IndicatorCalculator always instantiates Config() -- DONE

**File:** `src/fwii/indicator_calculator.py:90`

**Fix:** Added optional `config` parameter; `Config()` is now lazy-loaded via a property only when needed.

---

### #15 FloodMonitoringClient not used as context manager -- DONE

**File:** `scripts/fetch_warning_areas.py:26`

**Fix:** Replaced manual `close()` in `finally` with `with FloodMonitoringClient(config) as client:`.

---

### #16 Test coverage gaps -- TODO

Missing tests for:
- `validators.py` -- no tests at all
- `data_fetcher.py` -- at least `_extract_zip` with a fixture ZIP
- Scripts -- no integration tests
- "Update" prefix stripping in `_normalize_schema`
- `test_config.py` hits real filesystem with no mocking

---

### #17 is_update regex matches too broadly -- DONE

**File:** `src/fwii/duration_calculator.py:87`

**Fix:** Changed pattern from `(?i)update` to `(?i)^update\s` to anchor to start-of-string with trailing whitespace.
