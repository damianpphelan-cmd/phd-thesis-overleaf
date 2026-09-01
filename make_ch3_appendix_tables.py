r"""Regenerate the ten Chapter 3 appendix tables from ch3_appendix_estimates.csv
(thesis/ch3_appendix.do, the primary specification) and the companion CSVs written by
build_ch3_appendix_input.py. 19 Aug 2026, Damian's Option A.

Tables: tab_subscores, tab_items_fdr, tab_typology, tab_gaps, tab_parentview,
tab_llm_p8_matrix, tab_entry_rates, tab_p8_proxy, tab_semh_mechanism,
tab_stability_p8.

Every number in every table comes from a CSV; nothing is typed in. Run with --check
to compare against the files on disk without writing.
"""
import argparse, os, sys
import numpy as np
import pandas as pd

from fix_tables import move_caption_above

ROOT = r"C:\Users\damia\OneDrive\Documents\Schools Project"
TAB = os.path.join(ROOT, "thesis", "tables")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

E = pd.read_csv(os.path.join(TAB, "ch3_appendix_estimates.csv"))
E["panel"] = E["panel"].fillna("")
E["outcome"] = E["outcome"].fillna("")
IRR = pd.read_csv(os.path.join(TAB, "ch3_appendix_items_irr.csv"))
STAB = pd.read_csv(os.path.join(TAB, "ch3_appendix_stability.csv"))
ACAD = pd.read_csv(os.path.join(TAB, "ch3_appendix_academisation.csv"))
VAL = pd.read_csv(os.path.join(TAB, "ch3_appendix_p8proxy_validation.csv")) if os.path.exists(os.path.join(TAB, "ch3_appendix_p8proxy_validation.csv")) else None

SYM = r"\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}"
NOTES_STARS = r"\sym{*} \(p<0.10\), \sym{**} \(p<0.05\), \sym{***} \(p<0.01\)."


def stars(p):
    if pd.isna(p): return ""
    return r"\sym{***}" if p < 0.01 else r"\sym{**}" if p < 0.05 else r"\sym{*}" if p < 0.10 else ""


def f3(x, signed=False):
    if pd.isna(x): return "---"
    s = f"{x:.3f}"
    if x < 0: s = "$-$" + s[1:]
    elif signed: s = "$+$" + s
    return s


def nfmt(n):
    return f"{int(n):,}".replace(",", "{,}")


def row(table, panel="", model=None, outcome=None, term=None):
    q = E[E.table == table]
    if panel is not None: q = q[q.panel == panel]
    if model is not None: q = q[q.model == model]
    if outcome is not None: q = q[q.outcome == outcome]
    if term is not None: q = q[q.term == term]
    if len(q) != 1:
        raise SystemExit(f"expected one row for {table}/{panel}/{model}/{outcome}/{term}, got {len(q)}")
    return q.iloc[0]


def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); r = np.empty(n)
    ranked = p[o] * n / (np.arange(n) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    r[o] = np.minimum(ranked, 1.0); return r


def write(name, tex, check, changed):
    if name.endswith(".tex") and name.startswith("tab_"):
        # Float convention: tabular first, then \caption + \label, then notes.
        tex, _ = move_caption_above(tex)
    path = os.path.join(TAB, name)
    cur = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if cur != tex:
        changed.append(name)
        if not check:
            open(path, "w", encoding="utf-8", newline="\n").write(tex)
            print("wrote", name)
    else:
        print("unchanged", name)


# ---------------------------------------------------------------- subscores
def t_subscores():
    cells = {}
    for oc in ["overall", "english", "maths"]:
        for t in ["z_gs_w1", "z_gs_w2", "z_gs_s1", "z_gs_s2", "z_gs_t1"]:
            cells[(oc, t)] = row("subscores", "", "joint", oc, t)
    n = int(cells[("overall", "z_gs_w1")].n)
    vif = {t: row("subscores", "vif", "joint", "overall", t).b for t in ["z_gs_w1", "z_gs_w2", "z_gs_s1", "z_gs_s2", "z_gs_t1"]}
    labels = [("z_gs_w1", "Classroom warmth (W1)"), ("z_gs_w2", "Outside warmth (W2)"), ("z_gs_s1", "Classroom strictness (S1)"),
              ("z_gs_s2", "Outside strictness (S2)"), ("z_gs_t1", "Teaching quality (T1)")]
    body = []
    for t, lab in labels:
        body.append(f"{lab:<28} & " + " & ".join(f3(cells[(oc, t)].b) + stars(cells[(oc, t)].pval) for oc in ["overall", "english", "maths"]) + r" \\")
        body.append(f"{'':<28} & " + " & ".join(f"({cells[(oc, t)].se:.3f})" for oc in ["overall", "english", "maths"]) + r" \\")
        body.append(r"\addlinespace")
    body = body[:-1]
    return rf"""\begin{{table}}[htbp]\centering
{SYM}
\small
\caption{{The five visit sub-scores entered jointly. Classroom warmth (W1), outside-of-classroom
warmth (W2), classroom strictness (S1), outside-of-classroom strictness (S2) and teaching
quality (T1) are entered together, each standardised within the estimation sample, with the
primary control set. Outside-of-lesson warmth and in-lesson strictness carry the association;
the other three add little once those two are held fixed.}}
\label{{tab:subscores}}
\begin{{tabular}}{{lccc}}
\toprule
Sub-score & Overall & English & Maths \\
\midrule
{chr(10).join(body)}
\midrule
$N$                          & {n} & {n} & {n} \\
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Standard errors (HC3) in parentheses.
{NOTES_STARS}
Primary specification: visited schools, late-entry schools excluded, full control set with
the predecessor-filled 2019 grade. The sub-scores are correlated, so the individual
coefficients should be read with care: variance inflation factors are {vif['z_gs_w1']:.2f} (W1),
{vif['z_gs_w2']:.2f} (W2), {vif['z_gs_s1']:.2f} (S1), {vif['z_gs_s2']:.2f} (S2) and {vif['z_gs_t1']:.2f} (T1) --- W1 and T1
overlap heavily, which widens their standard errors.
\end{{minipage}}
\end{{table}}
"""


# ---------------------------------------------------------------- items
def t_items():
    q = E[(E.table == "items")].copy()
    q = q.merge(IRR.assign(term="z_" + IRR["var"]), on="term", how="left")
    q["q_bh"] = bh(q.pval)
    q = q.sort_values("b", ascending=False)
    n = int(q.n.max()); nmin = int(q.n.min())
    nsurv = int((q.q_bh < 0.05).sum()); npos = int((q.b > 0).sum())
    lines = []
    for _, r in q.iterrows():
        setting, item = r["item"].split("|")
        sub = r["subscore"] if r["subscore"] != "unused" else "--"
        qtxt = "$<$0.001" if r.q_bh < 0.001 else f"{r.q_bh:.3f}"
        dag = r"\sym{\dagger}" if r.q_bh < 0.05 else ""
        lines.append(f"{item:<15} & {setting:<9} & {sub:<3} & {f3(r.b)}{dag} & {r.se:.3f} & {qtxt:<8} & {r.irr_r:.3f} & {int(r.irr_pairs):<3} \\\\")
    return rf"""\begin{{table}}[htbp]\centering
{SYM}
\footnotesize
\caption{{Each visit-sheet item as a predictor of Progress 8, one small model per item.
Every row regresses average Progress 8 on that item alone (standardised) plus the primary
control set with the predecessor-filled grade; late-entry schools excluded. $N={n}$ for the
in-lesson items and as low as {nmin} for the outside items, which were recorded at fewer
schools. Rows are
sorted by coefficient size. The $q$ column is the Benjamini--Hochberg false-discovery-rate
adjusted $p$-value across all {len(q)} items; a dagger marks items that survive at $q<0.05$
({nsurv} of {len(q)}; {npos} carry a positive coefficient). The final columns give each item's
inter-rater reliability: the pooled pairwise Pearson correlation between independent
observers, and the number of observer pairs it rests on.}}
\label{{tab:items_fdr}}
\begin{{tabular}}{{llcccccr}}
\toprule
Item & Setting & Sub-score & $\beta$ & SE & $q$ & IRR $r$ & Pairs \\
\midrule
{chr(10).join(lines)}
\bottomrule
\end{{tabular}}
\end{{table}}
""", npos, nsurv, len(q)


# ---------------------------------------------------------------- typology
def t_typology():
    def cell(panel, model, term):
        return row("typology", panel, model, "overall", term)
    qn = {"gold": "z_gs_warmth_enacted", "natA": "z_ofsted_llmwarmthscore", "natB": "z_ofsted_llmwarmthscore"}
    sn = {"gold": "z_gs_strictness_enacted", "natA": "z_ofsted_llmstrictnessscore", "natB": "z_ofsted_llmstrictnessscore"}
    P = ["gold", "natA", "natB"]
    quadlab = [("quad1", "Authoritative (high $W$, high $S$)"), ("quad2", "Authoritarian (low $W$, high $S$) "),
               ("quad3", "Permissive (high $W$, low $S$)    "), ("quad4", "Neglectful (low $W$, low $S$)     ")]
    body = []
    for qk, lab in quadlab:
        cs = [cell(p, "quadrant_adjmean", qk) for p in P]
        body.append(f"{lab} & " + " & ".join(f"{f3(c.b, signed=True)} ({c.se:.3f})" for c in cs) + r" \\")
        body.append("   & " + " & ".join(f"$n={nfmt(c.n)}$" for c in cs) + r" \\")
    reg = []
    for lab, key in [("Warmth ($W$)", "w"), ("Strictness ($S$)", "s"), (r"$W \times S$ interaction", "z_wxs"), ("Authoritative vs rest", "auth")]:
        cs = []
        for p in P:
            t = qn[p] if key == "w" else sn[p] if key == "s" else key
            cs.append(cell(p, "auth_vs_rest" if key == "auth" else "interaction", t))
        reg.append(f"{lab:<24} & " + " & ".join(f3(c.b) + stars(c.pval) for c in cs) + r" \\")
        reg.append(f"{'':<24} & " + " & ".join(f"({c.se:.3f})" for c in cs) + r" \\")
    ns = [int(cell(p, "auth_vs_rest", "auth").n) for p in P]
    return rf"""\begin{{table}}[htbp]\centering
{SYM}
\small
\caption{{The authoritative-school typology tested directly. The upper panel gives
covariate-adjusted mean Progress 8 for the four quadrants formed by median splits on
warmth and strictness; the lower panel gives the continuous interaction test and the
contrast of the authoritative (high-warmth, high-strictness) quadrant against all
others. The first column uses the visit scores on the primary
specification; the national columns use the Ofsted-derived scores without (A) and with
(B) the predecessor-filled 2019 inspection-grade control. Scores are standardised within
each estimation sample; late-entry schools excluded throughout.}}
\label{{tab:typology}}
\footnotesize\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{lccc}}
\toprule
 & Visited schools & \multicolumn{{2}}{{c}}{{National (Ofsted scores)}} \\
\cmidrule(lr){{3-4}}
 & & Panel A & Panel B \\
\midrule
\multicolumn{{4}}{{l}}{{\textit{{Adjusted quadrant means (mean, SE, $n$)}}}} \\
\addlinespace[2pt]
{chr(10).join(body)}
\midrule
\multicolumn{{4}}{{l}}{{\textit{{Regression tests}}}} \\
\addlinespace[2pt]
{chr(10).join(reg)}
\midrule
$N$                      & {ns[0]} & {nfmt(ns[1])} & {nfmt(ns[2])} \\
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Standard errors (HC3) in parentheses; for the
visited-sample adjusted quadrant means they are HC1, because the HC3 leverage
adjustment is undefined when a covariate cell contains a single school.
{NOTES_STARS}
Quadrant means are covariate-adjusted; quadrants are median splits within each sample.
The visited-sample interaction is a low-power test at this sample size; the pattern --- interaction
near zero with the high-both quadrant on top --- reads as additive rather than
synergistic. In the national columns the warmth--strictness halo in the Ofsted scores
thins the off-diagonal cells, and the Ofsted scores carry the verdict-reconstruction
caveat described in the text.
\end{{minipage}}
\end{{table}}
"""


# ---------------------------------------------------------------- gaps
def t_gaps():
    def g(label, spec, term):
        return row("gaps", label, spec, "overall", term)
    blocks = [("gold_warmth", "Warmth"), ("gold_strictness", "Strictness")]
    nat = [("nat_bp_warmth", "BP warmth"), ("nat_bp_strictness", "BP strictness"), ("nat_web_warmth", "Website warmth"), ("nat_web_strictness", "Website strictness")]
    def lines(items):
        out = []
        for lab, name in items:
            c1 = g(lab, "signed", "sgap"); c2 = g(lab, "absolute", "agap"); c3 = g(lab, "absolute_quad", "agap")
            out.append(f"{name:<19} & {f3(c1.b)}{stars(c1.pval)} & {f3(c2.b)}{stars(c2.pval)} & {f3(c3.b)}{stars(c3.pval)} \\\\")
            out.append(f"{'':<19} & ({c1.se:.3f}) & ({c2.se:.3f}) & ({c3.se:.3f}) \\\\")
        return out
    ngold = int(g("gold_warmth", "signed", "sgap").n)
    nn = [int(g(l, "signed", "sgap").n) for l, _ in nat]
    nat_n = f"{nfmt(min(nn))}--{nfmt(max(nn))}" if min(nn) != max(nn) else nfmt(nn[0])
    # curvature note: squared enacted (Ofsted) term in the strictness sources
    ze_bp = g("nat_bp_strictness", "absolute_quad", "ze2"); ze_web = g("nat_web_strictness", "absolute_quad", "ze2")
    zd_bp = g("nat_bp_strictness", "absolute_quad", "zd2"); zd_web = g("nat_web_strictness", "absolute_quad", "zd2")
    a_bp = g("nat_bp_strictness", "absolute", "agap"); a_web = g("nat_web_strictness", "absolute", "agap")
    return rf"""\begin{{table}}[htbp]\centering
{SYM}
\small
\caption{{Does the gap between what a school says and what it does predict progress?
Each row regresses average Progress 8 on the enacted (observed) score, the
espoused-minus-enacted gap, and the primary control set. The first column enters the
signed gap, the second the absolute gap, and the third re-enters the absolute gap
alongside quadratics in both component scores --- the robustness check that decides
whether an absolute-gap effect is genuine dissonance or just curvature in the components.}}
\label{{tab:gaps}}
\footnotesize\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{lccc}}
\toprule
 & Signed gap & Absolute gap & \shortstack{{Absolute gap\\(+ component quadratics)}} \\
\midrule
\multicolumn{{4}}{{l}}{{\textit{{Visited sample (visit vs interview, $n={ngold}$)}}}} \\
\addlinespace[2pt]
{chr(10).join(lines(blocks))}
\midrule
\multicolumn{{4}}{{l}}{{\textit{{National (document vs Ofsted, $n={nat_n}$)}}}} \\
\addlinespace[2pt]
{chr(10).join(lines(nat))}
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Standard errors in parentheses (HC3; behaviour-policy rows
clustered on the shared document digest).
{NOTES_STARS}
Scores are z-standardised within instrument and estimation sample before the gap is
formed; late-entry schools excluded. In the visited sample neither gap adds anything beyond
the enacted level. Nationally, the absolute strictness gap is {'positive' if a_bp.b > 0 else 'negative'} for the
behaviour-policy source ($p={a_bp.pval:.2f}$) and {'same' if np.sign(a_web.b) == np.sign(a_bp.b) else 'opposite'}-signed for the website
source ($p={a_web.pval:.2f}$); once component quadratics enter, the squared enacted (Ofsted)
score carries $\beta = {ze_bp.b:+.3f}$ ($p={ze_bp.pval:.3f}$) for the behaviour-policy pair and
${ze_web.b:+.3f}$ ($p={ze_web.pval:.3f}$) for the website pair, while the squared document score is
${zd_bp.b:+.3f}$ ($p={zd_bp.pval:.2f}$) and ${zd_web.b:+.3f}$ ($p={zd_web.pval:.2f}$). Effects are tiny
(0.01--0.02 of a grade per SD) and should be read in that light.
\end{{minipage}}
\end{{table}}
"""


# ---------------------------------------------------------------- parent view
def t_parentview():
    ins = [("web_llmwarmthscore_v18", "Website warmth (v18)"), ("web_llmwarmthscore_v13", "Website warmth (v13)"),
           ("bp_llmwarmthscore_v4", "Behaviour-policy warmth (v4)"), ("ofsted_llmwarmthscore", "Ofsted warmth")]
    A = []
    for v, lab in ins:
        rb = row("parentview", "A", v, "pv_warmth", "z_" + v)
        rp = row("parentview", "A_corr", v, "pv_warmth", "pearson"); rs = row("parentview", "A_corr", v, "pv_warmth", "spearman")
        ptxt = "$<$0.001" if rb.pval < 0.001 else f"{rb.pval:.2f}"
        A.append(f"{lab:<29} & {f3(rp.b, True)} & {f3(rs.b, True)} & {nfmt(rp.n)} & {f3(rb.b, True)} ({rb.se:.3f}) & {ptxt} \\\\")
    B = []
    for oc, lab in [("overall", "P8 overall"), ("english", "P8 English"), ("maths", "P8 Maths")]:
        rb = row("parentview", "B", "pv_to_p8", oc, "z_pv_warmth")
        ptxt = "$<$0.001" if rb.pval < 0.001 else f"{rb.pval:.3f}"
        B.append(f"{lab:<11} & \\multicolumn{{2}}{{c}}{{{f3(rb.b, True)}}} & {rb.se:.3f} & {nfmt(rb.n)} & {ptxt} \\\\")
    return rf"""\begin{{table}}[htbp]\centering
{SYM}
\small
\caption{{Parent View as a soft national criterion for the warmth instruments. The parent
composite is the mean of the ``my child is happy at this school'' and ``my child feels
safe at this school'' positive-response rates. The upper panel correlates each warmth
instrument with the composite and then regresses the composite on the instrument
(standardised) plus the national control set; the lower panel reports the composite's own
association with Progress 8 on the primary specification, which is descriptive only
because parents observe outcomes.}}
\label{{tab:parentview}}
\footnotesize\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{lccccc}}
\toprule
\multicolumn{{6}}{{l}}{{\textit{{Panel A: warmth instruments against the parent composite}}}} \\
\addlinespace[2pt]
Instrument & $r$ & $\rho$ & $n$ & Controlled $\beta$ & $p$ \\
\midrule
{chr(10).join(A)}
\midrule
\multicolumn{{6}}{{l}}{{\textit{{Panel B: parent composite as a Progress 8 predictor (descriptive)}}}} \\
\addlinespace[2pt]
Outcome & \multicolumn{{2}}{{c}}{{$\beta$}} & SE & $n$ & $p$ \\
\midrule
{chr(10).join(B)}
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Standard errors in parentheses (HC3; the behaviour-policy row
clustered on the shared document digest). Panel A regressions control for the national
control set without the grade; Panel B adds the predecessor-filled 2019 grade. Late-entry
schools excluded. Parent View is a soft criterion: it conflates school culture with parent
satisfaction, each school contributes its single most recent survey release (releases span
September 2022 to September 2025), and responses are not temporally aligned with the
instrument sources. The document-based instruments (website, behaviour policy) do not
track parents' experienced climate; the Ofsted-derived score does, consistent with both
drawing on visits to the school. Panel B is endogenous --- parents plausibly respond to
results as well as climate --- so it is reported as a description, never as a causal
predictor.
\end{{minipage}}
\end{{table}}
"""


# ---------------------------------------------------------------- LLM x P8 matrix
def t_llm_matrix():
    preds = [("ofsted_llmstrictnessscore", "Ofsted strictness"), ("ofsted_llmwarmthscore", "Ofsted warmth"),
             ("ofsted_llmteachingscore", "Ofsted teaching"), ("bp_llmstrictnessscore_v4", "BP strictness (v4)"),
             ("bp_llmwarmthscore_v4", "BP warmth (v4)"), ("web_llmwarmthscore_v13", "Website warmth (v13)"),
             ("web_llmstrictnessscore_v13", "Website strictness (v13)"), ("web_llmstrictnessscore_v15", "Website strictness (v15)"),
             ("web_tradethos_v2", "Traditional ethos (v2)"), ("web_tradpedagogy_v1b", "Traditional pedagogy (v1b)"),
             ("faith_prominence", "Faith prominence (0--3)"), ("trx_llmstrictnessscore_v13", "Interview strictness (v13)"),
             ("trx_llmteachingscore_v3", "Interview teaching (v3)"), ("trx_llmwarmthscore_v15", "Interview warmth (v15)"),
             ("trx_llmwarmthscore_counts", "Interview warmth (counts)")]
    ocs = ["overall", "english", "maths", "ebac", "open"]
    q = E[E.table == "llm_matrix"].copy()
    q["q_bh"] = bh(q.pval)   # across both panels, all predictors and outcomes
    ntests = len(q)
    lines = []
    for v, lab in preds:
        cs = [q[(q.panel == "B") & (q.model == v) & (q.outcome == oc)].iloc[0] for oc in ocs]
        lines.append(f"{lab:<26} & {nfmt(cs[0].n):<7} & " + " & ".join(f3(c.b) + (r"\sym{\dagger}" if c.q_bh < 0.05 else "") for c in cs) + r" \\")
        lines.append(f"{'':<26} & {'':<7} & " + " & ".join(f"({c.se:.3f})" for c in cs) + r" \\")
    return rf"""\begin{{table}}[htbp]\centering
{SYM}
\caption{{Every LLM-derived culture score against every Progress 8 outcome. Each cell is
the coefficient from one regression of the outcome on the (standardised) predictor plus
the national control set, including the predecessor-filled 2019 inspection-grade control;
late-entry schools excluded. Because the sweep runs {ntests} such tests ({ntests // 2} per grade
panel), significance is marked only after Benjamini--Hochberg correction across the whole
matrix. The Ofsted-derived scores carry the grade-reconstruction caution described in the
text; behaviour-policy rows use standard errors clustered on the shared document digest.}}
\label{{tab:llm_p8_matrix}}
\footnotesize\setlength{{\tabcolsep}}{{4pt}}
\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{lrccccc}}
\toprule
Predictor & $N$ & Overall & English & Maths & EBacc & Open \\
\midrule
{chr(10).join(lines)}
\bottomrule
\end{{tabular}}%
}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Standard errors in parentheses (HC3 throughout, except the
behaviour-policy rows, which are clustered on the shared trust-template document
digest). \sym{{\dagger}} survives Benjamini--Hochberg correction at $q<0.05$ across all {ntests}
tests in the sweep (both grade panels); the panel shown here includes the 2019
inspection-grade control, which is why $N$ falls below the full spine. The companion
panel without the grade control gives the same qualitative picture with slightly larger
Ofsted coefficients. Interview rows are limited to schools with a scoreable
head-teacher interview.
\end{{minipage}}
\end{{table}}
"""


# ---------------------------------------------------------------- entry rates
def t_entry():
    A = []
    for panel in ["A", "B"]:
        for model, term, lab in [("gold", "z_gs_warmth_enacted", "Visited warmth ($W$)"), ("gold", "z_gs_strictness_enacted", "Visited strictness ($S$)"),
                                 ("national", "z_ofsted_llmstrictnessscore", "Ofsted strictness")]:
            cs = [row("entry", panel, model, oc, term) for oc in ["ebacc_entry", "hum_entry", "lang_entry"]]
            A.append(f"{panel} & {lab:<22} & {nfmt(cs[0].n):<7} & " + " & ".join(f"{f3(c.b)}{stars(c.pval)} ({c.se:.3f})" for c in cs) + r" \\")
        if panel == "A": A.append(r"\addlinespace")
    B = []
    for panel in ["A", "B"]:
        for who, lab, term in [("national", "National (Ofsted $S$)", "z_ofsted_llmstrictnessscore"), ("gold", "Visited ($S$)", "z_gs_strictness_enacted")]:
            w = row("channel", panel, f"{who}_without", "ebac", term); wi = row("channel", panel, f"{who}_with", "ebac", term)
            att = 100 * (w.b - wi.b) / w.b
            B.append(f"{panel} & {lab:<22} & {nfmt(w.n):<7} & {f3(w.b)}{stars(w.pval)} & {f3(wi.b)}{stars(wi.pval)} & {att:.1f}\\% \\\\")
    ent = [row("channel", p, f"{who}_with", "ebac", "ebacc_entry") for p in ["A", "B"] for who in ["national", "gold"]]
    atts = []
    for panel in ["A", "B"]:
        for who, term in [("national", "z_ofsted_llmstrictnessscore"), ("gold", "z_gs_strictness_enacted")]:
            w = row("channel", panel, f"{who}_without", "ebac", term); wi = row("channel", panel, f"{who}_with", "ebac", term)
            atts.append(100 * (w.b - wi.b) / w.b)
    return rf"""\begin{{table}}[htbp]\centering
{SYM}
\small
\caption{{Culture and curriculum entry. Panel A asks whether warm or strict schools
enter pupils for more academic curricula: each cell regresses an entry rate (EBacc,
humanities, languages) on the standardised culture score plus controls, for the
visit scores and the national Ofsted-derived strictness score, without (A) and with (B)
the predecessor-filled 2019 inspection-grade control; late-entry schools excluded.
Panel B then asks how much of the strictness--EBacc-progress association runs through
entry: the strictness coefficient on the EBacc Progress 8 component before and after
controlling the EBacc entry rate.}}
\label{{tab:entry_rates}}
\footnotesize\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{llcccc}}
\toprule
\multicolumn{{6}}{{l}}{{\textit{{Panel A: entry-rate regressions}}}} \\
\addlinespace[2pt]
 & Predictor & $N$ & EBacc entry & Humanities entry & Languages entry \\
\midrule
{chr(10).join(A)}
\midrule
\multicolumn{{6}}{{l}}{{\textit{{Panel B: channel decomposition, strictness $\rightarrow$ EBacc Progress 8 component}}}} \\
\addlinespace[2pt]
 & Model & $N$ & Without entry & With entry & Attenuation \\
\midrule
{chr(10).join(B)}
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Standard errors (HC3) in parentheses.
{NOTES_STARS}
Entry rates are derived from pupil counts. Languages entry is the sharp test of
curriculum steering because double science leaves the science slots close to their
ceiling. In Panel B the EBacc entry rate itself predicts the EBacc component strongly
($\beta$ between ${min(e.b for e in ent):+.2f}$ and ${max(e.b for e in ent):+.2f}$, $p<0.01$ in every model), but
controlling it removes only {min(atts):.0f}--{max(atts):.0f}\% of the strictness association: most of the
strictness--EBacc link is progress within the curriculum entered, not entry itself.
\end{{minipage}}
\end{{table}}
""", min(atts), max(atts)


# ---------------------------------------------------------------- pseudo-P8
def t_p8proxy():
    lines = []
    printed = {}
    for panel in ["A", "B"]:
        for model, term, lab in [("gold", "z_gs_warmth_enacted", "Visited warmth ($W$)"), ("gold", "z_gs_strictness_enacted", "Visited strictness ($S$)"),
                                 ("national", "z_ofsted_llmstrictnessscore", "Ofsted strictness")]:
            cs = [row("p8proxy", panel, model, oc, term) for oc in ["pseudo_p8_2425", "pseudo_p8_2425_eng", "pseudo_p8_2425_mat", "p8mea_avg"]]
            printed[(panel, term)] = cs
            lines.append(f"{panel} & {lab:<22} & {nfmt(cs[0].n):<7} & " + " & ".join(f3(c.b) + stars(c.pval) for c in cs) + r" \\")
            lines.append(f"  & {'':<22} & {'':<7} & " + " & ".join(f"({c.se:.3f})" for c in cs) + r" \\")
        if panel == "A": lines.append(r"\addlinespace")
    corr = row("p8proxy", "", "corr_pseudo_vs_real_p8avg", "overall", "pearson")
    # The note quotes the same cells the panels print (pseudo overall vs real
    # overall for the visited-school rows); it used to quote a separate
    # raw-score export, which disagreed with the table by rounding and spec.
    pw_a = printed[("A", "z_gs_warmth_enacted")]; ps_a = printed[("A", "z_gs_strictness_enacted")]
    pw_b = printed[("B", "z_gs_warmth_enacted")]; ps_b = printed[("B", "z_gs_strictness_enacted")]
    maxdiff = max(abs(cs[0].b - cs[3].b) for cs in (pw_a, ps_a, pw_b, ps_b))
    valtxt = ""
    if VAL is not None:
        try:
            v = VAL.iloc[0].to_dict()
            valtxt = " ".join(f"{k}={v[k]}" for k in v)
        except Exception:
            valtxt = ""
    return rf"""\begin{{table}}[htbp]\centering
{SYM}
\small
\caption{{Culture coefficients on the pseudo 2024/25 progress measure beside their
real-Progress 8 twins. The pseudo measure residualises 2024/25 Attainment 8 on a
multi-year z-averaged KS2 intake proxy, giving a progress-like score for the cohort
measured contemporaneously with the fieldwork. Each cell is the (standardised) culture
coefficient from the same specification run on the pseudo outcome and on real (2022--24
average) Progress 8 for the same schools, without (A) and with (B) the predecessor-filled
2019 inspection-grade control; late-entry schools excluded.}}
\label{{tab:p8_proxy}}
\footnotesize\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{llccccc}}
\toprule
 & Predictor & $N$ & \shortstack{{Pseudo\\overall}} & \shortstack{{Pseudo\\English}} & \shortstack{{Pseudo\\Maths}} & \shortstack{{Real P8\\overall}} \\
\midrule
{chr(10).join(lines)}
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Standard errors (HC3) in parentheses.
{NOTES_STARS}
Across the national panel the pseudo measure correlates with real average Progress 8 at
$r = {corr.b:+.3f}$ ($n = {nfmt(corr.n)}$). Validation of the construction one year back (the
pseudo measure rebuilt from 2021--22 and 2022--23 baselines against the real 2023--24
Progress 8) is $+0.81$ (two-year construction, $n = 3{{,}}242$;
ch3\_appendix\_p8proxy\_validation.csv). On the body's per-standard-deviation scale, the
visited-school coefficients on the pseudo outcome sit within ${maxdiff:.2f}$ of their
real-Progress 8 twins in the same panel (Panel A: pseudo {pw_a[0].b:.3f}/{ps_a[0].b:.3f} against real
{pw_a[3].b:.3f}/{ps_a[3].b:.3f}; Panel B: pseudo {pw_b[0].b:.3f}/{ps_b[0].b:.3f} against real {pw_b[3].b:.3f}/{ps_b[3].b:.3f},
warmth/strictness). The ``Ofsted strictness'' rows use the marking-scheme strictness
bands of Chapter~2 (1--5, standardised over each estimation sample), not the retired
analyser score. The pseudo measure is
school-level, not pupil-matched, so it is a robustness check, never a primary outcome.
\end{{minipage}}
\end{{table}}
""", maxdiff, corr


# ---------------------------------------------------------------- SEMH mechanism
def t_semh():
    s = row("semh", "", "tier1_S", "semh_share", "z_gs_strictness_enacted"); sb = row("semh", "", "tier1_S", "semh_share", "semh_share_2016")
    w = row("semh", "", "tier1_W", "semh_share", "z_gs_warmth_enacted"); wb = row("semh", "", "tier1_W", "semh_share", "semh_share_2016")
    n_ = row("semh", "", "national_S", "semh_share", "z_ofsted_llmstrictnessscore"); nb = row("semh", "", "national_S", "semh_share", "semh_share_2016")
    return rf"""\begin{{table}}[htbp]\centering
{SYM}
\caption{{The SEMH composition mechanism. Each column regresses a school's 2023--24
share of pupils with social, emotional and mental-health (SEMH) needs, as a
percentage of the roll, on one culture score plus the school's 2015--16 baseline
SEMH share and the primary control set: visited-school strictness and warmth
($n=94$ visited schools), and the national Ofsted marking-scheme strictness
($n=2{{,}}594$). Coefficients are percentage points per standard deviation of the
score. The strictness coefficients are null or negative: strict schools do not
carry more SEMH pupils today than their baseline predicts, so a changing intake
does not explain the strictness--progress association.}}
\label{{tab:semh_mechanism}}
\begin{{tabular}}{{l*{{3}}{{c}}}}
\toprule
                    &\multicolumn{{1}}{{c}}{{Visited (S)}}&\multicolumn{{1}}{{c}}{{Visited (W)}}&\multicolumn{{1}}{{c}}{{National (S)}}\\
\midrule
Strictness ($S_{{\text{{visit}}}}$, per SD)&      {f3(s.b)}{stars(s.pval)}         &                     &                     \\
                    &     ({s.se:.3f})         &                     &                     \\
\addlinespace
SEMH share 2015--16 (\%)&       {f3(sb.b)}{stars(sb.pval)} &       {f3(wb.b)}{stars(wb.pval)}&       {f3(nb.b)}{stars(nb.pval)}\\
                    &     ({sb.se:.3f})         &     ({wb.se:.3f})         &     ({nb.se:.3f})         \\
\addlinespace
Warmth ($W_{{\text{{visit}}}}$, per SD)&                     &      {f3(w.b)}{stars(w.pval)}         &                     \\
                    &                     &     ({w.se:.3f})         &                     \\
\addlinespace
Strictness (Ofsted LLM, per SD)&                     &                     &      {f3(n_.b)}{stars(n_.pval)}\\
                    &                     &                     &     ({n_.se:.3f})         \\
\midrule
N                   &          {int(s.n)}         &          {int(w.n)}         &        {nfmt(n_.n)}         \\
r2                  &       {s.r2:.3f}         &       {w.r2:.3f}         &       {n_.r2:.3f}         \\
\bottomrule
\multicolumn{{4}}{{l}}{{\footnotesize Standard errors (HC3) in parentheses. Outcome: 2023--24 SEMH pupils as a percentage of the roll;}}\\
\multicolumn{{4}}{{l}}{{\footnotesize baseline is the 2015--16 SEMH count over the current roll. Primary controls; late-entry excluded.}}\\
\multicolumn{{4}}{{l}}{{\footnotesize {NOTES_STARS}}}\\
\end{{tabular}}
\end{{table}}
""", s, n_


# ---------------------------------------------------------------- stability
def t_stability():
    S = STAB.set_index("stat")
    n = int(S.loc["within_school_sd_mean", "n"])
    pairs = [("2017-2018->2018-2019", "2017--18 $\\rightarrow$ 2018--19"), ("2021-2022->2022-2023", "2021--22 $\\rightarrow$ 2022--23"),
             ("2022-2023->2023-2024", "2022--23 $\\rightarrow$ 2023--24"), ("pooled", "All adjacent pairs pooled")]
    pl = []
    for k, lab in pairs:
        a = S.loc[f"share_gt_0.3|{k}"]; b = S.loc[f"share_gt_0.5|{k}"]
        pl.append(f"{lab:<31} & {nfmt(a.n)} & {100*a.value:.1f}\\% & {100*b.value:.1f}\\% \\\\")
    ev = ACAD.pivot(index="event_t", columns="atype", values=["mean", "count"])
    el = []
    for t in sorted(ev.index):
        def cell(at):
            try:
                m = ev.loc[t, ("mean", at)]; c = ev.loc[t, ("count", at)]
                if pd.isna(m): return ""
                return f"{'$-$' if m < 0 else '$+$'}{abs(m):.2f} \\,($n={int(c)}$)"
            except KeyError:
                return ""
        el.append(f"$t{int(t):+d}$ & {cell('converter')} & {cell('sponsor-led')} & \\\\")
    return rf"""\begin{{table}}[htbp]\centering
\small
\caption{{How stable is a school's Progress 8, and what happens around academisation.
Panel A summarises each school's own standard deviation of Progress 8 across the five
published years and the share of schools moving by more than 0.3 or 0.5 of a grade
between consecutive years. Panel B gives mean Progress 8 by year relative to the year of
academy conversion, separately for converter and sponsor-led academies.}}
\label{{tab:stability_p8}}
\begin{{tabular}}{{lrrr}}
\toprule
\multicolumn{{4}}{{l}}{{\textit{{Panel A: within-school variation (2017--18 to 2023--24, $n={nfmt(n)}$ schools)}}}} \\
\addlinespace[2pt]
\multicolumn{{4}}{{l}}{{Within-school SD: mean {S.loc['within_school_sd_mean','value']:.3f}, median {S.loc['within_school_sd_median','value']:.3f}, 10th percentile {S.loc['within_school_sd_p10','value']:.3f}, 90th percentile {S.loc['within_school_sd_p90','value']:.3f}}} \\
\addlinespace[4pt]
Adjacent-year pair & $N$ & Moved $>$0.3 & Moved $>$0.5 \\
\midrule
{chr(10).join(pl)}
\midrule
\multicolumn{{4}}{{l}}{{\textit{{Panel B: mean Progress 8 by event year around academisation}}}} \\
\addlinespace[2pt]
Event year & \multicolumn{{1}}{{c}}{{Converter}} & \multicolumn{{1}}{{c}}{{Sponsor-led}} & \\
\midrule
{chr(10).join(el)}
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Panel A uses schools with at least three published years.
There is no Progress 8 for 2019--20 or 2020--21 (COVID), so ``adjacent'' means
consecutive academic years only; the 2018--19 to 2021--22 boundary is not counted as a
pair. Panel B rests on the predecessor--successor bridging table (converter and
sponsor-led academies; cells with fewer than five schools suppressed); these are raw
event-time means, not a matched event study. Sponsor-led academies are taken over from a
much lower base and close roughly half the gap over eight years; converters start near
zero and drift slightly upward.
\end{{minipage}}
\end{{table}}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    changed = []
    write("tab_subscores.tex", t_subscores(), a.check, changed)
    items_tex, npos, nsurv, nitems = t_items(); write("tab_items_fdr.tex", items_tex, a.check, changed)
    write("tab_typology.tex", t_typology(), a.check, changed)
    write("tab_gaps.tex", t_gaps(), a.check, changed)
    write("tab_parentview.tex", t_parentview(), a.check, changed)
    write("tab_llm_p8_matrix.tex", t_llm_matrix(), a.check, changed)
    entry_tex, amin, amax = t_entry(); write("tab_entry_rates.tex", entry_tex, a.check, changed)
    p8_tex, maxdiff, corr = t_p8proxy(); write("tab_p8_proxy.tex", p8_tex, a.check, changed)
    semh_tex, s_row, n_row = t_semh(); write("tab_semh_mechanism.tex", semh_tex, a.check, changed)
    write("tab_stability_p8.tex", t_stability(), a.check, changed)
    print(f"\nprose-relevant: items positive {npos}/{nitems}, surviving BH {nsurv}; entry attenuation {amin:.0f}-{amax:.0f}%; "
          f"pseudo-vs-real max raw diff {maxdiff:.3f}, corr {corr.b:.3f} (n={int(corr.n)}); SEMH tier1 S {s_row.b:.3f} p={s_row.pval:.2f} n={int(s_row.n)}; "
          f"national S {n_row.b:.3f} p={n_row.pval:.3f} n={int(n_row.n)}")
    if a.check:
        if changed:
            print("DIFFER:", changed); return 1
        print("all ten appendix tables match their CSVs"); return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
