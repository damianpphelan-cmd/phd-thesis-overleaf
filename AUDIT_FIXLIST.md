# Thesis Audit — Working Fix List

**Audit date:** 31 July 2026
**Worked through:** 31 July – 1 August 2026
**Scope:** Chapters 2 and 3, thesis LaTeX tree, `analysis_dataset.csv`, scoring/build scripts.
**Not covered:** Chapter 4 (separate project), Chapters 1 and 5 (scaffolding only).

**Status legend:** `[ ]` to do · `[~]` in progress · `[x]` done · `[!]` blocked / needs your decision

**Headline:** the core Chapter 3 finding replicates cleanly (independent HC3 run: β_W = 0.128,
β_S = 0.115, N = 95, R² = 0.598 vs reported 0.127 / 0.120 / 0.595). The problems were in the
layer between the data and the prose, not in the research.

---

## Current state — 1 August 2026

**Done:** A1 · A2 · A3 · A4 · A5 · A5b · A6 · **A7** · A8 · A9 · A11 · **A13** · B1–B9 · **B9c** · C1 · C2 · C3
**Blocked on you:** A10 (acknowledgements, funding) · C3 residue (Paper 3 sentences) · **A14**
**Open, added 8 Aug 2026:** **B10** (BP scores are clustered — needs digest-clustered SEs; also
supplies the reliability figure §B9b was missing, for free) · **B11** (5 wrong documents)

### [ ] A14 — Chapter 3 is estimated on 102 schools; there are 103 (opened 5 Aug 2026)

Every regression, descriptive table and figure in Chapter 3 comes from a Stata run that
predates the URN join. The join added URN 136538 (Trinity CofE), taking the gold standard
from 102 schools to 103. Checked against `analysis_dataset.csv` on 5 Aug 2026: **all 103
full-tier schools have non-missing P8, KS2, FSM and enacted scores**, so 102 is not listwise
deletion — it is one school short.

Chapter 3 says "102" in about ten places (L16, 62, 297, 478, 499, 845, 903, 921, 1133) and
the Stata-generated tables (`tab_control_stats`, `tab_outcome_stats`, `tab_tier_summary`,
`tab_main_results*`) all carry $N = 102$. Appendix~3A and `tab_score_controls_corr` were
regenerated on 5 Aug and now correctly say 103, so **the chapter is currently inconsistent
with itself**. Leaving the two correct tables in place rather than reverting them to 102: the
right fix is to re-run, not to re-stale.

Fixing it needs a Stata re-run of `chapter3_analysis.ipynb` end to end, plus
`make_outcome_stats.py`, `make_tier_summary.py` and whatever regenerates `tab_control_stats`
(no generator found — it may be hand-maintained, which would make it the fifth). Coefficients
will move slightly. Not started; needs Damian's go-ahead because it re-writes Chapter 3's
headline numbers.
**Needs your decision:** the behaviour-policy scores are **not reproducible** — `temperature: 0` is
silently dropped by gpt-5-nano, and 3 of 8 anchors moved on an identical re-run. Recommendation is to
measure and report the reliability (§B9b). File renamed to `…v26_national.csv`; anchor test done.
**Needs 30 minutes of your reading:** §B9d — the behaviour-policy rubric has **no out-of-sample
validity** (r = −0.000, n = 98, where the Ofsted score reaches +0.396 on the same schools).
`bp_heldout_anchor_sheet.csv` — 15 held-out schools — is built and waiting for your target labels;
it settles whether the rubric or the source is at fault, and needs no API calls.
**Bibliography:** verified against the upgrade report — 23 confirmed, 7 corrected, 4 CONFIRM flags
and 16 post-2022 entries still to source

Verification as of the last run:

```
cross-references   118 labels · 187 references · 0 dangling · 0 duplicate
bibliography       49 entries · 0 cited-but-missing · 0 unused
generators         make_numbers --check              33 canonical figures, no drift
                   make_prompts --check              in sync
                   make_instruments --check          in sync
                   make_outcome_stats --check        matches analysis_dataset.csv
                   make_national_strictness --check  matches a7_estimates.csv
tables             fix_tables --check                all 31 clean (incl. BEL-corruption guard)
snippets           5/5 pure ASCII, braces and environments balanced
```

Nothing here has been compile-verified — there is no LaTeX toolchain on this machine.
The checks above are structural (encoding, braces, environments, labels, citation keys),
which catches the error classes that were actually present, but a real `pdflatex` run
on Overleaf is still the last step before you trust it.

---

## A. Must fix before submission

### [x] A1 — Reframe Model A: the LOO-CV validation is circular

**Where:** [02_paper1.tex:827-843](chapters/02_paper1.tex#L827-L843), `tab_interview_model_loo.tex`

Model A predicts `gs_warmth_composite` using `gs_W3_adj` as a feature — but W3\* is 40% of that
composite by construction. The model is partly predicting a quantity it was handed.

```
corr(gs_W3_adj, gs_warmth_composite) = 0.758
Model A warmth LOO-CV r (reported)   = 0.765     <- same number
```

Against the observationally independent part (the visit component the model must actually infer):

| | vs composite (reported) | vs visit only |
|---|---|---|
| Model A warmth | r = 0.765 | **r = 0.267** |
| Model A strictness | r = 0.701 | **r = 0.276** |
| Model B warmth | r = −0.018 | r = −0.081 |
| Model B strictness | r = 0.329 | r = 0.364 |

**Fixed by:** reframing Model A as *score construction*, not out-of-sample validation; stating
explicitly that W3\*/S3/S4 are components of the outcome; adding `tab_ridge_circularity` reporting
the r ≈ 0.27 visit-component figures alongside the LOO numbers; removing the "large incremental
signal" claim.

---

### [x] A2 — Regenerate the Ofsted convergent/discriminant validity table

**Where:** [02_paper1.tex:1123-1155](chapters/02_paper1.tex#L1123-L1155)

Not one of the eight cells reproduced from current data. All eight replaced with recomputed values
(Panel A n = 299, Panel B n = 101 — one gold-standard school has no Ofsted score, so not 102).

**The discriminant conclusion genuinely reversed** and the surrounding prose was rewritten, not just
the numbers: Ofsted *strictness* predicts interview warmth (+0.137) better than Ofsted *warmth* does
(+0.017). Superseded rubric labels ("v3"/"v5") corrected to unified v3 / warmth v11.

The table note's `r = 0.647` for warmth × strictness is gone. (The `0.647` still in the chapter at
[L1123](chapters/02_paper1.tex#L1123) is an unrelated RMSE — checked, not a leftover.)

---

### [x] A3 — Fix `r = 0.483` in the abstract

**Where:** [02_paper1.tex:22-23](chapters/02_paper1.tex#L22-L23), also L1021 and L1113

`0.483` no longer appears anywhere in Chapter 2. The LOO-CV figure is now correctly **0.329**, and
the raw convergent correlation is **0.418** (vs visit, n = 101). Companion warmth claim at L1023
corrected to r = 0.012, p = 0.908, n = 101.

Guarded against recurrence: `make_numbers.py` carries `0.483` as a stale literal, so reintroducing
it fails `--check`.

---

### [x] A4 — Resolve the headteacher continuity claim

**Where:** [03_paper2.tex:462-476](chapters/03_paper2.tex#L462-L476)

There is no continuity-since-interview variable in `analysis_dataset.csv`. The only headteacher
variable is `ofsted_HeadteacherChanged` (continuity since the *Ofsted inspection*), missing for 72
of 102 Tier 1 schools — which is why `tab_continuity_robustness` has N = 23, exactly the `False`
count.

**Fixed by** rewriting §sec:p2_continuity to describe what actually exists, dropping the false
"included as a control in all main specifications" claim, and stating the n = 23 sign flip openly
as a power problem rather than leaving it in an unreferenced table.

**Still worth doing if you have time:** building a genuine continuity-since-interview variable from
the GIAS snapshot would turn this from a limitation into a robustness check.

---

### [x] A5 — Fix ~28 broken cross-references

All eight estout tables now carry `\label`. All six previously-orphaned tables are now `\input`.
All other dangling refs resolved. Final audit: **118 labels, 187 references, 0 dangling,
0 duplicates.**

### [x] A5b — Make the labels survive Stata regeneration

`thesis/fix_tables.py` restores labels and un-escapes math subscripts after any regeneration,
idempotently and without touching line endings (esttab writes LF; a naive rewrite would turn a
one-line fix into a whole-file diff). Round-trip tested: strip a label, re-escape a subscript, run
the script, and the file returns byte-identical to the original.

```
python thesis/fix_tables.py --check    # exit 1 if anything needs fixing
python thesis/fix_tables.py            # repair in place
```

Run it after **every** Stata table regeneration. Documented in [PIPELINE.md](../PIPELINE.md) Stage 4.

---

### [x] A6 — Fix the W3 compression passage (wrong variable)

**Where:** [02_paper1.tex:1460-1489](chapters/02_paper1.tex#L1460-L1489)

| Claim | Actual |
|---|---|
| mean 4.08 | 4.078 ✓ |
| SD 0.44 | **0.386** |
| 84% score exactly 4 | **12.2%** |

The 84% belonged to `trx_LLMWarmthScore`, not W3. (W3 is not carried into `analysis_dataset.csv` at
all — only the quality-adjusted W3\* is — which is how the two got confused. The true figures come
from `scores/warm_strict_scores.csv`.)

**The argument was broken, not just the arithmetic,** and the repair is more than a number swap.
The passage used that statistic to argue compression reflects *genuine homogeneity* rather than
*instrument artefact* — but its real source is an LLM score, i.e. precisely the instrument-artefact
case. Rewritten so the two sources are distinguished by **distribution shape**, which the data
actually supports:

- **W3** (researcher-coded): mean 4.08, SD 0.39, spanning 2.60–5.00, only 12% at the mode.
  Narrow but smooth — a real distribution over a homogeneous population.
- **LLM transcript scores**: 84% (warmth) / 85% (management) / 78% (strictness) at exactly 4.
  Not compression — an instrument that has stopped discriminating.

That contrast is now the paragraph's evidence, and it argues for the conclusion instead of against
it. Both halves are in `make_numbers.py --check`, with the old wording registered as a stale literal.

The parallel management claim at L1499 ("85 per cent scoring exactly 4") **was always correct** (84.8%).

---

### [x] A7 — Add the pre-COVID grade row to the national strictness table

**Where:** [03_paper2.tex:682-720](chapters/03_paper2.tex#L682-L720), `tab_national_strictness.tex`
**Done:** 1 August 2026, Stata run approved and executed.

The spec omits the Ofsted grade control "to avoid conditioning on a downstream confounder". That's
defensible but it is *not* the conservative choice: the LLM strictness score is read from a report
about a school Ofsted judged, and Ofsted grades correlate with P8. The obvious examiner challenge
is that β = 0.135 partly measures "Ofsted approved of this school".

**The result survives, and more cleanly than the Python trial run suggested.** Stata, HC3,
`a7_national_strictness.do`:

| Specification | N | β_strictness | R² |
|---|---|---|---|
| Panel A — no Ofsted grade (thesis spec) | 3,148 | +0.135\*\*\* | 0.506 |
| Panel B — with pre-COVID 2019 grade | 2,820 | **+0.136\*\*\*** | 0.518 |

Conditioning on the inspection verdict absorbs essentially none of the association — overall P8
moves 0.135 → 0.136, and no component moves more than 0.005 (largest: English 0.124 → 0.128).
All five stay significant at 1%.

**Panel A reproduces the published table exactly** (β = 0.1350, N = 3,148, R² = 0.5060), which
validates the do-file as a faithful replication of notebook cells 0–2. It also **supersedes the
Python approximation recorded during the audit** (which gave β = 0.141 at N = 3,194 for the
no-grade spec and 0.131 for the 2019-grade spec): that run used a slightly different
listwise-deletion sample. Trust the Stata numbers.

**Caption discrepancy resolved.** The old caption's "N ≈ 3,194" was simply wrong — Stata's no-grade
spec is N = 3,148, matching the N row. The regenerated caption carries no N at all, and both sample
sizes are now stated in the table notes.

Table is generated, not hand-edited: `thesis/make_national_strictness.py` builds it from
`tables/a7_estimates.csv`, with `--check` to detect drift.

---

### [x] A8 — Numeric errors in Chapter 3 prose

All eight corrected. The two that mattered most:

- **L610** "change by at most six per cent" was true for overall P8 only; Open warmth actually falls
  32% (0.124→0.084) and loses significance. The Conclusion's 68–109% was right and the Results
  section was wrong — the Results section now matches.
- **L842** "three of four" contradicted L640's "every espoused coefficient is insignificant". It is
  **four of four**; L640 was right.

Also fixed: seven→six of eight cells; the 303/102/95 three-way N inconsistency; 3,311 full-file
counts mislabelled as the analysis sample; 63–91% → 63–106%; p = 0.021 → 0.016; R² 0.46–0.51 →
0.462–0.535.

---

### [x] A9 — Correct model / version / date claims in Chapter 2

| Where | Was | Now |
|---|---|---|
| v6 scorer | `gpt-5-nano` | `gpt-5-mini-2025-08-07` (script default) |
| Ofsted LLM subcomponents | scores four then holistic | holistic only; subcomponent scoring was removed — **but the chapter text was NOT actually changed until 4 Aug 2026, see A13** |
| Interview dates | 2022/23 and 2023/24 | Nov 2023 – Apr 2025 |
| National run | 3,322 schools | 3,333 rows, 3,330 analysed, 3 errors |

The `gpt-5-nano` references for the **Ofsted and behaviour-policy** scorers were checked separately
and are correct — both scripts default to nano and both output CSVs record `LLMModel = gpt-5-nano`.
All bare model names are now in `\texttt{}` for consistency.

**Also fixed while here:** W3\* was written two ways in the same chapter — `$W3^*$` with quality
weight `$\omega$` in the body, `$W3^{\text{adj}}$` with `$q$` in Appendix 2A. Unified on the body's
notation.

---

### [~] A10 — `main.tex` front matter placeholders

- [x] `[Your Full Name]` in the signed Declaration → Damian Phelan
- [x] `[Abstract goes here...]`
- [ ] `[Acknowledgements go here.]` — **yours to write**
- [ ] `[Acknowledge any funding sources here...]` — **yours to write**

---

### [x] A11 — 34 cited works had no bibliography entry *(found during the run; not in the original audit)*

Not on the original list, and the largest undiscovered defect in the thesis. `bibliography.bib` held
15 entries against 49 cited keys: **the reference list was under a third complete**, and 34
citations would have printed as `[?]`.

All 34 added. The `.bib` now has 49 entries, and the final audit shows 0 cited-but-missing and
0 unused.

> **All 34 need checking against the source before submission** — they were reconstructed from the
> citing sentence, not from a library record. Eight are flagged `% CONFIRM` in the file where the
> citing sentence did not uniquely identify the work, or where the year in the key disagrees with
> the publication year: `majumder2015` `zhang2020` `hamre2007` `sammons2008` `eyles2016` `eyles2019`
> `murphy2011` `hodge2021`. Start with those.

---

## B. Should fix

### [x] B1 — Leadership direction contradiction
Resolved in text: the pilot r = −0.739 on raw coding is **the same** as +0.739 against the reversed
grade, which is the form the r > 0.5 threshold was specified in. The national r = −0.588 is the same
direction at lower magnitude, and the attenuation is now explained by design — the pilot was
stratified across all four grade bands, which inflates the correlation relative to the national
distribution where most schools are Good.

### [x] B2 — `tab_espoused_enacted_gap` treats Ofsted as the *enacted* source
Justified explicitly rather than relabelled. The comparison runs at national scale where no visit
benchmark exists; Ofsted is the only source not authored by the school itself, and its strictness
signal converges with observed strictness at r = 0.418. That warrant is dimension-specific, so the
comparison is restricted to strictness and leadership, and the gaps are now framed as
self-description against external inspection rather than against the researcher visits.

### [x] B3 — Update Parent View correlations — *no change needed; the audit entry was wrong*
The chapter's +0.157 (p = .008, n = 289) and +0.242 (p = .020, n = 93) are **correct**. My audit
figures (+0.218 / +0.283) came from a different column pairing. Left as they were.

### [x] B4 — S4 / S4\* notation inconsistency
`S4^*` no longer appears. S4 is unadjusted throughout, matching the data.

### [x] B5 — Move Ch3 table `\input`s next to their discussion
All eighteen are now distributed through the chapter beside the prose that discusses them.

### [x] B6 — Fix math-mode escaping in `tab_enacted_espoused`
Subscripts render correctly, and `fix_tables.py` now repairs this automatically after any
regeneration rather than leaving it to be re-broken.

### [x] B7 — Regenerate `tab_tier_summary`
Regenerated: EAL% populated, Tier 2 N = 201.

### [x] B8 — State that Ridge Model B is a measurement exercise
Stated at [L1587-1593](chapters/02_paper1.tex#L1587-L1593), with the reason (regressing an outcome
on a shrunken prediction attenuates the coefficient unrecoverably) and the point that Model B's
failure is itself the informative result.

### [x] B9 — Repair or delete dead scripts; document the build order
- `ridge_diagnostics.py` repaired — it read two deleted files. **Three real bugs surfaced in the
  process**; the build now reproduces `analysis_dataset.csv` exactly (101 columns, all values
  identical).
- `chapter3_tier1_staged.py` documented as a Python **cross-check** by an independent route, not a
  replication — it runs N = 102 against the notebook's N = 95. Expect agreement in sign and rough
  magnitude only; if it disagrees on sign or significance, the notebook wins.
- The circular `build_analysis_dataset.py` ↔ `build_ridge_models.py` dependency is documented as a
  deliberate two-pass build in [PIPELINE.md](../PIPELINE.md) Stage 2.
- **[~] The behaviour-policy scores file is misnamed. Corrected 1 August 2026 — an earlier entry
  here said the opposite and was wrong.** `scores/behaviour_policy_analysis_results_v25_national.csv`
  (3,364 rows, gpt-5-nano) was **not** produced by v25. It was produced by the current
  `analyse_behaviour_policies_v3.py`, decision procedures and all, at `PROMPT_VERSION = v26`.

  **The evidence is in the output, not in inference.** 2,828 of 3,364 rows carry reasons that follow
  the numbered decision procedure and quote its wording ("Step 1 finds positive culture content
  beyond aspirational statements", "named rewards mechanism"). The **second row of the file** already
  does, and rows are appended in input order, so the procedure was live from the first minute of the
  run. Mean scores are flat across the file (block SD 0.049 strictness, 0.064 warmth over 17 blocks
  of 200) — URN order is arbitrary with respect to school character, so a mid-run prompt change would
  have shown as a step, and there is none. And Longdean (URN 137110) scores **S=2** here against
  **S=1** in the v25 anchor run, on the same PDF with a cached extraction: the rule changed, not the
  document. Its reason reads "Step 1: … yields S=2".

  The v25 rubric descriptors are still in the file ("WHAT DOES NOT QUALIFY", "necessary and
  sufficient"). The procedure was layered **on top of** them, not swapped for them.

  **Restoring an old copy of the script does not help, and would mislead.** An earlier revision gives
  the code behind the *anchor* results, not the code behind the scores in use. The current file **is**
  the reproduction path for the national scores — keep it. Equally, do not edit the string back to
  v25: that would put a false label on unchanged behaviour.

  **Renamed, 1 August 2026.** The file is now
  `scores/behaviour_policy_analysis_results_v26_national.csv`. Four consumers updated:
  `build_analysis_dataset.py` (step 11), `ridge_spec_comparison.py`, `PIPELINE.md`, and
  `ch3_completion_notes.md` §G5.

### [ ] B9b — The behaviour-policy scores are not reproducible **(new, 1 August 2026)**

The 8-anchor test was re-run against the current code on the same eight documents the national run
scored (`bp_8_anchor_test_input.csv`, rebuilt — it had been deleted; output in
`scores/bp_anchor_test_v26_2026-08-01.csv`).

| School | target | v25 | in thesis | re-run |
|---|---|---|---|---|
| Hammersmith Academy | S4 W4 | S4 W4 | S4 W4 | **S5 W3** |
| Longdean School | S1 W1 | S1 W2 | S2 W2 | **S2 W3** |
| School 21 | S3 W3 | S3 W3 | S3 W3 | S3 W3 |
| Michaela Community School | S5 W2 | S5 W2 | S5 W2 | S5 W2 |
| Hall Park Academy | S3 W3 | S3 W3 | S3 W3 | S3 W3 |
| Mossbourne Community Academy | S3 W3 | S3 W3 | S3 W3 | S3 W3 |
| West London Free School | S4 W3 | S5 W3 | S5 W3 | S5 W3 |
| Mercia School | S5 W4 | S5 W3 | S4 W3 | **S5 W3** |

**v25 13/16 · scores in the thesis 11/16 · re-run today 10/16.**

**Three of eight schools scored differently on identical code and identical documents** — 4 of 16
dimension-scores moved, every one by a full point.

**Cause, verified against the live API.** `analyse_behaviour_policies_v3.py` sets `"temperature": 0`,
then catches the resulting error and silently re-sends **without** it. gpt-5-nano rejects the
parameter outright (*"Unsupported parameter: 'temperature' is not supported with this model"*). So
every behaviour-policy score in the project was drawn at **default sampling**; that line has never
had any effect. The fallback now warns once per run instead of passing silently.

**This weakens the version comparison rather than settling it.** The run-to-run noise is the same
size as the gap between versions, so 13 vs 11 vs 10 does not show that v25 beats v26 — it shows a
single run of this measure is not a stable quantity. It also propagates: `bp_LLMStrictnessScore`
feeds the Ridge models and Chapter 3's national extension.

**Also corrected:** the anchor URNs recorded for West London Free School (136721) and Mercia (143498)
were wrong — those are Bishop Creighton Academy and Marus Bridge Primary School. Correct: **136750**
and **145897**. Both are in the national file, so the earlier "absent from the national file" claim
was my URN error, not a gap in the data.

**Your call, one of:**
(a) **Report it.** Score each school k times (k=5, majority vote per dimension); publish the modal
    score plus the disagreement rate as a reliability statistic. Turns the defect into a measurement
    property, which is the defensible position. Costs ~5 × 3,364 calls.
(b) **Re-run once and disclose.** Cheapest, but leaves the reliability question open for an examiner.
(c) **Switch to a model that honours `temperature=0`** and re-run. Removes the noise but changes the
    measure, so the anchor calibration has to be redone from scratch.

**Recommendation: (a).** A stated reliability figure is far stronger than a silent assumption of
determinism, and it is the honest answer to "would you get these numbers again?" Do not overwrite the
existing scores file under any option.

---

### [x] B9c — Model IDs pinned; the same temperature bug found and fixed in the Ofsted scorer **(1 August 2026)**

Every scorer asked for a **floating alias** (`gpt-5-nano`, `gpt-4o-mini`) rather than a dated
snapshot. An alias is a pointer the provider may repoint at will, and old snapshots are retired. The
day that happens, nobody — including us — can reproduce any score in the thesis: prompt, rubric and
input document all survive, and the thing that turned them into a number does not.

`model_pins.py` is now the single source of truth (alias → dated snapshot), and
`check_model_pins.py --check` guards it in the same style as the six existing `--check` scripts.

**The trap that nearly made this worse.** The model string is hashed into the response-cache key in
**6 of the 8 scorers**. Rewriting the alias before the key is computed would have orphaned ~17,000
archived responses in `_llm_cache/` — the strongest replication evidence the project has — in the
name of improving replicability. The rule, now enforced in code and comments: **resolve at the API
boundary only**; cache keys keep the caller's string. Verified after the change: 200/200 cache hits
on each of the three live website archives.

**What can honestly be claimed about scores already collected.** Each alias used has **exactly one**
dated snapshot in the provider's model list, so the resolution over the collection period is
unambiguous (`gpt-5-nano-2025-08-07`, `gpt-4o-mini-2024-07-18`, `gpt-5-mini-2025-08-07`); listing
archived at `docs/model_snapshot_listing_2026-08-01.txt`. What must **not** be claimed is that the
snapshot was recorded at the time — it was not, and the caches store only parsed results. Archives
written from now on carry a `model_resolved` field.

**Found while verifying: the website teaching scores were produced by `gpt-4o-mini`, not
`gpt-5-nano`.** The script *defaulted* to nano; the run of record used mini. Proved by recomputing
cache keys against the archive — 300/300 hit under mini, 0/300 under nano. A default that disagrees
with the run of record is a replication trap in itself; corrected. Any thesis text naming the model
for website teaching philosophy needs checking against this.

**The same silent temperature drop was live in `analyse_ofsted_reports.py`** — identical `try/except`
to the behaviour-policy scorer, and the Ofsted scores are a *used* predictor. Now warns once per run.
The Ofsted leadership scripts use `gpt-4o-mini`, which honours `temperature=0`, so they are unaffected.

---

### [ ] B9d — The behaviour-policy rubric has no out-of-sample validity **(new, 1 August 2026)**

"13 of 16 anchor dimension-scores correct" is an **in-sample fit statistic**: v21→v26 were all tuned
against those same eight schools. It shows the rubric can be made to reproduce the labels it was
tuned on, which is not the claim Chapter 2 needs.

Only **3 of the 8 anchors are Tier 1**, so 99 Tier-1 schools were never tuned on and already carry
v26 scores — a held-out test costing nothing (`validate_bp_heldout.py`, n=98):

| Comparison | Pearson r | |
|---|---|---|
| BP strictness vs composite strictness | **−0.000** | ns (p = 0.998) |
| BP strictness vs visit-only strictness | −0.034 | ns |
| BP warmth vs composite warmth | −0.194 | p = 0.056 (negative, as the aspiration effect predicts) |
| **Ofsted strictness — same 98 schools** | **+0.396** | *** |
| **Ofsted strictness vs visit-only — same 98 schools** | **+0.421** | *** |

Quintile contrast, which survives the coarse 1–5 granularity: the BP score separates the strictest
fifth of schools from the least strict by **+0.24 points (ns)**; the Ofsted score by **+1.00
(p = 0.001)**. In-sample on the anchors: 11/16.

**The benchmark is what makes this interpretable.** A weak correlation from a well-behaved instrument
on a hard construct looks identical to a weak correlation from a broken one. Ofsted reaching r ≈ 0.4
on the identical schools shows the construct *is* measurable from text and this instrument does not
measure it. Consistent with the earlier Ridge diagnostic (r = −0.097).

**Live consequence:** `build_ridge_models.py` uses `BP_S = ['bp_LLMStrictnessScore']` as a Model B
feature, so `pred_b_strictness` — powering Chapter 3's ~3,095-school national tier — is built partly
on this. Note `ridge_spec_comparison.py` cannot answer the question: BP features appear in all four
of its specifications. The existing with/without evidence is the Ridge diagnostics table
(Ofsted-only R² = 0.095 vs Ofsted+BP R² = 0.100 for strictness), which suggests the practical damage
is small because Ridge shrinks a useless feature toward zero. **Cheap check, no API calls:** re-fit
Model B without the BP features and compare `pred_b` and the national β. If they barely move, say so
in Chapter 2 — that converts a vulnerability into a robustness result.

**Needs Damian — the one part that cannot be automated.** The result above cannot separate two very
different failures: (i) the rubric reads policy documents faithfully and policy documents simply do
not encode enacted strictness — the espoused/enacted structural finding, i.e. evidence *for* the
argument Chapter 2 already makes; or (ii) the rubric reads policy documents unreliably, in which case
every BP number is noise and the structural claim cannot rest on it. Only a held-out **anchor** test
separates them, and the target labels have to be Damian's own reading or the test is circular.

`bp_heldout_anchor_sheet.csv` is built and waiting: **15 held-out Tier-1 schools stratified across
human-coded strictness** (stratified on the *human* score, so it cannot hand-pick agreement). Fill in
`TargetStrictness` / `TargetWarmth` from the policy documents, then run `compare_bp_heldout_anchors.py`.
The model's scores are deliberately withheld in a separate file so the labelling stays blind, and
**no API calls are needed at any stage** — the v26 scores for these schools already exist. The report
prints the answer-the-mode baseline (~60%); beating *that* is the bar, not beating zero.

---

### [ ] B10 — Behaviour-policy scores are **clustered**, not independent, and the clusters hand us a free reliability estimate **(new, 8 August 2026)**

A corpus-wide duplicate scan (`scratchpad/duplicate_documents.py`, zero API calls) hashed the
extracted text of all 3,327 national behaviour policies:

```
3,318 readable · 3,075 distinct documents · 90 shared by 2+ schools · 333 schools (10%)
group sizes: 48×2 · 10×3 · 10×4 · 7×5 · 8×6 · 4×9 · 1×11 · 1×15 · 1×22
```

**Almost all of it is trusts, as expected** — every large group is a multi-academy trust
publishing one policy that each academy links: Outwood 22, Delta 15, Northern Education Trust 11,
Inspiration 9, David Ross 6, Scholars' Education Trust 6. Only 5 schools of 3,327 hold a document
that is genuinely wrong for them (§B11).

**The inference consequence.** `bp_LLMStrictnessScore` and `bp_LLMWarmthScore` are **not 3,327
independent observations**. Every academy in a trust receives a mechanically identical score from
a mechanically identical document, so the effective N for anything BP-based is nearer **3,075**,
and the largest trust is one data point entered 22 times. Any regression, correlation or standard
error using a BP variable needs **standard errors clustered on the document digest** — which
nothing in the pipeline currently does. This bites hardest in Chapter 3's national tier, where
`pred_b_strictness` is built partly on BP features.

The digest for every affected school is in `scores/_duplicate_documents.csv`, so this is a join,
not a re-run: add the digest as a cluster variable (singletons cluster on themselves) and re-fit.
No API calls.

**The by-product is more valuable than the problem: this is a reliability sample.** The national
run scored each shared document **once per school**, independently, not knowing the texts were
identical. So each group is a repeat measurement of one document with **no true-score variation to
confound it** — a far better test–retest design than the 8-anchor re-run in §B9b, and it costs
nothing because the runs already happened. Verified before use: all 778 pairs match on
`BodyChars`/`CompanionChars`/`CompanionCount` (identical prompt input), the school name is not
injected into the prompt, and pairs where **both** rows were cache hits agree no *more* than the
rest (86.6% vs 93.3% strictness; 78.4% vs 78.3% warmth) — so no pair is sharing one cached
response, and every score was a real call.

| scorer | model | documents | repeat pairs | exact | within 1 |
|---|---|---|---|---|---|
| **v30 strictness** (current) | gpt-4o-mini | 84 | 778 | **88.2%** | 99.9% |
| **v31 warmth** (current) | gpt-4o-mini | 84 | 778 | **78.4%** | 97.2% |
| v26 strictness — **the scores in the thesis** | gpt-5-nano | 90 | 863 | **65.4%** | 97.5% |
| v26 warmth — **the scores in the thesis** | gpt-5-nano | 90 | 863 | **66.6%** | 99.3% |

**This settles §B9b's open question with a real number instead of eight schools.** The scores
currently in Chapter 2 and feeding Chapter 3 reproduce on identical input about **two times in
three**. The 22-academy Outwood group is the cleanest illustration: one document, scored 22 times,
returns 3 eight times, 4 twelve times and 5 twice. The rebuilt v30/v31 scorers are materially
better (gpt-4o-mini honours `temperature=0`, which nano silently dropped), and warmth is the
weaker of the two at 78%.

**Recommended, and cheaper than §B9b option (a):** report this table as the instrument's
reliability rather than paying ~5 × 3,364 calls for a k-fold re-scoring design. It is a larger
sample than a bespoke reliability run would buy, and it was collected under live conditions.
Caveat to state alongside it: the duplicate groups are trust documents, which are longer and more
formulaic than average, so this is reliability on *that* stratum, not proof of the corpus-wide rate.

### [ ] B11 — Five schools hold the wrong document **(new, 8 August 2026)**

| URN | school | holds |
|---|---|---|
| 141105 | Holy Trinity School | Trinity High School's policy (137167) — download row says `no_match`, so the file came from another pass. Unambiguously a pipeline fault |
| 136579 | The Appleton School | NCEA Duke's Secondary School's policy (135886) |
| 137612 | Range High School | Meols Cop High School's policy (149828) |
| 136102 | Co-op Academy Stoke-On-Trent | the **DfE's own statutory guidance**, "Behaviour in Schools: Advice for headteachers and school staff", Feb 2024 |
| 147177 | Co-op Academy Grange | same DfE guidance |

Appleton's and Range's copies were downloaded **from those schools' own websites**, so the school
may genuinely have published another school's document — that is a finding about the school, not
only about the pipeline. Damian is tracking down replacements. 5 of 3,327 does not block anything;
carry a flag and drop them at analysis time.

Separately resolved and **closed**: 13 schools whose selected document was the *sixth form's own*
behaviour policy. All 13 replaced on 8 Aug 2026 and the detector now returns zero.

---

## C. Worth doing if time allows

### [x] C1 — Populate `snippets/numbers.tex`
Populated with 33 canonical figures, all but the Stata-sourced ones recomputed from
`analysis_dataset.csv` on every run. The mechanism that earns its keep is `--check`, which scans the
chapters for the literal that should be there *and* for known-stale literals — the values corrected
during this audit. Ten stale values are now live traps; reintroduce one and the check fails.

```
python thesis/make_numbers.py            # write the snippet
python thesis/make_numbers.py --check    # scan chapters for drift (exit 1 if any)
```

Note the file is deliberately **not** `\input` by `main.tex` — the chapters keep their figures as
literals, which stays readable and diffable, and the macros exist for `--check` to compare against.
The header says so, so it doesn't read as an oversight.

Same pattern now covers the LLM prompts (`make_prompts.py`) and the instruments
(`make_instruments.py`). The last of those parses `warm_strict_scorer.py` with `ast` and **fails if
the scorer uses an item the appendix does not describe**, so the sub-score table cannot silently
drift from the code that produces the scores.

### [x] C2 — Cite the gpt-5-mini pilot as supporting evidence
Cited at [L1299-1306](chapters/02_paper1.tex#L1299-L1306). It strengthens the argument: re-scoring
with a larger model leaves the warmth null unchanged (r = 0.055, p = 0.598), so the missing signal
is in the Ofsted source text, not the scoring model.

### [~] C3 — Clear remaining `INSERT` markers
All cleared except four, every one of which is yours to write:

- [02_paper1.tex:9](chapters/02_paper1.tex#L9) — acknowledgements, funding
- [03_paper2.tex:8](chapters/03_paper2.tex#L8) — acknowledgements
- [main.tex:81](main.tex#L81) — one to two sentences summarising Paper 3
- [01_introduction.tex:53](chapters/01_introduction.tex#L53) — one to two sentences on Paper 3

The three Chapter 2 appendices that were `INSERT` markers are now real content, generated from your
own `.docx` proformas rather than transcribed: the interview guide (301 lines), the visit protocol
(317 lines), and the item→sub-score mapping table.

### [ ] C4 — Sync Overleaf from GitHub
The `thesis/` tree is committed and pushed. **Pulling into Overleaf is a manual step only you can
do** — Overleaf → Menu → GitHub → Pull.

---

## Chapters 1 and 5 — deliberately not drafted

`01_introduction.tex` and `05_conclusion.tex` are still scaffolding. Two unambiguous fixes were made
to Chapter 1 and nothing else:

- The **Motivation** prompt described a project about what school websites convey. That is not what
  the thesis became — websites are one of four public text sources in Chapter 2, and the null result
  on them is a supporting finding, not the research question. Replaced with a prompt matching the
  chapters as they stand, with a dated note explaining why.
- The **Overview** section now has real paragraphs describing Chapters 2 and 3, since those chapters
  exist and summarising them is mechanical.

Everything else in both chapters is substantive authorship of your argument, and Chapter 5 cannot be
written at all until Paper 3 exists. **Say the word and I'll draft either.**

---

## Framing issues to pre-empt in the viva

Not errors — points where the current text invites a challenge it could answer better.

- **Stage 3 R² equals Stage 1 R² to three decimals (0.595).** Teaching adds literally nothing.
  Legitimate finding, but stated flatly it invites "then your teaching instrument doesn't work".
  The correlated-measurement-error defence at [L830-832](chapters/03_paper2.tex#L830-L832) is
  right — promote it rather than burying it.
- **The Att8 2024-25 robustness column** sits awkwardly beside the argument that 2024-25 is
  unusable for lack of a KS2 baseline. Needs a sentence.
- **The n = 23 continuity subsample** (see A4) will be found. Now addressed in the text, but expect
  the question.

---

## Verified correct — do not re-check

These reproduce exactly from `analysis_dataset.csv`:

- **Ch3 headline result.** Independent HC3 run: β_W = 0.128 (SE 0.041, p = 0.002),
  β_S = 0.115 (SE 0.044, p = 0.009), N = 95, R² = 0.598 vs reported 0.127 / 0.120 / 0.595.
  *(Small differences are my reconstruction of the control set, not errors.)*
- **The four warmth nulls.** Ofsted +0.008 · behaviour policy −0.082 · website −0.015 ·
  transcript +0.080 (n = 96–102). The central negative finding is solid.
- **Ofsted strictness convergent validity:** +0.418 vs visit strictness (n = 101, p < 0.001).
- **GS descriptives:** warmth mean 6.795 / SD 0.901, strictness 7.094 / SD 0.715, ranges exact.
- **Prediction SDs:** Model A 0.714 / 0.423; Model B 0.087 / 0.237.
- **Both LOO tables** (auto-generated by `build_ridge_models.py` — which is why these survived).
- **Stage 1→3 attenuation in the Conclusion:** warmth 68–109%, strictness 84–104%. Correct.
- **Management discourse compression:** 84.8% score exactly 4. Correct.
- **Parent View correlations** +0.157 and +0.242. Correct — see B3.
- **Structural stability / ICC analysis** throughout Appendix 3A.

---

## Closed threads

**gpt-5-mini Ofsted pilot — it doesn't help.** Same 39 schools:

| | warmth SD | warmth r vs visit | strictness r vs visit |
|---|---|---|---|
| gpt-5-nano | 0.576 | −0.184 | **+0.658** |
| gpt-5-mini | 0.552 | −0.059 | +0.414 |

No gain in spread, still no warmth signal, strictness materially worse. Useful negative: the missing
warmth signal is in the Ofsted source text, not the scoring model. **Don't spend more on model swaps
for Ofsted warmth.** Cited in the chapter — see C2.

**Two things found in your proformas** while generating the appendices, both minor and both yours to
decide about:

- The **S9 Likert statement** in `Headteacher Interview.docx` ("Teachers feel respected by all
  students") carries a stray `4` in the blank proforma — a value left behind from a filled-in copy.
  `make_instruments.py` strips it via a documented `FIXUPS` entry, but the source document is worth
  correcting.
- **S10 (parental engagement)** is collected in the interview but feeds no sub-score. Either wire it
  in or note it as collected-but-unused.

**Visit scores are averaged, not agreed.** `warm_strict_scorer.py:378` takes
`groupby("school").mean()` across observers and across lessons. An earlier draft of the appendix
said the final score is the agreed value — corrected in both the appendix prose and the generated
snippet headers.

---

### [x] A13 — Ofsted LLM sub-components removed from the models and the thesis (4 Aug 2026)

Damian's ruling: an older Ofsted rubric scored four sub-components feeding each
holistic score; given how short inspection narratives are, this was an
overcomplication and comes out of the models and the thesis entirely.

**Measured before acting, on the 101 Tier 1 schools in
`scores/ofsted_analysis_goldstandard_v7.csv` — the only file where these columns
ever varied.** The four facets are not four measurements:

| | strictness | warmth |
|---|---|---|
| schools scoring **identically on all four** facets | 34.7% | **77.2%** |
| mean within-school spread across the four (1–5 scale) | 0.83 | **0.25** |
| median facet intercorrelation | 0.569 | 0.734 |
| best facet's r with the holistic score | 0.949 | 0.953 |

**A live thesis claim was an artefact.** Appendix 2A said enforcement consistency
was "the strongest predictive signal" among the strictness facets. Enforcement
consistency also had the widest spread of the four (sd 0.93 vs 0.68–0.70). When
four near-clones compete, the one with the most variance wins by construction.
That is a property of the noise, not a finding about inspection reports.

**Independent support:** the redesign work measured that bundling constructs into
one API call roughly doubles their intercorrelation (+0.128 split → +0.300
bundled on the website corpus). Sub-components asked in the same call as the
holistic score are the most extreme case of bundling there is.

**Changed:**

| File | Change |
|---|---|
| `analyse_ofsted_reports.py` | 8 fields dropped from `LLMScoreResult`, `parse_llm_result`, the output row, and `FIELDS` |
| `rescore_ofsted_national.py` | same 8 columns dropped from `FIELDS` and the row builder |
| `ridge_spec_comparison.py` | specifications (B) and (C) removed; now (A) LLM holistic vs (D) keyword-rule only; docstring and table caption rewritten |
| `chapters/02_paper1.tex` §`sec:p1_text` | four-subcomponent method paragraph replaced with what the instrument actually does, plus a paragraph recording the withdrawal and the numbers above |
| `chapters/02_paper1.tex` L1276 | "Ofsted warmth subcomponents are excluded from the Ridge model" — clause dropped |
| `chapters/02_paper1.tex` L1358 | sub-score-correlation cross-reference to the heatmap deleted |
| `chapters/02_paper1.tex` App 2A | heatmap figure + paragraph deleted; spec-comparison passage rewritten from three results to two |

**(A) and (D) did not move**: warmth 0.220 / −0.002, strictness 0.265 /
degenerate — identical to the published numbers, because the specifications were
always estimated independently. All six `--check` scripts pass.

**Two loose ends, both deliberate:**

1. `figures/fig_C_subscore_heatmap.pdf` is now orphaned. Left on disk rather than
   deleted; nothing references it.
2. `ridge_spec_comparison.py` still reads `ofsted_analysis_goldstandard_v7.csv`,
   but **only for the two Ofsted keyword-rule columns now**. Those columns also
   exist, with variance, in `ofsted_analysis_results_v4_cutoff.csv`, which is
   reproducible where goldstandard_v7 is not. Removing the sub-components is what
   unblocked this — the swap was impossible while the script needed sub-scores.
   It would move specification (D)'s numbers, so it is left as Damian's call.

**Note on A9.** A9 recorded this same subcomponent correction as done. The chapter
text still described the four-subcomponent design when it was read on 4 Aug 2026,
so A9's row was aspirational. Marking a text fix complete in the fixlist is not
evidence the text was edited.

**Superseded in two places, 5 Aug 2026 (the no-blend ruling).** Recorded here rather
than edited above, because the entry is a record of what was true on 4 August:

1. "(A) and (D) did not move" is no longer the case. The outcome variable changed
   from `gs_*_composite` to `gs_*_enacted`, so the specification comparison was
   re-estimated against a different target: warmth is now $-0.028$ / degenerate
   (was 0.220 / $-0.002$) and strictness 0.339 / 0.094 (was 0.265 / degenerate).
   The substantive reading changed with it — "the LLM beats term-counting" now
   holds for strictness only.
2. `figures/fig_C_subscore_heatmap.pdf` was **deleted**, not left on disk. It was
   verified unreferenced by any `.tex` first.
