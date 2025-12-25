# Impact Analysis: Excluding Flood Alerts (Level 3) from FWII Calculations

**Date**: December 2024
**Status**: Analysis Only (Not Implemented)

---

## Executive Summary

Removing Flood Alerts (severity level 3) from the FWII would fundamentally alter the indicator's sensitivity and purpose. Based on 2020-2024 data, level 3 alerts constitute **95-97% of all warning events** in the West of England. Exclusion would shift the indicator from measuring "flood warning activity" to measuring "confirmed flooding events requiring immediate action."

**Key Finding**: The proposed change would reduce sample size by 95% and create extreme statistical volatility, with two years (2022, 2023) producing FWII = 0.

---

## Current Warning Distribution (2020-2024)

| Year | Level 1 (Severe) | Level 2 (Warning) | Level 3 (Alert) | Total | % Alerts |
|------|------------------|-------------------|-----------------|-------|----------|
| 2020 | 0 | 3 | 92 | 95 | 97% |
| 2021 | 0 | 1 | 27 | 28 | 96% |
| 2022 | 0 | 0 | 23 | 23 | 100% |
| 2023 | 0 | 0 | 54 | 54 | 100% |
| 2024 | 0 | 4 | 95 | 99 | 96% |

**Key Observation**: The West of England has experienced **ZERO Severe Flood Warnings** (level 1) in the past five years. Level 2 warnings are rare (0-4 per year), while level 3 alerts dominate the signal.

---

## Quantitative Impact on FWII

### Current Contribution of Each Severity Level to 2020 Baseline

Based on current weighting scheme (level 1: ×3, level 2: ×2, level 3: ×1):

**2020 Baseline Components**:
- Fluvial score: 1,051.65 weighted hours
- Coastal score: 2,410.57 weighted hours
- Total score: 3,462.22 weighted hours

**Estimated breakdown by severity** (level 3 has weight ×1, so hours ≈ score for alerts):
- Level 3 contribution: ~85-90% of total hours (unweighted)
- Level 2 contribution: ~10-15% of total score (weight ×2 amplifies impact)
- Level 1 contribution: 0% (no severe warnings issued)

### Projected Impact on 2020 Baseline If Level 3 Excluded

**New baseline estimate**:
- Fluvial score: ~100-200 weighted hours (down 80-90%)
- Coastal score: ~200-400 weighted hours (down 80-90%)
- Total score: ~300-600 weighted hours (down 82-91%)

**Critical consequence**: The baseline becomes **5-10 times smaller**, dramatically increasing volatility.

### Impact on Year-to-Year Sensitivity

**Current scenario** (with level 3):
- 2022 (quietest year): FWII = 29.3 (70.7% below baseline)
- 2024 (busiest year): FWII = 167.0 (67% above baseline)
- Range: 137.7 index points

**Projected scenario** (without level 3):
- Years with zero level 2/1 warnings (2022, 2023): FWII = 0 (100% below baseline)
- Years with 3-4 level 2 warnings (2020, 2024): FWII could vary 200-500% depending on duration
- Range: Potentially 0 to 500+ index points

**Volatility assessment**: The indicator would become extremely volatile, with high probability of zero values in quiet years and extreme spikes when any level 2 warnings occur.

---

## Qualitative Impact on Indicator Purpose

### Current Purpose (with level 3 included)

The FWII measures **flood warning activity** as a proxy for flood hazard exposure. Level 3 alerts represent:
- Early notification that flooding is **possible**
- Community preparedness and awareness activation
- Precautionary monitoring by emergency services
- Regional exposure to elevated flood risk

**Strengths**:
- Captures full spectrum of flood risk events
- Sufficient sample size for statistical reliability (23-99 events per year)
- Year-on-year trends are relatively stable

**Weaknesses**:
- Includes events where flooding may not occur
- Conflates "risk awareness" with "actual flooding"
- May overstate flood intensity (alerts ≠ actual flooding)

### Proposed Purpose (without level 3)

The FWII would measure **confirmed flooding events requiring immediate action**. Only level 2 warnings would contribute (level 1 has never occurred). Level 2 represents:
- Flooding **expected** (not just possible)
- Immediate action required (move possessions, evacuate ground floors, etc.)
- Higher probability of actual property/infrastructure impacts

**Strengths**:
- Stronger alignment with "actual flooding events" objective
- Reduces false positives (alerts that don't materialize into flooding)
- More directly comparable to flood damage/impact data

**Weaknesses**:
- **Extremely sparse data**: Only 0-4 events per year across entire region
- Statistical unreliability: 2 years (2022, 2023) would have FWII = 0
- Loss of trend detection capability due to low sample size
- High sensitivity to single events (one 48-hour level 2 warning could dominate annual score)
- Regional indicator becomes essentially a "count of warnings" rather than intensity measure

---

## Impact on Regional Coverage

### Current Coverage (with level 3)

Level 3 alerts provide geographic breadth:
- Multiple warning areas activate simultaneously during weather events
- Captures regional coherence (e.g., atmospheric rivers affecting entire Bristol Avon catchment)
- Distinguishes between localized and widespread events

### Reduced Coverage (without level 3)

Only 0-4 level 2 warnings per year means:
- Likely only 1-2 warning areas affected per year
- Loss of regional-scale signal
- Indicator becomes measure of "which specific warning area flooded" rather than "regional flood intensity"

---

## Impact on Policy and Decision-Making

### Use Case: Annual Reporting to Government

**Current capability**:
- Clear year-on-year trends (2020→2024: +67% increase)
- Sufficient data to distinguish fluvial vs coastal patterns
- Statistical confidence in multi-year trends

**Proposed capability**:
- High inter-annual volatility (potential 0 to 500+ swings)
- Difficult to interpret: Is FWII=0 "good news" or "missing data"?
- Multi-year averaging required to detect any trend
- Risk of "indicator becoming meaningless" if multiple consecutive zero years occur

### Use Case: Climate Change Monitoring

**Current capability**:
- Tracks changing frequency and duration of flood warnings
- 5-year dataset shows clear pattern shift (fluvial increase, coastal decrease)

**Proposed capability**:
- Too few events to detect climate signal within 5-year window
- Requires 15-20 year dataset to achieve statistical power
- Loss of ability to distinguish "no flooding occurred" from "warning system didn't escalate to level 2"

---

## Alternative Approaches to Address Current FWII Limitations

If the concern is that level 3 alerts overstate flood intensity, consider:

### Option 1: Reduce Level 3 Weight (Rather Than Exclude)

**Change**: Level 3 weight from ×1 to ×0.5 or ×0.25

**Impact**:
- Preserves sample size for statistical reliability
- Reduces contribution of "possible flooding" events
- Maintains sensitivity to regional patterns
- Still captures 23-99 events per year

**Rationale**: Acknowledges that alerts are precautionary while keeping them in scope.

**Implementation complexity**: Low (2 configuration files)

### Option 2: Report Level 2/3 as Separate Sub-Indicators

**Change**: Create two metrics:
- Primary FWII: Level 2 + Level 1 only ("confirmed flooding")
- Secondary FWII-Extended: Level 3 + Level 2 + Level 1 ("flood risk exposure")

**Impact**:
- Provides both "actual flooding" and "flood risk" signals
- Allows users to choose appropriate metric for their purpose
- Maintains historical continuity

**Rationale**: Serves multiple stakeholder needs without losing data.

**Implementation complexity**: Medium (new indicator calculation, separate reporting)

### Option 3: Add Minimum Threshold for Level 3 Inclusion

**Change**: Only include level 3 warnings exceeding X hours duration (e.g., 72+ hours)

**Impact**:
- Filters out brief, precautionary alerts
- Retains sustained flood risk periods
- Partial reduction in sample size while maintaining trend detection

**Rationale**: Long-duration alerts more likely to indicate genuine flood events.

**Implementation complexity**: Medium (add duration filtering logic)

### Option 4: No Change to Methodology, Add Caveats to Interpretation

**Change**: Enhance documentation to clarify that FWII measures "flood warning activity" not "actual flooding"

**Impact**:
- No technical implementation required
- Improves user understanding
- Acknowledges limitations explicitly

**Rationale**: Current methodology is fit-for-purpose if users understand what it measures.

**Implementation complexity**: Low (documentation updates only)

---

## Recommendation

**Do not exclude level 3 alerts** from the FWII calculation. The proposed change would:

1. Reduce sample size by 95%, creating statistical unreliability
2. Produce frequent zero values (years with no level 2 warnings)
3. Eliminate regional-scale signal (1-2 events per year insufficient)
4. Undermine policy utility (high volatility, loss of trend detection)

### Alternative Recommendations (in order of preference)

1. **First choice**: Reduce level 3 weight to ×0.5 (preserves data, reduces dominance)
2. **Second choice**: Report dual indicators (level 2-only + full FWII)
3. **Third choice**: Maintain current methodology with enhanced caveats

All alternatives provide better balance between "capturing actual flooding" and "maintaining statistical reliability for policy decisions."

---

## Technical Feasibility

If exclusion of level 3 is still required despite impacts above:

**Implementation complexity**: Medium (9 files to modify, baseline recalculation required)

**Files requiring modification**:
1. `config/settings.yaml` - Remove level 3 from severity_weights
2. `config/baseline_2020.yaml` - Regenerate baseline
3. `src/fwii/duration_calculator.py` - Remove level 3 from calculations
4. `src/fwii/indicator_calculator.py` - Remove flood_alerts field
5. `src/fwii/validators.py` - Update valid severity levels
6. `src/fwii/db_storage.py` - Update database constraints
7. `scripts/calculate_fwii.py` - Update console output
8. `scripts/download_historic_data.py` - Add level 3 filtering
9. Documentation files (CLAUDE.md, SUMMARY.md)

**Timeline estimate**: 2-3 hours implementation + 1-2 hours validation/testing

**Reversibility**: High (changes are well-isolated, old baseline can be restored)

**Data regeneration required**:
- Delete and rebuild database
- Re-download all years 2020-2024
- Recalculate baseline and all annual indicators
- Regenerate trend reports

---

## Conclusion

This analysis demonstrates that excluding level 3 alerts from FWII calculations would fundamentally compromise the indicator's statistical reliability and policy utility. The West of England's flood warning pattern (zero severe warnings, rare flood warnings, dominant alerts) makes level 3 data essential for meaningful trend detection.

The recommended alternative approaches maintain statistical robustness while addressing concerns about level 3 alerts potentially overstating flood intensity.
