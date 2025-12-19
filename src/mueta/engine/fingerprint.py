# src/mueta/engine/fingerprint.py
"""Audio fingerprint generation and AcoustID lookup."""

from pathlib import Path
from loguru import logger

import acoustid

from mueta.core.config import settings


class FingerprintService:
    """Service for audio fingerprint generation and AcoustID lookup."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.acoustid_api_key

    def get_fingerprint(self, file_path: Path) -> tuple[float, str]:
        """
        Generate acoustic fingerprint for an audio file.

        Args:
            file_path: Path to the audio file.

        Returns:
            Tuple of (duration in seconds, fingerprint string).

        Raises:
            acoustid.FingerprintGenerationError: If fingerprint generation fails.
        """
        logger.debug(f"Generating fingerprint for: {file_path}")
        duration, fingerprint = acoustid.fingerprint_file(str(file_path))
        logger.debug(f"Fingerprint generated, duration: {duration}s")
        return float(duration), str(fingerprint) if fingerprint else ""

    def lookup(self, file_path: Path) -> list[dict]:
        """
        Look up audio file in AcoustID database.

        Args:
            file_path: Path to the audio file.

        Returns:
            List of matching results with recordings.
        """
        logger.info(f"Looking up AcoustID for: {file_path.name}")

        results = []
        try:
            for score, recording_id, title, artist in acoustid.match(
                self.api_key, str(file_path)
            ):
                results.append(
                    {
                        "score": score,
                        "recording_id": recording_id,
                        "title": title,
                        "artist": artist,
                    }
                )
                logger.debug(f"Match: {title} - {artist} (score: {score:.2f})")
        except acoustid.NoBackendError:
            logger.error("Chromaprint library not found. Please install fpcalc.")
            raise
        except acoustid.FingerprintGenerationError as e:
            logger.error(f"Fingerprint generation failed: {e}")
            raise
        except acoustid.WebServiceError as e:
            logger.error(f"AcoustID web service error: {e}")
            raise

        return results

    def get_best_match(self, file_path: Path) -> dict | None:
        """
        Get the best matching result for an audio file.

        Args:
            file_path: Path to the audio file.

        Returns:
            Best matching result or None if no matches found.
        """
        results = self.lookup(file_path)
        if results:
            # Sort by score and return the best match
            best = max(results, key=lambda x: x["score"])
            logger.info(f"Best match: {best['title']} - {best['artist']}")
            return best
        return None
