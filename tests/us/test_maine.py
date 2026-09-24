"""Maine distribution — source and title PDF list only, no network."""

from us.maine import Maine


def test_source():
    assert Maine.source == 'https://legislature.maine.gov/legis/statutes/homepage.html'


def test_list_editions_no_network():
    editions = Maine().list_editions()
    assert editions == [
        'https://www.mainelegislature.org/legis/statutes/1/title1.pdf',
        'https://www.mainelegislature.org/legis/statutes/2/title2.pdf',
        'https://www.mainelegislature.org/legis/statutes/3/title3.pdf',
    ]


def test_editions_empty():
    assert Maine.editions == ()
