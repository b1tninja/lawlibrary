"""Structured statute queries over the local Whoosh index.

Jason and MCP call this module. Sacramento, California (US-CA) is the home
corpus. It does not download publications, and it does not fetch Sacramento
ordinances.
"""

import os
import re
import sqlite3

from whoosh import index
from whoosh.query import And, Term

import corpus
from core import index_dir
from indexer import DEFAULT_COUNTRY, DEFAULT_SUBDIVISION, Indexer
from us.ca.counties.sacramento.cities.sacramento import Sacramento

HEADING_LEVELS = (
    ('division', 'DIVISION_HEADING'),
    ('title', 'TITLE_HEADING'),
    ('part', 'PART_HEADING'),
    ('chapter', 'CHAPTER_HEADING'),
    ('article', 'ARTICLE_HEADING'),
)

ACTS = {
    'davis-stirling': ('CIV', '4000', '6150'),
    'cid-manager': ('BPC', '11500', '11506'),
    'mutual-benefit': ('CORP', '7110', '8910'),
}

TEXT_SPAN_LIMIT = 30

_SECTION_NUM = re.compile(r'^\[?(?P<body>\d+(?:\.\d+)*)(?P<letter>[a-zA-Z]?)\]?\.?$')

_FEDERAL = re.compile(
    r'(?is)'
    r'\b(?:fair\s+housing\s+act|americans?\s+with\s+disabilities|ada|nfip|national\s+flood)\b'
    r'|\b\d+\s+u\.?\s*s\.?\s*c\.?\b'
)

# Known federal bodies Jason hits. Miss still says outside_us_ca; these name the
# official United States Code chapter and CFR title so the caller can fetch later.
_FEDERAL_BODIES = (
    {
        'match': re.compile(
            r'(?is)\bfair\s+housing\s+act\b'
            r'|\b42\s+u\.?\s*s\.?\s*c\.?\s*(?:§§?\s*)?(?:360[1-9]|361\d|362\d|363[01])\b'
        ),
        'statute': {'title': '42', 'chapter': '45'},
        'regulations': {'title': '24'},
    },
    {
        'match': re.compile(
            r'(?is)\bamericans?\s+with\s+disabilities(?:\s+act)?\b|\bada\b'
        ),
        'statute': {'title': '42', 'chapter': '126'},
        'regulations': {'title': '28'},
    },
    {
        'match': re.compile(
            r'(?is)\bnfip\b|\bnational\s+flood(?:\s+insurance)?\b'
        ),
        'statute': {'title': '42', 'chapter': '50'},
        'regulations': {'title': '44'},
    },
)

_USC_TITLE = re.compile(
    r'(?is)\b(?P<title>\d+)\s+u\.?\s*s\.?\s*c\.?\b'
)

_ORDINANCE = re.compile(
    r'(?is)'
    r'(?:sacramento\b.*\b(?:ordinance|municipal|city\s+code|county\s+code|mmc)\b)'
    r'|(?:\b(?:ordinance|municipal\s+code)\b.*\bsacramento\b)'
)

_ACT_NAME = re.compile(
    r'(?i)^\s*(?P<name>davis-stirling|cid-manager|mutual-benefit)\s*$'
)

_CODE_TOKEN = r'[A-Za-z][A-Za-z .]{0,60}?'

_SPAN = re.compile(
    rf'''(?ix)
    ^\s*
    (?P<code>{_CODE_TOKEN})
    \s+
    (?:sections?\s+|§§\s*|§\s*)?
    (?P<start>\d[\d.]*(?:[a-z])?)
    \s*(?:[-–—]|\bto\b)\s*
    (?P<end>\d[\d.]*(?:[a-z])?)
    \s*$
    '''
)

_SECTION = re.compile(
    rf'''(?ix)
    ^\s*
    (?P<code>{_CODE_TOKEN})
    \s+
    (?:section\s+|§\s*)?
    (?P<section>\d[\d.]*(?:[a-z])?)
    (?P<sub>(?:\([a-z0-9]+\))*)?
    \s*$
    '''
)


_ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}


def _roman(text):
    total = 0
    previous = 0
    for char in reversed(str(text or '').strip().upper()):
        value = _ROMAN.get(char)
        if value is None:
            return None
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total or None


def heading_key(value):
    """A division, title, part, chapter, article, or section, in statutory order."""
    text = str(value or '').strip().rstrip('.')
    if _SECTION_NUM.match(text):
        return (0, section_key(text))
    roman = _roman(text)
    if roman is not None:
        return (1, ((roman,), '', text))
    return (2, text.lower())


def section_key(number):
    """Sort key so 5375.5 sits between 5375 and 5376."""
    text = str(number or '').strip()
    matched = _SECTION_NUM.match(text)
    if not matched:
        return ((1 << 30,), '', text)
    parts = tuple(int(piece) for piece in matched.group('body').split('.'))
    letter = (matched.group('letter') or '').lower()
    return (parts, letter, text)


def _in_span(number, start, end):
    key = section_key(number)
    return section_key(start) <= key <= section_key(end)


def _miss(expression, reason, **extra):
    miss = {
        'found': False,
        'reason': reason,
        'expression': expression if expression is not None else '',
    }
    miss.update(extra)
    return miss


def _federal_miss(expression):
    """Outside US-CA; attach statute/CFR corpus pointers when the body is known."""
    text = expression if expression is not None else ''
    for body in _FEDERAL_BODIES:
        if body['match'].search(text):
            return _miss(
                text,
                'outside_us_ca',
                statute=dict(body['statute']),
                regulations=dict(body['regulations']),
            )
    title_match = _USC_TITLE.search(text)
    if title_match:
        return _miss(
            text,
            'outside_us_ca',
            statute={'title': title_match.group('title')},
        )
    return _miss(text, 'outside_us_ca')


def _indexer():
    return Indexer()


def _index_ready(idxer=None):
    idxer = idxer or _indexer()
    return index.exists_in(idxer.idx_path)


def _resolve_known_code(idxer, token):
    token = getattr(token, 'value', token)
    if not isinstance(token, str):
        return None
    resolved = idxer._resolve_code(token)
    codes = idxer._read_codes()
    if resolved in codes:
        return resolved
    return None


def _session_value(idxer, session):
    if session is None:
        years = idxer.sessions()
        return years[-1] if years else None
    if session == 'all':
        return 'all'
    return str(session)


def _path_from_doc(doc):
    path = []
    for level, field in HEADING_LEVELS:
        heading = (doc.get(field) or '').strip()
        if heading:
            path.append({'level': level, 'heading': heading})
    return path


def _section_payload(doc, subdivision=None):
    code = doc.get('LAW_CODE')
    number = doc.get('SECTION_NUM')
    history = doc.get('SECTION_HISTORY') or doc.get('HISTORY') or ''
    payload = {
        'found': True,
        'citation': doc.get('CITATION') or '%s %s' % (code, number),
        'code': code,
        'section': number,
        'subdivision': subdivision,
        'title': doc.get('SECTION_TITLE') or '',
        'path': _path_from_doc(doc),
        'text': doc.get('LEGAL_TEXT') or doc.get('text') or '',
        'session': doc.get('SESSION'),
        'country': doc.get('COUNTRY') or doc.get('country'),
        'region': doc.get('SUBDIVISION') or doc.get('subdivision'),
        'locality': doc.get('LOCALITY') or doc.get('locality') or '',
        'active': bool(doc.get('ACTIVE_FLG', True)),
        'history': history,
        'chapters': _chapters(history),
    }
    when = doc.get('EFFECTIVE_DATE')
    if when is not None:
        payload['effective'] = when.date().isoformat() if hasattr(when, 'date') else str(when)
    return payload


def _chapters(history):
    """Statutes chapters named in a section history credit. Not code chapters."""
    if not history:
        return []
    from structure import find_links
    rows = []
    for link in find_links(history):
        law = link.session
        if link.kind != 'session' or law is None:
            continue
        rows.append({
            'year': law.year,
            'chapter': law.chapter,
            'act': law.act or '',
            'action': '' if link.action is None else link.action.value,
        })
    return rows


def _docs_for_code(idxer, code, session=None, country=None, subdivision=None):
    if not _index_ready(idxer):
        return []
    idx = index.open_dir(idxer.idx_path)
    with idx.searcher() as searcher:
        results = searcher.search(
            Term('LAW_CODE', code),
            limit=None,
            filter=idxer._filter(True, session, country=country, subdivision=subdivision),
        )
        return [dict(hit) for hit in results]


def _sections_in_span(idxer, code, start, end, session=None, country=None, subdivision=None):
    docs = _docs_for_code(
        idxer, code, session=session, country=country, subdivision=subdivision,
    )
    matched = [doc for doc in docs if _in_span(doc.get('SECTION_NUM'), start, end)]
    matched.sort(key=lambda doc: section_key(doc.get('SECTION_NUM')))
    return matched


def _outline_nodes(docs):
    nodes = []
    if not docs:
        return nodes
    for level, field in HEADING_LEVELS:
        current = None
        for doc in docs:
            heading = (doc.get(field) or '').strip()
            number = doc.get('SECTION_NUM')
            if not heading:
                if current is not None:
                    nodes.append(current)
                    current = None
                continue
            if current is None or current['heading'] != heading:
                if current is not None:
                    nodes.append(current)
                current = {
                    'level': level,
                    'heading': heading,
                    'first': number,
                    'last': number,
                    'count': 1,
                }
            else:
                current['last'] = number
                current['count'] += 1
        if current is not None:
            nodes.append(current)
    return nodes


def place(locality='Sacramento'):
    name = (locality or '').strip()
    if name.lower() != Sacramento.name.lower():
        return _miss(locality, 'not_in_index')
    return {
        'country': 'US',
        'region': Sacramento.region(),
        'locality': Sacramento.name,
        'statutes': Sacramento.region(),
        'ordinances': 'absent',
    }


def _get_section_doc(idxer, code, number, session=None, country=None, subdivision=None):
    section_num = str(number).rstrip('.')
    idx = index.open_dir(idxer.idx_path)
    query = And([Term('LAW_CODE', code), Term('SECTION_NUM', section_num)])
    with idx.searcher() as searcher:
        results = searcher.search(
            query,
            limit=20,
            filter=idxer._filter(True, session, country=country, subdivision=subdivision),
        )
        if not results:
            return None
        return dict(results[0])


def _indexed_in(idxer, code, number, *, exclude, country=None, subdivision=None):
    """Other loaded years that store this same code and section number.

    The asked year is left out. An ``all`` lookup already searched every year,
    so the list is empty. This is not a renumbering.
    """
    if exclude == 'all':
        return []
    section_num = str(number).rstrip('.')
    idx = index.open_dir(idxer.idx_path)
    query = And([Term('LAW_CODE', code), Term('SECTION_NUM', section_num)])
    with idx.searcher() as searcher:
        results = searcher.search(
            query,
            limit=50,
            filter=idxer._filter(True, 'all', country=country, subdivision=subdivision),
        )
        rows = []
        seen = set()
        for hit in results:
            doc = dict(hit)
            year = doc.get('SESSION')
            if not year or year == exclude or year in seen:
                continue
            seen.add(year)
            rows.append({
                'session': year,
                'citation': doc.get('CITATION') or '%s %s' % (code, section_num),
            })
    rows.sort(key=lambda row: row['session'])
    return rows


def section(code, number, *, subdivision=None, session=None, country=None, region=None):
    code = getattr(code, 'value', code)
    code = code if isinstance(code, str) else ''
    expression = '%s %s' % (code or '', number or '')
    if subdivision:
        expression = '%s%s' % (
            expression.rstrip(),
            subdivision if str(subdivision).startswith('(') else '(%s)' % subdivision,
        )
    if not (code or '').strip() or number is None or str(number).strip() == '':
        return _miss(expression.strip(), 'not_in_index')
    idxer = _indexer()
    if not _index_ready(idxer):
        return _miss(expression.strip(), 'not_in_index')
    resolved = _resolve_known_code(idxer, code)
    if resolved is None:
        return _miss(expression.strip(), 'unknown_code')
    doc = _get_section_doc(
        idxer, resolved, number, session=session,
        country=country, subdivision=region,
    )
    if doc is None:
        chosen = _session_value(idxer, session)
        return _miss(
            expression.strip(),
            'not_in_index',
            session=chosen,
            indexed_in=_indexed_in(
                idxer, resolved, number, exclude=chosen,
                country=country, subdivision=region,
            ),
        )
    return _section_payload(doc, subdivision=subdivision)


def beside(code, number):
    """The previous and next section in the tightest heading that holds this one.

    The search is that heading, not the whole code. A miss leaves both sides empty.
    """
    idxer = _indexer()
    resolved = _resolve_known_code(idxer, getattr(code, 'value', code))
    if resolved is None or not _index_ready(idxer):
        return {'found': False, 'previous': None, 'next': None}
    doc = _get_section_doc(idxer, resolved, number)
    if doc is None:
        return {'found': False, 'previous': None, 'next': None}
    identity = {
        'division': 'DIVISION',
        'title': 'TITLE',
        'part': 'PART',
        'chapter': 'CHAPTER',
        'article': 'ARTICLE',
    }
    terms = [Term('LAW_CODE', resolved)]
    for level, _stored in HEADING_LEVELS:
        value = (doc.get(identity[level]) or '').strip()
        if value:
            terms.append(Term(identity[level], value))
    numbers = []
    if len(terms) > 1:
        ix = index.open_dir(idxer.idx_path)
        with ix.searcher() as searcher:
            hits = searcher.search(
                And(terms),
                limit=None,
                filter=idxer._filter(True, None),
            )
            numbers = [hit.get('SECTION_NUM') for hit in hits if hit.get('SECTION_NUM')]
    ordered = sorted(set(numbers), key=section_key)
    here = section_key(str(number).rstrip('.'))
    keys = [section_key(item) for item in ordered]
    if here not in keys:
        return {'found': True, 'previous': None, 'next': None}
    place = keys.index(here)
    previous = ordered[place - 1] if place else None
    following = ordered[place + 1] if place + 1 < len(ordered) else None
    return {'found': True, 'previous': previous, 'next': following}


def excerpt(code, number, phrase, **kwargs):
    """The sentence in a stored section that contains ``phrase``.

    The section is looked up. A section that is not in the index, or a
    phrase that is not in that section, is an empty string.
    """
    doc = section(code, number, **kwargs)
    text = doc.get('text') or ''
    if not doc.get('found') or not text or not phrase:
        return ''
    from analysis import split_sentences
    needle = str(phrase).casefold()
    for sentence in split_sentences(text):
        if needle in sentence.casefold():
            return sentence
    return ''


def outline(code, start, end, *, session=None, country=None, subdivision=None):
    expression = '%s %s-%s' % (code or '', start or '', end or '')
    if not (code or '').strip() or start is None or end is None:
        return _miss(expression.strip(), 'not_in_index')
    idxer = _indexer()
    if not _index_ready(idxer):
        return _miss(expression.strip(), 'not_in_index')
    resolved = _resolve_known_code(idxer, code)
    if resolved is None:
        return _miss(expression.strip(), 'unknown_code')
    docs = _sections_in_span(
        idxer, resolved, start, end, session=session,
        country=country, subdivision=subdivision,
    )
    if not docs:
        return _miss(expression.strip(), 'not_in_index')
    chosen = _session_value(idxer, session)
    return {
        'found': True,
        'code': resolved,
        'start': str(start).rstrip('.'),
        'end': str(end).rstrip('.'),
        'session': None if chosen == 'all' else chosen,
        'nodes': _outline_nodes(docs),
    }


def range(code, start, end, *, session=None, text=False, country=None, subdivision=None):
    expression = '%s %s-%s' % (code or '', start or '', end or '')
    idxer = _indexer()
    if not (code or '').strip() or start is None or end is None:
        return _miss(expression.strip(), 'not_in_index')
    if not _index_ready(idxer):
        return _miss(expression.strip(), 'not_in_index')
    resolved = _resolve_known_code(idxer, code)
    if resolved is None:
        return _miss(expression.strip(), 'unknown_code')

    mutual = ACTS['mutual-benefit']
    is_mutual = (
        resolved == mutual[0]
        and section_key(start) == section_key(mutual[1])
        and section_key(end) == section_key(mutual[2])
    )

    docs = _sections_in_span(
        idxer, resolved, start, end, session=session,
        country=country, subdivision=subdivision,
    )
    if not docs:
        return _miss(expression.strip(), 'not_in_index')

    if text and (is_mutual or len(docs) > TEXT_SPAN_LIMIT):
        result = outline(
            resolved, start, end, session=session,
            country=country, subdivision=subdivision,
        )
        if result.get('found'):
            result['reason'] = 'span_too_large'
        return result

    if text:
        chosen = _session_value(idxer, session)
        return {
            'found': True,
            'code': resolved,
            'start': str(start).rstrip('.'),
            'end': str(end).rstrip('.'),
            'session': None if chosen == 'all' else chosen,
            'sections': [_section_payload(doc) for doc in docs],
        }

    return outline(
        resolved, start, end, session=session,
        country=country, subdivision=subdivision,
    )


def _hit_from_section(doc):
    return {
        'citation': doc.get('citation'),
        'code': doc.get('code'),
        'section': doc.get('section'),
        'path': doc.get('path') or [],
        'snippet': (doc.get('text') or '')[:240],
        'session': doc.get('session'),
        'country': doc.get('country'),
        'subdivision': doc.get('region') or '',
        'locality': doc.get('locality') or '',
    }


def _citation_hits(text, limit, session, country, subdivision):
    """Open sections named by a § or §§ citation inside the query."""
    from citations import Cite, find_citations

    points = [point for point in find_citations(text) if point.code and point.numbers]
    if not points:
        return []
    hits = []
    for point in points:
        if point.cite is Cite.RANGE and len(point.numbers) >= 2:
            opened = range(
                point.code, point.numbers[0], point.numbers[-1],
                text=True, session=session, country=country, subdivision=subdivision,
            )
            for doc in opened.get('sections') or []:
                hits.append(_hit_from_section(doc))
                if len(hits) >= limit:
                    return hits
            continue
        for number in point.numbers:
            doc = section(
                point.code, number, session=session,
                country=country, region=subdivision,
            )
            if doc.get('found'):
                hits.append(_hit_from_section(doc))
            if len(hits) >= limit:
                return hits
    return hits


def search(query, *, code=None, codes=None, start=None, end=None, limit=10, session=None,
           country=None, subdivision=None):
    if query is None or str(query).strip() == '':
        return []
    if _ORDINANCE.search(str(query)):
        return []
    cited = _citation_hits(str(query), limit, session, country, subdivision)
    if cited:
        return cited
    idxer = _indexer()
    if not _index_ready(idxer):
        return []

    if country is None:
        country = DEFAULT_COUNTRY
    if subdivision is None:
        subdivision = DEFAULT_SUBDIVISION

    named = []
    if code is not None and str(getattr(code, 'value', code) or '').strip() != '':
        named.append(code)
    named.extend(codes or ())
    allowed = set()
    for item in named:
        token = _resolve_known_code(idxer, item)
        if token is None:
            return []
        allowed.add(token)
    resolved = next(iter(allowed)) if len(allowed) == 1 else None

    span_filter = bool(allowed) or start is not None or end is not None
    fetch_limit = max(limit * 25, 50) if span_filter else limit
    hits = idxer.search_law(
        query, limit=fetch_limit, session=session,
        country=country, subdivision=subdivision,
    )

    results = []
    for hit in hits:
        hit_code = hit.get('code')
        hit_section = hit.get('section')
        if allowed and hit_code not in allowed:
            continue
        if start is not None and end is not None and not _in_span(hit_section, start, end):
            continue
        if start is not None and end is None and section_key(hit_section) < section_key(start):
            continue
        if end is not None and start is None and section_key(hit_section) > section_key(end):
            continue
        doc = {
            'DIVISION_HEADING': hit.get('division'),
            'TITLE_HEADING': None,
            'PART_HEADING': hit.get('part'),
            'CHAPTER_HEADING': hit.get('chapter'),
            'ARTICLE_HEADING': hit.get('article'),
        }
        results.append({
            'citation': hit.get('citation'),
            'code': hit_code,
            'section': hit_section,
            'path': _path_from_doc(doc),
            'snippet': hit.get('snippet') or '',
            'session': hit.get('session'),
            'country': hit.get('country'),
            'subdivision': hit.get('subdivision'),
            'locality': hit.get('locality') or '',
        })
        if len(results) >= limit:
            break
    return results


def act(name, *, session=None):
    key = (name or '').strip().lower()
    if not key:
        return _miss(name, 'unknown_act')
    if key not in ACTS:
        return _miss(name, 'unknown_act')
    code, start, end = ACTS[key]
    return outline(code, start, end, session=session)


def parse_citation(expression):
    """Parse a citation string into a structured ask, or a miss dict."""
    text = expression if expression is not None else ''
    stripped = str(text).strip()
    if not stripped:
        return _miss(stripped, 'not_in_index')
    if _ORDINANCE.search(stripped):
        return _miss(stripped, 'ordinance_absent')
    if _FEDERAL.search(stripped):
        return _federal_miss(stripped)

    act_match = _ACT_NAME.match(stripped)
    if act_match:
        return {
            'kind': 'act',
            'name': act_match.group('name').lower(),
            'expression': stripped,
        }

    span_match = _SPAN.match(stripped)
    if span_match:
        return {
            'kind': 'span',
            'code': span_match.group('code').strip(),
            'start': span_match.group('start').rstrip('.'),
            'end': span_match.group('end').rstrip('.'),
            'expression': stripped,
        }

    section_match = _SECTION.match(stripped)
    if section_match:
        sub = section_match.group('sub') or None
        return {
            'kind': 'section',
            'code': section_match.group('code').strip(),
            'section': section_match.group('section').rstrip('.'),
            'subdivision': sub,
            'expression': stripped,
        }

    return _miss(stripped, 'not_in_index')


def session_law(year, chapter, act=None):
    """A chapter of the Statutes of a year. This is not a code section."""
    from needles import Session
    if not str(year or '').strip() or not str(chapter or '').strip():
        return _miss('Statutes', 'not_in_index', kind='session')
    law = Session.year(year).chapter(chapter)
    if act:
        law = law.section(act)
    return {
        'found': True,
        'kind': 'session',
        'year': law.year,
        'chapter': law.chapter,
        'act': law.act,
        'reference': law.reference(),
        'target': law.target(),
    }


def cite(expression, *, session=None):
    from structure import find_links
    session_links = [link for link in find_links(expression or '') if link.kind == 'session']
    parsed = parse_citation(expression)
    if session_links and parsed.get('found') is False:
        law = session_links[0].citation()
        return session_law(law.year, law.chapter, law.act)
    if parsed.get('found') is False:
        return parsed
    kind = parsed['kind']
    if kind == 'act':
        return act(parsed['name'], session=session)
    if kind == 'span':
        return outline(parsed['code'], parsed['start'], parsed['end'], session=session)
    if kind == 'section':
        return section(
            parsed['code'],
            parsed['section'],
            subdivision=parsed.get('subdivision'),
            session=session,
        )
    return _miss(expression, 'not_in_index')


def federal_section(title, section, *, kind):
    """Read one USC or CFR section from a loaded corpus SQLite file.

    kind is ``usc`` or ``cfr``. A missing file or missing row is a miss;
    this does not download or scrape.
    """
    title = str(title or '').strip()
    section = str(section or '').strip()
    kind = str(kind or '').strip().lower()
    if kind == 'usc':
        path = corpus.corpus_path('US')
        citation = '%s USC %s' % (title, section)
    elif kind == 'cfr':
        path = corpus.cfr_corpus_path(title)
        citation = '%s CFR %s' % (title, section)
    else:
        citation = '%s %s %s' % (title, (kind or 'USC').upper(), section)
        return _miss(citation, 'not_in_index', corpus='')

    if not title or not section or not os.path.isfile(path):
        return _miss(citation, 'not_in_index', corpus=path)

    try:
        db = sqlite3.connect(path)
        try:
            row = db.execute(
                'SELECT legal_text FROM section '
                'WHERE law_code = ? AND section_num = ?',
                (title, section),
            ).fetchone()
        finally:
            db.close()
    except sqlite3.Error:
        return _miss(citation, 'not_in_index', corpus=path)

    if row is None:
        return _miss(citation, 'not_in_index', corpus=path)

    return {
        'found': True,
        'kind': kind,
        'citation': citation,
        'code': title,
        'section': section,
        'text': row[0] or '',
    }


_LADDER = (
    ('division', 'DIVISION', 'DIVISION_HEADING'),
    ('title', 'TITLE', 'TITLE_HEADING'),
    ('part', 'PART', 'PART_HEADING'),
    ('chapter', 'CHAPTER', 'CHAPTER_HEADING'),
    ('article', 'ARTICLE', 'ARTICLE_HEADING'),
    ('section', 'SECTION_NUM', 'SECTION_TITLE'),
)
_UNITS = {unit for unit, _field, _heading in _LADDER}


class LawPath:
    """One node in a code tree.

    ``us-ca/civ/division/1/section/1940`` is Civil Code section 1940
    inside division 1. ``subdivision`` is a label inside the section.
    """

    def __init__(self, region, code=None, units=(), subdivision=None):
        self.region = (region or DEFAULT_SUBDIVISION).upper()
        self.code = (code or '').upper() or None
        self.units = tuple(units)
        self.subdivision = subdivision

    @property
    def section(self):
        for unit, value in self.units:
            if unit == 'section':
                return value
        return None

    @property
    def url(self):
        parts = [self.region.lower()]
        if self.code:
            parts.append(self.code.lower())
        for unit, value in self.units:
            parts.extend((unit, value))
        if self.subdivision:
            parts.extend(('subdivision', self.subdivision.strip('()')))
        return '/'.join(parts)

    def child(self, unit, value):
        if unit == 'subdivision':
            return LawPath(self.region, self.code, self.units, value)
        return LawPath(self.region, self.code, self.units + ((unit, str(value)),))


def parse_law_url(url):
    """A path into the code tree. An empty path is the home region."""
    parts = [part for part in str(url or '').strip().strip('/').split('/') if part]
    if not parts:
        return LawPath(DEFAULT_SUBDIVISION)
    region = parts[0].upper()
    if len(parts) == 1:
        return LawPath(region)
    code = parts[1]
    units = []
    subdivision = None
    rest = parts[2:]
    index = 0
    while index < len(rest):
        unit = rest[index].lower()
        if index + 1 >= len(rest):
            break
        value = rest[index + 1]
        if unit == 'subdivision':
            subdivision = value
        elif unit in _UNITS:
            units.append((unit, value))
        index += 2
    return LawPath(region, code, units, subdivision)


def _constraints(path):
    """The same year filter as a section lookup. Stored rows have no subdivision."""
    terms = []
    filt = _indexer()._filter(True, None)
    if filt is not None:
        terms.append(filt)
    if path.code:
        terms.append(Term('LAW_CODE', path.code))
    fields = {unit: field for unit, field, _heading in _LADDER}
    for unit, value in path.units:
        field = fields.get(unit)
        if field:
            terms.append(Term(field, value))
    return And(terms) if len(terms) > 1 else terms[0]


def law_tree(url=''):
    """The node at ``url`` and the children one level down.

    A region lists codes. A code lists the next heading that is present.
    A section lists its subdivision labels. A missing index is found false.
    """
    path = parse_law_url(url)
    node = {'url': path.url, 'region': path.region, 'code': path.code, 'found': True, 'children': []}
    if path.section:
        node['section'] = path.section
    if not _index_ready():
        node['found'] = False
        node['reason'] = 'not_in_index'
        return node
    if path.code is None:
        for row in _indexer().list_codes():
            child = LawPath(path.region, row['code'])
            node['children'].append({'url': child.url, 'unit': 'code', 'value': row['code'], 'heading': row['title']})
        return node
    if path.section and path.subdivision is None:
        from apa import Code
        from places import Citation
        try:
            book = Code.get(path.code)
        except KeyError:
            node['found'] = False
            node['reason'] = 'unknown_code'
            return node
        labels = Citation(book).section(path.section).subdivisions
        node['children'] = [
            {'url': path.child('subdivision', label.strip('()')).url, 'unit': 'subdivision', 'value': label}
            for label in labels
        ]
        return node
    if path.subdivision:
        return node
    seen = {unit for unit, _value in path.units}
    ix = index.open_dir(_indexer().idx_path)
    with ix.searcher() as searcher:
        hits = searcher.search(_constraints(path), limit=None)
        for unit, field, heading in _LADDER:
            if unit in seen:
                continue
            found = {}
            for hit in hits:
                value = (hit.get(field) or '').strip()
                if not value or value in found:
                    continue
                found[value] = (hit.get(heading) or '').strip()
                if len(found) >= 400:
                    break
            if not found:
                continue
            node['children'] = [
                {'url': path.child(unit, value).url, 'unit': unit, 'value': value, 'heading': text}
                for value, text in found.items()
            ]
            node['children'].sort(key=lambda child: heading_key(child.get('value')))
            return node
    return node


def index_path():
    return str(index_dir())


def index_present():
    path = index_path()
    return os.path.isdir(path) and index.exists_in(path)
