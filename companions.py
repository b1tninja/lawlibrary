"""Where each citation manual lives, and how a local file would be read.

A posted edition is free at the URL. A lesser edition is sold or behind a
subscription. This module does not fetch either one. A local HTML file can
be split on headings. A PDF stays a pointer until a text extractor exists.
"""

import enum
import os
import re
from html.parser import HTMLParser
from urllib.request import Request, urlopen

from corpus import connect, manual_corpus_path
from parsers import Guide


class Standing(enum.Enum):
    """Whether the words are posted free or sold."""

    POSTED = 'posted'
    LESSER = 'lesser'


class Shape(enum.Enum):
    """The file a reader would open. The value is the string."""

    HTML = 'html'
    PDF = 'pdf'
    SALE = 'sale'


class Edition:
    """One manual. ``source`` is the official page. ``standing`` says if it is free."""

    def __init__(self, guide, title, source, standing, shape, note):
        self.guide = guide
        self.title = title
        self.source = source
        self.standing = standing
        self.shape = shape
        self.note = note

    def companion(self):
        return Companion(self)


EDITIONS = (
    Edition(
        Guide.CALIFORNIA_STYLE_MANUAL,
        'California Rules of Court, rules 1.200 and 8.204',
        'https://courts.ca.gov/cms/rules/index/one/rule1_200',
        Standing.POSTED,
        Shape.HTML,
        'The Judicial Council posts the rules that name the California Style Manual. Rule 8.204 encourages the fourth edition (2000).',
    ),
    Edition(
        Guide.CALIFORNIA_STYLE_MANUAL,
        'California Rules of Court, rule 8.204',
        'https://courts.ca.gov/cms/rules/index/eight/rule8_204',
        Standing.POSTED,
        Shape.HTML,
        'Briefs are encouraged to follow the California Style Manual, fourth edition (2000). The rule page is posted. The manual is not.',
    ),
    Edition(
        Guide.CALIFORNIA_STYLE_MANUAL,
        'California Style Manual (4th ed. 2000)',
        'https://www.courts.ca.gov/cms/rules/index/eight/rule8_204',
        Standing.LESSER,
        Shape.SALE,
        'The Reporter of Decisions prepares the manual. The full text is not posted on courts.ca.gov. Copies are sold.',
    ),
    Edition(
        Guide.BLUEBOOK,
        'The Bluebook: A Uniform System of Citation',
        'https://www.legalbluebook.com/',
        Standing.LESSER,
        Shape.SALE,
        'Published by the Harvard Law Review Association, the Columbia Law Review, the University of Pennsylvania Law Review, and the Yale Law Journal. The book is sold.',
    ),
    Edition(
        Guide.INDIGO,
        'The Indigo Book',
        'https://law.resource.org/pub/us/code/blue/indigobook-2.1.html',
        Standing.POSTED,
        Shape.HTML,
        'Public.Resource.Org posts the second edition as HTML under a CC0 dedication. It implements the practitioner citation system. It is not The Bluebook.',
    ),
    Edition(
        Guide.ALWD,
        'ALWD Guide to Legal Citation',
        'https://www.alwd.org/about-guide',
        Standing.LESSER,
        Shape.SALE,
        'The Association of Legal Writing Directors prepares the guide. The current edition is sold. The Indigo Book describes it as a paid competitor.',
    ),
    Edition(
        Guide.UNIVERSAL,
        'Universal Citation Guide',
        'https://www.aallnet.org/resources-publications/publications/universal-citation-guide/',
        Standing.LESSER,
        Shape.SALE,
        'The American Association of Law Libraries recommends medium-neutral citation. The third edition is sold by William S. Hein & Co.',
    ),
    Edition(
        Guide.APA,
        'APA Style legal reference examples',
        'https://apastyle.apa.org/style-grammar-guidelines/references/examples/clinical-practice-references',
        Standing.POSTED,
        Shape.HTML,
        'The APA Style site posts the statute pattern: name, source, section sign, year, with no italics.',
    ),
    Edition(
        Guide.APA,
        'Publication Manual of the American Psychological Association',
        'https://apastyle.apa.org/products/publication-manual-7th-edition',
        Standing.LESSER,
        Shape.SALE,
        'Chapter 11 is the legal-reference chapter. The manual is sold. The free site is the edition this library uses.',
    ),
    Edition(
        Guide.CHICAGO,
        'The Chicago Manual of Style',
        'https://www.chicagomanualofstyle.org/',
        Standing.LESSER,
        Shape.SALE,
        'The University of Chicago Press sells the manual. It defers to The Bluebook for legal citation and adds ibid for a repeated note. The text is behind a subscription.',
    ),
)


def editions(guide=None, standing=None):
    """The catalog. Filter by guide or by posted versus lesser."""
    rows = list(EDITIONS)
    if guide is not None:
        rows = [row for row in rows if row.guide is guide]
    if standing is not None:
        rows = [row for row in rows if row.standing is standing]
    return rows


class _Heads(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = []
        self._title = None
        self._buf = []
        self._capture = False
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self._skip += 1
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5') and not self._skip:
            self._flush()
            self._capture = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self._skip:
            self._skip -= 1
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5') and self._capture:
            self._title = ' '.join(''.join(self._buf).split())
            self._buf = []
            self._capture = False

    def handle_data(self, data):
        if not self._skip:
            self._buf.append(data)

    def close(self):
        super().close()
        self._flush()

    def _flush(self):
        if not self._title:
            self._buf = []
            return
        body = ' '.join(''.join(self._buf).split())
        self._buf = []
        if body:
            self.sections.append({'title': self._title, 'text': body})


def _slug(source):
    leaf = source.rstrip('/').rsplit('/', 1)[-1]
    leaf = re.sub(r'\.html?$', '', leaf, flags=re.I)
    leaf = re.sub(r'[^A-Za-z0-9]+', '-', leaf).strip('-').lower()
    return leaf or 'index'


def fetch_posted(dest, opener=None):
    """Download posted HTML editions. A lesser edition is skipped."""
    folder = os.fspath(dest)
    os.makedirs(folder, exist_ok=True)
    saved = []
    for edition in editions(standing=Standing.POSTED):
        if edition.shape is not Shape.HTML:
            continue
        name = '%s-%s.html' % (edition.guide.value, _slug(edition.source))
        path = os.path.join(folder, name)
        if opener is None:
            request = Request(
                edition.source,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; lawlibrary/0.2)'},
            )
            with urlopen(request, timeout=60) as response:
                body = response.read()
        else:
            body = opener(edition.source)
        if b'Incapsula' in body or len(body) < 500:
            saved.append({
                'guide': edition.guide.value,
                'path': None,
                'source': edition.source,
                'reason': 'blocked',
            })
            continue
        with open(path, 'wb') as fh:
            fh.write(body)
        saved.append({'guide': edition.guide.value, 'path': path, 'source': edition.source})
    return saved


def load_posted(folder, root=None):
    """Index posted HTML already on disk. One sqlite file per guide."""
    grouped = {}
    for edition in editions(standing=Standing.POSTED):
        if edition.shape is not Shape.HTML:
            continue
        name = '%s-%s.html' % (edition.guide.value, _slug(edition.source))
        path = os.path.join(os.fspath(folder), name)
        if not os.path.isfile(path):
            continue
        reading = Companion(edition).read(path)
        if not reading.get('found'):
            continue
        grouped.setdefault(edition.guide, []).extend(reading['sections'])
    counts = []
    for guide, sections in grouped.items():
        book = guide.value.upper()
        path = manual_corpus_path(book, root=root)
        db = connect(path)
        try:
            db.execute('DELETE FROM section WHERE law_code = ?', (book,))
            db.executemany(
                'INSERT INTO section (pk, law_code, section_num, legal_text, citation, session) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                [
                    (
                        '%s:%s' % (book, index),
                        book,
                        str(index),
                        item['text'],
                        item['title'],
                        None,
                    )
                    for index, item in enumerate(sections, start=1)
                ],
            )
            db.commit()
        finally:
            db.close()
        counts.append({'guide': guide.value, 'sections': len(sections), 'book': book})
    return counts


def search_manual(guide, words, root=None, limit=5):
    """Sections of a loaded manual whose text contains the words."""
    book = guide.value.upper() if isinstance(guide, Guide) else str(guide).strip().upper()
    path = manual_corpus_path(book, root=root)
    if not os.path.isfile(path):
        return {'found': False, 'reason': 'absent', 'guide': book, 'sections': []}
    needle = '%' + words.strip() + '%'
    db = connect(path)
    try:
        rows = db.execute(
            'SELECT citation, legal_text FROM section WHERE law_code = ? AND (legal_text LIKE ? OR citation LIKE ?) LIMIT ?',
            (book, needle, needle, int(limit)),
        ).fetchall()
    finally:
        db.close()
    return {
        'found': True,
        'guide': book,
        'sections': [{'title': title, 'text': text} for title, text in rows],
    }


class Companion:
    """Read a manual file that is already on disk. It does not download one."""

    def __init__(self, edition):
        self.edition = edition

    def read(self, path=None):
        edition = self.edition
        if edition.standing is Standing.LESSER and not path:
            return {
                'found': False,
                'reason': 'lesser',
                'guide': edition.guide.value,
                'title': edition.title,
                'source': edition.source,
            }
        if not path or not os.path.isfile(path):
            return {
                'found': False,
                'reason': 'absent',
                'guide': edition.guide.value,
                'source': edition.source,
            }
        if str(path).lower().endswith('.pdf') or edition.shape is Shape.PDF:
            return {
                'found': False,
                'reason': 'pdf',
                'guide': edition.guide.value,
                'title': edition.title,
                'source': edition.source,
            }
        with open(path, encoding='utf-8') as fh:
            html = fh.read()
        parser = _Heads()
        parser.feed(html)
        parser.close()
        sections = parser.sections
        if len(sections) < 2:
            sections = _article_text(html) or sections
        return {
            'found': True,
            'guide': edition.guide.value,
            'title': edition.title,
            'source': edition.source,
            'sections': sections,
        }


def _article_text(html):
    """One section from the article or main element when the page has no rule headings."""
    match = re.search(r'(?is)<article\b[^>]*>(.*)</article>', html) or re.search(
        r'(?is)<main\b[^>]*>(.*)</main>', html
    )
    if match is None:
        return []
    title = re.search(r'(?is)<h1\b[^>]*>(.*?)</h1>', html) or re.search(
        r'(?is)<title>(.*?)</title>', html
    )
    heading = ' '.join(re.sub(r'<[^>]+>', ' ', title.group(1)).split()) if title else 'Text'
    body = ' '.join(re.sub(r'<[^>]+>', ' ', match.group(1)).split())
    if not body:
        return []
    return [{'title': heading, 'text': body}]
