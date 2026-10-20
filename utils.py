import os
import os.path
import urllib.parse
import urllib.request

from config import logger

# TODO googletrans


def _hosts(host):
    """Hostnames a fetch may land on. One name, or several spellings of it."""
    names = host if isinstance(host, (tuple, list, set)) else (host,)
    return tuple(name.lower() for name in names)


def _hostname(url):
    return (urllib.parse.urlsplit(url).hostname or '').lower()


def open_official(url, host):
    """Open ``url``. A redirect that leaves ``host`` is refused.

    The caller closes the response. ``host`` is a hostname, or several
    spellings of the same body (``clrc.ca.gov`` and ``www.clrc.ca.gov``).
    """
    allowed = _hosts(host)
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ('http', 'https') or _hostname(url) not in allowed:
        raise OSError('not an official source: %s' % url)

    class Stay(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if urllib.parse.urlsplit(newurl).scheme not in ('http', 'https') or _hostname(newurl) not in allowed:
                raise OSError('not an official source: %s' % newurl)
            return urllib.request.HTTPRedirectHandler.redirect_request(
                self, req, fp, code, msg, headers, newurl,
            )

    opener = urllib.request.build_opener(Stay)
    request = urllib.request.Request(url, headers={'User-Agent': 'lawlibrary'})
    response = opener.open(request, timeout=120)
    if _hostname(response.geturl()) not in allowed:
        response.close()
        raise OSError('not an official source: %s' % response.geturl())
    return response


def read_url(url, host):
    """The bytes at ``url``. A redirect that leaves ``host`` is refused."""
    with open_official(url, host) as response:
        return response.read()


def save_url(url, dest, host):
    """Write ``url`` to ``dest``. A short body is refused when the server named a length."""
    with open_official(url, host) as response, open(dest, 'wb') as out:
        expected = response.headers.get('Content-Length')
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            total += len(chunk)
    if expected is not None and int(expected) != total:
        raise OSError('short read of %s' % url)
    return total


def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)
        logger.info(f"Creating {os.path.basename(path)} folder.")
        return True
    else:
        assert os.path.isdir(path)
        return False

