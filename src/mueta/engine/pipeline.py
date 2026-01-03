# src/mueta/engine/pipeline.py
"""Main processing pipeline for mueta."""

import re
import shutil
from pathlib import Path

import httpx
from loguru import logger
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from mueta.core.config import settings
from mueta.engine.cover import CoverService
from mueta.engine.fingerprint import FingerprintService
from mueta.engine.lyrics import LyricsService
from mueta.engine.models import AudioMetadata, ProcessOptions, ProcessResult
from mueta.engine.musicbrainz import MusicBrainzService
from mueta.engine.tagger import TaggerService
from mueta.utils.errors import translate_http_error


class MetaPipeline:
    """Main pipeline for processing audio files and fetching metadata."""

    def __init__(self):
        from mueta.engine.analysis import AudioAnalyzer

        self.fingerprint = FingerprintService()
        self.musicbrainz = MusicBrainzService()
        self.lyrics = LyricsService()
        self.tagger = TaggerService()
        self.cover = CoverService()
        self.analyzer = AudioAnalyzer()

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
                logger.warning(
                    f"Invalid audio file: {file_path.name} - {validation_error}"
                )
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
                logger.warning(
                    f"No AcoustID match for: {file_path.name}, trying MusicBrainz search..."
                )

                # Try to parse filename for artist and title
                artist, title = self._parse_filename(file_path.stem)

                candidates = []
                if artist and title:
                    # 1. Strict search with parsed order
                    candidates.append((title, artist, True))
                    # 2. Strict search with swapped order (Title - Artist assumption)
                    candidates.append((artist, title, True))  # Swap
                elif title:
                    candidates.append((title, None, True))

                # 3. Relaxed search (fuzzy match)
                if artist and title:
                    candidates.append((f"{title} {artist}", None, False))
                elif title:
                    candidates.append((title, None, False))

                # Clean up artist name for first attempts
                clean_artist = None
                if artist and "、" in artist:
                    clean_artist = artist.split("、")[0].strip()

                # Execute search strategy
                for q_title, q_artist, strict in candidates:
                    # Use cleaned artist for strict searches if available
                    search_artist = q_artist
                    if strict and search_artist and "、" in search_artist:
                        search_artist = search_artist.split("、")[0].strip()

                    if options.interactive:
                        # Interactive mode: search and prompt
                        query = (
                            f'recording:"{q_title}" AND artist:"{search_artist}"'
                            if strict
                            else q_title
                        )
                        results = self.musicbrainz.search_recordings(query, limit=5)

                        if results:
                            selected_id = self._prompt_user_selection(
                                results, q_title, search_artist or ""
                            )
                            if selected_id:
                                recording_id = selected_id
                                break
                    else:
                        # Automatic mode: pick best match
                        recording_id = self.musicbrainz.get_best_search_result(
                            q_title, search_artist, strict=strict
                        )
                        if recording_id:
                            logger.info(
                                f"Match found using strategy: title='{q_title}', artist='{search_artist}', strict={strict}"
                            )
                            break

                if not recording_id:
                    # Fallback: Try to get lyrics using existing metadata from file tags
                    if existing_meta and existing_meta.title and existing_meta.artist:
                        logger.info(
                            f"MusicBrainz failed, trying lyrics with existing tags: {existing_meta.artist} - {existing_meta.title}"
                        )

                        # Attempt lyrics fetch using existing metadata
                        if options.download_lyrics or options.embed_lyrics:
                            lyrics_result = self.lyrics.get_lyrics(
                                artist=existing_meta.artist,
                                track=existing_meta.title,
                                album=existing_meta.album,
                                duration=existing_meta.duration,
                            )

                            if lyrics_result:
                                logger.info(f"Lyrics found via existing metadata!")

                                # Embed if requested
                                if options.embed_lyrics:
                                    if lyrics_result.synced_lyrics:
                                        self.tagger.embed_lyrics(
                                            file_path,
                                            lyrics_result.synced_lyrics,
                                            synced=True,
                                        )
                                    elif lyrics_result.plain_lyrics:
                                        self.tagger.embed_lyrics(
                                            file_path,
                                            lyrics_result.plain_lyrics,
                                            synced=False,
                                        )

                                # Save .lrc file
                                if (
                                    settings.lyrics_save_dir
                                    and lyrics_result.synced_lyrics
                                ):
                                    lrc_dir = Path(settings.lyrics_save_dir)
                                    lrc_dir.mkdir(parents=True, exist_ok=True)
                                    safe_artist = re.sub(
                                        r'[<>:"/\\|?*]', "_", existing_meta.artist
                                    )
                                    safe_title = re.sub(
                                        r'[<>:"/\\|?*]', "_", existing_meta.title
                                    )
                                    lrc_path = (
                                        lrc_dir / f"{safe_artist} - {safe_title}.lrc"
                                    )
                                    self.lyrics.save_lrc_file(
                                        lyrics_result.synced_lyrics, lrc_path
                                    )

                                # Mark as partial success
                                result.success = True
                                result.metadata = existing_meta
                                result.error = "MusicBrainz failed but lyrics found via existing tags"
                                self._handle_file_placement(file_path, options)
                                return result

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
            if options.embed_cover:
                cover_data = None

                # Try MusicBrainz / Cover Art Archive first
                if metadata.release_mbid:
                    cover_url = self.musicbrainz.get_cover_url(metadata.release_mbid)
                    if cover_url:
                        metadata.cover_url = cover_url
                        cover_data = self.cover.download(cover_url)

                # Fallback to NetEase/QQMusic if no cover from MusicBrainz
                if not cover_data and metadata.artist and metadata.title:
                    logger.info(
                        "MusicBrainz cover not found, trying NetEase/QQMusic..."
                    )
                    cover_data = self.cover.get_cover_fallback(
                        metadata.artist, metadata.title
                    )

                # Embed cover if found
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
                            safe_artist = re.sub(r'[<>:"/\\|?*]', "_", metadata.artist)
                            safe_title = re.sub(r'[<>:"/\\|?*]', "_", metadata.title)

                            lrc_path = lrc_dir / f"{safe_artist} - {safe_title}.lrc"
                            self.lyrics.save_lrc_file(
                                lyrics_result.synced_lyrics, lrc_path
                            )

            # Step 5b: Analyze audio (if enabled)
            if options.analyze:
                logger.info(f"Analyzing audio features for: {file_path.name}")
                analysis_meta = self.analyzer.analyze(file_path)
                # Merge analysis results into metadata
                if analysis_meta.bpm:
                    metadata.bpm = analysis_meta.bpm
                if analysis_meta.key:
                    metadata.key = analysis_meta.key
                if analysis_meta.scale:
                    metadata.scale = analysis_meta.scale
                if analysis_meta.loudness_lufs:
                    metadata.loudness_lufs = analysis_meta.loudness_lufs
                if analysis_meta.danceability:
                    metadata.danceability = analysis_meta.danceability

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
            logger.error(f"Pipeline error for {file_path.name}: {e}")
            # Translate HTTP errors to user-friendly messages
            if isinstance(
                e,
                (
                    httpx.HTTPError,
                    httpx.HTTPStatusError,
                    httpx.ConnectError,
                    httpx.TimeoutException,
                ),
            ):
                result.error = translate_http_error(e)
            else:
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
        Parse filename to extract artist and title with smart pattern recognition.

        Supported formats:
        - "Title - Artist"
        - "Title (feat. X) - Artist"
        - "[Artist] Title"
        - "Title (Artist)"
        - "Title [Cover] - Artist"

        Args:
            filename: Filename without extension.

        Returns:
            Tuple of (artist, title).
        """
        original_filename = filename

        # Step 1: Extract featured artists from (feat. X) or (ft. X) patterns
        feat_match = re.search(
            r"\((?:feat\.?|ft\.?)\s*([^)]+)\)", filename, re.IGNORECASE
        )
        featured_artists = feat_match.group(1).strip() if feat_match else None

        # Step 2: Remove noise patterns but keep track of them
        # Remove (feat. ...), [Cover], [Remix], etc.
        clean_filename = re.sub(
            r"\s*\((?:feat\.?|ft\.?)\s*[^)]+\)", "", filename, flags=re.IGNORECASE
        )
        clean_filename = re.sub(
            r"\s*\[(?:Cover|Remix|Instrumental|Live|Ver\.?|Version)\]",
            "",
            clean_filename,
            flags=re.IGNORECASE,
        )
        clean_filename = clean_filename.strip()

        # Step 3: Try different parsing strategies

        # Strategy A: "[Artist] Title" format
        bracket_artist_match = re.match(r"^\[([^\]]+)\]\s*(.+)$", clean_filename)
        if bracket_artist_match:
            artist = bracket_artist_match.group(1).strip()
            title = bracket_artist_match.group(2).strip()
            return artist, title

        # Strategy B: "Title (Artist)" format (parentheses at end)
        paren_artist_match = re.match(r"^(.+?)\s*\(([^)]+)\)$", clean_filename)
        if paren_artist_match:
            title = paren_artist_match.group(1).strip()
            artist = paren_artist_match.group(2).strip()
            return artist, title

        # Strategy C: Standard "X - Y" format
        parts = clean_filename.split(" - ")
        if len(parts) >= 2:
            part1, part2 = parts[0].strip(), " - ".join(parts[1:]).strip()

            # Heuristic detection:
            # - If part2 contains '、' (Japanese comma) → likely multiple artists → part2 is artist
            # - If part2 is mostly CJK characters → likely artist
            # - Otherwise, assume "Title - Artist" or "Artist - Title" based on length

            if "、" in part2:
                # "Title - Artist1、Artist2" format
                return part2, part1
            elif "、" in part1:
                # "Artist1、Artist2 - Title" format
                return part1, part2
            else:
                # Default: assume "Title - Artist" based on common naming
                # Check if part1 looks more like a title (longer, has numbers/symbols)
                # Or part2 looks more like artist (shorter, proper noun style)
                return part2, part1  # Assume "Title - Artist"

        # Step 4: No clear separator, use filename as title
        return None, clean_filename

    def _handle_file_placement(
        self, file_path: Path, options: ProcessOptions
    ) -> Path | None:
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

    def _prompt_user_selection(
        self, candidates: list[dict], title: str, artist: str
    ) -> str | None:
        """
        Interactive prompt for user to select a recording.
        """
        console = Console()
        console.print(
            f"\n[bold cyan]❓ Multiple matches found for:[/bold cyan] {title} - {artist}"
        )

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Title", style="white")
        table.add_column("Artist", style="green")
        table.add_column("Album", style="cyan")
        table.add_column("Date", style="yellow")
        table.add_column("Score", style="blue")

        for idx, rec in enumerate(candidates, 1):
            rec_title = rec.get("title", "Unknown")
            rec_artists = (
                ", ".join(a["name"] for a in rec.get("artist-credit", [])) or "Unknown"
            )
            rec_album = (
                rec.get("releases", [{}])[0].get("title", "Unknown")
                if rec.get("releases")
                else "Unknown"
            )
            rec_date = rec.get("first-release-date", "Unknown")
            score = rec.get("score", "N/A")

            table.add_row(
                str(idx), rec_title, rec_artists, rec_album, rec_date, str(score)
            )

        console.print(table)

        choices = [str(i) for i in range(1, len(candidates) + 1)] + ["0", "s", "skip"]
        selection = Prompt.ask(
            "Select a match (0/s to skip)", choices=choices, default="1"
        )

        if selection in ("0", "s", "skip"):
            return None

        index = int(selection) - 1
        return candidates[index]["id"]
