"""Congress.gov search URL, from the captured query. No network."""

import json
from urllib.parse import parse_qs, urlsplit

from us.congress import search_url


def test_advanced_search_uses_the_captured_query():
    url = search_url(
        {'source': 'legislation', 'search': 'isBillByRequest:"Y"', 'congress': 119},
        page_sort='latestAction:desc',
    )
    query = parse_qs(urlsplit(url).query)
    assert json.loads(query['q'][0]) == {
        'source': 'legislation',
        'search': 'isBillByRequest:"Y"',
        'congress': 119,
    }
    assert query['pageSort'] == ['latestAction:desc']
    listed = search_url({'congress': ['119'], 'source': 'all'})
    assert json.loads(parse_qs(urlsplit(listed).query)['q'][0])['source'] == 'all'
