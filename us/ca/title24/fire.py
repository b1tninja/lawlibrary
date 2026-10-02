"""The California Fire Code, Title 24 Part 9, from its scan's OCR text.

The code is the International Fire Code with California's amendments
printed in place. The State Fire Marshal adopts it (Health and Safety Code
section 13143) and the Building Standards Commission approves and
publishes it (section 18930 et seq.).

The text is Public.Resource.Org's scan on the Internet Archive. Pages carry
furniture that is not the code: the ICC order number, a licence watermark,
running heads, page numbers, and the matrix adoption tables, which the
code itself says are nonregulatory. Those lines are dropped. The big
chapter numerals do not survive OCR, so a section's chapter is read from
its number (903 is in Chapter 9, 1.11 in Chapter 1).

A numbered provision is one row: ``903.3.1.1 NFPA 13 sprinkler systems.``
begins it and the next numbered provision of the same section ends it.

Chapter 80 lists the referenced standards, each with its edition, the
sections that name it, and whether California amends it. California's
amendments to a standard are printed there under ``*NFPA 13, Amended
Sections as follows:``; they are stored as a row of their own, numbered
by the standard (``NFPA 13``), because they are the state's words.
Appendix chapters are adopted only where a local ordinance adopts them and
are not read.
"""

import collections
import json
import os
import re
import sqlite3
from typing import NamedTuple

from adoption import Adoption, Standard, edition_year
from corpus import connect, title24_corpus_path
from publication import Instrument, Publication
from us.ca.title24 import EDITIONS, Part

CODE = 'CFC'
AUTHORITY = ('HSC 13143', 'HSC 18930')

_ORDER = re.compile(r'^\d{9}$')
_PAGE = re.compile(r'^(?:\d{1,3}[A-Z]?|[A-Z]{1,2})-\d{1,3}$')
_RUNNING = re.compile(r'^(?:20\d\d CALIFORNIA FIRE CODE|INTERNATIONAL CODE COUNCIL|[A-Z]+ \d{1,2}, 20\d\d)$')
_WATERMARK = re.compile(r'Copyright ©|License Agreement|@media\.org|Order Number #')
_BARS = re.compile(r'^(?:[|¦]\s*)+')
_MATRIX = 'MATRIX ADOPTION TABLE'
_CHAPTER_TITLE = re.compile(
    r'^CHAPTER (?P<num>\d+[A-Z]?)\s*[-—–]\s*(?P<title>[A-Z][A-Z0-9 ,’\'&/()—–-]*?)\s*$'
)
_CONTINUED = re.compile(r'\s*[—–-]\s*continued\s*$', re.IGNORECASE)
_SECTION = re.compile(r'^SECTION (?P<num>\d+(?:\.\d+)?)(?:\s*[—–-]+\s*(?P<title>\S.*?))?\s*$')
_CAPS = re.compile(r'^[A-Z][A-Z0-9 ,’\'&/()—–-]+$')
_HEADING = re.compile(
    r'^(?:\[[A-Z0-9 /&]{1,8}\]\s*)*'
    r'(?P<num>\d{1,4}(?:\.\d+)+)\*?\s+'
    r'(?P<title>[A-Z“"(\[](?:[^.]|\.(?=\d))*?)\.(?:\s+(?P<rest>.*))?$'
)
_REFERENCED = re.compile(r'^CHAPTER 80\s*[-—–]\s*REFERENCED STANDARDS')
_APPENDIX = re.compile(r'^APPENDIX (?:CHAPTER )?[0-9A-Z]+\b')
_ORG = re.compile(
    r'\b(?:Association|Institute|Society|Council|Laboratories|LLC|Inc|Commission|'
    r'Administration|Agency|Department|Bureau|Corporation|Global|Organization|Board|'
    r'Alliance|Conference|Officials|Manufacturers)\b'
)
_PUBLISHER = re.compile(r'^(?P<acr>[A-Z](?: ?[A-Z0-9]){1,8})\s+(?P<name>[A-Z][A-Za-z].*)$')
_ENTRY = re.compile(
    r'^(?P<num>[A-Z0-9][A-Za-z0-9./ ()-]{0,40}?)\s*[—–]\s*'
    r'(?P<ed>\d{2,4}(?:\s*CA)?[a-z]?(?:\(\d{4}\))?)\s*[:;]\s*(?P<title>.+?)\s*$'
)
_AMENDED = re.compile(r'^\*(?P<acr>[A-Z]+)\s+(?P<num>[0-9]+[A-Z]?),\s*Amended Sections as follows:?\s*$')
_STARRED = re.compile(r'^\*\S')
_REF_LINE = re.compile(r'^(?:\d|Table |Figure |Chapter |Appendix |Section )')
_AS_AMENDED = re.compile(r',?\s*as amended\s*\*?\s*$', re.IGNORECASE)
_SPACE = re.compile(r'[ \t\xa0]+')
_WORD = re.compile(r'[A-Za-z]+')


def read(path):
    """The scan's lines. A damaged byte stays marked (U+FFFD)."""
    with open(path, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace').replace('\r\n', '\n').split('\n')


def _furniture(line):
    """True for a line of page furniture, not of the code."""
    stripped = line.strip()
    return bool(
        _ORDER.match(stripped) or _PAGE.match(stripped) or _RUNNING.match(stripped)
        or _WATERMARK.search(stripped)
    )


def _clean(line):
    return _SPACE.sub(' ', _BARS.sub('', line.strip())).strip().rstrip('|¦ ')


def chapter_titles(lines):
    """Chapter number to its title, from the matrix tables' headings."""
    titles = {}
    for line in lines:
        match = _CHAPTER_TITLE.match(_CONTINUED.sub('', _clean(line)))
        if match and match.group('num') not in titles:
            titles[match.group('num')] = match.group('title').strip(' -—–')
    return titles


def _chapter(section_number):
    """The chapter a section number sits in: 903.3.1.1 is 9, 5704 is 57, 1.11.1 is 1."""
    top = section_number.split('.', 1)[0]
    if not top.isdigit():
        return top
    return str(int(top) // 100) if len(top) >= 3 else top


def _vocabulary(lines):
    return {word.lower() for line in lines for word in _WORD.findall(line)}


def _join(paragraph, vocabulary):
    """One paragraph from its wrapped lines.

    A line that ends in a hyphen joins the next without a space. The
    hyphen stays when the joined word is not a word the code uses
    elsewhere (``fire-`` / ``resistance-rated``), and goes when it is
    (``occu-`` / ``pancy``).
    """
    text = ''
    for line in paragraph:
        if text.endswith('-') and line[:1].islower():
            head = _WORD.findall(text[:-1])
            tail = _WORD.findall(line)
            if head and tail and (head[-1] + tail[0]).lower() in vocabulary:
                text = text[:-1] + line
            else:
                text += line
        elif text:
            text += ' ' + line
        else:
            text = line
    return text


def _paragraphs(body, vocabulary):
    """Paragraphs from lines, a None between two paragraphs.

    A page or column break also leaves a gap. A paragraph that stops
    mid-sentence (a hyphen, or no closing mark, before a lowercase word)
    runs on into the next.
    """
    blocks, current = [], []
    for line in body:
        if line is None:
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)
    merged = []
    for block in blocks:
        if merged and block[0][:1].islower() and not merged[-1][-1].rstrip().endswith(('.', ':', ';')):
            merged[-1].extend(block)
        else:
            merged.append(list(block))
    return '\n'.join(p for p in (_join(block, vocabulary) for block in merged) if p)


class Provision(NamedTuple):
    number: str
    title: str
    words: str
    chapter: str
    chapter_heading: str
    parent: str
    parent_heading: str


def provisions(lines):
    """Each numbered provision of Chapters 1 through 79, in order."""
    titles = chapter_titles(lines)
    running = set(titles.values())
    vocabulary = _vocabulary(lines)
    parent = parent_heading = ''
    heading = None
    body = []
    skipping = False
    titling = False  # the section's title is on the next line
    found = []

    def close():
        if heading is not None:
            found.append(Provision(
                heading['number'], heading['title'], _paragraphs(body, vocabulary),
                _chapter(heading['number']), titles.get(_chapter(heading['number']), ''),
                heading['parent'], heading['parent_heading'],
            ))

    for raw in lines:
        if _furniture(raw):
            continue
        line = _clean(raw)
        if _REFERENCED.match(line) and parent:
            break
        if _MATRIX in line:
            skipping = True
            continue
        section = _SECTION.match(line)
        if section:
            close()
            heading, body, skipping = None, [], False
            parent, parent_heading = section.group('num'), section.group('title') or ''
            titling = not parent_heading
            continue
        if skipping or not parent:
            continue
        if titling and line:
            titling = False
            if _CAPS.match(line):
                parent_heading = line
                continue
        if not line:
            body.append(None)
            continue
        if line in running:
            continue
        match = _HEADING.match(line)
        if match and _belongs(match.group('num'), parent):
            number = match.group('num')
            top = number.split('.', 1)[0]
            if '.' not in parent and top != parent:
                parent, parent_heading = top, ''
            close()
            heading = {'number': number, 'title': _SPACE.sub(' ', match.group('title')).strip(),
                       'parent': parent, 'parent_heading': parent_heading}
            body = [match.group('rest')] if match.group('rest') else []
            continue
        if heading is not None:
            body.append(line)
    close()
    return found


def _belongs(number, parent):
    """True when ``number`` is a provision of section ``parent``, or of a later one in its chapter."""
    if number.startswith(parent + '.'):
        return True
    top = number.split('.', 1)[0]
    if '.' in parent or not (top.isdigit() and parent.isdigit()):
        return False
    return _chapter(top) == _chapter(parent) and int(top) > int(parent)


class Reference(NamedTuple):
    """One standard Chapter 80 lists: its edition, who names it, California's amendments."""

    standard: Standard
    amended: bool
    via: tuple
    amendments: str


def referenced(lines):
    """Every standard in Chapter 80, in order, with California's amendments."""
    start = None
    for index, raw in enumerate(lines):
        if _REFERENCED.match(_clean(raw)):
            start = index
            break
    if start is None:
        return []
    vocabulary = _vocabulary(lines)
    publisher = None
    entries = []
    amending = None  # the entry whose amendments are being read
    for raw in lines[start:]:
        if _furniture(raw):
            continue
        line = _clean(raw)
        if _APPENDIX.match(line):
            break
        if not line:
            if amending is not None:
                amending['amendments'].append(None)
            continue
        head = _PUBLISHER.match(line)
        if head and _ORG.search(head.group('name')) and not _ENTRY.match(line):
            publisher = head.group('acr').replace(' ', '')
            amending = None
            continue
        if publisher is None:
            continue
        entry = _ENTRY.match(line)
        if entry and not line.startswith('*'):
            amending = None
            entries.append({
                'publisher': publisher, 'number': entry.group('num').strip(),
                'edition': edition_year(entry.group('ed')), 'title': entry.group('title'),
                'via': [], 'amendments': [], 'reading': 'title',
            })
            continue
        amended = _AMENDED.match(line)
        if amended or _STARRED.match(line):
            target = None
            if amended:
                wanted = (amended.group('acr'), amended.group('num'))
                for candidate in reversed(entries):
                    if (candidate['publisher'], candidate['number']) == wanted:
                        target = candidate
                        break
            amending = target or (entries[-1] if entries else None)
            if amending is not None and not amended:
                amending['amendments'].append(line.lstrip('*'))
            continue
        if amending is not None:
            amending['amendments'].append(line)
            continue
        if not entries:
            continue
        last = entries[-1]
        if _REF_LINE.match(line):
            last['via'].extend(v.strip() for v in line.split(',') if v.strip())
            last['reading'] = 'via'
        elif last['reading'] == 'title':
            last['title'] += ' ' + line
    found = []
    for item in entries:
        title = _SPACE.sub(' ', item['title']).strip()
        amended = bool(_AS_AMENDED.search(title)) or title.endswith('*') or bool(item['amendments'])
        title = _AS_AMENDED.sub('', title).rstrip('* ').rstrip(',')
        found.append(Reference(
            Standard(item['publisher'], item['number'], item['edition'], title),
            amended,
            tuple(dict.fromkeys(item['via'])),
            _paragraphs(item['amendments'], vocabulary),
        ))
    return found


def _edition_for(path):
    name = os.path.basename(str(path))
    for chosen in EDITIONS:
        if chosen.part is Part.FIRE and name.startswith(chosen.identifier):
            return chosen
    return None


_EXTRA = """
CREATE TABLE IF NOT EXISTS provision (
    pk TEXT PRIMARY KEY,
    title TEXT,
    chapter TEXT,
    chapter_heading TEXT,
    parent TEXT,
    parent_heading TEXT
);

CREATE TABLE IF NOT EXISTS reference (
    designation TEXT,
    publisher TEXT,
    number TEXT,
    edition TEXT,
    title TEXT,
    amended INTEGER,
    via TEXT,
    amendments TEXT
);
"""


class CaliforniaFireCode(Publication):
    """One edition's OCR text, saved from the Internet Archive."""

    instrument = Instrument.REGULATION

    @classmethod
    def accepts(cls, names):
        if isinstance(names, (set, frozenset, list, tuple)):
            return any(_edition_for(name) is not None for name in names)
        return _edition_for(names) is not None

    def sections(self, path):
        chosen = _edition_for(path)
        year = chosen.year if chosen else ''
        lines = read(path)
        seen = collections.Counter()
        for found in provisions(lines):
            seen[found.number] += 1
            number = found.number if seen[found.number] == 1 else '%s#%d' % (found.number, seen[found.number])
            yield {
                'PK': '%s %s:%s' % (CODE, year, number),
                'LAW_CODE': CODE,
                'CODE_HEADING': 'California Fire Code - %s' % CODE,
                'CHAPTER': found.chapter,
                'CHAPTER_HEADING': found.chapter_heading,
                'ARTICLE': found.parent,
                'ARTICLE_HEADING': found.parent_heading,
                'SECTION_NUM': number,
                'SECTION_TITLE': found.title,
                'LEGAL_TEXT': found.words,
                'ACTIVE_FLG': True,
                'SESSION': year,
                'SUBDIVISION': 'US-CA',
                'SHELF': CODE,
            }
        for ref in referenced(lines):
            if not ref.amendments:
                continue
            number = ref.standard.designation
            yield {
                'PK': '%s %s:%s' % (CODE, year, number),
                'LAW_CODE': CODE,
                'CODE_HEADING': 'California Fire Code - %s' % CODE,
                'CHAPTER': '80',
                'CHAPTER_HEADING': 'REFERENCED STANDARDS',
                'ARTICLE': '',
                'ARTICLE_HEADING': '',
                'SECTION_NUM': number,
                'SECTION_TITLE': '%s, Amended Sections' % number,
                'LEGAL_TEXT': ref.amendments,
                'ACTIVE_FLG': True,
                'SESSION': year,
                'SUBDIVISION': 'US-CA',
                'SHELF': CODE,
            }

    def load(self, path, root=None):
        """Write the edition to ``data/codes/US-CA/title24/{year}/9.sqlite``; return the row count.

        A second load replaces the first.
        """
        chosen = _edition_for(path)
        if chosen is None:
            raise ValueError('not a known Fire Code edition: %s' % path)
        rows = list(self.sections(path))
        if not rows:
            raise ValueError('no sections in %s' % path)
        refs = referenced(read(path))
        db = connect(title24_corpus_path(Part.FIRE.value, chosen.year, root=root))
        try:
            db.executescript(_EXTRA)
            for table in ('section', 'provision', 'reference', 'publication'):
                db.execute('DELETE FROM %s' % table)
            db.execute('INSERT INTO publication (session, source, instrument) VALUES (?, ?, ?)',
                       (chosen.year, chosen.page, self.instrument.value))
            db.executemany(
                'INSERT INTO section (pk, law_code, section_num, legal_text, citation, session) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                [(row['PK'], CODE, row['SECTION_NUM'], row['LEGAL_TEXT'],
                  '%s %s' % (CODE, row['SECTION_NUM']), chosen.year) for row in rows],
            )
            db.executemany(
                'INSERT INTO provision (pk, title, chapter, chapter_heading, parent, parent_heading) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                [(row['PK'], row['SECTION_TITLE'], row['CHAPTER'], row['CHAPTER_HEADING'],
                  row['ARTICLE'], row['ARTICLE_HEADING']) for row in rows],
            )
            db.executemany(
                'INSERT INTO reference (designation, publisher, number, edition, title, amended, via, amendments) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                [(r.standard.designation, r.standard.publisher, r.standard.number, r.standard.edition,
                  r.standard.title, int(r.amended), json.dumps(list(r.via)), r.amendments) for r in refs],
            )
            db.commit()
        finally:
            db.close()
        return len(rows)


def adoptions(root=None):
    """Every standard each loaded Fire Code edition names, as adoptions."""
    found = []
    for chosen in EDITIONS:
        if chosen.part is not Part.FIRE:
            continue
        path = title24_corpus_path(Part.FIRE.value, chosen.year, root=root)
        if not os.path.isfile(path):
            continue
        db = sqlite3.connect(path)
        try:
            rows = db.execute(
                'SELECT publisher, number, edition, title, amended, via FROM reference'
            ).fetchall()
        except sqlite3.Error:
            rows = []
        finally:
            db.close()
        for publisher, number, edition, title, amended, via in rows:
            found.append(Adoption(
                adopter=chosen.name,
                standard=Standard(publisher, number, edition, title),
                amended=bool(amended),
                effective=chosen.effective,
                through=chosen.through,
                via=tuple(json.loads(via or '[]')),
                authority=AUTHORITY,
                source=chosen.page,
            ))
    return found
