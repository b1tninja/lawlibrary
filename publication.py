"""A publication is one official edition of a state's law.

A state names the distribution point and the edition parsers it knows.
An edition subclass accepts a year when that year's files are shaped differently.
"""

import os
import os.path
import zipfile
from abc import ABC, abstractmethod


def table_names(path):
    with zipfile.ZipFile(path) as zf:
        return {os.path.splitext(os.path.basename(info.filename))[0]
                for info in zf.infolist()
                if os.path.splitext(info.filename)[1] == '.dat'}


class Publication(ABC):
    """Parser for one shape of official publication."""

    @classmethod
    @abstractmethod
    def accepts(cls, names):
        """True when the .dat tables in this zip are the shape this parser knows."""

    @abstractmethod
    def sections(self, path):
        """Yield one record per section or measure in the edition."""

    def parallel_sections(self, path, workers=None, chunk_size=400):
        yield from self.sections(path)

    def index(self, indexer, path, workers=None, subdivision=None):
        """Editions join the code index by overriding this. Others are recognized and left alone."""
        return 0


def subdivision(code):
    """Return the ISO 3166-2 record for code, or raise ValueError."""
    import pycountry
    found = pycountry.subdivisions.get(code=code)
    if found is None:
        raise ValueError('%s is not an ISO 3166-2 subdivision code' % code)
    return found


class State(ABC):
    """Where a state publishes, and which edition parsers cover its years.

    code is the ISO 3166-2 subdivision, such as US-CA. It is not a name or a slug.
    """

    code = None
    source = None
    editions = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'code' not in cls.__dict__:
            raise TypeError('%s must set code to an ISO 3166-2 subdivision' % cls.__name__)
        subdivision(cls.code)

    def edition(self, path):
        names = table_names(path)
        for parser in self.editions:
            if parser.accepts(names):
                return parser()
        raise TypeError('no parser for %s' % os.path.basename(path))

    def sections(self, path, workers=None):
        edition = self.edition(path)
        return edition.parallel_sections(path, workers=workers)

    @abstractmethod
    def list_editions(self):
        """Names or years currently offered at the distribution point."""
