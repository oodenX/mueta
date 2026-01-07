import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pylast
from rich.console import Console

from mueta.core import settings

logger = logging.getLogger(__name__)
console = Console()

# Lazy import ML predictor to avoid loading TensorFlow on startup
_ml_predictor = None

def get_ml_predictor():
    """Get or create the ML predictor (lazy loading)."""
    global _ml_predictor
    if _ml_predictor is None and settings.ml.enable:
        try:
            from mueta.engine.ml import MLPredictor, ModelManager
            model_dir = Path(settings.ml.model_dir) if settings.ml.model_dir else None
            model_manager = ModelManager(model_dir=model_dir)
            _ml_predictor = MLPredictor(model_manager=model_manager)
        except ImportError as e:
            logger.warning(f"ML predictor not available: {e}")
    return _ml_predictor


class SemanticAnalyzer:
    # Analyzes semantic information (Genre, Mood) using Last.fm API and taxonomy mapping.

    def __init__(self):
        self.enabled = settings.lastfm.enable
        self.api_key = settings.lastfm.api_key
        self.api_secret = settings.lastfm.api_secret
        self.network = None
        self.taxonomy = self._load_taxonomy()

        if self.enabled and self.api_key:
            try:
                self.network = pylast.LastFMNetwork(
                    api_key=self.api_key,
                    api_secret=self.api_secret
                )
            except Exception as e:
                logger.error(f"Failed to initialize Last.fm network: {e}")
                self.enabled = False

    def _load_taxonomy(self) -> Dict[str, Dict[str, List[str]]]:
        # Load genre and mood taxonomy from JSON file.
        try:
            current_file = Path(__file__)
            data_dir = current_file.parent.parent / "data"
            taxonomy_path = data_dir / "taxonomy.json"

            if not taxonomy_path.exists():
                logger.warning(f"Taxonomy file not found at {taxonomy_path}")
                return {"genres": {}, "moods": {}}

            with open(taxonomy_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load taxonomy: {e}")
            return {"genres": {}, "moods": {}}

    def analyze(
        self,
        artist: str,
        title: str,
        audio_file: Optional[Path | str] = None
    ) -> Dict[str, List[str]]:
        """Analyze track to find genres and moods.

        Uses ML-based prediction as the primary source if an audio file is provided.
        Falls back to Last.fm API if ML is disabled, unavailable, or returns no results.

        Args:
            artist: Artist name for Last.fm lookup fallback.
            title: Track title for Last.fm lookup fallback.
            audio_file: Optional path to audio file for ML.

        Returns:
            Dict with 'genres' and 'moods' lists.
        """
        result = {
            "genres": [],
            "moods": []
        }

        # 1. Try ML primarily if audio file is available
        if audio_file and settings.ml.enable:
            ml_predictor = get_ml_predictor()

            if ml_predictor and ml_predictor.is_available():
                ml_result = ml_predictor.predict_all(audio_file)
                result["genres"] = ml_result["genres"]
                result["moods"] = ml_result["moods"]

                if result["genres"] or result["moods"]:
                    logger.info(f"ML analysis primary: Genres={result['genres']}, Moods={result['moods']}")
                    # If we got results from ML, we can stop here or use Last.fm as fallback for empty fields
                    if result["genres"] and result["moods"]:
                        return result

        # 2. Fallback to Last.fm for missing attributes
        lastfm_result = self._analyze_lastfm(artist, title)
        
        if not result["genres"]:
            result["genres"] = lastfm_result["genres"]
        if not result["moods"]:
            result["moods"] = lastfm_result["moods"]

        return result

    def _analyze_lastfm(self, artist: str, title: str) -> Dict[str, List[str]]:
        """Analyze track using Last.fm API.

        Args:
            artist: Artist name.
            title: Track title.

        Returns:
            Dict with 'genres' and 'moods' lists.
        """
        result = {
            "genres": [],
            "moods": []
        }

        if not self.enabled or not self.network:
            return result

        if not artist or not title:
            return result

        try:
            track = self.network.get_track(artist, title)
            tags = track.get_top_tags(limit=20)

            if not tags:
                artist_obj = self.network.get_artist(artist)
                tags = artist_obj.get_top_tags(limit=15)

            found_genres = set()
            found_moods = set()

            for tag_item in tags:
                tag_name = tag_item.item.get_name().lower().strip()

                # 1. Match Genres
                for main_genre, aliases in self.taxonomy.get("genres", {}).items():
                    if tag_name == main_genre or tag_name in aliases:
                        found_genres.add(main_genre.title())

                # 2. Match Moods
                for main_mood, aliases in self.taxonomy.get("moods", {}).items():
                    if tag_name == main_mood or tag_name in aliases:
                        found_moods.add(main_mood.title())

            result["genres"] = sorted(list(found_genres))
            result["moods"] = sorted(list(found_moods))

            logger.info(f"Last.fm analysis for '{title} - {artist}': Genres={result['genres']}, Moods={result['moods']}")

        except pylast.WSError as e:
            if e.status == "6": # Invalid parameters (e.g. track not found)
                logger.debug(f"Track not found in Last.fm: {artist} - {title}")
            else:
                logger.warning(f"Last.fm API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during Last.fm analysis: {e}")

        return result

    def analyze_audio_only(self, audio_file: Path | str) -> Dict[str, List[str]]:
        """Analyze audio file using only ML prediction (no API lookup).

        Args:
            audio_file: Path to audio file.

        Returns:
            Dict with 'genres' and 'moods' lists.
        """
        result = {
            "genres": [],
            "moods": []
        }

        if not settings.ml.enable:
            return result

        ml_predictor = get_ml_predictor()
        if ml_predictor and ml_predictor.is_available():
            result = ml_predictor.predict_all(audio_file)
            logger.info(f"ML-only analysis: Genres={result['genres']}, Moods={result['moods']}")

        return result
