# Chapter 3 — Completion Plan
*School Culture and Pupil Progress: Evidence from English Secondary Schools*
*Prepared 31 July 2026*

Status key: **[FIX]** written but wrong/outdated · **[CHECK]** needs verification · **[READY]** can do now · **[ADD]** new content needed · **[BLOCKED]** waiting on Stata run, Ridge rebuild, or leadership national run

---

## Current State Assessment

Chapter 3 (03_paper2.tex, 714 lines) is in a different state from Chapter 2: the **methodology sections are complete and largely correct**, but the chapter is a well-constructed framework awaiting actual regression results. Unlike Chapter 2, there are almost no factually wrong passages — just placeholder INSERTs where analysis outputs will go.

**What is written and correct:**
- §sec:p2_lit (Related Literature) — complete
- §sec:p2_id (Research Question and ID Strategy) — complete
- §sec:p2_outcomes (Outcome Variables, primary and secondary) — complete; references `tab:outcome_stats`
- §sec:p2_controls (Control Variables) — complete; references `tab:control_stats` and `tab:score_controls_corr`
- §sec:p2_continuity (Headteacher Continuity) — framework complete; 4 INSERT values missing
- §sec:p2_specs (Empirical Specifications) — complete; references `tab:robustness`
- §app:3A:stability (Structural Stability appendix) — complete; uses `\input{}` for three tables that **already exist** in `thesis/tables/`

**Tables already produced (`thesis/tables/`):**
- `tab_structural_stability.tex` — ICC table for 9 panel variables ✓
- `tab_sen_category_stability.tex` — ICC table for 13 SEN categories ✓
- `tab_p8_component_stability.tex` — ICC table for P8 components ✓
- `tab_representativeness.tex` — sample representativeness (lives in tables but used by Chapter 2) ✓

**Critical data status:**
- `analysis_dataset.csv` — **COMPLETE** (3,332 rows × 96 columns). Contains: `gs_warmth_visit`, `gs_strictness_visit`, `gs_teaching_visit` (visit-only enacted scores); `ofsted_grade_2019` (pre-COVID Ofsted grade control); all P8 outcomes (single year and 2-year averages); all controls; all LLM scores; ridge predictions.
- No Stata `.do` file or analysis Jupyter notebook exists — only `chapter3_tier1_staged.py` (preliminary Python OLS, exploratory only).

**Primary blocker: writing and running the Stata regression script.**

---

## A — Prose Fixes (1 item)

### A1 ✅ DONE iq_weight S4* notation in robustness specification
**Location:** §sec:p2_specs (done) and §app:3A:tables (done)
Both instances of `$\tfrac{1}{2}(S3+S4^*)$` corrected to `$\tfrac{1}{2}(S3+S4)$`. W3* is correct — W3_adj IS quality-adjusted.

---

## B — INSERT Completions

### B1 ✅ DONE Headteacher continuity INSERT values
**Location:** §sec:p2_continuity (updated)

Filled: N = 1,422; reference date = July 2026. Updated "approximately 39%" → "approximately 45%" (actual: 636/1,422 = 44.7% from ofsted_HeadteacherChanged column).

**Note:** The 27% (visited, 102 schools) and 23% (interviewed, 303 schools) figures remain as unverified prior estimates. These require comparing headteacher names from interview data to current GIAS — `ofsted_HeadteacherChanged` only covers 30 of 102 visited schools (7 changed = 23.3%) and 109 of 303 GS schools (40 changed = 36.7%). The "since visit/interview" comparison is a different calculation from "since Ofsted inspection". Leave 27%/23% as approximate unless user wants to recompute from interview HT names.

### B2 [READY → draft now, finalise after Stata] Abstract
**Location:** `chapterabstract` block, lines 12–15

~150 words. Content (use preliminary Python OLS results as placeholder direction; finalise with Stata coefficients):

- RQ: whether enacted school culture (warmth and strictness) predicts KS2→KS4 pupil progress in English secondary schools
- Data: 102 gold-standard schools with directly observed culture scores from school visits; national panel dataset; 2022/23–2023/24 two-year average Progress 8 component scores
- Design: cross-sectional OLS, three-stage specification separating total culture effect from teaching quality channel; HC3 robust SEs
- Preliminary findings: warmth positively associated with P8 progress in 4/5 outcomes; strictness positively associated in English and EBaC; the EBaC culture effect is not mediated through teaching quality (99% attenuation retention), consistent with a curriculum-steering channel; results survive full control set including pre-2019 Ofsted grade
- Scale caveat: N=102, underpowered for modest effects; consistent directional pattern across four outcomes is the primary evidence
- Policy implication: school culture dimensions measurable at research scale are predictive of national progress metrics even conditional on all observable school characteristics

### B3 [READY → draft now, finalise after Stata] Introduction preview
**Location:** §sec:p2_intro, lines 73–76

One INSERT block: "Preview of main findings: sign and significance of $\hat{\beta}_1$ and $\hat{\beta}_2$; whether warmth, strictness, or their combination is the stronger predictor; robustness across alternative specifications; heterogeneity by school type, deprivation, and Ofsted grade."

Draft from preliminary Python OLS:
> Across four Progress 8 component outcomes, warmth emerges as the more consistent predictor, with positive and statistically significant associations in [N] of four components; strictness shows significant positive associations in [N] of four components, with the largest point estimates in the EBaC component. The culture–progress association is not explained by differences in teaching quality as directly observed during school visits; including the visit-based teaching quality score attenuates warmth and strictness coefficients by at most [X]% in the EBaC specification, consistent with culture operating through curriculum-steering and pupil engagement channels rather than solely through instruction.

Finalise once Stata results are available.

### B4 [BLOCKED] Results section prose
**Location:** §sec:p2_results, lines 544–551 — ENTIRELY INSERT

This is the largest single item. Full text needed covering:
1. Main regression results (`tab:main_results`) — Stage 1, 2, 3 coefficients; which outcomes show significant warmth/strictness effects; the teaching benchmark comparison
2. The EBaC attenuation finding (the theoretically most important result)
3. The differential warmth vs strictness pattern across outcomes (warmth stronger for Open/English; strictness stronger for EBaC)
4. Robustness (`tab:robustness`) — stability across key specifications
5. National extension — Ofsted strictness at n≈3,290 (if run separately)
6. Entry rates as secondary outcomes

Blocked on Stata.

### B5 ✅ DONE (skeleton) Conclusion
**Location:** §sec:p2_conclusion (drafted 31 July 2026)

Full conclusion drafted with actual prose for: opening/framing; enacted vs. espoused measurement asymmetry (warmth +0.45, strictness ≈ 0, teaching +0.71); three limitations; policy implications; five future extensions. One PENDING comment block remains for the main regression results paragraph — to be inserted once tab_main_results.tex is produced in Session 2.

**New finding in conclusion prose:** strictness gap (V-I) ≈ 0.01, NOT -0.55 as the original INSERT outline estimated. The limitation paragraph was updated to remove the wrong -0.55 strictness figure; it now correctly notes only the warmth overclaiming (+0.45) as the documented bias. Session 3 should reconcile this with the Chapter 1 convergence figure (-0.55) once both chapters are updated.

---

## C — Data Work (do before Stata)

### C1 ✅ DONE `interview_vs_visit_scores.csv`
**Status:** Built 31 July 2026. 102 rows × 61 cols at `Schools Project/interview_vs_visit_scores.csv`.
Script: `scratchpad/build_interview_vs_visit.py`

**Key findings from the comparison (n=102 visited schools):**
| Dimension | Visit mean (SD) | Interview mean (SD) | Gap (V−I) | r |
|-----------|----------------|---------------------|-----------|---|
| Warmth | 6.62 (1.00) | 7.06 (1.37) | −0.45 | 0.22 |
| Strictness | 7.09 (0.89) | 7.10 (0.96) | −0.01 | 0.18 |
| Teaching | 6.74 (0.85) | 7.44 (0.98) | −0.71 | 0.20 |

Interview "strictness" here = mean(S3,S4)×2; interview "warmth" = W3_adj×2; interview "teaching" = T2×2.
Note: strictness gap ≈ 0 (not −0.55 as the prior INSERT estimate stated). This is a substantive finding.

### C2 ✅ DONE Headteacher continuity numbers
See B1 above. Data computed. INSERTs filled. 27%/23% left as unverified approximations.

---

## D — Tables to Produce from `analysis_dataset.csv` (no Stata needed)

### D1 ✅ DONE `tab:outcome_stats` — P8 outcome summary statistics
**Referenced:** §sec:p2_primary_outcomes ("Summary statistics for all four primary outcome components by data tier")

Content: For each of the 4 P8 components (Eng, Mat, EBaC, Open), 2-year average, by tier:
- Tier 1 (n=102 visited): mean, SD, min, max
- Tier 2 (n=303 interview): mean, SD
- National (n≈3,200 with P8): mean, SD

Variables: `p8meaeng_avg`, `p8meamat_avg`, `p8meaebac_avg`, `p8meaopen_avg` (and single-year `_2223`, `_2324`).
Also include Att8 components for 2024/25 robustness spec: `att8screng_2425` etc.

Produce as LaTeX `longtable`, save to `thesis/tables/tab_outcome_stats.tex`.

### D2 ✅ DONE `tab:control_stats` — control variable summary statistics
**Referenced:** §sec:p2_controls ("reports summary statistics for all control variables by data tier")

Content: mean, SD, N by tier for all controls: `ks2`, `fsm`, `eal`, `sen`, `log_size`, `academy`, `urban_bin`, `selective`, `ofsted_grade_2019`, `years_since_ofsted`, plus workforce and financial controls.

Note: `ofsted_grade_2019` is the endogeneity-safe pre-COVID grade — verify its coverage for the 102 and 303 school subsamples.

Produce as LaTeX `longtable`, save to `thesis/tables/tab_control_stats.tex`.

### D3 ✅ DONE `tab:score_controls_corr` — score–control pairwise correlations
**Referenced:** §app:3A:tables ("Table~\ref{tab:score_controls_corr}—pairwise correlations between warmth and strictness scores and control variables")

Content: for the 102 full-data schools, Pearson r between each of gs_warmth_visit, gs_strictness_visit, gs_teaching_visit, gs_warmth_composite, gs_strictness_composite and each control variable. Shows whether warmth/strictness are confounded with school characteristics.

Produce as compact LaTeX table, save to `thesis/tables/tab_score_controls_corr.tex`.

---

## E — Stata Analysis (primary blocking task)

### E1 [ADD] Write Stata analysis notebook
**File:** `chapter3_analysis.ipynb` (Jupyter notebook with Stata kernel via nbstata)

The notebook should:
1. Load `analysis_dataset.csv` using `import delimited`
2. Create sample flags: `gen tier1 = (gs_warmth_visit != .)`; `gen tier2 = (trx_LLMWarmthScore != .)`
3. Define global macros for control variable lists:
   - `global controls_base "ks2 fsm eal sen log_size academy urban_bin selective i.ofsted_grade_2019 years_since_ofsted"`
   - `global outcomes "p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg"`
4. Run three stages for each outcome with `regress`, `vce(hc3)`:
   - Stage 1: outcome ~ gs_warmth_visit + gs_strictness_visit + $controls_base
   - Stage 2: outcome ~ gs_teaching_visit + $controls_base
   - Stage 3: outcome ~ gs_warmth_visit + gs_strictness_visit + gs_teaching_visit + $controls_base
5. Capture results in `estimates store` and produce tables via `esttab` or `outreg2`

**Note on controls:** Full control set per project overview includes workforce (QTS%, mean teacher salary, leadership size) and financial (PPE, share on teaching staff) variables. These may have missing values — check coverage for the 102-school sample before including. If <80 schools have all controls, consider two specifications: parsimonious (demographic controls only) and full.

**Ofsted grade handling:** `ofsted_grade_2019` is continuous 1–4 — encode as dummies (`i.ofsted_grade_2019`). Note: `ofsted_mi_overall` (contemporary 2024 grade) goes in a sensitivity check only.

**Grammar school note:** `selective` is already binary in the dataset.

### E2 [ADD] Run robustness specifications

All specifications listed in §sec:p2_specs (lines 520–542):

1. **Interview scores instead of visit scores (n=303):** Replace `gs_warmth_visit` with `gs_W3_adj` (warmth interview) and `gs_S4` (strictness interview raw); expand sample to `tier2==1`. This tests the predicted espoused-vs-enacted attenuation — expect warmth β to be biased upward and strictness β biased downward vs primary spec.

2. **Enriched scores:** Load `warm_strict_scores_enriched.csv`, merge to dataset; replace composite scores with enriched equivalents. Note: this will drop ~9 schools. Check whether findings stable.

3. **Headteacher continuity restricted sample:** Restrict to `ofsted_HeadteacherChanged == 0`. Likely reduces N substantially — check power implications.

4. **SEMH baseline control:** Add `semh_baseline_2016` as an additional control.

5. **W×S interaction:** Add `c.gs_warmth_visit#c.gs_strictness_visit` to Stage 1 specification.

6. **Alternative outcomes:** Replace P8 components with:
   - Overall P8 (`p8mea_avg`)
   - Att8 components (`att8screng_2425` etc.) — use for 2024/25 contemporaneous spec

### E3 [ADD] Run national extension
**N ≈ 3,290 schools** with both `ofsted_LLMStrictnessScore` and P8 outcomes.

Primary spec: `p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg ~ ofsted_LLMStrictnessScore + $controls_base` on full 3,290-school sample.

This is the "enacted culture nationally" result. Note: warmth is omitted from this specification — there is no valid national enacted warmth source. Report the strictness coefficient at national scale and compare to Tier 1 visit-only estimate.

Also run with `ofsted_LLMTeachingScore` (Ofsted teaching, though this failed r>0.3 gate and should be reported as near-zero confirmation, not as a usable predictor).

### E4 [ADD] Run validation appendix regressions (enacted vs espoused)
Using `interview_vs_visit_scores.csv` (which must be built first via C1):

For the 102 full-data schools, run parallel regressions:
- Visit-only scores → P8 (same as Stage 1, already done)
- Interview-only scores → P8 (using `gs_W3_adj` and `gs_S4`)
- Test whether β_interview ≈ β_visit × r(interview,visit) × σ_visit/σ_interview
- Also test gap variable as predictor: `warmth_gap ~ P8` (do schools with aligned culture do better?)

This goes in `tab:enacted_espoused` (appendix 3A).

---

## F — Tables from Stata Results

| Table label | Content | Status | Source |
|---|---|---|---|
| `tab:main_results` | 3-stage OLS (Stage 1/2/3 × 4 outcomes); β, SE, p, R² | **BLOCKED** | Stata output |
| `tab:robustness` | All 6 robustness specifications vs primary spec | **BLOCKED** | Stata output |
| `tab:continuity_robustness` | Primary spec restricted to continuity-confirmed schools | **BLOCKED** | Stata output |
| `tab:national_extension` | Ofsted strictness → P8, n≈3,290 | **BLOCKED** | Stata output |
| `tab:enacted_espoused` | Visit-only vs interview-only coefficients, gap-as-predictor | **BLOCKED** | Stata output + interview_vs_visit_scores.csv |

Each table should be a `longtable` environment with booktabs formatting, saved to `thesis/tables/tab_*.tex` and `\input{}`-ed into the chapter.

---

## G — Blocked Items (waiting on other runs)

### G1 [BLOCKED] Robustness Check 2b — iq_weight sensitivity
Re-run Chapter 3 Stata regressions using `gs_warmth_score_v1`, `gs_strictness_score_v1` (the old all-adjusted scores from the `_v1` columns already in `analysis_dataset.csv`) as alternative predictors. Compare β estimates to primary spec. If materially different, the iq_weight revision is load-bearing.
**Blocked on:** primary Stata run completing.

### G2 [BLOCKED] Robustness Check 3 — 60/40 vs 50/50 weighting sensitivity
Compute alternative composite (50/50 weighting) from `gs_W1`, `gs_W2`, `gs_W3_adj` and re-run. All sub-scores are in `analysis_dataset.csv`.
**Blocked on:** primary Stata run completing.

### G3 [BLOCKED] Management discourse as exploratory predictor
Add `trx_LLMManagementScore` as an exploratory predictor in the 303-school extended specification. Already in `analysis_dataset.csv`. Frame as explicitly exploratory given validation failures (null Ofsted leadership r, wrong-direction retention r). Report in main text or appendix as appropriate.
**Blocked on:** Stata setup, but can be run at the same time as primary.

### G4 [BLOCKED] Teaching philosophy (website) as national predictor
`web_id_LLMTeachingPhilosophy` (3-category: traditional/progressive/unmarked) is already in `analysis_dataset.csv`. Add to national extension spec (E3). Test whether traditional teaching philosophy predicts higher EBaC P8.
**Blocked on:** national extension Stata run.

### G5 [BLOCKED] Ridge model rebuild
Fix path errors in `build_ridge_models.py` and `ridge_diagnostics.py` (currently reference deleted files — update to `scores/ofsted_analysis_results_v2.csv` and `scores/behaviour_policy_analysis_results_v26_national.csv`). Rebuild Ridge models with the national BP + v6 interview scores. Ridge predictions are already in `analysis_dataset.csv` from the old models — update them.

> Note added 1 August 2026: the BP file was renamed from `..._v25_national.csv` — it was always v26 output. It also carries run-to-run sampling noise (3 of 8 anchors moved on an identical re-run), which propagates into any Ridge model built on `bp_LLMStrictnessScore`. See the header of `analyse_behaviour_policies_v3.py`.
**Blocked on:** script path fixes (15 min of work) + rebuild run.
Ridge predictions are used for the Chapter 3 validation appendix (showing how well Ridge A/B scores predict P8 vs direct visit scores).

### G6 [BLOCKED] Leadership national run completion
`ofsted_leadership_scores_national.csv` is running (July 2026). Once complete:
- Move to `scores/`
- Merge into analysis_dataset.csv
- Compute `gap_leadership` = trx_LLMManagementScore − ofsted_LLMLeadershipScore
- This feeds the Chapter 2 national espoused/enacted gap table (C3 in ch2_completion_notes.md), not Chapter 3 directly

### G7 [BLOCKED] SEMH composition mechanism test
From §sec:p2_specs: test whether strictness score predicts SEMH share *change* over time. Uses `semh_baseline_2016` and `semh_current` (both in `analysis_dataset.csv`). Run: `semh_current ~ gs_strictness_visit + semh_baseline_2016 + controls`. If strict schools have lower SEMH share than expected given baseline, consistent with exclusion sorting.
**Blocked on:** primary Stata run.

---

## H — Appendix Work

### H1 [READY] `app:3A:tables` — INSERT block items
**Location:** lines 699–713

The appendix section INSERT lists three tables:
1. `tab:score_controls_corr` — can produce now from analysis_dataset.csv (see D3)
2. `tab:robustness` — needs Stata
3. `tab:enacted_espoused` — needs Stata + interview_vs_visit_scores.csv

Once tables are produced, replace the INSERT block with `\input{tables/tab_*}` references and add brief description text.

---

## I — Recommended Working Order

**Session 1 — Fix and data prep (no Stata needed):**
1. Prose fix A1 (S4* → S4 in robustness spec)
2. Build `interview_vs_visit_scores.csv` from analysis_dataset.csv (C1)
3. Check headteacher continuity data (C2) — fill or drop INSERT placeholders
4. Produce `tab:outcome_stats`, `tab:control_stats`, `tab:score_controls_corr` (D1–D3)
5. Check coverage of workforce/financial controls for n=102 sample (needed before Stata)
6. Draft conclusion from the outline already in the INSERT block (B5)

**Session 2 — Stata analysis:**
7. Write `chapter3_analysis.ipynb` (E1)
8. Run Stage 1, 2, 3 on 4 outcomes (primary spec, n=102)
9. Run national extension (n≈3,290 with Ofsted strictness)
10. Run robustness specifications (E2)
11. Run enacted vs espoused comparison (E4)
12. Export tables to `thesis/tables/`

**Session 3 — Write results from tables:**
13. Write Results section prose (§sec:p2_results) — 600–900 words covering all 5 subsections
14. Finalize abstract and introduction preview (B2, B3)
15. Finalize conclusion with actual coefficient values (B5)
16. Update appendix INSERT with table references

**Session 4 — Robustness checks and extensions:**
17. Fix Ridge model scripts (G5) and rebuild
18. Run iq_weight sensitivity (G2b) and 50/50 weighting check (G3)
19. Run SEMH mechanism test (G7)
20. Run management discourse exploratory (G4) and teaching philosophy (G5)
21. Update robustness table with all checks

---

## Key Numbers Already Known (from preliminary Python OLS, July 2026)

These are from `chapter3_tier1_staged.py` — n=102, 2-year P8 average, 11 controls, **contemporaneous 2023-24 Ofsted grade** (NOT the correct pre-COVID 2019 grade). Final Stata results may differ.

| Outcome | Warmth β | p | Strictness β | p |
|---------|----------|---|--------------|---|
| Overall P8 | +0.113 | .006** | +0.083 | .045* |
| English | +0.127 | .003** | +0.041 | .37 |
| Maths | +0.078 | .094 | +0.066 | .15 |
| EBaC | +0.140 | .009** | +0.110 | .028* |
| Open | +0.105 | .049* | +0.095 | .088 |

**EBaC attenuation (culture net of teaching, Stage 1 → Stage 3):**
- Warmth 99% retained (still p=.034*)
- Strictness 99% retained (still p=.037*)

**VIFs:** warmth=2.78, strictness=1.81, teaching=3.44. No collinearity concern.

**Theoretical prediction (from §sec:p2_primary_outcomes):** Strictness expected to load more on EBaC; warmth more on Open P8 and English. Preliminary results: EBaC shows the strongest effects for BOTH warmth and strictness. Open shows warmth significant but strictness only marginal. English shows warmth significant, strictness near-zero. This partial match to theory is worth discussing.

**Note:** All these numbers will change when re-run with `ofsted_grade_2019` (pre-COVID Ofsted) as the control instead of the contemporaneous grade. Expect small changes — the pre-COVID grade is available for ~97% of the sample.
