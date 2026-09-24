"""Alaska Statutes — official title PDFs (not parsed here)."""

from publication import State

SOURCE = 'https://www.akleg.gov/statutesPDF/Title-1.pdf'
_TITLE_PDF = 'https://www.akleg.gov/statutesPDF/Title-{n}.pdf'


class Alaska(State):
    code = 'US-AK'
    source = SOURCE
    editions = ()

    def list_editions(self):
        # Finite set of title PDFs; no crawl, no PDF parse.
        return [_TITLE_PDF.format(n=n) for n in (1, 2, 3, 4, 5)]
