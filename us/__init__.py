"""United States. Sacramento, California is the home jurisdiction."""

import importlib
import pkgutil

from publication import City, Country, County, State

from .usc import SOURCE, UnitedStatesCode

HOME = 'US-CA'


class UnitedStates(Country):
    """National law. State statutes live in the sibling modules."""

    code = 'US'
    source = 'https://uscode.house.gov/'
    layers = (County, City)
    editions = (UnitedStatesCode,)

    def list_editions(self):
        """Live release-point href is resolved from this page."""
        return [SOURCE]


def load_states():
    """Map ISO 3166-2 code to the State subclass in this package."""
    found = {}
    for mod in pkgutil.iter_modules(__path__):
        if mod.name.startswith('_'):
            continue
        module = importlib.import_module('%s.%s' % (__name__, mod.name))
        for obj in vars(module).values():
            if isinstance(obj, type) and issubclass(obj, State) and obj is not State and obj.__module__ == module.__name__:
                found[obj.code] = obj
    return found
