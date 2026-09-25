# Textual canons

Rules a lexical engine can pin from wording alone. No structural clause map lives here; see the structural canons file for preamble, titles, and related layout. Illustrations below are labeled inventions, not citations.

For each canon: English name, Latin name if any, what the reader does, a short illustration, and search hooks a lexer can watch (`shall`, `may`, `including`, `other`, `unless`, `and`, `or`, plus nearby cues).

---

## 1. Ordinary-meaning canon

**Latin:** none.

**Do:** Give a word the sense an ordinary reader would give it in context, unless a technical or defined sense controls.

**Illustration:** A rule that forbids leaving a "vehicle" on a path covers cars and trucks in everyday talk before it covers exotic machines.

**Lexer hooks:** plain words without a nearby definition cue (`means`, `includes`, `as used in`); contrast with defined terms.

---

## 2. Technical-meaning exception

**Latin:** none (term of art / *voces artis* when named that way).

**Do:** If the field treats the word as a term of art, prefer that specialized sense over the street meaning.

**Illustration:** In a tax chapter, "basis" is the tax concept, not a physical footing.

**Lexer hooks:** definitional frames (`means`, `as used in this`), field markers near the term; still watch `including` / `other` when the technical list is open-ended.

---

## 3. Fixed-meaning canon

**Latin:** none (sometimes paired with *contemporanea expositio* in older usage).

**Do:** Keep the sense the word had when the provision was enacted; later slang or drift does not rewrite it.

**Illustration:** A word that meant one class of device at enactment is not stretched to cover a later invention that only shares a modern nickname.

**Lexer hooks:** enactment / effective-date cues in nearby text; stable defined terms; avoid treating new popular synonyms as if they were in the original wording.

---

## 4. Noscitur a sociis

**English also:** associated-words canon (see §19).

**Latin:** *noscitur a sociis* ("it is known by its associates").

**Do:** Read an ambiguous word in light of the company it keeps in the list or phrase.

**Illustration:** In "lions, tigers, and bears," "bears" is read as an animal of that zoo list, not every metaphorical "bear."

**Lexer hooks:** commas and `and` / `or` in short lists; shared category words; `other` and `including` when the list frames the ambiguous item.

---

## 5. Ejusdem generis

**Latin:** *ejusdem generis* ("of the same kind").

**Do:** When general words follow specific ones, limit the general words to things of the same kind as the specifics.

**Illustration:** "Apples, oranges, and other fruit" does not pull in lumber; "other fruit" stays in the fruit class.

**Lexer hooks:** `other`, `including`, `and other`, `or other`, residual generics after a specific series.

---

## 6. Expressio unius est exclusio alterius

**Latin:** *expressio unius est exclusio alterius* ("the expression of one is the exclusion of others").

**Do:** Naming some items in a set implies omission of the unmentioned ones, when the structure looks exclusive.

**Illustration:** A fee schedule that lists three filing types and is silent on a fourth does not invite inventing a fourth rate.

**Lexer hooks:** closed lists with `and` / `or`; contrast with `including` (often open); `unless` exceptions that name what escapes the rule.

---

## 7. Rule against surplusage

**Latin:** none (anti-surplusage / no idle words).

**Do:** Prefer a reading that gives effect to every word; do not treat a clause as empty if another reading uses it.

**Illustration:** If a sentence says "written and signed," do not read "written" as doing no work beside "signed."

**Lexer hooks:** paired requirements with `and`; dual modals (`shall` … `and shall`); exception words (`unless`) that would be idle under a broader reading.

---

## 8. Harmonious-reading canon (whole text)

**Latin:** none (*in pari materia* is related but usually cross-statute; here the focus is one instrument read as a whole).

**Do:** Read provisions so they fit together; avoid a local reading that clashes with the rest of the same text.

**Illustration:** A permission in one section and a limit in another are read so both can operate, not so one silently cancels the other.

**Lexer hooks:** cross-references; matching defined terms; `shall` / `may` pairs across sections; `unless` bridges between rules.

---

## 9. Presumption of consistent usage

**Latin:** none.

**Do:** The same word in the same text usually keeps the same sense.

**Illustration:** If "notice" is defined once, later bare uses of "notice" in that chapter track that definition.

**Lexer hooks:** repeated lemmas; definition blocks; consistent `shall` / `may` patterns for the same actor.

---

## 10. Presumption of meaningful variation

**Latin:** none.

**Do:** A change of word usually signals a change of sense; different terms are not treated as duplicates without reason.

**Illustration:** Switching from "may" in one duty to "shall" in the next is read as a real shift from permission to command.

**Lexer hooks:** nearby swaps of `shall` / `may`, `and` / `or`, `including` vs bare lists, `other` vs named exclusives.

---

## 11. General/specific canon

**Latin:** none (*generalia specialibus non derogant* when stated that way: the specific is not overridden by the general).

**Do:** On the same subject, the specific provision controls the general one.

**Illustration:** A general ban on nighttime work yields to a specific license for night repair of a named system.

**Lexer hooks:** overlapping subject nouns; `unless` / `except` in the specific rule; `shall` in the narrow rule against `may` or broad `shall` in the general one.

---

## 12. Last-antecedent canon

**Latin:** none.

**Do:** A limiting clause or pronoun ordinarily modifies only the nearest suitable antecedent.

**Illustration:** In "banks, credit unions, or brokers licensed by the state," "licensed by the state" attaches first to "brokers."

**Lexer hooks:** trailing modifiers after `or` / `and` lists; commas that set off or withhold the qualifier; `other` items before the trailing phrase.

---

## 13. Series-qualifier canon

**Latin:** none.

**Do:** When a qualifier follows a parallel series and fits each item, it may apply to the whole series.

**Illustration:** "cars, trucks, and vans registered in the county" can treat "registered in the county" as covering all three if the series is parallel.

**Lexer hooks:** parallel nouns joined by `and` / `or`; a shared trailing modifier; contrast with last-antecedent when parallel structure is weak.

---

## 14. Nearest-reasonable-referent canon

**Latin:** none.

**Do:** A pronoun or relative phrase points to the nearest noun that makes sense; skip an absurd nearer noun.

**Illustration:** "Remove the bolt from the panel and discard it" points "it" to the bolt, not the panel, when only the bolt is meant to be thrown away.

**Lexer hooks:** `it`, `such`, `said`, `which`, `that` after multi-noun phrases; `and` / `or` chains that create competing referents.

---

## 15. Punctuation canon

**Latin:** none.

**Do:** Use commas, semicolons, and similar marks as evidence of grouping—not as the sole trump over clear wording.

**Illustration:** A comma before a trailing "or" phrase can show whether the last alternative stands alone or shares a modifier.

**Lexer hooks:** comma placement around `and` / `or`; serial commas; dashes and parentheses around `including` / `unless` asides.

---

## 16. Conjunctive/disjunctive canon

**Latin:** none.

**Do:** Read `and` as joining requirements (all) and `or` as alternatives (any), unless context forces a different sense.

**Illustration:** "Submit A and B" demands both; "submit A or B" allows either.

**Lexer hooks:** `and`, `or`, `and/or` (flag for human review), `either` … `or`, `both` … `and`.

---

## 17. Mandatory/permissive canon

**Latin:** none.

**Do:** Treat `shall` as mandatory and `may` as permissive, absent a clear contrary usage in that code.

**Illustration:** "The clerk shall file the form" is a duty; "the clerk may waive the fee" is discretion.

**Lexer hooks:** `shall`, `may`, `must`, `is authorized to`; negatives (`shall not`, `may not`).

---

## 18. Singular and plural; gender

**Latin:** none.

**Do:** Where the code so provides, the singular includes the plural and vice versa, and gendered words include every gender. Follow the local construction statute when present.

**Illustration:** A duty phrased with "a member … he shall" still reaches every member if the code's gender rule so states.

**Lexer hooks:** construction-section cues (`singular`, `plural`, `gender`, `masculine`, `feminine`); nearby `shall` / `may` attached to gendered pronouns.

---

## 19. Associated-words canon

**Latin:** *noscitur a sociis* (same rule as §4).

**Do:** Already covered under noscitur: infer sense from neighboring words in the phrase or list. No separate lexer rule beyond §4.

**Illustration:** Same pattern as §4 — the neighbors set the category for the contested word.

**Lexer hooks:** same as §4 (`and`, `or`, `other`, `including` in tight lists).

---

## 20. Prefatory-materials canon

**Latin:** none.

**Do:** A preamble, purpose clause, or findings section informs sense but is not itself the operative command. One short note: the structural canons file owns how those clauses are marked and scoped.

**Illustration:** A purpose sentence that praises "safety" does not by itself create a duty; the operative `shall` / `may` clauses do.

**Lexer hooks:** prefatory lead-ins; contrast with operative `shall` / `may`; `unless` in the body still controls the duty.

---

## Count

**20** canons documented in this file.
