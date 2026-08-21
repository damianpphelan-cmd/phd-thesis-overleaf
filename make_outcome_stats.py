#!/usr/bin/env python3
"""Regenerate thesis/tables/tab_outcome_stats.tex from analysis_dataset.csv.

The committed version of this table was corrupt in two independent ways, and
the script that produced it no longer exists, so it is rebuilt here.

  1. LaTeX corruption. Whatever wrote it used a non-raw Python string, so every
     ``\\a`` became a BEL byte (0x07): ``\\addlinespace`` printed as
     ``ddlinespace``, ``\\approx`` as ``pprox``, and every ``\\\\`` row
     terminator collapsed to a single backslash, so no row ever ended. BEL is
     an invalid character to TeX; combined with the broken alignment this is a
     fatal compile error, which is why the thesis stopped producing a PDF.
  2. Data corruption. Every Tier 1 and Tier 2 cell read ``0`` or ``nan``. The
     underlying data was never missing -- Tier 1 has 102 schools and Tier 2
     has 299 on the P8 components -- so the filter in the lost script was
     simply wrong.

    python thesis/make_outcome_stats.py            # write the table
    python thesis/make_outcome_stats.py --check    # verify, change nothing

Tier definitions follow tab_control_stats.tex: Tier 2 is the whole interviewed
sample (303) and therefore contains Tier 1 (102); National is every school.
"""
from __future__ import annotations

import argparse
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "thesis" / "tables" / "tab_outcome_stats.tex"
OUT_FULL = ROOT / "thesis" / "tables" / "tab_outcome_stats_full.tex"

# (row label, column in analysis_dataset.csv). The body table carries the
# outcomes the chapter reports (overall, English, Maths); the appendix version
# adds EBacc and Open (Damian, 17 Aug 2026).
OUTCOMES_BODY = [
    ("P8 Overall (2-yr avg)",   "p8mea_avg"),
    ("P8 English (2-yr avg)",   "p8meaeng_avg"),
    ("P8 Maths (2-yr avg)",     "p8meamat_avg"),
    ("Att8 English (2024--25)", "att8screng_2425"),
    ("Att8 Maths (2024--25)",   "att8scrmat_2425"),
]
OUTCOMES_FULL = [
    ("P8 Overall (2-yr avg)",   "p8mea_avg"),
    ("P8 English (2-yr avg)",   "p8meaeng_avg"),
    ("P8 Maths (2-yr avg)",     "p8meamat_avg"),
    ("P8 EBacc (2-yr avg)",     "p8meaebac_avg"),
    ("P8 Open (2-yr avg)",      "p8meaopen_avg"),
    ("Att8 English (2024--25)", "att8screng_2425"),
    ("Att8 Maths (2024--25)",   "att8scrmat_2425"),
    ("Att8 EBacc (2024--25)",   "att8screbac_2425"),
    ("Att8 Open (2024--25)",    "att8scropen_2425"),
]


def build(OUTCOMES=OUTCOMES_BODY, full=False) -> str:
    d = pd.read_csv(ROOT / "analysis_dataset.csv", encoding="utf-8-sig",
                    low_memory=False)
    tier = d["gs_data_tier"].fillna("national")

    tiers = [
        (r"Visited (Tier~1)",     tier == "full"),
        (r"Interviewed (Tier~2)", tier.isin(["full", "interview_only"])),
        (r"National",             pd.Series(True, index=d.index)),
    ]

    blocks = []
    for label, col in OUTCOMES:
        lines = []
        for i, (tier_label, mask) in enumerate(tiers):
            v = pd.to_numeric(d.loc[mask, col], errors="coerce").dropna()
            head = r"\multirow{3}{*}{%s}" % label if i == 0 else ""
            lines.append(
                r"    %s & %s & %d & %.3f & %.3f & %.3f & %.3f \\"
                % (head, tier_label, len(v), v.mean(), v.std(), v.min(), v.max())
            )
        blocks.append("\n".join(lines))

    body = ("\n" + r"    \addlinespace[3pt]" + "\n").join(blocks)

    return r"""\begin{table}[htbp]
  \centering
  \caption{Summary statistics: Progress~8 @WHICH@outcomes by data tier}
  \label{tab:outcome_stats@LABTAIL@}
  \footnotesize\setlength{\tabcolsep}{4pt}
  \begin{tabular}{llrrrrr}
    \toprule
    Outcome & Tier & $N$ & Mean & SD & Min & Max \\
    \midrule
@BODY@
    \bottomrule
  \end{tabular}
  \begin{minipage}{\linewidth}
    \vspace{2pt}
    \footnotesize
    \textit{Notes:} P8 outcomes are 2-year averages of 2022--23 and 2023--24 component scores where both
    years are available (both years are present for every school in the current data,
    so the single-year fallback never binds). Att8 2024--25 components are the
    contemporaneous robustness outcome; no Progress~8 is available for this cohort because the cohort were
    in Year~6 in 2019--20 when Key Stage~2 assessments were cancelled. Tier~2 is the full interviewed
    sample and therefore contains Tier~1; both are subsets of the national sample, hence the different
    $N$ values across tiers.
  \end{minipage}
\end{table}
""".replace("@BODY@", body) \
   .replace("@WHICH@", "and Attainment~8 outcomes, all components, " if full else "") \
   .replace("@LABTAIL@", "_full" if full else "")


def audit(text: str) -> list[str]:
    """Catch the corruption class that broke the previous version."""
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
    tex_full = build(OUTCOMES_FULL, full=True)
    problems = audit(tex) + audit(tex_full)
    if problems:
        print("refusing to write -- generated table is malformed:")
        for p in problems:
            print("  " + p)
        return 2

    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        current_full = OUT_FULL.read_text(encoding="utf-8") if OUT_FULL.exists() else ""
        stale = audit(current) + audit(current_full)
        if stale:
            print(f"{OUT.name}/{OUT_FULL.name} corrupt on disk:")
            for p in stale:
                print("  " + p)
            return 1
        if current != tex or current_full != tex_full:
            print(f"{OUT.name}/{OUT_FULL.name} differ from what the data produces "
                  f"-- run: python thesis/make_outcome_stats.py")
            return 1
        print(f"{OUT.name} and {OUT_FULL.name} match analysis_dataset.csv")
        return 0

    OUT.write_text(tex, encoding="utf-8")
    OUT_FULL.write_text(tex_full, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} and {OUT_FULL.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
