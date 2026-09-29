"""The Zoning Code of Sacramento County, from the County's own pages.

The Planning department publishes the code at landuse.saccounty.gov/szc/
as one page per chapter (Chapters 1-7, Title IV Interim Zones, Title IX
Floodplain Management), each a Starlight page whose headings are the
sections: ``<h2>1.4. APPLICABILITY AND JURISDICTION</h2>`` holds
``<h3>1.4.1. General Applicability</h3>`` and so on. ``fetch`` saves the
pages; ``SacramentoZoningCode`` reads a directory of them and yields one
row per numbered section, the shape the indexer takes. The words are the
County's; no commercial host is read.
"""

import html
import os
import re
import urllib.request

from publication import Instrument, Publication

SITE = 'https://landuse.saccounty.gov/szc/'
PAGES = ('ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch6', 'ch7', 'title4', 'title9')
CODE = 'SZC'

_TITLE = re.compile(r'<title>([^<|]+)')
_HEADING = re.compile(r'<h([2-6])\s[^>]*id="([^"]*)"[^>]*>(.*?)</h\1>', re.S)
_NUMBERED = re.compile(r'^\s*(?P<num>\d+(?:\.\d+)*)\.?\s*(?P<title>.*?)\s*$', re.S)
_TAG = re.compile(r'<[^>]+>')
_SPACE = re.compile(r'\s+')
_ANCHOR = re.compile(r'<a class="sl-anchor-link".*?</a>', re.S)


def fetch(dest, pages=PAGES, opener=None):
    """Save each chapter page under ``dest``. Returns the paths written."""
    os.makedirs(dest, exist_ok=True)
    read = opener or (lambda url: urllib.request.urlopen(urllib.request.Request(
        url, headers={'User-Agent': 'lawlibrary (statute reader)'})).read())
    written = []
    for page in pages:
        path = os.path.join(dest, page + '.html')
        with open(path, 'wb') as fh:
            fh.write(read(SITE + page + '/'))
        written.append(path)
    return written


def _words(fragment):
    # A heading carries its own anchor link, a '#' with a screen-reader
    # label ("Section titled ..."); neither is a word of the code.
    text = _TAG.sub(' ', _ANCHOR.sub(' ', fragment))
    text = html.unescape(text)
    return _SPACE.sub(' ', text).strip()


def chapter(page_text):
    """The chapter title and its numbered sections, in order.

    Each section is ``(number, title, level, words)``; ``words`` is the
    text between its heading and the next heading of any level.
    """
    title = _TITLE.search(page_text)
    title = _words(title.group(1)) if title else ''
    marks = list(_HEADING.finditer(page_text))
    found = []
    for index, mark in enumerate(marks):
        heading = _words(mark.group(3))
        numbered = _NUMBERED.match(heading)
        if numbered is None:
            continue
        start = mark.end()
        end = marks[index + 1].start() if index + 1 < len(marks) else len(page_text)
        found.append((numbered.group('num'), numbered.group('title'), int(mark.group(1)), _words(page_text[start:end])))
    return title, found


class SacramentoZoningCode(Publication):
    """A directory of the County's chapter pages, as ``fetch`` saves them."""

    instrument = Instrument.ORDINANCE

    @classmethod
    def accepts(cls, names):
        names = set(names)
        return 'ch1.html' in names and 'ch2.html' in names

    def sections(self, path):
        for page in PAGES:
            file = os.path.join(path, page + '.html')
            if not os.path.isfile(file):
                continue
            with open(file, encoding='utf-8') as fh:
                title, found = chapter(fh.read())
            for number, heading, level, words in found:
                yield {
                    'PK': '%s:%s' % (CODE, number),
                    'LAW_CODE': CODE,
                    'CODE_HEADING': 'Zoning Code of Sacramento County - SZC',
                    'CHAPTER': page,
                    'CHAPTER_HEADING': title,
                    'SECTION_NUM': number,
                    'SECTION_TITLE': heading,
                    'LEGAL_TEXT': words,
                    'ACTIVE_FLG': True,
                    'SUBDIVISION': 'US-CA',
                    'LOCALITY': 'Sacramento County',
                    'SHELF': CODE,
                }
