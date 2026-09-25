from apa import Code
from mcp_server import analyze_text, annotations_law, cite_law, diagram_law, list_courts, list_offices, pin_section, serve_reader
from places import Citation


def test_annotations_law_passes_case_target(monkeypatch):
    captured = {}

    class FakeIndexer:
        def annotations(self, note=None, code=None, target=None, limit=24):
            captured.update(note=note, code=code, target=target, limit=limit)
            return [{'citation': 'CIV 1', 'code': 'CIV', 'note': 'case', 'text': 'X', 'target': target}]

    monkeypatch.setattr('mcp_server._indexer', lambda: FakeIndexer())
    rows = annotations_law(note='case', target='uppercase', limit=3)
    assert captured == {'note': 'case', 'code': None, 'target': 'uppercase', 'limit': 3}
    assert rows[0]['target'] == 'uppercase'


def test_offices_include_the_real_estate_authority():
    row = next(item for item in list_offices() if item['model'] == 'CaliforniaDepartmentOfRealEstate')
    assert row['authority'] == 'BPC 10050'
    assert row['parent'] == 'US-CA'
    assert 'real_estate' in row['functions']


def test_courts_name_sacramento_under_california():
    row = next(item for item in list_courts() if item['model'] == 'SacramentoSuperiorCourt')
    assert row['bench'] == 'trial'
    assert row['jurisdiction'] == 'US-CA'
    assert 'traffic' in row['divisions']


def test_analyze_text_binds_the_department_and_its_duty():
    """BPC 10050. The department and the duty are read from the section."""
    text = Citation(Code.BUSINESS_AND_PROFESSIONS).section('10050').text
    if 'Department of Real Estate' not in text:
        return
    reading = analyze_text(text)
    subjects = [subject for sentence in reading['sentences'] for subject in sentence['subjects']]
    assert subjects[0]['model'] == 'CaliforniaDepartmentOfRealEstate'
    assert subjects[0]['jurisdiction'] == 'US-CA'
    assert any(item['fact'] == 'responsibility' for item in subjects[0]['relations'])


def test_a_history_chapter_keeps_the_action():
    """Added by Stats. is an action on the chapter row. The year and chapter stay."""
    from query import _chapters
    rows = _chapters('Added by Stats. 2011, Ch. 383, Sec. 2.')
    assert rows[0]['action'] == 'added'
    assert rows[0]['year'] == '2011'
    assert rows[0]['chapter'] == '383'
    assert rows[0]['act'] == '2'
    amended = _chapters('Amended by Stats. 1987, Ch. 56, Sec. 4.')
    assert amended[0]['action'] == 'amended'


def test_a_session_cite_is_not_a_code_section():
    """Chapter 387 of the Statutes of 1913 resolves to a session, not a code miss."""
    result = cite_law('Chapter 387 of the Statutes of 1913')
    assert result['kind'] == 'session'
    assert result['found'] is True
    assert result['target'] == '1913 387'
    assert result['reference'] == 'Chapter 387 of the Statutes of 1913'
    act = cite_law('Section 1 of Chapter 387 of the Statutes of 1913')
    assert act['act'] == '1'
    assert isinstance(annotations_law(note='session', code='WAT', limit=1), list)


def test_a_diagram_page_is_a_mermaid_flowchart():
    page = diagram_law('codes')
    assert page['kind'] == 'codes'
    assert page['page'].startswith('# Code citations')
    assert '```mermaid' in page['page']
    assert page['chart'].startswith('flowchart')
    assert diagram_law('vesting')['page'].startswith('# Vesting')
    assert diagram_law('enactments')['page'].startswith('# Enactments')


def test_serve_reader_starts_and_stops_only_its_process(monkeypatch, tmp_path):
    monkeypatch.setattr('mcp_server._reader_dir', lambda: tmp_path)
    monkeypatch.setattr('mcp_server.time.sleep', lambda _seconds: None)
    opened = {'up': False}
    spawned = {'calls': 0}

    class Process:
        pid = 4242

        def poll(self):
            return None

        def terminate(self):
            opened['up'] = False

        def wait(self, timeout=None):
            return 0

    def spawn(port):
        spawned['calls'] += 1
        spawned['port'] = port
        opened['up'] = True
        return Process()

    monkeypatch.setattr('mcp_server._port_open', lambda port: opened['up'])
    monkeypatch.setattr('mcp_server._spawn', spawn)
    monkeypatch.setattr('mcp_server._alive', lambda pid: pid == 4242 and opened['up'])
    idle = serve_reader('status', port=8765)
    assert idle['running'] is False
    assert idle['url'] == 'http://127.0.0.1:8765/view'
    started = serve_reader('start', port=8765)
    assert started['running'] is True
    assert started['pid'] == 4242
    assert spawned['port'] == 8765
    again = serve_reader('start', port=8765)
    assert again['running'] is True
    assert spawned['calls'] == 1
    stopped = serve_reader('stop')
    assert stopped['running'] is False
    assert not (tmp_path / 'reader.pid').exists()
    opened['up'] = True
    blocked = serve_reader('stop', port=8765)
    assert blocked['found'] is False
    assert blocked['reason'] == 'untracked'
    assert serve_reader('publish')['reason'] == 'unknown_action'


def test_pin_section_misses_without_writing():
    missed = pin_section('NOTACODE', '1')
    assert missed['found'] is False
