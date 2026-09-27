"""The ledger: each word's count at each place, summed into a scope.

The index is the synthetic tree from the ingest tests, so a place is a node
of the publisher's tree. Nothing here opens the live index.
"""

import os
import pathlib

from ledger import Ledger, build, keep, ledger_path, open_ledger


def _tree_index(tmp_path, year='2025'):
    from test_tree_ingest import _pubinfo
    from indexer import Indexer
    from us.states.ca import California
    pub = tmp_path / ('pubinfo_%s.zip' % year)
    _pubinfo(pub)
    california = California()
    california.edition(pub).index(Indexer(tmp_path / 'idx'), pub, subdivision=california.code)
    return str(tmp_path / 'idx')


def test_a_term_is_a_word():
    """Short tokens and anything led by a digit — a cited section number — are not counted."""
    assert keep(b'landlord') == 'landlord'
    assert keep('mean') == 'mean'
    assert keep(b'of') is None
    assert keep(b'1798.110') is None
    assert keep(b'2924g') is None
    assert keep('10th') is None


def test_a_section_sits_at_one_place_and_a_node_covers_its_subtree(tmp_path):
    root = _tree_index(tmp_path)
    book = open_ledger(root)
    assert isinstance(book, Ledger)
    assert book.session == '2025'
    # Three sections, each at its own node: 1.2.3, 2.1.1, and the unnumbered 3.
    assert int(book.meta['sections']) == 3 and int(book.meta['places']) == 3
    assert book.n('node') == 3 and book.n('code') == 1
    title = book.places('node', 'CIV 2.1.1')
    assert len(title) == 1
    assert book.places('node', 'CIV 2.1') == title
    assert book.places('node', 'CIV 2') == title
    assert book.places('node', 'CIV 2.1.10') == []
    assert sorted(book.places('code', 'CIV')) == sorted(
        book.places('node', 'CIV 1') + title + book.places('node', 'CIV 3')
    )
    assert book.places('node', 'CIV') == [] and book.places('node', '') == []
    assert book.places('state', 'US-CA') and book.places('federal', 'US') == []


def test_a_count_is_a_sum_over_places_and_a_frequency_is_exact(tmp_path):
    root = _tree_index(tmp_path)
    book = open_ledger(root)
    one = book.tally(book.places('node', 'CIV 2.1.1'))
    assert one.get('mean') == 1 and 'habit' not in one
    whole = book.tally(book.places('code', 'CIV'))
    assert whole['mean'] == 1 and whole['habit'] == 1
    # The landlord is in two of the three sections: two places, one code.
    assert whole['landlord'] == 2
    assert book.df('node', ['landlord', 'mean']) == {'landlord': 2, 'mean': 1}
    assert book.df('code', ['landlord']) == {'landlord': 1}
    assert book.tally(book.places('node', 'CIV 1'))['landlord'] == 1
    assert book.tally([]) == {} and book.df('node', []) == {}


def test_the_ledger_follows_the_index_generation(tmp_path):
    """A grown index gets a new ledger, and the earlier file is swept away."""
    root = _tree_index(tmp_path, '2011')
    first = open_ledger(root)
    early = first.path
    assert os.path.exists(early) and first.session == '2011'
    _tree_index(tmp_path, '2025')
    second = open_ledger(root)
    assert second.generation != first.generation
    assert second.session == '2025'
    assert os.path.exists(second.path) and not os.path.exists(early)
    # The newest edition only: the section published twice is counted once.
    assert second.tally(second.places('code', 'CIV'))['mean'] == 1
    assert open_ledger(root) is second


def test_a_build_names_its_own_file_and_says_what_it_did(tmp_path):
    root = _tree_index(tmp_path)
    said = []
    path = build(root, workers=1, log=said.append)
    assert path == ledger_path(root, 1) or path.endswith('.sqlite')
    assert any('places' in words for words in said)
    assert open_ledger(str(tmp_path / 'nowhere')) is None


def test_the_ledger_defaults_to_where_readers_look(tmp_path, monkeypatch):
    """A shelf that readers have turned to is what the ledger counts, not the flat index."""
    import core
    root = _tree_index(tmp_path)
    monkeypatch.setattr(core, 'index_root', lambda: pathlib.Path(root))
    book = open_ledger()
    assert book.root == root and book.session == '2025'


def test_two_builds_of_one_generation_keep_the_first(tmp_path, monkeypatch):
    """A reader holding the finished file stops the replace on Windows; the finished file stands."""
    import ledger
    root = _tree_index(tmp_path)
    first = build(root, workers=1)
    real = os.replace

    def held(src, dst):
        raise PermissionError(5, 'Access is denied', src)

    monkeypatch.setattr(ledger.os, 'replace', held)
    again = build(root, workers=1)
    monkeypatch.setattr(ledger.os, 'replace', real)
    assert again == first and os.path.exists(first)
    assert not [name for name in os.listdir(root) if name.endswith('.tmp')]
