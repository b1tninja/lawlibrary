"""Find governments and offices by the frame around the name.

``State of California`` and ``City of Sacramento`` share a shape. The frame
says what kind of thing the name is. A later check asks the places, courts,
and agencies already registered whether that name is one of theirs. A name
the catalog does not have is still a mention. It is not dropped for lack of
a list entry.

The first time a proper name appears it may be followed by a short form in
parentheses, as in ``Department of Real Estate (DRE)`` or
``(hereinafter "DRE")``. Later uses of that short form in the same text
name the same thing.
"""

import enum
import re

import pycountry

from agency import agencies
from court import courts
from needles import noun_pattern


class Kind(enum.Enum):
    """What the frame says the name is. The value is the string."""

    STATE = 'state'
    COUNTY = 'county'
    CITY = 'city'
    COURT = 'court'
    AGENCY = 'agency'


class Relation(enum.Enum):
    """How a sentence ties an office to a duty or to another body. The value is the string."""

    RESPONSIBILITY = 'responsibility'
    DUTY = 'duty'
    POWER = 'power'
    PROCEDURE = 'procedure'
    APPOINTMENT = 'appointment'
    SUPERVISION = 'supervision'
    SCOPE = 'scope'


class Mention:
    """One named thing inside a text."""

    def __init__(self, kind, name, start, end, text, code=None):
        self.kind = kind
        self.name = name
        self.start = start
        self.end = end
        self.text = text
        self.code = code

    def __eq__(self, other):
        return (
            isinstance(other, Mention)
            and self.kind is other.kind
            and self.name == other.name
            and self.start == other.start
            and self.code == other.code
        )

    def __repr__(self):
        return 'Mention(%s, %r, %s)' % (self.kind.value, self.name, self.code)


_NAME = r'[A-Z][a-z]+(?:[ \-][A-Z][a-z]+)*'

_FRAMES = (
    (Kind.STATE, re.compile(r'\b(?:State|Commonwealth) of (?P<name>%s)\b' % _NAME)),
    (Kind.COUNTY, re.compile(r'\bCounty of (?P<name>%s)\b' % _NAME)),
    (Kind.CITY, re.compile(r'\bCity of (?P<name>%s)\b' % _NAME)),
    (Kind.COURT, re.compile(
        r'\b(?:Supreme Court of (?:the )?(?P<name>%s)|'
        r'Superior Court of (?:the )?(?:State of )?(?P<state>%s), County of (?P<county>%s)|'
        r'(?P<district>First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Federal) '
        r'(?:Appellate|Judicial) District)\b' % (_NAME, _NAME, _NAME)
    )),
    (Kind.AGENCY, re.compile(
        r'\b(?:%s) of (?P<name>%s)\b' % (noun_pattern(), _NAME)
    )),
)


def _state_code(name):
    target = name.lower()
    for record in pycountry.subdivisions.get(country_code='US'):
        if record.name.lower() == target and record.type in ('State', 'Commonwealth'):
            return record.code
    return None


def _locality_code(kind, name):
    from entities import list_entities
    hits = [
        row for row in list_entities(kind.value)
        if row['name'].lower() == name.lower()
    ]
    if len(hits) == 1:
        return hits[0]['parent']
    return None


def _known_court(text):
    for court in courts():
        if court.name and court.name in text:
            return court
    return None


def _known_agency(text):
    folded = text.lower()
    for agency in agencies():
        if agency.name and agency.name.lower() in folded:
            return agency
    return None


_ENACTMENT = (
    ('establishment', re.compile(
        r'(?i)\bthere is in (?:the )?[^.]*?\b(?:department|board|bureau|office|commission|agency)\b[^.]*',
    )),
    ('officer', re.compile(
        r'(?i)\bthe chief officer of which [^.]*\bis named\b[^.]*',
    )),
    ('creation', re.compile(
        r'(?i)\bthere is hereby (?:created|established)\b[^.]*',
    )),
    ('continuation', re.compile(
        r'(?i)\bis continued in existence\b',
    )),
    ('vesting', re.compile(
        r'(?i)\b(?:shall )?succeed to,?\s+and is (?:hereby )?vested with\b[^.]*'
        r'|\b(?:is|are) (?:hereby )?vested (?:in|with)\b[^.]*',
    )),
)


def name_queries(printed):
    """Search phrases for one registered name. The roster order is not the statute order."""
    text = (printed or '').strip()
    if not text:
        return []
    phrases = [text]
    paren = re.match(r'^(?P<body>.+?)\s*\([^)]*\)\s*$', text)
    body = paren.group('body').strip() if paren else text
    inverted = re.match(r'^(?P<rest>.+),\s*(?P<kind>Department|Office|Commission|Board|Bureau|Agency) of$', body)
    if inverted:
        phrases.append('%s of %s' % (inverted.group('kind'), inverted.group('rest').strip()))
    return phrases


_RELATIONS = (
    (Relation.RESPONSIBILITY, re.compile(
        r'(?i)\bprincipal responsibility of\b[^.]*?\bto\b',
    )),
    (Relation.DUTY, re.compile(
        r'(?i)\bshall enforce the provisions\b|\bacts and duties\b',
    )),
    (Relation.POWER, re.compile(
        r'(?i)\bfull power to\b|\bmay adopt, amend, or repeal\b',
    )),
    (Relation.PROCEDURE, re.compile(
        r'(?i)\bin accordance with the provisions of the Administrative Procedure\b[^.]*',
    )),
    (Relation.APPOINTMENT, re.compile(
        r'(?i)\bappointed by the Governor\b',
    )),
    (Relation.SUPERVISION, re.compile(
        r'(?i)\bunder the supervision of\b[^.]*',
    )),
    (Relation.SCOPE, re.compile(
        r'(?i)\bcommencing with Section\s+\d[\d.]*',
    )),
)


class Tie:
    """One duty or relationship span."""

    def __init__(self, relation, start, end, text):
        self.relation = relation
        self.start = start
        self.end = end
        self.text = text

    def __repr__(self):
        return 'Tie(%s, %s)' % (self.relation.value, self.start)


def find_relations(text):
    """Return duty and relationship frames in ``text``."""
    if not text:
        return []
    found = []
    for relation, pattern in _RELATIONS:
        for match in pattern.finditer(text):
            found.append(Tie(relation, match.start(), match.end(), match.group(0).strip()))
    found.sort(key=lambda tie: (tie.start, tie.end))
    return found


def find_enactments(text):
    """Return creation and authorization frames in ``text``."""
    if not text:
        return []
    found = []
    for frame, pattern in _ENACTMENT:
        for match in pattern.finditer(text):
            found.append(Mention(Kind.AGENCY, frame, match.start(), match.end(), match.group(0).strip()))
    found.sort(key=lambda mention: (mention.start, mention.end))
    return found


_FRAME_QUERIES = (
    'There is in the',
    'chief officer of which',
    'is continued in existence',
    'powers and duties are vested',
)


def hunt_authorities(limit=40):
    """Find sections that enact a California office already registered.

    The index is California, so offices under another state are skipped.
    A section counts when its text contains the office name, roster order or
    statute order, and one of the enactment frames. An office that already
    has ``authority`` is read at that citation as well.
    """
    import query

    known = []
    for agency in agencies():
        if agency.parent != 'US-CA':
            continue
        phrases = [phrase.casefold() for phrase in name_queries(agency.name)]
        known.append((agency, phrases))

    pins = []
    seen = set()

    def consider(agency, citation, text):
        if (agency.name, citation) in seen:
            return
        folded = text.casefold()
        phrases = next(item[1] for item in known if item[0] is agency)
        if not any(phrase in folded for phrase in phrases):
            return
        frames = find_enactments(text)
        relations = find_relations(text)
        if not frames and not relations:
            return
        seen.add((agency.name, citation))
        pins.append({
            'agency': agency.name,
            'citation': citation,
            'frames': [mark.name for mark in frames],
            'relations': [tie.relation.value for tie in relations],
        })

    for agency, _phrases in known:
        if not agency.authority:
            continue
        parts = agency.authority.split()
        if len(parts) != 2:
            continue
        doc = query.section(parts[0], parts[1])
        if doc.get('found'):
            consider(agency, doc.get('citation'), doc.get('text') or '')

    for phrase in _FRAME_QUERIES:
        for hit in query.search(phrase, limit=limit):
            text = hit.get('snippet') or ''
            for agency, _phrases in known:
                consider(agency, hit.get('citation'), text)
    return pins


_OFFICES = (
    'board of supervisors',
    'county auditor',
    'county assessor',
    'Secretary of State',
    'Attorney General',
    'State Treasurer',
    'State Fire Marshal',
    'State Auditor',
    'Judicial Council',
    'Franchise Tax Board',
)


class Abbreviation:
    """A short form introduced beside a proper name and used again in this text."""

    def __init__(self, name, short, start, end, introduction):
        self.name = name
        self.short = short
        self.start = start
        self.end = end
        self.introduction = introduction


_ABBREV = re.compile(
    r'(?P<name>(?:The\s+)?(?:[A-Z][A-Za-z.&]+(?:\s+(?:of|the|and|for|&)\s+|\s+)){0,10}[A-Z][A-Za-z.&]+)'
    r'\s+\((?:hereinafter\s+|hereafter\s+)?["“]?(?P<short>[A-Z][A-Z0-9&]{1,11})["”]?\)'
)


def abbreviations(text):
    """Short forms defined beside a name, then each later use in this text.

    The introduction is the parenthetical. A later use keeps the same name.
    A short form that was never introduced is not recorded.
    """
    if not text:
        return []
    found = []
    for match in _ABBREV.finditer(text):
        name = re.sub(r'^(?:The|A|An)\s+', '', match.group('name').strip())
        short = match.group('short')
        found.append(Abbreviation(name, short, match.start('short'), match.end('short'), True))
        for later in re.finditer(r'\b%s\b' % re.escape(short), text[match.end():]):
            start = match.end() + later.start()
            found.append(Abbreviation(name, short, start, start + len(short), False))
    return found


def find_mentions(text):
    """Return every framed name in ``text``, in order of appearance."""
    if not text:
        return []
    found = []
    for kind, pattern in _FRAMES:
        for match in pattern.finditer(text):
            if kind is Kind.COURT and match.groupdict().get('district'):
                name = match.group('district') + ' Appellate District' if 'Appellate' in match.group(0) else match.group(0)
                code = None
                known = _known_court(match.group(0))
                if known is not None:
                    code = known.government()
                    name = known.name
            elif kind is Kind.COURT and match.groupdict().get('county'):
                name = match.group('county')
                code = _locality_code(Kind.COUNTY, name)
            else:
                name = match.group('name')
                code = None
                if kind is Kind.STATE:
                    code = _state_code(name)
                elif kind in (Kind.CITY, Kind.COUNTY):
                    code = _locality_code(kind, name)
                elif kind is Kind.COURT:
                    known = _known_court(match.group(0))
                    if known is not None:
                        code = known.government()
                elif kind is Kind.AGENCY:
                    known = _known_agency(match.group(0))
                    if known is not None:
                        code = known.parent if isinstance(known.parent, str) else None
            found.append(Mention(kind, name, match.start(), match.end(), match.group(0), code))
    folded = text.lower()
    for title in _OFFICES:
        start = folded.find(title.lower())
        if start < 0:
            continue
        found.append(Mention(Kind.AGENCY, title, start, start + len(title), text[start:start + len(title)]))
    found.sort(key=lambda mention: (mention.start, mention.end))
    return found
