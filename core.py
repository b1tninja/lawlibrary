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
import re
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
    """The flat index: every edition in one Whoosh directory, one writer."""
    return data_dir() / "idx"


def shelf_dir() -> Path:
    """The shelf: one Whoosh index per edition, ``shelf/<year>/``, each with
    its own needle store and code list. Editions build at once, in their own
    processes, and are read together as one index by ``open_index``."""
    return data_dir() / "shelf"


EDITION_MARK = "edition.json"
_EDITION = re.compile(r"^\d{4}$")


def _flat_exists(path) -> bool:
    from whoosh import index
    return index.exists_in(str(path))


def editions(root=None) -> list:
    """The complete editions under ``root``, oldest first.

    An edition is a four-digit directory holding an index and the mark its
    build wrote last (``EDITION_MARK``); a directory still building has no
    mark and is not read. A flat index has no editions.
    """
    root = Path(root) if root is not None else shelf_dir()
    if not root.is_dir():
        return []
    found = [
        child for child in root.iterdir()
        if child.is_dir() and _EDITION.match(child.name)
        and (child / EDITION_MARK).is_file() and _flat_exists(child)
    ]
    return sorted(found)


def index_root() -> Path:
    """Where a reader looks: the shelf once it holds an edition, else the flat index."""
    return shelf_dir() if editions(shelf_dir()) else index_dir()


def index_ready(path=None) -> bool:
    """Whether there is an index to read at ``path``: a shelf with an edition, or a flat one."""
    path = Path(path) if path is not None else index_root()
    return bool(editions(path)) or (path.is_dir() and _flat_exists(path))


def newest_edition(path=None):
    """The newest edition directory under ``path``, or None for a flat index."""
    found = editions(path if path is not None else index_root())
    return found[-1] if found else None


class Shelf:
    """Several editions read as one index.

    Whoosh's own reader over a multi-segment index is a ``MultiReader`` of
    segment readers; the shelf is the same shape one level up, with each
    edition's segments laid end to end. A searcher over it answers every
    question a flat index does — search, stored fields, lexicon, postings —
    and its generation changes when any edition's does.
    """

    def __init__(self, root, parts):
        self.root = str(root)
        self.parts = parts  # [(edition name, whoosh Index)], oldest first

    @property
    def schema(self):
        return self.parts[-1][1].schema

    @property
    def storage(self):
        return self.parts[-1][1].storage

    @property
    def sessions(self):
        return [name for name, _ix in self.parts]

    def latest_generation(self):
        import zlib
        words = ';'.join('%s:%d' % (name, ix.latest_generation()) for name, ix in self.parts)
        return zlib.crc32(words.encode('utf-8'))

    def doc_count(self):
        return sum(ix.doc_count() for _name, ix in self.parts)

    def doc_count_all(self):
        return sum(ix.doc_count_all() for _name, ix in self.parts)

    def reader(self):
        from whoosh.reading import MultiReader
        leaves = []
        for _name, ix in self.parts:
            reader = ix.reader()
            # Lay the segments flat: a searcher splits only one level down.
            leaves.extend(reader.readers if isinstance(reader, MultiReader) else [reader])
        if len(leaves) == 1:
            return leaves[0]
        return MultiReader(leaves, generation=self.latest_generation())

    def searcher(self, **kwargs):
        from whoosh.searching import Searcher
        return Searcher(self.reader(), **kwargs)

    def close(self):
        for _name, ix in self.parts:
            ix.close()


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

    ``path`` may be a flat index or a shelf root (see ``shelf_dir``); with
    none given, ``index_root`` decides. A shelf comes back as a ``Shelf``.
    """
    root = Path(path) if path is not None else index_root()
    parts = editions(root)
    if parts:
        return Shelf(root, [(part.name, _open_flat(part)) for part in parts])
    return _open_flat(root)


def _open_flat(path):
    from whoosh.filedb.filestore import FileStorage
    return FileStorage(str(path), supports_mmap=False, readonly=True).open_index()


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
