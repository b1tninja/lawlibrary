import zipfile
from pathlib import Path

from us.states.ca import California, iter_laws
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


def _bills(path: Path, *, extras=()):
    """Minimal 1989-style bills zip. extras names companion .dat stems for later eras."""
    row = _row(['19891SCR198CHP', '198919901SCR1', '98', '1989-11-03 00:00:00', 'Chaptered', None,
                'Joint Rules.', None, None, None, None, None, None, None,
                'BILL_VERSION_TBL_1.lob', 'Y', 'LEG_ESI', '2007-08-22 11:53:13'])
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('BILL_TBL.dat', _row(['198919901SCR1', 'bill']) + '\n')
        zf.writestr('BILL_VERSION_TBL.dat', row + '\n')
        zf.writestr('BILL_VERSION_AUTHORS_TBL.dat', _row(['a']) + '\n')
        for stem in extras:
            zf.writestr('%s.dat' % stem, _row(['x']) + '\n')
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


def test_bill_era_shapes_still_dispatch(tmp_path):
    """Companion-table eras differ; BILL_VERSION_TBL columns do not. One bills edition."""
    california = California()
    eras = {
        1989: (),
        1993: ('BILL_ANALYSIS_TBL',),
        1999: ('BILL_ANALYSIS_TBL', 'BILL_HISTORY_TBL', 'LEGISLATOR_TBL'),
        2003: ('BILL_ANALYSIS_TBL', 'COMMITTEE_HEARING_TBL', 'LEGISLATOR_TBL'),
    }
    for year, extras in eras.items():
        path = tmp_path / ('pubinfo_%d.zip' % year)
        _bills(path, extras=extras)
        assert type(california.edition(path)).__name__ == 'CaliforniaBills'
        row = next(california.sections(path))
        assert row['SESSION'] == str(year)
        assert row['LAW_CODE'] == 'BILL'


def test_codes_and_bills_stamp_subdivision(tmp_path):
    codes = tmp_path / 'pubinfo_2025.zip'
    bills = tmp_path / 'pubinfo_1989.zip'
    _pubinfo(codes)
    _bills(bills)
    california = California()
    indexer = Indexer(tmp_path / 'idx')
    assert california.edition(codes).index(indexer, codes, subdivision=california.code) == 1
    assert california.edition(bills).index(indexer, bills, subdivision=california.code) == 1
    hits = indexer.search_law('habitable dwelling')
    assert hits[0]['subdivision'] == 'US-CA'
    bill_hits = indexer.search_law('joint rules', session='1989')
    assert bill_hits[0]['subdivision'] == 'US-CA'


def test_sacramento_is_home():
    from us import HOME, UnitedStates, load_states
    from us.states.ca import California
    from us.states.idaho import Idaho
    from us.counties.ca.sacramento import SacramentoCounty
    from us.counties.ca.sacramento.cities.sacramento import Sacramento
    assert HOME == 'US-CA'
    assert SacramentoCounty.region() == HOME
    assert Sacramento.parent is SacramentoCounty
    assert Sacramento.county() is SacramentoCounty
    assert SacramentoCounty.cities()['sacramento'] is Sacramento
    from publication import City
    try:
        class NotUnderACounty(City):
            name = 'Loose'
            parent = 'US-CA'
    except TypeError:
        pass
    else:
        raise AssertionError('a US city parents on a county')
    assert California.counties()['sacramento'] is SacramentoCounty
    assert UnitedStates.code == 'US'
    assert load_states()['US-CA'].__name__ == 'California'
    assert Idaho.counties() == {}


def test_california_is_iso_subdivision():
    from us.states.ca import California, CaliforniaBills, CaliforniaCodes
    from publication import Instrument, State, country, subdivision
    assert issubclass(California, State)
    assert California.legislates is True
    assert California.code == 'US-CA'
    assert subdivision(California.code).country_code == 'US'
    assert California.country() is country('US')
    assert California.country().alpha_3 == 'USA'
    assert CaliforniaCodes.instrument is Instrument.STATUTE
    assert CaliforniaBills.instrument is Instrument.MEASURE


def test_layers_follow_iso():
    from publication import Country, Locality, Region, State

    class UnitedStates(Country):
        code = 'US'
        def list_editions(self):
            return []

    class Tokyo(Region):
        code = 'JP-13'
        legislates = False
        def list_editions(self):
            return []

    class Sacramento(Locality):
        name = 'Sacramento'
        parent = 'US-CA'

    assert UnitedStates.record().alpha_2 == 'US'
    assert Tokyo.legislates is False
    assert Tokyo.record().type == 'Prefecture'
    assert Sacramento.region() == 'US-CA'
    from publication import _countries
    from us import UnitedStates as home
    _countries['US'] = home
    for bad in ('US-DC', 'JP-13'):
        try:
            class NotAState(State):
                code = bad
                def list_editions(self):
                    return []
        except TypeError:
            pass
        else:
            raise AssertionError(bad)


def test_state_code_must_be_iso():
    from publication import State
    try:
        class NotASubdivision(State):
            code = 'not-a-code'
            def list_editions(self):
                return []
    except ValueError:
        pass
    else:
        raise AssertionError('expected ValueError')


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
    from us.states.ca import iter_laws_parallel
    parallel = list(iter_laws_parallel(pub, workers=2, chunk_size=1))
    fields = ('SECTION_NUM', 'LEGAL_TEXT', 'SESSION', 'ARTICLE_HEADING', 'CODE_HEADING')
    assert [{key: law[key] for key in fields} for law in serial] == [{key: law[key] for key in fields} for law in parallel]
    assert parallel[0]['PK'] == '2025:pk1'


def test_index_search_and_citation(tmp_path):
    pub = tmp_path / 'pubinfo_2025.zip'
    _pubinfo(pub)
    california = California()
    indexer = Indexer(tmp_path / 'idx')
    assert california.edition(pub).index(indexer, pub, subdivision=california.code) == 1

    hits = indexer.search_law('habitable dwelling')
    assert hits[0]['citation'] == 'CIV 1940'
    assert hits[0]['subdivision'] == 'US-CA'
    assert 'habitable' in hits[0]['snippet'].lower() or 'HABITABLE' in hits[0]['snippet']

    cited = indexer.search_law('Civil Code section 1940')
    assert cited[0]['section'] == '1940'

    full = indexer.get_section('Civil Code', '1940')
    assert 'landlord' in full[0]['text'].lower()
    assert indexer.list_codes() == [{'code': 'CIV', 'title': 'Civil Code'}]
