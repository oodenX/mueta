import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pylast
from rich.console import Console

from mueta.core import settings

logger = logging.getLogger(__name__)
console = Console()

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

    def analyze(self, artist: str, title: str) -> Dict[str, List[str]]:
        # Analyze track to find genres and moods.
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

            logger.info(f"Semantic analysis for '{title} - {artist}': Genres={result['genres']}, Moods={result['moods']}")

        except pylast.WSError as e:
            if e.status == "6": # Invalid parameters (e.g. track not found)
                logger.debug(f"Track not found in Last.fm: {artist} - {title}")
            else:
                logger.warning(f"Last.fm API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during semantic analysis: {e}")

        return result
