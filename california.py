"""The California citation form. This name stays until every import says us.ca.citation."""

import sys as _sys

import us.ca.citation as _moved

_sys.modules[__name__] = _moved
