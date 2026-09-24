"""Tennessee distribution — no network, no local corpus."""

from us.tennessee import Tennessee


def test_source():
    assert Tennessee.source == (
        'https://www.capitol.tn.gov/legislation/publications/index.html'
    )


def test_no_editions():
    assert Tennessee.editions == ()


def test_list_editions_empty():
    assert Tennessee().list_editions() == []
