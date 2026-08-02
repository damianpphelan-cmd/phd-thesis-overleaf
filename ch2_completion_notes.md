# Chapter 2 — Completion Plan
*Measuring School Culture: Warmth and Strictness in English Secondary Schools*
*Prepared 31 July 2026*

Status key: **[FIX]** written but wrong/outdated · **[READY]** can do now · **[ADD]** new content needed · **[BLOCKED]** waiting on Ridge rebuild, leadership run, or analysis dataset

---

## A — Prose Fixes (3 items — do first)

### A1 [FIX] iq_weight methodology — Composite Scores subsection
**Location:** `§sec:p1_composite`, lines 527–551

The text currently defines *S4\* = S4 × ω* and *T2\* = T2 × ω* and uses these in the composite formulas. The July 2026 methodology revision found the adjustment hurts strictness (r: 0.274 adj vs 0.374 raw) and teaching (0.173 vs 0.196). Current methodology applies iq_weight **only to W3**. S4 and T2 use raw scores.

Required changes:
1. Remove S4\* and T2\* from the definition; keep only W3\* = W3 × ω
2. Update Strictness formula: `0.6 × ½(S1+S2) + 0.4 × ½(S3+S4)` [raw S4, not S4\*]
3. Update Teaching formula: `0.6 × T1 + 0.4 × T2` [raw T2, not T2\*]
4. Update rationale footnote: "The iq_weight adjustment improves warmth calibration (r: 0.156 raw → 0.224 adjusted) but reduces predictive validity for strictness and teaching, which carry their signal in interview content rather than expressive engagement."

### A2 [FIX] Ofsted scoring description — old subcomponent / split-rubric approach
**Location:** `§sec:p1_text_method`, Ofsted subsection, lines 855–893

The text describes the old v3/v5 split-rubric approach (separate LLM passes per dimension, each preceded by four subcomponent scores). The current national run (`ofsted-strictness-warmth-teaching-v3`, `gpt-5-nano`) uses a **unified prompt** scoring W, S, and T in a single call with holistic rubric. The full extracted narrative body (4,000–6,000 chars) replaced keyword-selected passage subsets; subcomponent scoring was removed.

Required changes:
1. Replace "separate scoring passes" with "a single unified LLM call"
2. Remove the four-subcomponent paragraph
3. Add a sentence: teaching dimension scored in same call; r=0.133 (ns) vs T1, failed r>0.3 gate, not used as national predictor
4. **Check `ofsted_analysis_results_v2.csv` columns** — if no subcomponent columns exist, update the Ridge feature-set description (currently says "four Ofsted subcomponent scores" entering the model) to reflect what is actually available

### A3 [FIX] Behaviour policy scoring description — old v2 subcomponent approach
**Location:** `§sec:p1_text_method`, BP subsection, lines 895–927

The text describes the old v2 rubric with five strictness and five warmth subcomponents. The current national run uses the **v25 anchored rubric** (`behaviour-policy-strictness-warmth-v25`, `gpt-5-nano`): no subcomponents; S=3 as explicit default; built via anchor calibration on 8 schools.

Required changes:
1. Replace subcomponent list with v25 rubric description. Key discriminating features:
   - S=4: named tracking system where position determines consequence automatically
   - S=5: S=4 PLUS mandatory issuance PLUS deportment norms (SLANT/posture/eye contact)
   - W=4: named reward system PLUS explicit staff guidance on individual relationships (both necessary)
2. Note the policy-as-aspiration finding as motivation for anchoring approach
3. Update "five BP subcomponent scores" entering the Ridge — if v25 has no subcomponents, the Ridge feature description needs updating
4. Update convergent/discriminant table footnote to reference "v25 anchored rubric"

---

## B — INSERT Completions (12 items)

### B1 [READY] Fill in all N values throughout
**Location:** `§sec:p1_intro` (×4), `§sec:p1_data` (×4), `§sec:p1_text` (×2)

- Tier 1 = **102** full-data schools
- Tier 2 = **303** interview schools
- Tier 3 national ≈ **3,319** schools (check exact row count in `ofsted_analysis_results_v2.csv`)
- Behaviour policies: **3,365** schools with selected documents; **3,364** with v25 scores

### B2 [READY] Abstract (~150 words)
**Location:** `chapterabstract` block, lines 12–15

Cover: research question (can school culture be measured at scale?), data (304 interviews, 103 visits, national text sources), framework (three-tier cascade, visit gold standard, Ridge calibration), key findings (enacted strictness measurable nationally r=0.48; enacted warmth not; espoused/enacted gap confirmed across four sources; preliminary P8 associations positive).

### B3 [READY] Introduction preview paragraph
**Location:** `§sec:p1_intro`, INSERT block at lines 72–74

Two–three sentences: inter-rater reliability (within-1 agreement >X% across items); the espoused/enacted gap finding (r=0.22 warmth, r=0.16 strictness; +0.45/−0.55 pts systematic bias); Ofsted strictness validity (r=0.483, p<0.001); and the policy-aspiration effect (three independent null/negative warmth signals). Keep short — detail is in later sections.

### B4 [READY] Literature review: fill [CITE] placeholders
**Location:** `§sec:p1_lit`, lines 96, 133, 229

- Line 96: "long history in educational research [CITE]" → Hoy & Miskel (2001); Cohen et al. (2009); Thapa et al. (2013) meta-analysis
- Line 133: "authoritative school concept [CITE]" → Gregory et al. (2010) *Authoritative School Discipline*; related evidence: Gregory & Cornell; Gottfredson et al.
- Line 229: "authoritative model [CITE]" and "Baumrind's typology [CITE]" → Baumrind (1971); Gregory et al. (2010)

### B5 [READY] Document collection statistics
**Location:** `§sec:p1_text_docs`, lines 808–826

- Ofsted: obtained from the Ofsted website and Ofsted Report Card (post-2024 inspections); 3,288 PDFs for 3,312 open schools (99.3%); 24 schools uninspected (all opened 2023+)
- Inspection date distribution: pull date range from `ofsted_analysis_results_v2.csv`
- Behaviour policies: 3,365 schools (of ~3,400 in scope); 1 permanently unresolvable (Lubavitch House School, URN 145609, no public policy); 117 schools written off (closed/studio/UTCs)

### B6 [READY] Inter-rater reliability — interview data
**Location:** `§sec:p1_irr_int`, lines 650–673

Data: `Novel Data/Headteacher Interview - Responses_with_urns.xlsx` — questioner and observer columns for Q2–Q12. Compute per question: Pearson r, MAD, exact agreement %, within-1 %, weighted Cohen's κ. Build `tab_irr_interview` (appendix). Body text: median r; identify strongest (likely Q5 sanctions/rewards, Q8 marking) and weakest (likely Q2 or Q4). Expected: within-1 > 90% for most; κ "substantial" (0.6–0.8) for structured questions.

### B7 [READY] Inter-rater reliability — visit observation data
**Location:** `§sec:p1_irr_obs`, lines 675–696

Data: School Visit Proforma files. Compute pairwise r, exact agreement, within-1, MAD for all lesson items and outside-lesson items where two or three researchers present. Build `tab_irr_classroom` and `tab_irr_outside`. Expected strongest: Disruption, Discussion. Expected weakest: Names, Interactions (require integrating many simultaneous events).

### B8 [READY] Score distribution reference text
**Location:** `§sec:p1_composite` end, lines 589–592

The reference calls to `tab:score_dist` and `fig:warmth_strict_joint` just need brief accompanying text stating range and SD of each sub-score. Data all in `warm_strict_scores.csv` (102 rows).

### B9 [READY] Policy-aspiration section: insert final sample sizes and values
**Location:** `§sec:p1_policy_aspiration`, lines 1152–1163

- Website pilot n: 96 schools (or 75 — confirm exact n from holistic validation run)
- Website LLM warmth r = −0.167; check p-value (memory says p=0.09 or p=0.15 — verify)
- BP warmth Ridge LOO-CV r ≈ +0.184 (update once Ridge rebuilt with v25)
- Add website strictness result (r=+0.002, p=0.99) if not yet referenced
- Remove the INSERT note once values are confirmed

### B10 [BLOCKED] Interview-tier Ridge model LOO-CV (tab:interview_model_loo)
**Location:** `§sec:p1_enriched_model`, lines 779–793

Blocked on Ridge rebuild (`build_ridge_models.py` path fixes + rerun with v25 BP + v6 interview scores). Preliminary: Model A LOO-CV r=0.891 (warmth), r=0.958 (strictness) — will change slightly with corrected inputs. Also fill in fitted coefficient interpretation.

### B11 [BLOCKED] National-tier Ridge model LOO-CV (tab:national_model_loo)
**Location:** `§sec:p1_text_valid`, lines 962–990

Blocked on Ridge rebuild. Current values (old data): Model B warmth r=0.184 (R²=0.027), strictness r=0.321 (R²=0.100). Expected to change with v25 BP (BP contribution near-zero → Model B strictness driven almost entirely by Ofsted LLM strictness score). Fill INSERT blocks and update appendix coefficient table.

### B12 [BLOCKED] Results section — ENTIRE SECTION is INSERT
**Location:** `§sec:p1_results`, lines 1192–1203

Five sub-items to cover: (i) distribution of W/S scores across full sample; (ii) W–S correlation; (iii) GS vs interview-only correlation; (iv) GS vs public-data correlation; (v) school characteristics associated with W/S; (vi) score compression note. Gold-standard summary statistics (i, ii) can be written now from `warm_strict_scores.csv`; national distribution (iii, iv) needs Ridge rebuild.

*Note: the Conclusion (lines 1209–1249) is also fully INSERT but has a detailed outline already in the text — draft immediately from existing material, refine once final numbers arrive.*

---

## C — New Sections to Add (4 items)

### C1 [ADD] Management/Leadership dimension — new subsection
**Location:** Add after `§sec:p1_policy_aspiration` (after line 1163), or as `§sec:p1_leadership`

Content to cover:
- **M score from interview transcripts:** `trx_LLMManagementScore` scored by v6 scorer (Q3/Q10 — HT deliberateness in communicating culture to staff and holding staff to account). Mean=3.84, sd≈0.44 (n≈290 schools)
- **Ofsted leadership LLM score:** scored from full 20k-char Ofsted report text via gpt-4o-mini. Pilot: r=0.739 vs actual Ofsted leadership grade (n=30, above r>0.5 gate). National run in progress (~3,330 schools). Contrast with W/S: different text passed (full report vs 4–6k narrative body)
- **Leadership espoused/enacted gap:** r=−0.166 (ns) between trx_LLMManagementScore and Ofsted leadership grade — null correlation. Two explanations: (a) London confound; (b) aspiration echo (HTs most emphasising management systems are in schools working hardest on management, same logic as BP warmth). This completes the multi-level espoused/enacted argument

*Partially blocked on national leadership run completing.*

### C2 [ADD/READY] School websites — new subsection in §sec:p1_text
**Location:** Add as `§sec:p1_text_web`, between BP method and Policy-Aspiration sections

Content to cover:
- National crawl: 3,053 .txt files; 2,962 with "ok" status; 9 borderline thin-file schools flagged (URNs in project_overview.md)
- Scoring: v4 rubric (`website-strictness-warmth-v4`, gpt-4o-mini); W and S scored independently on 1–5; signed off on 10-school anchor set (S=10/10, W=3/10)
- National results: strictness mean=1.97 (heavily left-skewed; most schools have limited explicit conduct language); warmth mean=3.22; W=2 boundary known to be weak
- Validation: LLM warmth r=−0.167 (ns); LLM strictness r=+0.002 (ns). Anchor-in-context approach reproduced holistic reading rank ordering (r=0.568) but did not recover enacted warmth
- Use in thesis: website S and W are espoused-culture characterisation only; not used in Chapter 3
- Teaching philosophy: 3-category classification (traditional/progressive/unmarked) from `website_identity_scores.csv` — IS used in Chapter 3 as novel national predictor

### C3 [BLOCKED] National-scale espoused/enacted gap table
**Location:** Add to `§sec:p1_results` once analysis dataset built and leadership run completes

Three gap variables to compute:
- `gap_strictness_bp` = bp_LLMStrictnessScore − ofsted_LLMStrictnessScore
- `gap_strictness_web` = web_LLMStrictnessScore − ofsted_LLMStrictnessScore
- `gap_leadership` = trx_LLMManagementScore − ofsted_LLMLeadershipScore

Report mean, SD, and direction for each. Confirm direction mirrors research-scale finding (espoused strictness < enacted strictness; espoused management claims don't align with Ofsted-observed leadership). Purely descriptive — no regression needed.

### C4 [ADD/READY] Parent View convergent validation — paragraph in §sec:p1_results

Parent View Q1+Q2 composite correlates r≈+0.157 (p=0.008) with gold-standard warmth for 289 overlapping schools; rises to r=+0.242 (p=0.020) for the 93 schools in the most temporally aligned Sep 2025 release. No question isolates strictness.

Frame as a fourth measurement cell: *perceived* culture from the recipients (parents), distinct from enacted (observer-recorded), espoused (school self-presentation), and formal/aspirational (governance documents). Weak but positive correlation expected given source-type mismatch. Note: release year must be controlled when using PV data; older releases show near-zero correlation.

---

## D — Figures to Produce (6 figures — all referenced, none exist as PDFs)

| Figure | Status | Content | Data source |
|---|---|---|---|
| `fig_A_score_distributions.pdf` | **READY** | 2×2 panel histograms: interview composite W+S (303 schools) vs Ofsted LLM W+S (3,319 schools). Shows compressed Ofsted warmth SD=0.44 vs interview SD=1.34 | `warm_strict_scores.csv` + `ofsted_analysis_results_v2.csv` |
| `fig_B_validation_scatter.pdf` | **READY** | 2-panel scatter: Ofsted LLM W (left) and S (right) vs interview/visit composite. Filled = 102 GS schools, grey = 201 interview-only. r=+0.161 warmth (ns) vs r=+0.483 strictness (p<0.001) | Join `warm_strict_scores.csv` + `ofsted_analysis_results_v2.csv` on URN |
| `fig_warmth_strict_joint` | **READY** | Joint distribution scatter of gold-standard warmth vs strictness (102 schools). Include quadrant labels | `warm_strict_scores.csv`, 102-school filter |
| `fig_D_regional_representativeness.pdf` | **CHECK FIRST** | Bar chart: regional distribution for national (3,312), interviewed (300), visited (101) schools. May have been produced by `generate_representativeness_outputs.py` in July 2026 | Check outputs alongside `thesis/tables/tab_representativeness.tex` |
| `fig_C_subscore_heatmap.pdf` | **BLOCKED** | Heatmap: Ofsted LLM sub-dimensions vs interview sub-scores S1–S4, W1–W3. **First check whether `ofsted_analysis_results_v2.csv` has subcomponent columns** — if unified run removed them, figure may need reconceiving | `ofsted_analysis_results_v2.csv` subcomponent columns (if present) + `warm_strict_scores.csv` |
| `fig_ofsted_subscore_heatmap` (appendix) | **BLOCKED** | More detailed version of fig_C with cell sample sizes. Same dependency | Same as above |

---

## E — Tables to Produce (8 tables — referenced but not yet LaTeX)

| Table label | Content | Status | Source data |
|---|---|---|---|
| `tab:tier_summary` | Schools across tiers: N and key observable characteristics (FSM%, EAL%, size, Ofsted grade) by tier | **READY** | `warm_strict_scores.csv` + panel spine |
| `tab:score_dist` | Distribution of all 9 sub-scores + composites for 102 full-data schools (mean, SD, min, max) | **READY** | `warm_strict_scores.csv`, 102-school filter |
| `tab:irr_interview` | Per-question IRR for Q2–Q12: Pearson r, MAD, exact %, within-1 %, weighted κ (appendix) | **READY** | Interview Excel; questioner vs observer columns |
| `tab:irr_classroom` | Classroom observation IRR by item and rater pair (appendix) | **READY** | School Visit proforma data |
| `tab:irr_outside` | Outside-of-lesson observation IRR by item and rater pair (appendix) | **READY** | School Visit proforma data |
| `tab:interview_model_loo` | LOO-CV R² and RMSE for interview-tier Ridge (warmth and strictness, main and enriched specs) | **BLOCKED** | Rebuild Ridge with v25 BP + v6 interview scores |
| `tab:national_model_loo` | LOO-CV R² and RMSE for national-tier Ridge; three-spec comparison (A/B/C) | **BLOCKED** | Same Ridge rebuild |
| `tab:national_model_coefs` + `tab:interview_model_coefs` | Fitted coefficient vectors for both models (appendix) | **BLOCKED** | Same Ridge rebuild |

---

## F — Appendix Sections (5 sections — mostly INSERT shells)

| Appendix | Status | Action |
|---|---|---|
| `app:2A:guide` — Scoring Guide and Item Definitions | **READY** | Transfer from `Novel Data/Headteacher Interview.docx` and visit proforma docx files |
| `app:2A:irr` — IRR Tables | **READY** | Produced alongside B6 and B7 above |
| `app:2A:interview_guide` — Interview Guide | **READY** | Transfer full schedule (Q2–Q12 + S1–S10) from `Novel Data/Headteacher Interview.docx` |
| `app:2A:visit_protocol` — Visit Protocol | **READY** | Transfer from `Novel Data/School Visit Proforma - Outside of Lessons v2.docx` and `Novel Data/School Visit Proforma - Lesson Observations v2.docx` |
| `app:2A:prompts` — LLM Prompt Text | **ADD** | Extract prompts from Python scripts: (1) Ofsted unified `ofsted-strictness-warmth-teaching-v3`; (2) BP extraction pass; (3) BP scoring `behaviour-policy-strictness-warmth-v25`; (4) Website `website-strictness-warmth-v4`; (5) Ofsted leadership (gpt-4o-mini) |
| `app:2A:crawl` — BP Crawl Methodology | **ADD** | Summarise from `README_behaviour_policy_selector.md`, `README_policy_downloader.md`, and the two scripts; cover crawl approach (Brave Search API fallback), filter criteria, output file |

---

## G — Recommended Working Order

**Session 1 — No blocking dependencies:**
1. Prose fixes A1, A2, A3
2. Fill N values throughout (B1)
3. Check `ofsted_analysis_results_v2.csv` columns (determines whether subcomponent figures are feasible)
4. Produce fig_A and fig_B (Python matplotlib, save as PDF to `thesis/`)
5. Produce `tab:score_dist` and `tab:tier_summary`
6. Check whether `fig_D_regional_representativeness.pdf` already exists

**Session 2 — IRR and remaining ready items:**
7. Compute IRR statistics from interview Excel and visit proformas; produce `tab:irr_interview`, `tab:irr_classroom`, `tab:irr_outside`
8. Write IRR section body text (B6, B7)
9. Write abstract (B2), introduction preview (B3), fill literature cites (B4)
10. Fill document collection statistics (B5) and policy-aspiration sample sizes (B9)
11. Add website subsection (C2)
12. Add Parent View paragraph (C4)
13. Draft conclusion (the INSERT outline is very detailed — draft now, refine later)

**Session 3 — After Ridge rebuild:**
14. Fix `build_ridge_models.py` and `ridge_diagnostics.py` path references
15. Rebuild Ridge models with v25 BP + v6 interview scores
16. Insert LOO-CV tables (B10, B11) and coefficient tables
17. Update Ridge feature-set description in §sec:p1_text_valid

**Session 4 — After leadership national run completes:**
18. Move `ofsted_leadership_scores_national.csv` to `scores/`
19. Build analysis dataset
20. Compute national espoused/enacted gap table (C3)
21. Finalise management/leadership subsection (C1) with gap numbers
22. Complete Results section (B12) with national distribution statistics
23. Refine conclusion with final numbers

**Appendix work (can be done any time):**
- Transfer interview guide and scoring guide from docx files (app:2A:guide, app:2A:interview_guide, app:2A:visit_protocol)
- Extract LLM prompt text from Python scripts (app:2A:prompts)
- Write crawl methodology summary (app:2A:crawl)
