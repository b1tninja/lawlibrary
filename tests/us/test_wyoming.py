"""Wyoming distribution — no network, no PDF parsing."""

from us.wyoming import Wyoming

SOURCE = 'https://wyoleg.gov/statutes/compress/'


def test_source():
    assert Wyoming.source == SOURCE


def test_editions_empty():
    assert Wyoming.editions == ()


def test_list_editions_no_network():
    editions = Wyoming().list_editions()
    assert editions[0] == SOURCE + 'title01.pdf'
    assert len(editions) == 2
    assert all(url.startswith(SOURCE) and url.endswith('.pdf') for url in editions)
