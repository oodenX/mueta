# src/mueta/engine/musicbrainz.py
"""MusicBrainz API client for fetching metadata using httpx."""

from loguru import logger
import httpx

from mueta.engine.models import AudioMetadata
from mueta.engine.cache import MetadataCache


class MusicBrainzService:
    """Service for fetching metadata from MusicBrainz using httpx (faster)."""

    BASE_URL = "https://musicbrainz.org/ws/2"
    COVER_ART_URL = "https://coverartarchive.org"
    TIMEOUT = 15.0

    HEADERS = {
        "User-Agent": "Mueta/1.0.0 (https://github.com/oodenX/mueta)",
        "Accept": "application/json",
    }

    def __init__(self):
        self.client = httpx.Client(
            timeout=self.TIMEOUT,
            headers=self.HEADERS,
            follow_redirects=True,
        )
        self.cache = MetadataCache()

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    def get_recording(self, mbid: str) -> AudioMetadata:
        """
        Get recording metadata by MusicBrainz Recording ID.
        Uses httpx for faster requests with proper timeout control.

        Args:
            mbid: MusicBrainz Recording ID.

        Returns:
            AudioMetadata with filled fields.
        """
        logger.info(f"Fetching MusicBrainz recording: {mbid}")

        # Check cache first
        cached = self.cache.get_recording(mbid)
        if cached:
            logger.info(f"Cache hit for recording: {mbid}")
            return AudioMetadata(**cached)

        url = f"{self.BASE_URL}/recording/{mbid}"
        params = {
            "inc": "artists+releases+tags+isrcs+artist-rels+work-rels",
            "fmt": "json",
        }

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            recording = response.json()
        except httpx.HTTPError as e:
            logger.error(f"MusicBrainz API error: {e}")
            raise

        metadata = AudioMetadata(
            title=recording.get("title"),
            mbid=mbid,
            duration=int(recording.get("length", 0)) / 1000 if recording.get("length") else None,
        )

        # Get ISRC
        if "isrcs" in recording and recording["isrcs"]:
            metadata.isrc = recording["isrcs"][0]

        # Get artist info with MBIDs
        if "artist-credit" in recording:
            artists = recording["artist-credit"]
            if artists:
                artist_names = []
                artist_sort_names = []
                first_artist_mbid = None
                first_sort_name = None

                for artist_credit in artists:
                    if isinstance(artist_credit, dict) and "artist" in artist_credit:
                        artist_names.append(artist_credit["artist"]["name"])
                        sort_name = artist_credit["artist"].get("sort-name")
                        if sort_name:
                            artist_sort_names.append(sort_name)

                        if first_artist_mbid is None:
                            first_artist_mbid = artist_credit["artist"].get("id")
                            first_sort_name = sort_name

                metadata.artist = ", ".join(artist_names)
                metadata.artists = artist_names if len(artist_names) > 1 else None
                metadata.artist_mbid = first_artist_mbid
                metadata.artist_sort_order = first_sort_name

        # Get release info - choose best release then fetch full details
        if "releases" in recording and recording["releases"]:
            release = self._select_best_release(recording["releases"])
            if release and release.get("id"):
                # Fetch full release details to get track/medium info
                full_release = self._get_release_details(release["id"])
                if full_release:
                    self._populate_release_metadata(metadata, full_release)
                else:
                    # Fallback to basic release info
                    self._populate_basic_release_metadata(metadata, release)

        # Get genre from tags
        if "tags" in recording and recording["tags"]:
            tags = sorted(recording["tags"], key=lambda x: int(x.get("count", 0)), reverse=True)
            if tags:
                metadata.genre = tags[0]["name"]

        # Get credits from artist relations
        if "relations" in recording:
            self._extract_credits(metadata, recording["relations"])

        # Get work MBID from work relations
        if "relations" in recording:
            for rel in recording["relations"]:
                if rel.get("type") == "performance" and "work" in rel:
                    metadata.work_mbid = rel["work"].get("id")
                    break

        logger.debug(f"Fetched metadata: {metadata.title} - {metadata.artist}")

        # Cache the result
        self.cache.set_recording(mbid, metadata.model_dump())

        return metadata

    def _get_release_details(self, release_mbid: str) -> dict | None:
        """
        Fetch full release details including medium and track lists.

        Args:
            release_mbid: MusicBrainz Release ID.

        Returns:
            Full release dictionary or None on error.
        """
        url = f"{self.BASE_URL}/release/{release_mbid}"
        params = {
            "inc": "artists+labels+recordings+release-groups+media",
            "fmt": "json",
        }

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch release details: {e}")
            return None

    def _extract_credits(self, metadata: AudioMetadata, relations: list) -> None:
        """
        Extract credits (composer, lyricist, producer, etc.) from artist relations.

        Args:
            metadata: AudioMetadata to populate.
            relations: List of relation dictionaries from MusicBrainz.
        """
        # Mapping of MusicBrainz relation types to metadata fields
        credit_mapping = {
            "composer": "composer",
            "lyricist": "lyricist",
            "producer": "producer",
            "arranger": "arranger",
            "mix": "mixer",
            "conductor": "conductor",
            "performer": "performer",
            "writer": "writer",
            "vocal": "performer",  # Map vocal to performer as fallback
        }

        credits_found: dict[str, list[str]] = {}

        for rel in relations:
            rel_type = rel.get("type", "").lower()
            if rel_type in credit_mapping and "artist" in rel:
                artist_name = rel["artist"].get("name")
                if artist_name:
                    field = credit_mapping[rel_type]
                    if field not in credits_found:
                        credits_found[field] = []
                    if artist_name not in credits_found[field]:
                        credits_found[field].append(artist_name)

        # Populate metadata fields (join multiple artists with ", ")
        if "composer" in credits_found:
            metadata.composer = ", ".join(credits_found["composer"])
        if "lyricist" in credits_found:
            metadata.lyricist = ", ".join(credits_found["lyricist"])
        if "producer" in credits_found:
            metadata.producer = ", ".join(credits_found["producer"])
        if "arranger" in credits_found:
            metadata.arranger = ", ".join(credits_found["arranger"])
        if "mixer" in credits_found:
            metadata.mixer = ", ".join(credits_found["mixer"])
        if "conductor" in credits_found:
            metadata.conductor = ", ".join(credits_found["conductor"])
        if "performer" in credits_found:
            metadata.performer = ", ".join(credits_found["performer"])
        if "writer" in credits_found:
            metadata.writer = ", ".join(credits_found["writer"])

    def _select_best_release(self, releases: list) -> dict:
        """
        Select the best release from a list (prefer official, album type).

        Args:
            releases: List of release dictionaries.

        Returns:
            Best matching release.
        """
        if not releases:
            return {}

        # Scoring system for releases
        def score_release(release):
            score = 0
            status = release.get("status") or ""
            status = status.lower() if status else ""

            # Prefer official releases
            if status == "official":
                score += 100

            # Prefer releases with more info
            if release.get("date"):
                score += 10
            if release.get("country"):
                score += 5
            if release.get("barcode"):
                score += 5

            return score

        # Sort by score and return the best one
        return max(releases, key=score_release)

    def _populate_release_metadata(self, metadata: AudioMetadata, release: dict) -> None:
        """
        Populate metadata with release information.

        Args:
            metadata: AudioMetadata to populate.
            release: Release dictionary from MusicBrainz.
        """
        if not release:
            return

        metadata.album = release.get("title")
        metadata.release_mbid = release.get("id")
        metadata.barcode = release.get("barcode")
        metadata.asin = release.get("asin")
        metadata.release_status = release.get("status")
        metadata.release_country = release.get("country")

        # Get script (writing system)
        if "text-representation" in release:
            text_rep = release["text-representation"]
            metadata.script = text_rep.get("script")

        # Get full release date
        if "date" in release:
            metadata.date = release["date"]
            try:
                metadata.year = int(release["date"][:4])
            except (ValueError, IndexError):
                pass

        # Get medium (track/disc) info
        if "media" in release:
            mediums = release["media"]
            metadata.total_discs = len(mediums)

            # Find the track in the medium
            for disc_num, medium in enumerate(mediums, 1):
                metadata.media = medium.get("format")  # CD, Digital, etc.

                if "tracks" in medium:
                    tracks = medium["tracks"]
                    metadata.total_tracks = medium.get("track-count", len(tracks))

                    for track in tracks:
                        if track.get("recording", {}).get("id") == metadata.mbid:
                            metadata.disc_number = disc_num
                            try:
                                metadata.track_number = int(track.get("position", track.get("number", 1)))
                            except (ValueError, TypeError):
                                pass
                            break

        # Get label info
        if "label-info" in release and release["label-info"]:
            label_info = release["label-info"][0]
            if "label" in label_info and label_info["label"]:
                metadata.label = label_info["label"].get("name")
            metadata.catalog_number = label_info.get("catalog-number")

        # Get release group info (for release type)
        if "release-group" in release:
            rg = release["release-group"]
            metadata.release_group_mbid = rg.get("id")
            metadata.release_type = rg.get("primary-type")  # Album, Single, EP, etc.

            # Get original release year and date
            if "first-release-date" in rg:
                first_date = rg["first-release-date"]
                metadata.original_release_date = first_date
                try:
                    metadata.original_year = int(first_date[:4])
                except (ValueError, IndexError):
                    pass

        # Get album artist if different from track artist
        if "artist-credit" in release:
            album_artists = []
            album_artist_sort_names = []
            album_artist_mbids = []

            for artist_credit in release["artist-credit"]:
                if isinstance(artist_credit, dict) and "artist" in artist_credit:
                    artist = artist_credit["artist"]
                    album_artists.append(artist["name"])

                    # Get sort name
                    sort_name = artist.get("sort-name")
                    if sort_name:
                        album_artist_sort_names.append(sort_name)

                    # Get MBID
                    artist_id = artist.get("id")
                    if artist_id:
                        album_artist_mbids.append(artist_id)

            album_artist = ", ".join(album_artists)
            if album_artist != metadata.artist:
                metadata.album_artist = album_artist

            # Set sort order and MBIDs
            if album_artist_sort_names:
                metadata.album_artist_sort_order = ", ".join(album_artist_sort_names)
            if album_artist_mbids:
                metadata.release_artist_mbids = album_artist_mbids

    def _populate_basic_release_metadata(self, metadata: AudioMetadata, release: dict) -> None:
        """
        Populate metadata with basic release information (fallback).

        Args:
            metadata: AudioMetadata to populate.
            release: Release dictionary from MusicBrainz (limited info).
        """
        if not release:
            return

        metadata.album = release.get("title")
        metadata.release_mbid = release.get("id")
        metadata.release_status = release.get("status")
        metadata.release_country = release.get("country")

        if "date" in release:
            metadata.date = release["date"]
            try:
                metadata.year = int(release["date"][:4])
            except (ValueError, IndexError):
                pass

    def get_cover_url(self, release_mbid: str) -> str | None:
        """
        Get cover art URL for a release using Cover Art Archive API directly.

        Args:
            release_mbid: MusicBrainz Release ID.

        Returns:
            URL to cover art or None if not found.
        """
        if not release_mbid:
            return None

        logger.debug(f"Fetching cover art for release: {release_mbid}")

        caa_url = f"{self.COVER_ART_URL}/release/{release_mbid}"

        try:
            response = self.client.get(caa_url, follow_redirects=True, timeout=10.0)

            if response.status_code == 404:
                logger.debug(f"No cover art found for release: {release_mbid}")
                return None

            response.raise_for_status()
            data = response.json()

            if data and "images" in data and data["images"]:
                # Get the front cover
                for image in data["images"]:
                    if image.get("front", False):
                        return image.get("image")
                # If no front cover, return the first image
                return data["images"][0].get("image")

        except httpx.TimeoutException:
            logger.warning(f"Cover art request timed out for release: {release_mbid}")
        except httpx.HTTPError as e:
            logger.debug(f"No cover art found for release: {release_mbid} ({e})")
        except Exception as e:
            logger.warning(f"Error fetching cover art: {e}")

        return None

    def search_recordings(self, query: str, artist: str | None = None, limit: int = 5, strict: bool = True) -> list[dict]:
        """
        Search for recordings by query string.

        Args:
            query: Search query (track title or raw string).
            artist: Artist name to narrow search (optional).
            limit: Maximum number of results.
            strict: If True, uses field prefixes (recording:..., artist:...).
                    If False, uses raw query string for fuzzy matching.

        Returns:
            List of recording search results.
        """
        logger.info(f"Searching MusicBrainz ({'strict' if strict else 'relaxed'}): {query}" + (f" by {artist}" if artist else ""))

        url = f"{self.BASE_URL}/recording"

        # Build search query
        search_parts = []

        if strict:
            if query:
                search_parts.append(f'recording:"{query}"')
            if artist:
                search_parts.append(f'artist:"{artist}"')
            search_query = " AND ".join(search_parts) if search_parts else query
        else:
            # Relaxed search: just combine terms
            terms = [query]
            if artist:
                terms.append(artist)
            search_query = " ".join(terms)



        params = {
            "query": search_query,
            "limit": limit,
            "fmt": "json",
        }

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            recordings = data.get("recordings", [])
            logger.debug(f"Found {len(recordings)} recordings")
            return recordings

        except httpx.HTTPError as e:
            logger.warning(f"MusicBrainz search error: {e}")
            return []

    def get_best_search_result(self, query: str, artist: str | None = None, strict: bool = True) -> str | None:
        """
        Search and return the best matching recording ID.

        Args:
            query: Track title.
            artist: Artist name (optional).
            strict: Strict search mode (field prefixes).

        Returns:
            Best matching recording MBID or None.
        """
        # Check search cache first
        cached_id = self.cache.get_search_result(query, artist, strict)
        if cached_id is not None:
            logger.info(f"Cache hit for search: '{query}'")
            return cached_id if cached_id else None

        recordings = self.search_recordings(query, artist, limit=5, strict=strict)

        if not recordings:
            # Cache negative result
            self.cache.set_search_result(query, artist, strict, "")
            return None

        # Return the first (best) result's ID
        best = recordings[0]
        recording_id = best.get("id")

        if recording_id:
            title = best.get("title", "Unknown")
            artist_credits = best.get("artist-credit", [])
            artist_name = artist_credits[0].get("name", "Unknown") if artist_credits else "Unknown"
            score = best.get("score", 0)
            logger.info(f"Best search match: {title} - {artist_name} (score: {score})")

            # Cache the result
            self.cache.set_search_result(query, artist, strict, recording_id)

        return recording_id
