"""Utah Code — Legislative Research XML API."""

import os
import xml.etree.ElementTree as ET

from publication import Publication, State

SOURCE = 'https://glen.le.utah.gov/code/'


class UtahCode(Publication):
    """One saved XML document from the glen.le.utah.gov code API."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        tree = ET.parse(path)
        root = tree.getroot()
        found = False
        for elem in root.iter():
            tag = elem.tag.split('}')[-1].lower()
            if tag not in ('section', 'sec'):
                continue
            number = (
                elem.get('number')
                or elem.get('num')
                or elem.get('id')
                or elem.get('SECTION_NUM')
            )
            text = ''.join(elem.itertext()).strip()
            if not number:
                number = os.path.splitext(os.path.basename(path))[0]
            if text:
                found = True
                yield {'SECTION_NUM': number, 'LEGAL_TEXT': text}
        if not found:
            text = ''.join(root.itertext()).strip()
            stem = os.path.splitext(os.path.basename(path))[0]
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text}


class Utah(State):
    code = 'US-UT'
    source = SOURCE
    editions = (UtahCode,)

    def list_editions(self):
        return [SOURCE]
