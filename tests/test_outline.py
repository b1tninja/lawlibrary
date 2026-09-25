from outline import Margin, Roman, format_roman
from structure import split_nodes


def test_a_roman_numeral_is_its_value():
    assert Roman.read('XIV').value == 14
    assert Roman.read('xiv').value == 14
    assert format_roman(14) == 'XIV'
    assert Roman.read('XXXIV').value == 34
    assert Roman.read('IIII') is None
    assert Roman.read('VV') is None


def test_a_deeper_indent_is_a_child():
    text = '(a) Courts.\n  (1) Trial.\n    (A) Civil.\n(b) Appeal.'
    root = split_nodes(text)
    letter = root.children[0]
    assert letter.label == '(a)'
    assert letter.children[0].label == '(1)'
    assert letter.children[0].children[0].label == '(A)'
    assert root.children[1].label == '(b)'
    assert letter.margin.spaces == 0
    assert letter.children[0].margin.spaces == 2


def test_a_margin_counts_spaces_and_tabs():
    assert Margin.read('  (a)').spaces == 2
    assert Margin.read('\t(a)').tabs == 1
    assert Margin.read('\t(a)') > Margin.read('  (a)')
