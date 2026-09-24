"""Washington distribution — no network, no PDF parsing."""

from states.washington import Washington

SOURCE = 'https://lawfilesext.leg.wa.gov/Law/RCWArchive/2025/pdf/'


def test_source():
    assert Washington.source == SOURCE


def test_editions_empty():
    assert Washington.editions == ()


def test_list_editions_no_network():
    editions = Washington().list_editions()
    assert len(editions) == 2
    assert all(url.startswith(SOURCE) and url.endswith('.pdf') for url in editions)
