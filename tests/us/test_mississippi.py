"""Mississippi distribution — no network, no local corpus."""

from us.mississippi import Mississippi


def test_source():
    assert Mississippi.source == 'https://www.legislature.ms.gov/'


def test_no_editions():
    assert Mississippi.editions == ()


def test_list_editions_empty():
    assert Mississippi().list_editions() == []
