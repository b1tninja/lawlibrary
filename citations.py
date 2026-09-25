"""Find statute citations inside a sentence.

A single section sign (``§``) introduces one section. A double sign (``§§``)
introduces more than one: a range when the numbers are joined by a dash or
by ``to``, and a series when they are separated by a comma, a semicolon,
``and``, ``or``, or ``and/or``. A series iterates one section at a time. The words
``section`` and ``sections`` are the same frames without the sign.

A point of authority is the citation a writer offers for a statement. A
signal such as ``see`` or ``cf.`` introduces it. The signal is not the
authority. California Rules of Court, rule 1.200, requires filed documents
to follow either the California Style Manual or The Bluebook, used
consistently. Both use the section sign this way. The Style Manual text is
not free on the courts site, so this parser follows the sign, not a
quotation from that book.
"""

import contextvars
import enum
import re
from contextlib import contextmanager

from needles import pattern as word_pattern


class Cite(enum.Enum):
    """How many sections the sign introduces. The value is the string."""

    SECTION = 'section'
    RANGE = 'range'
    SERIES = 'series'


class Join(enum.Enum):
    """How the items of a series are joined. The value is the string."""

    CONJUNCTION = 'conjunction'
    DISJUNCTION = 'disjunction'
    BOTH = 'both'


class Point:
    """One citation span. ``signal`` is set when a point-of-authority word precedes it.

    A series is iterable. Each item is one section, and ``join`` says whether
    ``and``, ``or``, or ``and/or`` holds the list together.
    """

    def __init__(self, cite, start, end, text, numbers, code=None, signal=None, join=None, spans=()):
        self.cite = cite
        self.start = start
        self.end = end
        self.text = text
        self.numbers = tuple(numbers)
        self.code = code
        self.signal = signal
        self.join = join
        self.spans = tuple(spans)

    def __repr__(self):
        return 'Point(%s, %s, %s)' % (self.cite.value, self.code, self.numbers)

    def __iter__(self):
        if self.cite is not Cite.SERIES or len(self.numbers) < 2:
            yield self
            return
        spans = self.spans or ((self.start, self.end),) * len(self.numbers)
        for number, (start, end) in zip(self.numbers, spans):
            yield Point(
                Cite.SECTION, start, end, number, (number,),
                self.code, self.signal, self.join,
            )

    def citation(self, here=None):
        """The same pointer as a ``Citation`` chain. A point with no book is none."""
        from apa import Code
        from places import Citation
        code = here if isinstance(here, Code) else None
        raw = self.code if isinstance(self.code, str) else ''
        if isinstance(self.code, Code):
            code = self.code
        elif raw:
            for candidate in sorted(Code, key=lambda item: len(item.title), reverse=True):
                if raw.lower().startswith(candidate.title.lower()) or raw.upper() == candidate.value:
                    code = candidate
                    break
        if code is None:
            return None
        cited = Citation(code)
        if self.cite is Cite.RANGE and len(self.numbers) >= 2:
            return cited.section(self.numbers[0]).through(self.numbers[-1])
        if self.cite is Cite.SERIES and len(self.numbers) >= 2:
            return cited.section(self.numbers[0]).and_(*self.numbers[1:])
        if not self.numbers:
            return cited
        cited = cited.section(self.numbers[0])
        if re.search(r'(?i)\bet\s+seq', self.text or ''):
            return cited.commencing()
        return cited


_NUM = r'\d+(?:\.\d+)*(?:[a-z])?(?:\([a-z0-9]+\))*'
_SEP = r'(?:;\s*(?:and/or|and|or)|;|,\s*(?:and/or|and|or)|,|and/or|and|or|to|through|[-–—])'
_CODE = (
    r'(?:'
    r'[A-Z][A-Za-z.]*(?:\s+(?:&|[A-Z][A-Za-z.]*)){0,5}\s+Code\s+'
    r'|Code\s+of\s+(?:[A-Z][A-Za-z.]*\s+){1,5}'
    r')?'
)
_SIGNALS = (
    'see also', 'but see', 'see', 'cf.', 'cf', 'accord', 'contra', 'e.g.',
)

_DOUBLE = re.compile(
    r'(?P<code>%s)§§\s*(?P<body>%s(?:\s*%s\s*%s)+)'
    r'(?:\s*et seq\.?)?' % (_CODE, _NUM, _SEP, _NUM),
)
_SINGLE = re.compile(
    r'(?P<code>%s)§(?!§)\s*(?P<num>%s)(?!\s*et seq)' % (_CODE, _NUM),
)
_WORDS = re.compile(
    r'(?P<code>%s)(?i:sections?)\s+(?P<body>%s(?:\s*%s\s*%s)*)'
    % (_CODE, _NUM, _SEP, _NUM),
)


def _numbers(body):
    return re.findall(r'\d[\d.]*(?:[a-z])?(?!\))', body)


def _cite_for(body):
    if re.search(r'[-–—]|\bto\b|\bthrough\b', body) and ',' not in body and ';' not in body:
        return Cite.RANGE
    if ',' in body or ';' in body or re.search(r'\band\b|\bor\b', body):
        return Cite.SERIES
    return Cite.SECTION


def _join(body):
    """The coordinating word in a series. ``and/or`` keeps both readings."""
    if re.search(r'(?i)\band/or\b', body or ''):
        return Join.BOTH
    conjunction = re.search(r'(?i)\band\b', body or '')
    disjunction = re.search(r'(?i)\bor\b', body or '')
    if conjunction and disjunction:
        return Join.BOTH
    if conjunction:
        return Join.CONJUNCTION
    if disjunction:
        return Join.DISJUNCTION
    return None


def _member_spans(match, numbers):
    """Where each number sits inside the citation match."""
    body = match.group(0)
    origin = match.start()
    spans = []
    cursor = 0
    for number in numbers:
        found = re.compile(
            r'(?<![\d.])' + re.escape(number) + r'(?![\d.]|\.\d)'
        ).search(body, cursor)
        if found is None:
            spans.append((origin, match.end()))
            continue
        spans.append((origin + found.start(), origin + found.end()))
        cursor = found.end()
    return tuple(spans)


def _code(raw):
    text = (raw or '').strip(' ,')
    return text or None


def _signal(text, start):
    window = text[max(0, start - 80):start]
    lowered = window.lower()
    for signal in _SIGNALS:
        idx = lowered.rfind(signal)
        if idx < 0:
            continue
        after = window[idx + len(signal):]
        if re.fullmatch(r'[\sA-Za-z.&]*', after or ''):
            return signal.replace('.', '')
    return None


def find_citations(text):
    """Return every section citation in ``text``, double signs first."""
    if not text:
        return []
    spans = []
    found = []

    def take(match, cite, numbers, code):
        for start, end in spans:
            if match.start() < end and match.end() > start:
                return
        spans.append((match.start(), match.end()))
        sign_at = match.group(0).find('§')
        if sign_at < 0:
            sign_at = match.group(0).lower().find('section')
        if code:
            for signal in _SIGNALS:
                if code.lower().startswith(signal):
                    code = code[len(signal):].strip()
                    break
        found.append(Point(
            cite, match.start(), match.end(), match.group(0).strip(),
            numbers, code, _signal(text, match.start() + max(sign_at, 0)),
            _join(match.group(0)) if cite is Cite.SERIES else None,
            _member_spans(match, numbers) if cite is Cite.SERIES else (),
        ))

    for match in _DOUBLE.finditer(text):
        body = match.group('body')
        take(match, _cite_for(body), _numbers(body), _code(match.group('code')))
    for match in _SINGLE.finditer(text):
        take(match, Cite.SECTION, _numbers(match.group('num')), _code(match.group('code')))
    for match in _WORDS.finditer(text):
        body = match.group('body')
        take(match, _cite_for(body), _numbers(body), _code(match.group('code')))
    found.sort(key=lambda point: point.start)
    return found


class Note(enum.Enum):
    """What kind of reference an annotation is. The value is the string."""

    CITATION = 'citation'
    CROSS_REFERENCE = 'cross_reference'
    NAMED_ACT = 'named_act'
    SHORT_FORM = 'short_form'
    AMOUNT = 'amount'
    PERIOD = 'period'
    DATE = 'date'
    SESSION = 'session'
    CUT = 'cut'
    CASE = 'case'


class Annotation:
    """A citation or a reference to mark on the text."""

    def __init__(self, note, start, end, text, target=None, guide=None, cite=None, join=None):
        self.note = note
        self.start = start
        self.end = end
        self.text = text
        self.target = target
        self.guide = guide
        self.cite = cite
        self.join = join

    def __repr__(self):
        return 'Annotation(%s, %r)' % (self.note.value, self.text)


_CITED_AS = re.compile(
    r'(?i)\b(?:shall be known,? and may be cited,? as|may be cited as|shall be known as)\s+the\s+'
    r'(?P<title>(?:[A-Z][A-Za-z0-9-]*\s+){0,12}Act)\b'
)
_REFERENCES = (
    (Note.CROSS_REFERENCE, re.compile(r'(?i)\bcommencing with Section\s+\d[\d.]*')),
    (Note.CROSS_REFERENCE, word_pattern(internal=True, prefix=r'\bthis ', suffix=r'\b')),
    (Note.NAMED_ACT, re.compile(r'\bAdministrative Procedure Act\b')),
    (Note.SHORT_FORM, re.compile(r'(?i)\bet seq\.?|\bsupra\b|\bid\.|\bas amended\b')),
    (Note.CROSS_REFERENCE, re.compile(r'(?i)\bthe following\b')),
)


def _overlaps(start, end, spans):
    return any(start < stop and end > begin for begin, stop in spans)


_document = contextvars.ContextVar('document', default=None)


class Context:
    """The book and section being read. Local words resolve against it."""

    def __init__(self, code, section=None, books=None):
        self.code = code
        self.section = section
        self.books = books or {}


def _compact(text):
    text = (text or '').upper().replace('.', '').replace('&', ' AND ')
    text = re.sub(r'\bAND\b', ' ', text)
    text = re.sub(r'(?i)^CALIFORNIA\s+', '', text, count=1)
    return re.sub(r'\s+', ' ', text).strip()


def resolve_book(token, books):
    """Map a title or a shorthand to the code abbreviation in ``books``.

    ``books`` is the index map, such as ``{"CIV": "Civil Code - CIV"}``.
    ``Civil Code``, ``Civ. Code``, ``CIV``, and ``California Civil Code``
    are the same book.
    """
    if not token or not books:
        return None
    key = _compact(token)
    if key in books:
        return key
    for abbr, title in books.items():
        base = re.sub(r'\s+-\s+[A-Z0-9]+\s*$', '', title)
        full = _compact(base)
        if key == full or key == abbr:
            return abbr
        full_words = full.split()
        key_words = key.split()
        if (
            full_words
            and key_words
            and full_words[-1] == 'CODE'
            and key_words[-1] == 'CODE'
            and len(full_words) == len(key_words)
            and all(word.startswith(short) and len(short) >= 3 for word, short in zip(full_words[:-1], key_words[:-1]))
        ):
            return abbr
    return None


@contextmanager
def document(code, section=None, books=None):
    """Read the following text as part of this book and section."""
    catalog = books or {}
    resolved = resolve_book(code, catalog) or code
    ctx = Context(resolved, section, catalog)
    token = _document.set(ctx)
    try:
        yield ctx
    finally:
        _document.reset(token)


def _active(context):
    return context if context is not None else _document.get()


_COUNTS = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'fifteen': 15, 'thirty': 30, 'sixty': 60, 'ninety': 90,
}
_FIGURE = r'\d{1,3}(?:,\d{3})+|\d+'
_CENTS = r'\.\d+'
_NUMWORD = (
    r'(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
    r'thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|'
    r'forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion)'
)
_SPELLED = r'%s(?:-%s)?(?:\s+(?:and\s+)?%s(?:-%s)?){0,8}' % (_NUMWORD, _NUMWORD, _NUMWORD, _NUMWORD)
_AMOUNT = re.compile(
    r'(?i)(?P<words>%s)\s+dollars\s*\(\s*\$\s*(?:(?P<num>%s)(?P<cents>%s)?|(?P<words_bare>%s))\s*\)'
    r'|\$\s*(?:(?P<sign>%s)(?P<sign_cents>%s)?|(?P<bare>%s))'
    r'|\b(?P<plain>%s)(?P<plain_cents>%s)?\s+dollars\b'
    % (_SPELLED, _FIGURE, _CENTS, _CENTS, _FIGURE, _CENTS, _CENTS, _FIGURE, _CENTS)
)
_PERIOD = re.compile(
    r'(?i)(?:(?P<lead>prior to|within|before|after|until|from)\s+)?'
    r'(?<![\d,])(?P<count>\d{1,3}(?:,\d{3})+|\d+|one|two|three|four|five|six|seven|eight|nine|ten|fifteen|thirty|sixty|ninety)'
    r'(?:\s+(?P<qual>calendar|legislative|business|working|court))?'
    r'\s+(?P<unit>days?|months?|years?)'
    r'(?:\s+(?P<trail>prior to|after|before|until|from|prior))?'
)


class Quantity(enum.Enum):
    """A measured element of a clause. The value is the string."""

    MONETARY = 'monetary'
    DURATION = 'duration'
    ABSOLUTE = 'absolute'


class Convention(enum.Enum):
    """How a measured value is printed. The value is the string.

    ``USD`` is ISO 4217. The minor unit is cents, exponent 2. ``GROUPED`` is a
    thousands comma. ``DECIMAL`` is a radix point. ``MONTH_DAY_YEAR`` is the
    California printed day. ``ISO_8601`` is ``YYYY-MM-DD``. ``NUMERIC_MDY`` is
    ``M/D/YYYY``. ``YEAR``, ``MONTH``, and ``DAY`` are the period designators.
    """

    USD = 'usd'
    GROUPED = 'grouped'
    DECIMAL = 'decimal'
    INTEGER = 'integer'
    SPELLED = 'spelled'
    MONTH_DAY_YEAR = 'month_day_year'
    ISO_8601 = 'iso_8601'
    NUMERIC_MDY = 'numeric_mdy'
    YEAR = 'year'
    MONTH = 'month'
    DAY = 'day'


_MONTHS = (
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
)
_DATE = re.compile(
    r'(?i)\b(?P<month>%s)\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4})\b' % '|'.join(_MONTHS)
)
_ISO_DATE = re.compile(r'\b(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\b')
_MDY_DATE = re.compile(r'\b(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})\b')
_DESIGNATOR = {'year': Convention.YEAR, 'month': Convention.MONTH, 'day': Convention.DAY}


def _dollars(raw):
    return re.sub(r'[$,\s]', '', raw or '').split('.')[0]


def _money_conventions(match, raw, fraction):
    """USD plus the number form that was printed."""
    found = [Convention.USD]
    if match.group('words'):
        found.append(Convention.SPELLED)
    if ',' in (raw or ''):
        found.append(Convention.GROUPED)
    if fraction:
        found.append(Convention.DECIMAL)
    else:
        found.append(Convention.INTEGER)
    return tuple(found)


def _fraction(raw):
    """Digits after the point. One digit is tenths, so ``5`` is ``50``."""
    digits = (raw or '').lstrip('.')
    if not digits or set(digits) == {'0'}:
        return 0, None
    if len(digits) == 1:
        digits = digits + '0'
    return int(digits[:2]), digits


def _under_hundred(number):
    ones = (
        '', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
        'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
        'seventeen', 'eighteen', 'nineteen',
    )
    tens = ('', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety')
    if number < 20:
        return ones[number]
    ten, rest = divmod(number, 10)
    if rest:
        return '%s-%s' % (tens[ten], ones[rest])
    return tens[ten]


def _chunk(number):
    """A count below one thousand, in words."""
    if number >= 100:
        hundreds, rest = divmod(number, 100)
        if rest:
            return '%s hundred %s' % (_under_hundred(hundreds), _under_hundred(rest))
        return '%s hundred' % _under_hundred(hundreds)
    return _under_hundred(number)


def _words(number):
    """The spelled dollars used beside the parenthetical sign."""
    if number == 0:
        return 'zero'
    parts = []
    for name, scale in (('million', 1000000), ('thousand', 1000)):
        count, number = divmod(number, scale)
        if count:
            parts.append('%s %s' % (_chunk(count), name))
    if number:
        parts.append(_chunk(number))
    return ' '.join(parts)


class Monetary:
    """A dollar amount. ``reference`` prints the spelled sum and the parenthetical sign."""

    kind = Quantity.MONETARY

    def __init__(self, dollars, cents=0, fraction=None, conventions=()):
        self.dollars = int(dollars)
        self.cents = int(cents)
        self.fraction = fraction
        self.conventions = tuple(conventions)

    def convention(self):
        """The currency and the number form. USD is the statute dollar."""
        return self.conventions

    def reference(self):
        if self.fraction:
            return '$%d.%s' % (self.dollars, self.fraction)
        sign = '$%s' % format(self.dollars, ',')
        return '%s dollars (%s)' % (_words(self.dollars), sign)

    def target(self):
        if self.fraction:
            return '%d.%s' % (self.dollars, self.fraction)
        return str(self.dollars)

    def shape(self):
        """The countable phrase. The figure is the classifier."""
        return self.kind.value

    @classmethod
    def parse(cls, text):
        match = _AMOUNT.fullmatch((text or '').strip())
        if match is None:
            return None
        raw = match.group('num') or match.group('sign') or match.group('plain') or '0'
        cents = (
            match.group('cents') or match.group('sign_cents') or match.group('plain_cents')
            or match.group('words_bare') or match.group('bare') or ''
        )
        hundredths, fraction = _fraction(cents)
        return cls(_dollars(raw), hundredths, fraction, _money_conventions(match, raw, fraction))


class Duration:
    """A relative period. The count runs from an event named by from, prior, within, or after."""

    kind = Quantity.DURATION

    def __init__(self, count, unit, qualifier=None, lead=None, trail=None, antecedent=None):
        self.count = int(count)
        self.unit = unit
        self.qualifier = qualifier
        self.lead = lead
        self.trail = trail
        self.antecedent = antecedent

    def reference(self):
        unit = self.unit if self.count == 1 else self.unit + 's'
        body = '%s %s %s' % (self.count, self.qualifier, unit) if self.qualifier else '%s %s' % (self.count, unit)
        if self.lead:
            body = '%s %s' % (self.lead, body)
        if self.trail:
            body = '%s %s' % (body, self.trail)
        if self.antecedent:
            body = '%s %s' % (body, self.antecedent)
        return body

    def target(self):
        unit = '%s %s %s' % (self.count, self.qualifier, self.unit) if self.qualifier else '%s %s' % (self.count, self.unit)
        if self.lead:
            unit = '%s %s' % (self.lead, unit)
        if self.trail:
            unit = '%s %s' % (unit, self.trail)
        return unit

    def convention(self):
        """The unit as a designator. The phrase stays the printed words."""
        return _DESIGNATOR[self.unit]

    def shape(self):
        """The countable phrase. The count is the classifier. The other words stay."""
        token = self.kind.value
        body = '%s %s %s' % (token, self.qualifier, self.unit) if self.qualifier else '%s %s' % (token, self.unit)
        if self.lead:
            body = '%s %s' % (self.lead, body)
        if self.trail:
            body = '%s %s' % (body, self.trail)
        return body

    @classmethod
    def parse(cls, text):
        match = _PERIOD.fullmatch((text or '').strip())
        if match is None:
            return None
        raw = match.group('count').lower()
        count = _COUNTS[raw] if raw in _COUNTS else int(raw.replace(',', ''))
        unit = match.group('unit').lower().rstrip('s')
        qual = match.group('qual')
        lead = match.group('lead')
        trail = match.group('trail')
        return cls(
            count, unit,
            qual.lower() if qual else None,
            lead.lower() if lead else None,
            trail.lower() if trail else None,
        )


_FORWARD = frozenset(('from', 'prior', 'prior to'))
_STOP = frozenset(('shall', 'may', 'must', 'and', 'or', 'provided', 'except'))


def _antecedent(text, end):
    """The noun phrase after from or prior. A miss is none."""
    match = re.match(
        r'(?i)\s+((?:the |a |an )?[a-z][a-z0-9-]*(?: (?:of |the |a |an )?[a-z][a-z0-9-]*){0,6})',
        text[end:],
    )
    if match is None:
        return None
    kept = []
    for word in match.group(1).split():
        if word.lower() in _STOP:
            break
        kept.append(word)
    phrase = ' '.join(kept).strip()
    return phrase or None


def _beside(text, start, end):
    """Up to three words before the span and two after it, inside the same sentence."""
    prior = text[:start]
    cut = max(prior.rfind(mark) for mark in '.!?;')
    prior = prior[cut + 1:]
    following = text[end:]
    stop = len(following)
    for mark in '.!?;':
        at = following.find(mark)
        if at >= 0:
            stop = min(stop, at)
    before = re.findall(r"[A-Za-z][A-Za-z'-]*", prior)
    after = re.findall(r"[A-Za-z][A-Za-z'-]*", following[:stop])
    return [word.casefold() for word in before[-3:]], [word.casefold() for word in after[:2]]


def frames(text):
    """The words around a quantity. The figure is its classifier.

    ``not more than $1,000`` and ``not more than $10,000`` are one expression.
    A citation number is left out. The stored target is unchanged.
    """
    found = []
    readers = {Note.AMOUNT: Monetary, Note.PERIOD: Duration, Note.DATE: Absolute}
    for note in annotate(text or ''):
        reader = readers.get(note.note)
        if reader is None:
            continue
        parsed = reader.parse(note.text)
        if parsed is None:
            continue
        before, after = _beside(text, note.start, note.end)
        found.append(' '.join(before + [parsed.shape()] + after))
    return found


_PLAIN = re.compile(r"\$?\d{1,3}(?:,\d{3})+(?:\.\d+)?|\$?\d+(?:\.\d+)?|[A-Za-z][A-Za-z'-]*")


def plain_tokens(text):
    """Printed words and figures, in order. A placeholder is not substituted."""
    return [token.casefold() for token in _PLAIN.findall(text or '')]


def marked_tokens(text):
    """Words in order. An annotated value is a placeholder, or the quantity type.

    A section number is ``{SECTION}``. A book is ``{CODE}``. A dollar amount is
    ``{AMOUNT}``. A calendar day is ``{YEAR}``. A period stays its type, such as
    ``within duration day``. A figure that is only a quantity is ``{QUANTITY}``.
    """
    text = text or ''
    spans = []
    for start, end, note, words, _target in find_measures(text):
        if note is Note.AMOUNT:
            tokens = ['{AMOUNT}']
        elif note is Note.DATE:
            tokens = ['{YEAR}']
        elif note is Note.PERIOD:
            parsed = Duration.parse(words)
            tokens = parsed.shape().split() if parsed else ['{QUANTITY}']
        else:
            continue
        spans.append((start, end, tokens))
    from structure import find_links
    occupied = [(start, end) for start, end, _tokens in spans]
    lowered = text.lower()
    for link in find_links(text):
        if link.kind == 'session':
            tokens = ['{YEAR}']
        elif link.kind == 'statute' and link.section:
            tokens = ['{SECTION}']
            if link.code:
                tokens.append('{CODE}')
            if re.match(r'(?i)sections?\b', link.text or ''):
                tokens.insert(0, 'section')
        else:
            continue
        needle = (link.text or '').lower()
        if not needle:
            continue
        start = lowered.find(needle)
        while start >= 0 and _overlaps(start, start + len(link.text), occupied):
            start = lowered.find(needle, start + 1)
        if start < 0:
            continue
        end = start + len(link.text)
        occupied.append((start, end))
        spans.append((start, end, tokens))
    spans.sort()
    pieces = []
    cursor = 0
    for start, end, tokens in spans:
        if start < cursor:
            continue
        pieces.extend(
            word.casefold() for word in re.findall(r"[A-Za-z][A-Za-z'-]*", text[cursor:start])
        )
        pieces.extend(tokens)
        cursor = max(cursor, end)
    pieces.extend(word.casefold() for word in re.findall(r"[A-Za-z][A-Za-z'-]*", text[cursor:]))
    return pieces


def measure_tokens(text):
    """Words in order. A quantity span is its shape, not the printed figure."""
    text = text or ''
    pieces = []
    cursor = 0
    readers = {Note.AMOUNT: Monetary, Note.PERIOD: Duration, Note.DATE: Absolute}
    for start, end, note, words, _target in find_measures(text):
        if start < cursor:
            continue
        pieces.extend(re.findall(r"[A-Za-z][A-Za-z'-]*", text[cursor:start]))
        parsed = readers[note].parse(words) if note in readers else None
        if parsed is not None:
            pieces.extend(parsed.shape().split())
        cursor = end
    pieces.extend(re.findall(r"[A-Za-z][A-Za-z'-]*", text[cursor:]))
    return [piece.casefold() for piece in pieces]


class Form:
    """One measured span and the conventions it was printed in."""

    def __init__(self, kind, conventions, target, text):
        self.kind = kind
        self.conventions = tuple(conventions)
        self.target = target
        self.text = text


def forms(text):
    """Each measured span, with its currency, number, or date convention."""
    found = []
    readers = {Note.AMOUNT: Monetary, Note.PERIOD: Duration, Note.DATE: Absolute}
    for _start, _end, note, words, target in find_measures(text or ''):
        parsed = readers[note].parse(words) if note in readers else None
        if parsed is None:
            continue
        conventions = parsed.convention()
        if not isinstance(conventions, tuple):
            conventions = (conventions,)
        found.append(Form(parsed.kind, conventions, target, words))
    return found


def find_durations(text):
    """Relative periods, with the antecedent when from or prior points forward."""
    found = []
    for match in _PERIOD.finditer(text or ''):
        period = Duration.parse(match.group(0))
        if period is None or period.trail not in _FORWARD:
            if period is not None:
                found.append(period)
            continue
        period.antecedent = _antecedent(text, match.end())
        found.append(period)
    return found


class Absolute:
    """A calendar day. It names a month, a day, and a year, and it does not run from another event."""

    kind = Quantity.ABSOLUTE

    def __init__(self, year, month, day, convention=None):
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)
        self._convention = convention or Convention.MONTH_DAY_YEAR

    def convention(self):
        """The printed date form. ``target`` stays ``YYYY-MM-DD``."""
        return self._convention

    def reference(self):
        return '%s %s, %s' % (_MONTHS[self.month - 1], self.day, self.year)

    def target(self):
        return '%04d-%02d-%02d' % (self.year, self.month, self.day)

    def shape(self):
        """The countable phrase. The calendar day is the classifier."""
        return self.kind.value

    @classmethod
    def parse(cls, text):
        text = (text or '').strip()
        named = _DATE.fullmatch(text)
        if named is not None:
            month = _MONTHS.index(named.group('month').title()) + 1
            return cls._calendar(named.group('year'), month, named.group('day'), Convention.MONTH_DAY_YEAR)
        iso = _ISO_DATE.fullmatch(text)
        if iso is not None:
            return cls._calendar(iso.group('year'), iso.group('month'), iso.group('day'), Convention.ISO_8601)
        numeric = _MDY_DATE.fullmatch(text)
        if numeric is not None:
            return cls._calendar(
                numeric.group('year'), numeric.group('month'), numeric.group('day'), Convention.NUMERIC_MDY,
            )
        return None

    @classmethod
    def _calendar(cls, year, month, day, convention):
        month = int(month)
        day = int(day)
        if month < 1 or month > 12 or day < 1 or day > 31:
            return None
        return cls(int(year), month, day, convention)


_UNIT_FWD = re.compile(
    r'(?i)(?P<gap>\s+)(?:(?P<qual>calendar|legislative|business|working|court)\s+)?'
    r'(?P<unit>days?|months?|years?)\b'
    r'(?P<trail>\s+(?:prior to|after|before|until|from|prior))?'
)
_LEAD_END = re.compile(r'(?i)(?:prior to|within|before|after|until|from)\s+$')
_SPELLED_TAIL = re.compile(r'(?i)(?P<words>%s)\s+dollars\s*\(\s*$' % _SPELLED)
_COUNT_WORDS = re.compile(
    r'(?i)(?<![A-Za-z])(?:one|two|three|four|five|six|seven|eight|nine|ten|fifteen|thirty|sixty|ninety)\b'
)
_NUMBER = re.compile(
    r'(?<![\d,])(?P<sign>\$\s*)?(?P<body>\d{1,3}(?:,\d{3})+|\d+)(?P<frac>\.\d+)?'
    r'|(?<![\d,])(?P<bare>\$\s*\.\d+)'
)


def _money_span(text, start, end):
    """A ``$`` figure. The spelled sum is included only when it sits against that sign."""
    prefix = text[max(0, start - 180):start]
    tail = None
    for hit in _SPELLED_TAIL.finditer(prefix):
        if hit.end() == len(prefix):
            tail = hit
    if tail is not None:
        spelled = start - (len(prefix) - tail.start())
        close = end + 1 if text[end:end + 1] == ')' else end
        words = text[spelled:close]
        if Monetary.parse(words) is not None:
            return spelled, close, words
    words = text[start:end]
    if Monetary.parse(words) is None:
        return None
    return start, end, words


def _period_span(text, start, end):
    """A figure or a short count word, classified by the unit that follows it."""
    fwd = _UNIT_FWD.match(text, end)
    if fwd is None:
        return None
    end = fwd.end()
    window = text[max(0, start - 16):start]
    lead = _LEAD_END.search(window)
    if lead is not None:
        start -= len(window) - lead.start()
    words = text[start:end]
    if Duration.parse(words) is None:
        return None
    return start, end, words


def find_measures(text):
    """One pass over figures. The marker beside the figure chooses the record.

    ``$`` or ``dollars`` is USD. ``day``, ``month``, and ``year`` are the
    period. A month name with a day and a year is the calendar date. A bare
    number, including a section number, is left out.
    """
    if not text:
        return []
    found = []
    occupied = []

    def take(start, end, note, words, parser, target):
        if _overlaps(start, end, occupied):
            return
        parsed = parser.parse(words)
        if parsed is None:
            return
        occupied.append((start, end))
        found.append((start, end, note, words.strip(), target(parsed)))

    for pattern in (_DATE, _ISO_DATE, _MDY_DATE):
        for match in pattern.finditer(text):
            take(match.start(), match.end(), Note.DATE, match.group(0), Absolute, lambda item: item.target())
    for match in _NUMBER.finditer(text):
        if match.group('sign') or match.group('bare'):
            span = _money_span(text, match.start(), match.end())
            if span is not None:
                take(span[0], span[1], Note.AMOUNT, span[2], Monetary, lambda item: item.target())
            continue
        span = _period_span(text, match.start(), match.end())
        if span is not None:
            take(span[0], span[1], Note.PERIOD, span[2], Duration, lambda item: item.target())
    for match in _COUNT_WORDS.finditer(text):
        span = _period_span(text, match.start(), match.end())
        if span is not None:
            take(span[0], span[1], Note.PERIOD, span[2], Duration, lambda item: item.target())
    found.sort(key=lambda item: (item[0], item[1]))
    return found


def _measure_notes(text, spans, guide):
    notes = []
    for start, end, note, words, target in find_measures(text):
        if _overlaps(start, end, spans):
            continue
        spans.append((start, end))
        notes.append(Annotation(note, start, end, words, target, guide))
    return notes


def _cut_notes(text, guide):
    """Each cut word, for sampling. A link still carries a reference to another section.

    A definition target ends in means. A reference target is the cut word.
    """
    from needles import Cut
    words = sorted((cut.value for cut in Cut), key=len, reverse=True)
    pattern = re.compile(
        r'(?i)\b(?P<word>%s)s?\b(?:\W{0,3}\s+means|\s+\([^)]+\)(?:\s*(?:,|,?\s*(?:and|or))\s*\([^)]+\))*)?' % '|'.join(words)
    )
    notes = []
    for match in pattern.finditer(text or ''):
        word = match.group('word').lower()
        phrase = match.group(0).strip()
        target = word + ' means' if phrase.lower().rstrip('”"\'').endswith('means') else word
        notes.append(Annotation(Note.CUT, match.start(), match.end(), phrase, target, guide))
    return notes


_TITLE = re.compile(
    r'\b[A-Z][a-z]+(?:\s+(?:of|the|and|for|&)\s+[A-Z][a-z]+|\s+[A-Z][a-z]+){1,8}\b'
)


def _case_notes(text, guide):
    """Uppercase words in a mixed sentence, and title-case names."""
    from analysis import capitals
    notes = []
    for phrase in capitals(text or ''):
        if phrase.reading != 'name':
            continue
        notes.append(Annotation(Note.CASE, phrase.start, phrase.end, phrase.text, 'uppercase', guide))
    for match in _TITLE.finditer(text or ''):
        notes.append(Annotation(Note.CASE, match.start(), match.end(), match.group(0), 'title', guide))
    return notes


_HEADING_CUT = re.compile(r'(?i)^(?P<cut>division|title|part|chapter|article)\b')
_HEADING_SPAN = re.compile(r'\[(?P<start>\d+(?:\.\d+)*)\.?\s*-\s*(?P<end>\d+(?:\.\d+)*)\.?\]')


def heading_notes(text, context=None):
    """The same notes as the section text, plus the cut the heading names.

    ``PART`` under a division heading is that cut. A bracketed span is the
    section range the heading covers, ``[38. - 86.]``. A history credit such as
    ``Added by Stats. 2008, Ch. 549, Sec. 3`` stays a session.
    """
    source = text or ''
    from apa import active as _citation_system
    guide = _citation_system()
    notes = []
    spans = []
    match = _HEADING_CUT.match(source)
    if match is not None:
        notes.append(Annotation(
            Note.CUT, match.start('cut'), match.end('cut'),
            match.group('cut'), match.group('cut').casefold(), guide,
        ))
        spans.append((match.start('cut'), match.end('cut')))
    span = _HEADING_SPAN.search(source)
    if span is not None:
        target = '%s-%s' % (span.group('start'), span.group('end'))
        notes.append(Annotation(
            Note.CITATION, span.start(), span.end(), span.group(0), target, guide, Cite.RANGE,
        ))
        spans.append((span.start(), span.end()))
    for note in annotate(source, context):
        if _overlaps(note.start, note.end, spans):
            continue
        notes.append(note)
    notes.sort(key=lambda note: (note.start, note.end))
    return notes


def annotate(text, context=None):
    """Citations and the internal references a style manual would keep.

    A section sign is a citation. ``commencing with Section`` and ``this part``
    point at another place in the same code. A named act is a reference by
    title: the Administrative Procedure Act, or the act a section says it
    may be cited as. ``id.``, ``supra``,
    and ``et seq.`` are the short forms. The California Style Manual is not
    posted in full, so these are the shapes rule 1.200's manuals share.
    """
    if not text:
        return []
    here = _active(context)
    from apa import active as _citation_system
    guide = _citation_system()
    notes = []
    spans = []
    for point in find_citations(text):
        spans.append((point.start, point.end))
        code = point.code
        if code:
            code = resolve_book(code, here.books) or code if here else code
        elif here is not None:
            code = here.code
        lead = text[max(0, point.start - 16):point.start].lower()
        if lead.endswith('commencing with '):
            start = point.start - len('commencing with ')
            words = text[start:point.end].strip()
            spans.append((start, point.end))
            book = (here.code + ' ') if here is not None and here.code else ''
            notes.append(Annotation(Note.CROSS_REFERENCE, start, point.end, words, (book + words).strip(), guide))
            continue
        items = list(point) if point.cite is Cite.SERIES else [point]
        for item in items:
            item_target = code or ''
            if item.numbers:
                item_target = (item_target + ' ' + item.numbers[0]).strip()
            notes.append(Annotation(
                Note.CITATION, item.start, item.end, item.text,
                item_target or None, guide, point.cite, point.join,
            ))
    for match in _CITED_AS.finditer(text):
        title = match.group('title')
        start, end = match.start('title'), match.end('title')
        if _overlaps(start, end, spans):
            continue
        spans.append((start, end))
        notes.append(Annotation(Note.NAMED_ACT, start, end, title, title, guide))
    for note, pattern in _REFERENCES:
        for match in pattern.finditer(text):
            if _overlaps(match.start(), match.end(), spans):
                continue
            spans.append((match.start(), match.end()))
            words = match.group(0).strip()
            target = words.casefold() if note is Note.SHORT_FORM else words
            if here is not None and re.fullmatch(r'(?i)this code', words):
                target = here.code
            elif here is not None and here.code and note is Note.CROSS_REFERENCE:
                target = '%s %s' % (here.code, words)
            notes.append(Annotation(note, match.start(), match.end(), words, target, guide))
    from structure import find_links
    book = here.code if here is not None else None
    for link in find_links(text, here=book):
        if link.kind == 'subdivision' and link.section:
            start = text.lower().find(link.text.lower())
            if start < 0:
                continue
            end = start + len(link.text)
            nested = any(
                start <= begin and end >= stop and (start < begin or end > stop)
                for begin, stop in spans
            )
            if _overlaps(start, end, spans) and not nested:
                continue
            spans.append((start, end))
            book_name = link.code.value if hasattr(link.code, 'value') else (link.code or '')
            target = '%s %s(%s)' % (book_name, link.section, link.label)
            notes.append(Annotation(Note.CROSS_REFERENCE, start, end, link.text, target.strip(), guide))
            continue
        if link.kind == 'session':
            start = text.lower().find(link.text.lower())
            if start < 0 or _overlaps(start, start + len(link.text), spans):
                continue
            end = start + len(link.text)
            spans.append((start, end))
            target = link.session.target() if link.session is not None else None
            if target and link.action is not None:
                target = '%s %s' % (link.action.value, target)
            notes.append(Annotation(Note.SESSION, start, end, link.text, target, guide))
            continue
        if link.kind != 'article':
            continue
        start = text.lower().find(link.text.lower())
        if start < 0 or _overlaps(start, start + len(link.text), spans):
            continue
        end = start + len(link.text)
        spans.append((start, end))
        target = 'California Constitution, article %s, section %s' % (link.label, link.section)
        notes.append(Annotation(Note.CITATION, start, end, link.text, target, guide))
    notes.extend(_cut_notes(text, guide))
    notes.extend(_case_notes(text, guide))
    notes.extend(_measure_notes(text, spans, guide))
    notes.sort(key=lambda note: (note.start, note.end))
    return notes
