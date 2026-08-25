"""Regenerate tables/tab_score_dist.tex from analysis_dataset.csv.

The table was hand-maintained and went stale twice over: it reported n = 102
(the URN join added one school), the pre-extension sub-score means (W1, S1 and
T1 all moved when the four unused classroom items were folded in), and three
"composite" rows for a score the chapter withdrew on 5 Aug 2026. It now reports
the enacted and espoused scores that replaced the composite.

Run:  python thesis/make_tab_score_dist.py
"""

from pathlib import Path

import pandas as pd

from fix_tables import move_caption_below

BASE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "tables" / "tab_score_dist.tex"

SUBSCORES = [
    ("gs_W1",      r"$W1$",     "In-lesson staff--pupil warmth",        "visit"),
    ("gs_W2",      r"$W2$",     "Warmth in transitions and breaks",     "visit"),
    ("gs_W3",      r"$W3$",     "HT espoused warmth (statements)",      "interview"),
    ("gs_S1",      r"$S1$",     "In-lesson behaviour management",       "visit"),
    ("gs_S2",      r"$S2$",     "Out-of-lesson behaviour management",   "visit"),
    ("gs_S3",      r"$S3$",     "Behaviour management systems (count)", "interview"),
    ("gs_S4",      r"$S4$",     "HT espoused strictness (statements)",  "interview"),
    ("gs_T1",      r"$T1$",     "In-lesson teaching quality",           "visit"),
    ("gs_T2",      r"$SC$",     "HT espoused staff climate (statements)", "interview"),
]

SCORES = [
    ("gs_warmth_enacted",      "Warmth", "enacted"),
    ("gs_strictness_enacted",  "Strictness", "enacted"),
    ("gs_teaching_enacted",    "Teaching", "enacted"),
    ("gs_warmth_espoused",     "Warmth", "espoused"),
    ("gs_strictness_espoused", "Strictness", "espoused"),
    ("gs_staff_climate_espoused", "Staff climate", "espoused"),
]


def row(v, label, desc):
    return (rf"{label} & {desc} & {len(v)} & {v.mean():.2f} & {v.std():.2f} & "
            rf"{v.min():.2f} & {v.median():.2f} & {v.max():.2f} \\")


def main():
    d = pd.read_csv(BASE / "analysis_dataset.csv", low_memory=False)
    g = d[d["gs_data_tier"] == "full"]
    n = len(g)

    lines = []
    for col, label, desc, _src in SUBSCORES:
        lines.append(row(g[col].dropna(), label, desc))
    lines.append(r"\midrule")
    for col, dim, kind in SCORES:
        lines.append(row(g[col].dropna(), dim, rf"\emph{{{kind}}}"))

    body = "\n".join(lines)
    tex = rf"""\begin{{table}}[htbp]
\centering
\caption{{Distribution of sub-scores and of the enacted and espoused scores for
the visited schools with full data ($n = {n}$).
Sub-scores are on a $[0,5]$ scale; the enacted and espoused scores on a $[0,10]$ scale.}}
\label{{tab:score_dist}}
\footnotesize\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{llcccccc}}
\toprule
Score & Description & $N$ & Mean & SD & Min & Median & Max \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\textwidth}}\vspace{{0.5em}}\footnotesize
\textit{{Notes.}} The enacted scores are built from the visit sub-scores
($W1$, $W2$, $S1$, $S2$, $T1$) and the espoused scores from the interview
statement sub-scores ($W3$, $S4$; $SC$ is the staff-climate score), as set
out in \cref{{eq:enacted,eq:espoused}}. The systems count $S3$ enters no
score. No sub-score enters both sets.
\end{{minipage}}
\end{{table}}
"""
    tex, _ = move_caption_below(tex)
    OUT.write_text(tex, encoding="utf-8")

    print(f"wrote {OUT.relative_to(BASE)}  (n = {n})")
    for col, label, _d, _s in SUBSCORES:
        v = g[col].dropna()
        print(f"   {label:<8} n={len(v):4d}  mean={v.mean():.2f}  SD={v.std():.2f}")
    for col, dim, kind in SCORES:
        v = g[col].dropna()
        print(f"   {dim:<10} {kind:<9} n={len(v):4d}  mean={v.mean():.2f}  SD={v.std():.2f}")


if __name__ == "__main__":
    main()
