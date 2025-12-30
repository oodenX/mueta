# src/mueta/engine/models.py
"""Data models for mueta engine."""

from pydantic import BaseModel


class AudioMetadata(BaseModel):
    """Unified audio metadata model - Extended like Picard."""

    # Basic info
    title: str | None = None
    artist: str | None = None
    artists: list[str] | None = None  # Multiple artists list
    album: str | None = None
    album_artist: str | None = None

    # Sort orders (for proper alphabetization)
    artist_sort_order: str | None = None
    album_artist_sort_order: str | None = None

    # Track/Disc info
    track_number: int | None = None
    total_tracks: int | None = None
    disc_number: int | None = None
    total_discs: int | None = None

    # Date info
    year: int | None = None
    original_year: int | None = None  # Original release year
    date: str | None = None  # Full release date (YYYY-MM-DD)
    original_release_date: str | None = None  # Original release date (YYYY-MM-DD)

    # Classification
    genre: str | None = None

    # Credits
    composer: str | None = None
    lyricist: str | None = None
    producer: str | None = None
    arranger: str | None = None
    mixer: str | None = None
    conductor: str | None = None
    performer: str | None = None
    writer: str | None = None  # Songwriter

    # Additional info
    language: str | None = None
    copyright: str | None = None

    # Release info
    label: str | None = None  # Record label
    catalog_number: str | None = None  # Label catalog number
    barcode: str | None = None  # UPC/EAN barcode
    asin: str | None = None  # Amazon Standard Identification Number
    isrc: str | None = None  # International Standard Recording Code
    media: str | None = None  # Media type (CD, Digital, Vinyl, etc.)
    release_type: str | None = None  # Album, Single, EP, etc.
    release_status: str | None = None  # Official, Bootleg, etc.
    release_country: str | None = None  # Release country
    script: str | None = None  # Script/writing system (Jpan, Latn, etc.)

    # Audio info
    duration: float | None = None
    bpm: float | None = None

    # MusicBrainz IDs
    mbid: str | None = None  # MusicBrainz Recording ID (also known as Track ID)
    release_mbid: str | None = None  # MusicBrainz Release ID
    release_group_mbid: str | None = None  # MusicBrainz Release Group ID
    artist_mbid: str | None = None  # MusicBrainz Artist ID
    release_artist_mbids: list[str] | None = None  # MusicBrainz Release Artist IDs
    work_mbid: str | None = None  # MusicBrainz Work ID
    acoustid_id: str | None = None  # AcoustID fingerprint ID

    # Cover and lyrics
    cover_url: str | None = None
    lyrics: str | None = None
    synced_lyrics: str | None = None  # LRC format


class LyricsResult(BaseModel):
    """Lyrics search result from LRCLIB."""

    id: int
    track_name: str
    artist_name: str
    album_name: str | None = None
    duration: float | None = None
    instrumental: bool = False
    plain_lyrics: str | None = None
    synced_lyrics: str | None = None  # LRC format


class ProcessOptions(BaseModel):
    """Options for processing audio files."""

    download_lyrics: bool = False
    embed_lyrics: bool = False
    embed_cover: bool = True
    reserve_original: bool = False  # If True, keep original file and copy; if False, move file


class ProcessResult(BaseModel):
    """Result of processing a single audio file."""

    success: bool
    file_path: str
    title: str | None = None
    artist: str | None = None
    error: str | None = None
    metadata: AudioMetadata | None = None
