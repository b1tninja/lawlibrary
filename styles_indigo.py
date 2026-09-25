"""Indigo Book statute cites.

The Indigo Book is a free Creative Commons restatement aimed at The
Bluebook's practitioner notes. This module uses the same statute shape
as the Bluebook module. It does not copy either book.
"""

from parsers import Guide
from styles_bluebook import parse as parse_bluebook
from styles_bluebook import render as render_bluebook


def render(ref):
    return render_bluebook(ref)


def parse(text):
    found = parse_bluebook(text)
    found.guide = Guide.INDIGO
    return found
