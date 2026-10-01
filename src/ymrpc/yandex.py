from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .models import Track


@dataclass(slots=True)
class _Metadata:
    cover_url: str | None
    track_url: str | None


class YandexMetadata:
    """Enriches GSMTC metadata through the unofficial anonymous Yandex Music API."""

    def __init__(self) -> None:
        self._client = None
        self._cache: dict[tuple[str, str], _Metadata] = {}

    async def enrich(self, track: Track) -> Track:
        if track.identity in self._cache:
            value = self._cache[track.identity]
            return track.with_metadata(cover_url=value.cover_url, track_url=value.track_url)
        value = await asyncio.to_thread(self._search, track)
        if len(self._cache) >= 500:
            self._cache.pop(next(iter(self._cache)))
        self._cache[track.identity] = value
        return track.with_metadata(cover_url=value.cover_url, track_url=value.track_url)

    def _search(self, track: Track) -> _Metadata:
        try:
            if self._client is None:
                from yandex_music import Client

                self._client = Client().init()
            result = self._client.search(f"{track.artist} {track.title}", type_="track")
            candidates = (result.tracks.results if result and result.tracks else [])[:10]
            ranked = sorted(
                ((_match_score(track, item), item) for item in candidates),
                key=lambda pair: pair[0],
                reverse=True,
            )
            if not ranked or ranked[0][0] < 0.55:
                return _Metadata(None, None)
            best = ranked[0][1]
            cover_uri = best.cover_uri or (best.albums[0].cover_uri if best.albums else None)
            cover = f"https://{cover_uri.replace('%%', '400x400')}" if cover_uri else None
            album_id = best.albums[0].id if best.albums else None
            url = (
                f"https://music.yandex.ru/album/{album_id}/track/{best.id}"
                if album_id
                else f"https://music.yandex.ru/track/{best.id}"
            )
            return _Metadata(cover, url)
        except Exception:
            return _Metadata(None, None)


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE))


def _match_score(track: Track, candidate: object) -> float:
    title = _normalize(str(getattr(candidate, "title", "")))
    artists_method = getattr(candidate, "artists_name", None)
    artists = ", ".join(artists_method()) if callable(artists_method) else ""
    title_score = SequenceMatcher(None, _normalize(track.title), title).ratio()
    artist_score = SequenceMatcher(None, _normalize(track.artist), _normalize(artists)).ratio()
    return title_score * 0.75 + artist_score * 0.25
