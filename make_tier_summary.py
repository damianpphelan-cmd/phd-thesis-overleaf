#!/usr/bin/env python3
"""Regenerate thesis/tables/tab_tier_summary.tex from analysis_dataset.csv.

The previous version of this table was hand-built and had two defects: the
EAL column rendered as `--` (the source column is percent-formatted strings
such as "57.70%", which silently coerce to NaN), and the Tier 2 count was 196
where the chapter text says 201.

    python thesis/make_tier_summary.py
"""
from __future__ import annotations

import pathlib
import numpy as np
import pandas as pd

from fix_tables import move_caption_below

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "thesis" / "tables" / "tab_tier_summary.tex"


def pct(series: pd.Series) -> pd.Series:
    """Coerce a column that may be '57.70%' strings or plain floats."""
    return pd.to_numeric(
        series.astype(str).str.replace("%", "", regex=False).str.strip()
        .replace({"": np.nan, "nan": np.nan, "None": np.nan}),
        errors="coerce",
    )


def main() -> None:
    d = pd.read_csv(ROOT / "analysis_dataset.csv", low_memory=False)
    d.columns = [c.lstrip("﻿") for c in d.columns]

    for col in ("fsm", "eal", "size", "ofsted_grade"):
        d[col] = pct(d[col])

    tier = d["gs_data_tier"].fillna("national")
    groups = [
        ("Full data (Tier 1)", d[tier == "full"]),
        ("Interview only (Tier 2)", d[tier == "interview_only"]),
        ("Remaining national (Tier 3)", d[tier == "national"]),
        (None, None),                       # rule
        ("All schools", d),
    ]

    rows = []
    for label, g in groups:
        if label is None:
            rows.append(r"\midrule")
            continue
        graded = g["ofsted_grade"].dropna()
        outstanding = 100 * (graded == 1).mean() if len(graded) else np.nan
        good = 100 * (graded == 2).mean() if len(graded) else np.nan
        rows.append(
            "%s & %s & %.1f & %.1f & %s & %.0f & %.0f \\\\"
            % (
                label,
                "{:,}".format(len(g)).replace(",", "{,}"),
                g["fsm"].mean(),
                g["eal"].mean(),
                "{:,}".format(int(g["size"].median())).replace(",", "{,}"),
                outstanding,
                good,
            )
        )

    body = "\n".join(rows)
    tex = r"""\begin{table}[htbp]
\centering
\caption{Distribution of schools across measurement tiers and selected
observable characteristics (2023--24 school year). Tiers are mutually
exclusive: Tier~1 schools received both a headteacher interview and a
researcher visit, Tier~2 an interview only, and Tier~3 comprises the remaining
national population. FSM\%: mean proportion eligible for free school meals.
EAL\%: mean proportion with English as an additional language. Size: median
number of pupils on roll. Outstanding\%/Good\%: percentage rated Outstanding or
Good at most recent inspection, among schools with a grade.}
\label{tab:tier_summary}
\small
\begin{tabular}{lcccccc}
\toprule
Tier & $N$ & FSM\% & EAL\% & Median size & Outstanding\% & Good\% \\
\midrule
@BODY@
\bottomrule
\multicolumn{7}{l}{\footnotesize The tiers sum to one fewer than the total: one interviewed school whose head}\\
\multicolumn{7}{l}{\footnotesize left the statement battery blank belongs to the total but to no tier.}\\
\end{tabular}
\end{table}
""".replace("@BODY@", body)

    tex, _ = move_caption_below(tex)
    OUT.write_text(tex, encoding="utf-8")
    print("wrote", OUT)
    print(tex)


if __name__ == "__main__":
    main()
