# Code Review: Remaining Items

Tracked from critical code review on 2026-03-11.
Blocking issues (#1-5) already fixed in commit `12ca72f`.

## Required Changes

### #6 Missing encoding='utf-8' in scripts

**Files:**
- `scripts/download_historic_data.py:192` -- JSON write (validation report)
- `scripts/download_historic_data.py:319` -- JSON write (pipeline results)
- `scripts/fetch_warning_areas.py:103` -- YAML write (warning areas)

**Fix:** Add `encoding='utf-8'` to all three `open()` calls.

---

### #7 DurationConfig type hints

**File:** `src/fwii/duration_calculator.py:29-30`

```python
# Current (wrong)
default_durations: dict[int, float] = None
severity_weights: dict[int, float] = None

# Correct
default_durations: dict[int, float] | None = None
severity_weights: dict[int, float] | None = None
```

---

### #8 Trend report subprocess failure swallowed

**File:** `scripts/run_pipeline.py:93`

`subprocess.run` for the trend report ignores the return code. If it fails, the pipeline reports success.

**Fix:** Check `result.returncode` or use `check=True`.

---

### #9 cli.py uses runpy instead of direct imports

**File:** `src/fwii/cli.py`

`runpy.run_path` with `sys.argv[0]` mutation is fragile. `SystemExit` propagates unpredictably.

**Fix:** Import each script's `main()` function directly and call it. Handle return codes properly.

---

### #10 DataLoadError re-wrapping

**File:** `src/fwii/data_loader.py:140-143`

Generic `except Exception` catches and re-wraps `DataLoadError` from inner methods, losing the original message structure.

**Fix:** Add `except DataLoadError: raise` before the generic catch.

---

### #11 Silent file-load failures in load_directory

**File:** `src/fwii/data_loader.py:391`

Files that fail to load are silently skipped with a log message. Caller has no visibility.

**Fix:** Track failures and either raise after all files are attempted or return them alongside the DataFrame.

---

### #12 ValueError on malformed CSV filenames

**File:** `scripts/generate_trend_report.py:28-30`

`int(p.stem.split("_")[1])` crashes on non-numeric suffixes matching the glob.

**Fix:** Wrap in try/except or use a regex to validate the filename before parsing.

---

### #13 Manual sys.argv parsing in calculate_fwii.py

**File:** `scripts/calculate_fwii.py:28-36`

Every other script uses argparse. This one parses `sys.argv` manually with no validation.

**Fix:** Replace with argparse, matching the pattern in other scripts.

---

## Suggestions (Lower Priority)

### #14 IndicatorCalculator always instantiates Config()

**File:** `src/fwii/indicator_calculator.py:90`

Creates `Config()` unconditionally even when baseline is provided externally.

**Fix:** Accept `config` as optional parameter, lazy-load if needed.

---

### #15 FloodMonitoringClient not used as context manager

**File:** `scripts/fetch_warning_areas.py:26`

Class has `__enter__`/`__exit__` but script uses manual `close()` in `finally`.

**Fix:** Use `with FloodMonitoringClient(config) as client:` consistently.

---

### #16 Test coverage gaps

Missing tests for:
- `validators.py` -- no tests at all
- `data_fetcher.py` -- at least `_extract_zip` with a fixture ZIP
- Scripts -- no integration tests
- "Update" prefix stripping in `_normalize_schema`
- `test_config.py` hits real filesystem with no mocking

---

### #17 is_update regex matches too broadly

**File:** `src/fwii/duration_calculator.py:87`

`str.contains("(?i)update")` matches "update" anywhere in the string. Should anchor to prefix.

**Fix:** Change to `str.contains("(?i)^update\\s")` or similar.
