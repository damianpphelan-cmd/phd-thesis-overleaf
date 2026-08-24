# The thesis voice — a published economics paper

Replaced 16 Aug 2026 on the supervisor's feedback. The previous guide, derived
from Damian's earlier dissertations, optimised for a patient expository
register with generous signposting. That register is his, and it is right for
a document read in isolation; it is not the register of a published economics
paper, and the supervisor's instruction is explicit: *"you must follow the
style of any published economics paper."* The model is now an applied paper
in the Journal of Public Economics or Economics of Education Review.

## The rules, each tied to something the supervisor named

1. **Structure is the argument.** Five sections — Introduction, Data,
   Measurement (or Empirical Specification), Results, Conclusion — and few
   subsections. If a sentence needs to point to another section, the material
   is in the wrong place: move it or cut it. **Target: zero `\cref` to
   sections; `\cref` only to tables, figures, equations and appendix
   sections.** Signposting ("this section describes … there are seven parts")
   is a symptom of non-linear organisation, not a cure.

2. **State each thing once.** An important concept appears at most three
   times: previewed in the introduction, established in the body, restated
   in the conclusion. Everything else appears once. If a paragraph restates
   what an earlier paragraph established, cut it.

3. **No history, no diary.** What was done, and why. Never what was tried
   and dropped, what an earlier draft said, what was withdrawn, or what will
   come later. If a decision needs a rationale, give the rationale; the
   biography of the analysis belongs in the replication log. Banned
   constructions: "an earlier version", "previously", "was withdrawn",
   "superseded", "is not yet", "will be", "as we shall see", "documented
   below/above".

4. **Technical words keep their technical meaning.** *Convergence* means
   convergence in econometrics and numerical methods; for two measures
   agreeing, write "correlation", "agreement", or "association". The same
   discipline for *validate* (say what was tested against what), *robust*
   (to what), *significant* (at what level), *identify* (an effect, not a
   pattern), *predict* (a model predicts; a correlation does not).

5. **Register.** Declarative and compact. Third person, or authorial "I"
   used sparingly and consistently. Tables carry the detail, prose carries
   the argument. A paragraph makes one point and its first sentence states
   it. No rhetorical questions, no aphorisms, no italicised emphasis for
   effect, no dashes as a habit. Numbers in prose only when they carry the
   argument; the rest live in tables.

6. **Length is a constraint.** 35 pages per chapter including tables and
   figures in the body, appendix not bloated to compensate. Every cut is a
   real cut.

7. **The linear story the supervisor asked for**, and every section serves
   it: detailed data on a subset of schools → a gold-standard measure built
   from it → for schools without the detailed data, a prediction model from
   what is observable → evidence that the prediction reproduces the gold
   standard where both exist → facts about the measures.

## Kept from before

Precision and honesty are content, not style: every number derived by macro,
every limitation stated, the model-rater transparency stated plainly and once.
British English. The rules govern how things are said, never whether.

## Calibration

Old: "This section describes how those instruments were built, how they were
tested, and what was learned in the process. There are seven parts. The first
explains…"
New: [delete; the section's structure is visible from its subsections, and
its first substantive sentence begins the argument.]

Old: "The most plausible reading is that a school's website is simply not
written about the thing that parents experience."
New: "Website warmth is uncorrelated with the parent measure (r = 0.02)."

Old: "strictness converges across three independent sources"
New: "the strictness score is correlated with both the observed and the
espoused measure (r = 0.40 and 0.38)."

Old: "An earlier specification did produce the dissociation, but it did so
because the selectivity control was miscoded…"
New: [delete.]


## Clear and simple sentences (added 24 Aug 2026, Damian's instruction)

Prefer the clear, simple sentence. One idea per sentence. If a sentence needs
a second reading to parse, split it or shorten it.

- Keep most sentences under about 25 words; never stack more than two
  subordinate clauses.
- Subject early, verb close behind it. Avoid openings that delay the point
  ("It is worth noting that...", "In terms of...").
- Plain words over grand ones: "use" not "utilise", "show" not "demonstrate",
  "because" not "in consequence of the fact that".
- Prefer active voice unless the actor is genuinely irrelevant.
- Technical terms are fine; ornamental abstraction is not. Say "the model
  predicts warmth from word counts", not "the framework operationalises the
  construct via lexical frequencies".
- When a sentence must carry a number and a caveat, give each its own
  sentence rather than nesting the caveat mid-clause.

Calibration:

Old: "The residualisation procedure, which was implemented so as to preclude
the possibility of the intake composition of schools contaminating the
predictive relationship, was applied prior to estimation."
New: "Before estimation, intake is partialled out of the target, so the model
cannot get credit for reading demographics."


## What to include (added 24 Aug 2026, Damian's instruction)

Write for a reader who knows nothing about the project. Explain what was
done and what was found, clearly, and stop.

- Do NOT narrate process: no decision histories, no "we first tried X",
  no round-by-round genealogy, no rejected alternatives — unless a failed
  attempt IS the finding, in which case state the finding, not the story.
- One sentence of motivation is enough before any method; the reader needs
  to know what the method does, not why every design choice beat its rivals.
- Grainy operational detail (thresholds, file mechanics, tuning history)
  belongs in an appendix or nowhere.
- Test for every paragraph: could a stranger read it once and say what was
  done and what was found? If not, simplify or cut.

Calibration:
Old: "After the first round revealed that the models were exploiting
document metadata, a second pre-registered round was designed in which..."
New: "School and trust names, dates, and page furniture were removed from
the text before modelling."
