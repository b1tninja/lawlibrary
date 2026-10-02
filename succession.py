"""Which section continues a former one, and which former section a new one continues.

A recodification repeals a span of a code and adds another. The California
Law Revision Commission, which recommended the Davis-Stirling recodification
(Study H-855), published where each provision of the former law went: the
disposition table, and a Commission Comment on each new section. Those are
the official readings and the pin. They stay apart:

``Source.DISPOSITION_TABLE``
    a row of a disposition table. ``former`` provision, the ``targets`` it
    went to, or ``omitted`` / ``not continued``.
``Source.COMMISSION_COMMENT``
    a sentence of a Comment in the Commission's recommendation:
    ``continues former Section ... without change``, ``is new``, and the
    rest. The recommendation predates the bill's last amendments, so a
    Comment can disagree with the table; both rows are returned.
``Source.SIMILARITY``
    a candidate the words suggest, scored, only where the table is silent.
    A candidate is never a pin.

The documents are downloaded from clrc.ca.gov into the archive
(``data/clrc``) by ``fetch``; a missing file is a miss that says so. The
words of a section come from the index (``history``, ``query.section``);
nothing here stores a statute's sentences.
"""

from __future__ import annotations

import enum
import html
import math
import os
import re
import shutil
import subprocess
import urllib.request
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from core import data_dir
from needles import Session
from us.ca.apa import Code


# ---------------------------------------------------------------------------
# Closed sets.


class Succession(enum.Enum):
    """How a provision of the former law relates to the new law. The value is the stored word.

    ``CONTINUED`` is a disposition-table row: the table says where, not how.
    The Comment says how: ``CONTINUED_WITHOUT_CHANGE``,
    ``CONTINUED_WITHOUT_SUBSTANTIVE_CHANGE`` (``continues the substance of``,
    or only nonsubstantive changes listed), ``CONTINUED_WITH_CHANGES`` (a
    substantive change listed), ``RESTATED``, ``GENERALIZED``,
    ``SUPERSEDED``, ``SIMILAR``. ``NEW`` has no former provision.
    ``OMITTED`` and ``OMITTED_SEE`` are the table's ``omitted`` and
    ``omitted, but see``; ``NOT_CONTINUED`` is a table that prints ``not
    continued``. ``PARALLEL`` is a similar provision in a sibling act.
    ``CANDIDATE`` is a similarity reading.
    """

    CONTINUED = 'continued'
    CONTINUED_WITHOUT_CHANGE = 'continued_without_change'
    CONTINUED_WITHOUT_SUBSTANTIVE_CHANGE = 'continued_without_substantive_change'
    CONTINUED_WITH_CHANGES = 'continued_with_changes'
    RESTATED = 'restated'
    GENERALIZED = 'generalized'
    SUPERSEDED = 'superseded'
    SIMILAR = 'similar'
    NEW = 'new'
    OMITTED = 'omitted'
    OMITTED_SEE = 'omitted_see'
    NOT_CONTINUED = 'not_continued'
    PARALLEL = 'parallel'
    CANDIDATE = 'candidate'


CONTINUING = frozenset({
    Succession.CONTINUED,
    Succession.CONTINUED_WITHOUT_CHANGE,
    Succession.CONTINUED_WITHOUT_SUBSTANTIVE_CHANGE,
    Succession.CONTINUED_WITH_CHANGES,
    Succession.RESTATED,
    Succession.GENERALIZED,
    Succession.SUPERSEDED,
    Succession.SIMILAR,
})
LEFT_OUT = frozenset({Succession.OMITTED, Succession.OMITTED_SEE, Succession.NOT_CONTINUED})


class Shape(enum.Enum):
    """How many sections sit on each side of a row."""

    ONE_TO_ONE = 'one_to_one'
    SPLIT = 'split'
    COMBINED = 'combined'
    SPLIT_AND_COMBINED = 'split_and_combined'
    NONE = 'none'


class Source(enum.Enum):
    """Where a row was read. Two sources are two readings."""

    DISPOSITION_TABLE = 'disposition_table'
    COMMISSION_COMMENT = 'commission_comment'
    SIMILARITY = 'similarity'


class Report(enum.Enum):
    """A California Law Revision Commission publication read here. The value is the file stem."""

    STUDY_PAGE = 'H855'
    PUBLISHERS_PAGE = 'publishers'
    AB805_DISPOSITION = 'AB805DispoTable'
    SB752_DISPOSITION = 'SB752DispoTable'
    RECOMMENDATION_2011 = 'Pub235-H855'
    CLEANUP_2012 = 'Pub237-H855'
    CLEANUP_2013 = 'Pub238-H855'


@dataclass(frozen=True)
class Publication:
    """Where a Commission document is published and what it is."""

    title: str
    url: str
    suffix: str
    cite: str = ''


CLRC = 'http://www.clrc.ca.gov/'

PUBLICATIONS = {
    Report.STUDY_PAGE: Publication(
        'Statutory Clarification and Simplification of CID Law - Study H-855',
        CLRC + 'H855.html', '.html'),
    Report.PUBLISHERS_PAGE: Publication(
        'Legal Publisher Documents', CLRC + 'Menu3_reports/publishers.html', '.html'),
    Report.AB805_DISPOSITION: Publication(
        'Disposition Table (AB 805, Stats. 2012, Ch. 180)',
        CLRC + 'pub/publishers/2012/AB805DispoTable.pdf', '.pdf'),
    Report.SB752_DISPOSITION: Publication(
        'Disposition Tables for 2013 Cal. Stat. ch. 605 (SB 752)',
        CLRC + 'pub/publishers/2013/SB752DispoTable.docx', '.docx'),
    Report.RECOMMENDATION_2011: Publication(
        'Recommendation: Statutory Clarification and Simplification of CID Law (February 2011)',
        CLRC + 'pub/Printed-Reports/Pub235-H855.pdf', '.pdf',
        "40 Cal. L. Revision Comm'n Reports 235 (2010)"),
    Report.CLEANUP_2012: Publication(
        'Recommendation: Statutory Clarification and Simplification of CID Law: Clean-Up Legislation (December 2012)',
        CLRC + 'pub/Printed-Reports/Pub237-H855.pdf', '.pdf'),
    Report.CLEANUP_2013: Publication(
        'Recommendation: Statutory Clarification and Simplification of CID Law: Further Clean-Up Legislation (August 2013)',
        CLRC + 'pub/Printed-Reports/Pub238-H855.pdf', '.pdf'),
}


@dataclass(frozen=True)
class Recodification:
    """One act that repealed a span and added another, with the Commission's readings.

    ``chapter`` and ``bill`` are as the Commission's study page lists the
    enactment. ``repeals`` is true when this chapter repealed the former span
    (the second act here continued the same former law in a new part, so it
    repealed nothing of it). The operative day is read from the new
    sections' own notes, not stored here.
    """

    key: str
    title: str
    code: Code
    former: tuple
    current: tuple
    chapter: Session
    bill: str
    tables: tuple
    comments: Report | None = None
    repeals: bool = False
    repeal_act: str = ''
    source: Report = Report.STUDY_PAGE


DAVIS_STIRLING = Recodification(
    key='davis-stirling',
    title='Davis-Stirling Common Interest Development Act',
    code=Code.CIVIL,
    former=('1350', '1378'),
    current=('4000', '6150'),
    chapter=Session('2012', '180'),
    bill='AB 805',
    tables=(Report.AB805_DISPOSITION,),
    comments=Report.RECOMMENDATION_2011,
    repeals=True,
    repeal_act='1',
)

COMMERCIAL_AND_INDUSTRIAL = Recodification(
    key='commercial-industrial',
    title='Commercial and Industrial Common Interest Development Act',
    code=Code.CIVIL,
    former=('1350', '1378'),
    current=('6500', '6876'),
    chapter=Session('2013', '605'),
    bill='SB 752',
    tables=(Report.SB752_DISPOSITION,),
    source=Report.PUBLISHERS_PAGE,
)

RECODIFICATIONS = (DAVIS_STIRLING, COMMERCIAL_AND_INDUSTRIAL)


def recodification(key):
    key = getattr(key, 'key', key)
    for item in RECODIFICATIONS:
        if item.key == str(key or '').strip().lower():
            return item
    return None


# ---------------------------------------------------------------------------
# Provisions and rows.

_LABEL = re.compile(r'\(([0-9]+|[a-zA-Z]{1,4})\)')


@dataclass(frozen=True)
class Provision:
    """A section, and the part of it a row names, as printed: ``(e)(3) (except last ¶)``."""

    code: str
    section: str
    part: str = ''

    @property
    def path(self):
        """The leading cut labels: ``('e', '3')`` for ``(e)(3) (except last ¶)``."""
        labels = []
        rest = self.part
        while True:
            matched = _LABEL.match(rest)
            if matched is None:
                break
            labels.append(matched.group(1))
            rest = rest[matched.end():]
        return tuple(labels)

    @property
    def subdivision(self):
        path = self.path
        return path[0] if path else ''

    def tops(self):
        """The top-level labels the part covers. ``(a)-(e)`` covers five; ``(e)(3)`` covers ``e``."""
        ranged = re.match(r'^\(([a-z]|\d+)\)\s*-\s*\(([a-z]|\d+)\)', self.part)
        if ranged is not None:
            first, last = ranged.groups()
            if first.isdigit() and last.isdigit():
                return tuple(str(n) for n in range(int(first), int(last) + 1))
            if len(first) == len(last) == 1:
                return tuple(chr(n) for n in range(ord(first), ord(last) + 1))
        path = self.path
        return path[:1]

    def label(self):
        if not self.part:
            return self.section
        joiner = '' if self.part.startswith('(') and not self.part.startswith('(intro') else ' '
        return '%s%s%s' % (self.section, joiner, self.part)

    def record(self):
        return {
            'citation': '%s %s' % (self.code, self.label()),
            'code': self.code,
            'section': self.section,
            'part': self.part,
            'subdivision': self.subdivision,
        }


@dataclass(frozen=True)
class Row:
    """One reading of where a former provision went, or where a new one came from."""

    former: Provision | None
    targets: tuple
    succession: Succession
    source: Source
    report: Report | None = None
    page: str = ''
    line: int = 0
    see: tuple = ()
    act: str = ''
    score: float = 0.0
    shape: Shape = Shape.NONE

    def record(self):
        row = {
            'former': None if self.former is None else self.former.record(),
            'targets': [target.record() for target in self.targets],
            'succession': self.succession.value,
            'shape': self.shape.value,
            'source': self.source.value,
            'act': self.act,
        }
        if self.see:
            row['see'] = [item.record() for item in self.see]
        if self.report is not None:
            publication = PUBLICATIONS[self.report]
            row['report'] = {'key': self.report.value, 'title': publication.title,
                             'url': publication.url, 'cite': publication.cite}
            if self.page:
                row['report']['page'] = self.page
            if self.line:
                row['report']['line'] = self.line
        if self.source is Source.SIMILARITY:
            row['score'] = self.score
        return row


# ---------------------------------------------------------------------------
# The archive.


def archive():
    return Path(data_dir()) / 'clrc'


def path_of(report):
    return archive() / (report.value + PUBLICATIONS[report].suffix)


def fetch(reports=None, *, force=False, opener=None):
    """Download the Commission's documents into ``data/clrc``. Returns one row per document.

    Only clrc.ca.gov is read. A PDF is also turned into plain text beside it
    when ``pdftotext`` is on the path (``PDFTOTEXT`` names another).
    """
    opener = opener or _open_url
    folder = archive()
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for report in reports or tuple(Report):
        target = path_of(report)
        publication = PUBLICATIONS[report]
        row = {'report': report.value, 'url': publication.url, 'file': str(target)}
        if force or not target.exists():
            try:
                target.write_bytes(opener(publication.url))
                row['fetched'] = True
            except OSError as error:
                row.update({'fetched': False, 'reason': 'not_fetched', 'error': str(error)})
                rows.append(row)
                continue
        else:
            row['fetched'] = False
        if publication.suffix == '.pdf':
            text = text_of(report, refresh=force)
            row['text'] = text is not None
        rows.append(row)
    _tables.cache_clear()
    _comments.cache_clear()
    return rows


def _open_url(url):
    if not re.match(r'^https?://(?:www\.)?clrc\.ca\.gov/', url):
        raise OSError('not an official source: %s' % url)
    request = urllib.request.Request(url, headers={'User-Agent': 'lawlibrary'})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def _pdftotext():
    named = os.environ.get('PDFTOTEXT')
    if named and Path(named).exists():
        return named
    return shutil.which('pdftotext')


def text_of(report, refresh=False):
    """Plain text of a PDF in the archive, kept beside it. None when neither exists."""
    pdf = path_of(report)
    text = pdf.with_suffix('.txt')
    if text.exists() and not refresh and (not pdf.exists() or text.stat().st_mtime >= pdf.stat().st_mtime):
        return text.read_text(encoding='utf-8')
    if not pdf.exists():
        return None
    tool = _pdftotext()
    if tool is None:
        return text.read_text(encoding='utf-8') if text.exists() else None
    subprocess.run([tool, '-layout', '-enc', 'UTF-8', str(pdf), str(text)], check=True,
                   capture_output=True)
    return text.read_text(encoding='utf-8')


def _docx_paragraphs(path):
    """Each paragraph of a Word file, a tab where the file has one."""
    with zipfile.ZipFile(path) as book:
        xml = book.read('word/document.xml').decode('utf-8')
    rows = []
    for paragraph in re.findall(r'<w:p[ >].*?</w:p>', xml, re.S):
        words = re.sub(r'<w:tab/>', '\t', paragraph)
        words = html.unescape(re.sub(r'<[^>]+>', '', words)).strip()
        if words:
            rows.append(words)
    return rows


# ---------------------------------------------------------------------------
# Disposition tables.

_SECTION = r'\d{3,5}(?:\.\d+)*[a-z]?'
_TABLE_LINE = re.compile(r'^\s*(?P<former>%s)(?P<part>.*?)\s*\.{4,}\s*(?P<targets>\S.*?)\s*$' % _SECTION)
_TARGET = re.compile(r'^(?P<section>%s)?\s*(?P<part>.*)$' % _SECTION)
_SEE = re.compile(r'(?i)^(?P<word>omitted|not continued)\b[\s,]*(?:\(?\s*but see\s+(?P<see>[^)]*)\)?)?\s*$')


def _split_targets(text):
    """``5300(b) (intro. cl.), 5305 (intro. cl.)`` into items; commas inside parentheses stay."""
    items, depth, current = [], 0, ''
    for char in text:
        if char == '(':
            depth += 1
        elif char == ')':
            depth = max(0, depth - 1)
        if char == ',' and depth == 0:
            items.append(current.strip())
            current = ''
            continue
        current += char
    if current.strip():
        items.append(current.strip())
    return items


def _targets(code, text):
    """Provisions named on the right side of a table row. A bare ``(d)`` takes the section before it."""
    rows = []
    previous = ''
    for item in _split_targets(text):
        matched = _TARGET.match(item)
        section = matched.group('section') or previous
        if not section:
            continue
        previous = section
        rows.append(Provision(code, section, (matched.group('part') or '').strip()))
    return tuple(rows)


def _cell(code, former, part, right, act, report, line):
    right = right.strip()
    left = Provision(code, former, part.strip())
    seen = _SEE.match(right)
    if seen is not None:
        see = _targets(code, seen.group('see') or '')
        if seen.group('word').lower() == 'omitted':
            succession = Succession.OMITTED_SEE if see else Succession.OMITTED
        else:
            succession = Succession.NOT_CONTINUED
        return Row(left, (), succession, Source.DISPOSITION_TABLE, report, line=line, see=see, act=act)
    return Row(left, _targets(code, right), Succession.CONTINUED, Source.DISPOSITION_TABLE,
               report, line=line, act=act)


def read_pdf_table(text, code, act, report):
    """Rows of a disposition table printed with dot leaders (the AB 805 table)."""
    rows = []
    for number, line in enumerate((text or '').splitlines(), 1):
        matched = _TABLE_LINE.match(line)
        if matched is None:
            continue
        rows.append(_cell(code, matched.group('former'), matched.group('part'),
                          matched.group('targets'), act, report, number))
    return rows


def read_docx_tables(paragraphs, code, act, report, parallel_act=''):
    """The SB 752 tables: the disposition of the former law, then similar provisions.

    The first table's rows are ``former<TAB>new``; the second, after its own
    heading, is ``new<TAB>similar provision`` in the sibling act and is read
    as ``PARALLEL`` rows.
    """
    rows, parallels = [], []
    second = False
    for number, words in enumerate(paragraphs, 1):
        if '\t' not in words:
            if re.match(r'(?i)^similar provisions', words):
                second = True
            continue
        left, _, right = words.partition('\t')
        left, right = left.strip(), right.strip()
        head = re.match(r'^(%s)(.*)$' % _SECTION, left)
        if head is None:
            continue
        if not second:
            rows.append(_cell(code, head.group(1), head.group(2), right, act, report, number))
            continue
        if re.match(r'(?i)^(?:none|no similar)', right) or not right:
            parallels.append(Row(Provision(code, head.group(1), head.group(2).strip()), (),
                                 Succession.PARALLEL, Source.DISPOSITION_TABLE, report,
                                 line=number, act=parallel_act))
            continue
        parallels.append(Row(Provision(code, head.group(1), head.group(2).strip()),
                             _targets(code, right), Succession.PARALLEL,
                             Source.DISPOSITION_TABLE, report, line=number, act=parallel_act))
    return rows, parallels


@lru_cache(maxsize=None)
def _tables():
    """Every table row on disk, by act. ``(rows, parallels, misses)``."""
    rows, parallels, misses = [], [], []
    for act in RECODIFICATIONS:
        token = act.code.value
        for report in act.tables:
            path = path_of(report)
            if PUBLICATIONS[report].suffix == '.docx':
                if not path.exists():
                    misses.append({'report': report.value, 'reason': 'not_fetched'})
                    continue
                found, sibling = read_docx_tables(_docx_paragraphs(path), token, act.key, report,
                                                  parallel_act=DAVIS_STIRLING.key)
                rows.extend(found)
                parallels.extend(sibling)
            else:
                text = text_of(report)
                if text is None:
                    misses.append({'report': report.value,
                                   'reason': 'not_fetched' if not path.exists() else 'not_extracted'})
                    continue
                rows.extend(read_pdf_table(text, token, act.key, report))
    return tuple(rows), tuple(parallels), tuple(misses)


# ---------------------------------------------------------------------------
# Commission Comments.

_HEADING = re.compile(r'^§ (?P<section>%s)\. ' % _SECTION)
_BLOCK = re.compile(r'^(?:[A-Z][A-Za-z.&\' ]*)Code §§? (?P<span>[\d.a-z -]+?) \((?P<what>added|amended|repealed)\)')
_PAGE = re.compile(r'^\s*(?:(?P<a>\d{1,4})\s{2,}[A-Z].*\[Vol\. \d+\s*$|\d{4}\]\s.*?(?P<b>\d{1,4})\s*$)')
_FORMER = re.compile(
    r'former Sections? (?P<list>%s(?:\([^)]*\))*(?:(?:,\s*|,? and |,? or )%s(?:\([^)]*\))*)*)' % (_SECTION, _SECTION)
)
_ONE = re.compile(r'(?P<section>%s)(?P<part>(?:\([^)]*\))*)' % _SECTION)
_NEW = re.compile(r'\bis new\b')
_CUT_BEFORE = re.compile(
    r'(?:(?:sub)?(?:division|paragraph)s? \([0-9a-zA-Z]{1,4}\) of )+$', re.I
)
_SUBJECT = re.compile(
    r'^(?P<subject>.*?)\b(?:continues|restates|generalizes|supersedes|is similar to|is drawn from|is new)\b'
)


@dataclass(frozen=True)
class Comment:
    """One section's Comment, read. ``rows`` are its sentences that name a former provision or say new."""

    section: str
    page: str
    rows: tuple
    read: bool


_ABBREVIATIONS = frozenset((
    'Civ.', 'Code.', 'Sec.', 'Secs.', 'e.g.', 'i.e.', 'Prob.', 'Fam.', 'Evid.', 'Gov.', "Gov't",
    'Bus.', 'Prof.', 'Corp.', 'Stat.', 'Ch.', 'No.', 'Cal.', 'Rev.', 'Ins.', 'Veh.', 'Proc.',
    'Health', 'Saf.', "Comm'n",
))


def _sentences(text):
    """Sentences of a Comment. A period after a code or section abbreviation does not end one."""
    joined = re.sub(r'\s+', ' ', text).strip()
    pieces, start = [], 0
    for match in re.finditer(r'\.\s+(?=[A-Z(])', joined):
        word = joined[:match.start() + 1].rsplit(' ', 1)[-1]
        if word in _ABBREVIATIONS:
            continue
        pieces.append(joined[start:match.start() + 1].strip())
        start = match.end()
    pieces.append(joined[start:].strip())
    return [piece for piece in pieces if piece]


def _quality(sentence, comment):
    lowered = sentence.casefold()
    if 'restates' in lowered and 'continues' not in lowered:
        return Succession.RESTATED
    if 'generalizes' in lowered:
        return Succession.GENERALIZED
    if 'supersedes' in lowered:
        return Succession.SUPERSEDED
    if 'is similar to' in lowered or 'is drawn from' in lowered:
        return Succession.SIMILAR
    if 'without substantive change' in lowered or 'the substance of' in lowered:
        return Succession.CONTINUED_WITHOUT_SUBSTANTIVE_CHANGE
    if 'except as indicated below' in lowered:
        whole = re.sub(r'\s+', ' ', comment).casefold()
        if re.search(r'(?<!non)substantive changes? (?:is|are) made', whole):
            return Succession.CONTINUED_WITH_CHANGES
        if 'nonsubstantive change' in whole:
            return Succession.CONTINUED_WITHOUT_SUBSTANTIVE_CHANGE
        return Succession.CONTINUED
    if 'without change' in lowered:
        return Succession.CONTINUED_WITHOUT_CHANGE
    return Succession.CONTINUED


def _subject_part(subject):
    """The part of the new section a Comment sentence speaks of.

    ``Subdivision (a) of Section 4095`` is ``(a)``; ``Paragraph (2) of
    subdivision (a)`` is ``(a)(2)``; ``The first sentence of Section 4000``
    keeps its words; ``Section 4080`` is the whole section.
    """
    words = re.sub(r'\s*\bof Section %s\b.*$' % _SECTION, '', subject.strip())
    words = re.sub(r'^(?:[Pp]roposed )?Section %s\b' % _SECTION, '', words).strip()
    if not words or words in ('This section', 'It', 'The section'):
        return ''
    labels = _LABEL.findall(words)
    if labels:
        if words.lower().startswith(('paragraph', 'subparagraph', 'clause')):
            labels = labels[::-1]
        return ''.join('(%s)' % label for label in labels)
    return words[0].lower() + words[1:]


def read_comment(code, section, page, text, act, report):
    """The rows one Comment states. A Comment naming no former provision and not new is unread."""
    rows = []
    for sentence in _sentences(text):
        subject = _SUBJECT.match(sentence)
        if subject is None:
            continue
        named = re.search(r'\bSection (%s)\b' % _SECTION, subject.group('subject'))
        if named is not None and named.group(1) != section:
            continue
        current = Provision(code, section, _subject_part(subject.group('subject')))
        if _NEW.search(sentence[:subject.end() + 1]) and 'former Section' not in sentence:
            rows.append(Row(None, (current,), Succession.NEW, Source.COMMISSION_COMMENT, report,
                            page=page, act=act))
            continue
        cited = _FORMER.search(sentence)
        if cited is None:
            continue
        quality = _quality(sentence, text)
        before = _CUT_BEFORE.search(sentence[:cited.start()])
        lead = ''
        if before is not None:
            lead = ''.join('(%s)' % label for label in reversed(_LABEL.findall(before.group(0))))
        for index, found in enumerate(_ONE.finditer(cited.group('list'))):
            part = found.group('part') or ''
            if index == 0 and lead and not part:
                part = lead
            former = Provision(code, found.group('section'), part)
            rows.append(Row(former, (current,), quality, Source.COMMISSION_COMMENT, report,
                            page=page, act=act))
    return Comment(section=section, page=page, rows=tuple(rows), read=bool(rows))


def read_comments(text, act):
    """Each Comment on a section the act added, from the recommendation's text."""
    lo, hi = act.current
    import query
    code = act.code.value
    comments = []
    inside = False
    page = ''
    section = None
    start_page = ''
    buffer = []
    in_comment = False

    def flush():
        if section is not None and buffer:
            comments.append(read_comment(code, section, start_page, '\n'.join(buffer), act.key, act.comments))

    for line in (text or '').splitlines():
        printed = _PAGE.match(line)
        if printed is not None:
            page = printed.group('a') or printed.group('b') or page
            continue
        block = _BLOCK.match(line.strip())
        if block is not None:
            flush()
            section, buffer, in_comment = None, [], False
            span = block.group('span').replace(' ', '')
            inside = block.group('what') == 'added' and span == '%s-%s' % (lo, hi)
            continue
        if not inside:
            continue
        heading = _HEADING.match(line.strip())
        if heading is not None:
            flush()
            number = heading.group('section')
            section = number if query._in_span(number, lo, hi) else None
            buffer, in_comment = [], False
            start_page = page
            continue
        stripped = line.strip()
        if stripped.startswith('Comment.'):
            in_comment = True
            start_page = page
            buffer.append(stripped[len('Comment.'):])
            continue
        if in_comment:
            buffer.append(stripped)
    flush()
    return comments


@lru_cache(maxsize=None)
def _comments():
    """Every Comment read, by act. ``(comments, misses)``."""
    found, misses = [], []
    for act in RECODIFICATIONS:
        if act.comments is None:
            continue
        text = text_of(act.comments)
        if text is None:
            path = path_of(act.comments)
            misses.append({'report': act.comments.value,
                           'reason': 'not_fetched' if not path.exists() else 'not_extracted'})
            continue
        found.extend(read_comments(text, act))
    return tuple(found), tuple(misses)


# ---------------------------------------------------------------------------
# Shapes and lookups.


def _shaped(rows):
    """Each continuing row with its shape: split when its former section went to several, combined when its target came from several."""
    outgoing = defaultdict(set)
    incoming = defaultdict(set)
    for row in rows:
        if row.former is None or row.succession not in CONTINUING:
            continue
        for target in row.targets:
            outgoing[(row.act, row.former.section)].add(target.section)
            incoming[(row.act, target.section)].add(row.former.section)
    shaped = []
    for row in rows:
        if row.former is None or not row.targets:
            shaped.append(row)
            continue
        split = len(outgoing[(row.act, row.former.section)]) > 1
        combined = any(len(incoming[(row.act, target.section)]) > 1 for target in row.targets)
        shape = (Shape.SPLIT_AND_COMBINED if split and combined else
                 Shape.SPLIT if split else Shape.COMBINED if combined else Shape.ONE_TO_ONE)
        shaped.append(_with(row, shape=shape))
    return shaped


def _with(row, **changes):
    values = {name: getattr(row, name) for name in Row.__dataclass_fields__}
    values.update(changes)
    return Row(**values)


def _matches(provision, subdivision):
    if not subdivision:
        return True
    wanted = tuple(_LABEL.findall(subdivision)) or (str(subdivision).strip('()'),)
    path = provision.path
    if not path:
        return True
    if wanted[0] not in provision.tops():
        return False
    if len(provision.tops()) > 1:
        return True
    deeper = min(len(path), len(wanted))
    return path[1:deeper] == wanted[1:deeper]


def _section_of(code, number):
    import query
    return getattr(code, 'value', code), query.section_address(number)


def _misses():
    _rows, _parallels, table_misses = _tables()
    _found, comment_misses = _comments()
    return list(table_misses) + list(comment_misses)


def repeal_of(code, section, before, after):
    """The act on record that repealed ``section`` between two editions, or None.

    The statute is the recodification's chapter and the act section the
    Commission's proposed legislation gave the repeal; the operative day is
    read from the new sections' notes on the shelf.
    """
    import query
    token = getattr(code, 'value', code)
    for act in RECODIFICATIONS:
        if not act.repeals or act.code.value != token:
            continue
        if not query._in_span(section, *act.former):
            continue
        if not (int(before) <= int(act.chapter.year) + 1 and int(after) >= int(act.chapter.year)):
            continue
        return {
            'act': act.key,
            'statute': 'Stats. %s, Ch. %s, Sec. %s' % (act.chapter.year, act.chapter.chapter, act.repeal_act),
            'bill': act.bill,
            'operative': operative_day(act),
            'basis': 'recodification',
            'report': PUBLICATIONS[act.source].url,
        }
    return None


@lru_cache(maxsize=None)
def _operative(key):
    import history
    act = recodification(key)
    found = history.changes(act.code.value, [act.current], diff=False)
    days = Counter()
    for row in found.get('changes', ()):
        if row['change'] != 'added':
            continue
        days[row.get('operative') or ''] += 1
    days.pop('', None)
    return days.most_common(1)[0][0] if days else ''


def operative_day(act):
    """The day most of the act's new sections say they became operative, read from their notes."""
    try:
        return _operative(act.key)
    except Exception:  # an index that cannot be read leaves the day unknown
        return ''


def successors(code, number, subdivision=None, *, candidates=True, limit=3):
    """Where a former section (or one subdivision of it) went.

    ``rows`` holds every reading: disposition-table rows (the pin), then the
    Commission Comments that name this former provision, then similarity
    candidates when no table row names the section. ``targets`` adds where
    each named new section stands in the newest edition.
    """
    import query
    token, number = _section_of(code, number)
    expression = ('%s %s%s' % (token, number, subdivision or '')).strip()
    acts = [act for act in RECODIFICATIONS
            if act.code.value == token and query._in_span(number, *act.former)]
    if not acts:
        return query._miss(expression, 'not_recodified')
    rows_on_disk, _parallels, _misses_t = _tables()
    if not rows_on_disk and not _comments()[0]:
        return query._miss(expression, 'not_fetched', misses=_misses())
    table = [row for row in _shaped(list(rows_on_disk))
             if row.former is not None and row.former.section == number
             and _matches(row.former, subdivision)]
    comment_rows = []
    for comment in _comments()[0]:
        for row in comment.rows:
            if row.former is not None and row.former.section == number and _matches(row.former, subdivision):
                comment_rows.append(row)
    rows = table + comment_rows
    named_by_table = {row.act for row in table}
    if candidates:
        for act in acts:
            if act.key in named_by_table:
                continue
            rows.extend(similar(act, number, limit=limit))
    acts_out = [_act_record(act) for act in acts]
    if not rows:
        return query._miss(expression, 'not_in_table', recodifications=acts_out)
    return {
        'found': True,
        'citation': expression,
        'code': token,
        'section': number,
        'subdivision': subdivision or '',
        'recodifications': acts_out,
        'rows': [row.record() for row in rows],
        'targets': _standing(token, rows),
        'misses': _misses(),
    }


def predecessors(code, number, *, candidates=True, limit=3):
    """Which former provisions a new section continues, read from the table and the Comment."""
    import query
    token, number = _section_of(code, number)
    expression = '%s %s' % (token, number)
    acts = [act for act in RECODIFICATIONS
            if act.code.value == token and query._in_span(number, *act.current)]
    if not acts:
        return query._miss(expression, 'not_recodified')
    rows_on_disk, parallels, _misses_t = _tables()
    if not rows_on_disk and not _comments()[0]:
        return query._miss(expression, 'not_fetched', misses=_misses())
    keys = {act.key for act in acts}
    rows = [row for row in _shaped(list(rows_on_disk))
            if row.act in keys and any(target.section == number for target in row.targets)]
    rows += [row for row in rows_on_disk
             if row.act in keys and any(item.section == number for item in row.see)]
    for comment in _comments()[0]:
        if comment.section == number:
            rows.extend(comment.rows)
    rows += [row for row in parallels
             if (row.former is not None and row.former.section == number)
             or any(target.section == number for target in row.targets)]
    if candidates and not any(row.source is not Source.SIMILARITY and row.former is not None
                              and row.succession is not Succession.PARALLEL for row in rows):
        for act in acts:
            rows.extend(similar_from(act, number, limit=limit))
    if not rows:
        return query._miss(expression, 'not_in_table', recodifications=[_act_record(a) for a in acts])
    return {
        'found': True,
        'citation': expression,
        'code': token,
        'section': number,
        'recodifications': [_act_record(act) for act in acts],
        'rows': [row.record() for row in rows],
        'misses': _misses(),
    }


def _act_record(act):
    publication = PUBLICATIONS[act.source]
    return {
        'act': act.key,
        'title': act.title,
        'former': list(act.former),
        'current': list(act.current),
        'statute': 'Stats. %s, Ch. %s' % (act.chapter.year, act.chapter.chapter),
        'bill': act.bill,
        'operative': operative_day(act),
        'repeals_former': act.repeals,
        'source': publication.url,
        'tables': [PUBLICATIONS[report].url for report in act.tables],
        'comments': '' if act.comments is None else PUBLICATIONS[act.comments].url,
    }


def _standing(code, rows):
    """Each named new section: is it in the newest edition, and the act its note names now."""
    import history
    numbers = sorted({target.section for row in rows for target in row.targets})
    if not numbers:
        return []
    idxer, resolved, _reason = history._resolve(code)
    if resolved is None:
        return []
    carried = history.code_editions(resolved)
    newest = carried[-1] if carried else None
    docs = history._docs_for_sections(idxer, resolved, numbers)
    out = []
    for number in numbers:
        doc = docs.get((newest, number))
        if doc is None:
            out.append({'section': number, 'current': False, 'session': newest})
            continue
        note = history.read_note(doc.get('SECTION_HISTORY') or '')
        out.append({'section': number, 'current': True, 'session': newest,
                    'statute': note.citation(), 'bill': note.bill, 'action':
                    '' if note.action is None else note.action.value,
                    'effective': note.effective})
    return out


# ---------------------------------------------------------------------------
# Similarity: a candidate, never a pin.

_STOP = frozenset('a an and any as at be by for from has have if in is it its may not of on or shall '
                  'such that the this to which with'.split())


def _tokens(text):
    words = re.findall(r'[a-z]+', (text or '').lower())
    words = [word for word in words if word not in _STOP and len(word) > 2]
    return Counter(words + ['%s_%s' % pair for pair in zip(words, words[1:])])


class _Pool:
    """The new sections in the first edition that carries them, as weighted word vectors."""

    def __init__(self, act):
        import history
        self.act = act
        code = act.code.value
        idxer, resolved, _reason = history._resolve(code)
        carried = history.code_editions(resolved) if resolved else []
        self.former_edition = ''
        self.current_edition = ''
        self.former = {}
        self.current = {}
        for year in carried:
            rows = history._span_rows(idxer, resolved, year, [act.former])
            if rows:
                self.former_edition, self.former = year, rows
        for year in carried:
            rows = history._span_rows(idxer, resolved, year, [act.current])
            if rows:
                self.current_edition, self.current = year, rows
                break
        counts = {number: _tokens(doc.get('LEGAL_TEXT') or '') for number, doc in self.current.items()}
        documents = len(counts) or 1
        frequency = Counter()
        for vector in counts.values():
            frequency.update(vector.keys())
        self.idf = {term: math.log((1 + documents) / (1 + df)) + 1 for term, df in frequency.items()}
        self.vectors = {number: self._weigh(vector) for number, vector in counts.items()}

    def _weigh(self, counts):
        vector = {term: (1 + math.log(tf)) * self.idf.get(term, 1.0) for term, tf in counts.items()}
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1.0
        return {term: value / norm for term, value in vector.items()}

    def rank(self, text, limit):
        query_vector = self._weigh(_tokens(text))
        scored = []
        for number, vector in self.vectors.items():
            small, large = (query_vector, vector) if len(query_vector) < len(vector) else (vector, query_vector)
            score = sum(value * large.get(term, 0.0) for term, value in small.items())
            if score > 0:
                scored.append((round(score, 4), number))
        scored.sort(reverse=True)
        return scored[:limit]


@lru_cache(maxsize=None)
def _pool(key):
    return _Pool(recodification(key))


def similar(act, number, subdivision='', limit=3, text=None):
    """Candidate new sections for a former section by word overlap. Each is a ``CANDIDATE`` row."""
    pool = _pool(act.key)
    doc = pool.former.get(number)
    if text is None:
        if doc is None:
            return []
        text = doc.get('LEGAL_TEXT') or ''
    code = act.code.value
    return [
        Row(Provision(code, number, subdivision), (Provision(code, target),), Succession.CANDIDATE,
            Source.SIMILARITY, act=act.key, score=score,
            page='%s->%s' % (pool.former_edition, pool.current_edition))
        for score, target in pool.rank(text, limit)
    ]


def similar_from(act, number, limit=3):
    """Candidate former sections for a new section, by the same overlap in reverse."""
    pool = _pool(act.key)
    doc = pool.current.get(number)
    if doc is None:
        return []
    target = _tokens(doc.get('LEGAL_TEXT') or '')
    weighted = pool._weigh(target)
    scored = []
    for former, row in pool.former.items():
        vector = pool._weigh(_tokens(row.get('LEGAL_TEXT') or ''))
        score = sum(value * vector.get(term, 0.0) for term, value in weighted.items())
        if score > 0:
            scored.append((round(score, 4), former))
    scored.sort(reverse=True)
    code = act.code.value
    return [
        Row(Provision(code, former), (Provision(code, number),), Succession.CANDIDATE,
            Source.SIMILARITY, act=act.key, score=score,
            page='%s->%s' % (pool.former_edition, pool.current_edition))
        for score, former in scored[:limit]
    ]


# ---------------------------------------------------------------------------
# Coverage.


def coverage(key='davis-stirling', *, candidates=True):
    """How much of the former span the official readings place.

    Counts are over the former sections in the last edition that carries
    them and their top-level subdivisions (``structure.split_nodes``).
    ``by_table`` is a section or subdivision a continuing table row names;
    ``left_out`` is one only ``omitted`` / ``not continued`` rows name;
    ``unplaced`` is one no table row names, which gets similarity
    candidates. New sections are counted by what the table and the
    Comments say about them.
    """
    import query
    from structure import split_nodes
    act = recodification(key)
    if act is None:
        return query._miss(key, 'unknown_act')
    rows_on_disk, _parallels, _table_misses = _tables()
    rows = [row for row in rows_on_disk if row.act == act.key]
    if not rows:
        return query._miss(key, 'not_fetched', misses=_misses())
    pool = _pool(act.key)
    by_section = defaultdict(list)
    for row in rows:
        by_section[row.former.section].append(row)
    sections = {'total': 0, 'by_table': 0, 'left_out': 0, 'unplaced': 0}
    subdivisions = {'total': 0, 'by_table': 0, 'left_out': 0, 'unplaced': 0}
    unplaced, unplaced_subdivisions, left_out = [], [], []
    for number in sorted(pool.former, key=query.section_key):
        sections['total'] += 1
        named = by_section.get(number, [])
        if any(row.succession in CONTINUING for row in named):
            sections['by_table'] += 1
        elif named:
            sections['left_out'] += 1
            left_out.append(number)
        else:
            sections['unplaced'] += 1
            row = {'section': number}
            if candidates:
                row['candidates'] = [item.record() for item in similar(act, number)]
            unplaced.append(row)
        tree = split_nodes(pool.former[number].get('LEGAL_TEXT') or '')
        expected = 'a'
        for child in tree.children:
            label = child.label.strip('()')
            # A top-level subdivision runs (a), (b), (c) in order. A roman
            # clause the outline lifted to the top breaks the run and is
            # not counted as a subdivision.
            if label != expected:
                continue
            expected = chr(ord(expected) + 1)
            subdivisions['total'] += 1
            touching = [row for row in named if not row.former.path or label in row.former.tops()]
            if any(row.succession in CONTINUING for row in touching):
                subdivisions['by_table'] += 1
            elif touching:
                subdivisions['left_out'] += 1
            else:
                subdivisions['unplaced'] += 1
                item = {'section': number, 'subdivision': child.label}
                if candidates:
                    item['candidates'] = [found.record() for found in
                                          similar(act, number, child.label, text=child.text)]
                unplaced_subdivisions.append(item)
    comments, _comment_misses = _comments()
    mine = [comment for comment in comments if comment.rows and comment.rows[0].act == act.key] \
        if act.comments else []
    unread = [comment.section for comment in comments
              if not comment.read and act.comments is not None] if act.comments else []
    named_new = {target.section for row in rows for target in row.targets}
    named_see = {item.section for row in rows for item in row.see} - named_new
    new_sections = sorted(pool.current, key=query.section_key)
    said_new = {comment.section for comment in mine
                if any(row.succession is Succession.NEW for row in comment.rows)
                and not any(row.former is not None for row in comment.rows)}
    return {
        'found': True,
        'act': _act_record(act),
        'editions': {'former': pool.former_edition, 'current': pool.current_edition},
        'table_rows': len(rows),
        'table_rows_by_succession': dict(Counter(row.succession.value for row in rows)),
        'sections': sections,
        'subdivisions': subdivisions,
        'left_out': left_out,
        'unplaced': unplaced,
        'unplaced_subdivisions': unplaced_subdivisions,
        'new_sections': {
            'total': len(new_sections),
            'named_by_table': len([n for n in new_sections if n in named_new]),
            'named_only_as_see': len([n for n in new_sections if n in named_see]),
            'new_by_comment': len([n for n in new_sections if n in said_new]),
            'neither': [n for n in new_sections
                        if n not in named_new and n not in said_new and n not in named_see],
        },
        'comments': {
            'read': len(mine),
            'unread': unread,
            'rows_by_succession': dict(Counter(row.succession.value for comment in mine for row in comment.rows)),
        } if act.comments else None,
        'misses': _misses(),
    }
