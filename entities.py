"""Governments and agencies the MCP can name.

A region is an ISO subdivision that legislates. A department is a political
body created by statute. It adopts rules. It does not get the region's
statute file.
"""

import os

from jurisdiction import subdivision
from corpus import cfr_corpus_path, corpus_path, corpus_path_for, manual_corpus_path

# Political bodies whose regulations we have already placed in a corpus.
# The Secretary of State roster is the full California list. These rows are
# the ones with a known publication.
DEPARTMENTS = (
    {'name': 'Office of the Law Revision Counsel', 'parent': 'US', 'instrument': 'statute', 'corpus': 'us'},
    {'name': 'Office of the Federal Register', 'parent': 'US', 'instrument': 'regulation', 'corpus': 'cfr'},
    {'name': 'Department of Housing and Urban Development', 'parent': 'US', 'instrument': 'regulation', 'corpus': 'cfr_24'},
    {'name': 'Department of Justice', 'parent': 'US', 'instrument': 'regulation', 'corpus': 'cfr_28'},
    {'name': 'Federal Emergency Management Agency', 'parent': 'US', 'instrument': 'regulation', 'corpus': 'cfr_44'},
    {'name': 'Federal Communications Commission', 'parent': 'US', 'instrument': 'regulation', 'corpus': 'cfr_47'},
    {'name': 'Environmental Protection Agency', 'parent': 'US', 'instrument': 'regulation', 'corpus': 'cfr_40'},
    {'name': 'Occupational Safety and Health Administration', 'parent': 'US', 'instrument': 'regulation', 'corpus': 'cfr_29'},
    {'name': 'Office of Administrative Law', 'parent': 'US-CA', 'instrument': 'regulation', 'corpus': None},
    {'name': 'Department of Real Estate', 'parent': 'US-CA', 'instrument': 'regulation', 'corpus': None},
    {'name': 'California Building Standards Commission', 'parent': 'US-CA', 'instrument': 'regulation', 'corpus': None},
)


def _region_row(code, kind):
    record = subdivision(code)
    return {
        'kind': kind,
        'code': code,
        'name': record.name,
        'parent': record.country_code if kind == 'state' else None,
        'regional': True,
        'political': False,
    }


def list_entities(kind=None):
    """Countries, states, localities, and departments."""
    from us import UnitedStates, load_states
    from us.ca import California

    rows = [{
        'kind': 'country',
        'code': UnitedStates.code,
        'name': 'United States',
        'parent': None,
        'regional': True,
        'political': False,
    }]
    for code in sorted(load_states()):
        rows.append(_region_row(code, 'state'))
    for _slug, county in sorted(California.counties().items()):
        rows.append({
            'kind': 'county',
            'code': None,
            'name': county.name,
            'parent': county.region(),
            'regional': False,
            'political': True,
        })
        for _city_slug, city in sorted(county.cities().items()):
            rows.append({
                'kind': 'city',
                'code': None,
                'name': city.name,
                'parent': county.name,
                'regional': False,
                'political': True,
            })
    for department in DEPARTMENTS:
        rows.append({
            'kind': 'department',
            'code': None,
            'name': department['name'],
            'parent': department['parent'],
            'regional': False,
            'political': True,
            'instrument': department['instrument'],
            'corpus': department['corpus'],
        })
    if kind:
        rows = [row for row in rows if row['kind'] == kind]
    return rows


def list_corpora(root=None):
    """Independent corpus files and whether each one is on disk."""
    from core import codes_dir
    root = str(codes_dir()) if root is None else root
    specs = [
        ('us', corpus_path('US', root=root), 'statute'),
        ('us_ca', corpus_path('US', 'US-CA', root=root), 'statute'),
    ]
    for title in (24, 28, 29, 40, 44, 47):
        specs.append(('cfr_%s' % title, cfr_corpus_path(title, root=root), 'regulation'))
    for book in ('OLRC', 'HOLC', 'GPO'):
        specs.append(('manual_%s' % book.lower(), manual_corpus_path(book, root=root), 'manual'))
    try:
        from us.ca.counties.sacramento.cities.sacramento import Sacramento
        specs.append(('sacramento', corpus_path_for(Sacramento, root=root), 'ordinance'))
    except ImportError:
        pass
    return [
        {'schema': alias, 'path': path, 'instrument': instrument, 'present': os.path.isfile(path)}
        for alias, path, instrument in specs
    ]
