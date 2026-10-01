from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from platformdirs import user_config_dir

DEFAULT_DISCORD_CLIENT_ID = "1555244220007055360"


@dataclass(slots=True)
class Config:
    discord_client_id: str = DEFAULT_DISCORD_CLIENT_ID
    poll_interval_seconds: float = 2.0
    paused_timeout_seconds: int = 300
    autostart: bool = True
    yandex_enrichment: bool = True
    source_mode: str = "auto"
    presence_style: str = "detailed"
    show_button: bool = True
    show_album: bool = False

    @property
    def valid(self) -> bool:
        return self.discord_client_id.isdigit() and len(self.discord_client_id) >= 17


def config_path() -> Path:
    return Path(user_config_dir("YandexMusicRPC", appauthor=False)) / "config.json"


def load_config() -> Config:
    path = config_path()
    if not path.exists():
        return Config()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        allowed = Config.__dataclass_fields__.keys()
        return Config(**{key: value for key, value in raw.items() if key in allowed})
    except (OSError, ValueError, TypeError):
        return Config()


def save_config(config: Config) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
