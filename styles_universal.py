"""Medium-neutral cites.

The Universal Citation Guide, from the American Association of Law
Libraries, points at a decision by year, jurisdiction, and number
instead of a commercial reporter. A statute in this module uses the
Legislature token, which does not depend on a reporter.
"""

import re

from apa import Code, Reference, section
from parsers import Guide

_CASE = re.compile(r'^(?P<year>\d{4})\s+(?P<place>[A-Z]{2})\s+(?P<num>\d+)$')
_STATUTE = re.compile(r'^(?P<code>[A-Z]{2,5})\s+(?:§\s*)?(?P<num>\d+(?:\.\d+)*)$')


class NeutralCase:
    """A medium-neutral case cite. Not a code section."""

    def __init__(self, year, place, number):
        self.year = year
        self.place = place
        self.number = number
        self.guide = Guide.UNIVERSAL

    def reference(self):
        return '%s %s %s' % (self.year, self.place, self.number)


def render(ref):
    return '%s § %s' % (ref.code.value, ref.span.numbers[0])


def parse(text):
    raw = (text or '').strip().rstrip('.')
    case = _CASE.match(raw)
    if case:
        return NeutralCase(case.group('year'), case.group('place'), case.group('num'))
    found = _STATUTE.match(raw)
    if found is None:
        raise ValueError(raw)
    return Reference(
        Code.get(found.group('code')),
        section(found.group('num')),
        guide=Guide.UNIVERSAL,
    )
