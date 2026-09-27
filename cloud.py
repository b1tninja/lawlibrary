"""The words of a heading, counted from what the index already recorded.

A cloud is one node of the library and the sections under it. Each section
carries four count maps, and each map is a family of word the library already
keeps: the surface words its word classes matched, the annotation kinds it
recorded, the acts and codes it saw named, and the bodies it saw named.

Nothing here reads a section's text. The counts come from the rows written
when the section was indexed, so a chapter answers in one pass.
"""

import re

FAMILIES = ('term', 'note', 'act', 'body')

LEAVES = 400

_CODE_NAME = re.compile(r'(?i)\b(?:code|act|law|constitution)\s*$')


def _placed(rows):
    """One count map per citation, from `(citation, word, count)` rows."""
    found = {}
    for citation, word, many in rows:
        if not citation or not word:
            continue
        held = found.setdefault(citation, {})
        held[word] = held.get(word, 0) + many
    return found


def _ask(db, sql, citations, *more):
    """One query over a list of citations, in batches SQLite will take."""
    rows = []
    listed = list(citations)
    for start in range(0, len(listed), 400):
        batch = listed[start:start + 400]
        marks = ','.join('?' * len(batch))
        rows.extend(db.execute(sql % marks, list(batch) + list(more)).fetchall())
    return rows


def counts(citations):
    """The four families, keyed by citation.

    ``term`` is the surface word a needle class matched. ``note`` is the
    annotation kind. ``act`` and ``body`` are the names the index printed: a
    name that ends in code, act, law, or constitution is an act, and the rest
    are bodies.
    """
    from indexer import Indexer
    listed = [one for one in citations if one]
    empty = {one: {family: {} for family in FAMILIES} for one in listed}
    if not listed:
        return empty
    idxer = Indexer()
    db = idxer._needle_db()
    try:
        # Each ask is by citation, and says so: left to choose, SQLite took
        # the note index for the third and read every case and named act in
        # the store — two seconds — to answer for a few hundred sections.
        terms = _placed(_ask(
            db,
            'SELECT citation, form, COUNT(*) FROM needle INDEXED BY needle_citation '
            'WHERE citation IN (%s) GROUP BY citation, form',
            listed,
        ))
        notes = _placed(_ask(
            db,
            'SELECT citation, note, COUNT(*) FROM annotation INDEXED BY annotation_citation '
            "WHERE citation IN (%s) AND note NOT IN ('case', 'named_act') GROUP BY citation, note",
            listed,
        ))
        named = _ask(
            db,
            'SELECT citation, text, COUNT(*) FROM annotation INDEXED BY annotation_citation '
            "WHERE citation IN (%s) AND note IN ('case', 'named_act') AND text != '' GROUP BY citation, text",
            listed,
        )
    finally:
        db.close()
    acts = {}
    bodies = {}
    for citation, text, many in named:
        words = (text or '').strip()
        if not words:
            continue
        where = acts if _CODE_NAME.search(words) else bodies
        held = where.setdefault(citation, {})
        held[words] = held.get(words, 0) + many
    for one in listed:
        empty[one] = {
            'term': terms.get(one, {}),
            'note': notes.get(one, {}),
            'act': acts.get(one, {}),
            'body': bodies.get(one, {}),
        }
    return empty


_HEADING_UNIT = re.compile(
    r'(?i)^(?P<unit>division|title|part|chapter|article)\s+(?P<number>[0-9]+(?:\.[0-9]+)*[A-Za-z]?)'
)


def _rungs(doc):
    """The ladder this section sits in, each rung named by its own caption.

    A caption says which unit it is, so ``TITLE 5. HIRING`` names the title
    rung even where the index filed that caption on another field. A rung no
    caption names keeps its unit and number.
    """
    import query
    rungs = query._units_from_doc(doc)
    captions = {}
    for rung in rungs:
        matched = _HEADING_UNIT.match(rung['heading'] or '')
        if matched is not None:
            captions[(matched.group('unit').lower(), matched.group('number'))] = rung['heading']
    return [
        (
            rung['level'],
            rung['value'],
            captions.get(
                (rung['level'], rung['value']),
                '%s %s' % (rung['level'].title(), rung['value']),
            ),
        )
        for rung in rungs
    ]


def _nest(rows, code, title):
    """The sections as the heading tree they hang from."""
    root = {'id': code, 'unit': 'code', 'label': title or code, 'children': []}
    seats = {code: root}
    for doc, rungs in rows:
        here = root
        trail = [code]
        for level, value, caption in rungs:
            trail.append('%s%s' % (level[:1], value))
            key = '/'.join(trail)
            seat = seats.get(key)
            if seat is None:
                seat = {'id': key, 'unit': level, 'label': caption, 'children': []}
                seats[key] = seat
                here['children'].append(seat)
            here = seat
        number = doc.get('SECTION_NUM') or ''
        here['children'].append({
            'id': '%s %s' % (code, number),
            'unit': 'section',
            'label': number,
            'code': code,
            'num': number,
            'children': [],
        })
    return root


def books(words, most=240):
    """Which codes use each word, across the whole index.

    A cloud is scoped to one heading, so every section in it shares a code.
    What makes a word point somewhere is the company it keeps in the rest of
    the library, which is this. ``words`` is `(family, word)` pairs.
    """
    from indexer import Indexer
    wanted = list(words)[:most]
    found = {}
    if not wanted:
        return found
    terms = [word for family, word in wanted if family == 'term']
    # One name can be asked for as an act and as a body, and the index keeps
    # both under the same row, so the families a name was asked under decide
    # which keys its codes land on.
    families = {}
    for family, word in wanted:
        if family in ('act', 'body'):
            families.setdefault(word, set()).add(family)
    named = list(families)
    db = Indexer()._needle_db()
    try:
        for word, code, many in _ask(
            db,
            'SELECT form, code, COUNT(*) FROM needle WHERE form IN (%s) GROUP BY form, code',
            terms,
        ):
            held = found.setdefault('term|%s' % word, {})
            held[code] = held.get(code, 0) + many
        for word, code, many in _ask(
            db,
            'SELECT text, code, COUNT(*) FROM annotation WHERE text IN (%s) '
            "AND note IN ('case', 'named_act') GROUP BY text, code",
            named,
        ):
            for family in families.get(word) or ():
                held = found.setdefault('%s|%s' % (family, word), {})
                held[code] = held.get(code, 0) + many
        for note, code, many in _ask(
            db,
            'SELECT note, code, COUNT(*) FROM annotation WHERE note IN (%s) GROUP BY note, code',
            [word for family, word in wanted if family == 'note'],
        ):
            held = found.setdefault('note|%s' % note, {})
            held[code] = held.get(code, 0) + many
    finally:
        db.close()
    return found


def scope(url, limit=LEAVES):
    """One node of the library, the sections under it, and their words.

    ``url`` is a tree path, the same one ``query.law_tree`` reads. A scope
    wider than ``limit`` sections is cut to the first ones in statutory order,
    and ``more`` says how many were left out.
    """
    import query
    from core import open_index
    path = query.parse_law_url(url)
    if not path.code:
        return {'found': False, 'reason': 'not_in_index', 'expression': url or ''}
    idxer = query._indexer()
    if not query._index_ready(idxer):
        return {'found': False, 'reason': 'not_in_index', 'expression': url or ''}
    code = query._resolve_known_code(idxer, path.code)
    if code is None:
        return {'found': False, 'reason': 'unknown_code', 'expression': url or ''}
    opened = open_index(idxer.idx_path)
    with opened.searcher() as searcher:
        hits = searcher.search(query._constraints(path), limit=None)
        docs = [dict(hit) for hit in hits]
    docs.sort(key=lambda doc: query.section_key(doc.get('SECTION_NUM')))
    more = max(0, len(docs) - limit)
    docs = docs[:limit]
    if not docs:
        return {'found': False, 'reason': 'not_in_index', 'expression': url or ''}
    titles = {row['code']: row['title'] for row in idxer.list_codes()}
    rows = [(doc, _rungs(doc)) for doc in docs]
    tree = _nest(rows, code, titles.get(code, code))
    numbers = [doc.get('SECTION_NUM') or '' for doc in docs]
    marked = counts(['%s %s' % (code, number) for number in numbers])
    leaves = [
        {
            'id': '%s %s' % (code, number),
            'code': code,
            'num': number,
            'counts': marked.get('%s %s' % (code, number), {}),
        }
        for number in numbers
    ]
    seen = {}
    for leaf in leaves:
        for family, counted in leaf['counts'].items():
            for word, many in counted.items():
                key = (family, word)
                seen[key] = seen.get(key, 0) + many
    ranked = [pair for pair, _many in sorted(seen.items(), key=lambda row: -row[1])]
    return {
        'found': True,
        'books': books(ranked),
        'url': path.url,
        'code': code,
        'tree': tree,
        'leaves': leaves,
        'more': more,
        'codes': titles,
    }
