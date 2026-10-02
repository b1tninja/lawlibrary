"""How a California section changed from one edition on the shelf to the next.

The shelf holds one index per session (``data/shelf/<year>/``). From 2011 on
an edition carries the code tables, so each holds the words of every section
in force when the Legislature last refreshed that session's file, and the
history note the table printed beside it (``Amended by Stats. 2025, Ch. 22,
Sec. 4. (AB 130) Effective June 30, 2025.``). Editions before 2011 carry
bills, not code sections; a section is ``not_indexed`` there.

``section_history`` reads one section across the editions: present or not,
a digest of the words, the note read into a ``HistoryNote``, and a ``Step``
between each pair of editions with a ``Change`` and a short word-level
``Diff``. ``changes`` is the same comparison over a span (or several) as one
linear list, oldest first. ``between`` compares two editions directly.

A note names only the latest act on the section. A repeal leaves no note:
the section is simply absent from the next edition, so a ``REPEALED`` step
names no statute unless a recodification on record names one
(``succession.Recodification``). The words of a section come from the index;
nothing here stores them.
"""

from __future__ import annotations

import difflib
import enum
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from whoosh.query import And, Or, Term

from core import editions as _shelf_editions, open_index, within
from needles import Action, Occasion, Session


class Change(enum.Enum):
    """What happened to a section between two editions. The value is the stored word.

    ``AMENDED`` means the later note names a different statute than the
    earlier one. ``REVISED`` means the words differ while the note names the
    same statute (a later operative version, or the publisher's correction).
    ``RENOTED`` means the words are the same and only the note changed (a
    bill number added to the same credit, for one). A repeal is the section
    gone from the later edition.
    """

    ADDED = 'added'
    AMENDED = 'amended'
    REVISED = 'revised'
    RENOTED = 'renoted'
    UNCHANGED = 'unchanged'
    REPEALED = 'repealed'


QUIET = frozenset({Change.UNCHANGED, Change.RENOTED})


_ACTION = re.compile(
    r'^(?P<action>Enacted'
    r'|Added by renumbering Section (?P<source>\d+(?:\.\d+)*[a-z]?)'
    r'|Repealed \(in Sec\. [\d.]+[a-z]?\) and added'
    r'|Repealed and added'
    r'|Added'
    r'|Amended'
    r'|Repealed)\b'
)
_ACTIONS = (
    ('Enacted', Action.ENACTED),
    ('Added by renumbering', Action.RENUMBERED),
    ('Repealed (in', Action.REPEALED_AND_ADDED),
    ('Repealed and added', Action.REPEALED_AND_ADDED),
    ('Added', Action.ADDED),
    ('Amended', Action.AMENDED),
    ('Repealed', Action.REPEALED),
)
_STATS = re.compile(
    r'\bby Stats\. (?P<year>\d{4})(?:, (?P<extra>[^,]*Ex\. Sess\.))?, Ch\. (?P<chapter>\d+)'
    r'(?:, Sec\. (?P<act>\d+(?:\.\d+)*[a-z]?))?'
)
_CODE_AMENDMENTS = re.compile(r'\bby Code Amendments (?P<years>\d{4}(?:-\d{2,4})?), Ch\. (?P<chapter>\d+)')
_INITIATIVE = re.compile(r'\bby initiative Proposition (?P<prop>\w+)(?:, Sec\. (?P<act>[\d.]+))?')
_ENACTED = re.compile(r'^Enacted (?P<year>\d{4})')
_BILL = re.compile(r'^\((?P<bill>(?:[AS]B|[AS]CA|[AS]CR|[AS]JR|[AS]BX\d*)\s*\d+)\)\.?$')
_MONTHS = (
    'January February March April May June July August September October November December'
).split()
_DAY = re.compile(r'(?P<month>%s) (?P<day>\d{1,2}), (?P<year>\d{4})' % '|'.join(_MONTHS))


@dataclass(frozen=True)
class Dated:
    """One day the note ties to the section: when it took effect, became operative, and so on."""

    occasion: Occasion
    day: str
    by: str = ''

    def record(self):
        return {'occasion': self.occasion.value, 'day': self.day, 'by': self.by}


@dataclass(frozen=True)
class HistoryNote:
    """The history note a code table printed for one section in one edition.

    ``statute`` is the chapter of the Statutes and the enrolled bill's own
    section (``Session``); it is not a code chapter. ``measure`` holds a
    credit that is not a ``Stats.`` chapter (``Code Amendments 1873-74, Ch.
    612``, an initiative). ``read`` is false when the first clause did not
    parse; ``note`` still keeps the printed words.
    """

    note: str
    action: Action | None = None
    statute: Session | None = None
    extra_session: str = ''
    measure: str = ''
    bill: str = ''
    source: str = ''
    enacted: str = ''
    dates: tuple = ()
    read: bool = False

    @property
    def effective(self):
        return self._day(Occasion.EFFECTIVE)

    @property
    def operative(self):
        return self._day(Occasion.OPERATIVE)

    def _day(self, occasion):
        for dated in self.dates:
            if dated.occasion is occasion:
                return dated.day
        return ''

    def identity(self):
        """The act the note names: the action and the statute. A bill label is not part of it."""
        statute = None if self.statute is None else (self.statute.year, self.statute.chapter, self.statute.act)
        return (self.action, statute, self.measure, self.enacted, self.source)

    def citation(self):
        """``Stats. 2012, Ch. 180, Sec. 2`` when the note names a chapter."""
        if self.statute is None:
            return self.measure or (('Enacted %s' % self.enacted) if self.enacted else '')
        text = 'Stats. %s' % self.statute.year
        if self.extra_session:
            text += ', %s' % self.extra_session
        text += ', Ch. %s' % self.statute.chapter
        if self.statute.act:
            text += ', Sec. %s' % self.statute.act
        return text

    def record(self):
        statute = None
        if self.statute is not None:
            statute = {
                'year': self.statute.year,
                'chapter': self.statute.chapter,
                'act': self.statute.act or '',
                'reference': self.statute.reference(),
            }
        return {
            'note': self.note,
            'read': self.read,
            'action': '' if self.action is None else self.action.value,
            'statute': statute,
            'citation': self.citation(),
            'extra_session': self.extra_session,
            'measure': self.measure,
            'bill': self.bill,
            'renumbered_from': self.source,
            'enacted': self.enacted,
            'effective': self.effective,
            'operative': self.operative,
            'dates': [dated.record() for dated in self.dates],
        }


def _iso(match):
    return date(int(match.group('year')), _MONTHS.index(match.group('month')) + 1,
                int(match.group('day'))).isoformat()


def _occasion(words):
    lowered = words.casefold()
    for word, occasion in (
        ('inoperative', Occasion.INOPERATIVE),
        ('operative', Occasion.OPERATIVE),
        ('effective', Occasion.EFFECTIVE),
        ('repealed', Occasion.REPEALED),
        ('applicable', Occasion.APPLICABLE),
        ('superseded', Occasion.SUPERSEDED),
        ('approved', Occasion.APPROVED),
    ):
        if word in lowered:
            return occasion
    return None


def read_note(note):
    """Read a code table's history note into a ``HistoryNote``.

    The note's clauses are separated by runs of spaces. The first is the
    action and the credit; the rest are a bill label in parentheses and the
    days (``Effective``, ``Operative``, ``Inoperative``, ``Repealed as of``).
    A first clause that names no action is kept unread.
    """
    text = (note or '').strip()
    if not text:
        return HistoryNote(note='')
    clauses = [piece.strip() for piece in re.split(r'\s{2,}', text) if piece.strip()]
    head = clauses[0]
    fields = {'note': text}
    acted = _ACTION.match(head)
    if acted is not None:
        printed = acted.group('action')
        for lead, action in _ACTIONS:
            if printed.startswith(lead):
                fields['action'] = action
                break
        if acted.group('source'):
            fields['source'] = acted.group('source')
    bare = re.sub(r'\([^)]*\)', '', head)
    stats = _STATS.search(bare)
    if stats is not None:
        fields['statute'] = Session(stats.group('year'), stats.group('chapter'), stats.group('act'))
        fields['extra_session'] = (stats.group('extra') or '').strip()
    else:
        amendments = _CODE_AMENDMENTS.search(bare)
        initiative = _INITIATIVE.search(bare)
        if amendments is not None:
            fields['measure'] = 'Code Amendments %s, Ch. %s' % (amendments.group('years'), amendments.group('chapter'))
        elif initiative is not None:
            fields['measure'] = 'Proposition %s' % initiative.group('prop')
            day = _DAY.search(bare)
            if day is not None:
                fields.setdefault('dates', []).append(Dated(Occasion.APPROVED, _iso(day), 'election'))
    enacted = _ENACTED.match(head)
    if enacted is not None:
        fields['enacted'] = enacted.group('year')
    dates = list(fields.pop('dates', []))
    for clause in clauses[1:]:
        bill = _BILL.match(clause)
        if bill is not None:
            fields['bill'] = re.sub(r'\s+', ' ', bill.group('bill'))
            continue
        day = _DAY.search(clause)
        occasion = _occasion(clause[:day.start()] if day else clause)
        if day is None or occasion is None:
            continue
        rest = clause[day.end():].strip(' ,.')
        dates.append(Dated(occasion, _iso(day), rest))
    fields['dates'] = tuple(dates)
    fields['read'] = 'action' in fields and (
        'statute' in fields or 'measure' in fields or 'enacted' in fields
    )
    return HistoryNote(**fields)


# ---------------------------------------------------------------------------
# The words, compared.

_CUT = re.compile(r'^\((?:[a-z]{1,2}|\d{1,3}|[A-Z]{1,2}|[ivx]{1,5})\)$')
HUNKS = 6
HUNK_WORDS = 14


def words_of(text):
    return (text or '').split()


def digest(text):
    """A short fingerprint of the words. Whitespace does not count."""
    return hashlib.sha1(' '.join(words_of(text)).encode('utf-8')).hexdigest()[:16]


@dataclass(frozen=True)
class Hunk:
    """One run of words that differs. ``near`` is the cut label printed before it."""

    op: str
    before: str
    after: str
    near: str = ''

    def record(self):
        return {'op': self.op, 'before': self.before, 'after': self.after, 'near': self.near}


@dataclass(frozen=True)
class Diff:
    """A word-level summary of two texts. Counts, a similarity ratio, and the first few hunks."""

    words_before: int
    words_after: int
    inserted: int
    deleted: int
    replaced: int
    ratio: float
    hunks: tuple = ()
    more: int = 0

    def record(self):
        return {
            'words_before': self.words_before,
            'words_after': self.words_after,
            'inserted': self.inserted,
            'deleted': self.deleted,
            'replaced': self.replaced,
            'ratio': self.ratio,
            'hunks': [hunk.record() for hunk in self.hunks],
            'more': self.more,
        }

    def summary(self):
        if not (self.inserted or self.deleted or self.replaced):
            return 'no word changed'
        parts = []
        if self.inserted:
            parts.append('%d words inserted' % self.inserted)
        if self.deleted:
            parts.append('%d deleted' % self.deleted)
        if self.replaced:
            parts.append('%d replaced' % self.replaced)
        places = sorted({hunk.near for hunk in self.hunks if hunk.near})
        text = ', '.join(parts) + ' (%.0f%% the same)' % (self.ratio * 100)
        if places:
            text += ' near ' + ', '.join(places)
        return text


def _clip(words):
    if len(words) <= HUNK_WORDS:
        return ' '.join(words)
    half = HUNK_WORDS // 2
    return ' '.join(words[:half]) + ' ... ' + ' '.join(words[-half:])


def _near(words, index):
    for position in range(min(index, len(words) - 1), -1, -1):
        if _CUT.match(words[position]):
            return words[position]
    return ''


def compare(before, after, hunks=HUNKS):
    """``Diff`` of two texts by word. The hunks carry at most ``HUNK_WORDS`` words a side."""
    old, new = words_of(before), words_of(after)
    matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
    inserted = deleted = replaced = 0
    rows = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == 'equal':
            continue
        if op == 'insert':
            inserted += j2 - j1
        elif op == 'delete':
            deleted += i2 - i1
        else:
            replaced += max(i2 - i1, j2 - j1)
        rows.append(Hunk(op, _clip(old[i1:i2]), _clip(new[j1:j2]), _near(old, i1) or _near(new, j1)))
    return Diff(
        words_before=len(old),
        words_after=len(new),
        inserted=inserted,
        deleted=deleted,
        replaced=replaced,
        ratio=round(matcher.ratio(), 4),
        hunks=tuple(rows[:hunks]),
        more=max(0, len(rows) - hunks),
    )


# ---------------------------------------------------------------------------
# The shelf, read edition by edition.


def code_editions(code):
    """The editions on the shelf whose code tables carry ``code``, oldest first.

    An edition with no ``codes.json`` naming the code (a bills edition before
    2011) is left out. A flat index has no editions and gives an empty list.
    """
    token = getattr(code, 'value', code)
    years = []
    for path in _shelf_editions():
        listed = Path(path) / 'codes.json'
        try:
            codes = json.loads(listed.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if token in codes:
            years.append(Path(path).name)
    return years


def all_editions():
    return [Path(path).name for path in _shelf_editions()]


def _resolve(code):
    import query
    idxer = query._indexer()
    if not query._index_ready(idxer):
        return idxer, None, 'not_in_index'
    resolved = query._resolve_known_code(idxer, code)
    if resolved is None:
        return idxer, None, 'unknown_code'
    return idxer, resolved, ''


def _day_of(value):
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value)[:10]


@dataclass(frozen=True)
class Edition:
    """One section in one edition: there or not, the digest, and the note."""

    session: str
    found: bool
    reason: str = ''
    digest: str = ''
    words: int = 0
    credit: HistoryNote | None = None
    effective: str = ''
    text: str = field(default='', repr=False, compare=False)

    def record(self):
        row = {'session': self.session, 'found': self.found}
        if not self.found:
            row['reason'] = self.reason
            return row
        row.update({
            'digest': self.digest,
            'words': self.words,
            'effective': self.effective,
            'credit': None if self.credit is None else self.credit.record(),
        })
        return row


def _edition(session, doc):
    if doc is None:
        return Edition(session=session, found=False, reason='not_in_edition')
    text = doc.get('LEGAL_TEXT') or ''
    return Edition(
        session=session,
        found=True,
        digest=digest(text),
        words=len(words_of(text)),
        credit=read_note(doc.get('SECTION_HISTORY') or doc.get('HISTORY') or ''),
        effective=_day_of(doc.get('EFFECTIVE_DATE')),
        text=text,
    )


@dataclass(frozen=True)
class Step:
    """One section from one edition to the next."""

    code: str
    section: str
    before: str
    after: str
    change: Change
    credit: HistoryNote | None = None
    diff: Diff | None = None
    recodification: dict | None = None

    def record(self):
        credit = self.credit
        row = {
            'citation': '%s %s' % (self.code, self.section),
            'code': self.code,
            'section': self.section,
            'before': self.before,
            'after': self.after,
            'change': self.change.value,
            'action': '' if credit is None or credit.action is None else credit.action.value,
            'statute': '' if credit is None else credit.citation(),
            'bill': '' if credit is None else credit.bill,
            'effective': '' if credit is None else credit.effective,
            'operative': '' if credit is None else (credit.operative or credit.effective),
            'note': '' if credit is None else credit.note,
            'summary': '' if self.diff is None else self.diff.summary(),
            'diff': None if self.diff is None else self.diff.record(),
        }
        if self.recodification is not None:
            row['recodification'] = self.recodification
            if credit is None:
                # A repeal leaves no note; the act on record names it.
                row.update({
                    'action': Action.REPEALED.value,
                    'statute': self.recodification.get('statute', ''),
                    'bill': self.recodification.get('bill', ''),
                    'operative': self.recodification.get('operative', ''),
                })
        return row


def step(code, section, before, after, *, diff=True):
    """Compare one section's ``Edition`` rows from two editions."""
    if not before.found and not after.found:
        return None
    if not before.found:
        return Step(code, section, before.session, after.session, Change.ADDED, after.credit)
    if not after.found:
        return Step(code, section, before.session, after.session, Change.REPEALED, None,
                    recodification=_recodified(code, section, before.session, after.session))
    same_words = before.digest == after.digest
    old = before.credit.identity() if before.credit else None
    new = after.credit.identity() if after.credit else None
    if same_words and old == new:
        if (before.credit.note if before.credit else '') != (after.credit.note if after.credit else ''):
            change = Change.RENOTED
        else:
            change = Change.UNCHANGED
    elif old != new:
        change = Change.AMENDED
    else:
        change = Change.REVISED
    if change is Change.UNCHANGED:
        return Step(code, section, before.session, after.session, change, after.credit)
    return Step(
        code, section, before.session, after.session, change, after.credit,
        compare(before.text, after.text) if diff and not same_words else None,
    )


def _recodified(code, section, before, after):
    """The recodification on record that repealed this span between those editions, if any."""
    try:
        from succession import repeal_of
    except ImportError:  # pragma: no cover - the module ships beside this one
        return None
    return repeal_of(code, section, before, after)


def _docs_for_sections(idxer, code, numbers):
    """Every edition's stored row for each section number. ``{(session, number): doc}``."""
    import query
    wanted = []
    by_form = {}
    for number in numbers:
        for form in query.section_forms(number):
            wanted.append(Term('SECTION_NUM', form))
            by_form[form] = query.section_address(number)
    if not wanted:
        return {}
    rows = {}
    ix = open_index(idxer.idx_path)
    with ix.searcher() as searcher:
        hits = searcher.search(
            within(And([Term('LAW_CODE', code), Or(wanted)]), idxer._filter(True, 'all')),
            limit=None,
        )
        for hit in hits:
            doc = dict(hit)
            number = by_form.get(doc.get('SECTION_NUM'))
            if number is None:
                continue
            rows.setdefault((doc.get('SESSION'), number), doc)
    return rows


def section_history(code, number):
    """One section across every edition on the shelf.

    ``editions`` is a row per edition (``found``, ``digest``, ``words``,
    ``credit``); an edition whose tables do not carry the code says
    ``not_indexed``. ``steps`` compares each code edition with the next.
    ``credits`` is each distinct act the notes named, oldest first, with the
    first edition that printed it. A section on no edition is a miss.
    """
    import query
    expression = '%s %s' % (getattr(code, 'value', code) or '', number or '')
    idxer, resolved, reason = _resolve(code)
    if resolved is None:
        return query._miss(expression.strip(), reason)
    number = query.section_address(number)
    docs = _docs_for_sections(idxer, resolved, [number])
    carried = code_editions(resolved)
    rows = []
    for session in all_editions():
        if session not in carried:
            rows.append(Edition(session=session, found=False, reason='not_indexed'))
            continue
        rows.append(_edition(session, docs.get((session, number))))
    present = [row for row in rows if row.found]
    if not present:
        return query._miss(expression.strip(), 'not_in_index', editions=carried)
    coded = [row for row in rows if row.session in carried]
    steps = []
    for before, after in zip(coded, coded[1:]):
        found = step(resolved, number, before, after)
        if found is not None:
            steps.append(found)
    credits = []
    seen = set()
    for row in present:
        if row.credit is None:
            continue
        key = row.credit.identity()
        if key in seen:
            continue
        seen.add(key)
        credits.append({'first_edition': row.session, **row.credit.record()})
    last = present[-1]
    return {
        'found': True,
        'citation': '%s %s' % (resolved, number),
        'code': resolved,
        'section': number,
        'first': present[0].session,
        'last': last.session,
        'current': last.session == (carried[-1] if carried else None),
        'editions': [row.record() for row in rows],
        'steps': [item.record() for item in steps],
        'credits': credits,
    }


def _spans(spans):
    rows = []
    for span in spans or ():
        if isinstance(span, str):
            start, _, end = span.partition('-')
            rows.append((start.strip(), (end or start).strip()))
        else:
            start, end = span
            rows.append((str(start), str(end)))
    return rows


def _in_spans(number, spans):
    import query
    return any(query._in_span(number, start, end) for start, end in spans)


def _span_rows(idxer, code, session, spans):
    import query
    rows = {}
    for doc in query._docs_for_code(idxer, code, session=session):
        number = query.section_address(doc.get('SECTION_NUM'))
        if _in_spans(number, spans):
            rows.setdefault(number, doc)
    return rows


def _act_spans(act):
    from succession import recodification
    found = recodification(act)
    if found is None:
        return None
    return [found.former, found.current]


def changes(code, spans=(), *, since=None, until=None, act=None, unchanged=False, diff=True):
    """Every change to sections in ``spans`` between consecutive editions, oldest first.

    ``spans`` is ``[('4000', '6150'), ('1350', '1378')]`` or ``['4000-6150']``.
    ``act`` names a recodification (``davis-stirling``) and adds its former
    and current spans. ``since`` and ``until`` bound the editions compared
    (``since=2011`` starts with the 2011 to 2013 step). ``unchanged`` keeps
    the rows where the words and the act stayed the same (``UNCHANGED`` and
    ``RENOTED``); they are left out otherwise.
    """
    import query
    spans = _spans(spans)
    if act:
        extra = _act_spans(act)
        if extra is None:
            return query._miss(act, 'unknown_act')
        spans.extend(extra)
    expression = '%s %s' % (getattr(code, 'value', code) or '', ', '.join('%s-%s' % span for span in spans))
    if not spans:
        return query._miss(expression.strip(), 'not_in_index')
    idxer, resolved, reason = _resolve(code)
    if resolved is None:
        return query._miss(expression.strip(), reason)
    carried = [year for year in code_editions(resolved)
               if (since is None or int(year) >= int(since)) and (until is None or int(year) <= int(until))]
    if len(carried) < 2:
        return query._miss(expression.strip(), 'not_in_index', editions=carried)
    loaded = {session: _span_rows(idxer, resolved, session, spans) for session in carried}
    rows = []
    for before, after in zip(carried, carried[1:]):
        rows.extend(_pair(resolved, loaded[before], loaded[after], before, after, unchanged, diff))
    return {
        'found': True,
        'code': resolved,
        'spans': [list(span) for span in spans],
        'editions': carried,
        'counts': _count(rows),
        'changes': rows,
    }


def _pair(code, older, newer, before, after, unchanged, diff):
    import query
    rows = []
    numbers = sorted(set(older) | set(newer), key=query.section_key)
    for number in numbers:
        found = step(
            code, number,
            _edition(before, older.get(number)),
            _edition(after, newer.get(number)),
            diff=diff,
        )
        if found is None or (found.change in QUIET and not unchanged):
            continue
        rows.append(found.record())
    return rows


def _count(rows):
    counts = {}
    for row in rows:
        counts[row['change']] = counts.get(row['change'], 0) + 1
    return counts


def between(code, spans, before, after, *, unchanged=False, diff=True):
    """What changed in ``spans`` from edition ``before`` to edition ``after``, directly."""
    import query
    spans = _spans(spans)
    expression = '%s %s' % (getattr(code, 'value', code) or '', ', '.join('%s-%s' % span for span in spans))
    idxer, resolved, reason = _resolve(code)
    if resolved is None:
        return query._miss(expression.strip(), reason)
    carried = code_editions(resolved)
    for year in (str(before), str(after)):
        if year not in carried:
            return query._miss(expression.strip(), 'not_indexed', session=year, editions=carried)
    older = _span_rows(idxer, resolved, str(before), spans)
    newer = _span_rows(idxer, resolved, str(after), spans)
    rows = _pair(resolved, older, newer, str(before), str(after), unchanged, diff)
    return {
        'found': True,
        'code': resolved,
        'spans': [list(span) for span in spans],
        'before': str(before),
        'after': str(after),
        'counts': _count(rows),
        'changes': rows,
    }


# ---------------------------------------------------------------------------
# The command line: ``python ca.py --history CIV 1363`` and the rest.


def add_arguments(parser):
    """The history and succession flags on ``ca.py``."""
    parser.add_argument('--history', nargs=2, metavar=('CODE', 'SECTION'),
                        help="One section across every edition on the shelf, e.g. --history CIV 1363")
    parser.add_argument('--changes', nargs='+', metavar='CODE [START END ...]',
                        help="Every change in one or more spans, oldest first, e.g. --changes CIV 4000 6150 1350 1378")
    parser.add_argument('--act', default=None,
                        help="With --changes or --coverage: a recodification, e.g. davis-stirling")
    parser.add_argument('--since', default=None, help="With --changes: the first edition compared")
    parser.add_argument('--until', default=None, help="With --changes: the last edition compared")
    parser.add_argument('--between', nargs=2, metavar=('BEFORE', 'AFTER'), default=None,
                        help="With --changes: compare two editions directly")
    parser.add_argument('--unchanged', action='store_true',
                        help="With --changes: keep rows where nothing changed")
    parser.add_argument('--successors', nargs='+', metavar='CODE SECTION [SUBDIVISION]',
                        help="Where a former section went, e.g. --successors CIV 1363 (g)")
    parser.add_argument('--predecessors', nargs=2, metavar=('CODE', 'SECTION'),
                        help="Which former provisions a new section continues, e.g. --predecessors CIV 5855")
    parser.add_argument('--coverage', nargs='?', const='davis-stirling', default=None, metavar='ACT',
                        help="How much of the former law the Commission's tables place")
    parser.add_argument('--fetch-clrc', action='store_true',
                        help="Download the Law Revision Commission's tables and reports into data/clrc")


def _pairs(values):
    return [(values[index], values[index + 1]) for index in range(0, len(values) - 1, 2)]


def run(args, out=None):
    """Answer the flags ``add_arguments`` added. True when one was given."""
    import sys
    out = out or sys.stdout
    answers = []
    if getattr(args, 'fetch_clrc', False):
        from succession import fetch
        answers.append(fetch())
    if getattr(args, 'history', None):
        answers.append(section_history(*args.history))
    if getattr(args, 'changes', None):
        code, rest = args.changes[0], args.changes[1:]
        if args.between:
            answers.append(between(code, _pairs(rest), args.between[0], args.between[1],
                                   unchanged=args.unchanged))
        else:
            answers.append(changes(code, _pairs(rest), since=args.since, until=args.until,
                                   act=args.act, unchanged=args.unchanged))
    if getattr(args, 'successors', None):
        from succession import successors
        values = args.successors
        answers.append(successors(values[0], values[1], values[2] if len(values) > 2 else None))
    if getattr(args, 'predecessors', None):
        from succession import predecessors
        answers.append(predecessors(*args.predecessors))
    if getattr(args, 'coverage', None):
        from succession import coverage
        answers.append(coverage(args.act or args.coverage))
    for answer in answers:
        out.write(json.dumps(answer, indent=2, ensure_ascii=False) + '\n')
    return bool(answers)
