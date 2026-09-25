"""Congress.gov advanced search, from the captured GET /search calls.

``q`` is a JSON object. The capture uses ``source`` (``all`` or
``legislation``), ``congress`` (a list of year-strings or one number), and
``search`` for a fielded query. ``pageSort`` is optional. The response is
the HTML results page.
"""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SEARCH = 'https://www.congress.gov/search'


def search_url(query, page_sort=None):
    """The captured search URL. ``query`` is the ``q`` object."""
    params = {'q': json.dumps(query, separators=(',', ':'))}
    if page_sort:
        params['pageSort'] = page_sort
    return '%s?%s' % (SEARCH, urlencode(params))


class Congress:
    """The Library of Congress search page. One method, the captured GET."""

    source = SEARCH

    def search(self, query, page_sort=None, opener=None):
        url = search_url(query, page_sort)
        if opener is None:
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(request, timeout=60) as response:
                return response.read()
        return opener(url)
