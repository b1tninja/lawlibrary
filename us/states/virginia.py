"""Virginia Code — LIS law library per-title CSV."""

import csv

import html2text

from publication import Publication, State
SOURCE = 'https://law.lis.virginia.gov/law-library/'
# Sample title CSV; annotations are excluded from this LIS export.
TITLE_1_CSV = 'https://law.lis.virginia.gov/CSV/CoVTitle_1.csv'
BOOK = 'VAC'

# CSV columns that match a LawSchema level. Subtitle and subpart have no field.
_LADDER = (
    ('TitleNum', 'TITLE'),
    ('TitleName', 'TITLE_HEADING'),
    ('PartNum', 'PART'),
    ('PartName', 'PART_HEADING'),
    ('ChapterNum', 'CHAPTER'),
    ('ChapterName', 'CHAPTER_HEADING'),
    ('ArticleNum', 'ARTICLE'),
    ('ArticleName', 'ARTICLE_HEADING'),
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html).strip()


def _csv_rows(path):
    """One section per CSV record, with the title-to-article columns kept."""
    with open(path, encoding='utf-8', errors='replace', newline='') as fh:
        for raw in csv.DictReader(fh):
            number = (raw.get('Section') or raw.get('section') or '').strip()
            body = raw.get('Body') or raw.get('text') or raw.get('LEGAL_TEXT') or ''
            if not number:
                continue
            text = _html_to_text(body) if '<' in body else body.strip()
            row = {
                'SECTION_NUM': number,
                'LEGAL_TEXT': text,
                'SUBDIVISION': Virginia.code,
                'LAW_CODE': BOOK,
            }
            for source, field in _LADDER:
                value = (raw.get(source) or '').strip()
                if value:
                    row[field] = value
            catch = (raw.get('Title') or '').strip()
            if catch:
                row['SECTION_TITLE'] = catch
            yield row


class VirginiaCode(Publication):
    code_heading = 'Code of Virginia'
    """One title CSV (Section, Body). Case annotations are not in the export."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        yield from _csv_rows(path)


class Virginia(State):
    code = 'US-VA'
    source = SOURCE
    editions = (VirginiaCode,)

    def list_editions(self):
        return [TITLE_1_CSV]
