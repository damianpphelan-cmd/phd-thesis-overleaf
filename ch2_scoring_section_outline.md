# Chapter 2 — "Scoring documents at national scale" section skeleton

Drafted 14 Aug 2026 on Damian's instruction; approved structure to be turned
into tex in the writing pass. HIS TRANSPARENCY RULING (verbatim intent): "be
clear that the three independent raters here were not human but were three
Claude agents running the Opus model and that the tuning was done to try to get
gpt-4o-mini past the promotion bar." That framing governs subsection .2 and is
never softened elsewhere in the chapter.

## .1 The instruments and the two architectures
What an analyser is (document -> 1-5 score per construct). The two designs:
PROSE RUBRIC (a written marking scheme; the model judges holistically) vs
DECOMPOSED FACTS (narrow factual questions or verified counts; the band is
assigned by arithmetic in ordinary code, never by the model). One concrete
example of each (Ofsted prose; website warmth counts). Which design wins is an
empirical question answered per source in .5/.6.

## .2 Who did the labelling — model raters, a human anchor
THE TRANSPARENCY SUBSECTION. States plainly:
- The scoring model throughout is gpt-4o-mini (cheap enough to read ~3,300
  documents per instrument), with model pins recorded because the model is
  part of the instrument (.7).
- The reference labels the instruments were tuned against were produced by
  THREE INDEPENDENT CLAUDE AGENTS (Anthropic; Opus-class — pin the exact model
  identifier from the session records), each given only the written rule and
  the documents, blind to each other, to the researcher's labels, and to every
  model score; shuffled order; majority vote as the target. So the tuning
  question was: CAN A SMALL MODEL BE MADE TO REPRODUCE A LARGER MODEL'S
  READING OF THE RULE?
- Why this design: labelling capacity. The researcher wrote the rules, made
  the boundary rulings the raters could not (the adjudication log), labelled
  the earlier development packs himself, and agrees with his own labels two
  weeks apart at kappa_w +0.770 — which CEILINGS what any rater, human or
  model, can score against him (~0.88).
- The checks that make it defensible: researcher-vs-Claude agreement where
  both labelled the same documents; the determinacy test (.3); and above all
  the CRITERION ANCHOR — validity is always finally judged against the 103
  HUMAN visits (.4), which share no family with either model.
- The limitation, stated not buried: a rater from the same model family as
  the scorer is not independent human ground truth; one measured incident
  where a Claude adjudicator sided with the scorer against the researcher is
  reported as evidence the risk is real, not hypothetical. Agreement figures
  in this chapter are therefore MODEL-MODEL agreement wherever the target is
  the Claude majority, and are labelled as such in every table.

## .3 The written rule as an instrument
Determinacy: three cold raters, written ladder only, no shared notes, agree at
kappa_w +0.77-0.96 across six rule packs — a rule that transfers is an
instrument; a rule that needs its author is not. The repair loop: where the
three passes split, the rung is under-specified and gets re-cut BEFORE any
scoring money is spent (two worked examples: Ofsted teaching's boilerplate
band-4; website strictness's band-2 split). "A ladder that needs a rater to
invent a resolution is under-specified."

## .4 The three tests, in order
(i) AGREEMENT with the reference labels on documents the instrument was not
tuned on (the bar; anti-collapse guard; tune/held-out splits). (ii) OUT-OF-
SAMPLE honesty: ~85 archived versions scored once on fresh documents — every
in-sample figure read high; selection discipline (choose on one half, quote
the other). (iii) VALIDITY: criterion against the 103 visits; external
registers where one exists (faith prominence vs the official register, AUC
0.960). The K1 clean test as the worked example of isolating what a score
actually reads.

## .5 What the tests taught (findings, each with its number)
- AGREEMENT AND VALIDITY ARE DIFFERENT AXES and can trade off: tuning toward
  the labels repeatedly SPENT criterion validity (strictness prose +0.43 vs
  best-agreeing flags +0.07). The shipped set is chosen on all three tests.
- ASK FACTS, NOT JUDGEMENTS (replicated three times; the one uphill version
  history is the one that swapped judgement questions for fact questions).
- A RUNG MUST NOT REST ON THE GENRE'S BOILERPLATE (99.1% of school websites
  use a care word; Ofsted's stock sentences).
- DECOMPOSITION CAN MANUFACTURE INDEPENDENCE: visits put r(W,S) at +0.589;
  the bundled prose call reproduces it (+0.578); separate flag calls return
  +0.01-0.16.
- THE MODEL IS PART OF THE INSTRUMENT: same rubric, model swap, agreement
  +0.63 -> +0.12; hence pins, and hence one frozen gpt-5-nano island kept for
  its external validation.
- GATING vs COUNTING: models under-fire yes/no presence questions and count
  better, but only when the rubric states fact-shaped inclusion clauses (the
  website warmth v18 build as the worked example).

## .6 The shipped instruments
One table: source x construct -> architecture, version, the three test
results, the standing caveat (Ofsted warmth's grade confound; website
warmth's floor; BP's aspiration reading; website strictness band 5 = 25
schools nationally, added for scale consistency on the researcher's ruling).
Pointer to the appendix rubric book. The per-source architecture rule (within
a comparison, one architecture) stated as the discipline governing every
contrast in Chapter 3.

## .7 Reproducibility and provenance
Nothing here is deterministic: temperature honoured/dropped, measured
test-retest ~92% per dimension (nano ~2 in 3 — disclosed for the island);
caches keyed on the full prompt; every score row carries prompt version,
rubric digest and model; the drift guard that keeps printed numbers derived.
One unscoreable document (broken font encoding) recorded as an error row.

## Appendix
The full rubrics (the Instrument Book content); per-instrument entries (what
it is, three-test results, what it must not be used for); the version-history
measurement note; the adjudication log summary.
