"""Mark the words a canon of construction tells a reader to weigh.

Each hit is a phrase and the reading that phrase supports. A second phrase
in the same sentence can support a different reading. The marker does not
decide which reading wins. A test can show both.
"""

import enum
import re

from needles import Definition, Modal


class Canon(enum.Enum):
    """A reading the words support. The value is the string."""

    MANDATORY = 'mandatory'
    PERMISSIVE = 'permissive'
    CLOSED_SET = 'closed_set'
    OPEN_SET = 'open_set'
    EJUSDEM_GENERIS = 'ejusdem_generis'
    EXPRESSIO_UNIUS = 'expressio_unius'
    NOSCITUR = 'noscitur'
    CONJUNCTION = 'conjunction'
    DISJUNCTION = 'disjunction'
    PROVISO = 'proviso'
    EXCEPTION = 'exception'
    LAST_ANTECEDENT = 'last_antecedent'
    SERIES_QUALIFIER = 'series_qualifier'
    GENERAL = 'general'
    SPECIFIC = 'specific'
    SURPLUSAGE = 'surplusage'
    OFFICE = 'office'
    UNIT = 'unit'


class Signal:
    """One canon-bearing phrase."""

    def __init__(self, canon, start, end, text, reading):
        self.canon = canon
        self.start = start
        self.end = end
        self.text = text
        self.reading = reading

    def __repr__(self):
        return 'Signal(%s, %r)' % (self.canon.value, self.text)


_SIGNALS = (
    (Canon.MANDATORY, Modal.readings['shall'], re.compile(r'(?i)\b%s\b' % Modal.forms[0])),
    (Canon.PERMISSIVE, Modal.readings['may'], re.compile(
        r'(?i)(?<!as the case )\b%s\b(?!\s+not\b)' % Modal.forms[1]
    )),
    (Canon.MANDATORY, Modal.readings['may not'], re.compile(r'(?i)\b%s\b' % re.escape(Modal.forms[2]))),
    (Canon.CLOSED_SET, Definition.reading, re.compile(r'(?i)\b%s\b' % Definition.forms[0])),
    (Canon.OPEN_SET, Definition.reading, re.compile(
        r'(?i)\b%s\b(?:\s+but not limited to)?' % 'includ(?:e|es|ed|ing)'
    )),
    (Canon.EJUSDEM_GENERIS, 'The general words take the kind of the list.', re.compile(
        r'(?i)\bor (?:any )?other\b[^.]{0,40}'
    )),
    (Canon.EXPRESSIO_UNIUS, 'What is named is covered. What is omitted is not.', re.compile(
        r'(?i)\bonly\b'
    )),
    (Canon.NOSCITUR, 'The word takes its color from the words beside it.', re.compile(
        r'(?i)\b(?:and|or)\b'
    )),
    (Canon.CONJUNCTION, 'Every item in the pair is required.', re.compile(r'(?i)\band\b')),
    (Canon.DISJUNCTION, 'Any one item is enough.', re.compile(r'(?i)\bor\b')),
    (Canon.PROVISO, 'What follows qualifies what came before.', re.compile(
        r'(?i)\bprovided,? however, that\b|\bprovided that\b'
    )),
    (Canon.EXCEPTION, 'The named case is outside the rule.', re.compile(
        r'(?i)\bexcept\b|\bunless\b'
    )),
    (Canon.LAST_ANTECEDENT, 'A trailing modifier attaches to the nearest noun.', re.compile(
        r'(?i),?\s+which\b'
    )),
    (Canon.SERIES_QUALIFIER, 'A modifier after a list can apply to every item in it.', re.compile(
        r'(?i)\b(?:,|and|or)\s+[a-z][^.]{0,30}\b(?:that|who)\b'
    )),
    (Canon.SPECIFIC, 'A named case controls a general rule on the same subject.', re.compile(
        r'(?i)\bnotwithstanding any other\b[^.]{0,40}'
    )),
    (Canon.GENERAL, 'A broad duty yields where a specific rule speaks.', re.compile(
        r'(?i)\bany other provision\b|\bany other law\b'
    )),
    (Canon.SURPLUSAGE, 'A repeated word is there to do work.', re.compile(
        r'(?i)\beach and every\b|\bnull and void\b|\bforce and effect\b'
    )),
)


_OFFICE_READING = 'Of, or a title that closes the name, marks an office.'
_UNIT_READING = 'A number, or this before the title, marks a unit of the code.'


class Specimen:
    """One citation that shows a reading. Add a row when a sentence teaches a distinction."""

    def __init__(self, code, number, canon, text):
        self.code = code
        self.number = number
        self.canon = canon
        self.text = text


def _specimens():
    """Citations stored on the noun classes that have a rule worth checking."""
    from needles import nouns
    rows = []
    for cls in nouns():
        for code, number, reading, words in cls.examples:
            canon = Canon.OFFICE if reading == 'office' else Canon.UNIT
            rows.append(Specimen(code, number, canon, words))
    return tuple(rows)


SPECIMENS = _specimens()


def find_signals(text, canon=None):
    """Return every canon-bearing phrase in ``text``, in order."""
    if not text:
        return []
    found = []
    for kind, reading, pattern in _SIGNALS:
        if canon is not None and kind is not canon:
            continue
        for match in pattern.finditer(text):
            found.append(Signal(kind, match.start(), match.end(), match.group(0), reading))
    if canon is None or canon in (Canon.OFFICE, Canon.UNIT):
        from analysis import compose
        for phrase in compose(text):
            kind = Canon.OFFICE if phrase.reading == 'office' else Canon.UNIT
            if canon is not None and kind is not canon:
                continue
            reading = _OFFICE_READING if kind is Canon.OFFICE else _UNIT_READING
            found.append(Signal(kind, phrase.start, phrase.end, phrase.text, reading))
    found.sort(key=lambda signal: (signal.start, signal.end))
    return found


def readings(text):
    """The distinct canons the text supports. Two entries are a difference of interpretation."""
    return list(dict.fromkeys(signal.canon for signal in find_signals(text)))


class Ambiguity:
    """Two canons on the same sentence that pull in different directions.

    The parser records both. It does not choose.
    """

    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.canons = (left.canon, right.canon)

    def __repr__(self):
        return 'Ambiguity(%s, %s)' % (self.left.canon.value, self.right.canon.value)


# Pairs that cannot both be the reading of one sentence.
_TENSIONS = (
    frozenset({Canon.OPEN_SET, Canon.EJUSDEM_GENERIS}),
    frozenset({Canon.OPEN_SET, Canon.EXPRESSIO_UNIUS}),
    frozenset({Canon.CLOSED_SET, Canon.OPEN_SET}),
    frozenset({Canon.MANDATORY, Canon.PERMISSIVE}),
    frozenset({Canon.GENERAL, Canon.SPECIFIC}),
    frozenset({Canon.LAST_ANTECEDENT, Canon.SERIES_QUALIFIER}),
    frozenset({Canon.CONJUNCTION, Canon.DISJUNCTION}),
)


def ambiguities(text):
    """Canons in one sentence that disagree. A period starts a new sentence."""
    signals = find_signals(text)
    found = []
    seen = set()
    for index, left in enumerate(signals):
        for right in signals[index + 1:]:
            pair = frozenset({left.canon, right.canon})
            if pair not in _TENSIONS or pair in seen:
                continue
            between = text[left.end:right.start]
            if '.' in between:
                continue
            seen.add(pair)
            found.append(Ambiguity(left, right))
    return found
