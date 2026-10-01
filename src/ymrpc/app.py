from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
import time
import webbrowser
from logging.handlers import RotatingFileHandler

import pystray
from PIL import Image, ImageDraw

from .autostart import set_autostart
from .config import Config, config_path, load_config, save_config
from .diagnostics import copy_to_clipboard, diagnostics_text, log_path
from .discord_rpc import DiscordRPC
from .instance import SingleInstance
from .media import WindowsMediaProvider
from .models import PlaybackState, Track
from .settings import show_settings
from .yandex import YandexMetadata

APP_NAME = "YandexMusicRPC"
LOGGER = logging.getLogger(APP_NAME)


class Application:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.stop_event = threading.Event()
        self.force_refresh = threading.Event()
        self.status = "Запуск…"
        self.last_track: Track | None = None
        self.last_seen_at = 0.0
        self.paused_since: float | None = None
        self.rpc = DiscordRPC(config.discord_client_id)
        self.provider = WindowsMediaProvider(config.source_mode)
        self.metadata = YandexMetadata()
        self.icon = pystray.Icon(APP_NAME, _tray_image(), APP_NAME, self._menu())

    def _menu(self):
        return pystray.Menu(
            pystray.MenuItem(lambda _: self.status, None, enabled=False),
            pystray.MenuItem("Открыть Яндекс Музыку", self._open_music),
            pystray.MenuItem(
                "Запускать вместе с Windows",
                self._toggle_autostart,
                checked=lambda _: self.config.autostart,
            ),
            pystray.MenuItem("Настройки…", self._open_settings),
            pystray.MenuItem("Скопировать диагностику", self._copy_diagnostics),
            pystray.MenuItem("Открыть папку журнала", self._open_log_folder),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Выход", self._quit),
        )

    def run(self) -> None:
        set_autostart(self.config.autostart)
        thread = threading.Thread(target=lambda: asyncio.run(self._worker()), daemon=True)
        thread.start()
        self.icon.run()
        thread.join(timeout=5)

    async def _worker(self) -> None:
        last_sent: tuple | None = None
        try:
            while not self.stop_event.is_set():
                try:
                    self.provider.source_mode = self.config.source_mode
                    if self.force_refresh.is_set():
                        self.force_refresh.clear()
                        last_sent = None
                        await self.rpc.clear()
                    track = await self.provider.get_track()
                    now = time.time()
                    if track and self.config.yandex_enrichment:
                        track = await self.metadata.enrich(track)

                    if not track:
                        if self.last_track and now - self.last_seen_at < 8:
                            self._set_status("Медиасессия обновляется…")
                        else:
                            await self._clear()
                            last_sent = None
                    elif track.state == PlaybackState.STOPPED:
                        await self._clear()
                        last_sent = None
                    elif track.state == PlaybackState.PAUSED:
                        self.last_seen_at = now
                        self.paused_since = self.paused_since or now
                        if now - self.paused_since >= self.config.paused_timeout_seconds:
                            await self._clear()
                            last_sent = None
                        else:
                            signature = (
                                *track.identity,
                                track.state,
                                self.config.presence_style,
                                self.config.show_button,
                                self.config.show_album,
                            )
                            if signature != last_sent:
                                await self._update_rpc(track)
                                last_sent = signature
                            self._set_status(f"Пауза: {track.artist} — {track.title}")
                    else:
                        self.last_seen_at = now
                        self.paused_since = None
                        signature = (
                            *track.identity,
                            track.state,
                            self.config.presence_style,
                            self.config.show_button,
                            self.config.show_album,
                        )
                        if signature != last_sent:
                            await self._update_rpc(track)
                            last_sent = signature
                        self.last_track = track
                        self._set_status(f"{track.artist} — {track.title}")
                except Exception:
                    LOGGER.exception("Worker error")
                    self._set_status("Ожидание Discord или плеера…")
                    await self.rpc.close()
                    last_sent = None
                await asyncio.sleep(self.config.poll_interval_seconds)
        finally:
            await self.rpc.clear()
            await self.rpc.close()

    async def _update_rpc(self, track: Track) -> None:
        await self.rpc.update(
            track,
            style=self.config.presence_style,
            show_button=self.config.show_button,
            show_album=self.config.show_album,
        )

    async def _clear(self) -> None:
        await self.rpc.clear()
        self.paused_since = None
        self._set_status("Музыка не играет")

    def _set_status(self, status: str) -> None:
        if self.status != status:
            self.status = status
            self.icon.update_menu()

    def _open_music(self, *_args) -> None:
        url = self.last_track.track_url if self.last_track else "https://music.yandex.ru/"
        webbrowser.open(url)

    def _toggle_autostart(self, *_args) -> None:
        self.config.autostart = not self.config.autostart
        save_config(self.config)
        set_autostart(self.config.autostart)
        self.icon.update_menu()

    def _open_settings(self, *_args) -> None:
        if show_settings(self.config):
            set_autostart(self.config.autostart)
            self.force_refresh.set()
            self.icon.update_menu()

    def _copy_diagnostics(self, *_args) -> None:
        try:
            copy_to_clipboard(diagnostics_text(self.config, self.status))
            self.icon.notify("Диагностика скопирована в буфер обмена.", APP_NAME)
        except Exception:
            LOGGER.exception("Could not copy diagnostics")

    def _open_log_folder(self, *_args) -> None:
        config_path().parent.mkdir(parents=True, exist_ok=True)
        os.startfile(config_path().parent)  # type: ignore[attr-defined]

    def _quit(self, *_args) -> None:
        self.stop_event.set()
        self.icon.stop()


def _tray_image() -> Image.Image:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((3, 3, 61, 61), fill=(255, 204, 0, 255))
    draw.ellipse((23, 17, 31, 39), fill=(24, 24, 24, 255))
    draw.ellipse((37, 13, 45, 35), fill=(24, 24, 24, 255))
    draw.polygon([(30, 17), (42, 13), (42, 20), (30, 24)], fill=(24, 24, 24, 255))
    draw.ellipse((17, 35, 31, 47), fill=(24, 24, 24, 255))
    draw.ellipse((31, 31, 45, 43), fill=(24, 24, 24, 255))
    return image


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("YandexMusicRPC поддерживает Windows 10/11.")
    instance = SingleInstance()
    if instance.already_running:
        return
    config_path().parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_path(),
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)
    config = load_config()
    try:
        if config.valid:
            Application(config).run()
    finally:
        instance.close()


if __name__ == "__main__":
    main()
