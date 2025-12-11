# West of England Flood Warning Intensity Index (FWII)

Regional flood warning indicator for the West of England, tracking flood warning activity across Bristol, Bath & North East Somerset, South Gloucestershire, and North Somerset.

## Overview

The FWII is a duration-weighted composite indicator that tracks flood warning activity as a proxy for flooding events in the West of England region. It provides annual reporting to support climate resilience monitoring.

### Indicator Components

1. **Fluvial Flood Intensity Sub-indicator** - River flood warnings (55% weight)
2. **Coastal Flood Intensity Sub-indicator** - Tidal/coastal flood warnings (45% weight)
3. **Composite FWII** - Combined indicator normalized to 2020 baseline = 100
4. **Surface Water Flooding** - Reported as "not measurable" with caveats

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd fwii

# Install dependencies (requires Python 3.13+)
uv sync
```

### Fetch Flood Warning Areas

```bash
# Download current flood warning areas from Environment Agency API
uv run scripts/fetch_warning_areas.py
```

This fetches **18 flood warning and alert areas** covering the West of England:
- 7 Flood Warning areas (immediate action required)
- 11 Flood Alert areas (early notification)
- 9 fluvial (river) areas
- 9 coastal/tidal areas

## Project Structure

```
fwii/
   config/
      settings.yaml           # Configuration parameters
      warning_areas.yaml      # West of England flood areas
   src/fwii/
      __init__.py
      config.py              # Configuration management
      api_client.py          # EA API client
   scripts/
      fetch_warning_areas.py # Fetch flood areas script
   data/
      raw/                   # Downloaded historic warnings
      processed/             # Cleaned data
      outputs/               # Generated indicators
   notebooks/                 # Exploration and analysis
```

## Data Sources

- **Environment Agency Flood Monitoring API**: Real-time and area data
- **Historic Flood Warnings Dataset**: Complete warning history from 2006 onwards
- **Update frequency**: Quarterly

All data is available under the Open Government Licence v3.0.

## Methodology

See [CLAUDE.md](CLAUDE.md) for detailed specification including:
- Calculation methodology
- Duration weighting and severity scoring
- Baseline normalization approach
- Data quality requirements

## Development Status

**Current Progress**: 12% complete (4/34 tasks)

**Phase 1: Foundation & Setup** ✅ COMPLETE
- ✅ Project structure created
- ✅ Configuration management implemented
- ✅ EA API client built
- ✅ 18 flood warning areas fetched

**Phase 2: Data Acquisition** 🏗️ NEXT
- Download historic warnings (2020-present)
- Data validation and quality checks
- DuckDB storage setup

See [TODO.md](TODO.md) for detailed implementation plan and progress tracking.

## Caveats

This indicator measures **flood warning activity**, not actual flooding. It does NOT include:
- Surface water flooding (affects more properties than river/coastal combined)
- Flooding that occurred without warnings
- Unreported events

See [CLAUDE.md](CLAUDE.md) for full caveats and interpretation guidance.

## Contact

Environment Agency: enquiries@environment-agency.gov.uk

## License

Code: MIT License (see [LICENSE](LICENSE))
Data: [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
