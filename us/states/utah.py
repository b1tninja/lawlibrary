"""Utah Code — Legislative Research XML API."""

from publication import Publication, State
from readers import xml_sections

SOURCE = 'https://glen.le.utah.gov/code/'
# Developer token is path-scoped; required to fetch. Do not invent one.
TOKEN_NOTE = SOURCE + ' (developer token required)'

# Short book token for the Utah Code (not the ISO subdivision).
LAW_CODE = 'UT'


class UtahCode(Publication):
    code_heading = 'Utah Code'
    """One saved XML document from the glen.le.utah.gov code API (local fixture)."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        for row in xml_sections(
            path,
            section_tag='section',
            number='number',
            skip_tags=(),
        ):
            section_num = row['SECTION_NUM']
            yield {
                'PK': '%s:%s' % (LAW_CODE, section_num),
                'LAW_CODE': LAW_CODE,
                'SECTION_NUM': section_num,
                'LEGAL_TEXT': row['LEGAL_TEXT'],
                'SUBDIVISION': Utah.code,
            }


class Utah(State):
    code = 'US-UT'
    source = SOURCE
    editions = (UtahCode,)

    def list_editions(self):
        return [TOKEN_NOTE]
