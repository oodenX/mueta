# src/mueta/engine/pipeline.py
"""Main processing pipeline for mueta."""

from pathlib import Path
from loguru import logger
import shutil
import re

from mueta.core.config import settings
from mueta.engine.models import AudioMetadata, ProcessOptions, ProcessResult
from mueta.engine.fingerprint import FingerprintService
from mueta.engine.musicbrainz import MusicBrainzService
from mueta.engine.lyrics import LyricsService
from mueta.engine.tagger import TaggerService
from mueta.engine.cover import CoverService


class MetaPipeline:
    """Main pipeline for processing audio files and fetching metadata."""

    def __init__(self):
        self.fingerprint = FingerprintService()
        self.musicbrainz = MusicBrainzService()
        self.lyrics = LyricsService()
        self.tagger = TaggerService()
        self.cover = CoverService()

    def process_file(self, file_path: Path, options: ProcessOptions) -> ProcessResult:
        """
        Process a single audio file.

        Args:
            file_path: Path to the audio file.
            options: Processing options.

        Returns:
            ProcessResult with success status and metadata.
        """
        logger.info(f"Processing: {file_path.name}")

        result = ProcessResult(
            success=False,
            file_path=str(file_path),
        )

        try:
            # Step 0: Validate audio file first (quick check)
            is_valid, validation_error = self.tagger.validate_audio_file(file_path)
            if not is_valid:
                result.error = validation_error
                logger.warning(f"Invalid audio file: {file_path.name} - {validation_error}")
                # Still move file even if invalid (to avoid reprocessing)
                self._handle_file_placement(file_path, options)
                return result

            # Step 1: Read existing metadata
            existing_meta = self.tagger.read_metadata(file_path)

            # Step 2: Get fingerprint and lookup in AcoustID
            match = self.fingerprint.get_best_match(file_path)
            recording_id = None

            if match:
                recording_id = match.get("recording_id")

            # Step 2b: Fallback to MusicBrainz search if no AcoustID match
            if not recording_id:
                logger.warning(f"No AcoustID match for: {file_path.name}, trying MusicBrainz search...")

                # Try to parse filename for artist and title
                artist, title = self._parse_filename(file_path.stem)

                candidates = []
                if artist and title:
                    # 1. Strict search with parsed order
                    candidates.append((title, artist, True))
                    # 2. Strict search with swapped order (Title - Artist assumption)
                    candidates.append((artist, title, True)) # Swap
                elif title:
                    candidates.append((title, None, True))

                # 3. Relaxed search (fuzzy match)
                if artist and title:
                    candidates.append((f"{title} {artist}", None, False))
                elif title:
                     candidates.append((title, None, False))

                # Clean up artist name for first attempts
                clean_artist = None
                if artist and '、' in artist:
                    clean_artist = artist.split('、')[0].strip()

                # Execute search strategy
                for q_title, q_artist, strict in candidates:
                    # Use cleaned artist for strict searches if available
                    search_artist = q_artist
                    if strict and search_artist and '、' in search_artist:
                        search_artist = search_artist.split('、')[0].strip()

                    recording_id = self.musicbrainz.get_best_search_result(q_title, search_artist, strict=strict)
                    if recording_id:
                        logger.info(f"Match found using strategy: title='{q_title}', artist='{search_artist}', strict={strict}")
                        break

                if not recording_id:
                    result.error = "No match found in AcoustID or MusicBrainz search"
                    logger.warning(f"No match found for: {file_path.name}")

                    # Still move/copy file even if failed
                    self._handle_file_placement(file_path, options)
                    return result

            # Step 3: Get full metadata from MusicBrainz
            metadata = self.musicbrainz.get_recording(recording_id)

            # Set acoustid_id if we got it from AcoustID lookup
            if match and match.get("acoustid_id"):
                metadata.acoustid_id = match["acoustid_id"]

            # Step 4: Get and embed cover art (if enabled)
            if options.embed_cover and metadata.release_mbid:
                cover_url = self.musicbrainz.get_cover_url(metadata.release_mbid)
                if cover_url:
                    metadata.cover_url = cover_url
                    cover_data = self.cover.download(cover_url)
                    if cover_data:
                        image_data, mime_type = cover_data
                        self.tagger.embed_cover(file_path, image_data, mime_type)

            # Step 5: Get lyrics (if enabled)
            if options.download_lyrics or options.embed_lyrics:
                if metadata.artist and metadata.title:
                    lyrics_result = self.lyrics.get_lyrics(
                        artist=metadata.artist,
                        track=metadata.title,
                        album=metadata.album,
                        duration=metadata.duration,
                    )

                    if lyrics_result:
                        metadata.lyrics = lyrics_result.plain_lyrics
                        metadata.synced_lyrics = lyrics_result.synced_lyrics

                        # Embed lyrics if requested
                        if options.embed_lyrics and lyrics_result.synced_lyrics:
                            self.tagger.embed_lyrics(
                                file_path,
                                lyrics_result.synced_lyrics,
                                synced=True,
                            )
                        elif options.embed_lyrics and lyrics_result.plain_lyrics:
                            self.tagger.embed_lyrics(
                                file_path,
                                lyrics_result.plain_lyrics,
                                synced=False,
                            )

                        # Save .lrc file if configured (regardless of explicit download option since we have it)
                        if settings.lyrics_save_dir and lyrics_result.synced_lyrics:
                            lrc_dir = Path(settings.lyrics_save_dir)
                            lrc_dir.mkdir(parents=True, exist_ok=True)

                            # Clean filename
                            safe_artist = re.sub(r'[<>:"/\\|?*]', '_', metadata.artist)
                            safe_title = re.sub(r'[<>:"/\\|?*]', '_', metadata.title)

                            lrc_path = lrc_dir / f"{safe_artist} - {safe_title}.lrc"
                            self.lyrics.save_lrc_file(lyrics_result.synced_lyrics, lrc_path)

            # Step 6: Write metadata to file
            self.tagger.write_metadata(file_path, metadata)

            # Step 7: Handle file placement (move or copy)
            new_path = self._handle_file_placement(file_path, options)
            if new_path:
                result.file_path = str(new_path)

            # Success!
            result.success = True
            result.title = metadata.title
            result.artist = metadata.artist
            result.metadata = metadata

            logger.info(f"Successfully processed: {metadata.title} - {metadata.artist}")
            return result

        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            result.error = str(e)

            # Still handle file placement even on error
            try:
                new_path = self._handle_file_placement(file_path, options)
                if new_path:
                    result.file_path = str(new_path)
            except Exception as move_error:
                logger.error(f"Failed to move/copy file: {move_error}")

            return result

    def _parse_filename(self, filename: str) -> tuple[str | None, str | None]:
        """
        Parse filename to extract artist and title.

        Common formats:
        - "Artist - Title"
        - "Title - Artist"
        - "Artist、Artist - Title"

        Args:
            filename: Filename without extension.

        Returns:
            Tuple of (artist, title).
        """
        # Remove common unwanted patterns
        filename = re.sub(r'\(.*?\)', '', filename)  # Remove (feat. ...)
        filename = re.sub(r'\[.*?\]', '', filename)  # Remove [...]
        filename = filename.strip()

        # Try to split by " - "
        parts = filename.split(' - ')

        if len(parts) >= 2:
            # Assume format: "Title - Artist" or "Artist - Title"
            # Check which part has Japanese/Chinese characters (more likely artist)
            part1, part2 = parts[0].strip(), parts[-1].strip()

            # Heuristic: if second part has "、" (Japanese comma), it's likely artist
            if '、' in part2:
                return part2, part1  # artist, title
            else:
                return part1, part2  # assume artist, title

        # No clear separator, use filename as title
        return None, filename

    def _handle_file_placement(self, file_path: Path, options: ProcessOptions) -> Path | None:
        """
        Handle file placement according to options.

        Args:
            file_path: Original file path.
            options: Processing options.

        Returns:
            New file path or None if file wasn't moved/copied.
        """
        if not file_path.exists():
            return None

        audio_save_dir = Path(settings.audio_save_dir)
        audio_save_dir.mkdir(parents=True, exist_ok=True)

        # Generate destination path
        dest_path = audio_save_dir / file_path.name

        # Handle name collision
        if dest_path.exists() and dest_path != file_path:
            # Add number suffix
            stem = dest_path.stem
            suffix = dest_path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = audio_save_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        try:
            if options.reserve_original:
                # Copy file (keep original)
                if dest_path != file_path:
                    shutil.copy2(file_path, dest_path)
                    logger.info(f"Copied to: {dest_path}")
                    return dest_path
                return file_path
            else:
                # Move file (remove original)
                if dest_path != file_path:
                    shutil.move(str(file_path), str(dest_path))
                    logger.info(f"Moved to: {dest_path}")
                    return dest_path
                return file_path

        except Exception as e:
            logger.error(f"Failed to handle file placement: {e}")
            return None
