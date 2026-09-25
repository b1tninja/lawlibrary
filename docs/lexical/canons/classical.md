# Classical English canons and conflict rules

These are the classical English reading rules and the conflict maxims a lexical engine should know how to *spot*. Each entry names the trigger surface when one exists. The engine marks candidates; it does not choose which canon wins a case. Full textual canons live in [textual.md](textual.md). Structural formulas for American enacting clauses live in [structural.md](structural.md).

---

## 1. The literal rule

Give the words of the statute the ordinary meaning they bear in the language, and stop there. Context, purpose, and hardship do not move the reading when the words are clear.

**Lexer trigger.** Ordinary dictionary sense of the operative verbs and nouns; no special cue phrase. A miss under another canon (no list, no proviso, no conflict pair) leaves the clause as a literal candidate.

**Illustration.** A section that says a licence “shall expire on the thirty-first day of December” is read as ending on that calendar day, not on the next business day, unless another provision says otherwise.

---

## 2. The golden rule

Start with the literal meaning. Depart from it only so far as needed to avoid an absurdity, inconsistency, or repugnancy that the ordinary sense would produce.

**Lexer trigger.** Pair a candidate absurd or self-defeating reading (e.g. a duty that nullifies itself, a date that cannot occur) with the same clause’s ordinary sense. The mark is “golden-rule tension,” not a rewrite.

**Illustration.** A rule that forbids “any vehicle” in a park, read literally to include a child’s toy pushed by hand, may be flagged for golden-rule review when the surrounding schedule lists only motor carriages.

---

## 3. The mischief rule (Heydon’s Case, 1584)

A court was told to work through four points before fixing the sense of an Act. Stated without the report’s wording:

1. What the law was on the subject before the Act.
2. What gap, abuse, or defect that prior law left open.
3. What remedy the legislature chose to close that gap.
4. The reason for that remedy — so the Act is applied to suppress the mischief and advance the cure.

**Lexer trigger.** Recitals of defect (“whereas … has been found insufficient”), “for the better prevention of,” “to remedy,” and similar purpose clauses near the operative text. The four points are a checklist for a later reasoner, not four separate lexical marks.

**Illustration.** An Act passed after street gambling had been held outside an older gaming statute may carry a recital of that omission; the mischief checklist attaches to the new offence clause, not to the recital alone.

---

## 4. Purposive interpretation

The modern descendant of the mischief rule. Read the text in light of the purpose the legislature can be taken to have had, including materials the forum allows (long title, preamble, explanatory notes, and, where admitted, external aids). Purpose guides the choice among grammatically available readings; it does not license ignoring clear words.

**Lexer trigger.** Long title, preamble, purpose clause, “in order to,” “with a view to,” and defined objects of the Act. Link those spans to the enacting sections they introduce.

**Illustration.** A consumer-protection Act whose long title speaks of unfair trading practices pulls ambiguous “supply” language toward commercial supply, not a private gift, when both readings are open on the words.

---

## 5. The plain-meaning rule (American courts)

In American usage, if the statutory text is unambiguous on its face, the court applies that plain meaning and does not resort to legislative history or other extrinsic aids. Ambiguity is the gate to those aids.

**How it differs from the literal rule.** The English literal rule is a habit of staying with ordinary sense even when the result is harsh. The American plain-meaning rule is chiefly a *stop rule* against extrinsic materials: clear text ends the inquiry. Both privilege the words; only the American formulation is routinely framed as a bar on legislative history.

**Lexer trigger.** Same as literal for the text itself. Separately mark extrinsic-aid spans (committee reports, floor debate citations) so a reasoner can suppress them when the text mark is “unambiguous.”

**Illustration.** A federal section that says “within 30 days after service” is plain as to the count of days; committee gloss that “days” meant business days stays extrinsic unless ambiguity is first found in the text.

---

## 6. The rule of rank

When a later statute deals specifically with a matter already covered by an earlier general statute, the later specific enactment controls on that matter. Rank here is the pairing of *later* with *specific*, not specificity alone and not chronological order alone.

**Distinct from general/specific.** Pure *lex specialis* (entry 8) compares scope without requiring the special Act to be the later one. Pure *lex posterior* (entry 7) compares time without requiring the later Act to be the narrower one. Rank is the combined case: specific later over general earlier.

**Lexer trigger.** Two provisions that share a subject; dating metadata (enactment or effective date); and a specificity cue (named class, named procedure, named offence versus a catch-all).

**Illustration.** An 1870 Act regulating “all public houses” and an 1925 Act regulating “tied houses in the County of X” put the 1925 Act in rank over the 1870 Act for tied houses in that county.

---

## 7. Lex posterior derogat legi priori

A later law derogates from an earlier one. When two norms of equal rank cannot stand together, the later prevails to the extent of the conflict.

**Lexer trigger.** Conflicting duties or permissions on the same subject; compare enactment or effective dates. Mark the conflict span and the date order; do not silently drop the earlier text.

**Illustration.** An Act of 1990 that says “no licence may issue after dusk” and an Act of 2005 that says “a night licence may issue” leave the night-licence path governed by 2005 where they clash.

---

## 8. Lex specialis derogat legi generali

A special law derogates from a general one. The narrower norm controls the matter it specially addresses; the general norm continues elsewhere.

**Lexer trigger.** A general class word (“any person,” “any vehicle”) alongside a provision confined to a named subclass, named place, or named procedure. Specificity is about scope of subject, not about date.

**Illustration.** A code chapter on “contracts” and a chapter on “contracts of marine insurance” leave marine insurance to the special chapter where the two differ.

---

## 9. Lex superior derogat legi inferiori

A higher norm derogates from a lower one. Constitution over statute; statute over regulation or bye-law; primary legislation over secondary where the hierarchy of the forum so provides.

**Lexer trigger.** Source-of-law tags (constitution, organic law, statute, regulation, order, bye-law) on each provision in a conflict set. Hierarchy beats both date and specificity unless the forum’s own conflict rules say otherwise.

**Illustration.** A regulation that forbids what a parent statute expressly permits is marked inferior; the statute’s permission stands.

---

## 10. Ejusdem generis (cross-note)

English courts use *ejusdem generis* to read general words after a list of particulars as confined to the same kind as the particulars. **Full entry:** [textual.md](textual.md). Do not duplicate that treatment here.

**Lexer trigger (pointer only).** A closed or open list of specifics followed by a general extender (“or other,” “or otherwise,” “and the like”).

---

## 11. Expressio unius (cross-note)

*Expressio unius est exclusio alterius*: mention of one thing implies exclusion of another. **Full entry:** [textual.md](textual.md).

**Lexer trigger (pointer only).** An enumeration of permitted or required items without a catch-all; contrast with express “including without limitation” language that weakens the implication.

---

## 12. Reddendo singula singulis

Refer each to each. When a sentence pairs two lists or two sets of referents, distribute the first list’s items to the matching items of the second, rather than reading every word as applying to every referent.

**Lexer trigger.** Parallel structure: two coordinated noun lists, or a list of subjects with a list of verbs/objects, especially with “respectively” or mirrored commas and conjunctions.

**Illustration.** “Landlords and tenants shall repair the roof and the interior” may be distributed so landlords answer for the roof and tenants for the interior when the rest of the instrument supports that pairing — flagged as a *reddendo* candidate, not as a decided parse.

---

## 13. Generalia specialibus non derogant

General words do not derogate from special ones. A later general enactment is not taken to repeal or narrow an earlier special provision by mere generality; something more (express repeal, necessary implication, or clear intent to cover the same ground) is required.

**Relation to other maxims.** This is the shield for the special provision against a later general one — the counterpart concern to *lex specialis* and a restraint on bare *lex posterior* when the earlier norm is special.

**Lexer trigger.** Earlier special provision + later general provision on an overlapping subject, without express repeal language.

**Illustration.** A special Act for a named harbour’s dues is not treated as repealed by a later Act about “all harbours” unless the later Act speaks to that harbour or repeals the special Act by name or necessary implication.

---

## 14. Presumption that the legislature does not make mistakes

The legislature is presumed to mean what it enacted and to have used words deliberately. Courts do not lightly correct grammar, punctuation, or apparent slips; the enacted text is the starting point.

**Cross-note — scrivener’s exception.** Where the error is a patent clerical mistake (a wrong cross-reference digit, an obviously dropped negative, a transposed schedule label) and the intended sense is clear from the rest of the instrument, some forums allow a corrective reading. That exception is narrow; the lexer only marks *possible clerical inconsistency* (broken internal reference, schedule letter that does not exist). It does not “fix” the text.

**Lexer trigger.** Broken internal cites; defined term used with a spelling that matches no definition; schedule or section identifiers that do not resolve.

---

## 15. Presumption that a repeal is express

Repeal is presumed to be express. An earlier provision remains in force until a later one repeals it by clear words or by necessary implication. Mere silence, overlap, or a new scheme on a related subject is not enough without more.

**Lexer trigger.** “is hereby repealed,” “ceases to have effect,” “repeal of,” schedule of repeals; absence of those cues on a later overlapping Act is itself a fact to mark (no express repeal found).

**Illustration.** A 2010 licensing Act that never mentions a 1960 special-licence section does not, by that silence alone, count as an express repeal of the 1960 section.

---

## 16. Beneficial / penal construction (older English sense)

In the older English habit, remedial or beneficial statutes were construed liberally to advance the remedy, and penal statutes were construed strictly so that no one was brought within a penalty beyond the clear words. Modern practice has softened the dichotomy, but the lexical distinction still matters for tagging.

**Lexer trigger.** Penal cues: “guilty of an offence,” “liable on conviction,” “shall be punished,” fine and imprisonment schedules. Beneficial / remedial cues: “relief,” “protection of,” “compensation,” “shall be entitled.” Mark the clause type; do not apply the liberal or strict thumb on the engine’s own authority.

**Illustration.** A section creating a summary offence with a fixed fine is tagged penal; a section granting a rent rebate to a defined class is tagged beneficial.

---

## 17. The ejusdem-generis limit

*Ejusdem generis* operates only when the general words *follow* a list (or string) of items of the same kind. If there is no list of specifics, or the specifics are not of one genus, the general words keep their ordinary width. The limit is part of when the canon fires, not a second canon.

**Lexer trigger.** Require: (a) two or more particulars sharing a detectable kind, then (b) a general extender. Fail the mark if the general word comes first, if there is only one particular, or if the particulars have no common genus.

**Illustration.** “dogs, cats, or other animals” can trigger the limit test (pets / domestic animals). “or other animals, including dogs and cats” does not meet the follow-the-list pattern for this entry.

---

## 18. Noscitur a sociis (cross-note)

A word is known by its associates: nearby words in the same list or phrase colour its range. **Full entry:** [textual.md](textual.md).

**Lexer trigger (pointer only).** Coordinated nouns or verbs in one phrase; adjacency inside a schedule row or definitional series.

---

## 19. Enacting words as the operative start of an English Act

In classical English form, the operative statute begins with the enacting formula, conventionally along the lines of “Be it enacted by the King’s most Excellent Majesty, by and with the advice and consent of the Lords Spiritual and Temporal, and Commons, in this present Parliament assembled, and by the authority of the same, as follows.” Words before that formula (title, preamble) inform purpose; the enacting words mark where binding law starts.

**American formulas.** Documented for the engine in [structural.md](structural.md) (federal and state enacting style). Do not treat those variants as English classical form.

**Lexer trigger.** Match the English enacting formula (including modern “Queen’s” / “King’s” and short “Be it enacted … as follows”). Annotate `enactment` from that span forward as operative unless a later structural rule says otherwise.

---

## 20. How a lexer should treat a canon

A lexer finds the *words and structures that trigger* a canon. It records a candidate application. It does not decide the case.

Examples of triggers, not holdings:

- a list of particulars followed by “or other” / “or otherwise” → *ejusdem generis* candidate (and run the limit in entry 17);
- a proviso (“provided that,” “provided always”) → scope-narrowing candidate against the preceding principal clause;
- “shall” versus “may” → mandatory versus permissive candidate;
- express repeal schedule versus silent overlap → repeal-presumption facts;
- date-ordered conflicting sections → *lex posterior* candidate;
- constitution / statute / regulation tags on the same subject → *lex superior* candidate.

Downstream reasoners (or a human) choose among marked candidates, resolve conflicts, and announce a holding. The lexical pass stops at the mark.

---

## Entry count

**20** entries (items 1–20 above).
