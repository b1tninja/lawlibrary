"""New Jersey Statutes — official STATUTES-TEXT.zip distribution."""

import os
import zipfile

from publication import Publication, State


SOURCE = 'https://pub.njleg.gov/statutes/STATUTES-TEXT.zip'


class NewJerseyStatutes(Publication):
    """Plain-text dump inside STATUTES-TEXT.zip (one .txt)."""

    @classmethod
    def accepts(cls, names):
        # Not California .dat tables; accept any zip this State is asked to open.
        return True

    def sections(self, path):
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                if os.path.splitext(name)[1].lower() != '.txt':
                    continue
                with zf.open(info) as fh:
                    text = fh.read().decode('utf-8', errors='replace')
                stem = os.path.splitext(os.path.basename(name))[0]
                yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text}
                return


class NewJersey(State):
    code = 'US-NJ'
    source = SOURCE
    editions = (NewJerseyStatutes,)

    def list_editions(self):
        return [SOURCE]
