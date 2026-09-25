"""Office and unit readings, checked against the sections that teach them.

Add an example on the noun class when that class's rule is worth checking.
A class with no rule is not parsed and has nothing to cite. The words come
from the index.
"""

import query
from canons import SPECIMENS, find_signals


def test_each_specimen_carries_the_reading_it_was_kept_for():
    for specimen in SPECIMENS:
        doc = query.section(specimen.code, specimen.number)
        if not doc.get('found'):
            continue
        text = doc.get('text') or ''
        hits = find_signals(text, specimen.canon)
        folded = specimen.text.casefold()
        assert any(folded in signal.text.casefold() for signal in hits), specimen.text
