# Fix Plan: Severity Mapping & Duplicate ODS Loading

## Problem

The `SEVERITY_MAP` in `data_loader.py` uses exact string matching and only handles 4 TYPE values. The EA data contains variants that silently map to null severityLevel (weight=0, score=0):

| TYPE in data | Current mapping | Correct severity |
|---|---|---|
| `Flood Alert` | 3 | 3 |
| `Update Flood Alert` (111 rows) | **null** | 3 |
| `Flood Watch` (77 rows) | **null** | 3 (pre-2011 equivalent) |
| `Flood alert` (17 rows) | **null** | 3 |
| `Flood Warning` | 2 | 2 |

This causes the 2024 composite FWII to compute as 148 instead of the correct 167. The coastal index is most affected (31.5 vs 61.7) because 40 of 44 null-severity rows are coastal.

A secondary issue: two ODS files in `data/raw/` are both loaded and concatenated, doubling record counts (doesn't affect scores but inflates event counts).

## Stage 1: Fix severity mapping in data_loader.py

**File**: `src/fwii/data_loader.py` -- `_normalize_schema` method (line ~236)

Replace the exact-match `SEVERITY_MAP` dict with case-insensitive, prefix-tolerant mapping:
- Strip "Update " prefix before matching
- Case-insensitive comparison
- Map "Flood Watch" to severity 3 (pre-2011 equivalent of Flood Alert)

**Verify**: Run `uv run python -c` to load one ODS file and confirm zero null severityLevel rows for WoE data.

**Commit**: `fix: handle Update/Watch/lowercase severity types in schema mapping`

## Stage 2: Fix duplicate ODS file loading in download_historic_data.py

**File**: `scripts/download_historic_data.py` -- `process_single_year` function (line ~111)

When multiple ODS files exist, load only the **most recent** (sort by filename, take last). The filenames are prefixed with `YYYYMM` so lexicographic sort works.

**Verify**: Run pipeline for a single year (e.g. 2024) and confirm record count matches unique count (99 not 198).

**Commit**: `fix: load only latest ODS file when multiple exist`

## Stage 3: Recalculate baseline and verify FWII

- Run `uv run fwii-pipeline 2020 2025 --full` (or 2024 if 2025 data incomplete)
- Confirm 2020 baseline recalculated with correct severity mapping
- Confirm 2024 composite FWII approximately 167.0 (matching README)
- Update `config/baseline_2020.yaml` if values changed

**Commit**: `fix: recalculate baseline with corrected severity mapping`

## Stage 4: Update README if figures changed

Compare new timeseries output against README table. Update any figures that shifted due to the corrected mapping.

**Commit**: `docs: update results table with corrected FWII values`
