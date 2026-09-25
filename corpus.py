"""One SQLite file per government's complete published code.

The file is the plain text of that publication. Open it when a query names
that government. A second government is a second file. Federal law, a state
code, a canton, a county, and a city each keep their own file.
"""

import os
import re
import sqlite3

from core import codes_dir


def _root(root):
    return str(codes_dir()) if root is None else root

_SCHEMA = """
CREATE TABLE IF NOT EXISTS publication (
    session TEXT,
    source TEXT,
    instrument TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS section (
    pk TEXT PRIMARY KEY,
    law_code TEXT,
    section_num TEXT,
    legal_text TEXT,
    citation TEXT,
    session TEXT
);
"""


def _slug(name):
    return str(name).strip().lower().replace(' ', '-')


def corpus_path(country, subdivision=None, locality=(), session=None, root=None):
    """Path of the complete code for one government.

    ``US`` is the federal code. ``US-CA`` is California's codes. A session
    year is an older publication of that same government. ``locality`` is the
    chain under the region, outer to inner (county, then city).
    """
    country = str(country).upper()
    parts = [_root(root)]
    if subdivision:
        parts.append(str(subdivision).upper())
    else:
        parts.append(country)
    for name in locality:
        parts.append(_slug(name))
    if session not in (None, 'current'):
        parts.append('sessions')
        parts.append(str(session))
    leaf = parts[-1] + '.sqlite'
    return os.path.join(*parts[:-1], leaf)


def corpus_path_for(place, session=None, root=None):
    """Path for a Country, Region, State, County, or City class."""
    from jurisdiction import Locality

    if issubclass(place, Locality):
        chain = []
        current = place
        while issubclass(current, Locality):
            chain.append(current.name)
            parent = current.parent
            if not isinstance(parent, type):
                break
            current = parent
        chain.reverse()
        return corpus_path(place.region().split('-', 1)[0], place.region(), chain, session, root)
    code = getattr(place, 'code', None)
    if code and '-' in str(code):
        return corpus_path(str(code).split('-', 1)[0], code, session=session, root=root)
    return corpus_path(code, session=session, root=root)


def cfr_corpus_path(title, root=None):
    """One SQLite file per CFR title: ``data/codes/US/cfr/{title}.sqlite``.

    Not mixed with the United States Code (``US.sqlite``) or a state file
    such as ``US-CA.sqlite``.
    """
    return os.path.join(_root(root), 'US', 'cfr', '%s.sqlite' % str(title).strip())


def manual_corpus_path(book, root=None):
    """One SQLite file per official manual: ``data/codes/US/manuals/{book}.sqlite``."""
    return os.path.join(_root(root), 'US', 'manuals', '%s.sqlite' % str(book).strip().upper())


def statute_corpus_path(subdivision, law_code, root=None):
    """One file for a code of law inside a region: ``US-CA/statutes/CIV.sqlite``."""
    return os.path.join(
        _root(root), str(subdivision).upper(), 'statutes', '%s.sqlite' % str(law_code).strip().upper(),
    )


def connect(path):
    """Open one corpus, creating its tables when the file is new."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript(_SCHEMA)
    return db


_ALIAS = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def alias_for(*parts):
    """SQL schema name for a regional, political, or statutory file."""
    raw = '_'.join(str(part) for part in parts if part not in (None, ''))
    alias = re.sub(r'[^A-Za-z0-9]+', '_', raw).strip('_').lower()
    if not _ALIAS.match(alias) or alias in ('main', 'temp'):
        raise ValueError('schema alias %r' % alias)
    return alias


class Catalog:
    """A query connection with independent corpus files attached by name.

    The connection itself holds no sections. Each ``ATTACH`` adds one file
    under its own schema. Every file has the same ``section`` table.
    """

    def __init__(self):
        self.db = sqlite3.connect(':memory:')
        self.names = {}

    def attach(self, path, alias):
        """Attach an existing file. A missing file stays detached."""
        if not _ALIAS.match(alias) or alias in ('main', 'temp'):
            raise ValueError('schema alias %r' % alias)
        if alias in self.names:
            return alias
        if not os.path.isfile(path):
            return None
        quoted = os.path.abspath(path).replace("'", "''")
        self.db.execute("ATTACH DATABASE '%s' AS %s" % (quoted, alias))
        self.names[alias] = path
        return alias

    def attach_region(self, code, root=None):
        country = str(code).split('-', 1)[0]
        return self.attach(corpus_path(country, code, root=root), alias_for(code))

    def attach_cfr(self, title, root=None):
        return self.attach(cfr_corpus_path(title, root=root), alias_for('cfr', title))

    def attach_statute(self, subdivision, law_code, root=None):
        return self.attach(
            statute_corpus_path(subdivision, law_code, root=root),
            alias_for(subdivision, law_code),
        )

    def sections(self, aliases=None):
        """Rows from the attached schemas, each tagged with its schema name."""
        names = [name for name in (aliases or self.names) if name in self.names]
        if not names:
            return []
        sql = ' UNION ALL '.join(
            "SELECT '%s' AS corpus, law_code, section_num, legal_text, citation FROM %s.section" % (name, name)
            for name in names
        )
        return self.db.execute(sql).fetchall()

    def close(self):
        self.db.close()
