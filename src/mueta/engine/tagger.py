# src/mueta/engine/tagger.py
"""Audio file tag reader and writer using mutagen."""

from pathlib import Path
from loguru import logger
from mutagen._file import File
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from mutagen.id3._util import ID3NoHeaderError
from mutagen.id3._frames import APIC, USLT
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover

from mueta.engine.models import AudioMetadata


class TaggerService:
    """Service for reading and writing audio file tags."""

    # Supported audio formats
    SUPPORTED_EXTENSIONS = {'.mp3', '.flac', '.m4a', '.ogg', '.opus', '.wav', '.aac', '.wma'}

    def validate_audio_file(self, file_path: Path) -> tuple[bool, str]:
        """
        Validate if a file is a valid audio file that can be processed.

        Args:
            file_path: Path to the audio file.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check file extension
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported format: {file_path.suffix}"

        # Check file size (minimum 1KB to filter empty/corrupted files)
        try:
            file_size = file_path.stat().st_size
            if file_size < 1024:
                return False, f"File too small ({file_size} bytes), likely corrupted"
        except OSError as e:
            return False, f"Cannot read file: {e}"

        # Try to read the file with mutagen to verify it's valid audio
        try:
            audio = File(file_path)
            if audio is None:
                return False, "Not a valid audio file or unsupported format"
            # Check if file has audio info
            if not hasattr(audio, 'info') or audio.info is None:
                return False, "Cannot read audio information"
            return True, ""
        except Exception as e:
            error_msg = str(e)
            # Provide more user-friendly error messages
            if "can't sync to MPEG frame" in error_msg:
                return False, "Corrupted MP3 file (invalid MPEG frames)"
            elif "not a valid" in error_msg.lower():
                return False, "Invalid or corrupted audio file"
            return False, f"Audio validation failed: {error_msg}"

    def read_metadata(self, file_path: Path) -> AudioMetadata:
        """
        Read metadata from an audio file.

        Args:
            file_path: Path to the audio file.

        Returns:
            AudioMetadata with existing tags.
        """
        logger.debug(f"Reading metadata from: {file_path}")

        try:
            audio = File(file_path, easy=True)
        except Exception as e:
            logger.warning(f"Failed to read metadata: {e}")
            return AudioMetadata()

        if audio is None:
            return AudioMetadata()

        def get_first(key: str) -> str | None:
            values = audio.get(key)
            return values[0] if values else None

        def get_int(key: str) -> int | None:
            value = get_first(key)
            if value:
                try:
                    # Handle formats like "1/12"
                    return int(value.split("/")[0])
                except ValueError:
                    return None
            return None

        def get_list(key: str) -> list[str] | None:
            values = audio.get(key)
            return list(values) if values else None

        return AudioMetadata(
            title=get_first("title"),
            artist=get_first("artist"),
            artists=get_list("artists"),
            artist_sort_order=get_first("artistsort"),
            album=get_first("album"),
            album_artist=get_first("albumartist"),
            album_artist_sort_order=get_first("albumartistsort"),
            track_number=get_int("tracknumber"),
            disc_number=get_int("discnumber"),
            year=get_int("date"),
            original_release_date=get_first("originaldate"),
            genre=get_first("genre"),
            # Credits
            composer=get_first("composer"),
            lyricist=get_first("lyricist"),
            producer=get_first("producer"),
            arranger=get_first("arranger"),
            mixer=get_first("mixer"),
            conductor=get_first("conductor"),
            performer=get_first("performer"),
            writer=get_first("writer"),
            # Release info
            isrc=get_first("isrc"),
            barcode=get_first("barcode"),
            asin=get_first("asin"),
            label=get_first("label"),
            catalog_number=get_first("catalognumber"),
            media=get_first("media"),
            release_type=get_first("releasetype"),
            release_status=get_first("releasestatus"),
            release_country=get_first("releasecountry"),
            script=get_first("script"),
            # Additional info
            language=get_first("language"),
            copyright=get_first("copyright"),
            # MusicBrainz IDs
            mbid=get_first("musicbrainz_recordingid"),
            release_mbid=get_first("musicbrainz_albumid"),
            release_group_mbid=get_first("musicbrainz_releasegroupid"),
            artist_mbid=get_first("musicbrainz_artistid"),
            release_artist_mbids=get_list("musicbrainz_albumartistid"),
            work_mbid=get_first("musicbrainz_workid"),
            acoustid_id=get_first("acoustid_id"),
            duration=audio.info.length if audio.info else None,
        )

    def write_metadata(self, file_path: Path, meta: AudioMetadata) -> None:
        """
        Write metadata to an audio file.

        Args:
            file_path: Path to the audio file.
            meta: AudioMetadata to write.
        """
        logger.info(f"Writing metadata to: {file_path}")

        try:
            audio = File(file_path, easy=True)
        except Exception as e:
            logger.error(f"Failed to open file for writing: {e}")
            raise

        if audio is None:
            logger.error(f"Unsupported file format: {file_path}")
            raise ValueError(f"Unsupported file format: {file_path}")

        # Map metadata fields to tag keys (EasyID3/EasyMP4/etc. compatible)
        tag_mapping = {
            "title": meta.title,
            "artist": meta.artist,
            "album": meta.album,
            "albumartist": meta.album_artist,
            "genre": meta.genre,
            # Credits
            "composer": meta.composer,
            "lyricist": meta.lyricist,
            "producer": meta.producer,
            "arranger": meta.arranger,
            "mixer": meta.mixer,
            "conductor": meta.conductor,
            "performer": meta.performer,
            "writer": meta.writer,
            # Release info
            "isrc": meta.isrc,
            "barcode": meta.barcode,
            "asin": meta.asin,
            "label": meta.label,
            "catalognumber": meta.catalog_number,
            "media": meta.media,
            "releasetype": meta.release_type,
            "releasestatus": meta.release_status,
            "releasecountry": meta.release_country,
            "script": meta.script,
            # Additional
            "language": meta.language,
            "copyright": meta.copyright,
            # Sort orders
            "artistsort": meta.artist_sort_order,
            "albumartistsort": meta.album_artist_sort_order,
            # MusicBrainz IDs
            "musicbrainz_recordingid": meta.mbid,
            "musicbrainz_albumid": meta.release_mbid,
            "musicbrainz_releasegroupid": meta.release_group_mbid,
            "musicbrainz_artistid": meta.artist_mbid,
            "musicbrainz_workid": meta.work_mbid,
            "acoustid_id": meta.acoustid_id,
        }

        for key, value in tag_mapping.items():
            if value:
                try:
                    audio[key] = value
                except (KeyError, ValueError):
                    # Some tags may not be supported by EasyID3/EasyMP4
                    logger.debug(f"Tag not supported: {key}")

        # Numeric fields with special handling
        if meta.track_number:
            if meta.total_tracks:
                audio["tracknumber"] = f"{meta.track_number}/{meta.total_tracks}"
            else:
                audio["tracknumber"] = str(meta.track_number)

        if meta.disc_number:
            if meta.total_discs:
                audio["discnumber"] = f"{meta.disc_number}/{meta.total_discs}"
            else:
                audio["discnumber"] = str(meta.disc_number)

        if meta.year:
            audio["date"] = str(meta.year)
        elif meta.date:
            audio["date"] = meta.date

        if meta.original_year:
            try:
                audio["originaldate"] = str(meta.original_year)
            except (KeyError, ValueError):
                pass

        # Original release date (full date)
        if meta.original_release_date:
            try:
                audio["originaldate"] = meta.original_release_date
            except (KeyError, ValueError):
                pass

        # Multiple artists
        if meta.artists:
            try:
                audio["artists"] = meta.artists
            except (KeyError, ValueError):
                pass

        # Release artist MBIDs
        if meta.release_artist_mbids:
            try:
                audio["musicbrainz_albumartistid"] = meta.release_artist_mbids
            except (KeyError, ValueError):
                pass

        if meta.bpm:
            try:
                audio["bpm"] = str(int(meta.bpm))
            except (KeyError, ValueError):
                pass

        audio.save()
        logger.debug(f"Metadata saved to: {file_path}")

    def embed_cover(self, file_path: Path, image_data: bytes, mime_type: str = "image/jpeg") -> None:
        """
        Embed cover art into an audio file.

        Args:
            file_path: Path to the audio file.
            image_data: Cover image data.
            mime_type: MIME type of the image.
        """
        logger.debug(f"Embedding cover art to: {file_path}")

        suffix = file_path.suffix.lower()

        try:
            if suffix == ".mp3":
                self._embed_cover_mp3(file_path, image_data, mime_type)
            elif suffix == ".flac":
                self._embed_cover_flac(file_path, image_data, mime_type)
            elif suffix in (".m4a", ".mp4", ".aac"):
                self._embed_cover_mp4(file_path, image_data, mime_type)
            else:
                logger.warning(f"Cover embedding not supported for: {suffix}")
        except Exception as e:
            logger.error(f"Failed to embed cover: {e}")
            raise

    def _embed_cover_mp3(self, file_path: Path, image_data: bytes, mime_type: str) -> None:
        """Embed cover to MP3 file."""
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()

        audio.delall("APIC")
        audio.add(
            APIC(
                encoding=3,  # UTF-8
                mime=mime_type,
                type=3,  # Cover (front)
                desc="Cover",
                data=image_data,
            )
        )
        audio.save(file_path)

    def _embed_cover_flac(self, file_path: Path, image_data: bytes, mime_type: str) -> None:
        """Embed cover to FLAC file."""
        audio = FLAC(file_path)
        audio.clear_pictures()

        picture = Picture()
        picture.type = 3  # Cover (front)
        picture.mime = mime_type
        picture.desc = "Cover"
        picture.data = image_data

        audio.add_picture(picture)
        audio.save()

    def _embed_cover_mp4(self, file_path: Path, image_data: bytes, mime_type: str) -> None:
        """Embed cover to MP4/M4A file."""
        audio = MP4(file_path)

        if mime_type == "image/png":
            cover_format = MP4Cover.FORMAT_PNG
        else:
            cover_format = MP4Cover.FORMAT_JPEG

        audio["covr"] = [MP4Cover(image_data, imageformat=cover_format)]
        audio.save()

    def embed_lyrics(self, file_path: Path, lyrics: str, synced: bool = False) -> None:
        """
        Embed lyrics into an audio file.

        Args:
            file_path: Path to the audio file.
            lyrics: Lyrics text.
            synced: Whether the lyrics are synced (LRC format).
        """
        logger.debug(f"Embedding lyrics to: {file_path}")

        suffix = file_path.suffix.lower()

        try:
            if suffix == ".mp3":
                self._embed_lyrics_mp3(file_path, lyrics, synced)
            elif suffix == ".flac":
                self._embed_lyrics_flac(file_path, lyrics)
            elif suffix in (".m4a", ".mp4", ".aac"):
                self._embed_lyrics_mp4(file_path, lyrics)
            else:
                logger.warning(f"Lyrics embedding not supported for: {suffix}")
        except Exception as e:
            logger.error(f"Failed to embed lyrics: {e}")
            raise

    def _embed_lyrics_mp3(self, file_path: Path, lyrics: str, synced: bool) -> None:
        """Embed lyrics to MP3 file."""
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()

        audio.delall("USLT")
        audio.add(
            USLT(
                encoding=3,  # UTF-8
                lang="eng",
                desc="Lyrics",
                text=lyrics,
            )
        )
        audio.save(file_path)

    def _embed_lyrics_flac(self, file_path: Path, lyrics: str) -> None:
        """Embed lyrics to FLAC file."""
        audio = FLAC(file_path)
        audio["LYRICS"] = lyrics
        audio.save()

    def _embed_lyrics_mp4(self, file_path: Path, lyrics: str) -> None:
        """Embed lyrics to MP4/M4A file."""
        audio = MP4(file_path)
        audio["\xa9lyr"] = lyrics
        audio.save()
