# src/mueta/engine/cover.py
"""Cover art download service."""

from loguru import logger
import httpx


class CoverService:
    """Service for downloading cover art."""

    TIMEOUT = 15.0

    def __init__(self):
        self.client = httpx.Client(timeout=self.TIMEOUT)

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    def download(self, url: str) -> tuple[bytes, str] | None:
        """
        Download cover art from URL.

        Args:
            url: URL to the cover image.

        Returns:
            Tuple of (image data, mime type) or None if failed.
        """
        logger.debug(f"Downloading cover art from: {url}")

        try:
            response = self.client.get(url, follow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "image/jpeg")
            # Extract mime type (remove charset if present)
            mime_type = content_type.split(";")[0].strip()

            logger.info(f"Downloaded cover art: {len(response.content)} bytes")
            return response.content, mime_type

        except httpx.HTTPError as e:
            logger.warning(f"Failed to download cover art: {e}")
            return None
