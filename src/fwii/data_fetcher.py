"""Historic flood warnings data fetcher.

Downloads and extracts historic flood warning data from the Environment Agency's
Historic Flood Warnings Dataset.

Dataset URL: https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590
"""

import logging
from pathlib import Path
from zipfile import ZipFile

import httpx

from fwii.config import Config

logger = logging.getLogger(__name__)


class DataFetchError(Exception):
    """Raised when data fetching fails."""


class HistoricWarningsFetcher:
    """Fetches historic flood warning data from Environment Agency.

    The Environment Agency provides historic flood warnings as a single
    downloadable ZIP file containing all data from 2006 to present.
    Data is updated quarterly.
    """

    # Complete dataset download URL (public API endpoint)
    DATASET_URL = (
        "https://environment.data.gov.uk/api/file/download"
        "?fileDataSetId=766cb094-b392-4bd6-a02e-f60e143f3213"
        "&fileName=Historic_Flood_Warnings.zip"
    )

    def __init__(
        self, config: Config | None = None, output_dir: str | Path | None = None
    ):
        """Initialize the fetcher.

        Args:
            config: Configuration object. If None, loads from default location.
            output_dir: Directory to save downloaded files. If None, uses data/raw/
        """
        self.config = config or Config()
        self.output_dir = Path(output_dir) if output_dir else Path("data/raw")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create httpx client with appropriate timeouts
        self.client = httpx.Client(
            timeout=httpx.Timeout(
                timeout=300.0,  # 5 minutes for large file downloads
                connect=self.config.timeout,
            ),
            follow_redirects=True,
        )

    def download_complete_dataset(
        self,
        force_download: bool = False,
        extract: bool = True,
    ) -> Path:
        """Download the complete historic flood warnings dataset.

        Downloads a single ZIP file containing all historic flood warnings
        from January 2006 to present (updated quarterly).

        Args:
            force_download: If True, download even if file already exists
            extract: If True, extract ZIP contents after download

        Returns:
            Path to the downloaded (and optionally extracted) data directory

        Raises:
            DataFetchError: If download fails
        """
        output_path = self.output_dir / "Historic_Flood_Warnings.zip"

        # Check if already downloaded
        if output_path.exists() and not force_download:
            logger.info(f"Dataset already exists at {output_path}")
            if extract:
                return self._extract_zip(output_path)
            return output_path

        # Download the file
        logger.info("Downloading complete historic flood warnings dataset")
        logger.info(f"URL: {self.DATASET_URL}")

        try:
            with self.client.stream("GET", self.DATASET_URL) as response:
                response.raise_for_status()

                # Get file size if available
                total_size = int(response.headers.get("content-length", 0))
                downloaded_size = 0

                # Stream download with progress logging
                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # Log progress every 1MB for smaller files
                        if total_size > 0 and downloaded_size % (1024 * 1024) < 8192:
                            percent = (downloaded_size / total_size) * 100
                            logger.info(
                                f"Download progress: {downloaded_size / (1024 * 1024):.1f}MB / "
                                f"{total_size / (1024 * 1024):.1f}MB ({percent:.1f}%)"
                            )

            logger.info(
                f"Download complete: {downloaded_size / (1024 * 1024):.1f}MB saved to {output_path}"
            )

        except httpx.HTTPStatusError as e:
            msg = f"HTTP error downloading dataset: {e.response.status_code}"
            logger.error(msg)
            # Clean up partial download
            if output_path.exists():
                output_path.unlink()
            raise DataFetchError(msg) from e

        except httpx.RequestError as e:
            msg = f"Network error downloading dataset: {e}"
            logger.error(msg)
            # Clean up partial download
            if output_path.exists():
                output_path.unlink()
            raise DataFetchError(msg) from e

        # Extract if requested
        if extract:
            return self._extract_zip(output_path)

        return output_path

    def _extract_zip(self, zip_path: Path) -> Path:
        """Extract ZIP file contents.

        Args:
            zip_path: Path to ZIP file

        Returns:
            Path to extracted data directory

        Raises:
            DataFetchError: If extraction fails
        """
        extract_dir = self.output_dir / "historic_flood_warnings"
        extract_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting {zip_path} to {extract_dir}")

        try:
            with ZipFile(zip_path, "r") as zip_ref:
                # Get list of files
                file_list = zip_ref.namelist()
                logger.info(f"ZIP contains {len(file_list)} files")

                # Extract all files
                zip_ref.extractall(extract_dir)

                # Log what was extracted
                for file_name in file_list:
                    file_path = extract_dir / file_name
                    if file_path.is_file():
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                        logger.info(f"Extracted: {file_name} ({size_mb:.2f}MB)")

            logger.info(f"Extraction complete: {extract_dir}")
            return extract_dir

        except Exception as e:
            msg = f"Error extracting ZIP file: {e}"
            logger.error(msg)
            raise DataFetchError(msg) from e

    def download_historic_warnings(
        self,
        year: int | None = None,
        force_download: bool = False,
        extract: bool = True,
    ) -> Path:
        """Download historic flood warnings data.

        This method downloads the complete dataset (2006-present) and returns
        the path. Year filtering should be done during the loading phase.

        Args:
            year: Ignored (kept for backward compatibility). All years downloaded.
            force_download: If True, download even if file already exists
            extract: If True, extract ZIP contents after download

        Returns:
            Path to the downloaded (and optionally extracted) data directory

        Raises:
            DataFetchError: If download fails
        """
        if year is not None:
            logger.info(
                f"Note: Year {year} specified, but complete dataset "
                "(2006-present) will be downloaded. Filter by year during loading."
            )

        return self.download_complete_dataset(
            force_download=force_download,
            extract=extract,
        )

    def get_dataset_info(self) -> dict[str, str]:
        """Get information about the dataset source.

        Returns:
            Dictionary with dataset metadata
        """
        return {
            "name": "Historic Flood Warnings Dataset",
            "provider": "Environment Agency",
            "url": "https://environment.data.gov.uk/dataset/88bed270-d465-11e4-8669-f0def148f590",
            "download_url": self.DATASET_URL,
            "licence": "Open Government Licence v3.0",
            "update_frequency": "Quarterly",
            "coverage_start": "2006-01-26",
            "coverage_end": "Present",
            "last_updated": "October 2025",
            "description": (
                "Complete record of all Flood Alerts, Flood Warnings, and "
                "Severe Flood Warnings issued by the Environment Agency from "
                "January 2006 to present"
            ),
        }

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
