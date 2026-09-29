"""United States. Sacramento, California is the home jurisdiction."""

import importlib
import pkgutil

from publication import City, Country, County, State

from .plaw import PublicLaws
from .usc import SOURCE, AnnualCode, UnitedStatesCode

HOME = 'US-CA'


class UnitedStates(Country):
    """National law. State statutes live in ``us.states``."""

    code = 'US'
    source = 'https://uscode.house.gov/'
    layers = (County, City)
    editions = (UnitedStatesCode, AnnualCode, PublicLaws)

    def list_editions(self):
        """Live release-point href is resolved from this page."""
        return [SOURCE]


def load_states():
    """Map ISO 3166-2 code to its State subclass.

    California is its own package, ``us.ca``, with its editions, its markup
    and its counties inside it; the other states are one module each in
    ``us.states`` until one has a publication of its own.
    """
    import us.states as states
    from us.ca import California
    found = {California.code: California}
    for mod in pkgutil.iter_modules(states.__path__):
        if mod.name.startswith('_'):
            continue
        module = importlib.import_module('us.states.%s' % mod.name)
        for obj in vars(module).values():
            if isinstance(obj, type) and issubclass(obj, State) and obj is not State and obj.__module__ == module.__name__:
                found[obj.code] = obj
    return found
