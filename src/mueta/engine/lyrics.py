# src/mueta/engine/lyrics.py
"""LRCLIB lyrics service."""

from pathlib import Path
from loguru import logger
import httpx

from mueta.engine.models import LyricsResult


class LyricsService:
    """Service for fetching lyrics from LRCLIB."""

    BASE_URL = "https://lrclib.net/api"
    TIMEOUT = 10.0

    def __init__(self):
        self.client = httpx.Client(timeout=self.TIMEOUT)

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    def get_lyrics(
        self,
        artist: str,
        track: str,
        album: str | None = None,
        duration: float | None = None,
    ) -> LyricsResult | None:
        """
        Get lyrics by artist and track name.
        First tries exact match, then falls back to search if not found.

        Args:
            artist: Artist name.
            track: Track/song name.
            album: Album name (optional, for better matching).
            duration: Track duration in seconds (optional, for better matching).

        Returns:
            LyricsResult or None if not found.
        """
        logger.info(f"Fetching lyrics for: {artist} - {track}")

        params = {
            "artist_name": artist,
            "track_name": track,
        }
        if album:
            params["album_name"] = album
        if duration:
            params["duration"] = str(int(duration))

        try:
            response = self.client.get(f"{self.BASE_URL}/get", params=params)

            if response.status_code == 404:
                logger.debug(f"Exact match not found for: {artist} - {track}, trying search...")
                # Fallback to search
                return self._search_fallback(artist, track, duration)

            response.raise_for_status()
            data = response.json()

            return LyricsResult(
                id=data["id"],
                track_name=data["trackName"],
                artist_name=data["artistName"],
                album_name=data.get("albumName"),
                duration=data.get("duration"),
                instrumental=data.get("instrumental", False),
                plain_lyrics=data.get("plainLyrics"),
                synced_lyrics=data.get("syncedLyrics"),
            )
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching lyrics: {e}")
            # Try search as fallback
            return self._search_fallback(artist, track, duration)

    def _search_fallback(self, artist: str, track: str, duration: float | None = None) -> LyricsResult | None:
        """
        Search for lyrics as a fallback when exact match fails.

        Args:
            artist: Artist name.
            track: Track name.
            duration: Track duration for better matching (optional).

        Returns:
            Best matching LyricsResult or None.
        """
        # Try searching with track name only first
        results = self.search_lyrics(track, limit=10)

        if not results:
            logger.debug(f"No search results for: {track}")
            return None

        # Filter and score results
        best_match = None
        best_score = 0

        for result in results:
            score = 0

            # Check artist match (case-insensitive, partial match)
            if artist.lower() in result.artist_name.lower() or result.artist_name.lower() in artist.lower():
                score += 100

            # Check track name match (case-insensitive)
            if track.lower() == result.track_name.lower():
                score += 50
            elif track.lower() in result.track_name.lower():
                score += 30

            # Prefer results with synced lyrics
            if result.synced_lyrics:
                score += 20

            # Duration matching (within 5 seconds tolerance)
            if duration and result.duration:
                duration_diff = abs(duration - result.duration)
                if duration_diff < 5:
                    score += 10
                elif duration_diff < 10:
                    score += 5

            if score > best_score:
                best_score = score
                best_match = result

        if best_match and best_score >= 30:  # Minimum score threshold
            logger.info(f"Found via search: {best_match.track_name} by {best_match.artist_name} (score: {best_score})")
            return best_match

        logger.debug(f"No suitable match found in search results")
        return None

    def search_lyrics(self, query: str, limit: int = 10) -> list[LyricsResult]:
        """
        Search lyrics by keyword.

        Args:
            query: Search keyword.
            limit: Maximum number of results.

        Returns:
            List of LyricsResult.
        """
        logger.debug(f"Searching lyrics: {query}")

        try:
            response = self.client.get(
                f"{self.BASE_URL}/search",
                params={"q": query, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data:
                results.append(
                    LyricsResult(
                        id=item["id"],
                        track_name=item["trackName"],
                        artist_name=item["artistName"],
                        album_name=item.get("albumName"),
                        duration=item.get("duration"),
                        instrumental=item.get("instrumental", False),
                        plain_lyrics=item.get("plainLyrics"),
                        synced_lyrics=item.get("syncedLyrics"),
                    )
                )
            return results
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error searching lyrics: {e}")
            return []

    def save_lrc_file(self, synced_lyrics: str, output_path: Path) -> None:
        """
        Save synced lyrics to .lrc file.

        Args:
            synced_lyrics: LRC format lyrics string.
            output_path: Path to save the .lrc file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(synced_lyrics)
        logger.info(f"Saved lyrics to: {output_path}")
