"""Pick the citation system a text is already using.

California is the default. That is the system for Sacramento courts and
for the California codes. Another system is chosen only when the text
carries a signal that system owns.
"""

import re

from apa import CitationSystem


def identify(text):
    """The system a citation appears to use. California when the signals are quiet."""
    raw = (text or '').strip()
    folded = raw.lower()
    if 'indigo book' in folded:
        return CitationSystem.IndigoBook
    if re.match(r'(?i)^ibid\.?$', raw) or 'chicago' in folded:
        return CitationSystem.Chicago
    if 'alwd' in folded:
        return CitationSystem.ALWD
    if '¶' in raw or re.search(r'\b\d{4}\s+[A-Z]{2}\s+\d+\b', raw):
        return CitationSystem.Universal
    if re.search(r'\(\d{4}\)\.$', raw) and '§' in raw and ',' in raw:
        return CitationSystem.APA
    if re.match(r'(?i)^cal\.\s', raw) or folded.startswith('id.') or 'supra' in folded or 'u.s.c.' in folded:
        return CitationSystem.Bluebook
    return CitationSystem.CaliforniaStyleManual


def render(ref):
    """Render a guide other than California and APA. Those two live with their modules."""
    from styles_alwd import render as alwd
    from styles_bluebook import render as bluebook
    from styles_chicago import render as chicago
    from styles_indigo import render as indigo
    from styles_universal import render as universal
    from parsers import Guide

    chosen = {
        Guide.BLUEBOOK: bluebook,
        Guide.INDIGO: indigo,
        Guide.ALWD: alwd,
        Guide.UNIVERSAL: universal,
        Guide.CHICAGO: chicago,
    }.get(ref.guide)
    if chosen is None:
        raise ValueError(ref.guide)
    return chosen(ref)
