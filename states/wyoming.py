"""Wyoming Statutes — text-only title PDFs."""

from publication import State

SOURCE = 'https://wyoleg.gov/statutes/compress/'

# Sample title PDFs under the compress directory. No PDF parsing here.
SAMPLE_EDITIONS = (
    SOURCE + 'title01.pdf',
    SOURCE + 'title02.pdf',
)


class Wyoming(State):
    code = 'US-WY'
    source = SOURCE
    editions = ()

    def list_editions(self):
        return list(SAMPLE_EDITIONS)
