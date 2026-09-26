"""The markup California publishes its statutes in.

CAML borrows tags from XHTML, so it reads as HTML until it does not: an empty
span is a character, and a fraction is a number. The documents here are built
from the grammar in ``docs/caml.md``, not copied from a section; where a real
section is needed it is looked up.
"""

import caml
import query


def _caml(body):
    return caml.parse(
        '<caml:Content xmlns:caml="%s">%s</caml:Content>' % (caml.NAMESPACE, body)
    )


def _words(body):
    return caml.words(_caml(body))


def test_an_empty_span_is_the_space_it_stands_for():
    """CAML writes the space after a subdivision label as a span.

    An HTML reader drops an empty element, which runs the label into the
    words. The space is a character of the section, so it is read as one.
    """
    assert _words('<p>(a)<span class="EnSpace"/>The term applies.</p>') == '(a) The term applies.'
    assert _words('<p>one<span class="EmSpace"/>two</p>') == 'one two'
    assert _words('<p>Article XIII<span class="ThinSpace"/>B</p>') == 'Article XIII B'
    assert _words('<p>at<span class="NbSpace"/>noon</p>') == 'at noon'


def test_a_leader_is_a_rule_and_carries_no_word():
    """The dots ruled across a form are not words in the section."""
    for word in ('DottedLeaders', 'SpacedLeaders', 'DashedLeaders', 'UnderlinedLeaders'):
        assert _words('<p>Name<span class="%s"/></p>' % word) == 'Name'
    assert _words('<p><span class="DottedLeaders"/></p>') == ''


def test_a_fraction_is_a_number_and_not_two_digits():
    """``33`` and a third is ``33 1/3``. Run together it is three thousand."""
    third = ('<caml:Fraction><caml:Numerator>1</caml:Numerator>'
             '<caml:Denominator>3</caml:Denominator></caml:Fraction>')
    assert _words('<p>not less than 33%s percent</p>' % third) == 'not less than 33 1/3 percent'
    assert '3313' not in _words('<p>33%s</p>' % third)


def test_a_tipped_in_plate_has_no_words():
    """A plate bound into the printed volume is not part of the text."""
    body = '<p>before</p><caml:TipIn numPages="2"/><p>after</p>'
    assert _words(body) == 'before\n\nafter'
    plate = [
        piece for piece in _caml(body).walk()
        if piece.element is caml.Element.INSERT
    ]
    assert plate and plate[0].attrs['numPages'] == '2'


def test_a_labelled_field_keeps_its_caption():
    body = ('<p>I,<span class="EnSpace"/><caml:LabelledField>'
            '<span class="SpacedLeaders"/>(name)<span class="SpacedLeaders"/>'
            '</caml:LabelledField>, agree</p>')
    assert _words(body) == 'I, (name), agree'


def test_a_table_keeps_its_rows_and_its_cells():
    body = ('<table><tbody>'
            '<tr><td><p>Item</p></td><td><p>Rate</p></td></tr>'
            '<tr><td><p>One</p></td><td><p>Two</p></td></tr>'
            '</tbody></table>')
    assert _words(body) == 'Item\tRate\nOne\tTwo'


def test_each_block_stands_on_its_own():
    assert _words('<p>one</p><p>two</p>') == 'one\n\ntwo'
    assert _words('<p>one<br/>two</p>') == 'one\ntwo'
    assert _words('<h1>A Heading</h1><p>words</p>') == 'A Heading\n\nwords'


def test_the_closed_sets_are_the_words_the_file_writes():
    """A member's value is what the markup says, so a file can be matched."""
    assert caml.Element.DOCUMENT.value == 'caml:Content'
    assert caml.Element.PARAGRAPH.value == 'p'
    assert caml.Glyph.EN_SPACE.value == 'EnSpace'
    assert caml.SPACES < set(caml.Glyph)
    assert caml.LEADERS < set(caml.Glyph)
    assert not (caml.SPACES & caml.LEADERS)
    # Every glyph is a space, a rule, or one of the two that wrap words.
    rest = set(caml.Glyph) - caml.SPACES - caml.LEADERS
    assert rest == {caml.Glyph.SMALL_CAPS, caml.Glyph.SPECIAL_FORMATTING}


def test_a_tag_the_survey_did_not_meet_is_named_and_not_dropped():
    """A later edition may add an element. Its words still belong to the law."""
    doc = _caml('<p>before <clarification>and this</clarification> after</p>')
    assert doc.unknown == ['clarification']
    assert caml.words(doc) == 'before and this after'
    spanned = _caml('<p><span class="Fancy"/>words</p>')
    assert spanned.unknown == ['span.Fancy']


def test_the_glyph_tally_counts_what_the_document_sets():
    doc = _caml('<p>(a)<span class="EnSpace"/>one<span class="EnSpace"/>'
                '<span class="DottedLeaders"/></p>')
    assert caml.glyphs(doc) == {
        caml.Glyph.EN_SPACE: 2,
        caml.Glyph.DOTTED_LEADERS: 1,
    }


def test_a_stored_section_reads_the_same_words_it_was_indexed_with():
    """The model is not a rewrite of the law, only of the markup.

    A section with no span and no fraction reads identically either way, so
    the reading can be trusted where it does differ.
    """
    doc = query.section('CIV', '1860')
    assert doc.get('found')
    plain = (doc.get('text') or '').strip()
    assert plain
    built = _words('<p>%s</p>' % plain.replace('&', '&amp;').replace('<', '&lt;'))
    assert built == plain
