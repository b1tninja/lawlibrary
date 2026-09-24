"""Tennessee Code Annotated — no government bulk corpus.

The code link is Lexis; the legislature publishes only the annual Code Bill.
"""

from publication import State

SOURCE = 'https://www.capitol.tn.gov/legislation/publications/index.html'


class Tennessee(State):
    code = 'US-TN'
    """Publications index only; there is no full TCA download on a government host."""

    source = SOURCE
    editions = ()

    def list_editions(self):
        return []
