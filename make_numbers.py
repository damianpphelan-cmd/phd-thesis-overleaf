#!/usr/bin/env python3
"""Regenerate thesis/snippets/numbers.tex, and check the chapters against it.

Chapters 2 and 3 carry a few hundred hard-coded figures. Most appear in several
places at once — a count in the abstract, again in the introduction, again in the
results, again in the conclusion — and the audit found eight cases where one copy
had been updated and the others had not. This script attacks that from both ends:

    python thesis/make_numbers.py            # write snippets/numbers.tex
    python thesis/make_numbers.py --check    # scan chapters for drift (exit 1 if any)

`--check` is the part that earns its keep. For every canonical figure it searches
the chapter sources for the literal that *should* be there and for known-stale
literals that should not — the values corrected during the audit. Re-introduce
one and the check fails. It needs no LaTeX toolchain.

Figures marked source="notebook" cannot be recomputed here; they come from
thesis/chapter3_analysis.ipynb (Stata). They are asserted, not derived, and the
comment on each says where it came from. Everything else is computed from
analysis_dataset.csv on each run, so it cannot silently go stale.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
THESIS = ROOT / "thesis"
SNIPPETS = THESIS / "snippets" / "numbers.tex"
# main.tex and the introduction joined the guard 14 Aug 2026, after the thesis
# abstract was found quoting a superseded 0.418 that the chapter-only guard
# could not see.
CHAPTERS = [THESIS / "chapters" / "02_paper1.tex",
            THESIS / "chapters" / "03_paper2.tex",
            THESIS / "chapters" / "01_introduction.tex",
            THESIS / "main.tex"]


class Num:
    """One canonical figure.

    key     LaTeX command name (letters only)
    value   the rendered LaTeX body, e.g. "3{,}332" or "0.418"
    expect  literals that must appear in the chapters (defaults to [value])
    stale   literals that must NOT appear — previously-wrong values
    note    where the figure comes from
    """

    def __init__(self, key, value, note, expect=None, stale=()):
        self.key = key
        self.value = value
        self.note = note
        self.expect = list(expect) if expect is not None else [value]
        self.stale = list(stale)


def comma(n: int) -> str:
    """LaTeX thousands separator: 3332 -> 3{,}332."""
    return f"{n:,}".replace(",", "{,}")


def both_forms(n: int) -> list[str]:
    """Accept a thousands figure in math mode (3{,}332) or text mode (3,332)."""
    return [comma(n), f"{n:,}"]


def build() -> list[Num]:
    d = pd.read_csv(ROOT / "analysis_dataset.csv", encoding="utf-8-sig",
                    low_memory=False)
    tier = d["gs_data_tier"].fillna("national")
    full = d[tier == "full"]

    # NO BLEND, 5 Aug 2026: gs_*_composite is gone. The warmth-strictness correlation
    # now has to say WHICH construct it is about, and the two answers differ, so both
    # are emitted. The enacted one is the thesis's own contrast — warmth and strictness
    # as observed in the same lessons — and is the one to quote by default.
    def _r(a: str, b: str) -> tuple[float, int]:
        x = full[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
        return float(stats.pearsonr(x[a], x[b])[0]), len(x)

    r_ws_en, n_ws_en = _r("gs_warmth_enacted", "gs_strictness_enacted")
    r_ws_es, n_ws_es = _r("gs_warmth_espoused", "gs_strictness_espoused")

    lead = d.dropna(subset=["ofsted_LLMLeadershipScore", "ofsted_grade"])
    r_lead = stats.pearsonr(
        pd.to_numeric(lead["ofsted_LLMLeadershipScore"]),
        pd.to_numeric(lead["ofsted_grade"]))[0]

    ph = d["web_id_LLMTeachingPhilosophy"].value_counts(dropna=False)

    # W3 is a raw sub-score and is not carried into analysis_dataset.csv (only
    # the quality-adjusted W3* is), so it comes from the scorer's own output.
    w3 = pd.to_numeric(
        pd.read_csv(ROOT / "scores" / "warm_strict_scores.csv",
                    encoding="utf-8-sig", low_memory=False)["W3"],
        errors="coerce").dropna()

    N = []
    add = N.append

    # ── Sample sizes ─────────────────────────────────────────────────────────
    add(Num("NSchools", comma(len(d)), "analysis_dataset.csv rows",
            expect=both_forms(len(d))))
    add(Num("NTierOne", str((tier == "full").sum()),
            "visit + interview"))
    add(Num("NTierTwo", str((tier == "interview_only").sum()),
            "interview only"))
    add(Num("NTierThree", comma((tier == "national").sum()),
            "remaining national",
            expect=both_forms(int((tier == "national").sum())),
            stale=["3{,}027", "3,027"]))
    add(Num("NInterviewed", str(tier.isin(["full", "interview_only"]).sum()),
            "tiers 1+2"))

    # ── Chapter 2 headline measurement figures ───────────────────────────────
    # The old \CorrWarmthStrictness was 0.494 on the abolished composite. Both halves
    # of that number came partly from the same interview, which is most of why it was
    # so much higher than either construct measured on its own.
    # CAVEAT THAT MUST TRAVEL WITH THIS NUMBER: one observer scored warmth and
    # strictness in the same lesson, so it contains halo and shared-occasion
    # variance. The visit decomposition (visit_decomposition.py, 351 double- or
    # triple-rated lessons) puts the cross-observer lesson-level correlation at
    # +0.261 against +0.281 same-observer (individual halo is small), and the
    # disattenuated cross-observer trait correlation at +0.360. The macros below
    # are parsed from visit_decomposition_report.txt; rerun that script first if
    # the visit data change. (The +0.290 previously noted here was a stale
    # pre-item-extension figure.)
    add(Num("CorrWarmthStrictnessEnacted", f"{r_ws_en:.3f}",
            f"observed W-S correlation, Tier 1, n={n_ws_en}; contains halo and "
            f"shared-occasion variance — see CorrWSTrue",
            stale=["0.494"]))
    _rep = open(ROOT / "visit_decomposition_report.txt", encoding="utf-8").read()
    import re as _re
    _m = _re.search(r"warmth x strictness\s+\+(0\.\d+) \(n=351\)\s+\+(0\.\d+) \(n=351\)", _rep)
    _m2 = _re.search(r"warmth x strictness\s+\+(0\.\d+)\s+0\.\d+ x 0\.\d+\s+\+(0\.\d+)", _rep)
    if not (_m and _m2):
        raise SystemExit("make_numbers: halo figures not found in visit_decomposition_report.txt")
    add(Num("CorrWSSameObs", f"{float(_m.group(1)):.2f}",
            "visit_decomposition_report.txt: same-observer lesson-level W-S correlation"))
    add(Num("CorrWSCrossObs", f"{float(_m.group(2)):.2f}",
            "visit_decomposition_report.txt: cross-observer lesson-level W-S correlation"))
    add(Num("CorrWSTrue", f"{float(_m2.group(2)):.2f}",
            "visit_decomposition_report.txt: disattenuated cross-observer W-S trait correlation"))
    add(Num("CorrWarmthStrictnessEspoused", f"{r_ws_es:.3f}",
            f"interview W-S correlation, Tier 1 (visited) schools, n={n_ws_es}"))
    add(Num("CorrLeadershipNational", f"{r_lead:.3f}",
            "LLM leadership vs ofsted_grade (inverse coding)",
            expect=[f"{abs(r_lead):.3f}"]))
    add(Num("NLeadershipNational", comma(len(lead)),
            "schools with leadership score and Ofsted grade"))
    # CorrOfstedStrictness is derived below, with the other ridge_diagnostics
    # figures it belongs with.

    # ── Sub-score distributions (the score-compression argument) ─────────────
    # The chapter argues that compression has two sources, and distinguishes
    # them by distribution shape: W3 is narrow but smooth, while the LLM
    # transcript scores pile up on a single integer. Both halves of that
    # contrast are checked here, because an earlier draft attributed the LLM
    # scores' modal spike to W3 and drew the opposite conclusion from it.
    add(Num("MeanWThree", f"{w3.mean():.2f}", "W3 mean, warm_strict_scores.csv",
            expect=[f"mean of~${w3.mean():.2f}$"]))
    add(Num("SDWThree", f"{w3.std():.2f}", "W3 SD, warm_strict_scores.csv",
            expect=[f"deviation of~${w3.std():.2f}$"],
            stale=["deviation of~$0.44$"]))
    add(Num("PctWThreeModal", f"{(w3 == 4).mean() * 100:.0f}",
            "per cent of schools with W3 exactly 4",
            expect=[f"{(w3 == 4).mean() * 100:.0f}~per cent of schools at the modal"],
            stale=["84~per cent of interviewed schools scoring"]))
    # REPOINTED 5 Aug 2026 onto the segmented scorers. These three macros exist to
    # document a scale collapse -- the share of schools sitting on the single modal
    # band -- and the collapse belonged to the v6 bundled scorer, which is dead and
    # no longer written to the dataset. Recomputing the same statistic on the
    # segmented scorers is the honest move, but it is a DIFFERENT measurement, so
    # the --check guards below will fail against any chapter text still quoting the
    # v6 figures. That failure is the point: the prose has to be revisited, not the
    # macro silently refilled.
    for lab, col, phrase in [
            ("Warmth", "trx_warmth", "per cent of schools receive a warmth"),
            ("Management", "trx_management", "per cent a management"),
            ("Strictness", "trx_strictness", "per cent a strictness")]:
        v = pd.to_numeric(d[col], errors="coerce").dropna()
        # This hard-coded `== 4` until 5 Aug 2026, which was accidentally correct:
        # band 4 WAS the mode for all three v6 scores. It is not the mode for any of
        # the segmented ones (warmth peaks at 5, strictness and management at 3), so
        # a macro called "Modal" would have started reporting a non-modal band.
        modal = v.mode().iloc[0]
        pct = f"{(v == modal).mean() * 100:.0f}"
        add(Num(f"PctTrx{lab}Modal", pct,
                f"per cent of schools with {col} on its modal band ({modal:.0f})",
                expect=[f"{pct}~{phrase}"]))

    # ── Ridge models ─────────────────────────────────────────────────────────
    # DERIVED, not asserted. These were hard-coded string literals until 2 Aug
    # 2026, which made --check blind to the failure it exists to catch: adopting
    # Ofsted v4 moved Model B warmth from -0.018 to +0.220, and all six guards
    # still passed because the chapters agreed with the stale literal. The guard
    # only ever compared prose to macro, never macro to data.
    #
    # ridge_model_loo.csv is written by build_ridge_models.py on every refit, so
    # the chain now runs data -> model -> csv -> numbers.tex -> --check, and a
    # refit that moves a figure makes the chapters fail until they are updated.
    loo = pd.read_csv(ROOT / "ridge_model_loo.csv")
    loo_r = {(r["model"], r["dimension"]): r["loo_r"] for _, r in loo.iterrows()}

    def ridge(key: str, model: str, dim: str, note: str, stale=()) -> None:
        # LaTeX renders a leading minus as "-0.018"; match the chapters' form.
        add(Num(key, f"{loo_r[(model, dim)]:.3f}", note, stale=stale))

    ridge("RidgeAWarmth", "A", "Warmth", "Model A LOO-CV r, warmth",
          stale=["0.765"])
    ridge("RidgeAStrictness", "A", "Strictness", "Model A LOO-CV r, strictness")
    # Qualified with "r =" for the same reason BetaTraditional carries no stale
    # literal at all: a bare three-digit decimal collides with unrelated
    # coefficients. On 5 Aug 2026 the espoused warmth coefficient for the Open
    # component came out at exactly -0.018 and this check fired on it.
    # NOTE: RidgeBWarmth is the LOO r of a DEGENERATE model (predictions near
    # constant); the tables print "---" for it and no prose should quote it.
    ridge("RidgeBWarmth", "B", "Warmth", "Model B LOO-CV r, warmth",
          stale=["$r = -0.018$"])
    ridge("RidgeBStrictness", "B", "Strictness", "Model B LOO-CV r, strictness",
          stale=["0.329"])

    # The fitted N, which is NOT the Tier 1 count. Both models use Ofsted text
    # features and two Tier 1 schools have no scored report, so all four models
    # fit on 100 while the tier is 102. Every caption and every prose sentence
    # said 102 until 2 Aug 2026.
    #
    # The stale literals are full phrases, not a bare "102", because the chapter
    # says 102 a dozen times perfectly correctly when describing the tier, the
    # gold standard, or any interview-only quantity. Only sentences about
    # FITTING may not say 102. Whitespace is collapsed before matching, so these
    # survive LaTeX line-wrapping falling anywhere inside them.
    n_fit = sorted({int(v) for v in loo["n"]})
    add(Num("RidgeTrainN", str(n_fit[0]),
            "Ridge fitted sample (all four models)",
            expect=[f"{n_fit[0]} full-data schools",
                    f"{n_fit[0]} training schools"],
            stale=["trained on the 102 full-data schools",
                   "fitted on the 102 full-data schools",
                   "cross-validation on the 102 training schools",
                   "cross-validation on the 102 full-data schools",
                   "cross-validation on the 102 Tier~1 schools",
                   "interview composite scores for the 102 full-data schools"]))
    if len(n_fit) > 1:
        # The captions handle this, but the prose above says "the same 100
        # schools" and would become false.
        print(f"WARNING: models no longer share one fitted sample: {n_fit}. "
              f"Check the sentence in sec:p1_enriched_model claiming both "
              f"tiers train on an identical sample.")
    # Same treatment for the circularity figures, written by ridge_diagnostics.py.
    circ = pd.read_csv(ROOT / "ridge_circularity.csv")
    # Stale literals are qualified with "$r = " because the bare decimals collide
    # with unrelated numbers elsewhere: 0.228 is also the upper bound of a warmth
    # confidence interval in 03_paper2.tex, and an unqualified guard flagged it
    # as drift. A guard that cries wolf gets ignored, which is the one failure
    # mode it cannot afford.
    circ_stale = {"CircWarmthVisit": ["$r = 0.267$"],
                  "RefitWarmthVisit": ["$r = 0.228$", "$r = 0.240$"],
                  "RefitStrictnessVisit": ["$r = 0.349$"],
                  "CorrOfstedStrictness": ["$r = 0.418$", "$r = 0.483$"]}
    for _, r in circ.iterrows():
        add(Num(r["key"], f"{r['value']:.3f}", r["note"],
                stale=circ_stale.get(r["key"], ())))

    # ── The dissociation corrected, 14 Aug 2026 ──────────────────────────────
    # The Ch2 abstract used to claim a double dissociation (strictness tracks
    # visits not talk; warmth the reverse) quoting r = 0.087 and r = 0.312. The
    # espoused rebuild showed the 0.087 belonged to a broken measure: fix the
    # measure and strictness tracks BOTH sides — convergence, not dissociation
    # (`check_double_dissociation.py` is the file of record). This macro is the
    # espoused leg of the corrected claim, and the old 2x2's numbers are its
    # stale literals so they can never quietly return.
    es = d[["ofsted_LLMStrictnessScore", "gs_strictness_espoused"]].apply(
        pd.to_numeric, errors="coerce").dropna()
    r_se = float(stats.pearsonr(es.iloc[:, 0], es.iloc[:, 1])[0])
    # ── The primary-specification headline (guarded, not derived) ────────────
    # STATA IS THE SOURCE, 14 Aug 2026. These were the Python (statsmodels)
    # figures from analyse_ch3_batch.py until the control set was checked
    # against the documented specification: Python omitted `years_since_ofsted`,
    # which the documented control set includes. The Python numbers were
    # therefore off-spec, not merely a different software route, and they are
    # now stale literals so they cannot come back. thesis/ch3_estimates.do runs
    # the documented spec (full controls, predecessor-filled 2019 grade,
    # late-entry excluded, HC3); the extra control costs one school, so n is 99.
    #
    # The older 0.150/0.130 headline stays on the stale list too: the guards are
    # narrow (coefficient form only) so the SEMH passage's unrelated
    # 0.150 -> 0.165 comparison does not false-positive.
    # Read from the Stata export (19 Aug 2026): these were typed literals until
    # the number verification found the do-file had changed scale under them.
    _e = pd.read_csv(THESIS / "tables" / "ch3_estimates.csv")
    _p = _e[(_e.spec == "primary_stage1") & (_e.outcome == "overall")].set_index("term")
    _pw = f"{_p.loc['z_gs_warmth_enacted', 'b']:.3f}"
    _ps = f"{_p.loc['z_gs_strictness_enacted', 'b']:.3f}"
    add(Num("PrimarySpecW", _pw,
            "primary-spec warmth coefficient per SD, ch3_estimates.do (Stata)",
            expect=[r"\hat{\beta}_W = " + _pw],
            stale=[r"\hat{\beta}_W = 0.150", r"\hat{\beta}_W = 0.132", r"\hat{\beta}_W = 0.143"]))
    add(Num("PrimarySpecS", _ps,
            "primary-spec strictness coefficient per SD, ch3_estimates.do (Stata)",
            expect=[r"\hat{\beta}_S = " + _ps],
            stale=[r"\hat{\beta}_S = 0.130", r"\hat{\beta}_S = 0.117", r"\hat{\beta}_S = 0.131"]))
    _ppw = f"{_p.loc['z_gs_warmth_enacted', 'pval']:.3f}"
    _pps = f"{_p.loc['z_gs_strictness_enacted', 'pval']:.3f}"
    add(Num("PrimarySpecPW", _ppw,
            "primary-spec warmth p-value, ch3_estimates.do (Stata)",
            expect=[f"($p = {_ppw}$)"],
            stale=[r"($p = 0.002$)"]))
    add(Num("PrimarySpecPS", _pps,
            "primary-spec strictness p-value, ch3_estimates.do (Stata)",
            expect=[f"($p = {_pps}$)"],
            stale=[r"($p = 0.007$)"]))
    # Magnitudes in outcome standard deviations. The visited estimates
    # take the estimation-sample SD that Stata posts as sens_sd and the
    # sensitivity analysis already uses; the national estimates take the
    # SD across the national school population, because that is the
    # sample those regressions run on.
    _sd_est = float(_e[(_e.spec == "sens_sd")
                       & (_e.term == "p8mea_avg")]["b"].iloc[0])
    _sd_nat = float(pd.to_numeric(d["p8mea_avg"], errors="coerce").std())
    add(Num("SDPEightEst", f"{_sd_est:.2f}",
            "SD of Progress 8 on the visited estimation sample, "
            "posted by ch3_estimates.do as sens_sd"))
    add(Num("SDPEightNat", f"{_sd_nat:.2f}",
            "SD of Progress 8 across the national school population"))
    add(Num("PrimarySpecWSD", f"{float(_pw) / _sd_est:.2f}",
            "warmth coefficient in estimation-sample outcome SDs"))
    add(Num("PrimarySpecSSD", f"{float(_ps) / _sd_est:.2f}",
            "strictness coefficient in estimation-sample outcome SDs"))

    _ap = pd.read_csv(THESIS / "tables" / "ch3_appendix_estimates.csv")
    _auth = float(_ap[(_ap.table == "typology") & (_ap.panel == "gold")
                      & (_ap.term == "auth")]["b"].iloc[0])
    add(Num("QuadrantSD", f"{_auth / _sd_est:.2f}",
            "authoritative-vs-rest gap in estimation-sample outcome SDs"))

    # The espoused substitution: the same primary specification with the
    # headteacher's own ratings in place of the observers' scores.
    _es = _e[(_e.spec == "primary_espoused")
             & (_e.outcome == "overall")].set_index("term")
    add(Num("EspousedWCoef",
            f"{_es.loc['z_gs_warmth_espoused', 'b']:.3f}",
            "espoused warmth coefficient, primary spec (Stata)"))
    add(Num("EspousedWP",
            f"{_es.loc['z_gs_warmth_espoused', 'pval']:.2f}",
            "espoused warmth p-value, primary spec (Stata)"))
    add(Num("EspousedSCoef",
            f"{_es.loc['z_gs_strictness_espoused', 'b']:.3f}",
            "espoused strictness coefficient, primary spec (Stata)"))
    add(Num("EspousedSP",
            f"{_es.loc['z_gs_strictness_espoused', 'pval']:.3f}",
            "espoused strictness p-value, primary spec (Stata)"))

    add(Num("PrimarySpecN", "99",
            "primary estimation sample: 103 - 2 late-entry - 1 unfillable "
            "grade - 1 missing years_since_ofsted",
            expect=["$n = 99$"]))

    add(Num("CorrOfstedStrictEspoused", f"{r_se:.3f}",
            f"Ofsted LLM strictness vs espoused strictness (statement battery), "
            f"n={len(es)}. The espoused leg of the strictness-convergence claim "
            f"in the Ch2 abstract",
            expect=[f"$r = {r_se:.3f}$"],
            stale=["$r = 0.087$", "$r = 0.312$", "$r = 0.161$, $p = 0.11$"]))

    # ── Teaching quality: scored, validated, deliberately not carried forward ─
    # The chapter used to justify the exclusion with a bright-line "r > 0.30
    # validation gate" and the figure r = 0.133. Under Ofsted v4 that figure is
    # 0.292 and the gate stopped doing the work claimed of it: warmth, which IS
    # carried forward, sits at 0.268 and fails the same threshold. The argument
    # now rests on the espoused/enacted split, so all three figures below are
    # load-bearing and are derived here rather than asserted.
    #
    # The gate phrasing is itself a stale literal. It is the sentence, not just
    # the number, that the evidence stopped supporting.
    def corr(a: str, b: str) -> tuple[float, int]:
        d = full[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
        return float(stats.pearsonr(d[a], d[b])[0]), len(d)

    # ESPOUSED REBUILT, 6 Aug 2026. `gs_teaching_espoused` is now
    # `gs_staff_climate_espoused`: with the explanation-quality question scores removed its
    # items are "Teacher turnover is low" and "Staff morale is good". r_tc and r_tx are
    # therefore TEACHING-against-STAFF-MORALE, a cross-construct contrast, and must not be
    # written up as convergent validity for either teaching scorer. The interview has no
    # espoused teaching measure -- see the `warm_strict_scorer.py` header. r_tv is
    # unaffected: the visit side is unchanged.
    r_tc, _ = corr("ofsted_LLMTeachingScore", "gs_staff_climate_espoused")
    r_tv, _ = corr("ofsted_LLMTeachingScore", "gs_teaching_enacted")
    r_tx, _ = corr("trx_teaching", "gs_staff_climate_espoused")

    # ── Espoused vs enacted inside the gold standard itself ──────────────────
    # The exclusion argument above rests on an espoused/enacted asymmetry that a
    # sceptic can attribute to the LLM. These three figures close that off: both
    # sides are the researcher's own scoring, from one instrument.
    #
    # These used to be assembled by hand from sub-scores, with a warning that the
    # pairing had to be LIKE FOR LIKE — strictness needed mean(S3,S4) and not S4
    # alone, which returned 0.284 and invented a gradient that was not there. Since
    # 5 Aug 2026 the two sides are named columns, so there is nothing left to pair
    # up wrongly: gs_*_espoused IS the interview side and gs_*_enacted IS the
    # observation side. (Both are on the 0-10 scale; a common rescale leaves a
    # correlation unchanged.)
    #
    # These figures are also the empirical case for abolishing the composite: an average
    # of two measures that disagree this much is not a better measure of either.
    #
    # TEACHING LEFT THIS LOOP ON 6 AUG 2026. It has no espoused measure: once the
    # explanation-quality question scores were removed, the interview's teaching items were
    # "Teacher turnover is low" and "Staff morale is good". Iterating it here would have
    # emitted a \GoldTeachingSplit macro asserting an espoused/enacted split for a construct
    # the interview never measured.
    #
    # The warmth and strictness figures MOVED with the rebuild and the old range quoted in
    # this comment (0.18-0.24) is stale: dropping the question scores and the Y/N systems
    # count more than doubled strictness. Anything in the chapters quoting the old numbers
    # is out of date -- these macros are derived, so \GoldWarmthSplit and
    # \GoldStrictnessSplit update themselves, but surrounding PROSE does not.
    for dim in ("Warmth", "Strictness"):
        d = full[[f"gs_{dim.lower()}_espoused", f"gs_{dim.lower()}_enacted"]].apply(
            pd.to_numeric, errors="coerce").dropna()
        r_ee, p_ee = stats.pearsonr(d.iloc[:, 0], d.iloc[:, 1])
        add(Num(f"Gold{dim}Split", f"{r_ee:.3f}",
                f"gold {dim.lower()}: espoused vs enacted, "
                f"n={len(d)}, p={p_ee:.3f}",
                expect=[f"$r = {r_ee:.3f}$"]))
        # The chapters used to hard-code these p-values; they drifted when the
        # espoused rebuild moved the correlations (a quoted p of 0.054 next to
        # an r of 0.410 at n=103 is arithmetically impossible). Emitted as
        # macros so they can never detach from their r again.
        p_body = "< 0.001" if p_ee < 0.001 else f"{p_ee:.3f}"
        add(Num(f"Gold{dim}SplitP", p_body,
                f"p-value belonging to Gold{dim}Split", expect=[]))

    # ── The espoused-enacted GAP, recomputed on the rebuilt espoused scores ──
    # 17 Aug 2026. The chapters used to say heads over-claim warmth by +0.51
    # points and that the strictness gap was near zero (+0.07, p = 0.53). Both
    # predate the espoused rebuild; on the statement-battery scores the gaps
    # are +1.84 warmth and +0.88 strictness (paired t, p < 0.001 for both), so
    # the old figures are stale literals. Quoted in prose to one decimal.
    for dim, stale in (("Warmth", ["$0.51$ points higher", "$+0.51$ points",
                                   "average of $+0.51$", "0.51 points"]),
                       ("Strictness", ["$+0.07$ points", "\\Delta = +0.07",
                                       "+0.07 points"])):
        g = full[[f"gs_{dim.lower()}_espoused", f"gs_{dim.lower()}_enacted"]].apply(
            pd.to_numeric, errors="coerce").dropna()
        gap = float((g.iloc[:, 0] - g.iloc[:, 1]).mean())
        add(Num(f"Gap{dim}", f"{gap:.1f}",
                f"mean espoused minus enacted {dim.lower()}, Tier 1, n={len(g)}, "
                f"0-10 scale, {gap:+.2f} unrounded",
                expect=[f"${gap:.1f}$"], stale=stale))

    # Named for what it is. NOT a \GoldTeachingSplit: the two sides are different
    # constructs, so this is a descriptive contrast and not an espoused/enacted split.
    d = full[["gs_staff_climate_espoused", "gs_teaching_enacted"]].apply(
        pd.to_numeric, errors="coerce").dropna()
    r_sc, p_sc = stats.pearsonr(d.iloc[:, 0], d.iloc[:, 1])
    add(Num("GoldStaffClimateVsTeaching", f"{r_sc:.3f}",
            f"espoused staff climate (turnover + morale) vs ENACTED teaching, "
            f"n={len(d)}, p={p_sc:.3f}. CROSS-CONSTRUCT: the interview has no espoused "
            f"measure of teaching practice"))

    # Renamed 5 Aug 2026 with the composite. Nothing in the chapters referenced the old
    # macros yet, so this is a free rename; the values move as well as the names.
    # Renamed again 6 Aug 2026. The old macro names claimed these were teaching-vs-teaching
    # comparisons. They are teaching-vs-staff-climate, so the names now say so: writing
    # \OfstedTeachingEspoused into a chapter would assert convergent validity that this
    # number cannot support. There is no espoused teaching measure to put in its place.
    add(Num("OfstedTeachingVsStaffClimate", f"{r_tc:.3f}",
            "Ofsted teaching vs espoused STAFF CLIMATE (turnover + morale), full-data "
            "tier. CROSS-CONSTRUCT: not convergent validity for the teaching scorer",
            stale=["$r = 0.133$", "$r > 0.30$ validation gate",
                   "did not satisfy the"]))
    add(Num("OfstedTeachingEnacted", f"{r_tv:.3f}",
            "Ofsted teaching vs ENACTED gold teaching (the observed lessons)"))
    add(Num("TrxTeachingVsStaffClimate", f"{r_tx:.3f}",
            "interview-transcript teaching vs espoused STAFF CLIMATE. CROSS-CONSTRUCT: "
            "the interview has no espoused measure of teaching practice"))

    # ── Teaching philosophy (v3 classification) ──────────────────────────────
    add(Num("NTraditional", str(ph.get("traditional", 0)),
            "website teaching philosophy v3, full corpus", stale=["472"]))
    add(Num("NProgressive", str(ph.get("progressive", 0)),
            "website teaching philosophy v3, full corpus", stale=["179"]))
    # The chapters quote the estimation-sample count (3,037), not the corpus
    # count, so there is no literal to search for here.
    add(Num("NUnmarked", comma(int(ph.get("unmarked", 0))),
            "website teaching philosophy v3, full corpus", expect=[]))

    # ── Chapter 3 estimates ──────────────────────────────────────────────────
    # These used to be asserted from a Stata log, which is how NEstimation sat at
    # 95 through a re-run that moved it to 96 and BetaWarmth sat at 0.127 through
    # one that moved it to 0.150. They are now read from the tidy exports that
    # thesis/ch3_estimates.do and thesis/a7_national_strictness.do write, so a
    # re-run propagates here and --check fails until the chapters follow.
    ch3 = pd.read_csv(THESIS / "tables" / "ch3_estimates.csv")

    def est(spec: str, outcome: str, term: str) -> pd.Series:
        row = ch3[(ch3.spec == spec) & (ch3.outcome == outcome)
                  & (ch3.term == term)]
        if len(row) != 1:
            raise SystemExit(f"ch3_estimates.csv: expected 1 row for "
                             f"{spec}/{outcome}/{term}, found {len(row)}")
        return row.iloc[0]

    # REPOINTED 17 Aug 2026 from the "stage1" rows (the pre-primary spec, n=96,
    # kept in the CSV for the archive) to "primary_stage1", which is what the
    # chapter quotes. The old stale=["0.127"] guard was written when 0.127 was a
    # retired warmth headline; it collided with the primary-spec no-grade
    # strictness coefficient (0.127) the moment that entered the prose. A stale
    # literal must be unambiguous, so it is dropped here: PrimarySpecW/S carry
    # the headline guards with their own stale lists.
    s1w = est("primary_stage1", "overall", "z_gs_warmth_enacted")
    s1s = est("primary_stage1", "overall", "z_gs_strictness_enacted")
    add(Num("NEstimation", str(int(s1w["n"])),
            "ch3_estimates.csv: primary Stage 1-3 estimation sample", expect=[]))
    add(Num("BetaWarmth", f"{s1w['b']:.3f}",
            "ch3_estimates.csv: primary Stage 1 overall P8"))
    add(Num("BetaStrictness", f"{s1s['b']:.3f}",
            "ch3_estimates.csv: primary Stage 1 overall P8"))

    # Replacing the enacted scores with the espoused ones on the SAME schools is
    # the chapter's self-report test; the quoted range is over the four
    # components, and the top of it exceeds 100 because two of them reverse sign.
    drops = [100 * (1 - est("espoused_t1", o, "z_gs_warmth_espoused")["b"]
                        / est("stage1", o, "z_gs_warmth_enacted")["b"])
             for o in ("english", "maths", "ebac", "open")]
    add(Num("SelfReportReduction",
            f"{round(min(drops))}--{round(max(drops))}",
            "ch3_estimates.csv: espoused-for-enacted warmth reduction, per cent",
            stale=["63--91", "63--106"]))

    # REPOINTED 24 Aug 2026 from thesis/tables/a7_estimates.csv (the RETIRED
    # analyser-score national leg) to the new-instrument runs: the
    # marking-scheme strictness bands (national_strictness_regression_results
    # .csv, written by national_strictness_regression.py) and the band
    # age-interaction from band_extras_results.csv (analyse_band_extras.py).
    # The chapters quote the coefficients through \NatS/\NatSPre in
    # snippets/national_numbers.tex (make_ch3_national_tables.py), so the two
    # Beta macros carry expect=[] here; they exist so a literal 0.138/0.137 --
    # the retired a7 values -- can never be mistaken for canonical again.
    # Those retired values are NOT stale-guarded: bare "0.138"/"0.137" also
    # occur legitimately (gold EBaC strictness, one-cohort robustness), and a
    # stale literal must be unambiguous.
    nsr = pd.read_csv(ROOT / "national_strictness_regression_results.csv")
    nso = nsr[nsr.spec == "no grade control"].iloc[0]
    add(Num("NNationalStrictness", comma(int(nso["n"])),
            "national_strictness_regression_results.csv: marking-scheme "
            "bands, national estimation sample",
            stale=["3{,}194", "3{,}148"]))
    add(Num("BetaNationalStrictness", f"{nso['b']:.3f}",
            "national_strictness_regression_results.csv: marking-scheme "
            "bands, overall P8, no-grade spec (chapters quote \\NatS)",
            expect=[]))
    nsp = nsr[nsr.spec == "pre-2022 reports, no grade"].iloc[0]
    add(Num("BetaNationalPre", f"{nsp['b']:.3f}",
            "national_strictness_regression_results.csv: marking-scheme "
            "bands on reports published before Sept 2022 (pre-outcome-window "
            "subsample), no-grade spec (chapters quote \\NatSPre)",
            expect=[]))
    add(Num("NNationalPre", comma(int(nsp["n"])),
            "national_strictness_regression_results.csv: pre-window "
            "subsample size"))
    add(Num("ShareNationalPre", f"{100 * nsp['n'] / nso['n']:.0f}",
            "national_strictness_regression_results.csv: share of "
            "national-sample reports published before Sept 2022, per cent"))
    bex = pd.read_csv(ROOT / "band_extras_results.csv")
    bx = bex[bex.spec == "age interaction"].iloc[0]
    add(Num("BetaNationalAgeInt", f"{bx['b']:.3f}",
            "band_extras_results.csv: interaction of the marking-scheme band "
            "score with centred report age, per year",
            expect=["$-0.003$ per year of report age"],
            stale=["$-0.002$ per year of report age"]))
    add(Num("PNationalAgeInt", f"{bx['p']:.2f}",
            "band_extras_results.csv: p-value of the band x report-age "
            "interaction",
            expect=["$p = 0.09$, on the marking-scheme"],
            stale=["per year of report age, $p = 0.15$"]))

    # Context benchmarks quoted beside the primary estimates (referee point:
    # they had no cited source). Computed nationally from analysis_dataset.csv.
    _ds = pd.read_csv(ROOT / "analysis_dataset.csv", low_memory=False,
                      usecols=["p8mea_avg", "grade2019_filled", "fsm"])
    _p8 = pd.to_numeric(_ds["p8mea_avg"], errors="coerce")
    _g19 = pd.to_numeric(_ds["grade2019_filled"], errors="coerce")
    _gap_grade = _p8[_g19 == 1].mean() - _p8[_g19 == 2].mean()
    add(Num("GapOutstandingGood", f"{_gap_grade:.2f}",
            "national mean P8 gap, 2019 Outstanding vs Good "
            "(grade2019_filled), analysis_dataset.csv"))
    _fsm = pd.to_numeric(_ds["fsm"], errors="coerce")
    # Espoused means/SDs over all interviewed schools (referee close-out: the
    # 303-school figures previously appeared in no table or macro).
    _esp = pd.read_csv(ROOT / "analysis_dataset.csv", low_memory=False,
                       usecols=["gs_warmth_espoused", "gs_strictness_espoused"])
    _ew = pd.to_numeric(_esp["gs_warmth_espoused"], errors="coerce").dropna()
    _es = pd.to_numeric(_esp["gs_strictness_espoused"], errors="coerce").dropna()
    add(Num("MeanWEspAll", f"{_ew.mean():.1f}", "espoused warmth mean, all interviewed"))
    add(Num("SDWEspAll", f"{_ew.std():.1f}", "espoused warmth SD, all interviewed"))
    add(Num("MeanSEspAll", f"{_es.mean():.1f}", "espoused strictness mean, all interviewed"))
    add(Num("SDSEspAll", f"{_es.std():.1f}", "espoused strictness SD, all interviewed"))

    _q = pd.qcut(_fsm, 4, labels=False)
    _gap_fsm = _p8[_q == 0].mean() - _p8[_q == 3].mean()
    add(Num("GapFsmQuartiles", f"{_gap_fsm:.2f}",
            "national mean P8 gap, least vs most disadvantaged FSM quartile, "
            "analysis_dataset.csv"))

    # Still asserted: the teaching-philosophy cell writes only a LaTeX table, so
    # there is nothing tidy to read. Source is tables/tab_teaching_philosophy.tex,
    # column "Overall", row "Traditional (vs unmarked)".
    #
    # No stale literal for this one: the superseded v2 value was 0.039, but a
    # bare three-digit decimal collides with unrelated coefficients elsewhere
    # (e.g. the management-discourse range runs to $-0.039$). The v2/v3 split is
    # caught upstream instead, by NTraditional/NProgressive.
    add(Num("BetaTraditional", "0.124", "notebook: teaching philosophy v3"))

    return N


def write(nums: list[Num]) -> None:
    lines = [
        "% Auto-generated by thesis/make_numbers.py --- do not edit by hand.",
        "% Regenerate:  python thesis/make_numbers.py",
        "% Check the chapters against these values:",
        "%              python thesis/make_numbers.py --check",
        "%",
        "% This file IS \\input, by preamble.tex (it has been since the initial",
        "% skeleton commit), so every macro below is live. Nothing uses them yet:",
        "% the chapters carry their figures as literals, which keeps the .tex",
        "% readable and diffable, and the macros exist so that --check has",
        "% something canonical to compare those literals against.",
        "%",
        "% Because they are live, a new entry whose key collides with an existing",
        "% command would be a fatal \\newcommand error rather than a harmless",
        "% shadow. Keys are currently clash-free; keep the \\the... and \\text...",
        "% prefixes out of them and it stays that way.",
        "",
    ]
    for n in nums:
        lines.append(f"% {n.note}")
        lines.append(f"\\newcommand{{\\{n.key}}}{{{n.value}}}")
    SNIPPETS.parent.mkdir(parents=True, exist_ok=True)
    SNIPPETS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {SNIPPETS.relative_to(ROOT)} ({len(nums)} figures)")


def check(nums: list[Num]) -> int:
    # Whitespace is collapsed on both sides: a multi-word literal would
    # otherwise miss whenever LaTeX line-wrapping happened to fall inside it.
    def flat(s: str) -> str:
        return re.sub(r"\s+", " ", s)

    text = {p.name: flat(p.read_text(encoding="utf-8"))
            for p in CHAPTERS if p.exists()}
    joined = "\n".join(text.values())
    problems = 0

    for n in nums:
        for bad in map(flat, n.stale):
            hits = [f for f, t in text.items() if bad in t]
            if hits:
                problems += 1
                print(f"STALE  \\{n.key}: superseded value {bad!r} still in "
                      f"{', '.join(hits)} (current: {n.value})")
        # A chapter that carries the figure as \Key rather than as a literal
        # (the August rewrite converted most of them) also satisfies the check.
        if n.expect and not any(flat(e) in joined for e in n.expect) \
                and f"\\{n.key}" not in joined:
            print(f"absent \\{n.key}: {n.expect[0]!r} appears in no chapter "
                  f"-- {n.note}")

    if problems == 0:
        print(f"no stale figures across {len(text)} chapters "
              f"({len(nums)} canonical values checked)")
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="scan chapters for drift; do not write")
    args = ap.parse_args()

    nums = build()
    if args.check:
        return check(nums)
    write(nums)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
