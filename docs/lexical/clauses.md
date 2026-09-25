# Clauses a lexer can mark

`lexical.py` already marks drafting boilerplate: an enacting clause, a short title, definitions, a proviso, a savings clause, and an authority phrase such as “pursuant to section …”. The court hierarchy needs a second set. These clauses create a court, say who sits on it, or state what it may hear. A later pass can add a `Clause` value for each row. This note is the pattern list for that pass.

Each row is a strategy, not a holding. The lexer finds the words and pins a citation. It does not decide a case. Illustrations are the words the local California index returned for Constitution article VI (code `CONS`, article heading `ARTICLE VI JUDICIAL`). Section numbers in that code collide across articles, so a lookup has to keep the article heading.

| Strategy | Words to find | Fact to pin | Index illustration |
| --- | --- | --- | --- |
| Vesting | “judicial power” … “is vested in” | The courts that exist. Article VI, section 1 names the Supreme Court, the courts of appeal, and the superior courts. Article III, section 1 does the same for the United States: one Supreme Court and inferior courts Congress establishes | “The judicial power of this State is vested in the Supreme Court, courts of appeal, and superior courts, all of which are courts of record.” |
| Composition | “consists of” plus a court name | Who sits on that court. Section 2: the Chief Justice and 6 associate justices | “The Supreme Court consists of the Chief Justice of California and 6 associate justices.” |
| Geographic division | “divide the State into districts” | How appellate courts are mapped onto counties. Section 3 leaves the district lines to the Legislature | “The Legislature shall divide the State into districts each containing a court of appeal with one or more divisions.” |
| Establishment | “there is a superior court” | One trial court per county. Section 4. That is the authority on `SacramentoSuperiorCourt` | “In each county there is a superior court of one or more judges.” |
| Appellate division of the trial court | “appellate division” inside a superior-court section | A docket of the trial court, not the Court of Appeal. `Division.APPELLATE` on the superior court | “In each superior court there is an appellate division.” |
| Original jurisdiction | “original jurisdiction” | What the court may hear first. Section 10 names habeas corpus and extraordinary relief | “The Supreme Court, courts of appeal, superior courts, and their judges have original jurisdiction in habeas corpus proceedings.” |
| Appellate jurisdiction | “appellate jurisdiction” | What the court reviews. Section 11. The Supreme Court reviews a judgment of death; the courts of appeal review the rest of the superior-court cases the section names | “The Supreme Court has appellate jurisdiction when judgment of death has been pronounced.” |
| Delegation | “shall prescribe”, “delegated by”, “shall assign” | A duty handed to the Legislature, the Chief Justice, or the Judicial Council rather than a new court. Section 4 tells the Legislature to set the number of judges. Section 6 creates the Judicial Council | “The Legislature shall prescribe the number of judges and provide for the officers and employees of each superior court.” |
| Appointment of a court officer | “shall appoint” plus an office | An officer of a court, not a court. Government Code sections 68900–68905: the Supreme Court appoints the Reporter of Decisions | The index heading is “ARTICLE 3. The Reporter of Decisions of the Supreme Court and the Courts of Appeal [68900. - 68905.]” |

## How a strategy runs

1. Search the plain text for the words in the table.
2. Keep the citation (`CONS` article VI, or the Government Code section) on the mark.
3. Attach the mark to the `Court` whose `authority` is that citation. Vesting and establishment marks identify the court. Jurisdiction marks say what that court hears. Delegation marks point at the body that received the duty.

`Clause.AUTHORITY` already catches “pursuant to section” followed by a number. It does not catch “is vested in” or “has appellate jurisdiction”. Those stay unparsed until the strategies above are added.

## What is already marked

Named governments are classified by the frame around the name (`State of`, `City of`), not by a list of every place. That pass is [entities.md](entities.md). The first pass in `lexical.py` is the boilerplate list in [libraries.md](libraries.md). The canons that tell a reader how to treat words once they are found are [canons/index.md](canons/index.md). The courts those citations name are [../courts/index.md](../courts/index.md).

## Manuals that define the phrases

The official manuals in [../courts/manuals.md](../courts/manuals.md) are the next place to harvest clause patterns. They are style and drafting guides, not a second copy of the code.

| Manual | What a later lexer should take from it |
| --- | --- |
| GPO Style Manual | Form of federal publications. Not a list of statutory clauses |
| California Style Manual | Citation form for California courts, required by California Rules of Court, rule 1.200. A free full text was not found on courts.ca.gov |
| House Legislative Counsel’s Manual on Drafting Style (2022) | Federal bill conventions: enacting words, definitions, provisos, effective dates. Mine this before adding new `Clause` values |
| OLRC Detailed Guide to the U.S. Code | How a section number, a note, and a positive-law title are marked in the Code |
| California Rules of Court | Rule text the courts publish. Separate from the statutes in the index |
| Administrative Procedure Act | A named act, not a style manual. Federal: 5 U.S.C. chapter 5, subchapter II. California: the index names it at Government Code section 11370 |

The Senate Legislative Counsel and the California Legislative Counsel have not posted a drafting manual on the hosts checked in that file. Do not use a third-party copy as the pattern source.
