# src/mueta/engine/lyrics.py
"""LRCLIB lyrics service."""

from pathlib import Path
from loguru import logger
from mueta.core.config import settings
from mueta.engine.lyrics_providers import (
    GeniusProvider,
    LRCLIBProvider,
    LyricsProvider,
    NetEaseProvider,
)
from mueta.engine.models import LyricsResult


class LyricsService:
    """Service for fetching lyrics from multiple sources."""

    def __init__(self):
        self.providers: list[LyricsProvider] = [
            LRCLIBProvider(),
            NetEaseProvider(),
            GeniusProvider(api_key=settings.genius_api_key),
        ]

    def get_lyrics(
        self,
        artist: str,
        track: str,
        album: str | None = None,
        duration: float | None = None,
    ) -> LyricsResult | None:
        """
        Get lyrics by querying providers in order.

        Args:
            artist: Artist name.
            track: Track/song name.
            album: Album name (optional).
            duration: Track duration in seconds (optional).

        Returns:
            LyricsResult or None if not found.
        """
        logger.info(f"Fetching lyrics for: {artist} - {track}")

        for provider in self.providers:
            try:
                # Skip Genius if no key
                if isinstance(provider, GeniusProvider) and not provider.api_key:
                    continue

                logger.debug(f"Querying provider: {provider.NAME}")
                result = provider.get_lyrics(artist, track, album, duration)

                if result:
                    logger.info(f"Lyrics found via {provider.NAME}")
                    return result
            except Exception as e:
                logger.warning(f"Error with provider {provider.NAME}: {e}")
                continue

        logger.info("Lyrics not found in any provider.")
        return None

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
