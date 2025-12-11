"""Fetch flood warning areas for West of England and save to config."""

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

# Add src to path so we can import fwii
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fwii.api_client import FloodMonitoringClient
from fwii.config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Fetch all West of England flood warning areas and save to YAML."""
    logger.info("Starting flood warning areas fetch")

    # Initialize config and client
    config = Config()
    client = FloodMonitoringClient(config)

    try:
        # Fetch all areas
        logger.info(f"Fetching areas for counties: {', '.join(config.counties)}")
        areas = client.get_all_west_of_england_areas()

        # Process and structure the data
        warning_areas = []
        stats = {
            "fluvial": 0,
            "coastal": 0,
            "by_county": {county: 0 for county in config.counties},
        }

        for area in areas:
            # Extract key fields
            river_or_sea = area.get("riverOrSea", "")

            # Detect coastal/tidal areas
            is_tidal = any(
                keyword in river_or_sea.lower()
                for keyword in [
                    "severn estuary",
                    "sea",
                    "tidal",
                    "coast",
                    "bristol channel",
                ]
            )

            area_data = {
                "fwdCode": area.get("notation"),
                "label": area.get("label"),
                "description": area.get("description", ""),
                "county": area.get("county"),
                "riverOrSea": river_or_sea,
                "isTidal": is_tidal,
            }

            warning_areas.append(area_data)

            # Update statistics
            if is_tidal:
                stats["coastal"] += 1
            else:
                stats["fluvial"] += 1

            # Count by county (handle multi-county areas)
            county_str = area.get("county", "")
            for county in config.counties:
                if county in county_str or (
                    county == "Bristol" and "City of Bristol" in county_str
                ):
                    stats["by_county"][county] += 1

        # Sort by fwdCode for consistency
        warning_areas.sort(key=lambda x: x["fwdCode"])

        # Create output structure
        output = {
            "metadata": {
                "description": "Flood warning areas for West of England",
                "region": config.region_name,
                "counties": config.counties,
                "fetched_at": datetime.now(UTC).isoformat(),
                "total_areas": len(warning_areas),
                "fluvial_areas": stats["fluvial"],
                "coastal_areas": stats["coastal"],
                "areas_by_county": stats["by_county"],
            },
            "warning_areas": warning_areas,
        }

        # Save to YAML
        output_path = config.warning_areas_path
        logger.info(f"Saving {len(warning_areas)} areas to {output_path}")

        with open(output_path, "w") as f:
            yaml.dump(output, f, default_flow_style=False, sort_keys=False)

        # Print summary
        print("\n" + "=" * 60)
        print("FLOOD WARNING AREAS FETCH COMPLETE")
        print("=" * 60)
        print(f"Total areas:     {len(warning_areas)}")
        print(f"Fluvial areas:   {stats['fluvial']}")
        print(f"Coastal areas:   {stats['coastal']}")
        print("\nAreas by county:")
        for county, count in stats["by_county"].items():
            print(f"  {county:30s} {count:3d}")
        print(f"\nSaved to: {output_path}")
        print("=" * 60)

        logger.info("Fetch complete")

    except Exception as e:
        logger.error(f"Error fetching warning areas: {e}", exc_info=True)
        sys.exit(1)

    finally:
        client.close()


if __name__ == "__main__":
    main()
