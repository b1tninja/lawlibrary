import json
import logging
import os
import os.path
import re
import shutil
from enum import Enum, auto

from whoosh import highlight, index
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import SchemaClass, ID, TEXT, NUMERIC, DATETIME, BOOLEAN
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.query import And, Term
from whoosh.reading import TermNotFound

import sqlite3

from core import index_dir
from needles import occurrences
from utils import mkdir
from vesting import grants

def _index_base() -> str:
    return str(index_dir())


WHOOSH_INDEX_BASEDIR = _index_base()
logger = logging.getLogger('indexer')


def _plain_section(fields):
    """The stored fields a worker can parse. The searcher is not sent across."""
    return {
        'CITATION': fields.get('CITATION') or '',
        'LAW_CODE': fields.get('LAW_CODE') or '',
        'LEGAL_TEXT': fields.get('LEGAL_TEXT') or '',
        'SECTION_HISTORY': fields.get('SECTION_HISTORY') or fields.get('HISTORY') or '',
        'SHELF': fields.get('SHELF'),
    }


def _term_rows(doc, shelf=None):
    """Needle and edge tuples for one section. No database and no annotations."""
    citation = doc.get('CITATION') or ''
    code = doc.get('LAW_CODE') or ''
    text = doc.get('LEGAL_TEXT') or ''
    shelf = doc.get('SHELF') if shelf is None else shelf
    hits = occurrences(text, code, shelf)
    needles = [
        (citation, code, hit['class'], hit['form'], hit['start'], hit['end'])
        for hit in hits
    ]
    edges = []
    if any(hit['class'] == 'Vesting' for hit in hits):
        for grant in grants(text):
            if grant.prior and grant.receiver:
                edges.append((citation, code, 'vesting', grant.prior, grant.receiver))
    from structure import find_links
    for link in find_links(text, here=code or None):
        if link.kind == 'statute' and link.section and link.code is not None:
            token = getattr(link.code, 'value', link.code)
            edges.append((citation, code, 'citation', citation, '%s %s' % (token, link.section)))
        elif link.kind == 'article' and link.section:
            edges.append((
                citation, code, 'article', citation,
                'CONS %s %s' % (link.label or '', link.section),
            ))
    return needles, list(dict.fromkeys(edges))


def _annotation_rows(doc):
    """Annotation tuples for one section. No database and no needle forms."""
    citation = doc.get('CITATION') or ''
    code = doc.get('LAW_CODE') or ''
    text = doc.get('LEGAL_TEXT') or ''
    from citations import Note, annotate, find_durations
    notes = [_annotation_tuple(citation, code, note) for note in annotate(text)]
    history = doc.get('SECTION_HISTORY') or ''
    if history:
        for note in annotate(history):
            if note.note is not Note.SESSION:
                continue
            cite = note.cite.value if note.cite is not None else None
            join = note.join.value if note.join is not None else None
            notes.append((citation, code, note.note.value, note.text, note.target, None, None, cite, join))
    for period in find_durations(text):
        if period.antecedent:
            notes.append((
                citation, code, 'antecedent', period.reference(), period.antecedent, None, None,
                None, None,
            ))
    return notes


def _annotation_tuple(citation, code, note):
    """One annotation row. ``cite`` and ``join`` are empty when the note has neither."""
    cite = note.cite.value if getattr(note, 'cite', None) is not None else None
    join = note.join.value if getattr(note, 'join', None) is not None else None
    return (
        citation, code, note.note.value, note.text, note.target,
        note.start, note.end, cite, join,
    )


def _needle_rows(doc, shelf=None):
    """Needle, edge, and annotation tuples for one section. No database."""
    needles, edges = _term_rows(doc, shelf)
    return needles, edges, _annotation_rows(doc)

_ANALYZER = StemmingAnalyzer()
_CITATION = re.compile(
    r"""(?ix)
    ^\s*
    (?:section\s+)?
    (?P<code>[a-z][a-z .]{1,40}?)
    \s+
    (?:section\s+|§\s*)?
    (?P<section>\d[\d.]*(?:[a-z])?)
    \s*$
    """
)


# Home corpus: newest session of California state statutes.
DEFAULT_COUNTRY = 'US'
DEFAULT_SUBDIVISION = 'US-CA'


class LawSchema(SchemaClass):
    PK = ID(unique=True, stored=True)
    ACTIVE_FLG = BOOLEAN(stored=True)
    ARTICLE = ID(stored=True)
    ARTICLE_HEADING = TEXT(stored=True, analyzer=_ANALYZER)
    ARTICLE_HISTORY = TEXT(stored=True)
    CHAPTER = ID(stored=True)
    CHAPTER_HEADING = TEXT(stored=True, analyzer=_ANALYZER)
    CODE_HEADING = TEXT(stored=True, analyzer=_ANALYZER)
    CITATION = ID(stored=True)
    COUNTRY = ID(stored=True)
    SESSION = ID(stored=True)
    SUBDIVISION = ID(stored=True)
    LOCALITY = ID(stored=True)
    DIVISION = ID(stored=True)
    DIVISION_HEADING = TEXT(stored=True, analyzer=_ANALYZER)
    EFFECTIVE_DATE = DATETIME(stored=True)
    HISTORY = TEXT(stored=True)
    LAW_CODE = ID(stored=True)
    LAW_SECTION_VERSION_ID = ID(stored=True)
    LEGAL_TEXT = TEXT(stored=True, analyzer=_ANALYZER, phrase=True)
    LOB_FILE = ID(stored=True)
    OP_CHAPTER = ID()
    OP_SECTION = ID()
    OP_STATUES = ID()
    PART = ID(stored=True)
    PART_HEADING = TEXT(stored=True, analyzer=_ANALYZER)
    SECTION_HISTORY = TEXT(stored=True)
    SECTION_NUM = ID(stored=True)
    SECTION_TITLE = TEXT(stored=True, analyzer=_ANALYZER)
    TITLE = ID(stored=True)
    TITLE_HEADING = TEXT(stored=True, analyzer=_ANALYZER)
    TRANS_UID = ID()
    TRANS_UPDATE = DATETIME(stored=True)


class IndexState(Enum):
    Unknown = auto()
    Created = auto()
    Initialize = auto()
    Opening = auto()
    Opened = auto()
    Committed = auto()


_FIELDS = set(LawSchema().names())


def _present(law):
    names = _FIELDS
    doc = {}
    for key, value in law.items():
        if key in names and value is not None and value != '':
            doc[key] = value
    if 'COUNTRY' not in doc and doc.get('SUBDIVISION'):
        doc['COUNTRY'] = doc['SUBDIVISION'].split('-', 1)[0]
    code = doc.get('LAW_CODE') or ''
    section = doc.get('SECTION_NUM') or ''
    if code and section:
        doc['CITATION'] = '%s %s' % (code, section)
    return doc


_CODE_ORDER = (
    'CONS', 'BPC', 'CIV', 'CCP', 'COM', 'CORP', 'EDC', 'ELEC', 'EVID',
    'FAM', 'FIN', 'FGC', 'FAC', 'GOV', 'HNC', 'HSC', 'INS', 'LAB', 'MVC',
    'PEN', 'PROB', 'PCC', 'PRC', 'PUC', 'RTC', 'SHC', 'UIC', 'VEH', 'WAT', 'WIC',
)


def _code_rank(token):
    """The Legislature's code list. An unknown token follows that list."""
    try:
        return _CODE_ORDER.index(str(token or '').strip().upper())
    except ValueError:
        return len(_CODE_ORDER)


class Indexer:
    def __init__(self, basedir=None):
        self.state = IndexState.Unknown
        if basedir is None:
            basedir = _index_base()
        self.idx_path = basedir
        self.codes_path = os.path.join(basedir, 'codes.json')

        if not os.path.exists(basedir):
            self.state = IndexState.Initialize

        mkdir(basedir)

    def reset(self):
        if os.path.isdir(self.idx_path) and index.exists_in(self.idx_path):
            shutil.rmtree(self.idx_path)
        mkdir(self.idx_path)
        self.state = IndexState.Initialize

    def index_pubinfo_laws(self, pubinfo, laws):
        if not index.exists_in(self.idx_path):
            law_idx = index.create_in(self.idx_path, LawSchema)
            self.state = IndexState.Created
        else:
            law_idx = index.open_dir(self.idx_path)
            self.state = IndexState.Opened

        codes = self._read_codes()
        count = 0
        writer = law_idx.writer(limitmb=256)
        needles = self._needle_db()
        try:
            for law in laws:
                doc = _present(law)
                if 'PK' not in doc:
                    continue
                writer.update_document(**doc)
                self._record_needles(needles, doc, law.get('SHELF'))
                code = doc.get('LAW_CODE')
                heading = law.get('CODE_HEADING')
                if code and heading:
                    codes[code] = heading
                count += 1
                if count % 5000 == 0:
                    logger.info("Indexed %s sections from %s", count, os.path.basename(pubinfo))
            writer.commit()
            needles.commit()
            self.state = IndexState.Committed
        except Exception:
            writer.cancel()
            needles.rollback()
            raise
        finally:
            needles.close()
        self._write_codes(codes)
        return count

    def sessions(self, country=None, subdivision=None):
        """Stored chaptering years on the SESSION field. Not a two-year legislative session."""
        if not index.exists_in(self.idx_path):
            return []
        idx = index.open_dir(self.idx_path)
        with idx.searcher() as searcher:
            if country is None and subdivision is None:
                return sorted(term.decode() for term in searcher.lexicon('SESSION'))
            filt = self._region_terms(country, subdivision)
            if not filt:
                return sorted(term.decode() for term in searcher.lexicon('SESSION'))
            query = filt[0] if len(filt) == 1 else And(filt)
            results = searcher.search(query, limit=None)
            found = {hit.get('SESSION') for hit in results if hit.get('SESSION')}
            return sorted(found)

    def search_law(self, q, callback=None, limit=10, active_only=True, session=None,
                   country=None, subdivision=None):
        idx = index.open_dir(self.idx_path)
        with idx.searcher() as searcher:
            parsed = self._parse(q, idx.schema)
            results = searcher.search(
                parsed,
                limit=limit,
                filter=self._filter(active_only, session, country=country, subdivision=subdivision),
            )
            results.fragmenter = highlight.ContextFragmenter(surround=128)
            results.formatter = highlight.UppercaseFormatter()
            if callback is not None:
                callback(results)
            return [self._hit(hit) for hit in results]

    def hunt(self, anchor):
        """Grow a phrase from ``LEGAL_TEXT`` positions until the codes split.

        The query is a phrase on that field. Each hit contributes its term
        vector. The scope slides across ``LAW_CODE``. A missing phrase is none.
        """
        from whoosh.query import Phrase
        from weight import hunt as grow
        tokens = [token.text for token in _ANALYZER(anchor or '')]
        if not tokens or not index.exists_in(self.idx_path):
            return None
        ix = index.open_dir(self.idx_path)
        rows = []
        with ix.searcher() as searcher:
            matcher = Phrase('LEGAL_TEXT', tokens).matcher(searcher)
            while matcher.is_active():
                docnum = matcher.id()
                fields = searcher.stored_fields(docnum)
                if fields.get('ACTIVE_FLG') is False:
                    matcher.next()
                    continue
                text = fields.get('LEGAL_TEXT') or ''
                words = [token.text for token in _ANALYZER(text)]
                rows.append((fields.get('LAW_CODE') or '', words))
                matcher.next()
        if not rows:
            return None
        return grow(rows, ' '.join(tokens))

    def get_section(self, code, section, active_only=True, session=None,
                    country=None, subdivision=None):
        code = self._resolve_code(code)
        section = str(section).rstrip('.')
        idx = index.open_dir(self.idx_path)
        query = And([Term('LAW_CODE', code), Term('SECTION_NUM', section)])
        with idx.searcher() as searcher:
            results = searcher.search(
                query,
                limit=20,
                filter=self._filter(active_only, session, country=country, subdivision=subdivision),
            )
            return [self._section(hit) for hit in results]

    def list_codes(self):
        codes = self._read_codes()
        return [
            {'code': code, 'title': title}
            for code, title in sorted(codes.items(), key=lambda item: (_code_rank(item[0]), item[1]))
        ]

    def _parse(self, q, schema):
        citation = _CITATION.match(q or '')
        if citation:
            code = self._resolve_code(citation.group('code'))
            section = citation.group('section').rstrip('.')
            return And([Term('LAW_CODE', code), Term('SECTION_NUM', section)])
        fields = ['LEGAL_TEXT', 'SECTION_TITLE', 'CODE_HEADING', 'DIVISION_HEADING',
                  'TITLE_HEADING', 'PART_HEADING', 'CHAPTER_HEADING', 'ARTICLE_HEADING']
        return MultifieldParser(fields, schema, group=OrGroup).parse(q)

    def _resolve_code(self, token):
        text = re.sub(r'\s+', ' ', (token or '').strip())
        folded = text.upper().replace('.', '')
        codes = self._read_codes()
        if folded in codes:
            return folded
        titled = folded[:-5].strip() if folded.endswith(' CODE') else folded
        for abbr, title in codes.items():
            name = title.upper()
            # Pubinfo titles look like "Civil Code - CIV".
            base = re.sub(r'\s+-\s+[A-Z0-9]+\s*$', '', name).strip()
            if (
                folded == name
                or folded == base
                or titled == name
                or titled == base
                or titled == base.replace(' CODE', '')
                or titled == abbr
            ):
                return abbr
        return folded

    def _needle_db(self):
        path = os.path.join(self.idx_path, 'needles.sqlite')
        db = sqlite3.connect(path)
        db.execute(
            'CREATE TABLE IF NOT EXISTS needle ('
            'citation TEXT, code TEXT, class TEXT, form TEXT, start INTEGER, end INTEGER)'
        )
        db.execute(
            'CREATE TABLE IF NOT EXISTS edge ('
            'citation TEXT, code TEXT, kind TEXT, prior TEXT, receiver TEXT)'
        )
        columns = [row[1] for row in db.execute('PRAGMA table_info(edge)')]
        if 'kind' not in columns:
            db.execute('ALTER TABLE edge ADD COLUMN kind TEXT')
        db.execute(
            'CREATE TABLE IF NOT EXISTS annotation ('
            'citation TEXT, code TEXT, note TEXT, text TEXT, target TEXT, '
            'start INTEGER, end INTEGER, cite TEXT, join_kind TEXT)'
        )
        columns = [row[1] for row in db.execute('PRAGMA table_info(annotation)')]
        if 'cite' not in columns:
            db.execute('ALTER TABLE annotation ADD COLUMN cite TEXT')
        if 'join_kind' not in columns:
            db.execute('ALTER TABLE annotation ADD COLUMN join_kind TEXT')
        db.execute('CREATE INDEX IF NOT EXISTS needle_code_class ON needle (code, class)')
        db.execute('CREATE INDEX IF NOT EXISTS needle_citation ON needle (citation)')
        db.execute('CREATE INDEX IF NOT EXISTS edge_kind_code ON edge (kind, code)')
        db.execute('CREATE INDEX IF NOT EXISTS edge_citation ON edge (citation)')
        db.execute('CREATE INDEX IF NOT EXISTS edge_prior ON edge (kind, prior)')
        db.execute('CREATE INDEX IF NOT EXISTS annotation_note_code ON annotation (note, code)')
        db.execute('CREATE INDEX IF NOT EXISTS annotation_note_target ON annotation (note, target)')
        db.execute('CREATE INDEX IF NOT EXISTS annotation_citation ON annotation (citation)')
        return db

    def _record_needles(self, db, doc, shelf=None, replace=True):
        """Store the needles that apply to this document, and the relationships."""
        citation = doc.get('CITATION') or ''
        if replace:
            db.execute('DELETE FROM needle WHERE citation = ?', (citation,))
            db.execute('DELETE FROM edge WHERE citation = ?', (citation,))
            db.execute('DELETE FROM annotation WHERE citation = ?', (citation,))
        self._write_needle_rows(db, [_needle_rows(doc, shelf)])

    def _write_terms(self, db, packed):
        """Insert needle and edge rows. This connection does not parse."""
        needles, edges = [], []
        for part in packed:
            needles.extend(part[0])
            edges.extend(part[1])
        if needles:
            db.executemany(
                'INSERT INTO needle (citation, code, class, form, start, end) VALUES (?, ?, ?, ?, ?, ?)',
                needles,
            )
        if edges:
            db.executemany(
                'INSERT INTO edge (citation, code, kind, prior, receiver) VALUES (?, ?, ?, ?, ?)',
                edges,
            )

    def _write_annotations(self, db, packed):
        """Insert annotation rows. This connection does not parse."""
        notes = []
        for part in packed:
            notes.extend(part)
        if notes:
            db.executemany(
                'INSERT INTO annotation '
                '(citation, code, note, text, target, start, end, cite, join_kind) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                notes,
            )

    def _write_needle_rows(self, db, packed):
        """Insert rows on this connection. Callers do not share the connection."""
        self._write_terms(db, [(part[0], part[1]) for part in packed])
        self._write_annotations(db, [part[2] for part in packed])

    def index_stored_needles(self, workers=1):
        """Record needles for sections already in the index. The text index is left as it is.

        ``workers`` above 1 parse sections in other processes. Term rows and
        annotation rows are separate jobs. The SQLite connection only inserts
        them. It stays on this caller, it is not shared across threads, and
        ``check_same_thread`` stays on.
        """
        if not index.exists_in(self.idx_path):
            return 0
        workers = max(1, int(workers or 1))
        ix = index.open_dir(self.idx_path)
        db = self._needle_db()
        pool = None
        count = 0
        try:
            if workers > 1:
                import multiprocessing
                pool = multiprocessing.Pool(workers)
            db.execute('DELETE FROM needle')
            db.execute('DELETE FROM edge')
            db.execute('DELETE FROM annotation')
            batch = []
            since_commit = 0
            with ix.searcher() as searcher:
                total = searcher.doc_count()
                for docnum in range(total):
                    batch.append(_plain_section(searcher.stored_fields(docnum)))
                    if len(batch) < 32:
                        continue
                    count += self._flush_stored(db, batch, pool)
                    batch = []
                    since_commit += 32
                    if since_commit >= 5000:
                        db.commit()
                        since_commit = 0
                        logger.info('Needles recorded for %s of %s sections', count, total)
                if batch:
                    count += self._flush_stored(db, batch, pool)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            if pool is not None:
                pool.close()
                pool.join()
            db.close()
        return count

    def _flush_stored(self, db, batch, pool):
        if pool is None:
            terms = [_term_rows(doc) for doc in batch]
            notes = [_annotation_rows(doc) for doc in batch]
        else:
            terms = pool.map(_term_rows, batch)
            notes = pool.map(_annotation_rows, batch)
        self._write_terms(db, terms)
        self._write_annotations(db, notes)
        return len(batch)

    def annotations(self, note=None, code=None, target=None, limit=24):
        """Annotations recorded at ingestion.

        ``note`` is amount, period, date, antecedent, session, cut, case, or citation.
        ``target`` for a case note is ``uppercase`` or ``title``.
        A citation row includes ``cite`` and ``join``.
        """
        if not os.path.isfile(os.path.join(self.idx_path, 'needles.sqlite')):
            return []
        db = self._needle_db()
        try:
            query = 'SELECT citation, code, note, text, target, cite, join_kind FROM annotation WHERE 1 = 1'
            args = []
            if note:
                query += ' AND note = ?'
                args.append(note)
            if code:
                query += ' AND code = ?'
                args.append(getattr(code, 'value', code))
            if target:
                query += ' AND lower(target) = lower(?)'
                args.append(target)
            query += ' LIMIT ?'
            args.append(int(limit))
            rows = db.execute(query, args).fetchall()
        finally:
            db.close()
        return [
            {
                'citation': citation, 'code': book, 'note': kind, 'text': text,
                'target': target, 'cite': cite or '', 'join': join or '',
            }
            for citation, book, kind, text, target, cite, join in rows
        ]

    def targets(self, note):
        """Common and rare targets for one note.

        The list is highest count first. ``top`` is the common end. ``bottom``
        is the rare end. Case is folded, so ``ET SEQ.`` counts with ``et seq.``
        """
        from weight import ends
        if not os.path.isfile(os.path.join(self.idx_path, 'needles.sqlite')):
            return ends([])
        db = self._needle_db()
        try:
            rows = db.execute(
                'SELECT lower(target), COUNT(*), COUNT(DISTINCT code) FROM annotation '
                'WHERE note = ? AND target != "" '
                'GROUP BY lower(target) ORDER BY COUNT(*) DESC, lower(target)',
                (note,),
            ).fetchall()
        finally:
            db.close()
        return ends([
            {'target': target, 'count': count, 'codes': codes}
            for target, count, codes in rows
        ])

    def needles(self, code=None, cls=None):
        """Hits recorded at ingestion. ``code`` and ``cls`` narrow the scope."""
        if not os.path.isfile(os.path.join(self.idx_path, 'needles.sqlite')):
            return []
        db = self._needle_db()
        try:
            query = 'SELECT citation, code, class, form, start, end FROM needle WHERE 1 = 1'
            args = []
            if code:
                query += ' AND code = ?'
                args.append(getattr(code, 'value', code))
            if cls:
                query += ' AND class = ?'
                args.append(cls if isinstance(cls, str) else cls.__name__)
            query += ' ORDER BY citation, start'
            rows = db.execute(query, args).fetchall()
        finally:
            db.close()
        return [
            {'citation': row[0], 'code': row[1], 'class': row[2], 'form': row[3], 'start': row[4], 'end': row[5]}
            for row in rows
        ]

    def vesting_edges(self, code=None, kind='vesting'):
        """Stored edges of one kind, as ``(source, target, label)`` triples.

        Vesting is the office graph. Citation is the section graph. The chart
        and the client's drawing read this one list.
        """
        if not os.path.isfile(os.path.join(self.idx_path, 'needles.sqlite')):
            return []
        db = self._needle_db()
        try:
            query = 'SELECT DISTINCT prior, receiver FROM edge WHERE kind = ?'
            args = [kind]
            if code:
                query += ' AND code = ?'
                args.append(getattr(code, 'value', code))
            query += ' ORDER BY prior, receiver'
            rows = db.execute(query, args).fetchall()
        finally:
            db.close()
        label = 'vested' if kind == 'vesting' else kind
        return [(prior, receiver, label) for prior, receiver in rows]

    def code_edges(self):
        """Book to book. The cited book is the first word of the stored target."""
        if not os.path.isfile(os.path.join(self.idx_path, 'needles.sqlite')):
            return []
        db = self._needle_db()
        try:
            rows = db.execute(
                "SELECT code, receiver FROM edge WHERE kind = 'citation'"
            ).fetchall()
        finally:
            db.close()
        counted = {}
        for source, cited in rows:
            book = (cited or '').split(' ', 1)[0]
            if source and book:
                counted[(source, book)] = counted.get((source, book), 0) + 1
        return [
            (source, book, 'cites', count)
            for (source, book), count in counted.items()
        ]

    def enactment_edges(self, code=None):
        """A section and the Statutes chapter stored on its session note."""
        if not os.path.isfile(os.path.join(self.idx_path, 'needles.sqlite')):
            return []
        db = self._needle_db()
        try:
            query = "SELECT citation, target FROM annotation WHERE note = 'session' AND target != ''"
            args = []
            if code:
                query += ' AND code = ?'
                args.append(getattr(code, 'value', code))
            query += ' ORDER BY citation, target'
            rows = db.execute(query, args).fetchall()
        finally:
            db.close()
        return list(dict.fromkeys((citation, target, 'enacted') for citation, target in rows))

    def reference_edges(self, citation, limit=24):
        """One section, the targets it names, and the sections that name it."""
        if not os.path.isfile(os.path.join(self.idx_path, 'needles.sqlite')):
            return []
        db = self._needle_db()
        try:
            rows = db.execute(
                'SELECT DISTINCT prior, receiver, kind FROM edge '
                'WHERE kind IN (?, ?) AND (prior = ? OR receiver LIKE ?) '
                'ORDER BY kind, prior, receiver LIMIT ?',
                ('citation', 'article', citation, citation + '%', limit),
            ).fetchall()
        finally:
            db.close()
        return [(prior, receiver, kind) for prior, receiver, kind in rows]

    def vesting_diagram(self, code=None, kind='vesting'):
        """That edge list as a flowchart."""
        from structure import _chart
        label = 'vested' if kind == 'vesting' else kind
        return _chart(self.vesting_edges(code=code, kind=kind), label)

    def code_diagram(self):
        """One node per book. An arrow is a stored citation from one book into another."""
        from structure import _chart
        return _chart(self.code_edges(), 'cites')

    def enactment_diagram(self, code=None):
        """A section and the Statutes chapter stored on its session note. The chapter is not opened."""
        from structure import _chart
        return _chart(self.enactment_edges(code=code), 'enacted')

    def reference_diagram(self, citation, limit=24):
        """One section and the statute or article targets it names, plus sections that name it."""
        from structure import _chart
        return _chart(self.reference_edges(citation, limit=limit), 'citation')

    def _read_codes(self):
        if not os.path.isfile(self.codes_path):
            return {}
        with open(self.codes_path, encoding='utf-8') as fh:
            return json.load(fh)

    def _write_codes(self, codes):
        with open(self.codes_path, 'w', encoding='utf-8') as fh:
            json.dump(codes, fh, ensure_ascii=False, indent=2, sort_keys=True)

    def _region_indexed(self):
        """False when this index was built before region fields were stored."""
        if not index.exists_in(self.idx_path):
            return False
        idx = index.open_dir(self.idx_path)
        try:
            with idx.searcher() as searcher:
                return any(True for _ in searcher.lexicon('COUNTRY'))
        except TermNotFound:
            return False

    @staticmethod
    def _region_terms(country, subdivision):
        terms = []
        if country is None:
            country = DEFAULT_COUNTRY
        if subdivision is None:
            subdivision = DEFAULT_SUBDIVISION
        if country not in (None, 'all'):
            terms.append(Term('COUNTRY', str(country)))
        if subdivision not in (None, 'all'):
            terms.append(Term('SUBDIVISION', str(subdivision)))
        return terms

    def _filter(self, active_only, session, country=None, subdivision=None):
        if country is None:
            country = DEFAULT_COUNTRY
        if subdivision is None:
            subdivision = DEFAULT_SUBDIVISION
        terms = []
        if active_only:
            terms.append(Term('ACTIVE_FLG', True))
        if self._region_indexed():
            terms.extend(self._region_terms(country, subdivision))
        if session is None:
            if self._region_indexed():
                years = self.sessions(country=country, subdivision=subdivision)
            else:
                years = self.sessions()
            session = years[-1] if years else None
        if session not in (None, 'all'):
            terms.append(Term('SESSION', str(session)))
        if not terms:
            return None
        if len(terms) == 1:
            return terms[0]
        return And(terms)

    @staticmethod
    def _hit(hit):
        snippet = hit.highlights('LEGAL_TEXT') or (hit.get('LEGAL_TEXT') or '')[:400]
        return {
            'citation': hit.get('CITATION') or '%s %s' % (hit.get('LAW_CODE'), hit.get('SECTION_NUM')),
            'code': hit.get('LAW_CODE'),
            'code_title': hit.get('CODE_HEADING'),
            'section': hit.get('SECTION_NUM'),
            'title': hit.get('SECTION_TITLE'),
            'division': hit.get('DIVISION_HEADING'),
            'part': hit.get('PART_HEADING'),
            'chapter': hit.get('CHAPTER_HEADING'),
            'article': hit.get('ARTICLE_HEADING'),
            'session': hit.get('SESSION'),
            'country': hit.get('COUNTRY'),
            'subdivision': hit.get('SUBDIVISION'),
            'locality': hit.get('LOCALITY') or '',
            'score': hit.score,
            'snippet': snippet,
        }

    @staticmethod
    def _section(hit):
        found = Indexer._hit(hit)
        found['text'] = hit.get('LEGAL_TEXT') or ''
        found['history'] = hit.get('SECTION_HISTORY') or hit.get('HISTORY') or ''
        found.pop('snippet', None)
        found.pop('score', None)
        return found
