"""The ledger: how often each word appears at each place in the index.

A count by heading used to mean a walk of the whole lexicon, held in memory,
once per process, over every edition at once. The lexicon of the Whoosh index
is 68 million postings; the walk took five minutes single-threaded, and the
counts it kept — one row per word per member per scope — did not fit in
memory once the members were chapters, let alone nodes. This module keeps
the count on disk and builds it in parallel.

A **place** is one leaf of the publisher's tree: the node a section hangs
from (``TOC_PATH``), or, in an index built before the trail was stored, one
cell of the ladder (division, title, part, chapter, article). A section sits
at exactly one place, so a word's count at a place is counted once, and a
**scope** — a code, a chapter, a node and everything under it, a state — is
a set of places. Counting a scope is a sum over its places; nothing is
counted twice and nothing is stored per scope.

The ledger is built once per index generation, over the newest edition only
(a section the state has published in nineteen editions is one section), in
two parallel phases: the places are read from the stored fields in document
slices, and the lexicon is walked in term ranges, each worker holding the
map from document to place. The result is ``ledger-<generation>.sqlite``
beside the index. A reader opens the one for the current generation and
builds it when it is missing. See docs/tree.md, Aggregates.
"""

import os
import pathlib
import sqlite3
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from whoosh import index

from core import index_ready, index_root, open_index

SCOPES = ('code', 'division', 'chapter', 'article', 'node', 'state', 'federal')

_LADDER = ('DIVISION', 'TITLE', 'PART', 'CHAPTER', 'ARTICLE')
_FIELD = 'LEGAL_TEXT'
_SMALL = 2000
_BATCH = 400


def keep(term):
    """The word a term counts as, or None for one that is not a word.

    A term shorter than three letters is not kept, and neither is one that
    opens with a digit: ``1798.110`` and ``2924g`` are section numbers the
    text cites, and a rank that leads with them says only that the section
    is cited nearby.
    """
    word = term.decode('utf-8') if isinstance(term, bytes) else term
    if len(word) < 3 or word[:1].isdigit():
        return None
    return word


def newest_session(reader):
    """The newest edition the index holds, or None when none is stamped."""
    if 'SESSION' not in reader.schema.names():
        return None
    years = sorted(term.decode() for term in reader.lexicon('SESSION'))
    return years[-1] if years else None


# --- phase one: where each section sits -----------------------------------

def _seat(fields):
    """The place a section sits: code, path, ladder numbers, and subdivision."""
    return (
        fields.get('LAW_CODE') or '',
        fields.get('TOC_PATH') or '',
        tuple((fields.get(name) or '').strip() for name in _LADDER),
        (fields.get('SUBDIVISION') or '').strip(),
    )


def _seat_slice(path, docnums):
    """One slice of documents, each with its seat. Runs in a worker."""
    ix = open_index(path)
    found = []
    with ix.searcher() as searcher:
        for docnum in docnums:
            found.append((docnum, _seat(searcher.stored_fields(docnum))))
    return found


def _scope_keys(seat, place_id):
    """The member of each scope a place belongs to, in SCOPES order.

    ``node`` is the place itself, and only where the publisher's path is
    stored; ``division``, ``chapter`` and ``article`` are the code and the
    number, so every Chapter 2 of a code is one member there.
    """
    code, path, ladder, subdivision = seat
    division, _title, _part, chapter, article = ladder
    return (
        code or None,
        ('%s %s' % (code, division)) if code and division else None,
        ('%s %s' % (code, chapter)) if code and chapter else None,
        ('%s %s' % (code, article)) if code and article else None,
        place_id if code and path else None,
        subdivision if subdivision.startswith('US-') else None,
        'US' if subdivision == 'US' else None,
    )


# --- phase two: the walk ---------------------------------------------------

_PATH = None
_SEATS = None
_KEYS = None


def _boot(path, seats, keys):
    """Give a worker the index path and the seat of every counted document."""
    global _PATH, _SEATS, _KEYS
    _PATH = path
    _SEATS = seats
    _KEYS = keys


def _walk(bounds):
    """Count one range of the lexicon. Runs in a worker.

    Returns the tally rows ``(place, term, tf)`` and, for each scope, how
    many members the term reached ``(scope, term, df)``. Every posting of a
    term is seen here, so the document frequency is exact.
    """
    start, stop = bounds
    ix = open_index(_PATH)
    tallies = []
    frequencies = []
    with ix.searcher() as searcher:
        reader = searcher.reader()
        for (fieldname, raw), _info in reader.iter_from(_FIELD, start):
            if fieldname != _FIELD or (stop is not None and raw >= stop):
                break
            term = keep(raw)
            if term is None:
                continue
            counts = {}
            postings = reader.postings(_FIELD, raw)
            while postings.is_active():
                place = _SEATS.get(postings.id())
                if place is not None:
                    counts[place] = counts.get(place, 0) + postings.weight()
                postings.next()
            if not counts:
                continue
            reached = [set() for _scope in SCOPES]
            for place, weight in counts.items():
                tallies.append((place, term, int(round(weight))))
                for slot, key in enumerate(_KEYS[place]):
                    if key is not None:
                        reached[slot].add(key)
            for slot, scope in enumerate(SCOPES):
                if reached[slot]:
                    frequencies.append((scope, term, len(reached[slot])))
    return tallies, frequencies


def _bounds(reader, pieces):
    """Split the lexicon into ``pieces`` ranges of about equal term count."""
    terms = [raw for raw in reader.lexicon(_FIELD)]
    if not terms:
        return []
    step = max(1, len(terms) // max(1, pieces))
    starts = terms[::step]
    return [(starts[i], starts[i + 1] if i + 1 < len(starts) else None) for i in range(len(starts))]


def _chunks(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


# --- the build ---------------------------------------------------------------

def ledger_path(root, generation):
    return os.path.join(str(root), 'ledger-%d.sqlite' % generation)


def build(root=None, workers=None, log=None):
    """Write the ledger for the index's current generation. Returns its path.

    ``workers`` defaults to every processor. An index small enough to count
    in a moment is counted in this process.
    """
    root = str(root or index_root())
    ix = open_index(root)
    generation = ix.latest_generation()
    final = ledger_path(root, generation)
    started = time.time()
    say = log or (lambda *_words: None)
    with ix.searcher() as searcher:
        reader = searcher.reader()
        session = newest_session(reader)
        if session is None:
            docnums = list(range(reader.doc_count()))
        else:
            docnums = list(searcher.document_numbers(SESSION=session))
        workers = max(1, workers or os.cpu_count() or 1)
        inline = len(docnums) < _SMALL or workers == 1
        pieces = 1 if inline else workers * 4
        ranges = _bounds(reader, pieces)
    say('ledger: %d sections of edition %s, %d workers' % (len(docnums), session, 1 if inline else workers))

    # Phase one: seats.
    seats = {}
    places = {}
    keys = []
    rows = []

    def seat_rows(found):
        for docnum, seat in found:
            place = places.get(seat)
            if place is None:
                place = places[seat] = len(keys)
                keys.append(_scope_keys(seat, place))
                rows.append((place,) + (seat[0], seat[1]) + seat[2] + (seat[3],))
            seats[docnum] = place

    if inline:
        seat_rows(_seat_slice(root, docnums))
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for found in pool.map(_seat_slice, [root] * ((len(docnums) + 4999) // 5000),
                                  list(_chunks(docnums, 5000))):
                seat_rows(found)
    say('ledger: %d places in %.1fs' % (len(places), time.time() - started))

    # Phase two: the walk, into a fresh file.
    tmp = '%s.%d.tmp' % (final, os.getpid())
    if os.path.exists(tmp):
        os.remove(tmp)
    db = sqlite3.connect(tmp)
    db.execute('PRAGMA journal_mode=OFF')
    db.execute('PRAGMA synchronous=OFF')
    db.execute('CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)')
    db.execute(
        'CREATE TABLE place (id INTEGER PRIMARY KEY, code TEXT, path TEXT, '
        'division TEXT, title TEXT, part TEXT, chapter TEXT, article TEXT, subdivision TEXT, sections INTEGER)'
    )
    db.execute('CREATE TABLE tally (place INTEGER, term TEXT, tf INTEGER, PRIMARY KEY (place, term)) WITHOUT ROWID')
    db.execute('CREATE TABLE df (scope TEXT, term TEXT, df INTEGER, PRIMARY KEY (scope, term)) WITHOUT ROWID')
    held = {}
    for place in seats.values():
        held[place] = held.get(place, 0) + 1
    db.executemany('INSERT INTO place VALUES (?,?,?,?,?,?,?,?,?,?)', [row + (held.get(row[0], 0),) for row in rows])

    counted = 0
    if inline:
        _boot(root, seats, keys)
        for bounds in ranges:
            tallies, frequencies = _walk(bounds)
            db.executemany('INSERT INTO tally VALUES (?,?,?)', tallies)
            db.executemany('INSERT INTO df VALUES (?,?,?)', frequencies)
            counted += len(tallies)
    else:
        with ProcessPoolExecutor(max_workers=workers, initializer=_boot, initargs=(root, seats, keys)) as pool:
            jobs = [pool.submit(_walk, bounds) for bounds in ranges]
            for job in as_completed(jobs):
                tallies, frequencies = job.result()
                db.executemany('INSERT INTO tally VALUES (?,?,?)', tallies)
                db.executemany('INSERT INTO df VALUES (?,?,?)', frequencies)
                counted += len(tallies)
    members = {scope: len({key[slot] for key in keys if key[slot] is not None}) for slot, scope in enumerate(SCOPES)}
    meta = {
        'index': root, 'generation': str(generation), 'session': session or '',
        'sections': str(len(seats)), 'places': str(len(places)), 'rows': str(counted),
        'workers': str(1 if inline else workers), 'seconds': '%.1f' % (time.time() - started),
    }
    meta.update(('n:%s' % scope, str(many)) for scope, many in members.items())
    db.executemany('INSERT INTO meta VALUES (?,?)', list(meta.items()))
    db.commit()
    db.close()
    os.replace(tmp, final)
    say('ledger: %s rows at %d places in %.1fs -> %s' % (counted, len(places), time.time() - started, final))
    _sweep(root, final)
    return final


def _sweep(root, final):
    """Drop the ledgers of earlier generations. A file still open is left."""
    for name in os.listdir(root):
        if name.startswith('ledger-') and name.endswith('.sqlite') and os.path.join(root, name) != final:
            try:
                os.remove(os.path.join(root, name))
            except OSError:
                pass


# --- the read ----------------------------------------------------------------

class Ledger:
    """The counts for one index generation. Opened read-only."""

    def __init__(self, root, generation, path):
        self.root = root
        self.generation = generation
        self.path = path
        self.db = sqlite3.connect('%s?mode=ro' % pathlib.Path(path).resolve().as_uri(), uri=True, timeout=30)
        self.meta = dict(self.db.execute('SELECT key, value FROM meta'))
        self.session = self.meta.get('session') or None
        self._places = None

    def n(self, scope):
        """How many members ``scope`` has: the denominator of a document frequency."""
        return int(self.meta.get('n:%s' % scope) or 0)

    def _seated(self):
        if self._places is None:
            self._places = self.db.execute(
                'SELECT id, code, path, division, chapter, article, subdivision FROM place'
            ).fetchall()
        return self._places

    def places(self, scope, key):
        """The places one member of ``scope`` covers. Empty for a member the index lacks.

        ``node`` takes ``CIV 6.8`` and covers the node and every node under
        it — the path is a prefix. ``division``, ``chapter`` and ``article``
        take the code and the number. ``state`` takes ``US-CA``; ``federal``
        takes ``US``.
        """
        key = str(key or '').strip()
        if not key:
            return []
        rows = self._seated()
        if scope == 'code':
            return [row[0] for row in rows if row[1] == key]
        if scope in ('division', 'chapter', 'article'):
            code, _space, number = key.partition(' ')
            slot = {'division': 3, 'chapter': 4, 'article': 5}[scope]
            return [row[0] for row in rows if row[1] == code and row[slot] == number and number]
        if scope == 'node':
            code, _space, path = key.partition(' ')
            if not path:
                return []
            under = path + '.'
            return [row[0] for row in rows if row[1] == code and (row[2] == path or row[2].startswith(under))]
        if scope == 'state':
            return [row[0] for row in rows if row[6] == key and key.startswith('US-')]
        if scope == 'federal':
            return [row[0] for row in rows if row[6] == 'US' and key == 'US']
        return []

    def tally(self, places):
        """Each term's count summed over ``places``."""
        found = {}
        for batch in _chunks(list(places), _BATCH):
            marks = ','.join('?' * len(batch))
            for term, tf in self.db.execute(
                'SELECT term, SUM(tf) FROM tally WHERE place IN (%s) GROUP BY term' % marks, batch,
            ):
                found[term] = found.get(term, 0) + tf
        return found

    def df(self, scope, terms):
        """How many members of ``scope`` each term reached."""
        found = {}
        for batch in _chunks(list(terms), _BATCH):
            marks = ','.join('?' * len(batch))
            for term, df in self.db.execute(
                'SELECT term, df FROM df WHERE scope = ? AND term IN (%s)' % marks, [scope] + batch,
            ):
                found[term] = df
        return found

    def close(self):
        self.db.close()


_OPEN = {}
_LOCK = threading.Lock()


def open_ledger(root=None, workers=None, log=None):
    """The ledger for the index's current generation, built if it is missing.

    None when there is no index. One ledger is kept open per index path; a
    new generation closes it and opens the new one. Two threads asking at
    once build once.
    """
    root = str(root or index_root())
    if not index_ready(root):
        return None
    generation = open_index(root).latest_generation()
    with _LOCK:
        held = _OPEN.get(root)
        if held is not None and held.generation == generation and os.path.exists(held.path):
            return held
        path = ledger_path(root, generation)
        if held is not None:
            # Let go of the old generation first: the build sweeps its file,
            # and a file this process still holds open cannot be removed.
            held.close()
            _OPEN.pop(root, None)
        if not os.path.exists(path):
            build(root, workers=workers, log=log)
        book = _OPEN[root] = Ledger(root, generation, path)
        return book


def main(argv=None):
    """``python ledger.py [--workers N] [--root DIR]``: build the ledger and say how long it took."""
    import argparse
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('--workers', type=int, default=None)
    parser.add_argument('--root', default=None)
    args = parser.parse_args(argv)
    build(args.root, workers=args.workers, log=lambda words: print(words, flush=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
