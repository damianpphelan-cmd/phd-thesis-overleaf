#!/usr/bin/env python3
r"""Build thesis/tables/tab_national_strictness.tex from a7_estimates.csv.

The published national specification omits the Ofsted grade dummy "to avoid
conditioning on a downstream confounder". That is defensible but it is not the
conservative reading, and the obvious examiner challenge is that the strictness
coefficient partly measures "Ofsted approved of this school" -- the score is
read from the same inspection report that produced the grade.

Panel B answers that challenge by adding the pre-COVID (2019) Ofsted grade,
which is already a control in the primary Tier~1 specification, so no new
variable enters the thesis.

Regenerate the estimates first (the do-file path must be absolute):

    "C:\Program Files\StataNow19\StataMP-64.exe" /e do "...\thesis\a7_national_strictness.do"
    python thesis/make_national_strictness.py
    python thesis/make_national_strictness.py --check   # verify, change nothing

Written with raw strings throughout: the previous generation of table scripts
used ordinary strings, so `\a` became a BEL byte and `\\` collapsed to a single
backslash, which is what stopped the thesis producing a PDF at all. audit()
below refuses to write output in that state.
"""
from __future__ import annotations

import argparse
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
EST = ROOT / "thesis" / "tables" / "a7_estimates.csv"
OUT = ROOT / "thesis" / "tables" / "tab_national_strictness.tex"
OUT_FULL = ROOT / "thesis" / "tables" / "tab_national_strictness_full.tex"

# The body table carries the three outcomes the chapter reports; the appendix
# version carries all five (Damian, 17 Aug 2026: EBaC and Open to the appendix).
COLS_BODY = ["Overall", "English", "Maths"]
COLS_FULL = ["Overall", "English", "Maths", "EBaC", "Open"]

PANELS = [
    ("nograde", r"Panel A: published specification (Ofsted grade omitted)"),
    ("grade19", r"Panel B: adding the pre-COVID (2019) Ofsted grade"),
]

ROW_LABEL = r"Strictness (Ofsted LLM, per SD)"


def stars(p: float) -> str:
    """Significance markers matching the footnote: 0.10 / 0.05 / 0.01."""
    if p < 0.01:
        return r"\sym{***}"
    if p < 0.05:
        return r"\sym{**}"
    if p < 0.10:
        return r"\sym{*}"
    return ""


def build(COLS=COLS_BODY, full=False) -> str:
    est = pd.read_csv(EST)
    est = est.set_index(["spec", "outcome"])

    missing = [(s, c) for s, _ in PANELS for c in COLS
               if (s, c) not in est.index]
    if missing:
        raise SystemExit(f"a7_estimates.csv is missing estimates for {missing}")

    body = []
    for i, (spec, title) in enumerate(PANELS):
        rows = est.loc[spec]
        if i:
            body.append(r"\addlinespace[6pt]")
        body.append(r"\multicolumn{%d}{l}{\textit{%s}} \\" % (len(COLS) + 1, title))
        body.append(
            r"%s & %s \\" % (ROW_LABEL, " & ".join(
                r"%.3f%s" % (rows.loc[c, "b"], stars(rows.loc[c, "pval"]))
                for c in COLS))
        )
        body.append(
            r" & %s \\" % " & ".join(
                r"(%.3f)" % rows.loc[c, "se"] for c in COLS)
        )
        body.append(
            r"$N$ & %s \\" % " & ".join(
                r"{:,}".format(int(rows.loc[c, "n"])).replace(",", r"{,}")
                for c in COLS)
        )
        body.append(
            r"$R^2$ & %s \\" % " & ".join(
                r"%.3f" % rows.loc[c, "r2"] for c in COLS)
        )

    n_a = int(est.loc[("nograde", "Overall"), "n"])
    n_b = int(est.loc[("grade19", "Overall"), "n"])
    dropped = n_a - n_b

    return r"""\begin{table}[htbp]\centering
\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}
\caption{National extension: Ofsted LLM strictness and Progress~8@CAPTAIL@}
\label{tab:national_strictness@LABTAIL@}
\resizebox{\textwidth}{!}{%
\begin{tabular}{l*{@NCOL@}{c}}
\toprule
 & @HEAD@ \\
\midrule
@BODY@
\bottomrule
\end{tabular}%
}
\begin{minipage}{\linewidth}
  \vspace{4pt}
  \footnotesize
  \textit{Notes:} Heteroskedasticity-robust (HC3) standard errors in
  parentheses. \sym{*} \(p<0.10\), \sym{**} \(p<0.05\), \sym{***} \(p<0.01\).
  The strictness score is standardised over the estimation sample, so
  coefficients are per standard deviation of the score; late-entry schools are
  excluded. All specifications control for prior attainment (KS2), FSM, EAL, SEN, log
  cohort size, years since inspection, academy status, urban location and
  selective status. Panel~A is the specification reported in the text, which
  omits the Ofsted grade because the strictness score is read from the same
  inspection report. Panel~A includes @NA@ schools. Panel~B adds the predecessor-filled pre-COVID
  (2019) overall Ofsted grade as a set of dummies---the same control used in
  the primary Tier~1 specification---and is estimated on the @NB@ schools with
  a 2019 grade on record, @DROPPED@ fewer than Panel~A. The strictness
  coefficient is materially unchanged throughout, indicating that it is not
  simply recording Ofsted's overall approval of the school.
\end{minipage}
\end{table}
""".replace("@BODY@", "\n".join(body)) \
   .replace("@NA@", r"{:,}".format(n_a).replace(",", r"{,}")) \
   .replace("@NB@", r"{:,}".format(n_b).replace(",", r"{,}")) \
   .replace("@DROPPED@", str(dropped)) \
   .replace("@NCOL@", str(len(COLS))) \
   .replace("@HEAD@", " & ".join(COLS)) \
   .replace("@CAPTAIL@", " (all five outcomes)" if full else "") \
   .replace("@LABTAIL@", "_full" if full else "")


def audit(text: str) -> list[str]:
    """Catch the non-raw-string corruption class that once broke the build."""
    problems = []
    for i, line in enumerate(text.split("\n"), 1):
        bad = sorted({hex(ord(c)) for c in line
                      if ord(c) < 32 and c not in "\t\r"})
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
    tex_full = build(COLS_FULL, full=True)
    problems = audit(tex) + audit(tex_full)
    if problems:
        print("refusing to write -- generated table is malformed:")
        for p in problems:
            print("  " + p)
        return 2

    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        stale = audit(current)
        if stale:
            print(f"{OUT.name} is corrupt on disk:")
            for p in stale:
                print("  " + p)
            return 1
        current_full = OUT_FULL.read_text(encoding="utf-8") if OUT_FULL.exists() else ""
        if current != tex or current_full != tex_full:
            print(f"{OUT.name}/{OUT_FULL.name} differ from the Stata estimates "
                  f"-- run: python thesis/make_national_strictness.py")
            return 1
        print(f"{OUT.name} and {OUT_FULL.name} match {EST.name}")
        return 0

    OUT.write_text(tex, encoding="utf-8")
    OUT_FULL.write_text(tex_full, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} and {OUT_FULL.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
