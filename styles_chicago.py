"""Chicago citations of legal material.

The Chicago Manual of Style defers to The Bluebook for the legal cite
and adds ibid for a repeated footnote. The manual is not opened here.
A Chicago cite in this module is the Bluebook statute form, or ibid.
"""

import re

from parsers import Guide
from styles_bluebook import parse as parse_bluebook
from styles_bluebook import render as render_bluebook


class Ibid:
    """The same authority as the previous footnote."""

    guide = Guide.CHICAGO

    def reference(self):
        return 'Ibid.'


def render(ref):
    return render_bluebook(ref)


def parse(text):
    raw = (text or '').strip().rstrip('.')
    if re.match(r'(?i)^ibid$', raw):
        return Ibid()
    found = parse_bluebook(text)
    found.guide = Guide.CHICAGO
    return found
