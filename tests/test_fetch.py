"""A download stays on the host that publishes it, and a bad file is not kept."""

import threading
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from us.ca import PUBINFO_HOST, _fetch_pubinfo, _zip_intact
from us.ca.title24 import EDITIONS, fetch as fetch_edition
from utils import _on_host, read_url, save_url


def _server(handler):
    server = HTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_a_redirect_off_the_official_host_is_refused():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header('Location', 'https://example.invalid/pubinfo_2025.zip')
            self.end_headers()

        def log_message(self, fmt, *args):
            return

    server = _server(Handler)
    url = 'http://127.0.0.1:%s/pubinfo_2025.zip' % server.server_address[1]
    try:
        with pytest.raises(OSError, match='not an official source'):
            read_url(url, '127.0.0.1')
    finally:
        server.shutdown()


def test_a_short_body_is_not_a_complete_file(tmp_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = b'hi'
            self.send_response(200)
            self.send_header('Content-Length', '100')
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            return

    server = _server(Handler)
    url = 'http://127.0.0.1:%s/file' % server.server_address[1]
    dest = tmp_path / 'file'
    try:
        with pytest.raises(OSError, match='short read'):
            save_url(url, dest, '127.0.0.1')
    finally:
        server.shutdown()


def test_a_bad_pubinfo_zip_is_retrieved_again(tmp_path, monkeypatch):
    dest = tmp_path / 'pubinfo_2025.zip'
    dest.write_text('<html>not a zip</html>', encoding='utf-8')

    def save(url, path, host):
        assert host == PUBINFO_HOST
        assert url.endswith('/pubinfo_2025.zip')
        with zipfile.ZipFile(path, 'w') as zf:
            zf.writestr('CODES_TBL.dat', 'CIV\n')

    monkeypatch.setattr('utils.save_url', save)
    got = _fetch_pubinfo(2025, tmp_path)
    assert _zip_intact(got)
    assert not (tmp_path / 'pubinfo_2025.zip.partial').exists()


def test_an_html_page_is_not_kept_as_edition_text(tmp_path, monkeypatch):
    chosen = next(edition for edition in EDITIONS if edition.year == '2025')
    folder = tmp_path / 'title24'
    folder.mkdir()
    path = folder / chosen.filename
    path.write_bytes(b'<!DOCTYPE html><p>gone</p>')

    def body(url, host):
        assert host == 'archive.org'
        assert url == chosen.text_url
        return b'903.3.1.1 sprinklers\n'

    monkeypatch.setattr('utils.read_url', body)
    saved = fetch_edition(chosen, dest=folder)
    assert saved == str(path)
    assert b'sprinklers' in path.read_bytes()


def test_the_commission_host_is_the_only_one_read():
    import succession
    with pytest.raises(OSError, match='not an official source'):
        succession._open_url('https://example.invalid/table.pdf')


def test_a_storage_subdomain_is_on_the_host_and_a_lookalike_is_not():
    """The Internet Archive redirects a download to a numbered storage host."""
    stored = 'https://dn790003.ca.archive.org/0/items/x/x_djvu.txt'
    assert _on_host(stored, ('archive.org',))
    assert _on_host('https://archive.org/download/x', ('archive.org',))
    assert not _on_host('https://evilarchive.org/x', ('archive.org',))
    assert not _on_host('https://archive.org.example.invalid/x', ('archive.org',))
    assert not _on_host('https://example.invalid/archive.org', ('archive.org',))


def test_a_redirect_that_stays_on_the_host_is_followed():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/start':
                self.send_response(302)
                self.send_header('Location', '/there')
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'ok')

        def log_message(self, fmt, *args):
            return

    server = _server(Handler)
    try:
        assert read_url('http://127.0.0.1:%s/start' % server.server_address[1], '127.0.0.1') == b'ok'
    finally:
        server.shutdown()
