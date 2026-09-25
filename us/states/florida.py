"""Florida Statutes — Division of Law Revision download zip.

source points at FLLawDL2026.zip (a Windows Folio/statutes browser installer:
setup.exe, .dll, Folio templates, applets). That zip is not statute HTML/XML
for indexing. This edition parses saved chapter or section HTML from the
statutes site.
"""

from publication import Publication, State
from readers import html_sections

SOURCE = 'https://www.leg.state.fl.us/Statutes/FLLawDL2026.zip'

# Section numbers like "1.01" ahead of a catchline word.
_SECTION_PATTERN = r'(?<![\d.])(\d+\.\d+)\s+(?=[A-Za-z])'


def _stamp(row):
    row = dict(row)
    row['SUBDIVISION'] = Florida.code
    row['LAW_CODE'] = 'FS'
    row['PK'] = 'FS:%s' % row['SECTION_NUM']
    return row


class FloridaChapter(Publication):
    code_heading = 'Florida Statutes'
    session = '2026'
    """One saved chapter or section HTML page from the Florida Statutes site."""

    @classmethod
    def accepts(cls, names):
        # The official zip is a Windows browser, not chapter HTML.
        if isinstance(names, (set, frozenset)):
            return False
        return True

    def sections(self, path):
        for row in html_sections(path, _SECTION_PATTERN):
            yield _stamp(row)


class Florida(State):
    code = 'US-FL'
    source = SOURCE
    editions = (FloridaChapter,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return FloridaChapter()
