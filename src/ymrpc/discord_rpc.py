from __future__ import annotations

import logging
import time
from urllib.parse import quote_plus

from .models import PlaybackState, Track

LOGGER = logging.getLogger("YandexMusicRPC.discord")
DISPLAY_NAME = "Яндекс Музыку"


def presence_payload(
    track: Track,
    now: float | None = None,
    *,
    style: str = "detailed",
    show_button: bool = True,
    show_album: bool = False,
) -> dict:
    now = now or time.time()
    position = track.current_position(now)
    track_url = track.track_url or (
        "https://music.yandex.ru/search?text=" + quote_plus(f"{track.artist} {track.title}")
    )
    details = track.title
    state = track.artist
    cover_url = track.cover_url
    if show_album and track.album:
        state = f"{track.artist} • {track.album}"
    if style == "minimal":
        cover_url = None
    elif style == "private":
        details = "Слушает музыку"
        state = "Яндекс Музыка"
        cover_url = None

    payload: dict = {
        "activity_type": 2,
        "status_display_type": 2,
        "name": DISPLAY_NAME,
        "details": _limit(details),
        "details_url": track_url,
        "state": _limit(state),
        "large_text": _limit(track.album or "Яндекс Музыка"),
        "large_url": track_url,
    }
    if show_button and style != "private":
        payload["buttons"] = [{"label": "Открыть трек", "url": track_url}]
    if cover_url:
        payload["large_image"] = cover_url

    if track.state == PlaybackState.PLAYING and track.duration_seconds > 0:
        payload["start"] = int(now - position)
        payload["end"] = int(now + max(0, track.duration_seconds - position))
    elif track.state == PlaybackState.PAUSED and style != "private":
        payload["state"] = _limit(f"{track.artist} • На паузе")
    return payload


def _limit(value: str, maximum: int = 128) -> str:
    value = " ".join(value.split())
    return value[:maximum] or "Яндекс Музыка"


class DiscordRPC:
    def __init__(self, client_id: str) -> None:
        self.client_id = client_id
        self._rpc = None

    async def update(
        self,
        track: Track,
        *,
        style: str = "detailed",
        show_button: bool = True,
        show_album: bool = False,
    ) -> None:
        await self._ensure_connected()
        try:
            await self._rpc.update(
                **presence_payload(
                    track,
                    style=style,
                    show_button=show_button,
                    show_album=show_album,
                )
            )
            LOGGER.info(
                "Discord presence updated: %s — %s (style=%s, button=%s, album=%s)",
                track.artist,
                track.title,
                style,
                show_button,
                show_album,
            )
        except Exception:
            await self.close()
            raise

    async def clear(self) -> None:
        if self._rpc:
            try:
                await self._rpc.clear()
            except Exception:
                await self.close()

    async def _ensure_connected(self) -> None:
        if self._rpc:
            return
        from pypresence import AioPresence

        self._rpc = AioPresence(self.client_id)
        await self._rpc.connect()
        LOGGER.info("Connected to Discord IPC")

    async def close(self) -> None:
        if self._rpc:
            try:
                writer = getattr(self._rpc, "sock_writer", None)
                if writer:
                    writer.close()
                    wait_closed = getattr(writer, "wait_closed", None)
                    if wait_closed:
                        await wait_closed()
            except Exception:
                pass
            self._rpc = None
