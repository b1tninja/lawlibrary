"""Maine Revised Statutes — title PDF distribution (no PDF parsing)."""

from publication import State

SOURCE = 'https://legislature.maine.gov/legis/statutes/homepage.html'
TITLE_PDF = 'https://www.mainelegislature.org/legis/statutes/{n}/title{n}.pdf'


class Maine(State):
    code = 'US-ME'
    source = SOURCE
    editions = ()

    def list_editions(self):
        # Finite official title PDFs; parsers are not provided (do not read PDF bytes).
        return [TITLE_PDF.format(n=n) for n in (1, 2, 3)]
