# Citation and drafting shapes for the lexer

Patterns a parser must recognize in statute and court prose. Built from official government pages opened for this note, plus the section-sign and signal facts already in [citations.md](citations.md). Inventory of which manuals exist on official hosts: [courts/manuals.md](../courts/manuals.md).

Do not invent Bluebook or California Style Manual rules here. Rule 1.200 names those manuals; their full text was not opened on an official free host.

## Court rule that names the style manuals

| Field | Value |
| --- | --- |
| Official page | [California Rules of Court, rule 1.200](https://courts.ca.gov/cms/rules/index/one/rule1_200) |
| Fact | Documents filed in California courts must follow either the California Style Manual or The Bluebook, used consistently |
| Lexer note | Detects citation *shapes*, not which optional manual the filer chose |

## Section sign

Already fixed in [citations.md](citations.md). Official pages also print the mark.

| Shape | Pattern | Official page |
| --- | --- | --- |
| One section | `§` or `section` + one number (+ optional `(a)` / `(b)`…) | [1 U.S.C. positive-law citation form on govinfo](https://www.govinfo.gov/content/pkg/USCODE-2024-title1/html/USCODE-2024-title1.htm) (`1 U. S. C., §——.`); GPO Style Manual [ch. 10](https://www.govinfo.gov/content/pkg/GPO-STYLEMANUAL-2016/pdf/GPO-STYLEMANUAL-2016.pdf) uses `§` with a thin space before a figure |
| Range | `§§` / `sections` + dash or `to` | Same sign rules as citations.md; OLRC shows ranges via `et seq.` after a starting section (below) |
| Series | `§§` / `sections` + commas or `and` | Same as citations.md |
| Footnote reference mark | `§` as a symbol in a footnote-mark sequence | GPO Style Manual [ch. 15](https://www.govinfo.gov/content/pkg/GPO-STYLEMANUAL-2016/pdf/GPO-STYLEMANUAL-2016.pdf) (section mark in the symbol sequence) — not a statute cite by itself |

`§` is not the start of `§§`. Read the double sign first.

## United States Code

| Shape | Pattern | Official page |
| --- | --- | --- |
| Compact title-section | `{title} U.S.C. {section}` | GPO Style Manual ch. 9: `18 U.S.C. 38`; abbreviation list `U.S.C.—United States Code` ([2016 PDF](https://www.govinfo.gov/content/pkg/GPO-STYLEMANUAL-2016/pdf/GPO-STYLEMANUAL-2016.pdf)); OFR [1 CFR 21.52](https://www.ecfr.gov/current/title-1/chapter-I/subchapter-E/part-21/subpart-B) example `10 U.S.C. 501` |
| Positive-law form with section sign | `{title} U. S. C., §——.` | Positive-law note on [Title 1](https://www.govinfo.gov/content/pkg/USCODE-2024-title1/html/USCODE-2024-title1.htm) |
| Drafting long form | `section {n} of title {t}, United States Code` | [House Legislative Counsel Manual on Drafting Style (Dec 2022)](https://legcounsel.house.gov/sites/evo-subsites/legcounsel-evo.house.gov/files/documents/ManualDraftStyle_2022.pdf) § 341(b)(1) |
| Parenthetical Code cite | `( {title} U.S.C. {section} )` | Same manual § 341(c); OLRC [Detailed Guide](https://uscode.house.gov/detailed_guide.xhtml) (parentheses = usually in the underlying act) |
| Editorial bracketed cite | `[ {title} U.S.C. {section} et seq. ]` | OLRC Detailed Guide (square brackets = editorially inserted) |
| Appendix | `{title} U.S.C. App.` | House Manual § 341(c)(4): `(5 U.S.C. App.)` |
| Note classification | `{title} U.S.C. {section} note` | House Manual § 342 examples (`5 U.S.C. 3301 note`, `17 U.S.C. 104 note`) |
| Supplement | `U.S.C. Supp.` / `U.S.C., Sup.` | GPO abbreviation list; [1 U.S.C. § 204](https://www.govinfo.gov/content/pkg/USCODE-2024-title1/html/USCODE-2024-title1.htm) citation forms for supplements |
| Following sections | `{title} U.S.C. {section} et seq.` | OLRC Detailed Guide example `[42 U.S.C. 1396 et seq.]` |

House drafting also uses short-title + parenthetical Code cite when the title is not positive law (`section 5 of the Federal Trade Commission Act (15 U.S.C. 45)` style): same § 341 / Quick Guide on [legcounsel.house.gov](https://legcounsel.house.gov/).

## Code of Federal Regulations

| Shape | Pattern | Official page |
| --- | --- | --- |
| Compact title-part.section | `{title} CFR {part}.{section}` | [GovInfo CFR help](https://www.govinfo.gov/help/cfr): title left of `CFR`, part right of `CFR` before `.`, section after `.` — e.g. `21 CFR 310.502` |
| Parallel FR form | `{title} CFR {section} ({vol} FR {page})` | [1 CFR 21.23](https://www.ecfr.gov/current/title-1/chapter-I/subchapter-E/part-21/subpart-A/subject-group-ECFR095b3363a246648/section-21.23): `___ CFR ___ (___ FR ___)` |
| Part cite | `{title} CFR part {part}` / `{title} CFR Part {part}` | GovInfo help (part-level retrieval); 1 CFR 21.53 example `14 CFR part 4b` |
| Drafting long form | `section {part}.{section} of title {t}, Code of Federal Regulations` | House Manual § 342(c)(1) |
| Parenthetical with periods | `( {title} C.F.R. {part}.{section} )` | House Manual § 342(c)(2)(B) example `49 C.F.R. 571.208` |
| GPO initialism | `CFR` / `CFR Supp.` | GPO Style Manual 2016 abbreviation tables |

Most CFR citations are at the section level (GovInfo help). Subpart letters (`Subpart E`) retrieve a whole subpart, not one section.

## California codes (Legislature abbreviations)

Use the codes as printed on the Legislature’s site, not a vendor’s reporter abbreviations.

| Full name (as listed) | Token | Official page |
| --- | --- | --- |
| California Constitution | `CONS` | [leginfo Code Search](https://leginfo.legislature.ca.gov/faces/codes.xhtml) |
| Business and Professions Code | `BPC` | same |
| Civil Code | `CIV` | same; Civil Code § 21 allows designation as “The Civil Code” + section number ([display](https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CIV)) |
| Code of Civil Procedure | `CCP` | Code Search |
| Commercial Code | `COM` | same |
| Corporations Code | `CORP` | same |
| Education Code | `EDC` | same |
| Elections Code | `ELEC` | same |
| Evidence Code | `EVID` | same |
| Family Code | `FAM` | same |
| Financial Code | `FIN` | same |
| Fish and Game Code | `FGC` | same |
| Food and Agricultural Code | `FAC` | same |
| Government Code | `GOV` | same |
| Harbors and Navigation Code | `HNC` | same |
| Health and Safety Code | `HSC` | same |
| Insurance Code | `INS` | same |
| Labor Code | `LAB` | same |
| Military and Veterans Code | `MVC` | same |
| Penal Code | `PEN` | same |
| Probate Code | `PROB` | same |
| Public Contract Code | `PCC` | same |
| Public Resources Code | `PRC` | same |
| Public Utilities Code | `PUC` | same |
| Revenue and Taxation Code | `RTC` | same |
| Streets and Highways Code | `SHC` | same |
| Unemployment Insurance Code | `UIC` | same |
| Vehicle Code | `VEH` | same |
| Water Code | `WAT` | same |
| Welfare and Institutions Code | `WIC` | same |

Lexer shapes already treated as one book in [citations.md](citations.md): full name (`Civil Code`), catalog form (`Civil Code - CIV`), and bare token (`CIV`). Spelled-out “Gov. Code” / “Civ. Code” court short forms are Style Manual / Bluebook territory and were **not** taken from a copied manual; resolve them only when the catalog already maps them.

## Short forms

| Token | Role for the lexer | Official page |
| --- | --- | --- |
| `id.` | Same authority as the last cite | GPO Style Manual Latin abbreviations (`id.—(idem) the same`); ch. 11 lists `id.` among citation abbreviations |
| `ibid.` | Same place (print style) | Same Latin list (`ibid.—(ibidem)`) |
| `supra` | Earlier full cite | GPO ch. 9.49: *infra* and *supra* are not abbreviated; ch. 11.3: italicize in legal citation context |
| `et seq.` | This section and the following | GPO Latin list; OLRC Detailed Guide in Code cites |
| `hereinafter` / `hereafter` | Forward definition / naming | House Manual rejects both in parenthetical definitions (§ 326 note); still appears in older statutory text — recognize as a short-form marker, do not invent Bluebook usage |

These are the short-form marks already named in [citations.md](citations.md) (`id.`, `supra`, `et seq.`). Do not expand them from The Bluebook or the California Style Manual.

## Signals (point of authority)

Already implemented; roles are in [citations.md](citations.md). Patterns only:

| Signal | Pattern notes | Official footing |
| --- | --- | --- |
| `see` | Word before the cite | GPO ch. 11.11 italics *See* / *see also* in indexes and TOC only — not a citation-manual rule |
| `see also` | Two words | Same |
| `cf.` | Abbreviation with period | Not defined on the government pages opened for this note; keep as implemented signal |
| `but see` | Two words | Implemented; not redefined from a private manual |
| `accord` | One word | Implemented |
| `contra` | One word | Implemented |
| `e.g.` | Abbreviation | GPO Latin list: `e.g.—(exempli gratia) for example` |

A signal introduces a point of authority; it is not the source.

## Related drafting shapes (federal bills)

Useful when the lexer sees amendatory or cross-reference prose, not court briefs:

| Shape | Pattern | Official page |
| --- | --- | --- |
| Public Law | `Public Law {congress}-{number}` / `Pub. L.` | House Manual § 341; GPO `Public Law 85−1` |
| Statutes at Large | `{vol} Stat. {page}` | House Manual; GPO `Stat. L.` |
| Internal “such” back-reference | `such` + unit after a full cite in the same section | House Manual § 341(h) |

## Pages opened

| Host | Page |
| --- | --- |
| courts.ca.gov | [Rule 1.200](https://courts.ca.gov/cms/rules/index/one/rule1_200) |
| govinfo.gov | [GPO Style Manual 2016](https://www.govinfo.gov/content/pkg/GPO-STYLEMANUAL-2016/pdf/GPO-STYLEMANUAL-2016.pdf) (chs. 9–11, 15); [CFR help](https://www.govinfo.gov/help/cfr); [USCODE-2024-title1](https://www.govinfo.gov/content/pkg/USCODE-2024-title1/html/USCODE-2024-title1.htm) |
| uscode.house.gov | [Detailed Guide](https://uscode.house.gov/detailed_guide.xhtml) |
| legcounsel.house.gov | [Manual on Drafting Style (Dec 2022)](https://legcounsel.house.gov/sites/evo-subsites/legcounsel-evo.house.gov/files/documents/ManualDraftStyle_2022.pdf) |
| ecfr.gov | [1 CFR part 21 subpart B](https://www.ecfr.gov/current/title-1/chapter-I/subchapter-E/part-21/subpart-B) (authority cites); [1 CFR 21.23](https://www.ecfr.gov/current/title-1/chapter-I/subchapter-E/part-21/subpart-A/subject-group-ECFR095b3363a246648/section-21.23) (parallel CFR/FR) |
| leginfo.legislature.ca.gov | [Code Search](https://leginfo.legislature.ca.gov/faces/codes.xhtml); [Civil Code preliminary provisions](https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CIV) |

## Manuals refused (not opened / not copied)

| Manual | Reason |
| --- | --- |
| California Style Manual | Named by rule 1.200; full text is not free on courts.ca.gov — not opened, not quoted |
| The Bluebook | Not a government publication — not opened, not copied |
| APA (American Psychological Association) | Not a government publication; name collides with the Administrative Procedure Act — not used |
| Vendor copies (Justia, Westlaw, FindLaw, etc.) | Out of scope for this note |

Senate Office of the Legislative Counsel drafting manual and a California Legislative Counsel drafting-style PDF on leginfo were not found on official hosts in [courts/manuals.md](../courts/manuals.md); nothing from those was used here.
