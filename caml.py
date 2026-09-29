"""CAML, the markup California publishes in. This name stays until every import says us.ca.caml."""

import sys as _sys

import us.ca.caml as _moved

_sys.modules[__name__] = _moved
