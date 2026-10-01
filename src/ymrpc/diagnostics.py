from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .config import Config, config_path


def log_path() -> Path:
    return config_path().with_name("app.log")


def diagnostics_text(config: Config, status: str) -> str:
    safe_config = asdict(config)
    safe_config["discord_client_id"] = "(embedded)"
    lines = [
        f"YandexMusicRPC {__version__}",
        f"Windows: {platform.platform()}",
        f"Python: {platform.python_version()}",
        f"Status: {status}",
        "Config: " + json.dumps(safe_config, ensure_ascii=False, sort_keys=True),
        "",
        "Last log lines:",
    ]
    try:
        tail = log_path().read_text(encoding="utf-8", errors="replace").splitlines()[-100:]
        lines.extend(tail)
    except OSError:
        lines.append("(log unavailable)")
    return "\n".join(lines)


def copy_to_clipboard(text: str) -> None:
    subprocess.run(
        ["clip.exe"],
        input=text,
        text=True,
        check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
