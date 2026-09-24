"""Michigan Compiled Laws — legislature chapter XML directory."""

import os
import xml.etree.ElementTree as ET

from publication import Publication, State

SOURCE = 'https://www.legislature.mi.gov/documents/mcl/'


class MichiganCompiledLaws(Publication):
    """One local MCL chapter XML file; section body is BodyText."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        root = ET.parse(path).getroot()
        found = False
        for parent in root.iter():
            body = None
            section_num = None
            for child in list(parent):
                tag = child.tag.split('}')[-1]
                if tag in ('SectionNumber', 'Name', 'sectionNumber'):
                    text = (child.text or '').strip()
                    if text:
                        section_num = text
                elif tag == 'BodyText':
                    body = child
            if body is None:
                continue
            found = True
            if not section_num:
                section_num = (
                    parent.get('number')
                    or parent.get('id')
                    or parent.get('name')
                    or os.path.splitext(os.path.basename(path))[0]
                )
            yield {
                'SECTION_NUM': section_num,
                'LEGAL_TEXT': ''.join(body.itertext()).strip(),
            }
        if not found:
            stem = os.path.splitext(os.path.basename(path))[0]
            yield {
                'SECTION_NUM': stem,
                'LEGAL_TEXT': ''.join(root.itertext()).strip(),
            }


class Michigan(State):
    code = 'US-MI'
    source = SOURCE
    editions = (MichiganCompiledLaws,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return MichiganCompiledLaws()
