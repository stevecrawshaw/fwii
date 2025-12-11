"""Environment Agency Flood Monitoring API client."""

import logging
import time
from typing import Any

import httpx

from .config import Config

logger = logging.getLogger(__name__)


class FloodMonitoringAPIError(Exception):
    """Base exception for API errors."""

    pass


class FloodMonitoringClient:
    """Client for interacting with the EA Flood Monitoring API.

    Handles pagination, rate limiting, retries, and error handling.
    """

    def __init__(self, config: Config | None = None):
        """Initialize the API client.

        Args:
            config: Configuration object. If None, creates default Config.
        """
        self.config = config or Config()
        self.client = httpx.Client(timeout=self.config.timeout)
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        delay = self.config.rate_limit_delay - elapsed

        if delay > 0:
            time.sleep(delay)

        self._last_request_time = time.time()

    def _make_request(self, url: str, params: dict[str, Any] | None = None) -> dict:
        """Make an HTTP GET request with retry logic.

        Args:
            url: The URL to request
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            FloodMonitoringAPIError: If request fails after all retries
        """
        self._rate_limit()

        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Making request to {url} (attempt {attempt + 1})")
                response = self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"HTTP error {e.response.status_code} on attempt {attempt + 1}: {e}"
                )
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise FloodMonitoringAPIError(
                        f"Request failed after {self.config.max_retries} attempts: {e}"
                    ) from e

            except httpx.RequestError as e:
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise FloodMonitoringAPIError(
                        f"Request failed after {self.config.max_retries} attempts: {e}"
                    ) from e

        raise FloodMonitoringAPIError("Unexpected error in request logic")

    def _get_all_pages(
        self, url: str, params: dict[str, Any] | None = None
    ) -> list[dict]:
        """Fetch all pages from a paginated endpoint.

        Args:
            url: The initial URL
            params: Query parameters

        Returns:
            List of all items across all pages
        """
        all_items = []
        current_url = url

        while current_url:
            data = self._make_request(current_url, params)

            # Extract items from response
            items = data.get("items", [])
            all_items.extend(items)

            logger.info(f"Fetched {len(items)} items (total: {len(all_items)})")

            # Check for next page link
            meta = data.get("meta", {})
            current_url = meta.get("next")

            # Only use params on first request, subsequent use the full next URL
            params = None

        return all_items

    def get_flood_areas(self, county: str | None = None) -> list[dict]:
        """Get flood warning areas, optionally filtered by county.

        Args:
            county: County name to filter by (e.g., 'Bristol')

        Returns:
            List of flood area dictionaries

        Example:
            >>> client = FloodMonitoringClient()
            >>> areas = client.get_flood_areas(county="Bristol")
            >>> len(areas)
            15
        """
        params = {"county": county} if county else None
        logger.info(f"Fetching flood areas for county: {county or 'all'}")

        areas = self._get_all_pages(self.config.flood_areas_url, params)
        logger.info(f"Retrieved {len(areas)} flood areas")

        return areas

    def get_all_west_of_england_areas(self) -> list[dict]:
        """Get all flood warning areas for West of England counties.

        Fetches ALL areas from the API, then filters for those mentioning
        any West of England county (handles multi-county areas).

        Returns:
            List of flood area dictionaries for all 4 WoE counties

        Example:
            >>> client = FloodMonitoringClient()
            >>> areas = client.get_all_west_of_england_areas()
            >>> len(areas)
            67
        """
        logger.info("Fetching all flood warning areas...")
        all_areas = self._get_all_pages(self.config.flood_areas_url)
        logger.info(f"Retrieved {len(all_areas)} total areas from API")

        # Filter for West of England counties
        # County field may contain multiple counties separated by commas
        woe_areas = []
        county_keywords = [
            "Bristol",  # Matches "Bristol" and "City of Bristol"
            "Bath and North East Somerset",
            "South Gloucestershire",
            "North Somerset",
        ]

        for area in all_areas:
            county_str = area.get("county", "")
            if any(keyword in county_str for keyword in county_keywords):
                woe_areas.append(area)

        logger.info(f"Filtered to {len(woe_areas)} areas in West of England counties")

        return woe_areas

    def get_current_floods(self, severity: int | None = None) -> list[dict]:
        """Get currently active flood warnings.

        Args:
            severity: Filter by severity level (1=Severe, 2=Warning, 3=Alert)

        Returns:
            List of current flood warning dictionaries

        Example:
            >>> client = FloodMonitoringClient()
            >>> severe_warnings = client.get_current_floods(severity=1)
        """
        params = {"severity": severity} if severity else None
        logger.info(f"Fetching current floods (severity: {severity or 'all'})")

        floods = self._get_all_pages(self.config.floods_url, params)
        logger.info(f"Retrieved {len(floods)} current flood warnings")

        return floods

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
