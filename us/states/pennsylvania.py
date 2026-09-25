"""Pennsylvania Consolidated Statutes — official title PDFs (not parsed here)."""

from publication import State

SOURCE = 'https://www.palegis.us/statutes/consolidated'
_TITLE_PDF = 'https://www.legis.state.pa.us/WU01/LI/LI/CT/PDF/{n}/{n}.PDF'


class Pennsylvania(State):
    code = 'US-PA'
    source = SOURCE
    editions = ()

    def list_editions(self):
        # Sample title PDFs; no crawl, no PDF parse.
        return [_TITLE_PDF.format(n=n) for n in ('18', '01')]
