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


def open_index(path=None):
    """The index for reading, through the file and not through a copy of it.

    ``whoosh.index.open_dir`` maps each compound segment file and then, when
    a file inside it is opened, copies that mapping into memory (a
    ``BytesIO`` over the buffer). Every searcher paid for a copy of the
    postings: 1.5 seconds and gigabytes per open on the full index, on every
    request, and thirty-two readers at once exhausted the machine. Read
    through the file instead and a searcher opens in milliseconds; the
    drive and the page cache serve the seeks, and stored fields come back
    faster too. A writer keeps ``open_dir``: this storage is read-only.
    """
    from whoosh.filedb.filestore import FileStorage
    return FileStorage(str(path or index_dir()), supports_mmap=False, readonly=True).open_index()


def within(query, constraint):
    """``query`` limited to ``constraint``, in place of ``filter=``.

    Whoosh turns a filter into the set of every document it matches before
    the search starts. For a session's constraint that is a walk of four
    million postings, 1.3 to 4.6 seconds, on every lookup. Put the
    constraint inside the query instead and the intersection is read
    posting by posting: twenty milliseconds. Its terms are given no weight,
    so the rank stays the query's own. (Whoosh's ``Require``, which promises
    exactly this, returns documents outside the constraint in 2.7.4.)
    """
    if constraint is None:
        return query
    from whoosh.query import And
    return And([query, Silent(constraint)])


def _silent_query():
    """The wrapper classes, made once Whoosh is wanted and not at import."""
    from whoosh.matching.wrappers import WrappingMatcher
    from whoosh.query.wrappers import WrappingQuery

    class SilentMatcher(WrappingMatcher):
        """The child's documents, each scoring nothing.

        A boost of zero would do, but Whoosh divides by the boost when it
        skips by block quality. Saying instead that this matcher has no
        block quality keeps the intersection on the plain path: every match
        is read, and each is scored by the query alone.
        """

        def _replacement(self, newchild):
            return self.__class__(newchild)

        def score(self):
            return 0.0

        def weight(self):
            return 0.0

        def supports_block_quality(self):
            return False

    class Silent(WrappingQuery):
        """Matches what its child matches and scores none of it."""

        def _rewrap(self, child):
            return self.__class__(child)

        def matcher(self, searcher, context=None):
            return SilentMatcher(self.child.matcher(searcher, context))

    return Silent


class _Lazy:
    def __call__(self, constraint):
        global Silent
        Silent = _silent_query()
        return Silent(constraint)


Silent = _Lazy()


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
