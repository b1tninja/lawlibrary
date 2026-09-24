"""Oklahoma Statutes — title PDFs from the Legislature (not the SOS West portal)."""

from publication import State


SOURCE = 'https://www.oklegislature.gov/osStatuesTitle.html'

# Representative CompleteTitles PDFs. Full set is os01.pdf … os90.pdf etc.
TITLE_PDFS = (
    'https://www.oklegislature.gov/OK_Statutes/CompleteTitles/os01.pdf',
    'https://www.oklegislature.gov/OK_Statutes/CompleteTitles/os12.pdf',
    'https://www.oklegislature.gov/OK_Statutes/CompleteTitles/os21.pdf',
)


class Oklahoma(State):
    code = 'US-OK'
    source = SOURCE
    editions = ()

    def list_editions(self):
        return list(TITLE_PDFS)
