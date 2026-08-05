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
CHAPTERS = [THESIS / "chapters" / "02_paper1.tex",
            THESIS / "chapters" / "03_paper2.tex"]


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
    # strictness in the same lesson, so it contains halo. The visit decomposition
    # (three independent observer blocks, 351 lessons) puts the disattenuated
    # cross-observer true-score correlation at +0.290. Quote this figure as the
    # observed school-level association and that one as the trait correlation; do
    # not present this as evidence that the two constructs are barely separable.
    add(Num("CorrWarmthStrictnessEnacted", f"{r_ws_en:.3f}",
            f"observed W-S correlation, Tier 1, n={n_ws_en}; contains halo — "
            f"cross-observer true-score r is +0.290",
            stale=["0.494"]))
    add(Num("CorrWarmthStrictnessEspoused", f"{r_ws_es:.3f}",
            f"interview W-S correlation, all interviewed schools, n={n_ws_es}"))
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
    ridge("RidgeBWarmth", "B", "Warmth", "Model B LOO-CV r, warmth",
          stale=["-0.018"])
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

    r_tc, _ = corr("ofsted_LLMTeachingScore", "gs_teaching_espoused")
    r_tv, _ = corr("ofsted_LLMTeachingScore", "gs_teaching_enacted")
    r_tx, _ = corr("trx_teaching", "gs_teaching_espoused")

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
    # These three figures are also the empirical case for abolishing the composite:
    # a 0.6/0.4 average of two measures agreeing at r = 0.18-0.24 is not a better
    # measure of either.
    for dim in ("Warmth", "Strictness", "Teaching"):
        d = full[[f"gs_{dim.lower()}_espoused", f"gs_{dim.lower()}_enacted"]].apply(
            pd.to_numeric, errors="coerce").dropna()
        r_ee, p_ee = stats.pearsonr(d.iloc[:, 0], d.iloc[:, 1])
        add(Num(f"Gold{dim}Split", f"{r_ee:.3f}",
                f"gold {dim.lower()}: espoused vs enacted, "
                f"n={len(d)}, p={p_ee:.3f}",
                expect=[f"$r = {r_ee:.3f}$"]))

    # Renamed 5 Aug 2026 with the composite. Nothing in the chapters referenced the old
    # macros yet, so this is a free rename; the values move as well as the names.
    add(Num("OfstedTeachingEspoused", f"{r_tc:.3f}",
            "Ofsted teaching vs ESPOUSED gold teaching, full-data tier",
            stale=["$r = 0.133$", "$r > 0.30$ validation gate",
                   "did not satisfy the"]))
    add(Num("OfstedTeachingEnacted", f"{r_tv:.3f}",
            "Ofsted teaching vs ENACTED gold teaching (the observed lessons)"))
    add(Num("TrxTeachingEspoused", f"{r_tx:.3f}",
            "interview-transcript teaching vs ESPOUSED gold teaching"))

    # ── Teaching philosophy (v3 classification) ──────────────────────────────
    add(Num("NTraditional", str(ph.get("traditional", 0)),
            "website teaching philosophy v3, full corpus", stale=["472"]))
    add(Num("NProgressive", str(ph.get("progressive", 0)),
            "website teaching philosophy v3, full corpus", stale=["179"]))
    # The chapters quote the estimation-sample count (3,037), not the corpus
    # count, so there is no literal to search for here.
    add(Num("NUnmarked", comma(int(ph.get("unmarked", 0))),
            "website teaching philosophy v3, full corpus", expect=[]))

    # ── Chapter 3 estimates (source: chapter3_analysis.ipynb) ────────────────
    add(Num("NEstimation", "95", "notebook: Stage 1-3 estimation sample"))
    add(Num("NNationalStrictness", comma(3148),
            "notebook: national extension sample", stale=["3{,}194"]))
    add(Num("BetaWarmth", "0.127", "notebook: Stage 1 overall P8"))
    add(Num("BetaStrictness", "0.120", "notebook: Stage 1 overall P8"))
    add(Num("BetaNationalStrictness", "0.135",
            "notebook: national extension, overall P8"))
    # No stale literal for this one: the superseded v2 value was 0.039, but a
    # bare three-digit decimal collides with unrelated coefficients elsewhere
    # (e.g. the management-discourse range runs to $-0.039$). The v2/v3 split is
    # caught upstream instead, by NTraditional/NProgressive.
    add(Num("BetaTraditional", "0.125", "notebook: teaching philosophy v3"))
    add(Num("SelfReportReduction", "63--106",
            "notebook: self-report coefficient reduction, per cent",
            stale=["63--91"]))

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
        if n.expect and not any(flat(e) in joined for e in n.expect):
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
