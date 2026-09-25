# Document-local drafting idioms

A section is read inside a book. The words that point elsewhere in that book—or that open a list, a definition block, or an exception—are idioms, not holdings. `citations.annotate` already marks several of them as `Note.CROSS_REFERENCE` or `Note.SHORT_FORM`. `lexical.find_clauses` already marks definition and short-title frames as `Clause.DEFINITIONS` and `Clause.SHORT_TITLE`. This note is the idiom list a lexer should recognize when those modules expand.

It does not restate the interpretative canons in [canons/index.md](canons/index.md). Those tell a reader how to treat words once they are found. Index-key shapes for the same surface words are in [references.md](references.md). Section-sign grammar is in [citations.md](citations.md). Clause strategies for courts are in [clauses.md](clauses.md).

Illustrations marked **retrieved** are sentences taken from the local Whoosh index (`data/idx`) via `query.section` / `sample.sample`. Ellipses mark truncation of a long section, not invented words. Rows marked **labeled pattern** are shapes the code or style manuals already treat, with no matching statute sentence in the samples drawn here.

## How a mark resolves

| Context | What the open document supplies |
| --- | --- |
| `document(code, section, books=…)` | The book abbreviation and the section being read |
| Bare `section` / `§` number | A section of that book |
| Structural `this …` | A unit of that book (code, title, division, part, chapter, article) |
| `the following` / `as follows` | Material that follows in the open section |
| `commencing with Section N` | A span that starts at `N` in the named unit |

Emit an annotation target the way `annotate` already does: `this code` alone resolves to the open abbreviation; other cross-references keep `{ABBR} …` so lookup stays document-local.

## Structural “this …”

| Idiom | Points at | Lexer emit | Illustration |
| --- | --- | --- | --- |
| `this code` | The whole open statute book | `Note.CROSS_REFERENCE`; target = open abbreviation (e.g. `CIV`, `GOV`) | **Retrieved — CIV 14:** “Words used in this code in the present tense include the future as well as the present; …” **Retrieved — GOV 10:** “‘Section’ means a section of this code unless some other statute is specifically mentioned.” **Retrieved — GOV 5:** “Unless the provision or the context otherwise requires, these general provisions, rules of construction, and definitions shall govern the construction of this code.” |
| `this title` | The title that contains the open section | `Note.CROSS_REFERENCE`; target `{ABBR} this title` | **Retrieved — CIV 3426.9:** “If any provision of this title or its application to any person or circumstances is held invalid, the invalidity does not affect other provisions or applications of the title which can be given effect without the invalid provision or application, and to this end the provisions of this title are severable.” **Retrieved — GOV 99050:** “(a) This title shall be known and may be cited as the Economic Recovery Bond Act.” |
| `this division` | The division that contains the open section | `Note.CROSS_REFERENCE`; target `{ABBR} this division` | **Retrieved — CIV 1429:** “The rules which govern the interpretation of contracts are prescribed by Part II of this Division.” **Retrieved — GOV 66429:** “Of the maps required by this division, only final and parcel maps may be filed for record in the office of the county recorder.” |
| `this part` | The part that contains the open section | `Note.CROSS_REFERENCE`; target `{ABBR} this part` | **Retrieved — CIV 8000:** “Unless the provision or context otherwise requires, the definitions in this article govern the construction of this part.” **Retrieved — GOV 18538:** “‘Part’ means this part and those portions of Part 1 that confer powers or impose duties on the board.” |
| `this chapter` | The chapter that contains the open section | `Note.CROSS_REFERENCE`; target `{ABBR} this chapter` | **Retrieved — CIV 1794.5:** “The provisions of this chapter shall not preclude a manufacturer making express warranties from suggesting methods of effecting service and repair, in accordance with the terms and conditions of the express warranties, other than those required by this chapter.” **Retrieved — GOV 66000.5:** “(a) This chapter, Chapter 6 (commencing with Section 66010), Chapter 7 (commencing with Section 66012), Chapter 8 (commencing with Section 66016), and Chapter 9 (commencing with Section 66020) shall be known and may be cited as the Mitigation Fee Act.” |
| `this article` | The article that contains the open section | `Note.CROSS_REFERENCE`; target `{ABBR} this article` | **Retrieved — CIV 8830:** “‘Stop work notice’ means notice given under this article by a direct contractor to an owner that the contractor will stop work if the amount owed the contractor is not paid within 10 days after notice is given.” **Retrieved — GOV 8790.26:** “The revenues, rentals, and receipts from the facility authorized to be financed under this article may be pledged for the payment of principal of, premium, if any, and interest on, the bonds issued pursuant to this article.” |

`citations._REFERENCES` already matches `this (part|chapter|division|article|title|code)`. Nested units stay nested: “Division 3 of this code” is still the open book’s division 3, not another publication.

## Forward lists

| Idiom | Points at | Lexer emit | Illustration |
| --- | --- | --- | --- |
| `the following` | The enumeration or definitions that follow in the open section | `Note.CROSS_REFERENCE`; target `{ABBR} the following` | **Retrieved — CIV 1714.21:** “(a) For purposes of this section, the following definitions shall apply: (1) ‘AED’ or ‘defibrillator’ means an automated or automatic external defibrillator.” **Retrieved — GOV 5902:** “As used in this chapter, the following words and terms shall have the following meanings, unless the context otherwise indicates or requires another or different meaning or intent: …” |
| `as follows` | The same: material that follows, often after a colon or a headed notice | Same cross-reference family; also often co-occurs with `Clause.SHORT_TITLE` or a list | **Retrieved — CIV 1:** “This Act shall be known as The Civil Code of the State of California, and is in Four Divisions, as follows: …” **Retrieved — GOV 16724.4:** “Any state bond measure approved by the voters on or after January 1, 2004, shall be subject to an annual reporting process, as follows: (a) The head of the lead state agency administering the bond proceeds shall report to the Legislature and the Department of Finance …” |

Do not treat every “following” as this idiom. A phrase such as “the midnight following” is ordinary English, not a list opener.

## Definition and naming frames

| Idiom | Points at | Lexer emit | Illustration |
| --- | --- | --- | --- |
| `hereinafter` / `hereinafter set forth` | Text that will appear later in the open unit (definitions, maxims, provisos) | Keep as a forward pointer inside the open section; often precedes a `Clause.DEFINITIONS` block | **Retrieved — CIV 3509:** “The maxims of jurisprudence hereinafter set forth are intended not to qualify any of the foregoing provisions of this Code, but to aid in their just application.” **Retrieved — GOV 18520:** “Unless the context requires otherwise, the definitions hereinafter set forth govern the construction of this part and the rules adopted hereunder.” |
| `as used in this …` / `as used in Section(s) …` | Scope of a defined term: the named unit or the cited sections | `Clause.DEFINITIONS` when the frame is “as used in this …”; also pin any cited section numbers as `Note.CITATION` | **Retrieved — GOV 54090:** “As used in this article ‘public beach’ means any beach area used for recreational purposes which is owned, operated or controlled by the State, any state agency or any local agency.” **Retrieved — CIV 2784:** “As used in Sections 2782 and 2782.5, a ‘design defect’ is defined as a condition arising out of its design which renders a structure, item of equipment or machinery or any other similar object, movable or immovable, when constructed substantially in accordance with its design, inherently unfit, either wholly or in part, for its intended use …” |
| `for purposes of this …` / `for purposes of this section` | Same definitional scope, often paired with `the following definitions` | `Clause.DEFINITIONS` | **Retrieved — CIV 1103.7:** “For purposes of this article, ‘good faith’ means honesty in fact in the conduct of the transaction.” **Retrieved — GOV 6254.5:** “For purposes of this section, ‘agency’ includes a member, agent, officer, or employee of the agency acting within the scope of his or her membership, agency, office, or employment.” |
| `shall be known as` / `shall be known and may be cited as` | The short title of the act, chapter, or title | `Clause.SHORT_TITLE`; pair with `Note.NAMED_ACT` when the title is later cited by name | **Retrieved — CIV 1798:** “This chapter shall be known and may be cited as the Information Practices Act of 1977.” **Retrieved — GOV 3400:** “This chapter shall be known and may be cited as the Public Safety Officer Medal of Valor Act.” **Retrieved — CIV 1:** “This Act shall be known as The Civil Code of the State of California …” **Retrieved — GOV 11370:** “Chapter 3.5 (commencing with Section 11340), Chapter 4 (commencing with Section 11370), Chapter 4.5 (commencing with Section 11400), and Chapter 5 (commencing with Section 11500) constitute, and may be cited as, the Administrative Procedure Act.” |

## Hierarchy and exception frames

These are not cross-references to another book by themselves. They change how the open rule relates to other rules. `lexical.py` already folds some into `Clause.EXCEPTION` (`except as`, `unless otherwise`).

| Idiom | Points at | Lexer emit | Illustration |
| --- | --- | --- | --- |
| `subject to` | A limit that controls the open rule (another chapter, agreement, or condition) | Prefer a dependency / proviso mark; if a section or chapter follows, also emit `Note.CITATION` or `Note.CROSS_REFERENCE` | **Retrieved — CIV 1997.210:** “(a) Subject to the limitations in this chapter, a lease may include a restriction on use of leased property by a tenant.” **Retrieved — CIV 1609:** “In so far as it is executory it is subject to the provisions of Chapter IV of this Title.” **Retrieved — GOV 6509:** “Such power is subject to the restrictions upon the manner of exercising the power of one of the contracting parties, which party shall be designated by the agreement.” |
| `notwithstanding` | Overrides a conflicting rule named after it (`any other law`, a section, an agreement) | Exception / override mark; resolve the object of the phrase | **Retrieved — GOV 3520.8:** “Notwithstanding any other law, if a decision by an administrative law judge regarding the recognition or certification of an employee organization is appealed, the decision shall be deemed the final order of the board if the board does not issue a ruling that supersedes the decision on or before 180 days after the appeal is filed.” **Retrieved — CIV 1749.64:** “Notwithstanding any other provision of law, no club card issuer shall request in a supermarket club card application, or require as a condition of obtaining a supermarket club card, that an applicant provide a driver’s license number or a social security account number.” **Retrieved — CIV 2983.5:** “(a) An assignee of the seller’s right is subject to all equities and defenses of the buyer against the seller, notwithstanding an agreement to the contrary, but the assignee’s liability may not exceed the amount of the debt owing to the assignee at the time of the assignment.” |
| `unless otherwise provided` | A default that yields when another provision (or instrument) speaks | `Clause.EXCEPTION` | **Retrieved — GOV 25100:** “Unless otherwise provided by law, the county clerk is ex officio clerk of the board of supervisors of his county.” **Retrieved — CIV 1364:** “(a) Unless otherwise provided in the declaration of a common interest development, the association is responsible for repairing, replacing, or maintaining the common areas, other than exclusive use common areas, and the owner of each separate interest is responsible for maintaining that separate interest and any exclusive use common area appurtenant to the separate interest.” |
| `except as provided` | A carve-out that points at another subdivision or section | `Clause.EXCEPTION` plus a citation when a section number follows | **Retrieved — GOV 3208:** “Except as provided in Section 19990, the limitations set forth in this chapter shall be the only restrictions on the political activities of state employees.” **Retrieved — CIV 3334:** “(b)(1) Except as provided in paragraph (2), for purposes of subdivision (a), the value of the use of the property shall be the greater of the reasonable rental value of that property or the benefits obtained by the person wrongfully occupying the property by reason of that wrongful occupation.” **Retrieved — GOV 19862:** “(a) Sick leave may be accumulated, and no additional sick leave with pay beyond that accumulated shall be granted, except as provided in Section 19863.” |

## Spans and short forms

| Idiom | Points at | Lexer emit | Illustration |
| --- | --- | --- | --- |
| `commencing with Section` | A contiguous span that starts at the named section (often with a chapter/part/title wrapper) | `Note.CROSS_REFERENCE`; target `{ABBR} commencing with Section {n}` | **Retrieved — CIV 799.75:** “Disposition of any possessions abandoned by an occupant, tenant, or resident at a park shall be performed pursuant to Chapter 5 (commencing with Section 1980) of Title 5 of Part 4 of Division 3.” **Retrieved — GOV 11370:** “Chapter 3.5 (commencing with Section 11340), Chapter 4 (commencing with Section 11370), Chapter 4.5 (commencing with Section 11400), and Chapter 5 (commencing with Section 11500) constitute, and may be cited as, the Administrative Procedure Act.” **Retrieved — GOV 7060.1:** “… Part 2.8 (commencing with Section 12900) of Division 3 of Title 2 of this code, Chapter 5 (commencing with Section 17200) of Part 2 of Division 7 of the Business and Professions Code …” |
| `et seq.` | The cited section and those that follow in that publication | `Note.SHORT_FORM`; keep the lead citation | **Retrieved — CIV 1797.81:** “… Magnuson-Moss Warranty-Federal Trade Commission Improvement Act (see 15 U.S.C.A. Sec. 2302(b)(1)(A) and 16 C.F.R. 702.1 et seq.).” **Retrieved — GOV 12626:** “… Mutual Educational and Cultural Exchange Act of 1961 (22 U.S.C. Sec. 2451); 22 C.F.R. 514.1 et seq.) …” |
| `id.` | The immediately preceding citation | `Note.SHORT_FORM` | **Labeled pattern.** No `id.` hit in the Civil Code / Government Code / related samples drawn from the local index. Treat as a short form when the surrounding prose is a brief or opinion-style note, not as a California code cross-reference. |
| `supra` | An earlier full citation of the same authority | `Note.SHORT_FORM` | **Retrieved — PEN 1054.3:** “… in response to Verdin v. Superior Court, supra, it is not the intent of the Legislature to disturb, in any way, the remaining body of case law governing the procedural or substantive law that controls the administration of these tests or the admission of the results of these tests into evidence.” (`supra` here points at a case citation inside a statute, not at another code section.) |

## Civil Code and Government Code (from retrieved text only)

Differences that actually appear in the quotations above:

| Observation | Civil Code | Government Code |
| --- | --- | --- |
| How “this code” is framed at the front of the book | CIV 14 uses “Words used in this code …” as a general construction rule for ordinary words | GOV 5 says the general provisions “shall govern the construction of this code”; GOV 10 defines “‘Section’ means a section of this code unless some other statute is specifically mentioned” |
| Short-title formula at the head of the book | CIV 1: “This Act shall be known as The Civil Code of the State of California, and is in Four Divisions, as follows” | Later GOV chapters use “This chapter shall be known and may be cited as …”; GOV 11370 names the Administrative Procedure Act by listing chapters “commencing with Section …” |
| “hereinafter” | CIV 3509 points forward to maxims and says they do not qualify “this Code” | GOV 18520 points forward to definitions that “govern the construction of this part” |
| “notwithstanding” objects seen in samples | CIV 2983.5 overrides “an agreement to the contrary”; CIV 1749.64 uses “any other provision of law” | GOV 3520.8 uses “any other law” before an administrative override |
| `et seq.` in samples | Appears after a federal C.F.R. citation (CIV 1797.81) | Same pattern after a federal C.F.R. citation (GOV 12626) |

Do not invent further code-to-code contrasts from these rows. A miss in the sample draw is not evidence that the idiom is absent from that book.

## What the lexer should not do here

- Do not decide which provision prevails. That is canon work ([canons/index.md](canons/index.md)).
- Do not invent quotations from headings or file names.
- Do not treat a commercial reporter’s citation style as a source of statute text.
- Do not download missing books; a missing index section is a miss ([sample.md](sample.md), [references.md](references.md)).
