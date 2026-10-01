from __future__ import annotations

import logging
import time
from datetime import timedelta

from .models import PlaybackState, Track

LOGGER = logging.getLogger("YandexMusicRPC.media")


class WindowsMediaProvider:
    """Reads the active Windows Global System Media Transport Controls session."""

    def __init__(self, source_mode: str = "auto") -> None:
        self.source_mode = source_mode
        self._manager = None
        self._last_snapshot: tuple = ()

    async def _get_manager(self):
        if self._manager is None:
            from winsdk.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager,
            )

            self._manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        return self._manager

    async def get_track(self) -> Track | None:
        manager = await self._get_manager()
        sessions = list(manager.get_sessions())
        if not sessions:
            self._log_snapshot(("no-media-sessions",))
            return None

        current = manager.get_current_session()
        preferred = [
            session
            for session in sessions
            if "yandex" in (session.source_app_user_model_id or "").casefold()
            or "яндекс" in (session.source_app_user_model_id or "").casefold()
        ]
        ordered = preferred + ([current] if current and current not in preferred else [])
        ordered += [session for session in sessions if session not in ordered]
        snapshot: list[tuple[str, str, str]] = []

        for session in ordered:
            source = (session.source_app_user_model_id or "").casefold()
            is_browser = any(x in source for x in ("chrome", "msedge", "firefox", "opera", "brave"))
            is_yandex = "yandex" in source or "яндекс" in source
            if self.source_mode == "yandex" and not is_yandex:
                continue
            if self.source_mode == "browser" and not is_browser:
                continue

            props = await session.try_get_media_properties_async()
            playback = session.get_playback_info()
            status_name = str(playback.playback_status).casefold()
            snapshot.append(
                (
                    session.source_app_user_model_id or "unknown",
                    (props.title or "").strip() if props else "",
                    status_name,
                )
            )
            if not props or not (props.title or "").strip():
                continue

            state = _playback_state(playback.playback_status)

            timeline = session.get_timeline_properties()
            position = _seconds(timeline.position)
            duration = max(0, _seconds(timeline.end_time) - _seconds(timeline.start_time))
            track = Track(
                title=(props.title or "").strip(),
                artist=(props.artist or "").strip() or "Неизвестный исполнитель",
                album=(props.album_title or "").strip(),
                state=state,
                position_seconds=position,
                duration_seconds=duration,
                observed_at=time.time(),
                source_app=session.source_app_user_model_id or "",
            )
            self._log_snapshot(tuple(snapshot))
            return track
        self._log_snapshot(tuple(snapshot))
        return None

    def _log_snapshot(self, snapshot: tuple) -> None:
        if snapshot != self._last_snapshot:
            LOGGER.info("Windows media sessions: %r", snapshot)
            self._last_snapshot = snapshot


def _seconds(value: timedelta | object) -> float:
    if hasattr(value, "total_seconds"):
        return float(value.total_seconds())
    # WinRT TimeSpan bindings may expose duration in 100-nanosecond ticks.
    duration = getattr(value, "duration", 0)
    return float(duration) / 10_000_000


def _playback_state(raw_status: object) -> PlaybackState:
    """Normalize WinRT enum bindings that stringify as either names or integers."""
    status_name = str(raw_status).casefold()
    if "playing" in status_name:
        return PlaybackState.PLAYING
    if "paused" in status_name:
        return PlaybackState.PAUSED

    value = getattr(raw_status, "value", raw_status)
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return PlaybackState.STOPPED
    if numeric == 4:
        return PlaybackState.PLAYING
    if numeric == 5:
        return PlaybackState.PAUSED
    return PlaybackState.STOPPED
