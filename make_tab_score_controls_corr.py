"""Regenerate tables/tab_score_controls_corr.tex from analysis_dataset.csv.

Hand-maintained and stale on two counts: $N = 102$ predates the URN join, and
two of its five columns were the 60/40 composite scores withdrawn on
5 Aug 2026. The composite columns are replaced by the espoused (interview)
scores, which is the comparison the table was really making -- observation
against self-report -- now that the two are kept separate.

Run:  python thesis/make_tab_score_controls_corr.py
"""

from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "tables" / "tab_score_controls_corr.tex"

SCORES = [
    ("gs_warmth_enacted",      r"$W_{\text{enac}}$"),
    ("gs_strictness_enacted",  r"$S_{\text{enac}}$"),
    ("gs_teaching_enacted",    r"$T_{\text{enac}}$"),
    ("gs_warmth_espoused",     r"$W_{\text{esp}}$"),
    ("gs_strictness_espoused", r"$S_{\text{esp}}$"),
]

CONTROLS = [
    ("ks2",                "KS2"),
    ("fsm",                r"FSM\%"),
    ("eal",                r"EAL\%"),
    ("sen",                r"SEN\%"),
    ("log_size",           "Log size"),
    ("academy",            "Academy"),
    ("urban_bin",          "Urban"),
    ("selective",          "Selective"),
    ("years_since_ofsted", "Yrs Ofsted"),
]

BOLD = 0.30


def numeric(s: pd.Series) -> pd.Series:
    """Some control columns arrive as strings ('86.00%', '1,234')."""
    if s.dtype.kind in "fi":
        return s
    return pd.to_numeric(
        s.astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False),
        errors="coerce",
    )


def main():
    d = pd.read_csv(BASE / "analysis_dataset.csv", low_memory=False)
    g = d[d["gs_data_tier"] == "full"].copy()
    for col, _ in CONTROLS:
        g[col] = numeric(g[col])
    n = len(g)

    rows, biggest = [], (0.0, "", "")
    for col, label in CONTROLS:
        cells = []
        for sc, _ in SCORES:
            m = g[col].notna() & g[sc].notna()
            r = g.loc[m, col].corr(g.loc[m, sc])
            txt = f"{r:+.2f}".replace("-", "$-$")
            cells.append(rf"\textbf{{{txt}}}" if abs(r) >= BOLD else txt)
            if abs(r) > abs(biggest[0]):
                biggest = (r, label, sc)
        rows.append(f"    {label} & " + " & ".join(cells) + r" \\")

    header = " & ".join(lab for _, lab in SCORES)
    body = "\n".join(rows)

    OUT.write_text(rf"""\begin{{table}}[htbp]
  \centering
  \caption{{Pairwise correlations: culture scores and control variables (Tier~1, $N={n}$)}}
  \label{{tab:score_controls_corr}}
  \small
  \begin{{tabular}}{{lrrrrr}}
    \toprule
    Control & {header} \\
    \midrule
{body}
    \bottomrule
  \end{{tabular}}
  \begin{{minipage}}{{\linewidth}}
    \vspace{{2pt}}
    \footnotesize
    \textit{{Notes:}} Pearson correlation coefficients. $W_{{\text{{enac}}}}$,
    $S_{{\text{{enac}}}}$ and $T_{{\text{{enac}}}}$ are the enacted culture scores
    built from school visit observations only (mean of $W_1, W_2$; $S_1, S_2$;
    $T_1$, each scaled 0--10). $W_{{\text{{esp}}}}$ and $S_{{\text{{esp}}}}$ are the
    espoused scores built from the headteacher interview. The two sets share no
    component; they are reported side by side rather than averaged, because
    the two are correlated at only $r = \GoldWarmthSplit$ (warmth) and
    $\GoldStrictnessSplit$ (strictness).
    Bold entries indicate $|r| \geq {BOLD:.2f}$. $N$ varies slightly by column due to missing
    control values; all correlations use the Tier~1 sample of {n} visited schools.
  \end{{minipage}}
\end{{table}}
""", encoding="utf-8")

    print(f"wrote {OUT.relative_to(BASE)}  (N = {n})")
    print(f"  largest |r| = {biggest[0]:+.2f}  ({biggest[1]} x {biggest[2]})")
    short = [sc.replace("gs_", "").replace("_", " ")[:11] for sc, _ in SCORES]
    print("  " + " " * 13 + "  ".join(f"{s:>11}" for s in short))
    for col, label in CONTROLS:
        vals = [
            f"{g.loc[g[col].notna() & g[sc].notna(), col].corr(g[sc]):>+11.2f}"
            for sc, _ in SCORES
        ]
        print(f"  {label.replace(chr(92), ''):<13}" + "  ".join(vals))


if __name__ == "__main__":
    main()
