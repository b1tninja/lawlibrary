"""Virginia Code — LIS law library per-title CSV."""

import csv
import os

import html2text

from publication import Publication, State

SOURCE = 'https://law.lis.virginia.gov/law-library/'
# Sample title CSV; annotations are excluded from this LIS export.
TITLE_1_CSV = 'https://law.lis.virginia.gov/CSV/CoVTitle_1.csv'


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html).strip()


class VirginiaCode(Publication):
    """One title CSV (Section, Body). Case annotations are not in the export."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8', errors='replace', newline='') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                number = (
                    row.get('Section')
                    or row.get('section')
                    or ''
                ).strip()
                body = (
                    row.get('Body')
                    or row.get('text')
                    or row.get('LEGAL_TEXT')
                    or ''
                )
                if not number and not body:
                    continue
                text = _html_to_text(body) if '<' in body else body.strip()
                yield {
                    'SECTION_NUM': number or os.path.splitext(
                        os.path.basename(path)
                    )[0],
                    'LEGAL_TEXT': text,
                    'SUBDIVISION': Virginia.code,
                }


class Virginia(State):
    code = 'US-VA'
    source = SOURCE
    editions = (VirginiaCode,)

    def list_editions(self):
        return [TITLE_1_CSV]
