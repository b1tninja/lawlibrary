"""Needles are stored when a section is indexed, and only for its code."""

from indexer import Indexer, _annotation_rows, _term_rows


VESTING = (
    'The Natural Resources Agency shall succeed to, and is vested with, '
    'all the duties previously vested in the Resources Agency.'
)


def _index(tmp_path):
    idxer = Indexer(tmp_path / 'idx')
    laws = [
        {
            'PK': 'civ',
            'LAW_CODE': 'CIV',
            'SECTION_NUM': '1',
            'CODE_HEADING': 'Civil Code - CIV',
            'LEGAL_TEXT': 'This section shall apply. ' + VESTING,
            'ACTIVE_FLG': True,
            'SESSION': '2025',
            'SUBDIVISION': 'US-CA',
        },
        {
            'PK': 'puc',
            'LAW_CODE': 'PUC',
            'SECTION_NUM': '10',
            'CODE_HEADING': 'Public Utilities Code - PUC',
            'LEGAL_TEXT': 'Section means a section of this code.',
            'ACTIVE_FLG': True,
            'SESSION': '2025',
            'SUBDIVISION': 'US-CA',
        },
        {
            'PK': 'joint',
            'LAW_CODE': 'SCR',
            'SECTION_NUM': '1',
            'LEGAL_TEXT': 'Whenever the word bill is used in these rules, it includes a resolution.',
            'ACTIVE_FLG': True,
            'SESSION': '2025',
            'SUBDIVISION': 'US-CA',
            'SHELF': 'joint-rules',
        },
    ]
    idxer.index_pubinfo_laws(str(tmp_path / 'pub.zip'), laws)
    return idxer


def test_common_and_rare_targets_share_a_folded_spelling(tmp_path):
    idxer = Indexer(tmp_path / 'idx')
    db = idxer._needle_db()
    rows = (
        ('CIV 1', 'CIV', 'short_form', 'et seq.', 'et seq.', 0, 7),
        ('GOV 1', 'GOV', 'short_form', 'ET SEQ.', 'ET SEQ.', 0, 7),
        ('HSC 1', 'HSC', 'short_form', 'supra', 'supra', 0, 5),
    )
    db.executemany(
        'INSERT INTO annotation (citation, code, note, text, target, start, end) VALUES (?, ?, ?, ?, ?, ?, ?)',
        rows,
    )
    db.commit()
    db.close()
    found = idxer.targets('short_form')
    assert found.top(1)[0]['target'] == 'et seq.'
    assert found.top(1)[0]['count'] == 2
    assert found.bottom(1)[0]['target'] == 'supra'


def test_case_annotations_are_selected_by_target(tmp_path):
    idxer = Indexer(tmp_path / 'idx')
    db = idxer._needle_db()
    names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    db.execute(
        'INSERT INTO annotation (citation, code, note, text, target, start, end) VALUES (?, ?, ?, ?, ?, ?, ?)',
        ('CIV 1', 'CIV', 'case', 'CALIFORNIA', 'uppercase', 0, 10),
    )
    db.execute(
        'INSERT INTO annotation (citation, code, note, text, target, start, end) VALUES (?, ?, ?, ?, ?, ?, ?)',
        ('CIV 1', 'CIV', 'case', 'Department of Real Estate', 'Title', 11, 20),
    )
    db.commit()
    db.close()
    assert 'annotation_note_target' in names
    assert 'annotation_citation' in names
    upper = idxer.annotations(note='case', target='uppercase')
    assert upper and upper[0]['text'] == 'CALIFORNIA'
    titled = idxer.annotations(note='case', target='title')
    assert titled and titled[0]['text'] == 'Department of Real Estate'


def test_terms_and_annotations_are_parsed_apart():
    """The term job does not emit annotations. The annotation job does not emit forms."""
    doc = {
        'CITATION': 'CIV 1',
        'LAW_CODE': 'CIV',
        'LEGAL_TEXT': 'This section shall apply. The fee is $100, payable 30 days from the hearing.',
    }
    needles, _edges = _term_rows(doc)
    notes = _annotation_rows(doc)
    assert any(row[2] == 'Section' for row in needles)
    assert all(row[2] != 'amount' for row in needles)
    assert any(row[2] == 'amount' and row[4] == '100' for row in notes)
    assert any(row[2] == 'antecedent' for row in notes)


def test_workers_parse_while_one_connection_writes(tmp_path):
    """Processes parse sections. The SQLite connection stays on the caller."""
    idxer = _index(tmp_path)
    assert idxer.index_stored_needles(workers=2) == 3
    assert 'Section' in {row['class'] for row in idxer.needles(code='CIV')}
    assert 'PublicUtilitiesSection' in {row['class'] for row in idxer.needles(code='PUC')}


def test_a_code_keeps_only_its_own_needles(tmp_path):
    idxer = _index(tmp_path)
    civil = {row['class'] for row in idxer.needles(code='CIV')}
    utilities = {row['class'] for row in idxer.needles(code='PUC')}
    assert 'Section' in civil
    assert 'PublicUtilitiesSection' not in civil
    assert 'Vesting' in civil
    assert 'PublicUtilitiesSection' in utilities
    assert 'Section' not in utilities
    joint = {row['class'] for row in idxer.needles(code='SCR')}
    assert 'JointBill' in joint
    assert 'Bill' not in joint


def test_amounts_and_antecedents_are_stored_at_ingestion(tmp_path):
    idxer = Indexer(tmp_path / 'idx')
    idxer.index_pubinfo_laws(str(tmp_path / 'pub.zip'), [{
        'PK': 'gov',
        'LAW_CODE': 'GOV',
        'SECTION_NUM': '1',
        'LEGAL_TEXT': 'The fee is $100, payable 30 days from the hearing.',
        'ACTIVE_FLG': True,
        'SESSION': '2025',
        'SUBDIVISION': 'US-CA',
    }])
    amounts = idxer.annotations(note='amount', code='GOV')
    assert amounts and amounts[0]['target'] == '100'
    anchors = idxer.annotations(note='antecedent', code='GOV')
    assert anchors and anchors[0]['target'] == 'the hearing'


def test_vesting_edges_are_stored_for_the_diagram(tmp_path):
    idxer = _index(tmp_path)
    chart = idxer.vesting_diagram(code='CIV')
    assert 'Resources Agency' in chart
    assert 'Natural Resources Agency' in chart
    assert '-->|vested|' in chart
    assert idxer.vesting_diagram(code='PUC') == 'flowchart TD'
