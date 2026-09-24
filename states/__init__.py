"""One module per state. Each defines a single State subclass."""

import importlib
import pkgutil

from publication import State


def load_states():
    """Map ISO 3166-2 code to the State subclass."""
    found = {}
    for mod in pkgutil.iter_modules(__path__):
        if mod.name.startswith('_'):
            continue
        module = importlib.import_module('%s.%s' % (__name__, mod.name))
        for obj in vars(module).values():
            if isinstance(obj, type) and issubclass(obj, State) and obj is not State and obj.__module__ == module.__name__:
                found[obj.code] = obj
    return found
