from apa import Code, parse
from places import Citation

from structure import Diagram, Gap, _chart, _follows, code_chart, enactment_chart, find_links, inspect, markdown, related, review, split_nodes


def _text(code, number):
    text = Citation(code).section(number).text
    return text or None


def _open(citation):
    ref = parse(citation)
    return _text(ref.code, ref.span.numbers[0])


def _node(root, label):
    return next(node for node in root.walk() if node.label == label)


def test_depth_zero_stops_and_a_missing_depth_follows_until_a_repeat():
    assert _follows(0) is False
    assert _follows(1) is True
    assert _follows(None) is True
    assert _follows(-1) is True


def test_a_section_parenthetical_becomes_the_subdivision_chain():
    """Section 4600(b)(1) of the Civil Code is the citation closure, not a bare number."""
    links = find_links('Section 4600(b)(1) of the Civil Code')
    statute = next(link for link in links if link.section == '4600')
    assert statute.labels == ('b', '1')
    assert statute.citation().reference() == (
        'Civil Code section 4600, subdivision (b), paragraph (1)'
    )


def test_letters_hold_numbered_paragraphs():
    text = _text(Code.CIVIL, '1940')
    if text is None:
        return
    root = split_nodes(text)
    letter = _node(root, '(b)')
    assert _node(root, '(a)').children == []
    assert [child.label for child in letter.children] == ['(1)', '(2)']


def test_a_code_named_after_the_section_is_a_link():
    text = _text(Code.CIVIL, '1940')
    if text is None:
        return
    links = find_links(text, here=Code.CIVIL)
    assert any(link.kind == 'statute' and link.code is Code.REVENUE_AND_TAXATION and link.section == '7280' for link in links)
    assert not any(link.kind == 'statute' and link.code is Code.CIVIL and link.section == '728' for link in links)
    assert any(link.kind == 'subdivision' and link.label == 'b' for link in links)
    assert any(link.kind == 'internal' and link.text == 'this chapter' for link in links)


def test_a_bare_section_stays_in_the_open_code():
    text = _text(Code.CIVIL, '1940')
    if text is None:
        return
    links = find_links(text, here=Code.CIVIL)
    assert any(link.code is Code.CIVIL and link.section == '1860' for link in links)
    assert any(link.kind == 'internal' and link.text == 'this section' for link in links)


def test_a_federal_code_is_not_a_california_section():
    text = _text(Code.CIVIL, '1812.300')
    if text is None:
        return
    links = [link for link in find_links(text, here=Code.CIVIL) if link.kind == 'statute']
    assert not any(link.code is Code.CIVIL and link.section == '501' for link in links)


def test_a_double_letter_and_a_marked_letter_are_subdivisions():
    text = _text(Code.BUSINESS_AND_PROFESSIONS, '11212')
    if text is None:
        return
    labels = [node.label for node in split_nodes(text).walk()]
    assert '(_l_)' in labels
    assert '(aa)' in labels


def test_plural_subdivisions_are_each_a_label():
    text = _text(Code.HEALTH_AND_SAFETY, '17951')
    if text is None:
        return
    root = split_nodes(text)
    node = next(item for item in root.walk() if 'subdivisions (a) and (b)' in item.text)
    labels = [link.label for link in find_links(node.text, here=Code.HEALTH_AND_SAFETY) if link.kind == 'subdivision']
    assert labels == ['a', 'b']


def test_stacked_labels_on_one_line_nest():
    text = _text(Code.REVENUE_AND_TAXATION, '7280')
    if text is None:
        return
    letter = _node(split_nodes(text), '(e)')
    assert letter.children[0].label == '(1)'
    assert letter.children[0].children[0].label == '(A)'


def test_a_colon_introduces_a_numbered_list():
    text = _text(Code.BUSINESS_AND_PROFESSIONS, '11212')
    if text is None:
        return
    letter = _node(split_nodes(text), '(_l_)')
    assert [child.label for child in letter.children] == ['(1)', '(2)', '(3)']


def test_a_clause_list_stays_a_reference():
    text = _text(Code.REVENUE_AND_TAXATION, '7280')
    if text is None:
        return
    letter = _node(split_nodes(text), '(C)')
    assert [child.label for child in letter.children] == []


def test_the_code_of_civil_procedure_is_that_book():
    spelled = _text(Code.CIVIL, '937')
    if spelled is None:
        return
    links = find_links(spelled, here=Code.CIVIL)
    assert any(
        link.code is Code.CIVIL_PROCEDURE and link.section == '411.35' for link in links
    )
    assert not any(link.code is Code.CIVIL and link.section == '411.35' for link in links)
    comma = _text(Code.CIVIL, '1201')
    if comma is None:
        return
    links = find_links(comma, here=Code.CIVIL)
    assert any(
        link.code is Code.CIVIL_PROCEDURE and link.section == '2093' for link in links
    )


def test_review_cites_the_section_and_the_test_looks_it_up():
    federal = review(Code.CIVIL, '1812.300', depth=0)
    if not federal.get('found'):
        return
    gap = next(item for item in federal['gaps'] if item['gap'] is Gap.UNRESOLVED)
    assert gap['citation'] == 'Civil Code section 1812.300'
    assert _open(gap['citation'])
    spelled = review(Code.CIVIL, '937', depth=0)
    if spelled.get('found'):
        assert not any(item['gap'] is Gap.SHORT_TITLE for item in spelled['gaps'])


def test_words_after_a_code_title_are_not_a_longer_book():
    """CCP 1161. Words after Civil Code stay prose. The section link remains."""
    text = _text(Code.CIVIL_PROCEDURE, '1161')
    if text is None:
        return
    assert not any(item['gap'] is Gap.SHORT_TITLE for item in inspect(text, here=Code.CIVIL_PROCEDURE))
    links = find_links(text, here=Code.CIVIL_PROCEDURE)
    assert any(link.code is Code.CIVIL and link.section == '1946' for link in links)


def test_a_history_credit_is_a_session_chapter():
    """Stats. year, Ch. chapter, Sec. act is the enrolled bill, not a code section."""
    links = find_links('Repealed and added by Stats. 1985, Ch. 874, Sec. 14.')
    credit = next(link for link in links if link.kind == 'session')
    law = credit.session
    from needles import Action
    assert credit.action is Action.REPEALED_AND_ADDED
    assert law.year == '1985'
    assert law.chapter == '874'
    assert law.act == '14'
    assert law.reference() == 'Section 14 of Chapter 874 of the Statutes of 1985'


def test_a_session_link_keeps_the_act_section_off_the_code():
    """Section 1 of the chapter is the enrolled bill, not a code section."""
    links = find_links('Section 1 of Chapter 387 of the Statutes of 1913')
    law = links[0].citation()
    assert links[0].section is None
    assert law.act == '1'
    assert law.reference() == 'Section 1 of Chapter 387 of the Statutes of 1913'


def test_a_chapter_of_the_statutes_is_recorded():
    cases = (
        ('Revenue and Taxation Code section 7280', '257', '1985'),
        ('Welfare and Institutions Code section 14043.26', '693', '2007'),
        ('Fish and Game Code section 8681.5', '94', '1992'),
    )
    for citation, chapter, year in cases:
        ref = parse(citation)
        text = _text(ref.code, ref.span.numbers[0])
        if text is None:
            return
        links = find_links(text, here=ref.code)
        assert any(
            link.kind == 'session' and link.section is None and link.label is None
            and link.session.chapter == chapter and link.session.year == year
            for link in links
        )
        gaps = review(ref.code, ref.span.numbers[0], depth=0).get('gaps') or []
        assert not any(gap['gap'] is Gap.UNLINKED and 'Statutes' in gap['phrase'] for gap in gaps)


def test_the_internal_revenue_code_stays_unresolved():
    cases = (
        ('Civil Code section 1812.300', '501'),
        ('Labor Code section 3352', '101'),
    )
    for citation, number in cases:
        ref = parse(citation)
        text = _text(ref.code, ref.span.numbers[0])
        if text is None:
            return
        links = find_links(text, here=ref.code)
        named = [link for link in links if link.kind == 'statute' and link.section == number]
        assert named
        assert all(link.code is None for link in named)
        assert not any(link.code is ref.code and link.section == number for link in links)


def test_a_comma_before_this_code_is_not_a_citation():
    ref = parse('Fish and Game Code section 8597')
    if _text(ref.code, ref.span.numbers[0]) is None:
        return
    gaps = review(ref.code, ref.span.numbers[0], depth=0).get('gaps') or []
    assert not any('8598.2' in gap['phrase'] for gap in gaps)


def test_a_section_of_an_article_keeps_the_article():
    import sample
    drawn = sample.sample('CONS', n=20, pattern='of Article', seed=1659537390)
    if not drawn.get('found'):
        return
    articles = []
    for sec in drawn['sections']:
        for link in find_links(sec['text'], here=Code.CONSTITUTION):
            if link.kind == 'article':
                articles.append((link.label, link.section, link.code))
                assert link.text in sec['text'] or link.text.lower() in sec['text'].lower()
    assert ('XVI', '8', Code.CONSTITUTION) in articles
    assert ('II', '8', Code.CONSTITUTION) in articles
    assert ('II', '9', Code.CONSTITUTION) in articles
    glued = sample.sample('CONS', n=20, pattern='Article XIIIA', seed=155773146)
    if glued.get('found'):
        found = False
        for sec in glued['sections']:
            for link in find_links(sec['text'], here=Code.CONSTITUTION):
                if link.kind == 'article' and link.label == 'XIII A' and link.section == '4':
                    found = True
        assert found
    host = next(sec for sec in drawn['sections'] if 'Article XVI' in sec['text'])
    bare = [
        link for link in find_links(host['text'], here=Code.CONSTITUTION)
        if link.kind == 'statute' and link.section == '8'
    ]
    assert bare == []


def test_same_code_does_not_open_another_book():
    tree = related(Code.CIVIL, '1940', depth=1, same=True)
    if not tree.get('found'):
        return
    assert any(link['code'] is Code.REVENUE_AND_TAXATION for link in tree['links'])
    assert all(child['id'].startswith('CIV ') for child in tree['children'])
    assert any(child['id'] == 'CIV 1860' for child in tree['children'])
    opened = related(Code.CIVIL, '1940', depth=1, codes=(Code.CIVIL, Code.REVENUE_AND_TAXATION))
    assert any(child['id'] == 'RTC 7280' for child in opened['children'])


def test_a_roman_heading_is_its_own_rank():
    root = split_nodes('IV. The judicial power.\n(a) Courts of record.')
    assert root.children[0].label == 'IV.'
    assert root.children[0].children[0].label == '(a)'


def test_spans_nests_articles_and_this_chapter_rebuild_the_chain():
    """Lookup locators only. The printed form and the link are the same citation."""
    from apa import parse
    ranged = find_links('Sections 1119 to 1124 of the Civil Code')
    assert ranged[0].citation().reference() == 'Civil Code sections 1119 to 1124'
    opened = find_links('commencing with Section 11340', here=Code.GOVERNMENT)
    assert opened[0].citation().reference() == 'Government Code, commencing with Section 11340'
    host = _text(Code.CIVIL, '1940')
    if host:
        chapter = next(
            link for link in find_links(host, here=Code.CIVIL)
            if link.kind == 'internal' and link.text.casefold() == 'this chapter'
        )
        assert chapter.resolve('1940').reference() == 'Chapter 2 of the Civil Code'
    article = find_links('Section 4 of Article XIII A')
    assert article[0].citation().reference() == (
        'California Constitution, article XIII A, section 4'
    )
    assert parse(article[0].citation().reference()).span.subdivision is None
    nest = find_links('subdivision (b)(1) of Section 12867', here=Code.WATER)
    stacked = next(link for link in nest if link.labels == ('b', '1'))
    assert stacked.citation().reference() == (
        'Water Code section 12867, subdivision (b), paragraph (1)'
    )
    worded = find_links(
        'paragraph (1) of subdivision (b) of Section 12867', here=Code.WATER,
    )
    assert any(link.labels == ('b', '1') for link in worded)
    series = [
        link for link in find_links(
            'subdivisions (a) and (b) of Section 12867', here=Code.WATER,
        )
        if link.kind == 'subdivision'
    ]
    assert [link.label for link in series] == ['a', 'b']


def test_a_subsection_of_another_section_names_that_section():
    text = _text(Code.WATER, '12872')
    if text is None:
        return
    links = find_links(text, here=Code.WATER)
    assert any(
        link.kind == 'subdivision' and link.label == 'd' and link.section == '12867'
        for link in links
    )
    assert any(
        link.kind == 'subdivision' and link.label == 'f' and link.section == '12868'
        for link in links
    )


def test_related_follows_one_hop_and_draws_the_chart():
    tree = related(Code.CIVIL, '1940', depth=1)
    if not tree.get('found'):
        return
    assert any(link['code'] is Code.REVENUE_AND_TAXATION and link['section'] == '7280' for link in tree['links'])
    assert 'flowchart TD' in tree['mermaid']
    assert 'CIV1940' in tree['mermaid']
    rtc = next(child for child in tree['children'] if child['id'] == 'RTC 7280')
    assert rtc['found'] is True
    assert rtc['children'] == []


def test_a_chart_is_a_markdown_page():
    books = code_chart([('CIV', 'INS 533'), ('CIV', 'RTC 7280'), ('INS', 'CIV 1714.1')])
    page = markdown('Code citations', books)
    assert page.startswith('# Code citations')
    assert '```mermaid' in page
    assert 'CIV -->|cites| INS' in page
    assert 'CIV -->|cites| RTC' in page
    enacted = enactment_chart([('WAT 8681.5', '1985 257')])
    assert 'WAT86815 -->|enacted| 1985257' in enacted
    vesting = Diagram.vesting().code(Code.GOVERNMENT)
    assert vesting.kind == 'vesting'
    assert vesting.book is Code.GOVERNMENT
    assert Diagram.codes().page().startswith('# Code citations')
    assert Diagram.around('CIV 1714.1').kind == 'references'
    orphan = _chart([], 'vested', nodes=['Coastal Commission'])
    assert 'Coastal Commission' in orphan
    assert '-->' not in orphan
