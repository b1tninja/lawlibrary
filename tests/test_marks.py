"""Every reading a parser records on one text, as spans.

A span is a layer, a kind, and two offsets. The words come from the index, so
no sentence is copied here. A section is named by its citation and looked up.
"""

import marks
import query
from citations import document


def _text(code, number):
    doc = query.section(code, number)
    assert doc.get('found'), '%s %s is not in the index' % (code, number)
    return doc.get('text') or ''


def _targets(spans, kind):
    return [
        span.target for span in spans
        if span.layer is marks.Layer.NOTE and span.kind == kind
    ]


def _rows(spans):
    """A record carries no equality, so a test compares the fields."""
    return [
        (span.layer, span.kind, span.start, span.end, span.target)
        for span in spans
    ]


def test_the_book_the_sentence_named_beats_the_book_that_is_open():
    """``Section 7280 of the Revenue and Taxation Code`` is RTC, inside CIV.

    ``annotate`` sees the number and no book. An open book would stamp its own
    code on it. The phrase names another one, and the phrase is the evidence.
    """
    text = _text('CIV', '1940')
    bare = _targets(marks.layers(text, code='CIV'), 'citation')
    assert 'RTC 7280' in bare
    with document('CIV', '1940') as ctx:
        held = _targets(marks.layers(text, code='CIV', context=ctx), 'citation')
    assert held == bare
    with document('CIV', '1940'):
        ambient = _targets(marks.layers(text, code='CIV'), 'citation')
    assert ambient == bare


def test_a_layer_is_asked_for_by_the_word_a_file_stores():
    text = _text('CIV', '1940')
    only = marks.layers(text, code='CIV', only=('note',))
    assert only
    assert {span.layer for span in only} == {marks.Layer.NOTE}
    assert _rows(marks.layers(text, code='CIV', only=(marks.Layer.NOTE,))) == _rows(only)
    assert marks.layers('', code='CIV') == ()


def test_a_longer_reading_sorts_before_a_shorter_one_that_starts_with_it():
    """The client nests spans in one pass, so the order has to allow it."""
    spans = marks.layers(_text('CIV', '1940'), code='CIV')
    assert spans
    for one, two in zip(spans, spans[1:]):
        assert (one.start, -one.end) <= (two.start, -two.end)
    for span in spans:
        assert 0 <= span.start < span.end


def test_the_counts_tally_every_span_that_was_drawn():
    spans = marks.layers(_text('CIV', '1940'), code='CIV')
    tally = marks.counts(spans)
    assert set(tally) <= {member.value for member in marks.Layer}
    counted = sum(
        many for kinds in tally.values() for many in kinds.values()
    )
    assert counted == len(spans)
