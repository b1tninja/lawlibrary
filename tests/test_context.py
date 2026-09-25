from citations import Note, annotate, document, resolve_book


BOOKS = {
    'CIV': 'Civil Code - CIV',
    'BPC': 'Business and Professions Code - BPC',
}


def test_a_book_has_one_abbreviation():
    assert resolve_book('CIV', BOOKS) == 'CIV'
    assert resolve_book('Civil Code', BOOKS) == 'CIV'
    assert resolve_book('Civ. Code', BOOKS) == 'CIV'
    assert resolve_book('California Civil Code', BOOKS) == 'CIV'
    assert resolve_book('Bus. & Prof. Code', BOOKS) == 'BPC'
    assert resolve_book('Business and Professions Code', BOOKS) == 'BPC'


def test_this_code_means_the_book_being_read():
    """Inside the Civil Code, this code is CIV. A bare section uses that book."""
    with document('Civil Code', section='1940', books=BOOKS) as ctx:
        assert ctx.code == 'CIV'
        notes = annotate('A hiring under this code is governed by section 1940.')
    code = next(note for note in notes if note.text.lower() == 'this code')
    section = next(note for note in notes if note.note is Note.CITATION)
    assert code.target == 'CIV'
    assert section.target == 'CIV 1940'


def test_the_following_stays_inside_the_open_section():
    with document('BPC', section='10080', books=BOOKS):
        notes = annotate('The commissioner may adopt the following.')
    follow = next(note for note in notes if note.text.lower() == 'the following')
    assert follow.note is Note.CROSS_REFERENCE
    assert follow.target == 'BPC the following'
