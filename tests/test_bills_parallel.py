"""The bill editions parse in the pool, as the code editions always have.

Eleven of the nineteen session zips are measures, and a bill LOB is a whole
measure; on one core they took most of a full build. The pool must give the
same rows as the serial reader, in the same order. The zip here is built to
shape; no measure is quoted.
"""

import zipfile

from us.ca import CaliforniaBills


def _row(cols):
    return '\t'.join('NULL' if col is None else '`%s`' % col for col in cols)


def _bills(path, count=5):
    """A 1989-style bills zip with ``count`` versions, each with its own LOB."""
    versions = []
    with zipfile.ZipFile(path, 'w') as zf:
        for n in range(count):
            version_id = '1989%dSCR198CHP' % n
            versions.append(_row([
                version_id, '198919901SCR%d' % n, '98', '1989-11-03 00:00:00', 'Chaptered', None,
                'Joint Rules %d.' % n, None, None, None, None, None, None, None,
                'BILL_VERSION_TBL_%d.lob' % n, 'Y', 'LEG_ESI', '2007-08-22 11:53:13',
            ]))
            zf.writestr('BILL_VERSION_TBL_%d.lob' % n, '<p>Rule number %d of the session.</p>' % n)
        zf.writestr('BILL_TBL.dat', _row(['198919901SCR1', 'bill']) + '\n')
        zf.writestr('BILL_VERSION_TBL.dat', '\n'.join(versions) + '\n')
        zf.writestr('BILL_VERSION_AUTHORS_TBL.dat', _row(['a']) + '\n')


FIELDS = ('PK', 'LAW_CODE', 'SECTION_NUM', 'LEGAL_TEXT', 'SESSION', 'SECTION_TITLE')


def _shape(rows):
    return [{key: row.get(key) for key in FIELDS} for row in rows]


def test_the_pool_gives_the_serial_rows_in_order(tmp_path):
    pub = tmp_path / 'pubinfo_1989.zip'
    _bills(pub)
    edition = CaliforniaBills()
    serial = _shape(edition.sections(pub))
    pooled = _shape(edition.parallel_sections(pub, workers=2, chunk_size=2))
    assert len(serial) == 5
    assert pooled == serial
    assert serial[0]['PK'] == '1989:19890SCR198CHP'
    assert serial[0]['LAW_CODE'] == 'BILL'
    assert 'Rule number 3' in serial[3]['LEGAL_TEXT']


def test_one_worker_is_the_serial_path(tmp_path):
    pub = tmp_path / 'pubinfo_1989.zip'
    _bills(pub, count=3)
    edition = CaliforniaBills()
    assert _shape(edition.parallel_sections(pub, workers=1)) == _shape(edition.sections(pub))
