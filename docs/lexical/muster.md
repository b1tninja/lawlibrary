# What a section usually does

The official sources are [drafting.md](drafting.md).

`muster` walks the outline of one section and reports where it breaks an expectation. A break is a place to look again. It may be a parser miss. It may, rarely, be the text. The checker does not choose.

| Expectation | Claim |
| --- | --- |
| `sequence` | Siblings of one rank run in order: `(a)` then `(b)`, `(1)` then `(2)`, `(A)` then `(B)`, `(i)` then `(ii)`. A doubled letter `(aa)` follows `(z)`. `(_l_)` is the letter l. |
| `rank` | A child sits deeper than its parent, unless its line is indented further in. |
| `local_label` | `subdivision (b)`, `paragraph (1)`, `subparagraph (A)`, and `clause (i)` name a label in the same section. |
| `following` | "either of the following", "any of the following", "all of the following", or "both of the following" is followed by at least two items. |

A decimal section such as `54004.5` is an insertion between whole numbers. It is not a skipped subdivision inside one section.

## What the posted rules actually require

California Rules of Court, rule 1.200, retrieved from the courts site: citations in documents filed in the courts must be in the style of the California Style Manual or The Bluebook, and the same style must be used consistently. That rule governs the brief. It does not govern how a code section letters its subdivisions.

Joint Rule 8.5 of the Senate and Assembly, on the Legislature's bill page for the joint rules: a bill may not be introduced unless it is contained in a cover attached by the Legislative Counsel and accompanied by a digest prepared by the Legislative Counsel. The rule does not print the `(a)`, `(1)`, `(A)` alphabet. That alphabet is the expectation above, not a sentence those rules state.
