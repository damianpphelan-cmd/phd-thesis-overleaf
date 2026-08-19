"""Regenerate thesis/tables/tab_instruments_adopted.tex (Chapter 2, Table 2.3).
19 Aug 2026: was hand-typed; the validity columns are now computed from
analysis_dataset.csv against BOTH halves of the gold standard (enacted on the
visited schools, espoused on the interviewed schools), on Damian's ruling that
a source written by the school should be checked against what the school says
as well as what it does. The kappas are out-of-sample agreement figures traced
to the labelling packs (VERIFICATION_LEDGER.csv) and are carried as constants.
Run with --check to compare without writing."""
import argparse, os, sys
import pandas as pd
from scipy import stats
ROOT = r"C:\Users\damia\OneDrive\Documents\Schools Project"
OUT = os.path.join(ROOT, "thesis", "tables", "tab_instruments_adopted.tex")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

d = pd.read_csv(os.path.join(ROOT, "analysis_dataset.csv"), encoding="utf-8-sig", low_memory=False)
def r(a, b):
    m = d[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
    return stats.pearsonr(m[a], m[b])[0]
def f(v):
    return f"${'+' if v >= 0 else '-'}{abs(v):.2f}$"

# (source, construct, architecture, score column, enacted criterion, espoused criterion, kappa)
rows = [
    ("Inspection report", "Strictness", "Prose", "ofsted_LLMStrictnessScore", "gs_strictness_enacted", "gs_strictness_espoused", "0.64"),
    ("Inspection report", "Warmth", "Prose", "ofsted_LLMWarmthScore", "gs_warmth_enacted", "gs_warmth_espoused", "0.45"),
    ("Inspection report", "Teaching", "Prose", "ofsted_LLMTeachingScore", "gs_teaching_enacted", None, "0.75"),
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
    lines.append(f"{src} & {con} & {arch} & {en_s} & {es_s} & {k} \\\\")
lines.append(r"Website & Religious character & Prose classifier & \multicolumn{2}{c}{register, 97\% agree} & --- \\")
lines.append(r"\addlinespace[3pt]")
lines.append(r"Interview transcript & Strictness & Decomposed & --- & --- & 0.63 \\")
lines.append(r"Interview transcript & Warmth & Decomposed & --- & --- & 0.56 \\")

tex = r"""\begin{table}[htbp]
\centering
\small
\caption{The scoring instruments adopted for the national tier. Validity is
each instrument's correlation with the gold standard: with the enacted
(observed) score on the visited schools, and with the espoused
(headteacher-reported) score on the interviewed schools; for religious
character, agreement with the Department for Education's register.
Agreement is weighted kappa against the reference labels, measured out of
sample on documents no version was tuned on.}
\label{tab:instruments_adopted}
\begin{tabular}{llcccc}
\toprule
 & & & \multicolumn{2}{c}{\textit{Validity, $r$ with}} & \\
\cmidrule(lr){4-5}
\textit{Source} & \textit{Construct} & \textit{Architecture} &
enacted & espoused & $\kappa_w$ \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\begin{minipage}{0.92\linewidth}
\vspace{4pt}\scriptsize
\textit{Notes}: ``Prose'': the model reads a written marking scheme and
returns a band in one call. ``Decomposed'': the model answers factual
questions with verified quotations and the band is assigned by a rule in
code; $^{a}$the behaviour-policy instrument reads the whole policy against a
written decision procedure in one call and answers its steps, and the band is
computed from the answers rather than returned by the model. Kappas are model--model agreement against the majority label of three
blind model raters. The inspection-report warmth score also tracks the
inspection grade ($r = -0.40$) from grade-stripped text, and is used as a
description of the report rather than a predictor. The website warmth
instrument does not separate its two lowest bands reliably. The interview
transcript instruments are methodological comparisons only; the espoused
scores of record come from the statement battery, not the transcripts.
\end{minipage}
\end{table}
"""
ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
if cur == tex:
    print("unchanged tab_instruments_adopted.tex"); raise SystemExit(0)
if a.check:
    print("DIFFERS tab_instruments_adopted.tex"); raise SystemExit(1)
open(OUT, "w", encoding="utf-8", newline="\n").write(tex); print("wrote tab_instruments_adopted.tex")
