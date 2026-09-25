"""United States Code — OLRC USLM XML (release-point zips).

Parse format: official USLM ``<section>`` elements from title XML in an
OLRC release-point zip (or a local title ``.xml``). The USLM user guide
names ``section`` as the primary hierarchical level in a USC title.

Title 42 is not positive law. Ingest stores prima facie Code text for
search; it is not the Statutes at Large. Prefer USLM over XHTML, PDF, or
PCC of the same title. One publication is the whole Code
(``data/codes/US.sqlite``).
"""

import os
import re
import xml.etree.ElementTree as ET
import zipfile

from corpus import connect, corpus_path
from publication import Instrument, Publication

SOURCE = 'https://uscode.house.gov/download/download.shtml'
DOWNLOAD = 'https://uscode.house.gov/download/'
_XML_HREF = re.compile(
    r'href="(releasepoints/us/pl/(?P<congress>\d+)/(?P<law>\d+)/xml_usc[^"]+\.zip)"'
)
# Current release point as of docs/special/us-code.md (PL 119-111).
TITLE_1_ZIP = (
    'https://uscode.house.gov/download/releasepoints/us/pl/119/111/'
    'xml_usc01@119-111.zip'
)
TITLE_42_ZIP = (
    'https://uscode.house.gov/download/releasepoints/us/pl/119/111/'
    'xml_usc42@119-111.zip'
)
ALL_TITLES_ZIP = (
    'https://uscode.house.gov/download/releasepoints/us/pl/119/111/'
    'xml_uscAll@119-111.zip'
)

_TITLE_IN_IDENT = re.compile(r'/usc/t(\d+[a-z]?)', re.IGNORECASE)
_SECTION_IN_IDENT = re.compile(r'/s([^/]+)', re.IGNORECASE)
_TITLE_IN_NAME = re.compile(r'usc(\d+[a-z]?)', re.IGNORECASE)
_SECTION_SIGN = re.compile(r'^[§\s]+')
_RELEASE_IN_NAME = re.compile(r'@([\d-]+)')


def _local(tag):
    if tag is None:
        return ''
    if '}' in tag:
        return tag.rsplit('}', 1)[-1]
    return tag


def _attr(el, name):
    for key, value in el.attrib.items():
        if _local(key) == name or key == name:
            return value
    return None


def _plain(el):
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()


def _is_title_xml(name):
    """True for an OLRC USLM title file such as ``usc42.xml``."""
    base = os.path.basename(str(name)).lower()
    return base.endswith('.xml') and 'usc' in base


def _title_from_path(path):
    match = _TITLE_IN_NAME.search(os.path.basename(path))
    return match.group(1) if match else None


def _release_from_path(path):
    match = _RELEASE_IN_NAME.search(os.path.basename(path))
    return match.group(1) if match else ''


def _title_from_ident(ident):
    if not ident:
        return None
    match = _TITLE_IN_IDENT.search(ident)
    return match.group(1) if match else None


def _section_from_ident(ident):
    if not ident:
        return None
    match = _SECTION_IN_IDENT.search(ident)
    return match.group(1) if match else None


def _section_num(section):
    num_el = None
    for child in section:
        if _local(child.tag).lower() == 'num':
            num_el = child
            break
    if num_el is not None:
        value = _attr(num_el, 'value')
        if value:
            return str(value).strip()
        text = _SECTION_SIGN.sub('', _plain(num_el)).strip().rstrip('.')
        if text:
            return text
    return _section_from_ident(_attr(section, 'identifier'))


def _section_text(section):
    """Plain text of the section body; skip editorial notes and source credit."""
    parts = []
    for child in section:
        name = _local(child.tag).lower()
        if name in ('notes', 'note', 'sourcecredit', 'footnote', 'endnote'):
            continue
        text = _plain(child)
        if text:
            parts.append(text)
    if not parts:
        text = _plain(section)
        if text:
            parts.append(text)
    return '\n\n'.join(parts)


def _title_from_tree(root, fallback=None):
    ident = _attr(root, 'identifier')
    title = _title_from_ident(ident)
    if title:
        return title
    for el in root.iter():
        if _local(el.tag).lower() != 'title':
            continue
        title = _title_from_ident(_attr(el, 'identifier'))
        if title:
            return title
        for child in el:
            if _local(child.tag).lower() != 'num':
                continue
            value = _attr(child, 'value')
            if value:
                return str(value).strip()
    return fallback


def _title_heading(root, title):
    """Printed title name when the USLM file names it (num + heading)."""
    for el in root.iter():
        if _local(el.tag).lower() != 'title':
            continue
        num_text = heading = ''
        for child in el:
            name = _local(child.tag).lower()
            if name == 'num':
                num_text = _plain(child)
            elif name == 'heading':
                heading = _plain(child)
        if num_text or heading:
            return ('%s%s' % (num_text, heading)).strip() or None
    if title:
        return 'Title %s' % title
    return None


def _law_code(title):
    """Whoosh token such as ``42USC`` from the title number."""
    if not title:
        return None
    text = str(title).strip()
    if text.upper().endswith('USC'):
        return text.upper() if text[-3:].isalpha() else text
    return '%sUSC' % text


def _label(el):
    """Number and heading printed on a title or chapter element."""
    num = heading = ''
    for child in el:
        name = _local(child.tag).lower()
        if name == 'num':
            num = child.attrib.get('value') or _plain(child)
        elif name == 'heading':
            heading = _plain(child)
    return (num or '').strip(), (heading or '').strip()


def _outline(el, parents):
    """Title and chapter that contain this section."""
    fields = {}
    cur = parents.get(el)
    while cur is not None:
        name = _local(cur.tag).lower()
        if name in ('title', 'chapter'):
            key = name.upper()
            if key not in fields:
                num, heading = _label(cur)
                if num:
                    fields[key] = num
                if heading:
                    fields['%s_HEADING' % key] = heading
        cur = parents.get(cur)
    return fields


def _yield_sections(root, title):
    from readers import parent_map
    code_heading = _title_heading(root, title)
    parents = parent_map(root)
    for el in root.iter():
        if _local(el.tag).lower() != 'section':
            continue
        num = _section_num(el)
        text = _section_text(el)
        if not num or not text:
            continue
        title_num = (
            _title_from_ident(_attr(el, 'identifier'))
            or title
        )
        law_code = _law_code(title_num)
        if not law_code:
            continue
        row = {
            'COUNTRY': 'US',
            'SUBDIVISION': 'US',
            'LAW_CODE': law_code,
            'SECTION_NUM': num,
            'LEGAL_TEXT': text,
        }
        if code_heading:
            row['CODE_HEADING'] = code_heading
        row.update(_outline(el, parents))
        yield row


BROWSE = 'https://uscode.house.gov/view.xhtml'
ARCHIVES = 'https://uscode.house.gov/download/annualhistoricalarchives/XHTML'
RELEASES = 'https://uscode.house.gov/download/releasepoints/us/pl'
_TITLE_TOKEN = re.compile(r'^0*(\d+)([a-z]?)$', re.IGNORECASE)
_ARCHIVE_NAME = re.compile(r'(?i)^(\d{4})usc(\d+[a-z]?)\.htm$')
_ITEM_PATH = re.compile(r'itempath:([^>]*?/Sec\.\s*([^-\s>]+))')


def title_token(title):
    """``42`` and ``5a`` become the filename token ``42`` and ``05a``."""
    match = _TITLE_TOKEN.match(str(title).strip())
    if match is None:
        raise ValueError('not a title number: %s' % title)
    return '%02d%s' % (int(match.group(1)), match.group(2).lower())


def locate_section(title, section):
    """The current classified section on the House site.

    A bare ``42 U.S.C. 12101`` names this text. A public-law number names
    the slip law instead.
    """
    return (
        '%s?req=granuleid:USC-prelim-title%s-section%s&num=0&edition=prelim'
        % (BROWSE, title, section)
    )


def locate_archive(year, title=None):
    """Annual historical archive. One title is XHTML; the year is one zip."""
    year = int(year)
    if title is None:
        return '%s/%s.zip' % (ARCHIVES, year)
    return '%s/%s/%susc%s.htm' % (ARCHIVES, year, year, title_token(title))


def locate_release(congress, law, title=None):
    """A prior (or current) release point. XML, one title or every title."""
    congress = int(congress)
    law = str(law).strip()
    token = 'All' if title is None else title_token(title)
    return '%s/%s/%s/xml_usc%s@%s-%s.zip' % (
        RELEASES, congress, law, token, congress, law,
    )


def _fetch(url, dest, opener=None):
    from urllib.request import Request, urlopen
    name = url.rstrip('/').rsplit('/', 1)[-1]
    folder = os.fspath(dest)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    if opener is None:
        request = Request(url, headers={'User-Agent': 'lawlibrary'})
        with urlopen(request, timeout=120) as response:
            body = response.read()
    else:
        body = opener(url)
    with open(path, 'wb') as fh:
        fh.write(body)
    return path


def _archive_sections(path):
    """Sections marked by an ``itempath`` comment that names ``Sec.``."""
    named = _ARCHIVE_NAME.search(os.path.basename(str(path)))
    if named is None:
        return
    year, token = named.group(1), named.group(2)
    law_code = _law_code(token)
    text = open(path, encoding='utf-8', errors='replace').read()
    marks = list(_ITEM_PATH.finditer(text))
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        body = re.sub(r'<[^>]+>', ' ', text[mark.end():end])
        body = re.sub(r'\s+', ' ', body).strip()
        if not body:
            continue
        yield {
            'COUNTRY': 'US',
            'SUBDIVISION': 'US',
            'LAW_CODE': law_code,
            'SECTION_NUM': mark.group(2),
            'LEGAL_TEXT': body,
            'CITATION': '%s %s' % (law_code, mark.group(2)),
            'SESSION': year,
        }


def xml_downloads(page):
    """XML release-point zips named on the House download page.

    The current page is Public Law 119-111. Each href is one title, or every
    title in ``xml_uscAll``.
    """
    found = []
    for match in _XML_HREF.finditer(page or ''):
        found.append({
            'congress': match.group('congress'),
            'law': match.group('law'),
            'url': DOWNLOAD + match.group(1),
        })
    return found


class UnitedStatesCode(Publication):
    """OLRC USLM title XML. Walks ``<section>``; one class for every title."""

    instrument = Instrument.STATUTE

    @classmethod
    def accepts(cls, names):
        if isinstance(names, (set, frozenset, list, tuple)):
            return any(_is_title_xml(n) for n in names)
        return _is_title_xml(names)

    def sections(self, path):
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zf:
                for info in zf.infolist():
                    if info.is_dir() or not _is_title_xml(info.filename):
                        continue
                    with zf.open(info) as fh:
                        tree = ET.parse(fh)
                    title = _title_from_tree(
                        tree.getroot(),
                        _title_from_path(info.filename),
                    )
                    yield from _yield_sections(tree.getroot(), title)
            return
        tree = ET.parse(path)
        root = tree.getroot()
        title = _title_from_tree(root, _title_from_path(path))
        yield from _yield_sections(root, title)

    def load(self, path, root=None):
        """Parse local USLM title XML (or release zip) into ``US.sqlite``.

        Replaces existing rows for the titles present in the file so a
        second load does not duplicate. ``pk`` is ``{title}:{section}``;
        citation is ``{title} USC {section}``. ``session`` is the release
        id from the path when present, else empty.
        """
        rows = list(self.sections(path))
        if not rows:
            raise ValueError('no USC sections in %s' % path)
        session = _release_from_path(path)
        titles = sorted({row['LAW_CODE'] for row in rows})
        db_path = corpus_path('US', root=root)
        db = connect(db_path)
        try:
            db.executemany(
                'DELETE FROM section WHERE law_code = ?',
                [(title,) for title in titles],
            )
            db.executemany(
                'INSERT INTO section '
                '(pk, law_code, section_num, legal_text, citation, session) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                [
                    (
                        '%s:%s' % (row['LAW_CODE'], row['SECTION_NUM']),
                        row['LAW_CODE'],
                        row['SECTION_NUM'],
                        row['LEGAL_TEXT'],
                        '%s %s' % (row['LAW_CODE'], row['SECTION_NUM']),
                        session,
                    )
                    for row in rows
                ],
            )
            db.commit()
        finally:
            db.close()
        return len(rows)

    def locate(self, congress, law, title=None):
        return locate_release(congress, law, title)

    def fetch(self, congress, law, dest, title=None, opener=None):
        """Save one release-point XML zip. ``title`` omitted is every title."""
        return _fetch(locate_release(congress, law, title), dest, opener)


class AnnualCode(Publication):
    """A bound-year United States Code title, as House XHTML.

    USLM begins with the 113th Congress release points. Earlier editions,
    and the later bound years, are this file. The GPO locator zip is the
    typesetting source and is not this text.
    """

    instrument = Instrument.STATUTE
    source = ARCHIVES

    @classmethod
    def accepts(cls, names):
        if isinstance(names, (set, frozenset, list, tuple)):
            return any(cls.accepts(name) for name in names)
        return bool(_ARCHIVE_NAME.search(os.path.basename(str(names))))

    def locate(self, year, title=None):
        return locate_archive(year, title)

    def fetch(self, year, dest, title=None, opener=None):
        """Save one title's XHTML, or the whole-year zip when ``title`` is omitted."""
        return _fetch(locate_archive(year, title), dest, opener)

    def sections(self, path):
        yield from _archive_sections(path)
