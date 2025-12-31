# src/mueta/engine/cover.py
"""Cover art download service with multiple sources."""

from loguru import logger
import httpx

from mueta.engine.retry import make_request_with_retry


class CoverService:
    """Service for downloading cover art from multiple sources."""

    TIMEOUT = 15.0

    # NetEase API
    NETEASE_SEARCH_URL = "http://music.163.com/api/search/get/web"
    NETEASE_HEADERS = {
        "Referer": "http://music.163.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    # QQMusic API
    QQMUSIC_SEARCH_URL = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
    QQMUSIC_HEADERS = {
        "Referer": "https://y.qq.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    def __init__(self):
        self.client = httpx.Client(timeout=self.TIMEOUT, follow_redirects=True)

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with retry."""
        return make_request_with_retry(self.client, method, url, **kwargs)

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
            response = self._request('get', url)
            content_type = response.headers.get("content-type", "image/jpeg")
            mime_type = content_type.split(";")[0].strip()
            logger.info(f"Downloaded cover art: {len(response.content)} bytes")
            return response.content, mime_type

        except httpx.HTTPError as e:
            logger.warning(f"Failed to download cover art: {e}")
            return None

    def get_cover_from_netease(self, artist: str, track: str) -> tuple[bytes, str] | None:
        """
        Get cover art from NetEase Cloud Music.

        Args:
            artist: Artist name.
            track: Track name.

        Returns:
            Tuple of (image data, mime type) or None.
        """
        try:
            # Search for song
            params = {"s": f"{track} {artist}", "type": 1, "limit": 1}
            response = self._request('post', self.NETEASE_SEARCH_URL, data=params, headers=self.NETEASE_HEADERS)
            data = response.json()

            songs = data.get("result", {}).get("songs", [])
            if not songs:
                return None

            # Get album cover URL
            album = songs[0].get("album", {})
            pic_url = album.get("picUrl")
            if not pic_url:
                return None

            # Download high-res cover
            cover_url = f"{pic_url}?param=800y800"
            logger.info(f"Found NetEase cover for: {track}")
            return self.download(cover_url)

        except Exception as e:
            logger.warning(f"NetEase cover error: {e}")
            return None

    def get_cover_from_qqmusic(self, artist: str, track: str) -> tuple[bytes, str] | None:
        """
        Get cover art from QQ Music.

        Args:
            artist: Artist name.
            track: Track name.

        Returns:
            Tuple of (image data, mime type) or None.
        """
        try:
            # Search for song
            params = {
                "w": f"{track} {artist}",
                "format": "json",
                "p": 1,
                "n": 1,
            }
            response = self._request('get', self.QQMUSIC_SEARCH_URL, params=params, headers=self.QQMUSIC_HEADERS)
            data = response.json()

            songs = data.get("data", {}).get("song", {}).get("list", [])
            if not songs:
                return None

            # Get album mid
            albummid = songs[0].get("albummid")
            if not albummid:
                return None

            # Construct cover URL
            cover_url = f"https://y.qq.com/music/photo_new/T002R800x800M000{albummid}.jpg"
            logger.info(f"Found QQMusic cover for: {track}")
            return self.download(cover_url)

        except Exception as e:
            logger.warning(f"QQMusic cover error: {e}")
            return None

    def get_cover_fallback(self, artist: str, track: str) -> tuple[bytes, str] | None:
        """
        Try to get cover art from alternative sources (NetEase, QQMusic).

        Args:
            artist: Artist name.
            track: Track name.

        Returns:
            Tuple of (image data, mime type) or None.
        """
        # Try NetEase first
        result = self.get_cover_from_netease(artist, track)
        if result:
            return result

        # Fallback to QQMusic
        result = self.get_cover_from_qqmusic(artist, track)
        if result:
            return result

        return None
