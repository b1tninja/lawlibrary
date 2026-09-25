"""MCP server over the local statute index.

Home corpus is California (US-CA). The index can hold other ISO regions.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from agency import agencies
from analysis import analyze, pin, pins
from court import courts
from entities import list_corpora as corpora_on_disk, list_entities
from companions import editions, search_manual
from structure import Diagram
from structure import review as review_section
from indexer import Indexer
import query as law_query
import sample as law_sample

mcp = FastMCP('lawlibrary')


def _indexer():
    return Indexer()


def _plain_node(node):
    """A walk whose code members are tokens. The cached node is left as it is."""
    if not isinstance(node, dict):
        return node
    out = dict(node)
    links = []
    for link in out.get('links') or []:
        row = dict(link)
        book = row.get('code')
        if hasattr(book, 'value'):
            row['code'] = book.value
        links.append(row)
    if 'links' in out:
        out['links'] = links
    if out.get('children'):
        out['children'] = [_plain_node(child) for child in out['children']]
    return out


@mcp.tool()
def list_governments(kind: str = '') -> list:
    """Countries, states, counties, cities, and departments.

    kind: country, state, county, city, or department. Empty returns all.
    A state is a regional ISO subdivision. A department is a political body
    that adopts rules under its own statute. corpus is the schema to attach
    when that body has an independent database. None means no file yet.
    """
    return list_entities(kind or None)


@mcp.tool()
def list_corpora() -> list:
    """Independent statute and regulation databases, and whether each file is loaded.

    schema is the ATTACH name. present is false until that publication has been written.
    """
    return corpora_on_disk()


@mcp.tool()
def list_codes() -> list:
    """List codes present in the local index, with their official titles."""
    return _indexer().list_codes()


@mcp.tool()
def tree_law(url: str = '') -> dict:
    """One level of the code tree.

    url is a path such as us-ca, us-ca/civ, or us-ca/civ/division/1/section/1940.
    The region comes first, then the code, then unit/value pairs.
    Units are division, title, part, chapter, article, section, and subdivision.
    children are the next level only. A section's children are its labels.
    An empty url is the home region, us-ca.
    """
    return law_query.law_tree(url)


@mcp.tool()
def list_sessions() -> list:
    """Session years present in the local index. The newest is the law currently in force."""
    return _indexer().sessions()


@mcp.tool()
def _named_codes(text):
    """``same`` or a comma-separated list of code tokens. Empty is every book."""
    raw = (text or '').strip()
    if not raw:
        return None, False
    if raw.lower() == 'same':
        return None, True
    return [part.strip() for part in raw.split(',') if part.strip()], False


def search_law(query: str, limit: int = 10, session: str = '',
               country: str = '', subdivision: str = '', codes: str = '') -> list:
    """Full-text search of codified law.

    query: words, a phrase, or a citation such as "CIV 1940" or "Civil Code section 1940".
    session: a session year such as "2019", or "all". Empty uses the newest session.
    country: ISO 3166-1 alpha-2. Empty defaults to US.
    subdivision: ISO 3166-2. Empty defaults to US-CA (California).
    codes: a comma-separated list of books, such as "CIV,RTC". Empty searches every book.
    A section sign is opened as a citation: § is one section, §§ with a dash is a range,
    and §§ with commas is a series. Other queries stay a word search.
    Returns active sections with the heading path and a short snippet. Use get_section for the full text.
    """
    chosen = session or None
    named, _same = _named_codes(codes)
    return law_query.search(
        query,
        codes=named,
        limit=limit,
        session=chosen,
        country=country or None,
        subdivision=subdivision or None,
    )


@mcp.tool()
def get_section(code: str, section: str, session: str = '',
                subdivision_label: str = '') -> dict:
    """Return one active California section as words, or a miss.

    code: official abbreviation or title, such as "CIV" or "Civil Code".
    section: section number, such as "1940" or "1940.5".
    subdivision_label: a label such as "(d)" or "a". The text is the whole section.
    session: a session year, or "all". Empty uses the newest session.
    A hit has found, citation, text, path, session, and chapters.
    chapters is each Stats. credit: year, chapter, act, and action.
    A miss has found false and reason.
    """
    chosen = session or None
    label = subdivision_label or None
    return law_query.section(code, section, subdivision=label, session=chosen)


@mcp.tool()
def place(locality: str = 'Sacramento') -> dict:
    """Scope a query to a locality. Sacramento ordinances are absent from this index."""
    return law_query.place(locality=locality)


@mcp.tool()
def cite_law(expression: str, session: str = '') -> dict:
    """Resolve a citation, span, or named act to a section, outline, or miss.

    expression: forms such as "CIV 5806", "Civil Code section 5806",
    "CIV 4000-6150", or "davis-stirling".
    session: a session year, or "all". Empty uses the newest session.
    Payload includes kind: "section" | "outline" | "miss".
    """
    chosen = session or None
    result = law_query.cite(expression, session=chosen)
    if result.get('kind') == 'session':
        return result
    if result.get('found') is False:
        result = dict(result)
        result['kind'] = 'miss'
        return result
    result = dict(result)
    if 'nodes' in result:
        result['kind'] = 'outline'
    else:
        result['kind'] = 'section'
    return result


@mcp.tool()
def outline_law(code: str, start: str, end: str, session: str = '') -> dict:
    """Outline heading groups for a numeric section span in one code.

    code: official abbreviation or title, such as "CIV".
    start, end: section numbers, such as "5800" and "5810".
    session: a session year, or "all". Empty uses the newest session.
    """
    chosen = session or None
    return law_query.outline(code, start, end, session=chosen)


@mcp.tool()
def act_law(name: str, session: str = '') -> dict:
    """Outline a named California act.

    name: davis-stirling, cid-manager, or mutual-benefit.
    session: a session year, or "all". Empty uses the newest session.
    mutual-benefit returns an outline only. A miss has found false and reason unknown_act.
    """
    chosen = session or None
    result = law_query.act(name, session=chosen)
    result = dict(result)
    result['kind'] = 'miss' if result.get('found') is False else 'outline'
    return result


@mcp.tool()
def range_law(code: str, start: str, end: str, text: bool = False, session: str = '') -> dict:
    """Outline a span, or return section text when the span is at most 30 sections.

    code: official abbreviation or title.
    start, end: section numbers.
    text: when true, return section words only if the span has at most 30 sections.
    A larger span, including mutual-benefit, returns the outline and reason span_too_large.
    """
    chosen = session or None
    result = law_query.range(code, start, end, session=chosen, text=text)
    result = dict(result)
    if result.get('found') is False:
        result['kind'] = 'miss'
    elif 'sections' in result:
        result['kind'] = 'sections'
    else:
        result['kind'] = 'outline'
    return result


@mcp.tool()
def federal_section(title: str, section: str, kind: str = 'usc') -> dict:
    """Words only if that corpus file has been loaded; absence is a miss; do not scrape."""
    return law_query.federal_section(title, section, kind=kind)


@mcp.tool()
def search_span(query: str, code: str = '', start: str = '', end: str = '',
                limit: int = 10, session: str = '',
                country: str = '', subdivision: str = '') -> dict:
    """Full-text search limited to an optional code and numeric section span.

    query: words or a phrase.
    code: optional code abbreviation or title.
    start, end: optional section bounds. When both are set, hits outside the span are dropped.
    session: a session year, or "all". Empty uses the newest session.
    country: ISO 3166-1 alpha-2. Empty defaults to US.
    subdivision: ISO 3166-2. Empty defaults to US-CA.
    Returns {found, hits}. A Sacramento ordinance or a federal statute is a miss with an empty hits list.
    """
    chosen = session or None
    parsed = law_query.parse_citation(query)
    reason = parsed.get('reason')
    if reason in ('ordinance_absent', 'outside_us_ca'):
        result = dict(parsed)
        result['hits'] = []
        return result
    hits = law_query.search(
        query,
        code=code or None,
        start=start or None,
        end=end or None,
        limit=limit,
        session=chosen,
        country=country or None,
        subdivision=subdivision or None,
    )
    return {'found': True, 'hits': hits}


def _parent_name(parent):
    if isinstance(parent, str):
        return parent
    if isinstance(parent, type):
        return parent.__name__
    return None


def _subject_row(body, sentence):
    relations = []
    for item in body.relations:
        if hasattr(item, 'relation'):
            relations.append({'fact': item.relation.value, 'detail': item.text})
        else:
            relations.append({'fact': item.name, 'detail': item.text})
    return {
        'model': type(body).__name__,
        'kind': body.kind.value,
        'observed': body.observed,
        'jurisdiction': body.code or _parent_name(type(body).parent),
        'relations': relations,
        'citations': [
            {
                'cite': point.cite.value,
                'numbers': list(point.numbers),
                'code': point.code,
                'signal': point.signal,
                'text': point.text,
            }
            for point in body.citations
        ],
        'sentence': sentence,
    }


@mcp.tool()
def list_offices() -> list:
    """Registered agencies. Each row is the printed name, the class, and the statute that creates it.

    authority is empty until a section has been pinned. functions are the shared roles.
    """
    rows = []
    for office in agencies():
        rows.append({
            'model': office.__name__,
            'name': office.name,
            'parent': _parent_name(office.parent),
            'functions': [role.value for role in office.functions],
            'authority': office.authority,
            'source': office.source,
        })
    return rows


@mcp.tool()
def list_courts() -> list:
    """Registered courts, from the reviewing court down to the trial court.

    bench is supreme, appellate, trial, or article_i. jurisdiction is the government code.
    """
    rows = []
    for court in courts():
        rows.append({
            'model': court.__name__,
            'name': court.name,
            'bench': court.bench.value,
            'parent': _parent_name(court.parent),
            'jurisdiction': court.government(),
            'authority': court.authority,
            'divisions': [division.value for division in court.divisions],
            'source': court.source,
        })
    return rows


@mcp.tool()
def analyze_text(text: str) -> dict:
    """Read statute text into offices, courts, places, duties, and citations.

    A known name is the registered class. An unknown department stays Agency.
    A duty in a later sentence stays on the office named earlier.
    Does not write a pin and does not search the index.
    """
    reading = analyze(text or '')
    return {
        'sentences': [
            {
                'text': sentence.text,
                'subjects': [_subject_row(body, sentence.text) for body in sentence.subjects],
                'clauses': [mark.clause.value for mark in sentence.clauses],
            }
            for sentence in reading.sentences
        ],
    }


@mcp.tool()
def list_pins(citation: str = '', model: str = '', fact: str = '') -> list:
    """Pins of jurisdiction and delegation already stored.

    citation: such as "BPC 10050". model: class name. fact: jurisdiction, responsibility, establishment, or another frame.
    Empty filters return every pin.
    """
    return pins(
        citation=citation or None,
        model=model or None,
        fact=fact or None,
    )


@mcp.tool()
def pin_section(code: str, section: str) -> dict:
    """Read one indexed section, analyze it, and store jurisdiction and delegation pins.

    A miss from get_section is returned unchanged and nothing is written.
    """
    doc = law_query.section(code, section)
    if not doc.get('found'):
        return doc
    reading = analyze(doc.get('text') or '')
    pin(reading, doc.get('citation'))
    return {
        'found': True,
        'citation': doc.get('citation'),
        'pins': pins(citation=doc.get('citation')),
    }


@mcp.tool()
def list_sources() -> list:
    """Books a parser can sample: indexed statutes, CFR titles, and court-rule pointers.

    kind is statute, regulation, or rule. present is true when the words are on disk.
    A rule row has a url and a shape. Its text is not downloaded.
    """
    return law_sample.sources()


@mcp.tool()
def sample_book(book: str, n: int = 3, seed: str = '', kind: str = '', pattern: str = '') -> dict:
    """Draw a few sections from one book so a lexical pass can be developed against real wording.

    book: a code such as CIV, a CFR title such as 24, or a court class such as SacramentoSuperiorCourt.
    n: how many sections, at most 20.
    seed: the same seed returns the same sections. Empty picks a seed and returns it.
    kind: statute, regulation, or rule. Empty infers statute, or regulation when book is a number.
    pattern: optional words that a statute section must match.
    A court rule returns found false and reason not_indexed, with the official url.
    """
    return law_sample.Draw(book).take(n).seed(seed or None).kind(kind or None).matching(pattern or None).choose()


@mcp.tool()
def list_style_manuals(standing: str = '') -> list:
    """Citation manuals. standing is posted or lesser. Empty returns both.

    A posted edition is free at source. A lesser edition is sold. This tool
    does not download either one. present is true when that guide has been indexed.
    """
    from companions import Standing
    from corpus import manual_corpus_path
    import os

    chosen = None
    if standing:
        chosen = Standing(standing)
    rows = []
    for edition in editions(standing=chosen):
        path = manual_corpus_path(edition.guide.value.upper())
        rows.append({
            'guide': edition.guide.value,
            'title': edition.title,
            'source': edition.source,
            'standing': edition.standing.value,
            'shape': edition.shape.value,
            'note': edition.note,
            'present': os.path.isfile(path),
        })
    return rows


@mcp.tool()
def search_style_manual(guide: str, words: str, limit: int = 5) -> dict:
    """Search a style manual that has been indexed from a posted HTML edition.

    guide: indigo, apa, or california_style_manual.
    words: a phrase in the manual text.
    A guide that has not been indexed returns found false and reason absent.
    A lesser manual is not fetched.
    """
    return search_manual(guide, words, limit=limit)


def _weight_row(weight, needle):
    return {
        'term': weight.term,
        'tf': weight.tf,
        'df': weight.df,
        'idf': weight.idf,
        'score': weight.score,
        'needle': needle,
    }


@mcp.tool()
def common_terms(scope: str, key: str, limit: int = 20) -> dict:
    """The most common terms in a scope, the inverse of the distinctive rank.

    scope is code, chapter, division, article, state, or federal.
    key is a member such as CIV, or FGC 1 for a chapter.
    A term already registered as a needle form has needle true.
    The rest are candidates. A missing member is found false.
    """
    from weight import Scope
    found = Scope(scope)(key).take(limit).needles()
    needles = {weight.term for weight in found.get('needles') or []}
    found['terms'] = [
        _weight_row(weight, weight.term in needles) for weight in found.get('terms') or []
    ]
    found['needles'] = [row['term'] for row in found['terms'] if row['needle']]
    found['candidates'] = [row['term'] for row in found['terms'] if not row['needle']]
    scope = found.get('scope')
    found['scope'] = scope.value if scope is not None else scope
    return found


@mcp.tool()
def annotations_law(note: str = '', code: str = '', target: str = '', limit: int = 24) -> list:
    """Annotations stored with the needles.

    note: amount, period, date, antecedent, session, case, cut, citation, or named_act. Empty returns a mixed page.
    A citation row includes cite (section, range, or series) and join (conjunction, disjunction, or both).
    A session credit target is the action, the year, and the chapter, such as added 2011 383.
    A chapter with no history verb stays the year, then the chapter.
    A case target is uppercase or title.
    code is an abbreviation such as WAT.
    """
    return _indexer().annotations(
        note=note or None, code=code or None, target=target or None, limit=limit,
    )


@mcp.tool()
def related_law(code: str, section: str, depth: int = 1, codes: str = '') -> dict:
    """A California section, its subdivisions, and the statutes it cites.

    depth is how many hops of Section N of the Other Code to follow.
    0 is the section alone. A negative depth follows until a section repeats.
    A chapter of the Statutes of a year is a link, and it is not opened.
    codes: empty follows every book. "same" stays in the open book.
    Otherwise a comma-separated list such as "CIV,RTC".
    A citation outside that scope stays on the section and is not opened.
    The payload includes the plaintext, the subdivision labels, the links,
    and a mermaid flowchart. page is that flowchart as a Markdown page.
    sessions is the year and chapter. A history credit also names the action.
    articles is the article and section.
    Neither is opened. A missing section is found false.
    """
    from apa import Code
    from places import Citation
    try:
        book = Code.get(code)
    except KeyError:
        return {'found': False, 'reason': 'unknown_book', 'mermaid': ''}
    named, same = _named_codes(codes)
    cited = Citation(book).section(section).hops(depth)
    if same:
        cited = cited.same()
    elif named:
        books = []
        for token in named:
            try:
                books.append(Code.get(token))
            except KeyError:
                continue
        if books:
            cited = cited.only(*books)
    node = cited.refs
    payload = _plain_node(node.tree)
    payload['page'] = node.md
    payload['sessions'] = node.sessions
    payload['articles'] = node.articles
    return payload


@mcp.tool()
def diagram_law(kind: str = 'codes', code: str = '') -> dict:
    """A stored graph as a Markdown page with a mermaid flowchart.

    kind: codes, vesting, or enactments.
    codes is one node per book and a cites arrow where one book names another.
    vesting is an office grant. code narrows it to one book, such as GOV.
    enactments is a section and the Statutes chapter that enacted it.
    The chapter is a node. It is not opened.
    page is the Markdown. chart is the flowchart alone. Chat draws a flowchart.
    """
    chosen = (kind or 'codes').strip().lower()
    if chosen == 'vesting':
        diagram = Diagram.vesting()
    elif chosen == 'enactments':
        diagram = Diagram.enactments()
    else:
        diagram = Diagram.codes()
    if code:
        diagram = diagram.code(code)
    return {'kind': diagram.kind, 'chart': diagram.chart(), 'page': diagram.page()}


@mcp.tool()
def review_law(code: str, section: str, depth: int = 1, codes: str = '') -> dict:
    """Citation phrases in a section that the parser did not keep.

    depth and codes match related_law. "same" reviews only the open book.
    Each gap is a short title, an unresolved book, or an unlinked phrase.
    The words are the retrieved text. A missing section is found false.
    Write the gap down before changing the parser.
    """
    named, same = _named_codes(codes)
    payload = review_section(code, section, depth=depth, codes=named, same=same)
    for gap in payload.get('gaps') or []:
        book = gap.get('code')
        gap['code'] = book.value if book is not None else None
        gap['gap'] = gap['gap'].value
    return payload


_SERVE = 'from application import serve\nimport sys\nserve(sys.argv[1])\n'
_reader_proc = None


def _reader_dir():
    path = Path(__file__).resolve().parent / 'data'
    path.mkdir(exist_ok=True)
    return path


def _reader_record():
    path = _reader_dir() / 'reader.pid'
    if not path.is_file():
        return None, None
    parts = path.read_text(encoding='utf-8').split()
    if not parts:
        return None, None
    try:
        pid = int(parts[0])
        port = int(parts[1]) if len(parts) > 1 else 8765
    except ValueError:
        return None, None
    return pid, port


def _write_reader(pid, port):
    (_reader_dir() / 'reader.pid').write_text('%s %s\n' % (pid, port), encoding='utf-8')


def _clear_reader():
    path = _reader_dir() / 'reader.pid'
    if path.is_file():
        path.unlink()


def _port_open(port):
    with socket.socket() as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(('127.0.0.1', port)) == 0


def _alive(pid):
    """Whether that process id still exists. Signal 0 is not used on Windows."""
    if not pid or pid < 0:
        return False
    if os.name == 'nt':
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _spawn(port):
    log = open(_reader_dir() / 'reader.log', 'a', encoding='utf-8')
    return subprocess.Popen(
        [sys.executable, '-c', _SERVE, str(port)],
        cwd=str(Path(__file__).resolve().parent),
        stdout=log,
        stderr=subprocess.STDOUT,
    )


def _stop_pid(pid):
    global _reader_proc
    if _reader_proc is not None and _reader_proc.pid == pid:
        _reader_proc.terminate()
        try:
            _reader_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _reader_proc.kill()
        _reader_proc = None
        return
    if _alive(pid):
        os.kill(pid, 15)


def _reader_view(port, pid, running):
    return {
        'found': True,
        'running': running,
        'port': port,
        'pid': pid if pid and _alive(pid) else None,
        'url': 'http://127.0.0.1:%s/view' % port,
    }


def _serve_reader(action, port):
    """Start, stop, or report the development reader on 127.0.0.1."""
    global _reader_proc
    chosen = (action or 'status').strip().lower()
    try:
        number = int(port)
    except (TypeError, ValueError):
        return {'found': False, 'reason': 'port', 'running': False}
    if number < 1 or number > 65535:
        return {'found': False, 'reason': 'port', 'running': False}
    if chosen not in ('start', 'stop', 'status'):
        return {'found': False, 'reason': 'unknown_action', 'running': False}
    recorded, recorded_port = _reader_record()
    if chosen == 'status':
        watch = recorded_port or number
        return _reader_view(watch, recorded, _port_open(watch))
    if chosen == 'stop':
        watch = recorded_port or number
        if recorded and _alive(recorded):
            _stop_pid(recorded)
            for _ in range(20):
                if not _port_open(watch):
                    break
                time.sleep(0.1)
        elif _port_open(watch):
            return {
                'found': False,
                'reason': 'untracked',
                'running': True,
                'port': watch,
                'url': 'http://127.0.0.1:%s/view' % watch,
            }
        _clear_reader()
        _reader_proc = None
        return _reader_view(watch, None, _port_open(watch))
    if _port_open(number):
        return _reader_view(number, recorded, True)
    _reader_proc = _spawn(number)
    _write_reader(_reader_proc.pid, number)
    for _ in range(20):
        if _port_open(number):
            return _reader_view(number, _reader_proc.pid, True)
        if _reader_proc.poll() is not None:
            break
        time.sleep(0.1)
    return {'found': False, 'reason': 'stopped', 'running': False, 'port': number, 'pid': _reader_proc.pid}


@mcp.tool()
def serve_reader(action: str = 'status', port: int = 8765) -> dict:
    """Start, stop, or report the development reader.

    action: start, stop, or status. The process binds 127.0.0.1 only.
    url is the /view page. A start that finds the port open leaves that process running.
    A stop ends only the process this tool recorded. An open port with no record stays up.
    """
    return _serve_reader(action, port)


def main():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
