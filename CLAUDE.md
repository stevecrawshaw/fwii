# West of England Regional Flood Monitoring Indicator

## Project Overview

This project develops a Regional Flood Warning Intensity Index (FWII) for the West of England, comprising Bristol, Bath and North East Somerset (B&NES), South Gloucestershire, and North Somerset. The indicator supports annual reporting to government against a climate resilience outcome in an outcomes framework.

The geographic scope corresponds broadly with the Bristol Avon catchment, plus rivers in North Somerset and low-lying coastal areas along the Severn Estuary.

### Indicator Purpose

- Track actual flooding events (not risk assessments or near-misses)
- Report annually with year-on-year comparability
- Be meaningful to decision-makers indicating changing flood risk
- Be based on rigorous monitoring and open data
- Use 2020 onwards as the baseline period

### Indicator Structure

The indicator has three components:

1. **Fluvial (River) Flood Intensity Sub-indicator** - Duration-weighted flood warning days for river flooding
2. **Coastal/Tidal Flood Intensity Sub-indicator** - Duration-weighted flood warning days for tidal flooding
3. **Surface Water Flooding** - Reported as "not measurable" with explicit caveat, referencing Section 19 investigation counts from LLFAs where available

Plus one **Composite Indicator**: Regional Flood Warning Intensity Index (FWII) combining fluvial and coastal scores.

---

## Data Sources

### Primary Data Source: Historic Flood Warnings Dataset

**Dataset URL**: <https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590>

**Description**: Complete record of all Flood Alerts, Flood Warnings, and Severe Flood Warnings issued by the Environment Agency from January 2006 to present.

**Update Frequency**: Quarterly

**Format**: Downloadable ZIP files containing CSV/JSON

**Key Fields**:

- `fwdCode` - Flood warning area identifier (use to filter for West of England)
- `severityLevel` - 1=Severe Flood Warning, 2=Flood Warning, 3=Flood Alert, 4=Warning No Longer in Force
- `timeRaised` - ISO 8601 timestamp when warning was issued
- `timeSeverityChanged` - Timestamp when severity level changed
- `timeMessageChanged` - Timestamp when warning message was updated
- `isTidal` - Boolean indicating coastal/tidal (true) vs fluvial/river (false) warning

**Licence**: Open Government Licence v3.0

**Important Notes**:

- Data bridges two systems: Floodline Warnings Direct (Jan 2006 - Apr 2017) and current Flood Warning System (Apr 2017 onwards)
- Surface water warnings are NOT included - the EA states "warnings for surface water flooding are not yet available"

### Secondary Data Source: Real-Time Flood Monitoring API

**API Base URL**: <https://environment.data.gov.uk/flood-monitoring/>

**API Documentation**: <https://environment.data.gov.uk/flood-monitoring/doc/reference>

**Authentication**: None required

**Rate Limits**: None documented, but implement polite request spacing (1 request per second recommended)

**Key Endpoints**:

#### Flood Warning Areas

```
GET https://environment.data.gov.uk/flood-monitoring/id/floodAreas
```

Returns all flood warning area definitions including:

- `fwdCode` - Unique identifier
- `label` - Human-readable name
- `county` - County name (use to filter for West of England)
- `riverOrSea` - River/sea name
- `polygon` - GeoJSON boundary (via linked resource)

Filter by county:

```
GET https://environment.data.gov.uk/flood-monitoring/id/floodAreas?county=Bristol
GET https://environment.data.gov.uk/flood-monitoring/id/floodAreas?county=Bath%20and%20North%20East%20Somerset
GET https://environment.data.gov.uk/flood-monitoring/id/floodAreas?county=South%20Gloucestershire
GET https://environment.data.gov.uk/flood-monitoring/id/floodAreas?county=North%20Somerset
```

#### Current Flood Warnings

```
GET https://environment.data.gov.uk/flood-monitoring/id/floods
```

Returns currently active warnings. Filter by severity:

```
GET https://environment.data.gov.uk/flood-monitoring/id/floods?severity=1  # Severe warnings only
```

**Important**: This endpoint returns CURRENT warnings only - historical data requires the Historic Flood Warnings dataset above.

#### Monitoring Stations

```
GET https://environment.data.gov.uk/flood-monitoring/id/stations
```

Filter by catchment:

```
GET https://environment.data.gov.uk/flood-monitoring/id/stations?catchmentName=Bristol%20Avon%20Little%20Avon%20Axe%20and%20North%20Somerset%20St
```

#### Station Readings

```
GET https://environment.data.gov.uk/flood-monitoring/id/stations/{stationId}/readings
```

Returns water level readings. Add parameters:

- `since` - ISO 8601 datetime
- `_limit` - Maximum records to return

### Supplementary Data Source: Hydrology API (Historical Readings)

**API Base URL**: <https://environment.data.gov.uk/hydrology/>

**Description**: Quality-checked historical monitoring data with some time series extending back decades. Over 4 billion readings from ~8,000 stations.

**Use Case**: Supplementary metric for peak river level exceedances if required in future iterations.

### Supplementary Data Source: Recorded Flood Outlines

**Dataset URL**: <https://environment.data.gov.uk/dataset/8c75e700-d465-11e4-8b5b-f0def148f590>

**Description**: GIS polygons showing verified historic flooding from rivers, sea, groundwater, and surface water since 1946.

**Format**: GeoJSON, Shapefile, WFS/WMS

**Update Frequency**: Quarterly

**Important Caveat**: "The absence of coverage does not mean the area has never flooded, only that we do not currently have records."

**Use Case**: Validation of warning data against actual flood events; potential future enhancement.

### Data Archive for Historical Analysis

**Archive URL**: <https://environment.data.gov.uk/flood-monitoring/archive/>

**Format**: Daily CSV files from December 2016 onwards

**Filename Pattern**: `readings-full-{YYYY-MM-DD}.csv`

**Use Case**: Historical river/tidal level analysis if required.

---

## West of England Flood Warning Areas

The region contains approximately 60-70 flood warning areas. All use prefix **112** (Wessex region identifier).

### Area Type Prefixes

- `WAT` - Flood Alert Areas (early notification - flooding possible)
- `FW` or `FWT` - Flood Warning Areas (immediate action - flooding expected)

### Geographic Coverage by Local Authority

**Bristol**:

- Bristol Floating Harbour
- Tidal Avon from Sea Mills to Conham
- River Frome tributaries
- Brislington Brook
- Colliters Brook
- Severn Estuary at Avonmouth

**Bath and North East Somerset**:

- Mid-Bristol Avon
- River Chew catchment
- Cam Brook
- Wellow Brook
- Compton Dando area

**South Gloucestershire**:

- Upper Bristol Avon tributaries
- Severn Estuary at Severn Beach
- Bradley Brook
- Little Avon

**North Somerset**:

- Somerset coast at Portishead
- Gordano Valley
- River Yeo catchment
- River Axe
- River Banwell

### Identifying West of England Warning Areas

Use the API to retrieve all warning areas for the four counties, then maintain a master list of `fwdCode` values for filtering historic warnings. Store this list in a configuration file for reproducibility.

Example approach:

```python
WEST_OF_ENGLAND_COUNTIES = [
    "Bristol",
    "Bath and North East Somerset",
    "South Gloucestershire",
    "North Somerset"
]

# Query API for each county and compile master list of fwdCodes
```

---

## Indicator Calculation Methodology

### Duration-Weighted Flood Warning Days

For each flood warning event, calculate duration in hours and apply severity weighting.

**Severity Weights**:

- Severe Flood Warning (level 1): × 3
- Flood Warning (level 2): × 2
- Flood Alert (level 3): × 1
- Warning No Longer in Force (level 4): × 0 (exclude from calculation)

**Formula for single warning**:

```
warning_score = duration_hours × severity_weight
```

**Annual Sub-indicator**:

```
Fluvial_Score = Σ (warning_score for all fluvial warnings in year)
Coastal_Score = Σ (warning_score for all coastal warnings in year)
```

### Duration Calculation

A warning event spans from `timeRaised` to when it transitions to severity level 4 (Warning No Longer in Force) or is superseded.

**Important**: A single warning may escalate/de-escalate through multiple severity levels. Calculate duration at each severity level separately.

Example:

1. Alert raised at 09:00 (level 3)
2. Escalated to Warning at 14:00 (level 2)
3. Escalated to Severe Warning at 18:00 (level 1)
4. De-escalated to Warning at 22:00 (level 2)
5. De-escalated to Alert at 06:00 next day (level 3)
6. Warning removed at 12:00 (level 4)

Calculate:

- Alert hours: 5 hours (09:00-14:00) + 6 hours (06:00-12:00) = 11 hours × 1 = 11
- Warning hours: 4 hours (14:00-18:00) + 8 hours (22:00-06:00) = 12 hours × 2 = 24
- Severe hours: 4 hours (18:00-22:00) = 4 hours × 3 = 12
- Total score: 47

### Baseline Normalization

Use 2020 as the baseline year with a normalized score of 100.

```
Normalized_Score = (Raw_Score / Baseline_2020_Score) × 100
```

Calculate separate baseline values for:

- Fluvial_Baseline_2020
- Coastal_Baseline_2020

### Composite Indicator Formula

```
FWII = (Normalized_Fluvial_Score × 0.55) + (Normalized_Coastal_Score × 0.45)
```

**Weighting Rationale**: Based on relative properties at risk from each flood source in the West of England. These weights may be refined using NaFRA regional data.

### Interpretation Guidance

- FWII = 100: Same flood warning activity as 2020 baseline
- FWII > 100: Higher flood warning activity than baseline
- FWII < 100: Lower flood warning activity than baseline
- Year-on-year variability of ±30% is expected due to weather patterns
- Use 5-year rolling average for trend detection

---

## Surface Water Flooding Handling

Surface water flooding CANNOT be measured using Environment Agency warning data. The EA explicitly states that surface water warnings are not available.

### Required Approach

Report surface water flooding as "not measurable" with the following caveat:

> "Surface water flooding is not included in this indicator. The Environment Agency does not operate a surface water flood warning system due to the sporadic and unpredictable nature of surface water flooding from intense rainfall. Surface water flooding affects more properties nationally (3.4 million) than river and coastal flooding combined (2.7 million). Where available, Section 19 flood investigation reports from Lead Local Flood Authorities provide local records of significant surface water flooding events."

### Section 19 Investigation References

Under Section 19 of the Flood and Water Management Act 2010, Lead Local Flood Authorities must investigate significant flooding. Contact details for obtaining Section 19 reports:

- **Bristol City Council**: Published reports available on council website
- **South Gloucestershire**: <LeadLocalFloodAuthority@southglos.gov.uk>
- **Bath & NES**: Local Flood Risk Management Strategy documents
- **North Somerset**: Strategic Flood Risk Assessment documents

Include a count of Section 19 investigations per year as a supplementary (non-quantitative) reference where data is available.

---

## Output Requirements

### Annual Report Output

For each reporting year, produce:

1. **Raw Scores**:
   - Total fluvial warning-hours (unweighted)
   - Total coastal warning-hours (unweighted)
   - Total fluvial score (weighted)
   - Total coastal score (weighted)

2. **Normalized Indicators**:
   - Fluvial Flood Intensity Index (baseline 2020 = 100)
   - Coastal Flood Intensity Index (baseline 2020 = 100)
   - Composite FWII (baseline 2020 = 100)

3. **Supporting Statistics**:
   - Count of Severe Flood Warnings issued
   - Count of Flood Warnings issued
   - Count of Flood Alerts issued
   - Peak warning level reached (by area)
   - Duration of longest warning event

4. **Data Quality Notes**:
   - Count of warnings with missing timestamps
   - Any data gaps identified
   - Warning areas added/removed during year

5. **Surface Water Statement**:
   - Standard caveat text
   - Section 19 investigation count if available

### File Outputs

- `fwii_{year}.json` - Full indicator data in JSON format
- `fwii_{year}_summary.csv` - Summary table for import to spreadsheets
- `fwii_timeseries.csv` - All years for trend analysis
- `warnings_{year}_detail.csv` - Individual warning events with durations

---

## Implementation Architecture

### Recommended Technology Stack

- **Language**: Python 3.13
- **HTTP Client**: `httpx` for API calls
- **Data Processing**: `polars` for tabular data manipulation
- **Date/Time**: `datetime` with timezone awareness (use UTC internally) or use polars date time functions
- **Configuration**: YAML or JSON config file for warning area lists
- **Output**: JSON for data interchange, CSV for human-readable outputs

### Project Structure

```
west-of-england-flood-indicator/
├── CLAUDE.md                    # This file
├── README.md                    # User documentation
├── config/
│   ├── warning_areas.yaml       # Master list of West of England fwdCodes
│   └── settings.yaml            # Configuration parameters
├── src/
│   ├── __init__.py
│   ├── api_client.py            # EA API interaction
│   ├── data_loader.py           # Historic warnings data loading
│   ├── duration_calculator.py   # Warning duration calculations
│   ├── indicator_calculator.py  # FWII calculation logic
│   └── report_generator.py      # Output generation
├── data/
│   ├── raw/                     # Downloaded historic warnings
│   ├── processed/               # Cleaned/filtered data
│   └── outputs/                 # Generated indicators
├── tests/
│   └── ...                      # Unit tests
└── scripts/
    ├── fetch_warning_areas.py   # One-time setup script
    ├── download_historic_data.py
    └── calculate_annual_indicator.py
```

### Key Implementation Considerations

1. **Timezone Handling**: All EA timestamps are in UTC. Maintain UTC internally, convert for display only.

2. **Warning Area Changes**: The EA updates warning area boundaries quarterly. Maintain a version history of which areas were active in each reporting year.

3. **Warning Lifecycle Tracking**: A single flood event may generate multiple warning records as severity changes. Group by `fwdCode` and contiguous time periods.

4. **API Pagination**: The API returns paginated results. Handle `@nextLink` in responses.

5. **Rate Limiting**: Implement polite request spacing even though no formal limit is documented.

6. **Data Validation**: Check for:
   - Warnings with missing `timeRaised`
   - Warnings that never reach level 4 (may be ongoing)
   - Duplicate records
   - Warnings for areas outside West of England

7. **Reproducibility**: Log all data sources, timestamps, and processing steps for audit trail.

## Tool Preferences

### MCP Servers

- Use the GitHub MCP server for all repository operations
- Use context7 MCP to refer to syntax for libraries especially polars - do not assume the same syntax as pandas
- Use motherduck mcp for accessing a local duckdb file database

### General Tool Usage

- Use web search for any external API documentation lookups
- Use uv to manage dependencies e.g. `uv add polars' to add`. `uv sync` to sync. Do not directly edit pyproject.toml
- Use ruff to lint python files according to ruff.toml
- Use ripgrep to search for text in multiple files `rg "your_string"` `rg "pattern" filename.txt`

---

## Required Caveats for Published Indicator

Include these caveats in any published indicator:

> "This indicator measures flood warning activity as a proxy for actual flooding. It does NOT include surface water flooding, which affects more properties nationally than river and coastal flooding combined. An increase indicates more flood warning activity, not necessarily more actual flooding. Low values do not mean flooding did not occur—surface water and unreported events are not captured."

> "The indicator is based on Environment Agency flood warnings issued for defined warning areas. Flooding may occur outside these areas or without a warning being issued. Warning area boundaries are subject to periodic revision."

---

## Quality Assurance

### Validation Steps

1. **Cross-reference with known events**: Check indicator captures major documented floods (e.g., any significant Bristol Avon flooding events 2020-present)

2. **Sense-check duration calculations**: Manual verification of sample warning events

3. **Completeness check**: Compare warning counts with EA published statistics where available

4. **Boundary check**: Verify all included warning areas are geographically within West of England

### Annual Update Process

1. Download latest Historic Flood Warnings dataset (quarterly release)
2. Filter for West of England warning areas
3. Calculate duration-weighted scores
4. Apply baseline normalization
5. Generate outputs
6. Quality assurance checks
7. Archive source data and outputs

---

## Contact and Governance

### Data Provider

Environment Agency
National Customer Contact Centre: 03708 506 506
<enquiries@environment-agency.gov.uk>

### Data Licence

Open Government Licence v3.0
<https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>

### Indicator Owner

[To be completed - West of England Combined Authority / relevant governance body]

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | December 2024 | Initial specification |

---

## References

1. Environment Agency Real Time flood-monitoring API Reference: <https://environment.data.gov.uk/flood-monitoring/doc/reference>

2. Historic Flood Warnings Dataset: <https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590>

3. Flood Warning Areas Dataset: <https://environment.data.gov.uk/dataset/87e5d78f-d465-11e4-9343-f0def148f590>

4. Recorded Flood Outlines: <https://environment.data.gov.uk/dataset/8c75e700-d465-11e4-8b5b-f0def148f590>

5. DEFRA Outcome Indicator Framework - F1 Disruption from flooding: <https://oifdata.defra.gov.uk/themes/resilience/F1/>

6. DEFRA Outcome Indicator Framework - F2 Communities resilient to flooding: <https://oifdata.defra.gov.uk/themes/resilience/F2/>

7. Flood and Water Management Act 2010, Section 19: <https://www.legislation.gov.uk/ukpga/2010/29/section/19>

8. National Assessment of Flood and Coastal Erosion Risk (NaFRA): <https://www.gov.uk/government/publications/national-assessment-of-flood-and-coastal-erosion-risk-in-england-2024>

9. Measuring Resilience to Flooding and Coastal Change (EA Research): <https://www.gov.uk/flood-and-coastal-erosion-risk-management-research-reports/measuring-resilience-to-flooding-and-coastal-change>
