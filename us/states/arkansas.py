"""Arkansas Code — legislature points at Lexis; no government file."""

from publication import State

SOURCE = 'https://www.arkleg.state.ar.us/ArkansasLaw'


class Arkansas(State):
    code = 'US-AR'
    source = SOURCE
    editions = ()

    def list_editions(self):
        return []
