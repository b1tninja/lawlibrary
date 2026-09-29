"""The California codes. This name stays until every import says us.ca.apa."""

import sys as _sys

import us.ca.apa as _moved

_sys.modules[__name__] = _moved
