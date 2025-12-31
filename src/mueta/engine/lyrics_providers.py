# src/mueta/engine/lyrics_providers.py
"""Lyrics providers implementation."""

import abc
import re
from typing import ClassVar

import httpx
from loguru import logger

from mueta.engine.models import LyricsResult


class LyricsProvider(abc.ABC):
    """Base class for lyrics providers."""

    NAME: ClassVar[str] = "base"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.client = httpx.Client(timeout=10.0, follow_redirects=True)

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    @abc.abstractmethod
    def get_lyrics(
        self,
        artist: str,
        track: str,
        album: str | None = None,
        duration: float | None = None,
    ) -> LyricsResult | None:
        """Get lyrics for a track."""
        pass


class LRCLIBProvider(LyricsProvider):
    """Provider for LRCLIB."""

    NAME = "LRCLIB"
    BASE_URL = "https://lrclib.net/api"

    def get_lyrics(
        self,
        artist: str,
        track: str,
        album: str | None = None,
        duration: float | None = None,
    ) -> LyricsResult | None:
        # Code adapted from original LyricsService
        params = {"artist_name": artist, "track_name": track}
        if album:
            params["album_name"] = album
        if duration:
            params["duration"] = str(int(duration))

        try:
            # 1. Try exact match
            response = self.client.get(f"{self.BASE_URL}/get", params=params)
            if response.status_code == 200:
                data = response.json()
                return self._parse_result(data)

            # 2. Fallback to search
            return self._search_fallback(artist, track, duration)

        except httpx.HTTPError as e:
            logger.warning(f"LRCLIB error: {e}")
            return self._search_fallback(artist, track, duration)

    def _search_fallback(self, artist: str, track: str, duration: float | None) -> LyricsResult | None:
        try:
            response = self.client.get(
                f"{self.BASE_URL}/search",
                params={"q": track, "limit": 10},
            )
            response.raise_for_status()
            results = [self._parse_result(item) for item in response.json()]
            return self._find_best_match(results, artist, track, duration)
        except Exception as e:
            logger.warning(f"LRCLIB search error: {e}")
            return None

    def _parse_result(self, data: dict) -> LyricsResult:
        return LyricsResult(
            id=str(data["id"]),
            track_name=data["trackName"],
            artist_name=data["artistName"],
            album_name=data.get("albumName"),
            duration=data.get("duration"),
            instrumental=data.get("instrumental", False),
            plain_lyrics=data.get("plainLyrics"),
            synced_lyrics=data.get("syncedLyrics"),
        )

    def _find_best_match(
        self,
        results: list[LyricsResult],
        artist: str,
        track: str,
        duration: float | None
    ) -> LyricsResult | None:
        best_match = None
        best_score = 0

        for result in results:
            score = 0
            if artist.lower() in result.artist_name.lower() or result.artist_name.lower() in artist.lower():
                score += 100
            if track.lower() in result.track_name.lower():
                score += 50
            if result.synced_lyrics:
                score += 20
            if duration and result.duration:
                if abs(duration - result.duration) < 5:
                    score += 10

            if score > best_score:
                best_score = score
                best_match = result

        return best_match if best_score >= 30 else None


class NetEaseProvider(LyricsProvider):
    """Provider for NetEase Cloud Music."""

    NAME = "NetEase"
    SEARCH_URL = "http://music.163.com/api/search/get/web"
    LYRIC_URL = "http://music.163.com/api/song/lyric"
    HEADERS = {
        "Referer": "http://music.163.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": "appver=1.5.0.75771",
    }

    def get_lyrics(
        self,
        artist: str,
        track: str,
        album: str | None = None,
        duration: float | None = None,
    ) -> LyricsResult | None:
        try:
            # 1. Search for song
            search_query = f"{track} {artist}"
            params = {
                "s": search_query,
                "type": 1,
                "offset": 0,
                "total": "true",
                "limit": 5,
            }
            response = self.client.post(self.SEARCH_URL, data=params, headers=self.HEADERS)
            response.raise_for_status()
            data = response.json()

            songs = data.get("result", {}).get("songs", [])
            if not songs:
                return None

            # 2. Pick best song match (simple check)
            best_song_id = None
            for song in songs:
                # Basic check: artist name match
                song_artists = [a["name"].lower() for a in song.get("artists", [])]
                if any(art in artist.lower() for art in song_artists) or artist.lower() in str(song_artists):
                    best_song_id = song["id"]
                    break

            if not best_song_id and songs:
                best_song_id = songs[0]["id"]

            if not best_song_id:
                return None

            # 3. Get lyrics
            lyric_response = self.client.get(
                self.LYRIC_URL,
                params={"id": best_song_id, "lv": 1, "kv": 1, "tv": -1},
                headers=self.HEADERS,
            )
            lyric_response.raise_for_status()
            lyric_data = lyric_response.json()

            lrc = lyric_data.get("lrc", {}).get("lyric")
            tlyric = lyric_data.get("tlyric", {}).get("lyric")  # Translated lyrics

            if not lrc:
                return None

            # If translated lyrics exist, maybe append them? For now just use original.

            return LyricsResult(
                id=str(best_song_id),
                track_name=track,
                artist_name=artist,
                synced_lyrics=lrc,
                plain_lyrics=lrc,  # NetEase usually has synced, assume it can serve as plain
            )

        except Exception as e:
            logger.warning(f"NetEase error: {e}")
            return None


class QQMusicProvider(LyricsProvider):
    """Provider for QQ Music (unofficial API)."""

    NAME = "QQMusic"
    SEARCH_URL = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
    LYRIC_URL = "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
    HEADERS = {
        "Referer": "https://y.qq.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    def get_lyrics(
        self,
        artist: str,
        track: str,
        album: str | None = None,
        duration: float | None = None,
    ) -> LyricsResult | None:
        try:
            # 1. Search for song
            search_query = f"{track} {artist}"
            params = {
                "w": search_query,
                "format": "json",
                "p": 1,
                "n": 5,
                "ct": 24,
                "qqmusic_ver": 1298,
                "new_json": 1,
                "remoteplace": "txt.yqq.song",
            }
            response = self.client.get(self.SEARCH_URL, params=params, headers=self.HEADERS)
            response.raise_for_status()
            data = response.json()

            songs = data.get("data", {}).get("song", {}).get("list", [])
            if not songs:
                return None

            # 2. Pick best song match
            best_song = None
            for song in songs:
                song_artists = [s.get("name", "").lower() for s in song.get("singer", [])]
                if any(art in artist.lower() for art in song_artists) or artist.lower() in str(song_artists):
                    best_song = song
                    break

            if not best_song and songs:
                best_song = songs[0]

            if not best_song:
                return None

            songmid = best_song.get("mid")
            if not songmid:
                return None

            # 3. Get lyrics
            lyric_params = {
                "songmid": songmid,
                "g_tk": 5381,
                "format": "json",
                "nobase64": 1,
            }
            lyric_response = self.client.get(
                self.LYRIC_URL,
                params=lyric_params,
                headers=self.HEADERS,
            )
            lyric_response.raise_for_status()
            lyric_data = lyric_response.json()

            lrc = lyric_data.get("lyric", "")
            if not lrc:
                return None

            # Clean up potential HTML entities
            import html
            lrc = html.unescape(lrc)

            return LyricsResult(
                id=songmid,
                track_name=best_song.get("name", track),
                artist_name=", ".join(s.get("name", "") for s in best_song.get("singer", [])) or artist,
                synced_lyrics=lrc,
                plain_lyrics=lrc,
            )

        except Exception as e:
            logger.warning(f"QQMusic error: {e}")
            return None


class GeniusProvider(LyricsProvider):
    """Provider for Genius."""

    NAME = "Genius"
    BASE_URL = "https://api.genius.com"

    def get_lyrics(
        self,
        artist: str,
        track: str,
        album: str | None = None,
        duration: float | None = None,
    ) -> LyricsResult | None:
        if not self.api_key:
            return None

        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            # 1. Search
            response = self.client.get(
                f"{self.BASE_URL}/search",
                params={"q": f"{track} {artist}"},
                headers=headers,
            )
            response.raise_for_status()
            hits = response.json().get("response", {}).get("hits", [])

            if not hits:
                return None

            # 2. Pick best match
            best_hit = None
            for hit in hits:
                result = hit["result"]
                primary_artist = result["primary_artist"]["name"]

                # Check artist match
                if artist.lower() in primary_artist.lower() or primary_artist.lower() in artist.lower():
                    best_hit = result
                    break

            if not best_hit and hits:
                best_hit = hits[0]["result"]

            if not best_hit:
                return None

            # 3. Scrape lyrics from page URL
            page_url = best_hit["url"]
            lyrics_text = self._scrape_lyrics(page_url)

            if not lyrics_text:
                return None

            return LyricsResult(
                id=str(best_hit["id"]),
                track_name=best_hit["title"],
                artist_name=best_hit["primary_artist"]["name"],
                plain_lyrics=lyrics_text,
                synced_lyrics=None,  # Genius is usually plain text
            )

        except Exception as e:
            logger.warning(f"Genius error: {e}")
            return None

    def _scrape_lyrics(self, url: str) -> str | None:
        try:
            response = self.client.get(url)
            response.raise_for_status()
            html = response.text

            # Experimental Regex scraping for Genius
            # Look for containers with data-lyrics-container
            # This is fragile and might break if Genius changes themes

            # Strategy: Find all substrings between <br> tags in lyrics containers?
            # Or simpler: Try to extract everything in the lyrics containers and strip tags.

            # Regex to find content inside data-lyrics-container="true" div
            # Note: This is very rough
            pattern = re.compile(r'<div[^>]*data-lyrics-container="true"[^>]*>(.*?)</div>', re.DOTALL)
            matches = pattern.findall(html)

            if not matches:
                # Fallback: older Genius layout often used class="lyrics"
                pattern_old = re.compile(r'<div class="lyrics"[^>]*>(.*?)</div>', re.DOTALL)
                matches = pattern_old.findall(html)

            if not matches:
                return None

            full_lyrics = "\n".join(matches)

            # Clean up HTML tags
            # Replace <br> with newlines
            full_lyrics = re.sub(r'<br\s*/?>', '\n', full_lyrics)
            # Remove other tags
            full_lyrics = re.sub(r'<[^>]+>', '', full_lyrics)
            # Fix entities
            full_lyrics = full_lyrics.replace('&amp;', '&').replace('&quot;', '"').replace('&#x27;', "'")

            return full_lyrics.strip()

        except Exception as e:
            logger.warning(f"Genius scraping error: {e}")
            return None
