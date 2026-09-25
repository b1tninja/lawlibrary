"""Michigan Compiled Laws — legislature chapter XML directory.

Chapter XML files under https://www.legislature.mi.gov/documents/mcl/
(UTF-16; section body is BodyText on MCLSectionInfo). Not one zip.
"""

import os
import xml.etree.ElementTree as ET

from publication import Publication, State

SOURCE = 'https://www.legislature.mi.gov/documents/mcl/'


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def _row(section_num, legal_text):
    return {
        'SECTION_NUM': section_num,
        'LEGAL_TEXT': legal_text,
        'SUBDIVISION': Michigan.code,
    }


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
                tag = _local(child.tag)
                if tag in (
                    'SectionNumber',
                    'MCLNumber',
                    'Label',
                    'Name',
                    'sectionNumber',
                ):
                    text = ''.join(child.itertext()).strip()
                    if text and section_num is None:
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
            yield _row(section_num, ''.join(body.itertext()).strip())
        if not found:
            stem = os.path.splitext(os.path.basename(path))[0]
            yield _row(stem, ''.join(root.itertext()).strip())


class Michigan(State):
    code = 'US-MI'
    source = SOURCE
    editions = (MichiganCompiledLaws,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return MichiganCompiledLaws()
