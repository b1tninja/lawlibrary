"""California citation, the form used in California courts and codes.

Rule 8.204 encourages the California Style Manual. The Judicial Council's
Fourth Appellate District self-help appendix, on appellate.courts.ca.gov,
tells a filer to give the code name and the word "section". This renderer
uses that form. The section sign and the Legislature token still parse,
because both appear in California text. The Style Manual book was not opened.
"""

import re

from apa import Code, Reference, section, series, span
from citations import Cite
from government import Article, ArticleMark
from parsers import Guide

_SUB = re.compile(
    r'(?i)(?:,\s*)?(?:subdivision|subd\.?)\s*\(([a-z0-9]+)\)\s*$'
)
_ATTACHED = re.compile(r'(?i)^(?P<num>\d+(?:\.\d+)*)\((?P<sub>[a-z0-9]+)\)$')
_HEAD = re.compile(
    r'(?i)^(?:article\s+(?P<article>[IVXLC]+(?:\s*[A-D])?)\s*,?\s*)?'
    r'(?:sections|section|§§|§)\s+'
    r'(?P<body>.+)$'
)


def _labels():
    rows = []
    for code in Code:
        rows.append((code.title, code))
        rows.append((code.shorthand, code))
        rows.append((code.value, code))
    rows.sort(key=lambda item: len(item[0]), reverse=True)
    return rows


def _article(token):
    if token is None:
        return None
    label = ' '.join(token.upper().split())
    try:
        return Article(label)
    except ValueError:
        return ArticleMark(label)


def _span_from(body):
    body = body.strip().rstrip('.')
    open_ended = bool(re.search(r'(?i)\bet\s+seq', body))
    body = re.sub(r'(?i)\s*,?\s*et\s+seq\.?\s*$', '', body).strip()
    subdivision = None
    found = _SUB.search(body)
    if found:
        subdivision = found.group(1)
        body = body[:found.start()].strip(' ,')
    attached = _ATTACHED.match(body)
    if attached:
        return section(attached.group('num'), attached.group('sub'))
    if re.search(r'[-–—]|\bto\b|\bthrough\b', body) and ',' not in body:
        numbers = re.findall(r'\d+(?:\.\d+)*', body)
        if len(numbers) != 2:
            raise ValueError(body)
        return span(numbers[0], numbers[1])
    numbers = re.findall(r'\d+(?:\.\d+)*', body)
    if len(numbers) >= 2:
        return series(*numbers)
    if len(numbers) != 1:
        raise ValueError(body)
    found = section(numbers[0], subdivision)
    found.open = open_ended
    return found


def render(ref):
    """Code name, the word section, and the numbers."""
    name = ref.code.title
    if ref.article is not None:
        name = '%s, article %s,' % (name, ref.article.value)
    if ref.span.cite is Cite.SECTION:
        text = '%s section %s' % (name, ref.span.numbers[0])
        if ref.span.open:
            return '%s, commencing with Section %s' % (name, ref.span.numbers[0])
        if ref.span.subdivision:
            text = '%s, subdivision (%s)' % (text, str(ref.span.subdivision).strip('()'))
        return text
    if ref.span.cite is Cite.RANGE:
        body = '%s to %s' % ref.span.numbers
    elif len(ref.span.numbers) == 2:
        body = '%s and %s' % ref.span.numbers
    else:
        body = '%s, and %s' % (', '.join(ref.span.numbers[:-1]), ref.span.numbers[-1])
    return '%s sections %s' % (name, body)


def parse(text):
    """Read a California citation back into a code and a span."""
    raw = (text or '').strip().rstrip('.')
    session = None
    year = re.search(r'\((\d{4})\)$', raw)
    if year:
        session = year.group(1)
        raw = raw[:year.start()].strip().rstrip(',')
    for label, code in _labels():
        if raw.lower().startswith(label.lower()):
            rest = raw[len(label):].strip(' ,')
            break
    else:
        raise ValueError(raw)
    if re.match(r'\d', rest):
        rest = 'section ' + rest
    commencing = re.match(r'(?i)commencing with section\s+(?P<body>.+)$', rest)
    if commencing:
        body = section(commencing.group('body').strip().rstrip('.'))
        body.open = True
        return Reference(
            code, body, session=session, guide=Guide.CALIFORNIA_STYLE_MANUAL,
        )
    head = _HEAD.match(rest)
    if head is None:
        raise ValueError(raw)
    return Reference(
        code,
        _span_from(head.group('body')),
        session=session,
        article=_article(head.group('article')),
        guide=Guide.CALIFORNIA_STYLE_MANUAL,
    )
