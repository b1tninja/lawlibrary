# APA Style references

The default system is the California Style Manual. Sacramento courts file under California Rules of Court, and rule 8.204 encourages that manual. Outside a `with` block, `cite` writes the code name and the word "section", which is the form in the Fourth Appellate District self-help appendix on appellate.courts.ca.gov. `parse` reads that form, and also `Bus. & Prof. Code § 10050` and `BPC 10050`.

`identify` looks at the citation before choosing another system. A trailing `(year).` with a section sign is APA. A leading `Cal.` , `id.`, `supra`, or `U.S.C.` is The Bluebook. `Ibid.` is Chicago. A year, a jurisdiction, and a number, such as `2020 CA 5`, is the medium-neutral form. The Indigo Book and ALWD are chosen when the text names them. Those books are not copied. The Bluebook module adds `Cal.` before the shorthand. ALWD keeps the shorthand and the section sign. Chicago uses the Bluebook statute form, plus `Ibid.`

The style in force is a `with` block. The member is the system. Its value is the `Guide`.

```python
with CitationSystem.CaliforniaStyleManual:
    cite(Code.CIVIL, section('1940'))
```

Inside that block the reference is the California form, the code name and the word "section". `CitationSystem.APA` uses the reference-list pattern below. The blocks nest, and the inner block is the one in force. The official page for each manual, and whether it is posted free or sold, is [style-guides.md](style-guides.md).

Annotations taken while a block is open carry that `Guide` on `note.guide`.

## The reference-list pattern

APA Style legal references follow the pattern on the [APA Style site](https://apastyle.apa.org/style-grammar-guidelines/references/examples/clinical-practice-references): the name of the statute, the source, a section sign and the section numbers, then the year in parentheses. That page states the format does not use italics. The Publication Manual is not copied here.

`cite` takes a `Code` member and a span. A span is one section, a range, or a series. The year is the session of the code. When no session is passed, the year is left out.

| Call | Reference-list entry |
| --- | --- |
| `cite(Code.BUSINESS_AND_PROFESSIONS, section('10050', 'd'), session='2025')` | Business and Professions Code, Bus. & Prof. Code § 10050(d) (2025). |
| `cite(Code.CIVIL, span('4000', '6150'))` | Civil Code, Civ. Code §§ 4000-6150. |
| `cite(Code.CONSTITUTION, section('1'), article=Article.VI)` | California Constitution, art. VI, Cal. Const. § 1. |

The in-text forms use the printed name and the year: `(Business and Professions Code, 2025)` and `Business and Professions Code (2025)`. `index()` is the local key, `BPC 10050`. `Code.get('CIV')` returns the member. The shorthand is the source abbreviation on that member, such as `Bus. & Prof. Code` and `Civ. Code`.
