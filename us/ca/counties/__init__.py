"""California counties. Import one county from its module."""

from publication import County, load_localities


def load():
    return load_localities(__name__, __path__, County)
