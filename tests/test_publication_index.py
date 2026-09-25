"""Publication.index writes sections() into a temp Whoosh index."""

from whoosh import index

from indexer import Indexer
from publication import Publication


class _Tiny(Publication):
    """Minimal edition that yields two indexable law rows."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        yield {
            'PK': 'demo:1',
            'LAW_CODE': 'CIV',
            'SECTION_NUM': '100',
            'CODE_HEADING': 'Civil Code - CIV',
            'LEGAL_TEXT': 'First fixture section for indexing.',
            'ACTIVE_FLG': True,
            'SESSION': '2025',
        }
        yield {
            'PK': 'demo:2',
            'LAW_CODE': 'CIV',
            'SECTION_NUM': '200',
            'CODE_HEADING': 'Civil Code - CIV',
            'LEGAL_TEXT': 'Second fixture section for indexing.',
            'ACTIVE_FLG': True,
            'SESSION': '2025',
        }


class _State(Publication):
    """State edition row: section text and ISO subdivision, no PK."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        yield {
            'SECTION_NUM': '28-101',
            'LEGAL_TEXT': 'Nebraska fixture statute for state indexing.',
            'SUBDIVISION': 'US-NE',
            'ACTIVE_FLG': True,
            'SESSION': '2025',
        }


def test_publication_index_writes_sections(tmp_path):
    idxer = Indexer(tmp_path / 'idx')
    path = tmp_path / 'edition.txt'
    path.write_text('unused', encoding='utf-8')
    count = _Tiny().index(idxer, str(path), subdivision='US-CA')
    assert count == 2
    hits = idxer.search_law('fixture section', session='2025')
    assert {hit['section'] for hit in hits} == {'100', '200'}


def test_publication_index_fills_missing_pk(tmp_path):
    idx_path = tmp_path / 'idx'
    idxer = Indexer(idx_path)
    path = tmp_path / 'edition.txt'
    path.write_text('unused', encoding='utf-8')
    count = _State().index(idxer, str(path))
    assert count == 1
    pk = 'US-NE CODE 28-101'
    with index.open_dir(str(idx_path)).searcher() as searcher:
        hit = searcher.document(PK=pk)
    assert hit is not None
    assert hit['LAW_CODE'] == 'CODE'
    assert hit['COUNTRY'] == 'US'
    assert 'Nebraska fixture' in hit['LEGAL_TEXT']


def test_a_book_heading_is_written_to_the_code_catalog(tmp_path):
    class _Book(Publication):
        code_heading = 'Nebraska Revised Statutes'
        session = '2024'

        @classmethod
        def accepts(cls, names):
            return True

        def sections(self, path):
            yield {
                'SECTION_NUM': '28-101',
                'LEGAL_TEXT': 'Catalog fixture.',
                'SUBDIVISION': 'US-NE',
                'LAW_CODE': 'NRS',
                'ACTIVE_FLG': True,
            }

    idx_path = tmp_path / 'idx'
    idxer = Indexer(idx_path)
    path = tmp_path / 'edition.txt'
    path.write_text('unused', encoding='utf-8')
    assert _Book().index(idxer, str(path)) == 1
    assert idxer._read_codes()['NRS'] == 'Nebraska Revised Statutes'
    with index.open_dir(str(idx_path)).searcher() as searcher:
        hit = searcher.document(PK='US-NE NRS 28-101')
    assert hit['SESSION'] == '2024'
    assert hit['CODE_HEADING'] == 'Nebraska Revised Statutes'


def test_publication_index_empty_skips_index(tmp_path):
    class Empty(Publication):
        @classmethod
        def accepts(cls, names):
            return True

        def sections(self, path):
            return iter(())

    idx_path = tmp_path / 'idx'
    idxer = Indexer(idx_path)
    assert Empty().index(idxer, str(tmp_path / 'empty')) == 0
    assert not index.exists_in(str(idx_path))
