"""Read a statute sentence into the classes this catalog already has.

A reading can be stored as pins. A pin is a jurisdiction and a delegation
fact for one registered class, taken from one citation. Re-pinning that
citation replaces the earlier rows. The statute text stays in its own
corpus. This file is only the index of those facts.

The sentence splitter keeps a period that belongs to an abbreviation or to a
section sign. Each sentence is then scanned for the frames in ``mentions``,
``citations``, and ``lexical``. A name that matches a registered court,
agency, state, county, or city becomes an instance of that class. A name
the catalog has not registered becomes an instance of the base class for
its frame: ``Agency``, ``Court``, ``State``, ``County``, or ``City``.
"""

import os
import re
import sqlite3

from agency import Agency, agencies
from core import data_dir, ensure_dir
from citations import annotate, find_citations
from court import Court, courts
from jurisdiction import City, County, State
from lexical import find_clauses
from mentions import Kind, find_enactments, find_mentions, find_relations, name_queries
from needles import nouns


class Part:
    """One piece of a sentence. ``role`` is rule, condition, exception, or limit."""

    def __init__(self, role, text, start, end):
        self.role = role
        self.text = text
        self.start = start
        self.end = end


class Sentence:
    """One sentence and the entities, duties, clauses, and citations in it."""

    def __init__(self, text, subjects, clauses, citations, annotations, phrases=(), parts=()):
        self.text = text
        self.subjects = subjects
        self.clauses = clauses
        self.citations = citations
        self.annotations = annotations
        self.phrases = phrases
        self.parts = parts


class Reading:
    """The sentences of a text, in order."""

    def __init__(self, sentences):
        self.sentences = sentences

    @property
    def subjects(self):
        found = []
        for sentence in self.sentences:
            found.extend(sentence.subjects)
        return found


_ABBREV = re.compile(
    r'(?i)(?:\b(?:gov|code|sec|no|mr|mrs|dr|prof|dept|div|art|ch|bus|civ|pen|ed|corp|cf|al)|'
    r'\b[A-Z]|U\.S|e\.g|i\.e|et seq)\.$'
)


_CUTS = (
    ('exception', re.compile(r'(?i)\b(?:notwithstanding|except(?:\s+that|\s+as)?|unless)\b')),
    ('limit', re.compile(r'(?i)\b(?:provided,? however, that|provided that|subject to)\b')),
    ('condition', re.compile(r'(?i)\b(?:if|when|where)\b')),
)


def breakdown(text):
    """The rule and each condition, exception, or limit in one sentence.

    The House manual, section 102, says a sentence that states a general rule
    and an exception should be read as those parts. A cut at the start closes
    at the first comma. The text before any later cut is the rule.
    """
    source = text or ''
    marks = []
    for role, pattern in _CUTS:
        for match in pattern.finditer(source):
            marks.append((match.start(), role))
    marks.sort()
    if not source.strip():
        return []
    if not marks:
        return [Part('rule', source.strip(), 0, len(source))]
    if marks[0][0] == 0:
        comma = source.find(',')
        if comma > 0:
            role = marks[0][1]
            rest = [(start, name) for start, name in marks if start > comma]
            parts = [Part(role, source[:comma + 1].strip(), 0, comma + 1)]
            if not rest:
                parts.append(Part('rule', source[comma + 1:].strip(), comma + 1, len(source)))
                return parts
            if rest[0][0] > comma + 1:
                parts.append(Part('rule', source[comma + 1:rest[0][0]].strip(), comma + 1, rest[0][0]))
            for index, (start, name) in enumerate(rest):
                end = rest[index + 1][0] if index + 1 < len(rest) else len(source)
                parts.append(Part(name, source[start:end].strip(), start, end))
            return parts
    parts = []
    if marks[0][0] > 0:
        parts.append(Part('rule', source[:marks[0][0]].strip(), 0, marks[0][0]))
    for index, (start, role) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(source)
        parts.append(Part(role, source[start:end].strip(), start, end))
    return parts


def split_sentences(text):
    """Split on sentence ends. Keep abbreviations and decimals intact."""
    if not text or not str(text).strip():
        return []
    parts = []
    start = 0
    source = str(text)
    for index, char in enumerate(source):
        if char not in '.?!':
            continue
        if char == '.' and index and source[index - 1].isdigit() and index + 1 < len(source) and source[index + 1].isdigit():
            continue
        if char == '.' and _ABBREV.search(source[start:index + 1]):
            continue
        piece = source[start:index + 1].strip()
        if piece:
            parts.append(piece)
        start = index + 1
    tail = source[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _agency_model(mention):
    haystack = mention.text.casefold()
    for agency in agencies():
        for phrase in name_queries(agency.name):
            if phrase.casefold() in haystack or haystack in phrase.casefold():
                return agency
    return Agency


def _court_model(mention):
    haystack = mention.text.casefold()
    for court in courts():
        if court.name and court.name.casefold() in haystack:
            return court
        if mention.name and mention.name.casefold() in (court.name or '').casefold() and 'superior' in haystack and 'superior' in (court.name or '').casefold():
            return court
    return Court


def _locality_model(mention):
    base = City if mention.kind is Kind.CITY else County
    from us.states.ca import California
    for county in California.counties().values():
        if mention.kind is Kind.COUNTY and county.name.casefold() == mention.name.casefold():
            return county
        if mention.kind is Kind.CITY:
            for city in county.cities().values():
                if city.name.casefold() == mention.name.casefold():
                    return city
    return base


def _state_model(mention):
    from us import load_states
    if not mention.code:
        return State
    return load_states().get(mention.code, State)


def _model(mention):
    if mention.kind is Kind.AGENCY:
        return _agency_model(mention)
    if mention.kind is Kind.COURT:
        return _court_model(mention)
    if mention.kind is Kind.STATE:
        return _state_model(mention)
    if mention.kind in (Kind.CITY, Kind.COUNTY):
        return _locality_model(mention)
    return None


class Phrase:
    """One title after the words next to it have chosen a reading.

    ``of`` plus a name is the office. A number, or ``this`` before the title,
    is the unit of the code. ``score`` is how strongly the neighbor decided.
    """

    def __init__(self, text, start, end, reading, score, reason, noun):
        self.text = text
        self.start = start
        self.end = end
        self.reading = reading
        self.score = score
        self.reason = reason
        self.noun = noun


_NAME = r'[A-Z][A-Za-z]+(?:[ \-](?:and|the|for|[A-Z][A-Za-z]+))*'


def capitals(text):
    """All-capital words that contrast with the sentence, and clauses set in capitals.

    One capitalized word among ordinary words is a name. A whole clause or
    paragraph in capitals is emphasis, and the words inside it are not names.
    """
    if not text:
        return []
    found = []
    offset = 0
    for paragraph in re.split(r'\n\s*\n', text):
        letters = re.sub(r'[^A-Za-z]', '', paragraph)
        if letters and letters.isupper() and len(letters) > 3:
            found.append(Phrase(paragraph.strip(), offset, offset + len(paragraph), 'emphasis', 2, 'clause', None))
        else:
            for match in re.finditer(r'\b[A-Z]{3,}\b', paragraph):
                found.append(Phrase(
                    match.group(0), offset + match.start(), offset + match.end(),
                    'name', 2, 'case', None,
                ))
        offset += len(paragraph) + 2
    return found


def _forms(cls):
    return '|'.join(re.escape(form) for form in cls.forms)


def compose(text):
    """Apply each noun class's own rules. A class with no rules is skipped.

    ``of`` extends the title. ``tail`` takes the words in front of it.
    ``number`` and ``this`` are the unit of a code, and only a class that
    asks for them, such as Division, receives those parses.
    """
    if not text:
        return []
    found = []
    covered = []
    classes = [cls for cls in nouns() if cls.rules and cls.forms]

    def add(match, reading, score, reason, noun):
        if any(match.start() < right and match.end() > left for left, right in covered):
            return
        covered.append((match.start(), match.end()))
        found.append(Phrase(
            text[match.start():match.end()], match.start(), match.end(),
            reading, score, reason, noun,
        ))

    passes = (
        ('of', 'office', 3, r'\b(?i:(?P<title>%s))\s+of\s+(?:the\s+)?(?P<name>%s)' % ('%s', _NAME)),
        ('tail', 'office', 2, r'\b(?P<name>(?!(?:The|A|An)\b)[A-Z][A-Za-z]+(?: (?:and|the|for|[A-Z][A-Za-z]+)){0,5} )(?P<title>%s)\b'),
        ('number', 'unit', 3, r'\b(?i:(?P<title>%s))\s+(?P<number>\d+)'),
        ('this', 'unit', 3, r'(?i)\b(?:this|that|such)\s+(?P<title>%s)\b'),
    )
    for rule, reading, score, shape in passes:
        for cls in classes:
            if rule not in cls.rules:
                continue
            pattern = re.compile(shape % _forms(cls))
            for match in pattern.finditer(text):
                add(match, reading, score, rule, cls)
    found.sort(key=lambda phrase: (phrase.start, phrase.end))
    return found


def embody(mention):
    """An instance of the registered class, or of the base class for the frame."""
    model = _model(mention)
    body = model()
    body.observed = mention.text
    body.kind = mention.kind
    body.code = mention.code
    body.relations = []
    body.citations = []
    body.annotations = []
    return body


def parse_sentence(text, previous=None):
    """Parse one sentence. Duties with no new name attach to ``previous``."""
    mentions = find_mentions(text)
    subjects = [embody(mention) for mention in mentions]
    relations = find_relations(text)
    enactments = find_enactments(text)
    target = subjects[-1] if subjects else previous
    if target is not None:
        target.relations.extend(relations)
        target.relations.extend(enactments)
    citations = find_citations(text)
    notes = annotate(text)
    if target is not None:
        target.citations.extend(citations)
        target.annotations.extend(notes)
    parts = breakdown(text)
    for part in parts:
        part.notes = [note for note in notes if part.start <= note.start < part.end]
    return Sentence(text, subjects, find_clauses(text), citations, notes, compose(text), parts)


def _jurisdiction(body):
    if getattr(body, 'code', None):
        return body.code
    model = type(body)
    if isinstance(getattr(model, 'parent', None), str):
        return model.parent
    government = getattr(model, 'government', None)
    if government is not None:
        try:
            return government()
        except TypeError:
            return None
    region = getattr(model, 'region', None)
    if region is not None:
        try:
            return region()
        except TypeError:
            return None
    return None


def _fact(item):
    if hasattr(item, 'relation'):
        return item.relation.value, item.text
    return item.name, item.text


_PIN_SCHEMA = """
CREATE TABLE IF NOT EXISTS pin (
    citation TEXT NOT NULL,
    model TEXT NOT NULL,
    kind TEXT NOT NULL,
    jurisdiction TEXT,
    fact TEXT NOT NULL,
    detail TEXT,
    sentence TEXT,
    UNIQUE (citation, model, fact, detail)
);
"""


def pins_path(root=None):
    """SQLite file of jurisdiction and delegation pins."""
    base = data_dir() if root is None else root
    return os.path.join(str(base), 'pins.sqlite')


def pin(reading, citation, path=None):
    """Store each subject's jurisdiction and its duty or enactment frames.

    The same citation and model are replaced, so a reindex does not
    duplicate the pin.
    """
    destination = path or pins_path()
    ensure_dir(os.path.dirname(destination) or '.')
    connection = sqlite3.connect(destination)
    try:
        connection.executescript(_PIN_SCHEMA)
        for sentence in reading.sentences:
            for body in sentence.subjects:
                model = type(body).__name__
                connection.execute(
                    'DELETE FROM pin WHERE citation = ? AND model = ?',
                    (citation, model),
                )
                rows = [('jurisdiction', _jurisdiction(body))]
                rows.extend(_fact(item) for item in body.relations)
                rows.extend(('authority', point.text) for point in body.citations)
                rows.extend(
                    (note.note.value, note.text) for note in getattr(body, 'annotations', ())
                    if note.note.value != 'citation'
                )
                for fact, detail in rows:
                    connection.execute(
                        'INSERT OR REPLACE INTO pin'
                        ' (citation, model, kind, jurisdiction, fact, detail, sentence)'
                        ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (
                            citation, model, body.kind.value, _jurisdiction(body),
                            fact, detail, sentence.text,
                        ),
                    )
        connection.commit()
    finally:
        connection.close()
    return destination


def pins(citation=None, model=None, fact=None, path=None):
    """Return stored pins. Filter by citation, class name, or fact."""
    destination = path or pins_path()
    if not os.path.isfile(destination):
        return []
    connection = sqlite3.connect(destination)
    connection.row_factory = sqlite3.Row
    try:
        query = 'SELECT citation, model, kind, jurisdiction, fact, detail, sentence FROM pin WHERE 1 = 1'
        values = []
        if citation:
            query += ' AND citation = ?'
            values.append(citation)
        if model:
            query += ' AND model = ?'
            values.append(model)
        if fact:
            query += ' AND fact = ?'
            values.append(fact)
        query += ' ORDER BY citation, model, fact'
        return [dict(row) for row in connection.execute(query, values)]
    finally:
        connection.close()


def analyze(text):
    """Split ``text`` into sentences and bind each entity to a class instance."""
    previous = None
    parsed = []
    for piece in split_sentences(text):
        sentence = parse_sentence(piece, previous)
        parsed.append(sentence)
        if sentence.subjects:
            previous = sentence.subjects[-1]
    return Reading(parsed)
