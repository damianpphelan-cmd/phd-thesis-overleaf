"""Regenerate thesis/tables/tab_source_criterion.tex from analysis_dataset.csv.
19 Aug 2026: the table was hand-typed; now generated, and on the instruments of
record in BOTH chapters (Ofsted prose v4c column of record; behaviour policy v4;
website warmth v18 / strictness v15; Parent View composite).
Run with --check to compare without writing."""
import argparse, os, sys
import numpy as np
import pandas as pd
from scipy import stats

from fix_tables import caption_to_title, move_caption_below
ROOT = r"C:\Users\damia\OneDrive\Documents\Schools Project"
OUT = os.path.join(ROOT, "thesis", "tables", "tab_source_criterion.tex")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

d = pd.read_csv(os.path.join(ROOT, "analysis_dataset.csv"), encoding="utf-8-sig", low_memory=False)
for c in ["gs_warmth_enacted", "gs_strictness_enacted", "gs_warmth_espoused", "gs_strictness_espoused",
          "ofsted_LLMWarmthScore", "ofsted_LLMStrictnessScore", "bp_LLMWarmthScore_v4", "bp_LLMStrictnessScore_v4",
          "web_LLMWarmthScore_v18", "web_LLMStrictnessScore_v15", "pv_warmth"]:
    d[c] = pd.to_numeric(d[c], errors="coerce")

def r(x, y):
    m = d[x].notna() & d[y].notna()
    return stats.pearsonr(d.loc[m, x], d.loc[m, y])[0], int(m.sum())

def f(v):
    return f"${'+' if v >= 0 else '-'}{abs(v):.2f}$"

rows = [("Ofsted inspection report", "ofsted_LLMWarmthScore", "ofsted_LLMStrictnessScore"),
        ("Behaviour policy", "bp_LLMWarmthScore_v4", "bp_LLMStrictnessScore_v4"),
        ("School website", "web_LLMWarmthScore_v18", "web_LLMStrictnessScore_v15")]
lines, ns = [], []
for lab, w, s in rows:
    a, n1 = r(w, "gs_warmth_enacted"); b, n2 = r(w, "gs_warmth_espoused")
    c, n3 = r(s, "gs_strictness_enacted"); e, n4 = r(s, "gs_strictness_espoused")
    ns += [n1, n2, n3, n4]
    lines.append(f"{lab:<24} & {f(a)} & {f(b)} & {f(c)} & {f(e)} \\\\")
pa, _ = r("pv_warmth", "gs_warmth_enacted"); pb, _ = r("pv_warmth", "gs_warmth_espoused"); pc, _ = r("pv_warmth", "gs_strictness_enacted")
lines.append(f"{'Parent survey':<24} & {f(pa)} & {f(pb)} & \\multicolumn{{2}}{{c}}{{({f(pc)} vs enacted strictness)}} \\\\")
n_en = sorted(set(ns[0::2])); n_es = sorted(set(ns[1::2]))
tex = rf"""\begin{{table}}[htbp]
\centering
\small
\caption{{Each text source's warmth and strictness score correlated with the
enacted (observed) and espoused (headteacher-reported) gold-standard measure.
Enacted correlations use the visited schools; espoused correlations use the
interviewed schools. The parent survey has no strictness item; its warmth
composite is also shown against enacted strictness.}}
\label{{tab:source_criterion}}
\begin{{tabular}}{{lcccc}}
\toprule
 & \multicolumn{{2}}{{c}}{{\textit{{Warmth score vs}}}} & \multicolumn{{2}}{{c}}{{\textit{{Strictness score vs}}}} \\
\cmidrule(lr){{2-3}}\cmidrule(lr){{4-5}}
\textit{{Source}} & enacted & espoused & enacted & espoused \\
 & $(n = {min(n_en)}$--${max(n_en)})$ & $(n = {min(n_es)}$--${max(n_es)})$ & $(n = {min(n_en)}$--${max(n_en)})$ & $(n = {min(n_es)}$--${max(n_es)})$ \\
\midrule
{chr(10).join(lines)}
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{0.86\linewidth}}
\vspace{{4pt}}\scriptsize
\textit{{Notes}}: Pearson correlations. Text scores are the instruments of
record listed in \cref{{tab:instruments_adopted}}. Correlations of $|r| \geq 0.20$ are
significant at the five per cent level in the observed columns ($n \approx 101$);
in the espoused columns ($n \approx 300$) the threshold is $|r| \geq 0.11$.
\end{{minipage}}
\end{{table}}
"""
ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
tex, _ = move_caption_below(tex)
# caption convention (PIPELINE.md, 29 Aug 2026)
tex = caption_to_title(tex,
                       'Each text source against the gold-standard measures',
                       keep_first=True)
cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
if cur == tex:
    print("unchanged tab_source_criterion.tex"); raise SystemExit(0)
if a.check:
    print("DIFFERS tab_source_criterion.tex"); raise SystemExit(1)
open(OUT, "w", encoding="utf-8", newline="\n").write(tex); print("wrote tab_source_criterion.tex")
