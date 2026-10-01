from __future__ import annotations

import time
from dataclasses import dataclass, replace
from enum import Enum


class PlaybackState(str, Enum):
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class Track:
    title: str
    artist: str
    album: str = ""
    state: PlaybackState = PlaybackState.STOPPED
    position_seconds: float = 0
    duration_seconds: float = 0
    observed_at: float = 0
    cover_url: str | None = None
    track_url: str | None = None
    source_app: str = ""

    @property
    def identity(self) -> tuple[str, str]:
        return self.title.casefold().strip(), self.artist.casefold().strip()

    def current_position(self, now: float | None = None) -> float:
        if self.state != PlaybackState.PLAYING:
            return max(0, self.position_seconds)
        elapsed = (now or time.time()) - self.observed_at
        return max(0, min(self.duration_seconds or float("inf"), self.position_seconds + elapsed))

    def with_metadata(self, *, cover_url: str | None, track_url: str | None) -> Track:
        return replace(self, cover_url=cover_url, track_url=track_url)
