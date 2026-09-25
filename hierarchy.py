"""Where a California office sits, read from enactment and vesting clauses.

An enactment says an office is in another office. A vesting clause says one
office succeeded another. ``seats`` reads one section. ``collect`` reads the
index. ``chart`` draws the edges. ``absent`` names offices the clauses never
placed. ``crumbs`` is the outline above a section. ``lineage`` walks the
parent office and keeps that outline at each step.
"""

import os
import re
import sqlite3

from whoosh import index
from whoosh.qparser import QueryParser

from needles import noun_pattern
from vesting import grants


class Seat:
    """One office placed under another. ``frame`` is sits or succeeds."""

    def __init__(self, child, parent, citation, frame):
        self.child = child
        self.parent = parent
        self.citation = citation
        self.frame = frame

    def __repr__(self):
        return 'Seat(%r, %r, %s)' % (self.child, self.parent, self.frame)


_WORDS = r'[A-Z][A-Za-z]+(?:[ \-](?!which\b|consisting\b|that\b|under\b)[A-Za-z][A-Za-z]+)*'
_OFFICE = (
    r'(?:%s) of %%s'
    r'|California %%s'
    r'|State %%s'
    r"|Contractors[\u2019'\ufffd]? State License Board"
) % noun_pattern()
_OFFICE = _OFFICE % (_WORDS, _WORDS, _WORDS)
_PARENT_FIRST = re.compile(
    r'(?i)\bthere is(?: hereby)?(?: continued in existence)? in the (?P<body>[^.]+)'
)
_INDEPENDENT = re.compile(
    r'(?i)\bheretofore known as the (?P<child>%s) in the (?P<parent>[^.]{3,160}?) '
    r'is hereby made an independent' % _OFFICE
)
_ESTABLISH = re.compile(
    r'(?i)\bto establish an (?P<child>%s)\b' % _OFFICE
)
_CHILD_FIRST = re.compile(
    r"(?i)\b(?:the )?(?P<child>%s) (?:is hereby (?:created|continued in existence)|shall continue) "
    r"(?:in|within) the (?P<parent>[^.]{3,160})" % _OFFICE
)
_ROSTER = re.compile(
    r"(?i)\bthere are in the state government the following agencies:\s*(?P<body>[^.]+)"
)
_PHRASES = (
    '"there is in the"',
    '"continued in existence"',
    '"hereby created"',
    '"shall continue within"',
    '"following agencies"',
    '"heretofore known as"',
    '"to establish an"',
)


def _tidy(name):
    name = (name or '').replace('\ufffd', "'").replace('\u2019', "'")
    name = re.sub(r'\s+', ' ', name).strip(' .,;')
    name = re.sub(r'(?i)^(?:the|a|an) ', '', name)
    return name


def _key(name):
    return re.sub(r'[^a-z0-9]+', ' ', (name or '').casefold()).strip()


def _parent(text):
    parts = re.split(r'(?i),\s*in the ', text or '')
    return _tidy(parts[-1])


def _roster(body):
    body = re.sub(r'(?i)\s+and\s+', '; ', body or '')
    names = []
    for part in body.split(';'):
        name = _tidy(part)
        if not name:
            continue
        if not name.lower().endswith('agency'):
            name = name + ' Agency'
        names.append(name)
    return names


def seats(text, citation=''):
    """Offices this section places. A miss is an empty list."""
    if not text:
        return []
    found = []
    seen = set()

    def add(child, parent, frame):
        child = _tidy(child)
        parent = _parent(parent) if frame == 'sits' else _tidy(parent)
        if not child or _key(child) == _key(parent):
            return
        if frame != 'created' and not parent:
            return
        key = (_key(child), _key(parent), frame)
        if key in seen:
            return
        seen.add(key)
        found.append(Seat(child, parent, citation, frame))

    office = re.compile(r'(?i)(?:a|the) (?P<child>%s)\b' % _OFFICE)
    for match in _PARENT_FIRST.finditer(text):
        body = match.group('body')
        child = None
        for hit in office.finditer(body):
            if body[:hit.start()].endswith('in '):
                continue
            child = hit
            break
        if child is None:
            continue
        before = body[:child.start()]
        nested = re.split(r'(?i),\s*in the ', before)
        add(child.group('child'), nested[-1], 'sits')
    for match in _INDEPENDENT.finditer(text):
        add(match.group('child'), match.group('parent'), 'leaves')
    for match in _ESTABLISH.finditer(text):
        add(match.group('child'), '', 'created')
    for match in _CHILD_FIRST.finditer(text):
        add(match.group('child'), match.group('parent'), 'sits')
    for match in _ROSTER.finditer(text):
        for name in _roster(match.group('body')):
            add(name, 'state government', 'sits')
    for grant in grants(text):
        if grant.receiver and grant.prior:
            add(grant.receiver, grant.prior, 'succeeds')
    return found


def collect(idx_path):
    """Seats from the stored California sections, plus stored vesting edges."""
    rows = []
    seen = set()
    if index.exists_in(idx_path):
        ix = index.open_dir(idx_path)
        parser = QueryParser('LEGAL_TEXT', ix.schema)
        with ix.searcher() as searcher:
            for phrase in _PHRASES:
                for hit in searcher.search(parser.parse(phrase), limit=None):
                    citation = hit.get('CITATION') or ''
                    if citation in seen:
                        continue
                    seen.add(citation)
                    rows.extend(seats(hit.get('LEGAL_TEXT') or '', citation))
    path = os.path.join(idx_path, 'needles.sqlite')
    if os.path.isfile(path):
        db = sqlite3.connect(path)
        try:
            stored = db.execute(
                "SELECT citation, receiver, prior FROM edge WHERE kind = 'vesting'"
            ).fetchall()
        finally:
            db.close()
        have = {(row.child.casefold(), row.parent.casefold()) for row in rows if row.frame == 'succeeds'}
        for citation, receiver, prior in stored:
            key = ((receiver or '').casefold(), (prior or '').casefold())
            if key in have or not receiver or not prior:
                continue
            rows.append(Seat(receiver, prior, citation, 'succeeds'))
    return rows


def forest(rows):
    """Parent to children, for sits edges only."""
    children = {}
    for row in rows:
        if row.frame != 'sits':
            continue
        children.setdefault(row.parent, [])
        if row.child not in children[row.parent]:
            children[row.parent].append(row.child)
    return children


def absent(rows, names):
    """Names that never appear as a placed office."""
    placed = {_key(row.child) for row in rows}
    return [name for name in names if _key(name) not in placed]


class Crumb:
    """One outline step above a section: the code, a heading, or the section."""

    def __init__(self, level, heading):
        self.level = level
        self.heading = heading

    def __repr__(self):
        return 'Crumb(%s, %r)' % (self.level, self.heading)


class Step:
    """One ancestor of an office, and the outline of the section that names it."""

    def __init__(self, office, frame, citation, crumbs):
        self.office = office
        self.frame = frame
        self.citation = citation
        self.crumbs = crumbs


_ORDER = ('code', 'title', 'division', 'part', 'chapter', 'article', 'section')


def crumbs(source):
    """The outline above a section, from the code down to the section.

    ``source`` is a ``query.section`` payload or a citation such as ``BPC 10050``.
    A section the index does not hold is an empty list.
    """
    doc = source
    if isinstance(source, str):
        import query
        parts = source.split(None, 1)
        if len(parts) != 2:
            return []
        doc = query.section(parts[0], parts[1])
    if not isinstance(doc, dict) or not doc.get('found', True):
        return []
    found = []
    if doc.get('code'):
        found.append(Crumb('code', doc['code']))
    for item in doc.get('path') or []:
        heading = (item.get('heading') or '').strip()
        if heading:
            found.append(Crumb(item.get('level') or '', heading))
    if doc.get('citation'):
        found.append(Crumb('section', doc['citation']))
    rank = {level: place for place, level in enumerate(_ORDER)}
    found.sort(key=lambda crumb: rank.get(crumb.level, len(_ORDER)))
    return found


def trail(source):
    """The crumb headings in one line."""
    return ' > '.join(crumb.heading for crumb in crumbs(source))


def lineage(name, rows, depth=6):
    """Ancestors of ``name``. Each step keeps the outline of the placing section.

    A sits or leaves edge walks to that parent. A succeeds edge walks from the
    office that was replaced to the office that replaced it. A cycle stops.
    """
    steps = []
    seen = set()

    def walk(current, left):
        key = _key(current)
        if not key or key in seen or left < 0:
            return
        seen.add(key)
        for row in rows:
            if _key(row.child) != key or row.frame not in ('sits', 'leaves'):
                continue
            steps.append(Step(row.parent, row.frame, row.citation, crumbs(row.citation)))
            if row.parent:
                walk(row.parent, left - 1)
        for row in rows:
            if row.frame != 'succeeds' or _key(row.parent) != key:
                continue
            steps.append(Step(row.child, row.frame, row.citation, crumbs(row.citation)))
            walk(row.child, left - 1)

    walk(name, depth)
    return steps


def chart(rows):
    """A mermaid flowchart. Sits edges point at the parent. Succeeds edges point at the successor."""
    from structure import _chart
    edges = []
    for row in rows:
        if row.frame == 'sits':
            edges.append((row.child, row.parent, 'in'))
        elif row.frame == 'succeeds':
            edges.append((row.child, row.parent, 'succeeds'))
    return _chart(edges, 'in')
