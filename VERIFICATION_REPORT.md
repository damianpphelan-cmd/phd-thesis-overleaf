# Number verification report — Chapters 2 and 3

**19 Aug 2026.** Brief: every number, figure and table in Chapters 2 and 3 traced back to the
source of its data and recomputed; Stata used where the chapter's estimates come from Stata;
Option A (re-estimate the eleven appendix tables on the primary specification); **no prose
changed where a new number could lead to a different conclusion** — those are listed under
*Held for Damian* below.

Companion files: `VERIFICATION_LEDGER.csv` (383 prose numbers, each with family, source and
status), `VERIFICATION_TABLES.csv` (41 tables, each with producer and verdict),
`verify/FINDINGS.md` (the running log with every recomputed value).

---

## 1. Headline

| | Count |
|---|---|
| Prose numbers inventoried (body + appendix prose, both chapters) | 383 |
| — verified OK by recomputation | 320 |
| — verified OK by trace to the out-of-sample run record (instrument kappas) | 6 |
| — stale / mis-sourced / mis-worded and **fixed** (conclusion unchanged) | 52 |
| — **held** for Damian (could bear on a conclusion) | 5 (+ 2 sentences without a number) |
| Tables | 41: 23 reproduce from their producer unchanged; 4 were stale and regenerated; 11 re-estimated in Stata on the primary spec; 3 hand tables recomputed cell by cell (two cells fixed); 2 not verified by rerun (stability variants, traced only) |
| Figures | 7: all content streams identical to the committed files after regeneration |
| Macros | 22 used; every definition checked; one moved (`\BetaNationalStrictness` 0.166 → 0.201, `\NNationalStrictness` 3,147 → 3,052) |

**The two passes before this (15 Aug audit and this one) agree on the shape of the problem:
every macro-guarded figure was right; every defect was an unguarded literal or an artefact
whose producer had fallen behind the data.** This pass closes that gap structurally: every
table now has a producer, and `check_pipeline.py` gains a stage-5 check that re-runs each
producer in `--check` mode and asserts the Stata CSVs are no older than the dataset.

---

## 2. Held for Damian — the numbers are right, the decision is yours

> **Update, same day: Damian chose (b) for H1/H2.** All three do-files now standardise (the enacted and espoused scores over the late-entry-excluded visited/interviewed schools; the national score over its estimation sample), every body table and macro is regenerated, and the body prose is requoted per SD (W 0.142, S 0.114; national 0.138/0.140). H3 remains held.

### H1. Chapter 3 coefficients are per POINT of the 0–10 scale, not per standard deviation (C3-1)
`ch3_estimates.do` regresses Progress 8 on the raw enacted scores; nothing in it standardises.
The chapter says "per standard deviation" in the abstract, Data ("entered per standard
deviation so that the two coefficients are comparable"), Results and the magnitudes
paragraph. The in-sample SDs are 0.99 (warmth) and 0.88 (strictness), so:

| | as printed (per point) | per SD (Stata, `primary_z` block in `ch3_appendix_estimates.csv`) |
|---|---|---|
| Warmth | 0.143 (p=.002) | **0.141** (p=.002) |
| Strictness | 0.131 (p=.007) | **0.115** (p=.007) |
| Warmth alone / Strictness alone | 0.218 / 0.228 | 0.216 / 0.200 |
| Stage 3: W / S / T | 0.131 / 0.126 / 0.024 | 0.130 / 0.111 / 0.020 |
| English W / S | 0.167 / 0.087 | 0.165 / 0.076 |
| Maths W / S | 0.112 / 0.110 | 0.111 / 0.097 |

Both dimensions stay significant at the same levels. What moves is the "about equal weight"
reading: per SD the ratio is 1.23 rather than 1.09. The appendix tables (which were always
z-standardised) and the body currently sit on different scalings of the same predictors.
Two honest routes: **(a)** keep the Stata estimates and describe them as *per point of the
0–10 scale (about one SD of warmth, 1.15 SD of strictness)* — smallest edit, magnitudes
paragraph already reasons in points; **(b)** standardise in Stata and re-quote every body
number per SD. The per-SD figures are already in the CSV, so (b) is a table/macro regeneration
plus a prose pass. Until you choose, the body is unchanged.

### H2. National extension described as "standardised" (part of C3-1/C3-2)
Empirical Specification says the inspection-report strictness score enters "standardised";
`a7_national_strictness.do` enters it raw on its 1–5 scale (the table label says so). Per SD
the coefficient is about 0.14, not 0.20. Same decision as H1.

### H3. "The behaviour-policy warmth score is significantly negatively associated with progress" (Results, national extension)
On the primary spec with the real trust-template clustering (333 schools / 90 groups — the old
run clustered on a per-school key, i.e. not at all), BP warmth on overall P8 is −0.015 (raw
p≈.03) and **no longer survives Benjamini–Hochberg**; only the Open component does (−0.022,
daggered). The Chapter 2 echo ("the same result appears in the following chapter as a small
negative association") stands in weakened form. Suggested wording: "the behaviour-policy
warmth score is, if anything, negatively associated with progress (significant only for the
Open component after correction)". Unchanged pending your view.

---

## 3. What was fixed (conclusion unchanged) — old → new

### Chapter 2
| Where | Old | New | Why |
|---|---|---|---|
| Data, public text | "3,288 of the 3,312 open schools (99.3%)" | "scored for 3,324 schools; 3,272 of the 3,332 panel schools (98.2%)" | old figure traceable only to notes; recounted from the report files and the dataset |
| Gold standard, excluded components | "confidence (r = 0.34 to 0.47)" | "confidence and willingness (r = 0.34 to 0.48)" | item-level Q-scores vs the interview-quality composite recomputed from the workbook |
| Gold standard, external validation | "−0.48 conditional on the full control set" | "−0.48 net of the other espoused scores, disadvantage and school size" | that is what `check_staff_climate_external.py` conditions on |
| LLM finding 1 (+ `tab_instrument_findings`) | prose version "0.43" | "0.42 on the same grade-stripped text and the same schools" | 0.43 was the pre-grade-leak-fix Spearman; 0.07 (flags v13) and 0.415 (prose) are the like-for-like pair |
| LLM finding 3 (+ table) | separate-call "0.08 to 0.22" | "0.08 to 0.18" | the 0.22 was BP v4, a single-call instrument; web 0.075, Ofsted flags 0.150, transcript 0.183 |
| Limitations / Results | "human raters of the same text" (×2) | "the reference raters of the same text" | the raters were the Claude reference raters, as the chapter itself explains |
| Results, divergence | "rewards applied consistently, 0.29" (read as vs strictness) | "0.29 with observed warmth … 0.11 with observed warmth" | rewards vs strictness is 0.20; each statement is against its own dimension |
| Results, behaviour policies | "parent measure (−0.04, p = 0.03)" | "(−0.06, p = 0.001; −0.04, p = 0.03 on the revised instrument)" | the −0.04 is the v4 instrument; the sentence opened with v26 |
| Appendix, crawl | 334 flagged | 333 | count in `behaviour_policy_selected_documents_all.csv` |
| Appendix, ridge-spec prose | R² 0.114; −0.015 | 0.107; −0.020 | regenerated `ridge_spec_comparison.py` |
| Appendix, figure caption | visited n=101; 44.6% | n=102 matched to the panel; 45.1% | rebuilt representativeness pipeline |
| `tab_instruments_adopted` | Ofsted strictness "Visits +0.41"; teaching "+0.11" | +0.40; +0.06 | current column of record |
| `tab_irr_classroom` / `tab_irr_outside` | κw from an unknown implementation (0.01–0.09 off) | recomputed with a stated method; N, r, MAD, Exact, W1 unchanged | new producer `make_irr_tables.py` |
| `tab_representativeness` | header "n=103" over rows computed on 101; grade/P8 rows typed in | header n=102/300 "matched to the panel"; grade and prior-P8 rows computed in the generator on the full 103/303 tiers | `representativeness_check.py` now reads `gs_data_tier` |

### Chapter 3
| Where | Old | New | Why |
|---|---|---|---|
| National extension | 0.166 / 0.167 (n=2,823); "no component moves by more than 0.005" | **0.201 / 0.203 (n=3,052 / 2,746); "by more than 0.01"** | `a7_estimates.csv` predated the 14 Aug Ofsted column change AND the do-file neither excluded late-entry schools (95 inside the 3,147) nor used the filled grade — now follows the chapter's stated sample rules. Conclusion (survives grade conditioning) unchanged |
| Espoused substitution | 0.036 (p=.47); 0.113 (p=.019) | 0.055 (p=.29); 0.115 (p=.018) | old rows were the n=96 pre-primary spec; re-estimated on the same 99 schools |
| Quadrant contrast | 0.36 | 0.37 | primary spec n=99 (was n=100 without years-since) — footnote removed |
| Sub-scores | 0.107 (p=.017) / 0.118 (p=.006) | 0.108 (p=.023) / 0.120 (p=.009) | primary spec |
| Univariate | "roughly 60 per cent" | "roughly three-fifths to two-thirds" | 66% / 58% |
| Pseudo-P8 twin | "within 0.04" (×3) | "within 0.05" | 0.047 on the primary spec |
| Appendix SEMH | −0.166 (p<.001, n=2,909); −0.291 (p=.37, n=95) | −0.108 per SD (p=.013, n=2,594); −0.257 (p=.36, n=94) | outcome now a SHARE of roll on the primary spec; direction and reading unchanged |
| Appendix continuity | full n=96; S range 0.140–0.289 | n=99; 0.32–0.48 | primary spec |
| Appendix items | "28 of the 33 carry a positive association" | "all 33 positive, 28 survive BH" | what the table shows |
| Appendix entry | "10 to 14 per cent" | "11 to 14" | regenerated |
| Eleven appendix tables | Python batch, mixed specs (n=100; 103/96), numbers typed in | **all re-estimated in Stata on the primary spec** (`ch3_appendix.do` → `ch3_appendix_estimates.csv` → `make_ch3_appendix_tables.py`); captions state spec, scaling and n | Option A |

---

## 4. What was verified and found right
All of: n=99 / 0.143 / 0.131 / p-values / R² 0.62; the ladder; 0.218/0.228; components; stages 2–3;
interaction 0.045 (p=.25); every robustness row; Att8 1.17/1.73 and 0.31/0.22; national SD 0.51, IQR 0.66;
visited mean/SD; the 0.53 and 0.62 benchmarks; late-entry 98/2; the six/five/one grade accounting; all
Chapter 2 gold-standard statistics (means, SDs, gaps, shares, correlations, the two-school example);
the source-criterion table; the parent-survey figures; Ofsted-vs-grade −0.40/−0.49; single-call 0.54;
BP −0.08/−0.02/0.01/−0.08; faith AUC 0.96; turnover −0.52; ridge A coefficients 0.24/0.23; ridge LOO
tables; the interview IRR table to the last decimal; the visit IRR ranges; the ICC prose against the
stability CSV; corpus counts for BP (3,363) and websites (3,370 / 3,284); representativeness headline
shares; interview/visit timing; 304 interviews; ten systems and ten statements.

## 5. Not verified by rerun (stated, not hidden)
- Instrument κw values in `tab_instruments_adopted` (0.64, 0.45, 0.75, 0.76, 0.69, 0.66, 0.63), the
  model-swap 0.63 → 0.12, the intra-rater 0.77 / 0.88, and the reference raters' −0.25 against the
  grade: traced to `RUN_RESULTS_2.md` / the memory records of the 13 Aug out-of-sample run and the
  rater exercises, not recomputed from the pack files.
- `tab_sen_category_stability` and `tab_p8_component_stability`: no producer invocation on record;
  the prose matches the tables; not re-run.
- The p8-proxy back-test r = +0.81: from `validation_summary.csv` of `build_p8_proxy_2425.py`
  (present on disk), not re-run this pass.
- Literature figures quoted from cited papers: checked against the chapter's own earlier text only.

## 6. Infrastructure added so this holds
- `thesis/ch3_appendix.do`, `thesis/build_ch3_appendix_input.py`, `thesis/make_ch3_appendix_tables.py`
  — the appendix on the primary spec, regenerable end to end.
- `thesis/make_irr_tables.py` — the visit IRR tables from the raw workbook.
- `representativeness_check.py` reads `gs_data_tier`; `generate_representativeness_outputs.py` computes
  the grade and prior-P8 rows and the prose snippet from the data.
- `a7_national_strictness.do` applies the late-entry exclusion and the filled grade.
- `check_pipeline.py` stage 5: "every generated table reproduces from its producer" — runs every
  `make_*.py --check` and asserts the three Stata CSVs are no older than `analysis_dataset.csv`.
- Postfile string widths widened twice more (`str24 panel`, `str20 outcome`) after silent truncation
  bit again — the third time this trap has fired; every new postfile should start wide.
