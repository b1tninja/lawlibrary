"""Governments, from country to city.

A country is ISO 3166-1. A region is ISO 3166-2. Anything below a region is a
Locality. Country.layers is the order under a region, and it differs by
country. The United States uses a county, then a city. The code catalog is
pycountry. A class stores only its own code.

A layer package exists only when that place has been added. California has
counties. Sacramento County has cities. An empty state has neither.
"""

import importlib
import os
import pkgutil
import zipfile
from abc import ABC, abstractmethod

import pycountry

_countries = {}


def country(code):
    """Return the ISO 3166-1 record for an alpha-2 code, or raise ValueError."""
    found = pycountry.countries.get(alpha_2=code)
    if found is None:
        raise ValueError('%s is not an ISO 3166-1 country code' % code)
    return found


def subdivision(code):
    """Return the ISO 3166-2 record for code, or raise ValueError."""
    found = pycountry.subdivisions.get(code=code)
    if found is None:
        raise ValueError('%s is not an ISO 3166-2 subdivision code' % code)
    return found


def _table_names(path):
    with zipfile.ZipFile(path) as zf:
        return {os.path.splitext(os.path.basename(info.filename))[0]
                for info in zf.infolist()
                if os.path.splitext(info.filename)[1] == '.dat'}


class Jurisdiction(ABC):
    """A government with a distribution point and the edition parsers it knows."""

    code = None
    source = None
    editions = ()

    def edition(self, path):
        hint = _table_names(path) if zipfile.is_zipfile(path) else path
        for parser in self.editions:
            if parser.accepts(hint):
                return parser()
        raise TypeError('no parser for %s' % os.path.basename(path))

    def sections(self, path, workers=None):
        edition = self.edition(path)
        return edition.parallel_sections(path, workers=workers)

    @abstractmethod
    def list_editions(self):
        """Names or years currently offered at the distribution point."""


class Country(Jurisdiction):
    """National law. code is an ISO 3166-1 alpha-2, such as US.

    layers is the local stack under a region, outer to inner.
    """

    layers = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'code' not in cls.__dict__:
            return
        country(cls.code)
        _countries[cls.code] = cls

    @classmethod
    def record(cls):
        return country(cls.code)


class Region(Jurisdiction):
    """A first-level ISO 3166-2 region, such as US-CA or JP-13.

    legislates is false when the region does not publish statutes.
    """

    legislates = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'code' not in cls.__dict__:
            return
        subdivision(cls.code)

    @classmethod
    def country(cls):
        """ISO 3166-1 record for this region. The catalog is pycountry."""
        return subdivision(cls.code).country

    @classmethod
    def record(cls):
        return subdivision(cls.code)


def _open_layer(module_name):
    """Load a layer package. Missing packages are an empty registry."""
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return {}
    return module.load()


class State(Region):
    """A US state. Districts and outlying areas are other regions."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'code' not in cls.__dict__:
            return
        record = subdivision(cls.code)
        if record.country_code != 'US' or record.type != 'State':
            raise TypeError('%s code %s is not a US state' % (cls.__name__, cls.code))

    @classmethod
    def counties(cls):
        """This state's counties, keyed by module name."""
        return _open_layer(cls.__module__ + '.counties')


def load_localities(package_name, package_path, kind=None):
    """Map a module name to the Locality subclass defined in that module."""
    found = {}
    for mod in pkgutil.iter_modules(package_path):
        if mod.name.startswith('_'):
            continue
        module = importlib.import_module('%s.%s' % (package_name, mod.name))
        for obj in vars(module).values():
            if isinstance(obj, type) and issubclass(obj, Locality) and obj is not Locality and obj.__module__ == module.__name__:
                if kind is None or issubclass(obj, kind):
                    found[mod.name] = obj
    return found


def _layer_parent(locality):
    """Walk parent links to the ISO 3166-2 region code."""
    parent = locality.parent
    while isinstance(parent, type):
        parent = parent.parent
    return parent


class Locality(ABC):
    """A government below an ISO region. Not itself an ISO subdivision.

    parent is the region code, or the locality it sits inside. Country.layers
    says which of those is legal.
    """

    name = None
    parent = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'name' not in cls.__dict__ or 'parent' not in cls.__dict__:
            return
        parent = cls.parent
        if isinstance(parent, str):
            subdivision(parent)
        elif not (isinstance(parent, type) and issubclass(parent, Locality)):
            raise TypeError('%s parent must be a region code or a Locality' % cls.__name__)
        _check_layer(cls)

    @classmethod
    def region(cls):
        """ISO 3166-2 code of the region this locality sits in."""
        return _layer_parent(cls)


def _check_layer(cls):
    code = subdivision(_layer_parent(cls)).country_code
    country_cls = _countries.get(code)
    if country_cls is None or not country_cls.layers:
        return
    kind = next((layer for layer in country_cls.layers if issubclass(cls, layer)), None)
    if kind is None:
        raise TypeError('%s is not a local layer of %s' % (cls.__name__, code))
    index = country_cls.layers.index(kind)
    if index == 0:
        if not isinstance(cls.parent, str):
            raise TypeError('%s is the outer local layer of %s and parents on the region' % (cls.__name__, code))
        return
    outer = country_cls.layers[index - 1]
    if not (isinstance(cls.parent, type) and issubclass(cls.parent, outer)):
        raise TypeError('%s must sit inside a %s' % (cls.__name__, outer.__name__))


class County(Locality):
    """Outer local layer in the United States: a county, parish, or borough."""

    @classmethod
    def cities(cls):
        """Cities nested in this county. Empty when that package does not exist."""
        return _open_layer(cls.__module__ + '.cities')


class City(Locality):
    """A municipality. In the US its parent is a county. Another country chooses."""

    @classmethod
    def county(cls):
        if isinstance(cls.parent, type) and issubclass(cls.parent, County):
            return cls.parent
        return None
