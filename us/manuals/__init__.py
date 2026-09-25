"""Official style and drafting manuals.

HTML editions are indexed. A PDF edition, and a manual that is only named
in a court rule, stays a pointer. The California Style Manual and The
Bluebook are not opened here.
"""

import os
import re
from html.parser import HTMLParser

from corpus import connect, manual_corpus_path
from publication import Instrument, Publication

_RULE = re.compile(r'(?m)^(?=\d+\.\d+\.\s)')
_PART = re.compile(r'^(?P<num>[IVXLC]+)\.\s+(?P<title>.+)$')
_LETTER = re.compile(r'^(?P<letter>[A-Z])\.\s+(?P<title>.+)$')
_SKIP = {
    'table of contents',
    'law & bills',
    'bill status',
}


class _Regions(HTMLParser):
    """Headings and the text that follows each one."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.regions = []
        self._tag = None
        self._buf = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self._skip += 1
        if tag in ('h1', 'h2', 'h3') and not self._skip:
            self._close()
            self._tag = tag

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript') and self._skip:
            self._skip -= 1
        if tag == self._tag:
            self.regions.append((tag, self._text()))
            self._tag = None
            self._buf = []

    def handle_data(self, data):
        if self._skip:
            return
        self._buf.append(data)

    def close(self):
        super().close()
        self._close()

    def _text(self):
        return re.sub(r'\s+', ' ', ''.join(self._buf)).strip()

    def _close(self):
        text = self._text()
        self._buf = []
        if text:
            self.regions.append(('p', text))


def _heading_sections(html, code):
    parser = _Regions()
    parser.feed(html)
    parser.close()
    part = None
    title = ''
    chunks = []

    def emit():
        if not title or title.lower() in _SKIP:
            return
        body = '\n\n'.join(chunks).strip()
        if not body:
            return
        number = title
        match = _PART.match(title)
        if match:
            number = match.group('num')
        else:
            letter = _LETTER.match(title)
            if letter and part:
                number = '%s.%s' % (part, letter.group('letter'))
            elif letter:
                number = letter.group('letter')
        yield_row = {
            'LAW_CODE': code,
            'SECTION_NUM': number,
            'SECTION_TITLE': title,
            'LEGAL_TEXT': body,
        }
        sections.append(yield_row)

    sections = []
    for kind, text in parser.regions:
        if kind == 'h1':
            continue
        if kind in ('h2', 'h3'):
            emit()
            title = text.replace('[top]', '').strip()
            chunks = []
            match = _PART.match(title)
            if match:
                part = match.group('num')
            continue
        if title:
            chunks.append(text)
    emit()
    return sections


def _gpo_sections(html):
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    rows = []
    for chunk in _RULE.split(text):
        chunk = chunk.strip()
        match = re.match(r'(\d+\.\d+)\.\s+(.*)', chunk, re.S)
        if not match:
            continue
        body = re.sub(r'\s+', ' ', match.group(2)).strip()
        if not body:
            continue
        rows.append({
            'LAW_CODE': 'GPO',
            'SECTION_NUM': match.group(1),
            'SECTION_TITLE': match.group(1),
            'LEGAL_TEXT': body,
        })
    return rows


def _store(rows, book, citation_for, session, root):
    if not rows:
        raise ValueError('no sections in %s' % book)
    path = manual_corpus_path(book, root=root)
    db = connect(path)
    try:
        db.execute('DELETE FROM section WHERE law_code = ?', (book,))
        db.executemany(
            'INSERT INTO section (pk, law_code, section_num, legal_text, citation, session) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            [
                (
                    '%s:%s' % (book, row['SECTION_NUM']),
                    book,
                    row['SECTION_NUM'],
                    row['LEGAL_TEXT'],
                    citation_for(row),
                    session,
                )
                for row in rows
            ],
        )
        db.commit()
    finally:
        db.close()
    return len(rows)


class OlrcGuide(Publication):
    """OLRC Detailed Guide. One XHTML page; each heading is a section."""

    instrument = Instrument.MANUAL
    code = 'OLRC'
    source = 'https://uscode.house.gov/detailed_guide.xhtml'
    shape = 'html'

    @classmethod
    def accepts(cls, names):
        name = os.path.basename(str(names)).lower()
        return 'detailed_guide' in name and name.endswith(('.xhtml', '.html', '.htm'))

    def sections(self, path):
        with open(path, encoding='utf-8') as fh:
            html = fh.read()
        return _heading_sections(html, self.code)

    def load(self, path, root=None):
        rows = list(self.sections(path))
        return _store(rows, self.code, lambda row: 'OLRC %s' % row['SECTION_NUM'], '', root)


class HolcGuide(Publication):
    """House Office of the Legislative Counsel online drafting guide."""

    instrument = Instrument.MANUAL
    code = 'HOLC'
    source = 'https://legcounsel.house.gov/holc-guide-legislative-drafting'
    shape = 'html'

    @classmethod
    def accepts(cls, names):
        name = os.path.basename(str(names)).lower()
        return 'holc' in name and name.endswith(('.html', '.htm', '.xhtml'))

    def sections(self, path):
        with open(path, encoding='utf-8') as fh:
            html = fh.read()
        return _heading_sections(html, self.code)

    def load(self, path, root=None):
        rows = list(self.sections(path))
        return _store(rows, self.code, lambda row: 'HOLC %s' % row['SECTION_NUM'], '', root)


class GpoStyleManual(Publication):
    """2008 GPO Style Manual HTML chapters. Each numbered rule is a section.

    The 2016 edition on govinfo is a PDF. This parser reads the HTML edition.
    """

    instrument = Instrument.MANUAL
    code = 'GPO'
    source = 'https://www.govinfo.gov/content/pkg/GPO-STYLEMANUAL-2008/html/GPO-STYLEMANUAL-2008-5.htm'
    shape = 'html'

    @classmethod
    def accepts(cls, names):
        name = os.path.basename(str(names)).lower()
        return name.startswith('gpo-stylemanual') and name.endswith(('.htm', '.html'))

    def sections(self, path):
        with open(path, encoding='utf-8') as fh:
            html = fh.read()
        return _gpo_sections(html)

    def load(self, path, root=None):
        rows = list(self.sections(path))
        session = '2008' if '2008' in os.path.basename(path) else ''
        return _store(rows, self.code, lambda row: 'GPO %s' % row['SECTION_NUM'], session, root)


class Manuals:
    """Catalog of official manuals. ``edition`` picks a parser. It does not fetch."""

    editions = (OlrcGuide, HolcGuide, GpoStyleManual)
    pointers = (
        {
            'book': 'GPO-2016',
            'title': 'U.S. Government Publishing Office Style Manual (2016)',
            'url': 'https://www.govinfo.gov/content/pkg/GPO-STYLEMANUAL-2016/pdf/GPO-STYLEMANUAL-2016.pdf',
            'shape': 'pdf',
        },
        {
            'book': 'HOLC-2022',
            'title': "House Legislative Counsel's Manual on Drafting Style (December 2022)",
            'url': 'https://legcounsel.house.gov/sites/evo-subsites/legcounsel-evo.house.gov/files/documents/ManualDraftStyle_2022.pdf',
            'shape': 'pdf',
        },
        {
            'book': 'CSM',
            'title': 'California Style Manual',
            'url': 'https://courts.ca.gov/cms/rules/index/one/rule1_200',
            'shape': 'named',
        },
    )

    def edition(self, path):
        for parser in self.editions:
            if parser.accepts(path):
                return parser()
        raise TypeError('no manual parser for %s' % os.path.basename(path))

    def sections(self, path):
        return self.edition(path).sections(path)

    def load(self, path, root=None):
        return self.edition(path).load(path, root=root)
