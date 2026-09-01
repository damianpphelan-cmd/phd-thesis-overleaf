"""Regenerate thesis/tables/tab_instruments_adopted.tex (Chapter 2, Table 2.3).
19 Aug 2026: was hand-typed; the validity columns are now computed from
analysis_dataset.csv against BOTH halves of the gold standard (enacted on the
visited schools, espoused on the interviewed schools), on Damian's ruling that
a source written by the school should be checked against what the school says
as well as what it does. The kappas are out-of-sample agreement figures traced
to the labelling packs (VERIFICATION_LEDGER.csv; RUN_RESULTS_2.md prose-vs-ladder
table for the Ofsted prose rubric: kappa 0.489/0.182/0.537, rho 0.559/0.309/0.585;
interview warmth v15 OOS +0.412) and are carried as constants. 20 Aug 2026: the
Ofsted kappas had been the FLAG scorers' (0.64/0.45/0.75) beside the PROSE
instrument's validity; corrected on Damian's ruling.
Run with --check to compare without writing."""
import argparse, os, sys
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import cohen_kappa_score

from fix_tables import caption_to_title, move_caption_below
ROOT = r"C:\Users\damia\OneDrive\Documents\Schools Project"
OUT = os.path.join(ROOT, "thesis", "tables", "tab_instruments_adopted.tex")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

d = pd.read_csv(os.path.join(ROOT, "analysis_dataset.csv"), encoding="utf-8-sig", low_memory=False)
def r(a, b):
    m = d[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
    return stats.pearsonr(m[a], m[b])[0]
def f(v):
    return f"${'+' if v >= 0 else '-'}{abs(v):.2f}$"

# --- human concordance: the instrument of record against the author's own labels on the
# development packs (20 Aug 2026, referee round three point 7). These are the packs the
# written rules were drafted against, so they are development-set figures, reported as
# concordance evidence and not as a test.
LAB = os.path.join(ROOT, "labelling")
_labs = {
    "ofsted": pd.read_csv(os.path.join(LAB, "ofsted", "ofsted_labels.csv"), encoding="utf-8-sig"),
    "bp": pd.read_csv(os.path.join(LAB, "behaviour", "behaviour_labels.csv"), encoding="utf-8-sig"),
    "web": pd.read_csv(os.path.join(LAB, "website", "website_labels.csv"), encoding="utf-8-sig"),
}
def human_kappa(pack, dim, col):
    lab = _labs[pack].copy(); lab["URN"] = lab["URN"].astype(str)
    m = lab.merge(d.assign(urn=d["urn"].astype(str)), left_on="URN", right_on="urn", how="left")
    x = m[[dim, col]].apply(pd.to_numeric, errors="coerce").dropna()
    a, b = x[dim].round().astype(int), x[col].round().astype(int)
    k = cohen_kappa_score(a, b, weights="quadratic", labels=[1, 2, 3, 4, 5])
    return k, len(x), float((b - a).mean())
HUMAN = {
    "ofsted_LLMStrictnessScore": human_kappa("ofsted", "strictness", "ofsted_LLMStrictnessScore"),
    "ofsted_LLMWarmthScore": human_kappa("ofsted", "warmth", "ofsted_LLMWarmthScore"),
    "ofsted_LLMTeachingScore": human_kappa("ofsted", "teaching", "ofsted_LLMTeachingScore"),
    "bp_LLMStrictnessScore_v4": human_kappa("bp", "strictness", "bp_LLMStrictnessScore_v4"),
    "bp_LLMWarmthScore_v4": human_kappa("bp", "warmth", "bp_LLMWarmthScore_v4"),
    "web_LLMStrictnessScore_v15": human_kappa("web", "strictness", "web_LLMStrictnessScore_v15"),
    "web_LLMWarmthScore_v18": human_kappa("web", "warmth", "web_LLMWarmthScore_v18"),
}
def hcell(col):
    k, n, _ = HUMAN[col]
    return f"{k:.2f} ({n})"

# (source, construct, architecture, score column, enacted criterion, espoused criterion, kappa)
rows = [
    ("Inspection report", "Strictness", "Prose", "ofsted_LLMStrictnessScore", "gs_strictness_enacted", "gs_strictness_espoused", "0.49"),
    ("Inspection report", "Warmth", "Prose", "ofsted_LLMWarmthScore", "gs_warmth_enacted", "gs_warmth_espoused", "0.18"),
    ("Inspection report", "Teaching", "Prose", "ofsted_LLMTeachingScore", "gs_teaching_enacted", None, "0.54"),
    None,
    ("Behaviour policy", "Strictness", "Prose$^{a}$", "bp_LLMStrictnessScore_v4", "gs_strictness_enacted", "gs_strictness_espoused", "0.76"),
    ("Behaviour policy", "Warmth", "Prose$^{a}$", "bp_LLMWarmthScore_v4", "gs_warmth_enacted", "gs_warmth_espoused", "0.76"),
    None,
    ("Website", "Strictness", "Decomposed", "web_LLMStrictnessScore_v15", "gs_strictness_enacted", "gs_strictness_espoused", "0.66"),
    ("Website", "Warmth", "Decomposed", "web_LLMWarmthScore_v18", "gs_warmth_enacted", "gs_warmth_espoused", "0.69"),
]
lines = []
for row in rows:
    if row is None:
        lines.append(r"\addlinespace[3pt]"); continue
    src, con, arch, col, en, es, k = row
    en_s = f(r(col, en))
    es_s = f(r(col, es)) if es else "---"
    lines.append(f"{src} & {con} & {arch} & {en_s} & {es_s} & {k} & {hcell(col)} \\\\")
lines.append(r"Website & Religious character & Prose classifier & \multicolumn{2}{c}{register, 97\% agree} & --- & --- \\")
lines.append(r"\addlinespace[3pt]")
lines.append(r"Interview transcript & Strictness & Decomposed & --- & --- & 0.63 & --- \\")
lines.append(r"Interview transcript & Warmth & Decomposed & --- & --- & 0.41 & --- \\")

tex = r"""\begin{table}[htbp]
\centering
\small
\caption{The scoring instruments adopted for the national tier. Validity is
each instrument's correlation with the gold standard: with the enacted
(observed) score on the visited schools, and with the espoused
(headteacher-reported) score on the interviewed schools; for religious
character, agreement with the Department for Education's register.}
\label{tab:instruments_adopted}
\begin{tabular}{llccccc}
\toprule
 & & & \multicolumn{2}{c}{\textit{Validity, $r$ with}} & \multicolumn{2}{c}{\textit{Agreement, $\kappa_w$}} \\
\cmidrule(lr){4-5}\cmidrule(lr){6-7}
\textit{Source} & \textit{Construct} & \textit{Architecture} &
enacted & espoused & reference labels & author's labels ($n$) \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\begin{minipage}{0.92\linewidth}
\vspace{4pt}\scriptsize
\textit{Notes}: ``Prose'': the model reads a written mark scheme and
returns a band in one call. ``Decomposed'': the model answers factual
questions with verified quotations and the band is assigned by a rule in
code. $^{a}$The behaviour-policy instrument is applied to the whole policy against a
written decision procedure in one call and answers its steps, and the band is
computed from the answers rather than returned by the model. The
reference-label kappas are out-of-sample figures for the instrument in each
row, measuring agreement against the majority label of three blind model
raters on documents no version was tuned on. The author's-label kappas are
agreement with the author's own labels on the development packs (30
inspection reports, 25 behaviour policies, 50 websites), which are the
documents the written rules were drafted against, and are reported as
concordance evidence rather than as a test. The
inspection-report mark scheme was calibrated to a different labelling scale from
the reference labels, so its kappas carry a systematic offset and understate
its agreement on ordering (rank correlations with the reference labels:
$0.56$, $0.31$ and $0.59$ for strictness, warmth and teaching). The website warmth instrument does not separate its
two lowest bands reliably. The interview transcript instruments are
methodological comparisons only; the espoused scores of record come from the
statement battery, not the transcripts.
\end{minipage}
\end{table}
"""
# three-way concordance on the two development packs where a blind Claude pass exists
# (scripts check_claude_vs_damian_ofsted.py / _website.py; figures reproduced here from
# the three_way_website.csv file and the ofsted script's output, 20 Aug 2026)
tw = pd.read_csv(os.path.join(LAB, "website", "three_way_website.csv"), encoding="utf-8-sig")
def _kq(a, b): return cohen_kappa_score(a.astype(int), b.astype(int), weights="quadratic", labels=[1,2,3,4,5])
web_cd = {dim: _kq(g.damian, g.claude) for dim, g in tw.groupby("dim")}
mac = lambda name, val: f"\\newcommand{{\\{name}}}{{{val}}}\n"
NUM_OUT = os.path.join(ROOT, "thesis", "snippets", "concordance_numbers.tex")
nums = ("% Auto-generated by thesis/make_tab_instruments_adopted.py -- do not edit by hand.\n"
        + "".join(mac(n, f"{HUMAN[c][0]:.2f}") for n, c in (
            ("HumKOfstedS", "ofsted_LLMStrictnessScore"), ("HumKOfstedW", "ofsted_LLMWarmthScore"),
            ("HumKOfstedT", "ofsted_LLMTeachingScore"), ("HumKBPS", "bp_LLMStrictnessScore_v4"),
            ("HumKBPW", "bp_LLMWarmthScore_v4"), ("HumKWebS", "web_LLMStrictnessScore_v15"),
            ("HumKWebW", "web_LLMWarmthScore_v18")))
        + mac("ClaudeDamianWebS", f"{web_cd['strictness']:.2f}") + mac("ClaudeDamianWebW", f"{web_cd['warmth']:.2f}"))
ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
curn = open(NUM_OUT, encoding="utf-8").read() if os.path.exists(NUM_OUT) else ""
if curn != nums:
    if a.check:
        print("DIFFERS concordance_numbers.tex"); raise SystemExit(1)
    open(NUM_OUT, "w", encoding="utf-8", newline="\n").write(nums); print("wrote concordance_numbers.tex")
tex, _ = move_caption_below(tex)
tex = caption_to_title(
    tex, "The scoring instruments adopted for the national tier")
cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
if cur == tex:
    print("unchanged tab_instruments_adopted.tex"); raise SystemExit(0)
if a.check:
    print("DIFFERS tab_instruments_adopted.tex"); raise SystemExit(1)
open(OUT, "w", encoding="utf-8", newline="\n").write(tex); print("wrote tab_instruments_adopted.tex")
