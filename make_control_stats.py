#!/usr/bin/env python3
"""Regenerate thesis/tables/tab_control_stats.tex from analysis_dataset.csv.

This table had no generator. It was maintained by hand, and so it froze: it
still reported Tier 1 as 102 schools and Tier 2 as 303 long after the URN join
took them to 103 and 304, and its Ofsted-grade block still summed to the old
95-school regression sample rather than 96. A hand-maintained table cannot be
re-run, so it silently drifts away from the data every time the dataset moves.

It also carried a substantive error that only became visible once the numbers
were derived rather than typed. The row read "Selective admissions -- 93.1%",
which is not credible for English secondaries (roughly 5% are grammar schools).
The `selective` variable was built with a substring test, and "Non-selective"
contains "selective", so the flag was set for both categories; the table was
faithfully reporting a variable that meant "admissions policy is recorded".
build_analysis_dataset.py now matches the category exactly, and the row below
reports the selective share, which is what the label always claimed.

    python thesis/make_control_stats.py            # write the table
    python thesis/make_control_stats.py --check    # verify, change nothing

Tier definitions match thesis/make_outcome_stats.py: Tier 2 is the whole
interviewed sample and therefore contains Tier 1.
"""
from __future__ import annotations

import argparse
import pathlib

import pandas as pd

from fix_tables import move_caption_above

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "thesis" / "tables" / "tab_control_stats.tex"

# (row label, column) for the continuous block, in table order.
CONTINUOUS = [
    (r"Mean KS2 score",   "ks2"),
    (r"FSM eligible (\%)", "fsm"),
    (r"EAL share (\%)",    "eal"),
    (r"SEN share (\%)",    "sen"),
    (r"Log school size",  "log_size"),
    (r"Yrs since Ofsted", "years_since_ofsted"),
]

BINARY = [
    (r"Academy school",       "academy"),
    (r"Urban location",       "urban_bin"),
    (r"Selective admissions", "selective"),
]

GRADES = [
    (r"Grade~1 (Outstanding)",          1),
    (r"Grade~2 (Good)",                 2),
    (r"Grade~3 (Requires improvement)", 3),
    (r"Grade~4 (Inadequate)",           4),
]


def numeric(d: pd.DataFrame, col: str) -> pd.Series:
    """EAL and SEN arrive as percent strings ("57.70%"); the rest are numeric.

    Test for "not already numeric" rather than for the object dtype: on pandas 3
    these columns load as the `str` dtype, so an `== object` check silently
    misses them and every EAL and SEN cell comes back NaN.
    """
    s = d[col]
    if not pd.api.types.is_numeric_dtype(s):
        s = s.astype("string").str.replace("%", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def build() -> str:
    d = pd.read_csv(ROOT / "analysis_dataset.csv", encoding="utf-8-sig",
                    low_memory=False)
    tier = d["gs_data_tier"].fillna("national")
    t1 = tier == "full"
    t2 = tier.isin(["full", "interview_only"])
    n1, n2 = int(t1.sum()), int(t2.sum())

    rows = [r"    \multicolumn{7}{l}{\textit{Pupil composition and prior attainment}} \\"]
    for label, col in CONTINUOUS:
        cells = []
        for mask in (t1, t2):
            v = numeric(d, col)[mask].dropna()
            cells.append(r"%d & %.3f & %.3f" % (len(v), v.mean(), v.std())
                         if col in ("ks2", "log_size", "years_since_ofsted")
                         else r"%d & %.1f & %.1f" % (len(v), v.mean(), v.std()))
        rows.append(r"    \quad %s & %s & %s \\" % (label, cells[0], cells[1]))

    rows.append(r"    \addlinespace[3pt]")
    rows.append(r"    \multicolumn{7}{l}{\textit{School characteristics (share)}} \\")
    for label, col in BINARY:
        cells = []
        for mask in (t1, t2):
            v = numeric(d, col)[mask].dropna()
            cells.append(r"%d & \multicolumn{2}{c}{%.1f\%%}" % (len(v), 100 * v.mean()))
        rows.append(r"    \quad %s & %s & %s \\" % (label, cells[0], cells[1]))

    rows.append(r"    \addlinespace[3pt]")
    rows.append(r"    \multicolumn{7}{l}{\textit{Pre-COVID Ofsted grade "
                r"(as at 31~August~2019)}} \\")
    g1 = numeric(d, "ofsted_grade_2019")[t1]
    g2 = numeric(d, "ofsted_grade_2019")[t2]
    for label, g in GRADES:
        cells = []
        for gs in (g1, g2):
            k, tot = int((gs == g).sum()), int(gs.notna().sum())
            cells.append(r"%d & \multicolumn{2}{c}{%.1f\%%}" % (k, 100 * k / tot))
        rows.append(r"    \quad %s & %s & %s \\" % (label, cells[0], cells[1]))
    rows.append(r"    \quad No pre-COVID grade & %d & & & %d & & \\"
                % (int(g1.isna().sum()), int(g2.isna().sum())))

    body = "\n".join(rows)
    graded1, graded2 = int(g1.notna().sum()), int(g2.notna().sum())

    return r"""\begin{table}[htbp]
  \centering
  \caption{Summary statistics: control variables for the visited and
  interviewed samples. The interviewed sample contains the visited schools;
  within a column, $N$ falls below the sample size only where a control is
  missing for a school.}
  \label{tab:control_stats}
  \small
  \begin{tabular}{lrrrrrr}
    \toprule
    & \multicolumn{3}{c}{Visited ($N=@N1@$)} & \multicolumn{3}{c}{Interviewed ($N=@N2@$)} \\
    \cmidrule(lr){2-4}\cmidrule(lr){5-7}
    Variable & $N$ & Mean & SD & $N$ & Mean & SD \\
    \midrule
@BODY@
    \bottomrule
  \end{tabular}
  \begin{minipage}{\linewidth}
    \vspace{2pt}
    \footnotesize
    \textit{Notes:} KS2 is the mean scaled score of the 2023--24 KS4 cohort at Key Stage~2.
    FSM is the share eligible for the pupil premium (FSM6 definition); EAL and SEN are KS4
    cohort shares from the 2023--24 performance tables. Selective admissions is the share of
    schools recorded as selective in the performance tables. Pre-COVID Ofsted grade is the
    overall effectiveness grade from the Ofsted Management Information snapshot as at
    31~August~2019, used as the primary endogeneity-safe control; the contemporary 2024 grade
    enters sensitivity analyses only. Grade percentages are shares of the graded schools
    (@G1@ visited, @G2@ interviewed), not of the sample. The primary specification
    estimates on 99 of the @N1@ visited schools, because predecessor grades fill four
    of the seven schools without one; see the specification-ladder notes.
    The @N1@ visited schools all have both visit and interview data; the interviewed
    sample (@N2@ schools) includes them.
  \end{minipage}
\end{table}
""".replace("@BODY@", body).replace("@N1@", str(n1)).replace("@N2@", str(n2)) \
   .replace("@G1@", str(graded1)).replace("@G2@", str(graded2))


def audit(text: str) -> list[str]:
    problems = []
    for i, line in enumerate(text.split("\n"), 1):
        bad = sorted({hex(ord(c)) for c in line if ord(c) < 32 and c != "\t"})
        if bad:
            problems.append(f"line {i}: control characters {bad}")
        stripped = line.rstrip()
        if stripped.endswith("\\") and not stripped.endswith("\\\\"):
            problems.append(f"line {i}: row ends in a single backslash: "
                            f"{stripped[-40:]!r}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="compare against the file on disk; do not write")
    args = ap.parse_args()

    tex = build()
    tex, _ = move_caption_above(tex)
    problems = audit(tex)
    if problems:
        print("refusing to write -- generated table is malformed:")
        for p in problems:
            print("  " + p)
        return 2

    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != tex:
            print(f"{OUT.name} differs from what the data produces "
                  f"-- run: python thesis/make_control_stats.py")
            return 1
        print(f"{OUT.name} matches analysis_dataset.csv")
        return 0

    OUT.write_text(tex, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
