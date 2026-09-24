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

from config import data_dir
from utils import mkdir

WHOOSH_INDEX_BASEDIR = os.path.join(data_dir, 'idx')
logger = logging.getLogger('indexer')

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
    SESSION = ID(stored=True)
    SUBDIVISION = ID(stored=True)
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
    code = doc.get('LAW_CODE') or ''
    section = doc.get('SECTION_NUM') or ''
    if code and section:
        doc['CITATION'] = '%s %s' % (code, section)
    return doc


class Indexer:
    def __init__(self, basedir=WHOOSH_INDEX_BASEDIR):
        self.state = IndexState.Unknown
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
        try:
            for law in laws:
                doc = _present(law)
                if 'PK' not in doc:
                    continue
                writer.update_document(**doc)
                code = doc.get('LAW_CODE')
                heading = law.get('CODE_HEADING')
                if code and heading:
                    codes[code] = heading
                count += 1
                if count % 5000 == 0:
                    logger.info("Indexed %s sections from %s", count, os.path.basename(pubinfo))
            writer.commit()
            self.state = IndexState.Committed
        except Exception:
            writer.cancel()
            raise
        self._write_codes(codes)
        return count

    def sessions(self):
        if not index.exists_in(self.idx_path):
            return []
        idx = index.open_dir(self.idx_path)
        with idx.searcher() as searcher:
            return sorted(term.decode() for term in searcher.lexicon('SESSION'))

    def search_law(self, q, callback=None, limit=10, active_only=True, session=None):
        idx = index.open_dir(self.idx_path)
        with idx.searcher() as searcher:
            parsed = self._parse(q, idx.schema)
            results = searcher.search(parsed, limit=limit, filter=self._filter(active_only, session))
            results.fragmenter = highlight.ContextFragmenter(surround=128)
            results.formatter = highlight.UppercaseFormatter()
            if callback is not None:
                callback(results)
            return [self._hit(hit) for hit in results]

    def get_section(self, code, section, active_only=True, session=None):
        code = self._resolve_code(code)
        section = str(section).rstrip('.')
        idx = index.open_dir(self.idx_path)
        query = And([Term('LAW_CODE', code), Term('SECTION_NUM', section)])
        with idx.searcher() as searcher:
            results = searcher.search(query, limit=20, filter=self._filter(active_only, session))
            return [self._section(hit) for hit in results]

    def list_codes(self):
        codes = self._read_codes()
        return [{'code': code, 'title': title} for code, title in sorted(codes.items(), key=lambda item: item[1])]

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
            if folded == name or titled == name or titled == name.replace(' CODE', ''):
                return abbr
        return folded

    def _read_codes(self):
        if not os.path.isfile(self.codes_path):
            return {}
        with open(self.codes_path, encoding='utf-8') as fh:
            return json.load(fh)

    def _write_codes(self, codes):
        with open(self.codes_path, 'w', encoding='utf-8') as fh:
            json.dump(codes, fh, ensure_ascii=False, indent=2, sort_keys=True)

    def _filter(self, active_only, session):
        terms = []
        if active_only:
            terms.append(Term('ACTIVE_FLG', True))
        if session is None:
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
            'subdivision': hit.get('SUBDIVISION'),
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
