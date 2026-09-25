"""One file layout of a government's statutes, measures, or regulations.

The governments themselves live in jurisdiction.py. This module re-exports
them so a state parser can import its parser and its government together.
"""

import enum
from abc import ABC, abstractmethod

from jurisdiction import (
    City,
    Country,
    County,
    Jurisdiction,
    Locality,
    Region,
    State,
    _countries,
    country,
    load_localities,
    subdivision,
)

__all__ = [
    'City', 'Country', 'County', 'Instrument', 'Jurisdiction', 'Locality',
    'Publication', 'Region', 'State', 'country', 'load_localities', 'subdivision',
]


class Instrument(enum.Enum):
    """What an edition contains. The closed set is ours. The codes are ISO's."""

    STATUTE = 'statute'
    MEASURE = 'measure'
    REGULATION = 'regulation'
    RULE = 'rule'
    MANUAL = 'manual'


class Publication(ABC):
    """Parser that yields the plain text of an official publication.

    PDF and HTML are in the way of that text. Prefer plain text or Word, then
    an XML-like file (XML, SGML, CAML) over HTML or PDF of the same code.
    ``sections`` yields those words, not the page.
    """

    instrument = None

    @classmethod
    @abstractmethod
    def accepts(cls, names):
        """True when this path, or the table names inside a zip, is this shape."""

    @abstractmethod
    def sections(self, path):
        """Yield one record per section or measure in the edition."""

    def parallel_sections(self, path, workers=None, chunk_size=400):
        yield from self.sections(path)

    def index(self, indexer, path, workers=None, subdivision=None):
        """Write ``sections()`` into the Whoosh index. An empty edition leaves no index."""
        try:
            from us.states.ca import stamp_subdivision
        except ImportError:
            stamp_subdivision = None

        rows = []
        for row in self.parallel_sections(path, workers=workers):
            row = dict(row)
            if subdivision is not None and not row.get('SUBDIVISION'):
                row['SUBDIVISION'] = subdivision
            if stamp_subdivision is not None and subdivision is not None:
                stamp_subdivision(row, subdivision)
            law_code = getattr(self, 'law_code', None)
            if law_code and not row.get('LAW_CODE'):
                row['LAW_CODE'] = law_code
            heading = getattr(self, 'code_heading', None)
            if heading and not row.get('CODE_HEADING'):
                row['CODE_HEADING'] = heading
            session = getattr(self, 'session', None)
            if session and not row.get('SESSION'):
                row['SESSION'] = str(session)
            if row.get('SECTION_NUM'):
                if not row.get('LAW_CODE'):
                    row['LAW_CODE'] = 'CODE'
                if not row.get('PK') and row.get('SUBDIVISION'):
                    row['PK'] = '%s %s %s' % (
                        row['SUBDIVISION'], row['LAW_CODE'], row['SECTION_NUM'],
                    )
                if not row.get('COUNTRY') and row.get('SUBDIVISION'):
                    row['COUNTRY'] = row['SUBDIVISION'].split('-', 1)[0]
            rows.append(row)
        if not rows:
            return 0
        return indexer.index_pubinfo_laws(path, rows)
