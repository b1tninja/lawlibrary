"""Every surface a parser records on one text, as spans a client can draw.

A span is a layer, a kind, and two offsets. The layers are the records the
library already keeps: `Note` from `annotate`, `Canon` from `find_signals`,
`Clause` from `find_clauses`, `Kind` and `Relation` from `mentions`, a short
form from `abbreviations`, and the word classes `consider` says apply to the
open book. Spans overlap and nest, because the readings do: `shall` inside a
definition inside a subdivision is three spans, not one.

Nothing here opens the index and nothing composes a sentence. `layers` takes
words that were already looked up.
"""

import enum


class Layer(enum.Enum):
    """Which parser recorded the span. The value is the word a file may store."""

    NOTE = 'note'
    CANON = 'canon'
    CLAUSE = 'clause'
    MENTION = 'mention'
    RELATION = 'relation'
    NEEDLE = 'needle'
    ABBREVIATION = 'abbreviation'


class Span:
    """One reading on a slice of the text.

    ``kind`` is the member inside that layer. ``target`` is what the reading
    points at: a citation, a name, or the surface word. ``reading`` is the
    sentence the record already carries, and is empty when it carries none.
    """

    def __init__(self, layer, kind, start, end, text, target='', reading='', detail=None):
        self.layer = layer
        self.kind = kind
        self.start = start
        self.end = end
        self.text = text
        self.target = target or ''
        self.reading = reading or ''
        self.detail = detail or {}

    def __repr__(self):
        return 'Span(%s, %s, %s, %s)' % (self.layer.value, self.kind, self.start, self.end)


def _notes(text, context=None):
    from citations import annotate
    found = []
    for note in annotate(text, context):
        cite = getattr(note, 'cite', None)
        join = getattr(note, 'join', None)
        found.append(Span(
            Layer.NOTE,
            getattr(note.note, 'value', note.note),
            note.start, note.end, note.text,
            target=note.target or '',
            detail={
                'cite': getattr(cite, 'value', cite) or '',
                'join': getattr(join, 'value', join) or '',
                'guide': getattr(note.guide, 'value', note.guide) or '',
            },
        ))
    return found


def _statutes(text, code=None):
    """Where a statute pointer sits, and the book it names.

    ``annotate`` keeps the citation it can see. When the book is named beside
    the number, as in ``Section 7280 of the Revenue and Taxation Code``, the
    pointer that carries the book is the link, so the two are matched here.
    """
    from structure import find_links
    rows = []
    folded = (text or '').lower()
    cursor = {}
    for link in find_links(text, here=code):
        if link.kind != 'statute' or not link.section or link.code is None:
            continue
        words = link.text.lower()
        start = folded.find(words, cursor.get(words, 0))
        if start < 0:
            start = folded.find(words)
        if start < 0:
            continue
        cursor[words] = start + len(words)
        rows.append((start, start + len(link.text), getattr(link.code, 'value', link.code), link.section))
    return rows


def _resolve(text, spans, code=None):
    """Give a bare section number the book the sentence named."""
    rows = _statutes(text, code)
    if not rows:
        return spans
    for span in spans:
        if span.layer is not Layer.NOTE or span.kind not in ('citation', 'cross_reference'):
            continue
        target = (span.target or '').strip()
        if not target or not target[0].isdigit():
            continue
        for start, end, book, section in rows:
            if span.start >= start and span.end <= end and target.split()[0] == section:
                span.target = '%s %s' % (book, section)
                span.detail['book'] = book
                break
    return spans


def _canons(text):
    from canons import find_signals
    return [
        Span(
            Layer.CANON, signal.canon.value, signal.start, signal.end,
            signal.text, target=signal.text, reading=signal.reading,
        )
        for signal in find_signals(text)
    ]


def _clauses(text):
    from lexical import find_clauses
    return [
        Span(Layer.CLAUSE, mark.clause.value, mark.start, mark.end, mark.text)
        for mark in find_clauses(text)
    ]


def _mentions(text):
    from mentions import find_mentions
    return [
        Span(
            Layer.MENTION, mention.kind.value, mention.start, mention.end,
            mention.text, target=mention.name,
            detail={'government': mention.code or ''},
        )
        for mention in find_mentions(text)
    ]


def _relations(text):
    from mentions import find_relations
    return [
        Span(Layer.RELATION, tie.relation.value, tie.start, tie.end, tie.text)
        for tie in find_relations(text)
    ]


def _readings(code, shelf):
    """The reading each word class carries, by class name."""
    from needles import consider
    return {cls.__name__: getattr(cls, 'reading', '') for cls in consider(code, shelf)}


def _needles(text, code=None, shelf=None):
    from needles import occurrences
    said = _readings(code, shelf)
    return [
        Span(
            Layer.NEEDLE, row['class'], row['start'], row['end'],
            text[row['start']:row['end']],
            target=row['form'],
            reading=said.get(row['class'], ''),
        )
        for row in occurrences(text, code=code, shelf=shelf)
    ]


def _abbreviations(text):
    from mentions import abbreviations
    return [
        Span(
            Layer.ABBREVIATION, 'short_form', short.start, short.end,
            text[short.start:short.end], target=short.name,
            detail={'introduced': bool(short.introduction)},
        )
        for short in abbreviations(text)
    ]


_READERS = (
    (Layer.NOTE, _notes),
    (Layer.CANON, _canons),
    (Layer.CLAUSE, _clauses),
    (Layer.MENTION, _mentions),
    (Layer.RELATION, _relations),
    (Layer.ABBREVIATION, _abbreviations),
)


def layers(text, code=None, shelf=None, context=None, only=None):
    """Every span on ``text``, in reading order.

    ``code`` is the open book, which decides the word classes. ``only`` is a
    set of ``Layer`` members when a caller wants one surface. A longer span
    sorts before a shorter one that starts with it, so a client can nest them
    in one pass.
    """
    if not text:
        return ()
    wanted = None if only is None else {
        member if isinstance(member, Layer) else Layer(member) for member in only
    }
    found = []
    for layer, reader in _READERS:
        if wanted is not None and layer not in wanted:
            continue
        found.extend(_notes(text, context) if layer is Layer.NOTE else reader(text))
    if wanted is None or Layer.NEEDLE in wanted:
        found.extend(_needles(text, code, shelf))
    if wanted is None or Layer.NOTE in wanted:
        _resolve(text, found, code)
    found.sort(key=lambda span: (span.start, -span.end, span.layer.value, span.kind))
    return tuple(found)


def counts(spans):
    """How many spans each layer holds, then each kind inside it."""
    tally = {}
    for span in spans:
        inside = tally.setdefault(span.layer.value, {})
        inside[span.kind] = inside.get(span.kind, 0) + 1
    return tally
