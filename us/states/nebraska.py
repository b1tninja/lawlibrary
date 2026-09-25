"""Nebraska Revised Statutes — LegalDocs XML distribution.

Legislature GitHub nelegislature/LegalDocs (statute XML). Case annotations
live in sibling <annotation> elements under <law> and are skipped; only the
amendatory section body is yielded.
"""

from publication import Publication, State
from readers import xml_sections

SOURCE = 'https://github.com/nelegislature/LegalDocs'

# Case notes are <annotation>; revisor notes are <note> / <source>.
_SKIP = ('annotation', 'note', 'source', 'bookinfo')

# Short book token for the Revised Statutes (not the ISO subdivision).
LAW_CODE = 'NRS'


class NebraskaStatutes(Publication):
    code_heading = 'Nebraska Revised Statutes'
    """One local LegalDocs statute XML file (one section)."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        for row in xml_sections(
            path,
            section_tag='amendatorysection',
            number='statuteno',
            skip_tags=_SKIP,
            copies=('chaptername', 'catchline'),
        ):
            section_num = row['SECTION_NUM']
            out = {
                'PK': '%s:%s' % (LAW_CODE, section_num),
                'LAW_CODE': LAW_CODE,
                'SECTION_NUM': section_num,
                'LEGAL_TEXT': row['LEGAL_TEXT'],
                'SUBDIVISION': Nebraska.code,
            }
            if row.get('chaptername'):
                out['CHAPTER_HEADING'] = row['chaptername']
            if row.get('catchline'):
                out['SECTION_TITLE'] = row['catchline']
            yield out


class Nebraska(State):
    code = 'US-NE'
    source = SOURCE
    editions = (NebraskaStatutes,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return NebraskaStatutes()
