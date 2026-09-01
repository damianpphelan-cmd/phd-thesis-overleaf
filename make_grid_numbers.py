#!/usr/bin/env python3
"""Producer: the Chapter 2 grid table and every grid/prediction macro.

Reads rubric_grid_analysis.csv, the two rubric score files, the retest file,
text_spine.csv, analysis_dataset.csv (controls), the LOO-prediction files,
grid_perm_pvalues.csv (single-source permutation nulls, grid_perm_analysis.py)
and the text corpus; writes snippets/grid_numbers.tex (macros) and
tables/tab_p1_grid.tex (the grid).
Registered in check_pipeline.py stage-5 like every producer.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GRID = ROOT / "rubric_grid_analysis.csv"
PRED = ROOT / "text_prediction_results_r2_minilm.csv"
LOO = ROOT / "text_prediction_loo_preds_r2_minilm.csv"
PRIM = ROOT / "rubric_grid_scores_gpt-4o-mini.csv"
SENS = ROOT / "rubric_grid_scores_gpt-4o.csv"
RET = ROOT / "rubric_grid_scores_gpt-4o-mini_retest.csv"
GRIDP = ROOT / "grid_perm_pvalues.csv"
# The school's own documents (behaviour policy + website) pooled, from
# text_prediction_ownvoice.py. The frozen harness has no such block: its
# "combined" pools all three sources, inspection report included, which
# cannot support a claim about what schools write about themselves.
OWN_ESP = ROOT / "text_prediction_ownvoice_minilm.csv"
OWN_ENA = ROOT / "text_prediction_ownvoice_enacted_minilm.csv"
N_PERM = 200  # draws behind grid_perm_pvalues.csv; floor p = 1/(N_PERM+1)
SPINE = ROOT / "text_spine.csv"
LENGTHS = ROOT / "grid_doc_lengths.csv"
DATASET = ROOT / "analysis_dataset.csv"
CORPUS = ROOT / "text_corpus_r2"

CONTROLS = ["fsm", "eal", "ks2", "years_since_ofsted"]
VISIT_COL = {"warmth": "gs_warmth_enacted",
             "strictness": "gs_strictness_enacted",
             "teaching": "gs_teaching_enacted"}


def f3(x):
    return ("+" if x >= 0 else "") + f"{x:.2f}"


def pct(x):
    return f"{x:.0%}".replace("%", "\\%")


def corr(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    j = pd.concat([a, b], axis=1).dropna()
    if len(j) < 5 or j.iloc[:, 0].std() < 1e-9 or j.iloc[:, 1].std() < 1e-9:
        return float("nan"), len(j)
    return float(np.corrcoef(j.iloc[:, 0], j.iloc[:, 1])[0, 1]), len(j)


def deconf_target(y: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Residualise y on the controls (same as analyse_rubric_grid.py)."""
    m = ~np.isnan(y) & ~np.isnan(C).any(axis=1)
    A = np.column_stack([np.ones(int(m.sum())), C[m]])
    beta, *_ = np.linalg.lstsq(A, y[m], rcond=None)
    out = np.full(len(y), np.nan)
    out[m] = y[m] - A @ beta
    return out


def fisher_ci(r: float, n: int) -> tuple[float, float]:
    z = math.atanh(r)
    h = 1.96 / math.sqrt(n - 3)
    return math.tanh(z - h), math.tanh(z + h)


def steiger_z(r12: float, r13: float, r23: float, n: int) -> tuple[float, float]:
    """Steiger (1980) z for two dependent correlations sharing variable 1.

    r12 = r(criterion, A), r13 = r(criterion, B), r23 = r(A, B).
    Positive z means r12 > r13. Returns (z, two-sided p)."""
    rbar = (r12 + r13) / 2.0
    psi = (r23 * (1 - 2 * rbar ** 2)
           - 0.5 * rbar ** 2 * (1 - 2 * rbar ** 2 - r23 ** 2))
    c = psi / (1 - rbar ** 2) ** 2
    z = (math.atanh(r12) - math.atanh(r13)) * math.sqrt((n - 3) / (2 - 2 * c))
    p = math.erfc(abs(z) / math.sqrt(2))
    return z, p


def fmt_p(p: float) -> str:
    if not pd.notna(p):
        return "--"
    return "$<$.001" if p < 0.001 else f"{p:.3f}"


# the results files store perm_p rounded to 4 dp, so the attainable floor
# 1/201 arrives as 0.005 exactly
PERM_FLOOR = round(1.0 / (N_PERM + 1), 4) + 1e-9


def fmt_perm(p: float) -> str:
    """Table cell for a 200-draw permutation p (floor 1/201)."""
    if not pd.notna(p):
        return "--"
    return "$<$0.005" if p <= PERM_FLOOR else f"{p:.3f}"


def fmt_perm_macro(p: float) -> str:
    """Prose macro for a 200-draw permutation p."""
    if p <= PERM_FLOOR:
        return "$p<0.005$"
    return f"$p={p:.2f}$" if p >= 0.095 else f"$p={p:.3f}$"


def fmt_ci(lo: float, hi: float) -> str:
    return f"[{f3(lo)}, {f3(hi)}]"


def main() -> None:
    g = pd.read_csv(GRID).set_index(["source", "dimension"])
    p = pd.read_csv(PRED)
    nat = p[(p["leg"] == "deconf") & p["sample"].isin(["espoused", "enacted"])
            & (p["arm"] == "tfidf")]

    def pcell(block, target, col="loo_r"):
        s = nat[(nat["block"] == block) & (nat["target"] == target)]
        v = s[col].iloc[0]
        return float(v) if pd.notna(v) else float("nan")

    def pp(target):
        s = nat[(nat["block"] == "combined") & (nat["target"] == target)]
        return float(s["perm_p"].iloc[0])

    # single-source permutation nulls (grid_perm_analysis.py, 200 draws,
    # identical pipeline — each loo_r asserted against the results file there)
    gp = pd.read_csv(GRIDP).set_index(["source", "target"])
    for (src, tgt), row in gp.iterrows():
        assert abs(row["loo_r"] - pcell(src, tgt)) <= 1e-9, \
            f"grid_perm_pvalues.csv drifted from results file: {src}/{tgt}"

    def perm_cell(source, target):
        return float(gp.loc[(source, target), "perm_p"])

    a = pd.read_csv(PRIM)
    b = pd.read_csv(RET)
    j = a.merge(b, on=["urn", "source", "dimension"], suffixes=("_1", "_2"))
    retest_all = (j["band_1"] == j["band_2"]).mean()

    # ---- spine + controls, rubric deconfounded correlations recomputed ----
    spine = pd.read_csv(SPINE)
    spine["urn"] = spine["urn"].astype(int)
    yv = spine.set_index("urn")
    ds = pd.read_csv(DATASET, low_memory=False)
    ds["urn"] = pd.to_numeric(ds["urn"], errors="coerce").astype("Int64")
    ds = ds.dropna(subset=["urn"]).set_index("urn")
    ctrl = pd.DataFrame(index=ds.index)
    for c in CONTROLS:
        ctrl[c] = pd.to_numeric(ds[c].astype(str).str.rstrip("%"),
                                errors="coerce")

    sens = pd.read_csv(SENS)

    cells = {}  # (source, dim) -> dict with r_dec, n_dec, ci, band series
    for (src, dim), grp in a.groupby(["source", "dimension"]):
        if dim not in VISIT_COL:
            continue
        s = grp.set_index("urn")["band"].astype(float)
        urns = np.array(sorted(set(s.index) & set(yv.index)))
        y = yv.loc[urns, VISIT_COL[dim]].astype(float)
        C = ctrl.reindex(urns).to_numpy(float)
        ydec = pd.Series(deconf_target(y.to_numpy(float), C), index=urns)
        r_dec, n_dec = corr(s.reindex(urns), ydec)
        lo, hi = fisher_ci(r_dec, n_dec)
        cells[(src, dim)] = {"band": s, "ydec": ydec, "r_dec": r_dec,
                             "n_dec": n_dec, "ci": (lo, hi)}
        rec = round(g.loc[(src, dim), "rubric_deconf"], 3)
        if abs(round(r_dec, 3) - rec) > 0.0015:
            print(f"WARNING: recomputed deconf r for {src}/{dim} = "
                  f"{r_dec:.3f} != recorded {rec}")

    ns = {c["n_dec"] for c in cells.values()}
    assert len(ns) == 1, f"cell families disagree on n: {ns}"
    n_cell = ns.pop()

    # ---- gpt-4o rubric vs visit score, raw (Ofsted dimensions) ----
    fouro = {}
    for dim in ("strictness", "warmth", "teaching"):
        s4 = sens[(sens["source"] == "ofsted")
                  & (sens["dimension"] == dim)].set_index("urn")["band"]
        urns = np.array(sorted(set(s4.index) & set(yv.index)))
        r, _ = corr(s4.reindex(urns).astype(float),
                    yv.loc[urns, VISIT_COL[dim]].astype(float))
        fouro[dim] = r

    # ---- document lengths (words + chars) from the scored corpus ----
    # The scheme read text_corpus_r2/<source>/<urn>.txt verbatim
    # (score_rubric_grid.py), so word counts of those files ARE the lengths
    # the bands could be confounded by. Persisted to grid_doc_lengths.csv so
    # the numbers are reproducible even without the untracked corpus.
    len_rows = []
    for src in ("ofsted", "bp", "web"):
        d = CORPUS / src
        for u in a[a["source"] == src]["urn"].unique():
            f = d / f"{u}.txt"
            if f.exists():
                t = f.read_text(encoding="utf-8", errors="replace")
                len_rows.append({"source": src, "urn": int(u),
                                 "words": len(t.split()), "chars": len(t)})
    if len_rows:
        ldf = pd.DataFrame(len_rows).sort_values(["source", "urn"])
        ldf.to_csv(LENGTHS, index=False)
    else:  # corpus not on this machine: fall back to the persisted file
        ldf = pd.read_csv(LENGTHS)
    lengths = {}   # source -> Series urn -> log char length (legacy macros)
    wlengths = {}  # source -> Series urn -> log word count (partialling)
    for src in ("ofsted", "bp", "web"):
        s = ldf[ldf["source"] == src].set_index("urn")
        lengths[src] = np.log(s["chars"].clip(lower=1).astype(float))
        wlengths[src] = np.log(s["words"].clip(lower=1).astype(float))
    lencorr = {}
    for (src, dim), c in cells.items():
        r, _ = corr(c["band"], lengths[src])
        lencorr[(src, dim)] = r

    # ---- length-partialled scheme correlations ----
    # Partial r of band with the deconfounded visit score, controlling for
    # log word count of the document the scheme read (referee point: the
    # Ofsted strictness scheme's band-length correlation matches its
    # validity, so length must be partialled, not just disclosed).
    def partial_r(x: pd.Series, y: pd.Series, z: pd.Series
                  ) -> tuple[float, int]:
        j = pd.concat([x, y, z], axis=1).dropna()
        if len(j) < 5:
            return float("nan"), len(j)
        A = np.column_stack([np.ones(len(j)), j.iloc[:, 2].to_numpy(float)])
        rx = j.iloc[:, 0].to_numpy(float)
        ry = j.iloc[:, 1].to_numpy(float)
        bx, *_ = np.linalg.lstsq(A, rx, rcond=None)
        by, *_ = np.linalg.lstsq(A, ry, rcond=None)
        return float(np.corrcoef(rx - A @ bx, ry - A @ by)[0, 1]), len(j)

    print("scheme cells: raw deconf r vs length-partialled r")
    for (src, dim), c in cells.items():
        rp, n_p = partial_r(c["band"], c["ydec"], wlengths[src])
        c["r_lenp"], c["n_lenp"] = rp, n_p
        print(f"  {src:6s} {dim:10s} raw {c['r_dec']:+.3f}  "
              f"len-partialled {rp:+.3f}  (n={n_p})")

    # ---- dependent-correlation difference tests (Steiger) ----
    loo = pd.read_csv(LOO)
    loo_dec = loo[(loo["arm"] == "tfidf") & (loo["sample"] == "enacted")
                  & (loo["leg"] == "deconf") & (loo["block"] == "ofsted")]

    def diff_test(dim):
        cell = loo_dec[loo_dec["target"] == f"enacted_{dim}"].set_index("urn")
        band = cells[("ofsted", dim)]["band"]
        common = sorted(set(cell.index) & set(band.index))
        ycrit = cell.loc[common, "y"].astype(float)      # deconf enacted score
        pred = cell.loc[common, "pred"].astype(float)    # model LOO prediction
        bnd = band.reindex(common)
        r12, n = corr(ycrit, bnd)     # rubric vs criterion
        r13, _ = corr(ycrit, pred)    # model vs criterion
        r23, _ = corr(bnd, pred)      # rubric vs model
        z, pv = steiger_z(r12, r13, r23, n)
        return z, pv, r12, r13, r23, n

    sz, sp, *_ = diff_test("strictness")
    wz, wp, *_ = diff_test("warmth")

    # ---- multiplicity: BH q-values across the 14 grid tests ----
    # Family = the 7 model cells (200-draw permutation p's) + the 7 scheme
    # cells (two-sided Fisher-z p's on the deconfounded correlations).
    def fisher_p(r: float, n: int) -> float:
        z = math.atanh(r) * math.sqrt(n - 3)
        return math.erfc(abs(z) / math.sqrt(2))

    tmap_all = {"warmth": "enacted_warmth", "strictness": "enacted_strictness",
                "teaching": "enacted_teaching"}
    tests = []  # (label, p)
    for (src, dim), c in cells.items():
        tests.append((f"model_{src}_{dim}",
                      float(gp.loc[(src, tmap_all[dim]), "perm_p"])))
        tests.append((f"scheme_{src}_{dim}",
                      fisher_p(c["r_dec"], c["n_dec"])))

    def bh_q(pvals: list[float]) -> list[float]:
        m_ = len(pvals)
        order = sorted(range(m_), key=lambda i: pvals[i])
        q = [0.0] * m_
        prev = 1.0
        for rank_from_top, i in enumerate(reversed(order)):
            rank = m_ - rank_from_top
            prev = min(prev, pvals[i] * m_ / rank)
            q[i] = prev
        return q

    qvals = dict(zip([t[0] for t in tests], bh_q([t[1] for t in tests])))
    survivors = sorted(k for k, v in qvals.items() if v < 0.05)
    print("BH q-values over the 14 grid tests (q<0.05 starred):")
    for (lab, pv_) in sorted(tests, key=lambda t: t[1]):
        star = " *" if qvals[lab] < 0.05 else ""
        print(f"  {lab:26s} p={pv_:.4f}  q={qvals[lab]:.4f}{star}")

    # ---- raw-leg warmth model correlation, recomputed from LOO preds ----
    raw_w = loo[(loo["arm"] == "tfidf") & (loo["sample"] == "enacted")
                & (loo["leg"] == "raw") & (loo["block"] == "ofsted")
                & (loo["target"] == "enacted_warmth")]
    r_raw_w, _ = corr(raw_w.set_index("urn")["y"].astype(float),
                      raw_w.set_index("urn")["pred"].astype(float))

    def own(path, target):
        d = pd.read_csv(path)
        d = d[(d['arm'] == 'tfidf') & (d['leg'] == 'deconf')
              & (d['target'] == target)]
        assert len(d) == 1, f'own cell {target} x{len(d)}'
        return float(d['loo_r'].iloc[0])

    m = {
        "PredWOfsted": f3(pcell("ofsted", "enacted_warmth")),
        "PredTOfsted": f3(pcell("ofsted", "enacted_teaching")),
        "PredSOfsted": f3(pcell("ofsted", "enacted_strictness")),
        "PredWCombined": f3(pcell("combined", "enacted_warmth")),
        "PredWCombinedP": f"{pp('enacted_warmth'):.3f}",
        # espoused: the school's own documents, not all three sources
        "PredEspS": f3(own(OWN_ESP, "espoused_strictness")),
        "PredEspClim": f3(own(OWN_ESP, "espoused_staff_climate")),
        "PredEspW": f3(own(OWN_ESP, "espoused_warmth")),
        # the same two documents pooled, against the visit scores
        "PredBPWebW": f3(own(OWN_ENA, "enacted_warmth")),
        "PredBPWebS": f3(own(OWN_ENA, "enacted_strictness")),
        "PredBPWebT": f3(own(OWN_ENA, "enacted_teaching")),
        "PredSWeb": f3(pcell("web", "enacted_strictness")),
        "PredTCombined": f3(pcell("combined", "enacted_teaching")),
        # two language models applying the same scheme: exact band
        # agreement, used where the schemes' reliability is discussed
        "AgreeWebW": pct(g.loc[("web", "warmth"), "sens_exact"]),
        "AgreeWebS": pct(g.loc[("web", "strictness"), "sens_exact"]),
        "AgreeOfstedW": pct(g.loc[("ofsted", "warmth"), "sens_exact"]),
        "AgreeOfstedT": pct(g.loc[("ofsted", "teaching"), "sens_exact"]),
        "RubricSOfstedRaw": f3(g.loc[("ofsted", "strictness"), "rubric_raw"]),
        "RubricSOfstedDec": f3(g.loc[("ofsted", "strictness"), "rubric_deconf"]),
        "RubricWOfstedDec": f3(g.loc[("ofsted", "warmth"), "rubric_deconf"]),
        "RubricTOfstedDec": f3(g.loc[("ofsted", "teaching"), "rubric_deconf"]),
        "GridRetestExact": f"{retest_all:.0%}".replace("%", "\\%"),
        "RubricSSensAgree": f"{g.loc[('ofsted','strictness'),'sens_exact']:.0%}".replace("%", "\\%"),
        # gpt-4o rubric vs visit score, raw
        "RubricSFourO": f3(fouro["strictness"]),
        "RubricWFourO": f3(fouro["warmth"]),
        "RubricTFourO": f3(fouro["teaching"]),
        # band vs log document length (primary model)
        "LenOfstedS": f3(lencorr[("ofsted", "strictness")]),
        "LenOfstedW": f3(lencorr[("ofsted", "warmth")]),
        "LenOfstedT": f3(lencorr[("ofsted", "teaching")]),
        "LenBPS": f3(lencorr[("bp", "strictness")]),
        "LenBPW": f3(lencorr[("bp", "warmth")]),
        "LenWebS": f3(lencorr[("web", "strictness")]),
        "LenWebW": f3(lencorr[("web", "warmth")]),
        # length-partialled scheme correlations (log word count partialled
        # out of both band and deconfounded target)
        "RubricWOfstedLenP": f3(cells[("ofsted", "warmth")]["r_lenp"]),
        "RubricSOfstedLenP": f3(cells[("ofsted", "strictness")]["r_lenp"]),
        "RubricTOfstedLenP": f3(cells[("ofsted", "teaching")]["r_lenp"]),
        "RubricWBPLenP": f3(cells[("bp", "warmth")]["r_lenp"]),
        "RubricSBPLenP": f3(cells[("bp", "strictness")]["r_lenp"]),
        "RubricWWebLenP": f3(cells[("web", "warmth")]["r_lenp"]),
        "RubricSWebLenP": f3(cells[("web", "strictness")]["r_lenp"]),
        # BH q-value for the Ofsted strictness scheme cell (14-test family)
        "QGridSOfsted": f"{qvals['scheme_ofsted_strictness']:.3f}",
        # Steiger dependent-correlation difference tests (Ofsted cells)
        "StrictDiffZ": f"{sz:.2f}",
        "StrictDiffP": fmt_p(sp),
        "WarmDiffZ": f"{wz:.2f}",
        "WarmDiffP": fmt_p(wp),
        # raw (non-deconfounded) Ofsted warmth model correlation
        "PredWOfstedRaw": f3(r_raw_w),
        # single-source permutation p-values (200 draws, grid_perm_analysis.py)
        "PermPOfstedW": fmt_perm_macro(perm_cell("ofsted", "enacted_warmth")),
        "PermPOfstedS": fmt_perm_macro(
            perm_cell("ofsted", "enacted_strictness")),
        "PermPOfstedT": fmt_perm_macro(perm_cell("ofsted", "enacted_teaching")),
        # Fisher-z 95% CIs for the model-cell correlations
        "CIPredWOfsted": fmt_ci(*fisher_ci(pcell("ofsted", "enacted_warmth"),
                                           n_cell)),
        "CIPredSOfsted": fmt_ci(*fisher_ci(
            pcell("ofsted", "enacted_strictness"), n_cell)),
        "CIPredTOfsted": fmt_ci(*fisher_ci(pcell("ofsted", "enacted_teaching"),
                                           n_cell)),
        "CIPredWBP": fmt_ci(*fisher_ci(pcell("bp", "enacted_warmth"), n_cell)),
        "CIPredSBP": fmt_ci(*fisher_ci(pcell("bp", "enacted_strictness"),
                                       n_cell)),
        "CIPredWWeb": fmt_ci(*fisher_ci(pcell("web", "enacted_warmth"),
                                        n_cell)),
        "CIPredSWeb": fmt_ci(*fisher_ci(pcell("web", "enacted_strictness"),
                                        n_cell)),
        "CIPredWCombined": fmt_ci(*fisher_ci(
            pcell("combined", "enacted_warmth"), n_cell)),
    }
    lines = ["% generated by make_grid_numbers.py — do not edit"]
    for k, v in m.items():
        lines.append(f"\\newcommand{{\\{k}}}{{{v}}}")
    (HERE / "snippets" / "grid_numbers.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    # notes sentences: length-partialled headline cells, BH survivors
    lenp_note = (
        f"{f3(cells[('ofsted','warmth')]['r_lenp'])} (inspection warmth), "
        f"{f3(cells[('ofsted','strictness')]['r_lenp'])} (inspection "
        "strictness), "
        f"{f3(cells[('ofsted','teaching')]['r_lenp'])} (inspection teaching), "
        f"{f3(cells[('bp','warmth')]['r_lenp'])} (policy warmth), "
        f"{f3(cells[('bp','strictness')]['r_lenp'])} (policy "
        "strictness), "
        f"{f3(cells[('web','warmth')]['r_lenp'])} (website warmth) and "
        f"{f3(cells[('web','strictness')]['r_lenp'])} (website strictness)")
    cell_name = {"ofsted": "inspection", "bp": "policy", "web": "website"}

    def surv_name(lab: str) -> str:
        kind, src, dim = lab.split("_")
        return f"the {cell_name[src]} {dim} {kind} cell"

    _sn = [surv_name(s) for s in survivors]
    surv_note = ((", ".join(_sn[:-1]) + " and " + _sn[-1])
                 if len(_sn) > 1 else (_sn[0] if _sn else "no cell"))

    rows = []
    order = [("ofsted", "warmth"), ("ofsted", "strictness"),
             ("ofsted", "teaching"), ("bp", "warmth"), ("bp", "strictness"),
             ("web", "warmth"), ("web", "strictness")]
    src_name = {"ofsted": "Inspection report", "bp": "Behaviour policy",
                "web": "Website"}
    tmap = {"warmth": "enacted_warmth", "strictness": "enacted_strictness",
            "teaching": "enacted_teaching"}
    for s, d in order:
        r = g.loc[(s, d)]
        model = pcell(s, tmap[d])
        mlo, mhi = fisher_ci(model, n_cell)
        permp = perm_cell(s, tmap[d])
        c = cells[(s, d)]
        lo, hi = c["ci"]
        rows.append(
            f"{src_name[s]} & {d.capitalize()} & {f3(model)} & "
            f"{fmt_ci(mlo, mhi)} & {fmt_perm(permp)} & "
            f"{f3(c['r_dec'])} & {fmt_ci(lo, hi)} & "
            f"{r['sens_exact']:.0%} & {r['retest_exact']:.0%} \\\\"
            .replace("%", "\\%"))
    table = r"""% generated by make_grid_numbers.py — do not edit
\begin{table}[htbp]
\centering
\small\setlength{\tabcolsep}{4pt}
\begin{tabular}{llccccccc}
\toprule
Source & Dimension & Model & 95\% CI & $p$ & Scheme & 95\% CI & Agree & Retest \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{What each public text carries about enacted culture}
\label{tab:p1_grid}
\begin{minipage}{\linewidth}
\smallskip
\footnotesize\textit{Notes:} Cells are correlations with the visit scores on
the visited schools ($n = """ + str(n_cell) + r"""$ in every cell: 101 scored
documents, one school lost to a missing control), with intake and report age
partialled out of the target. ``$p$'' is the model's permutation $p$-value
from 200 target-scrambled draws through the identical pipeline (floor
$1/201$, shown as $<$0.005). Each bracketed interval is a Fisher-$z$ 95\%
confidence interval for the correlation to its left (model and marking
scheme respectively). ``Agree'' is exact band agreement between the two
language models applying the same mark scheme; ``Retest'' is exact
agreement on thirty documents re-scored by the primary model.
\end{minipage}
\end{table}
"""
    (HERE / "tables" / "tab_p1_grid.tex").write_text(table, encoding="utf-8")
    print(f"wrote grid_numbers.tex ({len(m)} macros) and tab_p1_grid.tex")
    print(f"cell n = {n_cell}")
    print(f"Steiger strictness: z={sz:.3f} p={sp:.4f}")
    print(f"Steiger warmth:     z={wz:.3f} p={wp:.4f}")


if __name__ == "__main__":
    main()
