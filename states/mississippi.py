"""Mississippi Code — legislature links Lexis; no government file."""

from publication import State

SOURCE = 'https://www.legislature.ms.gov/'


class Mississippi(State):
    code = 'US-MS'
    source = SOURCE
    editions = ()

    def list_editions(self):
        return []
