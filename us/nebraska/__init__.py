"""Nebraska Revised Statutes — LegalDocs XML distribution.

Legislature GitHub nelegislature/LegalDocs (statute XML). Case annotations
live in sibling <annotation> elements under <law> and are skipped; only the
amendatory section body is yielded.
"""

import os
import xml.etree.ElementTree as ET

from publication import Publication, State

SOURCE = 'https://github.com/nelegislature/LegalDocs'


def _text_excluding(el, skip_tags):
    skip = {t.lower() for t in skip_tags}
    parts = []
    if el.text and el.text.strip():
        parts.append(el.text.strip())
    for child in list(el):
        tag = child.tag.split('}')[-1].lower()
        if tag in skip:
            if child.tail and child.tail.strip():
                parts.append(child.tail.strip())
            continue
        parts.append(_text_excluding(child, skip_tags))
        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())
    return ' '.join(p for p in parts if p).strip()


def _row(section_num, legal_text):
    return {
        'SECTION_NUM': section_num,
        'LEGAL_TEXT': legal_text,
        'SUBDIVISION': Nebraska.code,
    }


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
        body = root.find('.//amendatorysection')
        if body is None:
            body = root.find('.//section')
        if body is None:
            body = root
        # Case notes are <annotation>; revisor notes are <note> / <source>.
        legal_text = _text_excluding(
            body,
            ('annotation', 'note', 'source', 'bookinfo'),
        )
        yield _row(section_num, legal_text)


class Nebraska(State):
    code = 'US-NE'
    source = SOURCE
    editions = (NebraskaStatutes,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return NebraskaStatutes()
