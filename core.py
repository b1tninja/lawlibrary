"""Runtime paths. Call these; do not remember a path from import time.

Resolution order for the publication archive:

1. ``LAWLIBRARY_DATA`` in the process environment, then the older name
   ``MOUNT_DIRECTORY``.
2. ``LAWLIBRARY_DATA`` in the ``.env`` file next to this module.
3. The platform data directory: ``%LOCALAPPDATA%\\lawlibrary`` on Windows,
   ``~/Library/Application Support/lawlibrary`` on macOS, and
   ``$XDG_DATA_HOME/lawlibrary`` or ``~/.local/share/lawlibrary`` elsewhere.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def package_root() -> Path:
    return Path(__file__).resolve().parent


def platform_data_dir() -> Path:
    """Where this operating system keeps an application's local data."""
    name = "lawlibrary"
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / name
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / name
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / name


def data_dir(environ: os._Environ[str] | dict[str, str] | None = None, dotenv_path: Path | None = None) -> Path:
    """Archive root. Environment, then ``.env``, then the platform directory."""
    env = os.environ if environ is None else environ
    chosen = env.get("LAWLIBRARY_DATA") or env.get("MOUNT_DIRECTORY")
    if chosen:
        return Path(chosen).expanduser().resolve()
    file_path = package_root() / ".env" if dotenv_path is None else dotenv_path
    from_file = _dotenv_value(file_path, "LAWLIBRARY_DATA")
    if from_file:
        return Path(from_file).expanduser().resolve()
    return platform_data_dir()


def index_dir() -> Path:
    return data_dir() / "idx"


def codes_dir() -> Path:
    return data_dir() / "codes"


def ensure_dir(path: Path | str) -> Path:
    destination = Path(path)
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def _dotenv_value(path: Path, key: str) -> str:
    if not path.is_file():
        return ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        return value
    return ""
