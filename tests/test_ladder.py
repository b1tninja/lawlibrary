"""The ladder above a section, read the way the publisher wrote it.

California's codes do not share one nesting. The Civil Code runs division,
part, title, chapter; the Penal Code runs part, title, division; the
Government Code starts at title. The stored fields were filled by one fixed
order that no code follows, so a caption can sit on the wrong field. In the
Legislature's own table of contents a caption's first word disagrees with the
rung it names zero times in 24,386 rows, so the word is what these read.

The documents here are built to shape. No statute is quoted.
"""

from query import _captions, _unnamed, _units_from_doc, heading_key, section_key


# What the index stores for a section of Civil Code Title 5: the title's
# caption was filed on the part field, and the part has no caption of its own.
CIV_SHAPE = {
    'DIVISION': '3', 'DIVISION_HEADING': 'DIVISION 3. OBLIGATIONS [1427. - 3273.91.]',
    'TITLE': '5', 'TITLE_HEADING': '',
    'PART': '4', 'PART_HEADING': 'TITLE 5. HIRING [1925. - 1997.270.]',
    'CHAPTER': '2', 'CHAPTER_HEADING': 'CHAPTER 2. Hiring of Real Property [1940. - 1954.071.]',
}


def test_a_caption_is_filed_under_the_unit_its_own_words_name():
    filed = _captions(CIV_SHAPE)
    assert filed[('title', '5')].startswith('TITLE 5.')
    assert filed[('division', '3')].startswith('DIVISION 3.')
    assert filed[('chapter', '2')].startswith('CHAPTER 2.')
    assert ('part', '4') not in filed, 'nothing names part 4, so it has no caption'


def test_each_rung_takes_the_caption_that_names_it():
    rungs = {rung['level']: rung for rung in _units_from_doc(CIV_SHAPE)}
    assert rungs['title']['heading'].startswith('TITLE 5.')
    # The misfiled caption does not leak onto the rung it was stored against.
    assert rungs['part']['heading'] == ''
    assert rungs['part']['value'] == '4'
    assert [rung['level'] for rung in _units_from_doc(CIV_SHAPE)] == ['division', 'title', 'part', 'chapter']


def test_a_lettered_rung_names_itself():
    doc = {'TITLE': '1A', 'PART_HEADING': 'TITLE 1A. INDEPENDENT WHOLESALE SALES REPRESENTATIVES'}
    assert _captions(doc)[('title', '1A')].startswith('TITLE 1A.')


def test_a_caption_naming_another_rung_is_never_a_fallback():
    """A stored caption that names no unit may stand; one that names a rung belongs to it."""
    assert _unnamed('TITLE 5. HIRING') == ''
    assert _unnamed('PRELIMINARY PROVISIONS') == 'PRELIMINARY PROVISIONS'
    assert _unnamed('') == ''
    assert _unnamed(None) == ''


def test_a_heading_number_is_a_decimal_and_a_section_number_is_not():
    """The publisher lists Part 2.52 between 2.5 and 2.6; section 1738.10 follows 1738.9."""
    parts = ['1', '2', '2.5', '2.52', '2.53', '2.55', '2.57', '2.6', '2.7', '2.9']
    assert sorted(reversed(parts), key=heading_key) == parts
    titles = ['1', '1A', '1.1', '1.1A', '1.2', '1.2A', '2']
    assert sorted(reversed(titles), key=heading_key) == titles
    sections = ['1738.2', '1738.9', '1738.10']
    assert sorted(reversed(sections), key=section_key) == sections
