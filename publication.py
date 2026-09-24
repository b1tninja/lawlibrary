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


class Publication(ABC):
    """Parser for one shape of official publication."""

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
        """Editions join the code index by overriding this. Others are recognized and left alone."""
        return 0
