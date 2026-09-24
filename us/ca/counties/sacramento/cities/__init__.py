"""Cities inside this county."""

from publication import City, load_localities


def load():
    return load_localities(__name__, __path__, City)
