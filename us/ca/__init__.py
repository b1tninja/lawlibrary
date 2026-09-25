#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import io
import json
import logging
import multiprocessing
import os
import os.path
import pprint
import re
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import closing
from types import SimpleNamespace

from publication import Instrument, Publication, State

import html2text  # Aaron Swartz original author
# On July 11, 2011, Swartz was indicted for unlawfully obtaining information.
# Facing trial and the possibility of imprisonment, Swartz committed suicide.

ENCODING = 'utf-8'
CURRENT_YEAR = datetime.datetime.today().year
PUBINFO_INDEX = 'https://downloads.leginfo.legislature.ca.gov/'
LAW_DATS = ('CODES_TBL', 'LAW_TOC_TBL', 'LAW_SECTION_TBL', 'LAW_TOC_SECTIONS_TBL')
# pubinfo_YYYY.zip table-set eras (core BILL_VERSION / LAW_SECTION columns stay 18):
#   1989-1991  bills only (3 .dat)
#   1993-1997  + BILL_ANALYSIS_TBL
#   1999-2001  votes / history / legislators
#   2003-2009  + COMMITTEE_HEARING_TBL
#   2011-2013  codes appear (17 .dat); no COMMITTEE_AGENDA_TBL
#   2015-2025  + COMMITTEE_AGENDA_TBL (18 .dat)
# Codes tables (LAW_SECTION_TBL) exist from 2011 on. Earlier zips are measures only.
HEADING_LEVELS = (
    ('DIVISION', 'DIVISION_HEADING'),
    ('TITLE', 'TITLE_HEADING'),
    ('PART', 'PART_HEADING'),
    ('CHAPTER', 'CHAPTER_HEADING'),
    ('ARTICLE', 'ARTICLE_HEADING'),
)

logger = logging.getLogger('ca')

# Instead of importing bcolors, just stole the dictionary. Props to Yogesh Sharma
ansi_escape_codes = {'OK': '\x1b[92m',
                     'WARN': '\x1b[93m',
                     'ERR': '\x1b[31m',
                     'UNDERLINE': '\x1b[4m',
                     'ITALIC': '\x1b[3m',
                     'BOLD': '\x1b[1m',
                     'BLUE': '\x1b[94m',
                     'ENDC': '\x1b[0m',
                     'HEADER': '\x1b[95m\x1b[1m',
                     'PASS': '\x1b[92m\x1b[1m',
                     'FAIL': '\x1b[31m\x1b[1m',
                     'HELP': '\x1b[93m',
                     'BITALIC': '\x1b[1m\x1b[3m',
                     'BLUEIC': '\x1b[1m\x1b[3m\x1b[92m',
                     'END': '\x1b[0m'}


def opt_tqdm(iterable):
    """
    Optional tqdm progress bars
    """
    try:
        import tqdm
    except:
        return iterable
    else:
        return tqdm.tqdm(iterable)


class LawLibrary:
    pass


def parse_caml(LOB):
    return html2text.HTML2Text(bodywidth=0).handle(LOB)


def read_text_from_zipped_file(zip_file, target):
    with io.TextIOWrapper(zip_file.open(target, 'r'), encoding=ENCODING, errors='replace') as text_file:
        return text_file.read()


def read_lines_from_zipped_file(zip_file, target):
    with io.TextIOWrapper(zip_file.open(target, 'r'), encoding=ENCODING) as text_file:
        for line in map(str.rstrip, iter(text_file.readline, '')):
            if not line:
                continue

            yield line


def read_rows_from_zipped(zip_file, target):
    for line in read_lines_from_zipped_file(zip_file, target):
        if not line:
            continue

        row = line.split("\t")
        yield tuple(col[1:-1] if col[0] == col[-1] == '`' else
                    None if col == 'NULL' else
                    col for col in row)


def get_dats_and_lobs(path, prefixes=None):
    """gotta get dats... and lobs"""
    # https://youtu.be/IC9nuBmeX-A
    basename = os.path.basename(path)
    dats = dict()
    lobs = dict()

    logger.info("Extracting dats and lobs from: %s", basename)
    with zipfile.ZipFile(path) as zf:
        for file in opt_tqdm(zf.filelist):
            name, ext = os.path.splitext(file.filename)
            if type(prefixes) is list and not any([file.filename.startswith(p) for p in prefixes]):
                logger.debug("Skipping: %s", file.filename)
                continue

            if ext == '.dat':
                dats[name] = list(read_rows_from_zipped(zf, file))

            elif ext == '.lob':
                CAML = read_text_from_zipped_file(zf, file.filename)
                lobs[file.filename] = CAML
            else:
                logger.debug("Unhandled content: %s", file.filename)

    return dats, lobs


def unzip_dats_and_lobs(path, jsonp=False, **kwargs):
    assert os.path.isfile(path)

    pubinfo = None
    json_path = path + '.jsonp'

    if jsonp and os.path.exists(json_path):
        assert os.path.isfile(json_path)
        with closing(open(json_path, 'r', encoding=ENCODING)) as fh:
            try:
                pubinfo = json.load(fh)
            except (json.JSONDecodeError, IOError):
                pass

    if pubinfo is None:
        dats, lobs = get_dats_and_lobs(path, **kwargs)
        pubinfo = dict(dats=dats, lobs=lobs)

        if jsonp:
            logger.info('Writting json version of dats and lobs found "%s" to "%s".', path, os.path.basename(json_path))
            with closing(open(json_path, 'w', encoding=ENCODING)) as fh:
                try:
                    json.dump(pubinfo, fh, ensure_ascii=False)  # ensure_ascii=True
                except UnicodeEncodeError as e:
                    logger.warning("Not Plain-Text:", e)
                except Exception as e:
                    logger.critical("Unable to write pubinfo JSON to disk", e)

    return pubinfo.get('dats', []), pubinfo.get('lobs', [])


def get_datses_and_lobses(basedir, **kwargs):
    for basename in os.listdir(basedir):
        if not basename.endswith('.zip'):
            continue

        path = os.path.join(basedir, basename)

        if not os.path.isfile(path):
            continue

        dats, lobs = unzip_dats_and_lobs(path, **kwargs)
        yield path, (dats, lobs)


def dxt(func):
    return lambda *args, **kwargs: func(*args, **dict([(os.path.splitext(k)[0], v) for k, v in kwargs.items()]))


def starg(func):
    return lambda args: func(*args)


def datetime_fromiso(dt):
    return datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')


def rstrip_dot(value):
    return value.rstrip('.') if value else value


def zip_dat_names(path):
    """Stem names of every .dat inside a pubinfo zip."""
    with zipfile.ZipFile(path) as zf:
        return {os.path.splitext(os.path.basename(info.filename))[0]
                for info in zf.infolist()
                if os.path.splitext(info.filename)[1].lower() == '.dat'}


def iter_dat_rows(zf, stem):
    """Yield parsed rows from one .dat table stem inside an open zip."""
    for info in zf.infolist():
        name, ext = os.path.splitext(os.path.basename(info.filename))
        if ext.lower() == '.dat' and name == stem:
            yield from read_rows_from_zipped(zf, info)
            return


@starg
def LawTocTblDict(LAW_CODE, DIVISION, TITLE, PART, CHAPTER, ARTICLE, HEADING, ACTIVE_FLG, TRANS_UID, TRANS_UPDATE,
                  NODE_SEQUENCE, NODE_LEVEL, NODE_POSITION, NODE_TREEPATH, CONTAINS_LAW_SECTIONS, HISTORY_NOTE,
                  OP_STATUES, OP_CHAPTER, OP_SECTION):
    # if DIVISION:
    #     DIVISION = float(DIVISION.rstrip('.'))
    # if TITLE:
    #     TITLE = int(float(TITLE.rstrip('.')))
    # if PART:
    #     PART = int(float(PART.rstrip('.')))
    # if CHAPTER:
    #     CHAPTER = int(float(CHAPTER.rstrip('.')))
    # if ARTICLE:
    #     ARTICLE = int(float(ARTICLE.rstrip('.')))
    # HEADING
    ACTIVE_FLG = 'Y' == ACTIVE_FLG
    # TRANS_UID
    TRANS_UPDATE = datetime_fromiso(TRANS_UPDATE)
    NODE_SEQUENCE = int(NODE_SEQUENCE)
    NODE_LEVEL = int(NODE_LEVEL)
    NODE_POSITION = int(NODE_POSITION)
    NODE_TREEPATH = tuple(map(int, NODE_TREEPATH.split('.')))
    CONTAINS_LAW_SECTIONS = 'Y' == CONTAINS_LAW_SECTIONS
    # HISTORY_NOTE
    # OP_STATUES = float(OP_STATUES or 0)
    # OP_CHAPTER = float(OP_CHAPTER or 0)
    # OP_SECTION = float(OP_SECTION or 0)

    d = dict(**locals())

    # pprint.pprint(d)
    # assert 1849 <= OP_STATUES <= CURRENT_YEAR

    return d


@starg
def LawTocSectionsTblDict(ID, LAW_CODE, NODE_TREEPATH, SECTION_NUM, SECTION_ORDER, TITLE, OP_STATUES, OP_CHAPTER,
                          OP_SECTION, TRANS_UID, TRANS_UPDATE, LAW_SECTION_VERSION_ID, SEQ_NUM):
    NODE_TREEPATH = tuple(map(int, NODE_TREEPATH.split('.'))) if NODE_TREEPATH else ()
    SECTION_NUM = rstrip_dot(SECTION_NUM)
    TRANS_UPDATE = datetime_fromiso(TRANS_UPDATE)
    return dict(**locals())


@starg
def LawSectionTblDict(PK, LAW_CODE, SECTION_NUM, OP_STATUES, OP_CHAPTER, OP_SECTION, EFFECTIVE_DATE,
                      LAW_SECTION_VERSION_ID, DIVISION, TITLE, PART, CHAPTER, ARTICLE, HISTORY, LOB_FILE, ACTIVE_FLG,
                      TRANS_UID, TRANS_UPDATE):
    # NOTE: changed ID to PK to avoid conflict with whoosh.fields.ID
    if EFFECTIVE_DATE is not None:
        EFFECTIVE_DATE = datetime_fromiso(EFFECTIVE_DATE)  # .date()

    DIVISION = rstrip_dot(DIVISION)
    TITLE = rstrip_dot(TITLE)
    PART = rstrip_dot(PART)
    CHAPTER = rstrip_dot(CHAPTER)
    ARTICLE = rstrip_dot(ARTICLE)
    SECTION_NUM = rstrip_dot(SECTION_NUM)
    ACTIVE_FLG = 'Y' == ACTIVE_FLG
    TRANS_UPDATE = datetime_fromiso(TRANS_UPDATE)

    return dict(**locals())


def _lob_text(LOBS, name):
    if not name:
        return ''
    if callable(LOBS):
        return LOBS(name) or ''
    try:
        return LOBS[name] or ''
    except KeyError:
        return ''


def deepest_heading(DIVISION, TITLE, PART, CHAPTER, ARTICLE):
    """The heading on a toc row names its deepest filled level. Parents are repeated on the row."""
    if ARTICLE:
        return 'ARTICLE_HEADING'
    if CHAPTER:
        return 'CHAPTER_HEADING'
    if PART:
        return 'PART_HEADING'
    if TITLE:
        return 'TITLE_HEADING'
    if DIVISION:
        return 'DIVISION_HEADING'
    return None


def heading_fields(DIVISION_HEADING, TITLE_HEADING, PART_HEADING, CHAPTER_HEADING,
                   ARTICLE_HEADING, ARTICLE_HISTORY):
    return dict(**locals())


def toc_headings(LAW_CODE, NODE_TREEPATH, toc_by_path):
    """Walk parent NODE_TREEPATH prefixes; shared by every LAW_SECTION edition."""
    DIVISION_HEADING = TITLE_HEADING = PART_HEADING = CHAPTER_HEADING = ARTICLE_HEADING = ''
    ARTICLE_HISTORY = ''
    for i in range(1, len(NODE_TREEPATH) + 1):
        try:
            node = toc_by_path[LAW_CODE, NODE_TREEPATH[:i]]
        except KeyError:
            continue
        level = deepest_heading(node.DIVISION, node.TITLE, node.PART, node.CHAPTER, node.ARTICLE)
        HEADING = node.HEADING or ''
        if level == 'DIVISION_HEADING':
            DIVISION_HEADING = HEADING
        elif level == 'TITLE_HEADING':
            TITLE_HEADING = HEADING
        elif level == 'PART_HEADING':
            PART_HEADING = HEADING
        elif level == 'CHAPTER_HEADING':
            CHAPTER_HEADING = HEADING
        elif level == 'ARTICLE_HEADING':
            ARTICLE_HEADING = HEADING
            ARTICLE_HISTORY = node.HISTORY_NOTE or ''
    return heading_fields(DIVISION_HEADING, TITLE_HEADING, PART_HEADING, CHAPTER_HEADING,
                          ARTICLE_HEADING, ARTICLE_HISTORY)


def section_overlay(CODE_HEADING, DIVISION_HEADING, TITLE_HEADING, PART_HEADING, CHAPTER_HEADING,
                    ARTICLE_HEADING, ARTICLE_HISTORY, LEGAL_TEXT, SECTION_TITLE, SECTION_HISTORY,
                    SESSION, PK):
    return dict(**locals())


def law_indexes(CODES_TBL, LAW_TOC_TBL, LAW_TOC_SECTIONS_TBL):
    CODES_TBL = dict(CODES_TBL)
    toc_by_path = dict()
    for record in map(LawTocTblDict, LAW_TOC_TBL):
        node = SimpleNamespace(**record)
        toc_by_path[node.LAW_CODE, node.NODE_TREEPATH] = node

    by_version = dict()
    by_section = dict()
    for node in map(LawTocSectionsTblDict, LAW_TOC_SECTIONS_TBL):
        placed = SimpleNamespace(**node)
        by_version[placed.LAW_CODE, placed.LAW_SECTION_VERSION_ID] = placed
        by_section[placed.LAW_CODE, placed.SECTION_NUM] = placed
    return CODES_TBL, toc_by_path, by_version, by_section


def format_law_section(law_section, LOB, *, CODES_TBL, toc_by_path, by_version, by_section, SESSION):
    ID, LAW_CODE, SECTION_NUM, OP_STATUES, OP_CHAPTER, OP_SECTION, EFFECTIVE_DATE, LAW_SECTION_VERSION_ID, DIVISION, TITLE, PART, CHAPTER, ARTICLE, HISTORY, LOB_FILE, ACTIVE_FLG, TRANS_UID, TRANS_UPDATE = law_section
    try:
        d = LawSectionTblDict(law_section)
    except Exception:
        logger.warning("Unexpected table structure, unsure how to format law section: %s %s %s %s %s",
                       LAW_CODE, DIVISION, CHAPTER, ARTICLE, SECTION_NUM)
        pprint.pprint(law_section)
        return None

    try:
        placed = by_version[LAW_CODE, LAW_SECTION_VERSION_ID]
    except KeyError:
        try:
            placed = by_section[LAW_CODE, rstrip_dot(SECTION_NUM)]
        except KeyError:
            placed = None

    try:
        CODE_HEADING = CODES_TBL[LAW_CODE]
    except KeyError:
        CODE_HEADING = ''
    head = SimpleNamespace(**heading_fields('', '', '', '', '', ''))
    SECTION_TITLE = ''
    if placed is not None:
        SECTION_TITLE = placed.TITLE or ''
        head = SimpleNamespace(**toc_headings(LAW_CODE, placed.NODE_TREEPATH, toc_by_path))
    LEGAL_TEXT = parse_caml(LOB) if LOB else ''
    SECTION_HISTORY = HISTORY or ''
    SESSION = '' if SESSION is None else str(SESSION)
    PK = '%s:%s' % (SESSION, ID)
    d.update(section_overlay(CODE_HEADING, head.DIVISION_HEADING, head.TITLE_HEADING, head.PART_HEADING,
                             head.CHAPTER_HEADING, head.ARTICLE_HEADING, head.ARTICLE_HISTORY,
                             LEGAL_TEXT, SECTION_TITLE, SECTION_HISTORY, SESSION, PK))
    return d


@dxt
def parse_datlobs(LOBS, *, CODES_TBL, LAW_TOC_TBL, LAW_SECTION_TBL, LAW_TOC_SECTIONS_TBL, SESSION=None):
    CODES_TBL, toc_by_path, by_version, by_section = law_indexes(CODES_TBL, LAW_TOC_TBL, LAW_TOC_SECTIONS_TBL)
    for law_section in LAW_SECTION_TBL:
        LOB_FILE = law_section[14]
        d = format_law_section(law_section, _lob_text(LOBS, LOB_FILE),
                               CODES_TBL=CODES_TBL, toc_by_path=toc_by_path,
                               by_version=by_version, by_section=by_section, SESSION=SESSION)
        if d is not None:
            yield d


def read_lob(zip_file, name):
    if not name:
        return ''
    for candidate in (name, os.path.basename(name)):
        try:
            return read_text_from_zipped_file(zip_file, candidate)
        except KeyError:
            continue
    logger.warning("Missing lob %s", name)
    return ''


def session_year(path):
    match = re.search(r'pubinfo_(\d{4})', os.path.basename(path))
    return int(match.group(1)) if match else None


def load_law_dats(path):
    with zipfile.ZipFile(path) as zf:
        present = {os.path.splitext(os.path.basename(info.filename))[0]
                   for info in zf.infolist()
                   if os.path.splitext(info.filename)[1].lower() == '.dat'}
        missing = [name for name in LAW_DATS if name not in present]
        if missing:
            raise TypeError('not a code publication, missing %s' % ', '.join(missing))
        return {stem: list(iter_dat_rows(zf, stem)) for stem in LAW_DATS}


def iter_laws(path):
    """Yield one code section at a time, reading each CAML lob as it is needed."""
    dats = load_law_dats(path)
    SESSION = session_year(path)
    with zipfile.ZipFile(path) as zf:
        yield from parse_datlobs(lambda name: read_lob(zf, name), SESSION=SESSION, **dats)


# One open zip and the toc tables, private to each index worker.
_WORK = {}


def _boot_worker(path, CODES_TBL, toc_by_path, by_version, by_section, SESSION):
    _WORK['zf'] = zipfile.ZipFile(path)
    _WORK['CODES_TBL'] = CODES_TBL
    _WORK['toc_by_path'] = toc_by_path
    _WORK['by_version'] = by_version
    _WORK['by_section'] = by_section
    _WORK['SESSION'] = SESSION


def _format_chunk(rows):
    zf = _WORK['zf']
    framed = []
    for law_section in rows:
        LOB_FILE = law_section[14]
        d = format_law_section(law_section, read_lob(zf, LOB_FILE),
                               CODES_TBL=_WORK['CODES_TBL'], toc_by_path=_WORK['toc_by_path'],
                               by_version=_WORK['by_version'], by_section=_WORK['by_section'],
                               SESSION=_WORK['SESSION'])
        if d is not None:
            framed.append(d)
    return framed


def _chunks(rows, size):
    batch = []
    for row in rows:
        batch.append(row)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def iter_laws_parallel(path, workers=None, chunk_size=400):
    """Parse CAML in a process pool. Whoosh still has a single writer in the parent."""
    dats = load_law_dats(path)
    SESSION = session_year(path)
    CODES_TBL, toc_by_path, by_version, by_section = law_indexes(
        dats['CODES_TBL'], dats['LAW_TOC_TBL'], dats['LAW_TOC_SECTIONS_TBL'])
    rows = dats['LAW_SECTION_TBL']
    workers = workers or min(8, os.cpu_count() or 1)
    if workers <= 1:
        with zipfile.ZipFile(path) as zf:
            yield from parse_datlobs(lambda name: read_lob(zf, name), SESSION=SESSION, **dats)
        return

    ctx = multiprocessing.get_context('spawn')
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx, initializer=_boot_worker,
                             initargs=(path, CODES_TBL, toc_by_path, by_version, by_section, SESSION)) as pool:
        for framed in pool.map(_format_chunk, _chunks(rows, chunk_size), chunksize=1):
            yield from framed


def session_zips(basedir):
    found = []
    if not os.path.isdir(basedir):
        return found
    for name in os.listdir(basedir):
        match = re.fullmatch(r'pubinfo_(\d{4})\.zip', name)
        if match:
            found.append((int(match.group(1)), os.path.join(basedir, name)))
    found.sort()
    return [path for _, path in found]


@starg
def BillVersionTblDict(BILL_VERSION_ID, BILL_ID, VERSION_NUM, BILL_VERSION_ACTION_DATE, BILL_VERSION_ACTION,
                       REQUEST_NUM, SUBJECT, VOTE_REQUIRED, APPROPRIATION, FISCAL_COMMITTEE, LOCAL_PROGRAM,
                       SUBSTANTIVE_CHANGES, URGENCY, TAXLEVY, LOB_FILE, ACTIVE_FLG, TRANS_UID, TRANS_UPDATE):
    # Same 18 columns in the 1989 zip and the current loader. The lob is BILL_XML.
    if BILL_VERSION_ACTION_DATE is not None:
        BILL_VERSION_ACTION_DATE = datetime_fromiso(BILL_VERSION_ACTION_DATE)
    ACTIVE_FLG = 'Y' == ACTIVE_FLG
    if TRANS_UPDATE is not None:
        TRANS_UPDATE = datetime_fromiso(TRANS_UPDATE)
    return dict(**locals())


def bill_text(SESSION, PK, LAW_CODE, SECTION_NUM, SECTION_TITLE, LEGAL_TEXT, CODE_HEADING):
    return dict(**locals())


def format_bill_section(row, LOB, SESSION):
    """Frame one BILL_VERSION_TBL row. Shared by every bill-era zip (1989-2009)."""
    version = BillVersionTblDict(row)
    bill = SimpleNamespace(**version)
    LEGAL_TEXT = parse_caml(LOB) if LOB else ''
    PK = '%s:%s' % (SESSION, bill.BILL_VERSION_ID)
    LAW_CODE = 'BILL'
    SECTION_NUM = bill.BILL_ID
    SECTION_TITLE = bill.SUBJECT or ''
    CODE_HEADING = 'California bill'
    return dict(version, **bill_text(SESSION, PK, LAW_CODE, SECTION_NUM, SECTION_TITLE, LEGAL_TEXT, CODE_HEADING))


def subdivision_field(SUBDIVISION):
    return dict(**locals())


def stamp_subdivision(row, SUBDIVISION):
    row.update(subdivision_field(SUBDIVISION))
    return row


class SubdivisionIndexed:
    """Mixin: stamp ISO subdivision (California.code) on rows before Whoosh."""

    def index(self, indexer, path, workers=None, subdivision=None):
        def tagged():
            for row in self.parallel_sections(path, workers=workers):
                yield stamp_subdivision(row, subdivision)
        return indexer.index_pubinfo_laws(path, tagged())


class BillVersionRows:
    """Mixin: read BILL_VERSION_TBL. Column layout is stable from 1989 on."""

    def bill_sections(self, path):
        SESSION = '' if session_year(path) is None else str(session_year(path))
        with zipfile.ZipFile(path) as zf:
            rows = list(iter_dat_rows(zf, 'BILL_VERSION_TBL'))
            for row in rows:
                bill = SimpleNamespace(**BillVersionTblDict(row))
                LOB = read_lob(zf, bill.LOB_FILE)
                yield format_bill_section(row, LOB, SESSION)


class CaliforniaCodes(SubdivisionIndexed, Publication):
    """Code tables. Present in the session zips from 2011 on."""

    instrument = Instrument.STATUTE

    @classmethod
    def accepts(cls, names):
        return set(LAW_DATS) <= set(names)

    def sections(self, path):
        yield from iter_laws(path)

    def parallel_sections(self, path, workers=None, chunk_size=400):
        yield from iter_laws_parallel(path, workers=workers, chunk_size=chunk_size)


class CaliforniaBills(BillVersionRows, SubdivisionIndexed, Publication):
    """Sessions whose zip has measures and no code tables. 1989 through 2009."""

    instrument = Instrument.MEASURE

    @classmethod
    def accepts(cls, names):
        return 'BILL_VERSION_TBL' in names and 'LAW_SECTION_TBL' not in names

    def sections(self, path):
        yield from self.bill_sections(path)


class California(State):
    code = 'US-CA'
    source = PUBINFO_INDEX
    editions = (CaliforniaCodes, CaliforniaBills)

    def list_editions(self):
        return list_pubinfo_years()


def index_pubinfos(basedir, all_sessions=True, workers=None):
    """whoosh fulltext search index of the pubinfo, currently each individual section from  the CODES/LAW table"""
    from indexer import Indexer

    california = California()
    zips = session_zips(basedir)
    if zips and not all_sessions:
        zips = zips[-1:]
    indexer = Indexer()
    indexer.reset()
    for path in zips:
        try:
            edition = california.edition(path)
        except TypeError as e:
            logger.warning("Skipping %s... %s.", path, e)
            continue
        logger.info("Pubinfo zip: %s (%s)", path, type(edition).__name__)
        try:
            count = edition.index(indexer, path, workers=workers, subdivision=california.code)
        except TypeError as e:
            logger.warning("Skipping %s... %s.", path, e)
        else:
            logger.info("Indexed %s sections from %s", count, os.path.basename(path))
    else:
        logger.info("No more pubinfo_*.zip(s) to index in %s", basedir)


def print_pubinfos(basedir, colorize=False, jsonp=False):
    """Print pubinfo laws directly from odd-year pubinfos"""
    # First replace the ANSI terminal codes in the format string for colorized output
    law_fmt = \
"""
{BLUE}{{CODE_HEADING}}{ENDC}
    {{DIVISION_HEADING}}
        {{CHAPTER_HEADING}}

{UNDERLINE}{{ARTICLE_HEADING}}{ENDC} ( {ITALIC}{{ARTICLE_HISTORY}}{ENDC} )

{BOLD}{{SECTION_TITLE}}{ENDC}
{{LEGAL_TEXT}}
{ITALIC}{{SECTION_HISTORY}}{ENDC}
""".format_map(ansi_escape_codes if colorize else dict([(k, '') for k in ansi_escape_codes.keys()]))

    for path in session_zips(basedir):
        logger.info("Pubinfo zip: %s", path)
        try:
            for law in iter_laws(path):
                print(law_fmt.format(**law))

        except TypeError as e:
            logger.warning("Skipping %s... %s.", path, e)
    else:
        logger.info("No more pubinfo_*.zip(s) to index in dir: %s", basedir)


def dir_path(path):
    logger.debug("Checking --path: %s", path)
    if not os.path.exists(path):
        os.mkdir(path)
        return path
    elif os.path.isdir(path):
        return path
    else:
        raise NotADirectoryError(path)


def current_session_year(today=None):
    """Odd year that opens the two-year session. 2026 is still the 2025 session."""
    year = (today or datetime.date.today()).year
    return year if year % 2 else year - 1


def list_pubinfo_years():
    import urllib.request

    with urllib.request.urlopen(PUBINFO_INDEX) as resp:
        page = resp.read().decode('utf-8', 'replace')
    return sorted({int(year) for year in re.findall(r'pubinfo_(\d{4})\.zip', page)})


def _fetch_pubinfo(year, path):
    import urllib.request

    pubinfo = "pubinfo_%d.zip" % year
    dst = os.path.join(path, pubinfo)
    if os.path.isfile(dst):
        logger.info("Already have %s", pubinfo)
        return dst
    partial = dst + '.partial'
    logger.info("Retrieving %s", pubinfo)
    urllib.request.urlretrieve(PUBINFO_INDEX + pubinfo, partial)
    os.replace(partial, dst)
    logger.info("Retrieved %s", pubinfo)
    return dst


def download_pubinfos(path, *, session=None, all_sessions=True, workers=3):
    os.makedirs(path, exist_ok=True)
    if session is not None:
        years = [session]
    elif all_sessions:
        years = list_pubinfo_years()
    else:
        years = [current_session_year()]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda year: _fetch_pubinfo(year, path), years))


def main(argv=None):
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='downloads.leginfo.legislature.ca.gov pubinfo_*.zip Code reader.')
    parser.add_argument('--path', type=dir_path,
                        default='data',
                        help="Directory of pubinfo_YYYY.zip files from downloads.leginfo.legislature.ca.gov")
    parser.add_argument('--current', action='store_true',
                        help="Download and index only the current session, not every pubinfo_YYYY.zip")
    parser.add_argument('--workers', type=int, default=None,
                        help="Parser processes. Whoosh writing stays in this process.")
    parser.add_argument('-q', '--query', help="Search the index and print matching sections")
    parser.add_argument('-g', '--get', nargs=2, metavar=('CODE', 'SECTION'),
                        help="Print one section, e.g. --get CIV 1940")
    parser.add_argument('-n', '--limit', type=int, default=10)

    try:
        parser.add_argument('-p', '--print', action=argparse.BooleanOptionalAction)
        parser.add_argument('-d', '--download', action=argparse.BooleanOptionalAction)
        parser.add_argument('-i', '--index', action=argparse.BooleanOptionalAction)
        parser.add_argument('-c', '--color', action=argparse.BooleanOptionalAction, default=False)
        parser.add_argument('-j', '--json', action=argparse.BooleanOptionalAction, default=False,
                            help="Export laws/codes into a .json per pubinfo by parsing the dats and lobs")
    except Exception:
        parser.add_argument('-p', '--print', action="store_true")
        parser.add_argument('-d', '--download', action="store_true")
        parser.add_argument('-i', '--index', action="store_true")
        parser.add_argument('-c', '--color', action="store_true")
        parser.add_argument('-j', '--json', action="store_true")

    try:
        args = parser.parse_args(argv)
    except NotADirectoryError:
        logger.critical("Please specify a path to a directory containing pubinfo_2025.zip")
        parser.print_help(sys.stderr)
        return 1

    if args.download:
        download_pubinfos(args.path, all_sessions=not args.current)

    if args.index:
        index_pubinfos(args.path, all_sessions=not args.current, workers=args.workers)

    if args.get or args.query:
        from indexer import Indexer
        indexer = Indexer()
        if args.get:
            for section in indexer.get_section(args.get[0], args.get[1]):
                pprint.pp({k: section[k] for k in section if k != 'LEGAL_TEXT'})
                print(section.get('LEGAL_TEXT') or '')
        if args.query:
            for hit in indexer.search_law(args.query, limit=args.limit):
                pprint.pp(hit)

    if args.print:
        print_pubinfos(args.path, colorize=args.color, jsonp=args.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
