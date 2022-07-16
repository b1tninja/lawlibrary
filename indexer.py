import logging
import os.path
from enum import Enum, auto

from whoosh import highlight, index
from whoosh.fields import SchemaClass, ID, TEXT, NUMERIC, DATETIME, BOOLEAN
from whoosh.qparser import QueryParser

from config import data_dir
WHOOSH_INDEX_BASEDIR = os.path.join(data_dir, 'idx')
from utils import mkdir

logger = logging.getLogger(os.path.basename(__file__))

class LawSchema(SchemaClass):
    PK = ID(unique=True)
    ACTIVE_FLG = BOOLEAN()
    ARTICLE = ID()
    ARTICLE_HEADING = TEXT(stored=True)
    ARTICLE_HISTORY = TEXT(stored=True)
    CHAPTER = ID()
    CHAPTER_HEADING = TEXT(stored=True)
    CODE_HEADING = TEXT(stored=True)
    DIVISION = ID()
    DIVISION_HEADING = TEXT(stored=True)
    EFFECTIVE_DATE = DATETIME(stored=True)
    HISTORY = TEXT(stored=True)
    LAW_CODE = ID()
    LAW_SECTION_VERSION_ID = ID()
    LEGAL_TEXT = TEXT(stored=True)
    LOB_FILE = ID()
    OP_CHAPTER = ID()
    OP_SECTION = ID()
    OP_STATUES = ID()
    PART = ID()
    SECTION_HISTORY = TEXT(stored=True)
    SECTION_NUM = ID(stored=True)
    SECTION_TITLE = TEXT(stored=True)
    TITLE = ID()
    TRANS_UID = ID()
    TRANS_UPDATE = DATETIME()


class IndexState(Enum):
    Unknown = auto()
    Created = auto()
    Initialize = auto()
    Opening = auto()
    Opened = auto()
    Committed = auto()


class Indexer:
    def __init__(self, basedir=WHOOSH_INDEX_BASEDIR):
        self.state = IndexState.Unknown

        self.idx_path = os.path.join(basedir, 'idx')

        if any([not os.path.exists(d) for d in [basedir,
                                                self.idx_path]]):
            self.state = IndexState.Initialize

        mkdir(basedir)

    def index_pubinfo_laws(self, pubinfo, laws):
        if mkdir(self.idx_path):
            law_idx = index.create_in(self.idx_path, LawSchema)
        else:
            law_idx = index.open_dir(self.idx_path)

        with law_idx.writer() as writer:
            for law in laws:
                writer.add_document(**law)

    def search_law(self, q, callback):
        idx = index.open_dir(self.idx_path)
        with idx.searcher() as searcher:
            parser = QueryParser("LEGAL_TEXT", idx.schema).parse(q)
            results = searcher.search(parser)
            # results.fragmenter = highlight.PinpointFragmenter(surround=64, autotrim=True)
            results.fragmenter = highlight.ContextFragmenter(surround=128)
            results.formatter = highlight.UppercaseFormatter()
            callback(results)
