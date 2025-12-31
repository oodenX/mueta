# tests/test_cache.py
"""Unit tests for cache module."""

import pytest
from pathlib import Path
from mueta.engine.cache import MetadataCache
from mueta.engine.models import AudioMetadata


def test_metadata_cache_init(tmp_path):
    """Test cache initialization."""
    cache_db = tmp_path / "test_cache.db"
    cache = MetadataCache(str(cache_db))
    assert cache_db.exists()


def test_cache_recording_storage(tmp_path):
    """Test storing and retrieving recordings."""
    cache = MetadataCache(str(tmp_path / "test_cache.db"))

    test_data = {
        "title": "Test Song",
        "artist": "Test Artist",
        "album": "Test Album"
    }

    cache.set_recording("test-mbid-123", test_data)
    result = cache.get_recording("test-mbid-123")

    assert result is not None
    assert result["title"] == "Test Song"
    assert result["artist"] == "Test Artist"


def test_cache_search_results(tmp_path):
    """Test caching search results."""
    cache = MetadataCache(str(tmp_path / "test_cache.db"))

    key = cache.get_search_key("test query", "test artist", True)
    cache.set_search_result(key, "result-mbid-456")

    result = cache.get_search_result(key)
    assert result == "result-mbid-456"


def test_cache_miss(tmp_path):
    """Test cache miss returns None."""
    cache = MetadataCache(str(tmp_path / "test_cache.db"))

    result = cache.get_recording("nonexistent-mbid")
    assert result is None
