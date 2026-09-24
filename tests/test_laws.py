import zipfile
from pathlib import Path

from ca import California, iter_laws
from indexer import Indexer


def _row(cols):
    return '\t'.join('NULL' if col is None else '`%s`' % col for col in cols)


def _pubinfo(path: Path):
    toc = [
        _row(['CIV', '1.', None, None, None, None, 'Division 1. Persons', 'Y', 'u',
              '2020-01-01 00:00:00', '1', '1', '1', '1', 'N', None, None, None, None]),
        _row(['CIV', '1.', None, None, '2.', None, 'Chapter 2. Hiring', 'Y', 'u',
              '2020-01-01 00:00:00', '2', '2', '1', '1.2', 'N', None, None, None, None]),
        _row(['CIV', '1.', None, None, '2.', '3.', 'Article 3. Hiring of Real Property', 'Y', 'u',
              '2020-01-01 00:00:00', '3', '3', '1', '1.2.3', 'Y', 'Added 1872.', None, None, None]),
    ]
    sections = [
        _row(['1', 'CIV', '1.2.3', '1940', '1', 'Landlord duty', None, None, None, 'u',
              '2020-01-01 00:00:00', 'ver1', '1']),
    ]
    law = [
        _row(['pk1', 'CIV', '1940.', '1872', '1', '1', None, 'ver1', '1.', None, None, '2.', '3.',
              'Enacted 1872.', 'LAW_SECTION_TBL_pk1.lob', 'Y', 'u', '2020-01-01 00:00:00']),
    ]
    codes = [_row(['CIV', 'Civil Code'])]
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('CODES_TBL.dat', '\n'.join(codes) + '\n')
        zf.writestr('LAW_TOC_TBL.dat', '\n'.join(toc) + '\n')
        zf.writestr('LAW_TOC_SECTIONS_TBL.dat', '\n'.join(sections) + '\n')
        zf.writestr('LAW_SECTION_TBL.dat', '\n'.join(law) + '\n')
        zf.writestr('LAW_SECTION_TBL_pk1.lob', '<p>The landlord shall keep the dwelling habitable.</p>')


def _bills(path: Path):
    row = _row(['19891SCR198CHP', '198919901SCR1', '98', '1989-11-03 00:00:00', 'Chaptered', None,
                'Joint Rules.', None, None, None, None, None, None, None,
                'BILL_VERSION_TBL_1.lob', 'Y', 'LEG_ESI', '2007-08-22 11:53:13'])
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('BILL_TBL.dat', _row(['198919901SCR1', 'bill']) + '\n')
        zf.writestr('BILL_VERSION_TBL.dat', row + '\n')
        zf.writestr('BILL_VERSION_TBL_1.lob', '<p>The joint rules of the session.</p>')


def test_edition_follows_the_tables(tmp_path):
    codes = tmp_path / 'pubinfo_2025.zip'
    bills = tmp_path / 'pubinfo_1989.zip'
    _pubinfo(codes)
    _bills(bills)
    california = California()
    assert type(california.edition(codes)).__name__ == 'CaliforniaCodes'
    assert type(california.edition(bills)).__name__ == 'CaliforniaBills'
    text = next(california.sections(bills))
    assert text['SECTION_NUM'] == '198919901SCR1'
    assert 'joint rules' in text['LEGAL_TEXT'].lower()
    assert text['SESSION'] == '1989'


def test_iter_laws_joins_headings(tmp_path):
    pub = tmp_path / 'pubinfo_2025.zip'
    _pubinfo(pub)
    laws = list(iter_laws(pub))
    assert len(laws) == 1
    law = laws[0]
    assert law['LAW_CODE'] == 'CIV'
    assert law['SECTION_NUM'] == '1940'
    assert law['CODE_HEADING'] == 'Civil Code'
    assert law['DIVISION_HEADING'] == 'Division 1. Persons'
    assert law['CHAPTER_HEADING'] == 'Chapter 2. Hiring'
    assert law['ARTICLE_HEADING'] == 'Article 3. Hiring of Real Property'
    assert 'habitable' in law['LEGAL_TEXT']
    assert law['SECTION_TITLE'] == 'Landlord duty'


def test_parallel_matches_serial(tmp_path):
    pub = tmp_path / 'pubinfo_2025.zip'
    _pubinfo(pub)
    serial = list(iter_laws(pub))
    from ca import iter_laws_parallel
    parallel = list(iter_laws_parallel(pub, workers=2, chunk_size=1))
    fields = ('SECTION_NUM', 'LEGAL_TEXT', 'SESSION', 'ARTICLE_HEADING', 'CODE_HEADING')
    assert [{key: law[key] for key in fields} for law in serial] == [{key: law[key] for key in fields} for law in parallel]
    assert parallel[0]['PK'] == '2025:pk1'


def test_index_search_and_citation(tmp_path):
    pub = tmp_path / 'pubinfo_2025.zip'
    _pubinfo(pub)
    indexer = Indexer(tmp_path / 'idx')
    assert indexer.index_pubinfo_laws(pub, iter_laws(pub)) == 1

    hits = indexer.search_law('habitable dwelling')
    assert hits[0]['citation'] == 'CIV 1940'
    assert 'habitable' in hits[0]['snippet'].lower() or 'HABITABLE' in hits[0]['snippet']

    cited = indexer.search_law('Civil Code section 1940')
    assert cited[0]['section'] == '1940'

    full = indexer.get_section('Civil Code', '1940')
    assert 'landlord' in full[0]['text'].lower()
    assert indexer.list_codes() == [{'code': 'CIV', 'title': 'Civil Code'}]
