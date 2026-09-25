"""Texas Statutes — Legislative Council HTML downloads."""

import os
import tempfile
import zipfile

from publication import Publication, State
from readers import html_sections

SOURCE = 'https://statutes.capitol.texas.gov/download'
# Per-code HTML zips: FileServerPath + /Zips/{CODE}.htm.zip from StatuteCodeDownloads.json.
FILE_SERVER = 'https://tcss.legis.texas.gov/resources'
DOWNLOADS_JSON = 'https://statutes.capitol.texas.gov/assets/StatuteCodeDownloads.json'

# Sec. 1.001 / Section 1.001 in HTML2Text output.
_SECTION_PATTERN = r'(?i)(?:Sec\.|Section)\s*(\d+\.\d+(?:\.\d+)?)'


def _book_token(path):
    """Short LAW_CODE from AG.htm.zip, an AG/ folder, or a chapter stem."""
    name = os.path.basename(str(path).rstrip('/\\'))
    lower = name.lower()
    if lower.endswith('.htm.zip') or lower.endswith('.html.zip'):
        return name.split('.', 1)[0].upper()
    if lower.endswith('.zip'):
        return os.path.splitext(name)[0].upper()
    parent = os.path.basename(os.path.dirname(str(path)))
    if parent and parent.upper() not in ('US-TX', 'HTM', 'HTML', 'ZIPS'):
        if len(parent) <= 4 and parent.replace('-', '').isalnum():
            return parent.upper()
    stem = os.path.splitext(name)[0]
    if '.' in stem:
        return stem.split('.', 1)[0].upper()
    return stem.upper() or 'TX'


def _stamp(row, law_code):
    row = dict(row)
    row['SUBDIVISION'] = Texas.code
    row['LAW_CODE'] = law_code
    row['PK'] = '%s:%s' % (law_code, row['SECTION_NUM'])
    return row


class TexasStatutes(Publication):
    """Per-code HTML zip, an unzipped chapter folder, or one chapter HTML file."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        law_code = _book_token(path)
        if os.path.isdir(path):
            for root, _dirs, files in os.walk(path):
                for name in sorted(files):
                    if name.lower().endswith(('.htm', '.html')):
                        for row in html_sections(os.path.join(root, name), _SECTION_PATTERN):
                            yield _stamp(row, law_code)
            return
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    if not info.filename.lower().endswith(('.htm', '.html')):
                        continue
                    data = zf.read(info.filename)
                    suffix = os.path.splitext(info.filename)[1] or '.htm'
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                        tmp.write(data)
                        tmp_path = tmp.name
                    try:
                        for row in html_sections(tmp_path, _SECTION_PATTERN):
                            yield _stamp(row, law_code)
                    finally:
                        os.unlink(tmp_path)
            return
        for row in html_sections(path, _SECTION_PATTERN):
            yield _stamp(row, law_code)


class Texas(State):
    code = 'US-TX'
    source = SOURCE
    editions = (TexasStatutes,)

    def list_editions(self):
        return [SOURCE]
