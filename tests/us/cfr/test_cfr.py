"""CFR eCFR XML indexer — synthetic fixture only, no network, no bulk XML in git."""

from pathlib import Path

from publication import Instrument, State
from corpus import connect, cfr_corpus_path
from us.cfr import CFR, CodeOfFederalRegulations, title_url

FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<DLPSTEXTCLASS>
<HEADER>
<FILEDESC>
<PUBLICATIONSTMT>
<IDNO TYPE="title">44</IDNO>
</PUBLICATIONSTMT>
</FILEDESC>
</HEADER>
<TEXT>
<BODY>
<ECFRBRWS>
<DIV1 N="1" NODE="44:1" TYPE="TITLE">
<HEAD>Title 44—Emergency Management and Assistance</HEAD>
<DIV5 N="1" NODE="44:1.0.1.1.2" TYPE="PART">
<HEAD>PART 1—RULEMAKING, POLICY, AND PROCEDURES</HEAD>
<DIV8 N="§ 1.1" NODE="44:1.0.1.1.2.0.1.1" TYPE="SECTION">
<HEAD>§ 1.1   Purpose and scope.</HEAD>
<P>(a) This part contains FEMA's procedures for informal rulemaking.</P>
<P>(b) This part does not apply to formal rulemaking.</P>
</DIV8>
<DIV8 N="§ 1.2" NODE="44:1.0.1.1.2.0.1.2" TYPE="SECTION">
<HEAD>§ 1.2   Definitions.</HEAD>
<P>(a) <I>Rule</I> or <I>regulation</I> have the same meaning as in the APA.</P>
</DIV8>
</DIV5>
</DIV1>
</ECFRBRWS>
</BODY>
</TEXT>
</DLPSTEXTCLASS>
"""


ANNUAL = """<?xml version="1.0" encoding="UTF-8"?>
<CFRDOC>
<TITLENUM>1</TITLENUM>
<TITLE>
<CFRTITLE>Title 1—Sample Provisions</CFRTITLE>
<CHAPTER>
<PART>
<EAR>Pt. 1</EAR>
<HD>PART 1—SAMPLE</HD>
<SECTION>
<SECTNO>§ 1.1</SECTNO>
<SUBJECT>Purpose.</SUBJECT>
<P>Synthetic annual section text.</P>
</SECTION>
</PART>
</CHAPTER>
</TITLE>
</CFRDOC>
"""


def _write_fixture(tmp_path: Path):
    path = tmp_path / 'ECFR-title44.xml'
    path.write_text(FIXTURE, encoding='utf-8')
    return path


def test_not_a_state():
    assert not issubclass(CodeOfFederalRegulations, State)
    assert not issubclass(CFR, State)


def test_instrument_is_regulation():
    assert CFR.instrument is Instrument.REGULATION


def test_editions_is_cfr_class():
    assert CodeOfFederalRegulations.editions == (CFR,)


def test_source():
    assert CodeOfFederalRegulations.source == 'https://www.govinfo.gov/bulkdata/ECFR'


def test_list_editions_pattern_no_network():
    editions = CodeOfFederalRegulations().list_editions()
    assert len(editions) == 50
    assert editions[0] == title_url(1)
    assert editions[43] == 'https://www.govinfo.gov/bulkdata/ECFR/title-44/ECFR-title44.xml'
    assert editions[-1] == title_url(50)


def test_accepts_local_xml():
    assert CFR.accepts('ECFR-title44.xml')
    assert CFR.accepts('/tmp/ECFR-title12.xml')
    assert not CFR.accepts({'LAW_SECTION_TBL'})
    assert not CFR.accepts('pubinfo_2025.zip')


def test_annual_xml_keeps_part_and_section(tmp_path):
    path = tmp_path / 'CFR-2025-title1-vol1.xml'
    path.write_text(ANNUAL, encoding='utf-8')
    rows = list(CFR().sections(path))
    assert len(rows) == 1
    assert rows[0]['LAW_CODE'] == '1CFR'
    assert rows[0]['SECTION_NUM'] == '1.1'
    assert rows[0]['PART'] == '1'
    assert rows[0]['SECTION_TITLE'] == 'Purpose.'
    assert rows[0]['CODE_HEADING'] == 'Title 1—Sample Provisions'
    assert 'Synthetic annual section text' in rows[0]['LEGAL_TEXT']


def test_sections_from_synthetic_fixture(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(CFR().sections(path))
    assert len(rows) == 2
    assert all(r['COUNTRY'] == 'US' for r in rows)
    assert all(r['SUBDIVISION'] == 'US' for r in rows)
    assert all(r['LAW_CODE'] == '44CFR' for r in rows)
    assert 'Title 44' in rows[0]['CODE_HEADING']
    assert rows[0]['SECTION_NUM'] == '1.1'
    assert rows[0]['TITLE'] == '1'
    assert rows[0]['PART'] == '1'
    assert 'informal rulemaking' in rows[0]['LEGAL_TEXT']
    assert 'Purpose and scope' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '1.2'
    assert 'regulation' in rows[1]['LEGAL_TEXT']

    assert CFR().load(path, root=tmp_path) == 2
    assert CFR().load(path, root=tmp_path) == 2  # reload replaces, no dupes
    db = connect(cfr_corpus_path(44, root=tmp_path))
    try:
        stored = db.execute(
            'SELECT pk, law_code, section_num, legal_text, citation, session '
            'FROM section ORDER BY section_num'
        ).fetchall()
        assert len(stored) == 2
        assert stored[0][0] == '44CFR:1.1'
        assert stored[0][1] == '44CFR'
        assert stored[0][2] == '1.1'
        assert 'informal rulemaking' in stored[0][3]
        assert stored[0][4] == '44CFR 1.1'
        assert stored[1][0] == '44CFR:1.2'
        assert stored[1][4] == '44CFR 1.2'
    finally:
        db.close()


def test_cfr_corpus_path_per_title(tmp_path):
    path = cfr_corpus_path(44, root=tmp_path)
    assert path.endswith('US/cfr/44.sqlite') or path.endswith('US\\cfr\\44.sqlite')
    ca = tmp_path / 'US-CA.sqlite'
    assert Path(path) != ca
