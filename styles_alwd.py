"""ALWD statute cites.

The Association of Legal Writing Directors manual is a streamlined
alternative. The District of Montana local rules, opened earlier, allow
either that manual or The Bluebook. This module renders the shorthand
and the section sign, without the Cal. prefix the Bluebook module adds.
"""

from california import parse as parse_california
from parsers import Guide


def render(ref):
    return '%s %s' % (ref.code.shorthand, ref.span.text())


def parse(text):
    found = parse_california(text)
    found.guide = Guide.ALWD
    return found
