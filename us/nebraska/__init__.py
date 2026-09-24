"""Nebraska Revised Statutes — LegalDocs XML distribution."""

import os
import xml.etree.ElementTree as ET

from publication import Publication, State


SOURCE = 'https://github.com/nelegislature/LegalDocs'


class NebraskaStatutes(Publication):
    """One local LegalDocs statute XML file (one section)."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        root = ET.parse(path).getroot()
        num_el = root.find('.//statuteno')
        if num_el is not None and (num_el.text or '').strip():
            section_num = num_el.text.strip()
        else:
            section_num = os.path.splitext(os.path.basename(path))[0]
        # Element text is the section body.
        body = root.find('.//amendatorysection')
        if body is None:
            body = root.find('.//section')
        if body is None:
            body = root
        legal_text = ''.join(body.itertext()).strip()
        yield {'SECTION_NUM': section_num, 'LEGAL_TEXT': legal_text}


class Nebraska(State):
    code = 'US-NE'
    source = SOURCE
    editions = (NebraskaStatutes,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return NebraskaStatutes()
