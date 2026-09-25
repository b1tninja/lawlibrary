"""Draw a few sections from one book so a parser can be developed against real wording.

A statute is a code in the Whoosh index. A regulation is one CFR title file.
A court rule is a pointer until its words are indexed. The same seed returns
the same sections.
"""

import os
import random

from whoosh import index
from whoosh.qparser import QueryParser
from whoosh.query import And, Term

from corpus import connect, cfr_corpus_path, manual_corpus_path
from court import courts
from entities import list_corpora
from indexer import Indexer
from publication import Instrument
import query as law_query


_LIMIT = 20


def _indexer(indexer):
    return Indexer() if indexer is None else indexer


def _books(idxer):
    if not index.exists_in(idxer.idx_path):
        return []
    return idxer.list_codes()


def sources(indexer=None, root=None):
    """Books an agent can select.

    kind is statute, regulation, or rule. present is true when the words are
    already on disk. A rule row names the page; its words are not downloaded.
    """
    idxer = _indexer(indexer)
    rows = []
    for item in _books(idxer):
        rows.append({
            'kind': Instrument.STATUTE.value,
            'book': item['code'],
            'title': item['title'],
            'present': True,
        })
    for item in list_corpora(root):
        if item['instrument'] == Instrument.MANUAL.value:
            book = item['schema'].split('_', 1)[-1].upper()
            rows.append({
                'kind': Instrument.MANUAL.value,
                'book': book,
                'title': book,
                'present': item['present'],
                'schema': item['schema'],
            })
            continue
        if item['instrument'] != Instrument.REGULATION.value:
            continue
        title = item['schema'].split('_', 1)[-1]
        rows.append({
            'kind': Instrument.REGULATION.value,
            'book': title,
            'title': 'Code of Federal Regulations title %s' % title,
            'present': item['present'],
            'schema': item['schema'],
        })
    seen = set()
    for court in courts():
        for book in court.rules:
            key = book.url
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                'kind': Instrument.RULE.value,
                'book': court.__name__,
                'title': book.title,
                'present': False,
                'url': book.url,
                'shape': book.shape,
            })
    return rows


def _miss(reason, **extra):
    row = {'found': False, 'reason': reason, 'sections': []}
    row.update(extra)
    return row


def _payload(doc):
    row = law_query._section_payload(doc)
    row.pop('found', None)
    return row


def _draw_statute(idxer, code, n, seed, pattern):
    if not index.exists_in(idxer.idx_path):
        return _miss('index_absent', kind=Instrument.STATUTE.value, book=code)
    known = {item['code']: item['title'] for item in idxer.list_codes()}
    resolved = idxer._resolve_code(code)
    if resolved not in known:
        return _miss('unknown_book', kind=Instrument.STATUTE.value, book=code)
    session = law_query._session_value(idxer, None)
    idx = index.open_dir(idxer.idx_path)
    with idx.searcher() as searcher:
        if pattern:
            parsed = QueryParser('LEGAL_TEXT', idx.schema).parse(pattern)
            query = And([Term('LAW_CODE', resolved), parsed])
            docnums = [hit.docnum for hit in searcher.search(query, limit=200)]
        else:
            docnums = []
            for docnum in searcher.document_numbers(LAW_CODE=resolved):
                fields = searcher.stored_fields(docnum)
                if fields.get('ACTIVE_FLG') is False:
                    continue
                if session not in (None, 'all') and fields.get('SESSION') not in (None, session):
                    continue
                docnums.append(docnum)
        if not docnums:
            return _miss('no_match', kind=Instrument.STATUTE.value, book=resolved, title=known[resolved])
        rng = random.Random(seed)
        picked = docnums if len(docnums) <= n else rng.sample(docnums, n)
        picked.sort()
        sections = [_payload(searcher.stored_fields(docnum)) for docnum in picked]
    return {
        'found': True,
        'kind': Instrument.STATUTE.value,
        'book': resolved,
        'title': known[resolved],
        'seed': seed,
        'sections': sections,
    }


def _draw_regulation(book, n, seed, root):
    path = cfr_corpus_path(book, root=root)
    title = 'Code of Federal Regulations title %s' % book
    if not os.path.isfile(path):
        return _miss('not_in_index', kind=Instrument.REGULATION.value, book=str(book), title=title)
    return _draw_rows(path, Instrument.REGULATION.value, str(book), title, n, seed)


def _draw_manual(book, n, seed, root):
    from us.manuals import Manuals

    token = str(book).strip().upper()
    catalog = {parser.code: parser for parser in Manuals.editions}
    pointers = {item['book']: item for item in Manuals.pointers}
    if token in pointers:
        item = pointers[token]
        return _miss(
            'not_indexed',
            kind=Instrument.MANUAL.value,
            book=token,
            title=item['title'],
            url=item['url'],
            shape=item['shape'],
        )
    parser = catalog.get(token)
    if parser is None:
        return _miss('unknown_book', kind=Instrument.MANUAL.value, book=token)
    path = manual_corpus_path(token, root=root)
    if not os.path.isfile(path):
        return _miss(
            'not_in_index',
            kind=Instrument.MANUAL.value,
            book=token,
            title=parser.code,
            url=parser.source,
            shape=parser.shape,
        )
    return _draw_rows(path, Instrument.MANUAL.value, token, parser.code, n, seed)


def _draw_rows(path, kind, book, title, n, seed):
    db = connect(path)
    try:
        rows = db.execute('SELECT pk, law_code, section_num, citation FROM section').fetchall()
        if not rows:
            return _miss('no_match', kind=kind, book=book, title=title)
        rng = random.Random(seed)
        chosen = rows if len(rows) <= n else rng.sample(rows, n)
        sections = []
        for pk, law_code, number, citation in chosen:
            text = db.execute('SELECT legal_text FROM section WHERE pk = ?', (pk,)).fetchone()
            sections.append({
                'citation': citation or '%s %s' % (law_code, number),
                'code': law_code,
                'section': number,
                'text': text[0] if text else '',
            })
    finally:
        db.close()
    return {
        'found': True,
        'kind': kind,
        'book': book,
        'title': title,
        'seed': seed,
        'sections': sections,
    }


def _draw_rule(book):
    for row in sources():
        if row['kind'] == Instrument.RULE.value and row['book'] == book:
            return _miss(
                'not_indexed',
                kind=Instrument.RULE.value,
                book=book,
                title=row['title'],
                url=row['url'],
                shape=row['shape'],
            )
    return _miss('unknown_book', kind=Instrument.RULE.value, book=book)


def sample(book, n=3, seed=None, kind=None, pattern=None, indexer=None, root=None):
    """Return up to n sections from one book.

    book is a code abbreviation, a CFR title number, or a court class name.
    pattern keeps statute sections whose text matches that query. n is at most 20.
    """
    if not book:
        return _miss('unknown_book', book='')
    count = max(1, min(int(n or 3), _LIMIT))
    chosen = seed if seed not in (None, '') else random.SystemRandom().randrange(2 ** 31)
    shelf = (kind or '').strip().lower()
    token = getattr(book, 'value', None)
    token = token if isinstance(token, str) else str(book).strip()
    if shelf == Instrument.REGULATION.value or (not shelf and token.isdigit()):
        return _draw_regulation(token, count, chosen, root)
    if shelf == Instrument.MANUAL.value or token.upper() in ('OLRC', 'HOLC', 'GPO', 'GPO-2016', 'HOLC-2022', 'CSM'):
        return _draw_manual(token, count, chosen, root)
    if shelf == Instrument.RULE.value:
        return _draw_rule(token)
    return _draw_statute(_indexer(indexer), token, count, chosen, pattern)


class Draw:
    """One book to sample. ``take``, ``seed``, and ``matching`` close over it.

    ``Draw(Code.CIVIL).take(20).seed(1).matching('subdivision').choose()``
    """

    def __init__(self, book, n=3, seed=None, kind=None, pattern=None, root=None):
        self.book = getattr(book, 'value', book)
        self.count = n
        self._seed = seed
        self._kind = kind
        self.pattern = pattern
        self.root = root

    def _copy(self, **changed):
        fields = {
            'book': self.book,
            'n': self.count,
            'seed': self._seed,
            'kind': self._kind,
            'pattern': self.pattern,
            'root': self.root,
        }
        fields.update(changed)
        return Draw(**fields)

    def take(self, n):
        return self._copy(n=n)

    def seed(self, seed):
        return self._copy(seed=seed)

    def kind(self, kind):
        return self._copy(kind=kind)

    def matching(self, pattern):
        return self._copy(pattern=pattern)

    def choose(self):
        """The sampled sections. ``draw`` stays free for a graph."""
        return sample(
            self.book,
            n=self.count,
            seed=self._seed,
            kind=self._kind,
            pattern=self.pattern,
            root=self.root,
        )

    def citations(self):
        """The citations in this draw. The list can be sliced."""
        from apa import Code
        from places import Citation
        found = []
        for row in self.choose().get('sections') or []:
            try:
                code = Code.get(row.get('code'))
            except KeyError:
                found.append(row)
                continue
            found.append(Citation(code).section(row.get('section')))
        return found

    def __iter__(self):
        return iter(self.citations())

    def __call__(self):
        return self.choose()
