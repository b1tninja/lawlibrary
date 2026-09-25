"""Bluebook-shaped statute cites.

Rule 1.200 allows The Bluebook instead of the California Style Manual.
The book is not opened here. The form this module renders is the state
shorthand, a leading Cal., and the section sign. Short forms id. and
supra are recognized and are not given a code.
"""

import re

from apa import Code, Reference
from california import parse as parse_california
from parsers import Guide


def render(ref):
    return 'Cal. %s %s' % (ref.code.shorthand, ref.span.text())


def parse(text):
    raw = (text or '').strip()
    if re.match(r'(?i)^id\.', raw) or re.search(r'(?i)\bsupra\b', raw):
        raise ValueError(raw)
    body = re.sub(r'(?i)^cal\.\s+', '', raw)
    found = parse_california(body)
    return Reference(
        found.code, found.span, session=found.session, article=found.article, guide=Guide.BLUEBOOK,
    )
