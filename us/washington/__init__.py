"""Washington Revised Code — certified title PDFs."""

from publication import State

SOURCE = 'https://lawfilesext.leg.wa.gov/Law/RCWArchive/2025/pdf/'

# Sample title PDFs under the archive directory. No PDF parsing here.
SAMPLE_EDITIONS = (
    SOURCE + 'RCW%20Title%2001.pdf',
    SOURCE + 'RCW%20Title%2002.pdf',
)


class Washington(State):
    code = 'US-WA'
    source = SOURCE
    editions = ()

    def list_editions(self):
        return list(SAMPLE_EDITIONS)
