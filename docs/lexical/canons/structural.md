# Structural canons and customary clauses

The skeleton of a statute and the interpretive rules that treat the act (or the code) as a whole. The first lexical pass in `lexical.py` already marks six customary spans: `enactment`, `short_title`, `definitions`, `severability`, `effective_date`, and `authority`. For each item below: what it is, a labeled illustration (not a quotation of any act or opinion), and whether one of those marks is the hook or what new mark would be needed.

Textual word-level canons live in [textual.md](textual.md).

---

## 1. Enacting clause

The sentence that makes the rest of the bill law. Without it, the text is not an act. It sits at the front of the enrolled bill and is often stripped or reduced when the act is folded into a code title.

Federal formula (illustration): *Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled,* then the operative text.

State formula (illustration): *The people of the State of … do enact as follows:* then the operative text. Constitutions and style guides vary the exact words; the pattern is a people-or-legislature subject, the verb *enact*, and a break into the body.

**Hook:** `enactment` (already marked).

---

## 2. Short title

The citation name of the act—the label used in speech and in later cross-references. It is not the full bill caption.

Illustration: *This Act shall be known as the … Act* (also *may be cited as* / *is known as*, applied to *chapter*, *part*, *title*, *article*, or *division*).

**Hook:** `short_title` (already marked).

---

## 3. Long title

The full caption of the bill: the statement of subject that procedure uses for germaneness and single-subject checks. Session laws keep it; codified titles often drop or rewrite it.

Illustration: *An Act to amend … relating to … and for other purposes.*

**Hook:** none of the six. Needs a new mark, e.g. `long_title`, aimed at session-law caption lines.

---

## 4. Preamble and purpose clause

Why the legislature is acting. May appear as *whereas* clauses before the enacting clause, or as a purpose / policy section after. Usually interpretive context, not an operative command, unless the jurisdiction treats it as one.

Illustration: *Whereas …; now, therefore…* or *The purpose of this Act is to…*

**Hook:** none of the six. Needs a new mark, e.g. `purpose` (optional split: `preamble` for *whereas* blocks vs. purpose sections).

---

## 5. Findings

Legislative declarations of fact or circumstance that support the act. Often numbered under a *Findings* or *Legislative findings* heading. Usually inform interpretation; they create duties only when the text makes a finding itself operative.

Illustration: *The Legislature finds and declares that…*

**Hook:** none of the six. Needs a new mark, e.g. `findings`.

---

## 6. Definitions section

Assigns meaning to words used in the act (or chapter, part, title). Scope cues: *as used in this Act*, *for purposes of this chapter*, *the following definitions apply*.

Two definitional verbs:

- *Means* closes the set: the term equals the listed content (subject to other canons).
- *Includes* / *includes but is not limited to* opens the set: the listed items are members or examples; they do not exhaust ordinary meaning unless the text says so.

Illustration: *As used in this Act: (a) “Agency” means … (b) “Record” includes …*

**Hook:** `definitions` (already marked) for the section opener. A later pass may sub-mark *means* vs. *includes* on each defined term; that sub-mark is not one of the six clause kinds.

---

## 7. Proviso

Narrows or conditions what precedes it. Classic cue: *provided that* (or *provided, however, that*). Part of the same section’s operative force, not a separate act.

Illustration: *… shall issue a permit, provided that the applicant files proof of insurance.*

**Hook:** none of the six. Needs a new mark, e.g. `proviso` (often mid-sentence).

---

## 8. Exception

Carves cases out of a general rule. Cues: *except*, *except that*, *unless*, *unless otherwise provided*.

Illustration: *No person shall park overnight except an authorized resident* or *… unless the board grants a waiver.*

**Hook:** none of the six. Needs a new mark, e.g. `exception`. Distinct from `proviso` if cue words are tracked separately; some pipelines collapse both into `qualification`.

---

## 9. Savings clause

Preserves rights, proceedings, or liabilities that would otherwise fall when the act repeals or changes prior law. Keeps pending cases, accrued claims, or existing licenses under the old regime or under stated transition rules.

Illustration: *Nothing in this Act affects any proceeding commenced before the effective date…* or *The repeal of … does not affect rights accrued under that section.*

**Hook:** none of the six. Needs a new mark, e.g. `savings`. Do not fold into `severability`.

---

## 10. Severability clause

If one provision is held invalid, the remainder stays in force (sometimes with an express non-severability reverse). A drafting instruction about remedial scope, not a definition of the substantive duty.

Illustration: *If any provision of this Act is held invalid, the remainder shall not be affected.*

**Hook:** `severability` (already marked).

---

## 11. Effective-date clause

When the act (or a section) takes effect: on enactment, on a fixed date, or on a contingent event. Absent a clause, the jurisdiction’s default rules supply the date.

Illustration: *This Act shall take effect on January 1, …* or *This section becomes effective ninety days after enactment.*

**Hook:** `effective_date` (already marked).

---

## 12. Sunset clause

Ends the act or a provision on a stated date or after a stated period unless renewed. Temporal opposite of a permanent commencement clause: not when the law starts, but when it stops.

Illustration: *This Act is repealed on December 31, …* or *This chapter remains in effect until … and as of that date is repealed.*

**Hook:** none of the six. Needs a new mark, e.g. `sunset`. Related to `effective_date` and `repealer`, but the cue is expiry or automatic repeal on a future date.

---

## 13. Repealer

Withdraws prior law. May name sections (*Section … is repealed*) or use a general form (*all acts and parts of acts inconsistent with this Act are repealed*). Named repealers are clearer; general inconsistency repealers require reading more of the code.

Illustration: *Section 12 of the … Act is hereby repealed.*

**Hook:** none of the six. Needs a new mark, e.g. `repealer`. A later pass may distinguish named-section repeal from general inconsistency repeal.

---

## 14. Headings and section titles

**Canon.** In most American jurisdictions, catchlines, article headings, and marginal titles are editorial aids, not part of the enacted law, and do not control meaning when they conflict with the body. The engine must not treat a heading as an operative clause solely because it sits next to a section.

**The split.** A minority of jurisdictions enact headings as part of the statute, or give them limited weight by their own statute or constitution. Others expressly provide that headings are not law. Follow the jurisdiction’s rule; this note invents no code section for either camp. Where headings are non-law, ignore them for operative marking. Where they are law or admissible interpretive aids, a heading mark is still context, not a substitute for the body.

**Hook:** none of the six. Needs a new mark only if headings are stored as spans, e.g. `heading` / `catchline`, plus a jurisdiction flag for whether the heading is law.

---

## 15. Whole-act canon

Read the act as a whole. A word in one section is read against related sections of the same act so the parts fit. Isolated reading that makes another section surplus or contradictory is disfavored when a harmonious reading is available.

**Hook:** not a clause mark. Interpretive rule over the marked document; no new `Clause` value unless the pipeline records canon applications as a different annotation kind.

---

## 16. Whole-code canon

Read a provision against the surrounding code, not only the single act that inserted it. Cross-references, parallel chapters, and shared defined terms in the same compilation supply context.

**Hook:** not a clause mark. Same as whole-act: interpretive posture, not a customary phrase to find.

---

## 17. In pari materia

Statutes on the same subject are read together as if one law, even if passed at different times, when they share a common purpose or scheme. Bridges separate acts that the whole-code canon also reaches inside one compilation.

**Hook:** not a clause mark. Needs corpus-level linking (shared subject, cross-citation), not a new customary-clause pattern.

---

## 18. Later-in-time rule

When two provisions conflict and cannot be reconciled, the later enactment controls over the earlier (all else equal). Specificity and other canons may still prefer a narrower earlier rule when both can stand; later-in-time is the conflict rule, not the first tool.

**Hook:** not a phrase mark. Needs enactment or effective dates on competing provisions—often from `effective_date` marks, session-law metadata, or `enactment` context.

---

## 19. Reenactment / codification canon

A later reenactment or official codification speaks as of its own date. When the legislature reenacts a section in a code revision, or adopts a codified title as positive law, the reenacted text is treated as law of that later date for continuity, amendment history, and conflict with intervening acts—subject to the jurisdiction’s own revision statutes. Do not treat the code print as a mere reprint of an older session law when the legislature has spoken again.

**Hook:** not a customary-phrase mark. Needs edition / positive-law / reenactment metadata on the text unit. Optional revision-note marks are out of band for the six existing kinds.

---

## 20. Scrivener’s-error doctrine

When the enacted text contains an obvious slip—a misplaced word, a crossed cross-reference, a clerical garble that no reasonable reading can treat as intended—a court may correct the error to reflect the clear legislative meaning. The doctrine is narrow: the mistake must be plain from the face of the act or its enactment history, not a chance to rewrite policy. The lexical engine does not “fix” text under this doctrine; at most it can flag internal contradictions for human or judicial review.

**Hook:** not a clause mark. Optional diagnostic annotation (e.g. `scrivener_flag`) is not one of the six and is not required to document the canon.

---

## Mark summary

| # | Item | Existing hook | New mark if needed |
| --- | --- | --- | --- |
| 1 | Enacting clause | `enactment` | — |
| 2 | Short title | `short_title` | — |
| 3 | Long title | — | `long_title` |
| 4 | Preamble / purpose | — | `purpose` (optional `preamble`) |
| 5 | Findings | — | `findings` |
| 6 | Definitions | `definitions` | optional `means` / `includes` sub-mark |
| 7 | Proviso | — | `proviso` |
| 8 | Exception | — | `exception` |
| 9 | Savings clause | — | `savings` |
| 10 | Severability | `severability` | — |
| 11 | Effective date | `effective_date` | — |
| 12 | Sunset | — | `sunset` |
| 13 | Repealer | — | `repealer` |
| 14 | Headings | — | `heading` / `catchline` + jurisdiction rule |
| 15 | Whole-act | — | interpretive; no clause mark |
| 16 | Whole-code | — | interpretive; no clause mark |
| 17 | In pari materia | — | corpus link; no clause mark |
| 18 | Later-in-time | uses dates / metadata | no phrase mark |
| 19 | Reenactment / codification | edition metadata | no phrase mark |
| 20 | Scrivener’s error | — | optional diagnostic only |

`authority` remains the mark for citations that name the statute under which an office acts. It is not the structural hook for the twenty items above, except insofar as a later-in-time or in-pari-materia pass consumes citations that `authority` (or a citation tool) has already found.
