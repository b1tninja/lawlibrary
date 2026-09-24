"""Georgia Code — the General Assembly links the public code to Lexis.

There is no government corpus to download. ``source`` is the legislature site;
the code itself is hosted at Lexis
(https://www.lexisnexis.com/hottopics/gacode/).
"""

from publication import State

SOURCE = 'https://www.legis.ga.gov/'


class Georgia(State):
    code = 'US-GA'
    source = SOURCE
    editions = ()

    def list_editions(self):
        return []
