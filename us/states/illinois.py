"""Illinois Compiled Statutes — ilga.gov FTP HTML tree.

Directory of section HTML at https://www.ilga.gov/ftp/ILCS/ (not one zip).
The FTP readme says the print at the Secretary of State is the official copy.
"""

from publication import Publication, State
from readers import html_sections

SOURCE = 'https://www.ilga.gov/ftp/ILCS/'

# ILCS cites like "(5 ILCS 5/1)" in section HTML dumps (one capture group).
_ILCS_PATTERN = r'(?i)\((\d+\s+ILCS\s+\d+/[\d.]+)\)'
# Fallback when a dump only has "Sec. 1." / "Section 1.".
_SEC_PATTERN = r'(?i)(?:Section|Sec\.)\s*([\d.]+)'


def _stamp(row):
    row = dict(row)
    row['SUBDIVISION'] = Illinois.code
    row['LAW_CODE'] = 'ILCS'
    row['PK'] = 'ILCS:%s' % row['SECTION_NUM']
    return row


class IllinoisCompiledStatutes(Publication):
    code_heading = 'Illinois Compiled Statutes'
    """One saved ILCS section HTML file from the FTP tree."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        rows = list(html_sections(path, _ILCS_PATTERN))
        if not rows:
            rows = list(html_sections(path, _SEC_PATTERN))
        for row in rows:
            yield _stamp(row)


class Illinois(State):
    code = 'US-IL'
    source = SOURCE
    editions = (IllinoisCompiledStatutes,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return IllinoisCompiledStatutes()
