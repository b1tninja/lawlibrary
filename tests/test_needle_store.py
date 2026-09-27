"""The needle store is read while it is written.

A route, a test, or the MCP server opens the store to read. An index build
opens it to write, for an hour at a time. In SQLite's default journal a
writer's commit shuts every reader out, and opening the store used to run
schema statements that took the write lock even when there was nothing to
do, so a reader failed the instant a build was under way. These hold the two
properties that fix that: opening to read takes no write lock, and a reader
and a writer proceed together.
"""

import os
import sqlite3

import pytest

import indexer
from indexer import Indexer


@pytest.fixture
def store(tmp_path):
    """An Indexer whose needle store is a fresh file, and the path it is at."""
    idxer = Indexer()
    idxer.idx_path = str(tmp_path)
    return idxer, os.path.join(str(tmp_path), 'needles.sqlite')


def test_a_fresh_store_is_built_in_write_ahead_mode(store):
    idxer, path = store
    db = idxer._needle_db()
    assert db.execute('PRAGMA journal_mode').fetchone()[0] == 'wal'
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == {'needle', 'edge', 'annotation'}
    assert Indexer._needle_schema_present(db)
    db.close()


def test_opening_a_built_store_runs_no_schema_statements(store):
    """The first open builds the schema. Every later one reads that it is there."""
    idxer, path = store
    idxer._needle_db().close()
    assert path in indexer._NEEDLE_READY
    # Opened a second time with the file locked for writing by another
    # connection: a schema statement would need that lock and fail, a read
    # does not.
    holder = sqlite3.connect(path, timeout=1)
    holder.execute('BEGIN IMMEDIATE')
    db = idxer._needle_db()
    assert db.execute('SELECT COUNT(*) FROM needle').fetchone()[0] == 0
    db.close()
    holder.rollback()
    holder.close()


def test_a_reader_and_an_open_writer_proceed_together(store):
    """The writer's transaction is not the reader's problem, and vice versa."""
    idxer, path = store
    writer = idxer._needle_db()
    writer.execute('BEGIN')
    writer.executemany(
        'INSERT INTO annotation (citation, code, note, text, target, start, end, cite, join_kind) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [('X %d' % n, 'X', 'citation', 'w', 't', 0, 1, None, None) for n in range(5000)],
    )
    reader = idxer._needle_db()
    assert reader.execute('SELECT COUNT(*) FROM annotation').fetchone()[0] == 0, 'a consistent snapshot'
    writer.commit()
    assert reader.execute('SELECT COUNT(*) FROM annotation').fetchone()[0] == 5000
    reader.close()
    writer.close()


def test_an_empty_file_is_not_a_store():
    db = sqlite3.connect(':memory:')
    assert not Indexer._needle_schema_present(db)
    db.close()
