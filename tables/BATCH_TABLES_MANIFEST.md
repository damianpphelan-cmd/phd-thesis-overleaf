# Batch tables manifest — Chapter 3 restructure + post-merge analyses

Built 14 Aug 2026 from the scratchpad CSVs (`ch3_batch/`, `p8_sweep/`, `p8_proxy/`).
**All numbers are hard-coded from the CSVs; conversion to `make_numbers.py` macros is a
later pass.** No chapter file was edited; the `\cref` sites below are where each table
is intended to be `\input` and referenced.

| File | Label | Intended site | Placement | Data caveat carried in notes |
|---|---|---|---|---|
| `tab_spec_ladder.tex` | `tab:spec_ladder` | Ch3 (`03_paper2.tex`), main results section, beside `tab_main_results_s1` (~line 625) | **Main body** | Predecessor grade-fill described; including-late-entry sensitivity betas in notes |
| `tab_univariate_ws.tex` | `tab:univariate_ws` | Ch3 main results section, after the spec ladder | **Main body** | Trio outcomes only; EBacc/Open pointed to appendix |
| `tab_subscores.tex` | `tab:subscores` | Ch3 appendix (visit-component decomposition, ruling 4.6) | Appendix | VIF note: W1=4.70, T1=5.81 overlap heavily |
| `tab_items_fdr.tex` | `tab:items_fdr` | Ch3 appendix, directly after `tab_subscores` | Appendix (long) | BH-FDR across 33 items; per-item IRR beside each beta; composites stay headline |
| `tab_typology.tex` | `tab:typology` | Ch3 appendix (ruling 4.7); one main-body sentence may quote the authoritative contrast | Appendix | Gold interaction low-power; national W–S halo thins off-diagonal cells; verdict-reconstruction caveat; exploratory cross-source null in notes |
| `tab_gaps.tex` | `tab:gaps` | Ch3 appendix (ruling 4.8) | Appendix | Quadratic robustness kills the absolute-strictness gaps → named extremity, not dissonance; effects 0.01–0.02/SD |
| `tab_parentview.tex` | `tab:parentview` | Ch2 appendix (`02_paper1.tex`, ruling 4.9); Ch2 prose quotes the Ofsted row and the BP-negative row | Appendix | Soft criterion (single release per school, temporal misalignment noted, not fixed); Panel B endogeneity-footnoted |
| `tab_llm_p8_matrix.tex` | `tab:llm_p8_matrix` | Ch3 appendix (ruling 4.4); shows Panel B (grade-controlled) | Appendix | BH across the full 150-test sweep; BP rows clustered on document digest; grade-reconstruction caution; Panel A summarised in notes |
| `tab_entry_rates.tex` | `tab:entry_rates` | Ch3 appendix (ruling 4.4, the promised `sec:p2_secondary_outcomes` results) | Appendix | Languages = sharp test (double-science ceiling); channel decomposition second panel, 10–14% attenuation |
| `tab_p8_proxy.tex` | `tab:p8_proxy` | Ch3 appendix, pseudo-2024/25 section (ruling 4.5) | Appendix | +0.813 validation, +0.945 KS2 proxy, coverage 3,263/3,273, 14.7% intake-unstable (recomputed from CSV; the plan's 14.9% is superseded); gold-vs-headline spec reconciliation in notes |
| `tab_stability_p8.tex` | `tab:stability_p8` | Ch3 appendix (ruling 4.10) | Appendix | COVID gap: 2018-19→2021-22 boundary not an adjacent pair; event-time means are raw, not matched |
| `tab_representativeness.tex` (UPDATED) | `tab:2A:representativeness` | Already input at `02_paper1.tex:2071` | Appendix (existing) | New rows on full-tier n (103/303/3,332); grade rows use graded counts, prior-P8 rows n=95/259/2,731 — per-row n stated in notes |

## Representativeness table — exact changes
- Header: visited column `$(n=101)$` → `$(n=103)$`. (Interviewed left at 300 — the
  existing categorical rows were computed on that sample; only the new rows use 303.)
- New categorical block *Ofsted grade (Aug 2024)*: Outstanding 14.7 / 18.3 / 25.2;
  Good 69.2 / 70.3 / 63.1; Requires improvement 12.9 / 8.0 / 8.7; Inadequate
  3.2 / 3.3 / 2.9; Int. p<.05 (χ²=9.03, p=.029), Vis. p<.05 (χ²=9.96, p=.019).
- New continuous row *Prior P8 (2018–19)*, Mean: +0.04 / +0.08 / +0.17; Int. ns
  (t=+1.72, p=.087), Vis. p<.01 (t=+3.09, p=.003).
- Notes extended with the per-row n's. Every pre-existing row untouched.

## What the CSVs could not support
- No SD for the prior-P8 means (the batch reports means only), so that row shows
  Mean without (SD) unlike the other continuous rows.
- The typology table reports the gold model at n=100 (late-entry excluded); the
  three-way quadrant × traditional-pedagogy descriptive (raw cell means, 146
  traditional schools) was left for prose — one cell has n=1.
- `tab_p8_proxy` gold rows are n=103/96 (no late-entry exclusion in that run) —
  flagged in its notes as the reason its gold betas exceed the headline 0.13/0.12.
- Parent View temporal alignment is noted, not implemented (no per-release columns
  exist in the dataset).
