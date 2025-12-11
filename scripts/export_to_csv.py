"""Export flood warning data to CSV files by year."""

import sys
from pathlib import Path

import polars as pl
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fwii.data_loader import HistoricWarningsLoader


def main():
    """Export data to CSV files for each year."""
    # Load warning areas config
    config_path = Path(__file__).parent.parent / "config" / "warning_areas.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Create loader (will use default config)
    data_dir = Path(__file__).parent.parent / "data" / "raw" / "historic_flood_warnings"
    loader = HistoricWarningsLoader()

    print(f"Loading data from {data_dir}...")
    df = loader.load_directory(str(data_dir), pattern="*.ods")
    print(f"Loaded {len(df)} West of England records")

    # Add isTidal from config
    areas_list = [
        {"fwdCode": area["fwdCode"], "isTidal": area.get("isTidal", False)}
        for area in config["warning_areas"]
    ]
    areas_df = pl.DataFrame(areas_list)

    # Drop isTidal if it exists, then join
    if "isTidal" in df.columns:
        df = df.drop("isTidal")
    df = df.join(areas_df, on="fwdCode", how="left")

    # Export by year
    output_dir = Path(__file__).parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    for year in [2020, 2021, 2022, 2023, 2024]:
        year_df = loader.filter_by_year(df, year)
        output_path = output_dir / f"warnings_{year}.csv"

        if len(year_df) > 0:
            year_df.write_csv(output_path)
            print(f"Exported {len(year_df)} records to {output_path}")
        else:
            print(f"No records for year {year}")


if __name__ == "__main__":
    main()
