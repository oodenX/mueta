# src/mueta/engine/cache.py
"""SQLite cache for MusicBrainz and AcoustID results."""

import json
import sqlite3
from pathlib import Path
from typing import Any
from loguru import logger


class MetadataCache:
    """SQLite-based cache for metadata lookups."""

    def __init__(self, cache_path: Path | None = None):
        """Initialize the cache.

        Args:
            cache_path: Path to SQLite database. Defaults to ~/.mueta/cache.db
        """
        if cache_path is None:
            cache_path = Path.home() / ".mueta" / "cache.db"

        self.cache_path = cache_path
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS musicbrainz_recordings (
                    recording_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS acoustid_lookups (
                    fingerprint_hash TEXT PRIMARY KEY,
                    recording_id TEXT,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    query_hash TEXT PRIMARY KEY,
                    recording_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        logger.debug(f"Cache initialized at: {self.cache_path}")

    def _hash_query(self, query: str, artist: str | None, strict: bool) -> str:
        """Generate hash for search query."""
        import hashlib
        key = f"{query}|{artist or ''}|{strict}"
        return hashlib.md5(key.encode()).hexdigest()

    def _hash_fingerprint(self, fingerprint: str, duration: float) -> str:
        """Generate hash for fingerprint lookup."""
        import hashlib
        key = f"{fingerprint[:100]}|{int(duration)}"
        return hashlib.md5(key.encode()).hexdigest()

    # MusicBrainz Recording Cache
    def get_recording(self, recording_id: str) -> dict | None:
        """Get cached recording metadata."""
        with sqlite3.connect(self.cache_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM musicbrainz_recordings WHERE recording_id = ?",
                (recording_id,)
            )
            row = cursor.fetchone()
            if row:
                logger.debug(f"Cache hit: recording {recording_id}")
                return json.loads(row[0])
        return None

    def set_recording(self, recording_id: str, data: dict) -> None:
        """Cache recording metadata."""
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO musicbrainz_recordings (recording_id, data) VALUES (?, ?)",
                (recording_id, json.dumps(data))
            )
            conn.commit()
        logger.debug(f"Cached recording: {recording_id}")

    # Search Cache
    def get_search_result(self, query: str, artist: str | None, strict: bool) -> str | None:
        """Get cached search result."""
        query_hash = self._hash_query(query, artist, strict)
        with sqlite3.connect(self.cache_path) as conn:
            cursor = conn.execute(
                "SELECT recording_id FROM search_cache WHERE query_hash = ?",
                (query_hash,)
            )
            row = cursor.fetchone()
            if row:
                logger.debug(f"Cache hit: search '{query}'")
                return row[0]
        return None

    def set_search_result(self, query: str, artist: str | None, strict: bool, recording_id: str | None) -> None:
        """Cache search result."""
        query_hash = self._hash_query(query, artist, strict)
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO search_cache (query_hash, recording_id) VALUES (?, ?)",
                (query_hash, recording_id)
            )
            conn.commit()

    # AcoustID Cache
    def get_acoustid_result(self, fingerprint: str, duration: float) -> dict | None:
        """Get cached AcoustID result."""
        fp_hash = self._hash_fingerprint(fingerprint, duration)
        with sqlite3.connect(self.cache_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM acoustid_lookups WHERE fingerprint_hash = ?",
                (fp_hash,)
            )
            row = cursor.fetchone()
            if row:
                logger.debug("Cache hit: AcoustID fingerprint")
                return json.loads(row[0])
        return None

    def set_acoustid_result(self, fingerprint: str, duration: float, data: dict) -> None:
        """Cache AcoustID result."""
        fp_hash = self._hash_fingerprint(fingerprint, duration)
        recording_id = data.get("recording_id") if data else None
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO acoustid_lookups (fingerprint_hash, recording_id, data) VALUES (?, ?, ?)",
                (fp_hash, recording_id, json.dumps(data))
            )
            conn.commit()

    def clear(self) -> None:
        """Clear all cached data."""
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("DELETE FROM musicbrainz_recordings")
            conn.execute("DELETE FROM acoustid_lookups")
            conn.execute("DELETE FROM search_cache")
            conn.commit()
        logger.info("Cache cleared")

    def stats(self) -> dict:
        """Get cache statistics."""
        with sqlite3.connect(self.cache_path) as conn:
            recordings = conn.execute("SELECT COUNT(*) FROM musicbrainz_recordings").fetchone()[0]
            acoustid = conn.execute("SELECT COUNT(*) FROM acoustid_lookups").fetchone()[0]
            searches = conn.execute("SELECT COUNT(*) FROM search_cache").fetchone()[0]
        return {
            "recordings": recordings,
            "acoustid_lookups": acoustid,
            "search_queries": searches,
        }
