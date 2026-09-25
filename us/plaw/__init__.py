"""United States public laws. GPO USLM XML from the 113th Congress on.

Earlier Congresses are the slip law on Congress.gov. The bulk page is
``https://www.govinfo.gov/bulkdata/PLAW``. One file is one public law.
"""

import os
import re
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

from publication import Instrument, Publication

BULK = 'https://www.govinfo.gov/bulkdata/PLAW'
SLIP = 'https://www.congress.gov'
FIRST_XML = 113

_NAME = re.compile(r'(?i)PLAW-(\d+)publ(\d+)')


def locate(congress, number):
    """The official file for this public law. XML when GPO publishes it."""
    congress = int(congress)
    number = int(number)
    if congress >= FIRST_XML:
        return '%s/%s/public/PLAW-%spubl%s.xml' % (BULK, congress, congress, number)
    return '%s/%s/plaws/publ%s/PLAW-%spubl%s.pdf' % (SLIP, congress, number, congress, number)


def _local(tag):
    if tag is None:
        return ''
    if '}' in tag:
        return tag.rsplit('}', 1)[-1]
    return tag


def _find(root, name):
    for el in root.iter():
        if _local(el.tag) == name and el.text and el.text.strip():
            return el.text.strip()
    return ''


def _main_text(root):
    for el in root.iter():
        if _local(el.tag) == 'main':
            return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()
    return re.sub(r'\s+', ' ', ''.join(root.itertext())).strip()


class PublicLaws(Publication):
    """One public law. The identity is the Congress, then the law number."""

    instrument = Instrument.STATUTE
    source = BULK

    @classmethod
    def accepts(cls, names):
        if isinstance(names, (set, frozenset, list, tuple)):
            return any(cls.accepts(name) for name in names)
        base = os.path.basename(str(names))
        return bool(_NAME.search(base) and base.lower().endswith('.xml'))

    def locate(self, congress, number):
        return locate(congress, number)

    def fetch(self, congress, number, dest, opener=None):
        """Save the official file under ``dest``. Returns the path."""
        url = locate(congress, number)
        name = url.rstrip('/').rsplit('/', 1)[-1]
        folder = os.fspath(dest)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, name)
        if opener is None:
            request = Request(url, headers={'User-Agent': 'lawlibrary'})
            with urlopen(request, timeout=60) as response:
                body = response.read()
        else:
            body = opener(url)
        with open(path, 'wb') as fh:
            fh.write(body)
        return path

    def sections(self, path):
        tree = ET.parse(path)
        root = tree.getroot()
        congress = _find(root, 'congress')
        number = _find(root, 'docNumber')
        named = _NAME.search(os.path.basename(str(path)))
        if named is not None:
            congress = congress or named.group(1)
            number = number or named.group(2)
        text = _main_text(root)
        if not congress or not number or not text:
            return
        yield {
            'COUNTRY': 'US',
            'SUBDIVISION': 'US',
            'LAW_CODE': 'PL',
            'SECTION_NUM': '%s-%s' % (congress, number),
            'LEGAL_TEXT': text,
            'CITATION': 'PL %s %s' % (congress, number),
            'SESSION': congress,
        }
