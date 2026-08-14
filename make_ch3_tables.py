#!/usr/bin/env python3
"""Regenerate the six Chapter 3 primary-specification tables from one CSV.

    python thesis/make_ch3_tables.py

Source is thesis/tables/ch3_estimates.csv, written by thesis/ch3_estimates.do.
Stata is the single source of truth for every Chapter 3 estimate: the earlier
Python (statsmodels) route omitted `years_since_ofsted` from the control set,
which the documented specification includes, so every figure it produced was off
the documented spec. Rather than keep two routes and re-discover the gap, this
script rebuilds the tables from the Stata export, and nothing else may write
them.

The six tables all sit on the SAME specification -- full controls, HC3, the
predecessor-filled pre-COVID grade, late-entry schools excluded -- including the
three appendix five-outcome tables, which used to be estimated on the older
spec. That is deliberate: an appendix column that a reader compares against a
body column has to be comparable.

Each table keeps its own house style, because they were written at different
times and the chapter's cross-references and captions depend on their shape:
the two esttab-derived families report standard errors and star at
0.10/0.05/0.01, while tab_stages23_trio reports p-values and stars at
0.05/0.01/0.001. Do not unify them here; unify them in the chapter or not at
all.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "thesis" / "tables"
CSV = TABLES / "ch3_estimates.csv"

W = "gs_warmth_enacted"
S = "gs_strictness_enacted"
T = "gs_teaching_enacted"

FIVE = ["overall", "english", "maths", "ebac", "open"]
TRIO = ["overall", "english", "maths"]


def load() -> pd.DataFrame:
    return pd.read_csv(CSV)


def get(df: pd.DataFrame, spec: str, outcome: str, term: str) -> pd.Series:
    row = df[(df.spec == spec) & (df.outcome == outcome) & (df.term == term)]
    if len(row) != 1:
        raise SystemExit(f"{CSV.name}: expected 1 row for {spec}/{outcome}/"
                         f"{term}, found {len(row)}")
    return row.iloc[0]


def num(x: float, minus: str = "-") -> str:
    """Three decimals, with the file's own way of writing a leading minus."""
    s = f"{abs(x):.3f}"
    return f"{minus}{s}" if x < 0 else s


def stars_010(p: float) -> str:
    """The esttab convention: * 0.10, ** 0.05, *** 0.01."""
    for cut, mark in ((0.01, "***"), (0.05, "**"), (0.10, "*")):
        if p < cut:
            return f"\\sym{{{mark}}}"
    return ""


def stars_001(p: float) -> str:
    """The trio table's convention: * 0.05, ** 0.01, *** 0.001."""
    for cut, mark in ((0.001, "***"), (0.01, "**"), (0.05, "*")):
        if p < cut:
            return f"\\sym{{{mark}}}"
    return ""


def cell(r: pd.Series, stars=stars_010, minus: str = "-") -> str:
    return num(r["b"], minus) + stars(r["pval"])


def write(name: str, body: str) -> None:
    (TABLES / name).write_text(body, encoding="utf-8")
    print(f"wrote thesis/tables/{name}")


# ── tab_spec_ladder ──────────────────────────────────────────────────────────
def spec_ladder(df: pd.DataFrame) -> None:
    rungs = [("ladder_a", "Grade as recorded (missing dropped)"),
             ("ladder_b", "Predecessor-filled grade (primary)"),
             ("ladder_c", "Missing-grade category retained"),
             ("ladder_d", "No grade control")]
    rows = []
    for spec, label in rungs:
        w, s = get(df, spec, "overall", W), get(df, spec, "overall", S)
        rows.append(f"{label:<40} & {int(w['n']):>3d} & "
                    f"{cell(w):<15s} & {cell(s):<15s} \\\\")
        rows.append(f"{'':<40} &     & ({w['se']:.3f})        & "
                    f"({s['se']:.3f})        \\\\")
    table = "\n\\addlinespace\n".join(
        "\n".join(rows[i:i + 2]) for i in range(0, len(rows), 2))

    lw = get(df, "primary_late", "overall", W)
    ls = get(df, "primary_late", "overall", S)

    write("tab_spec_ladder.tex", rf"""\begin{{table}}[htbp]\centering
\def\sym#1{{\ifmmode^{{#1}}\else\(^{{#1}}\)\fi}}
\small
\caption{{The headline gold-standard model under four treatments of the pre-COVID
inspection-grade control. Each row is the same regression of average Progress 8 on
enacted warmth ($W$) and enacted strictness ($S$) with the full control set; the rows
differ only in how schools with a missing 2019 grade are handled. Schools with a
statutory admission age of 13 or above are excluded throughout.}}
\label{{tab:spec_ladder}}
\begin{{tabular}}{{lccc}}
\toprule
Grade-control specification & $N$ & Warmth ($W$) & Strictness ($S$) \\
\midrule
{table}
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Standard errors in parentheses.
\sym{{*}} \(p<0.10\), \sym{{**}} \(p<0.05\), \sym{{***}} \(p<0.01\).
Outcome is average Progress 8; predictors are standardised. Seven visited academies
lacked a 2019 grade under their current URN; the primary specification fills five of
them from the predecessor school's grade. Including the late-entry schools leaves the
primary estimates essentially unchanged ($W = {lw['b']:.3f}$, $p = {lw['pval']:.3f}$;
$S = {ls['b']:.3f}$, $p = {ls['pval']:.3f}$; $N = {int(lw['n'])}$).
\end{{minipage}}
\end{{table}}
""")


# ── tab_univariate_ws ────────────────────────────────────────────────────────
def univariate_ws(df: pd.DataFrame) -> None:
    def line(head: str, term_label: str, spec: str, term: str) -> str:
        rs = [get(df, spec, o, term) for o in TRIO]
        top = (f"{head:<10s} & {term_label:<16s} & "
               + " & ".join(f"{cell(r):<15s}" for r in rs) + " \\\\")
        bot = (f"{'':<10s} & {'':<16s} & "
               + " & ".join(f"({r['se']:.3f})".ljust(15) for r in rs) + " \\\\")
        return top + "\n" + bot

    n = int(get(df, "primary_stage1", "overall", W)["n"])
    body = "\n\\addlinespace\n".join([
        line("$S$ only", "Strictness ($S$)", "primary_strict", S),
        line("$W$ only", "Warmth ($W$)", "primary_warmth", W)])
    joint = "\n\\addlinespace\n".join([
        line("Joint", "Warmth ($W$)", "primary_stage1", W),
        line("Joint", "Strictness ($S$)", "primary_stage1", S)])

    write("tab_univariate_ws.tex", rf"""\begin{{table}}[htbp]\centering
\def\sym#1{{\ifmmode^{{#1}}\else\(^{{#1}}\)\fi}}
\small
\caption{{Warmth and strictness entered alone and together. Each column is a Progress 8
outcome; the first two rows enter one culture dimension at a time and the final two
rows enter both jointly, always with the full control set and the predecessor-filled
grade control. The drop from the univariate to the joint coefficients shows the two
dimensions share some variance, but each keeps an independent association when the
other is held fixed.}}
\label{{tab:univariate_ws}}
\begin{{tabular}}{{llccc}}
\toprule
Specification & Term & Overall & English & Maths \\
\midrule
{body}
\midrule
{joint}
\midrule
$N$        &                  & {n}            & {n}            & {n}            \\
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Standard errors in parentheses.
\sym{{*}} \(p<0.10\), \sym{{**}} \(p<0.05\), \sym{{***}} \(p<0.01\).
Gold-standard visited tier, late-entry schools excluded. EBacc and Open components
are reported in the chapter appendix.
\end{{minipage}}
\end{{table}}
""")


# ── tab_stages23_trio ────────────────────────────────────────────────────────
def stages23_trio(df: pd.DataFrame) -> None:
    def rows(label: str, spec: str, term: str) -> str:
        rs = [get(df, spec, o, term) for o in TRIO]
        top = (f"{label:<12s} & "
               + " & ".join(cell(r, stars_001, "$-$") for r in rs) + " \\\\")
        bot = ("             & "
               + " & ".join(f"({r['pval']:.3f})" for r in rs) + " \\\\")
        return top + "\n" + bot

    r2 = " & ".join(f"{get(df, 'primary_stage2', o, T)['r2']:.3f}"
                    for o in TRIO)
    n = int(get(df, "primary_stage1", "overall", W)["n"])

    # The \def\sym line is load-bearing: \sym is defined per-file by esttab, and
    # the hand-written version of this table used it undefined, which halts
    # pdflatex outright. Do not drop it when reformatting.
    write("tab_stages23_trio.tex", rf"""\begin{{table}}[htbp]\centering
\def\sym#1{{\ifmmode^{{#1}}\else\(^{{#1}}\)\fi}}
\small
\caption{{Stages 2 and 3 under the primary specification: teaching quality as
the sole culture predictor (Stage~2), and teaching quality added to the
warmth-and-strictness model (Stage~3). Coefficients are per standard
deviation of the predictor; HC3 robust standard errors; $n = {n}$. The full
five-outcome versions, estimated on the same specification, are reported
in the appendix.}}
\label{{tab:stages23_trio}}
\begin{{tabular}}{{lccc}}
\toprule
 & \textit{{Overall P8}} & \textit{{English}} & \textit{{Maths}} \\
\midrule
\multicolumn{{4}}{{l}}{{\textit{{Stage 2: teaching quality only}}}} \\
\addlinespace[2pt]
{rows("Teaching $T$", "primary_stage2", T)}
$R^2$        & {r2} \\
\addlinespace[6pt]
\multicolumn{{4}}{{l}}{{\textit{{Stage 3: warmth, strictness and teaching}}}} \\
\addlinespace[2pt]
{rows("Warmth $W$", "primary_stage3", W)}
{rows("Strictness $S$", "primary_stage3", S)}
{rows("Teaching $T$", "primary_stage3", T)}
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{0.8\linewidth}}
\vspace{{4pt}}\scriptsize
\textit{{Notes}}: $p$-values in parentheses. \sym{{*}} $p<0.05$, \sym{{**}}
$p<0.01$, \sym{{***}} $p<0.001$. Primary specification throughout: full
control set, predecessor-filled pre-COVID grade, late-entry schools
excluded.
\end{{minipage}}
\end{{table}}
""")


# ── tab_main_results_s1 / s2 / s3 ────────────────────────────────────────────
def main_results(df: pd.DataFrame) -> None:
    specs = [
        ("tab_main_results_s1.tex", "primary_stage1", "tab:main_results_s1",
         "Stage 1: Total culture effect ($W + S$)",
         [("Warmth ($W$)", W), ("Strictness ($S$)", S)]),
        ("tab_main_results_s2.tex", "primary_stage2", "tab:main_results_s2",
         "Stage 2: Teaching quality benchmark ($T$)",
         [("Teaching quality ($T$)", T)]),
        ("tab_main_results_s3.tex", "primary_stage3", "tab:main_results_s3",
         "Stage 3: Culture net of teaching ($W + S + T$)",
         [("Warmth ($W$)", W), ("Strictness ($S$)", S),
          ("Teaching quality ($T$)", T)]),
    ]
    # esttab's own column geometry, reproduced so the diff against the previous
    # generation of these tables is a diff in the numbers and nothing else: a
    # 12-character right-aligned value followed by a 9-character star field.
    def col(text: str, star: str = " " * 9) -> str:
        return f"{text:>12}{star}"

    def starfield(p: float) -> str:
        for cut, mark in ((0.01, "***"), (0.05, "**"), (0.10, "*")):
            if p < cut:
                return f"\\sym{{{mark}}}".ljust(9)
        return " " * 9

    for name, spec, label, title, terms in specs:
        blocks = []
        for term_label, term in terms:
            rs = [get(df, spec, o, term) for o in FIVE]
            top = (f"{term_label:<20s}&"
                   + "&".join(col(num(r["b"]), starfield(r["pval"]))
                              for r in rs) + "\\\\")
            bot = (f"{'':<20s}&"
                   + "&".join(col(f"({r['se']:.3f})") for r in rs) + "\\\\")
            blocks.append(top + "\n" + bot)
        head = get(df, spec, "overall", terms[0][1])
        r2 = "&".join(col(f"{get(df, spec, o, terms[0][1])['r2']:.3f}")
                      for o in FIVE)
        ns = "&".join(col(str(int(head["n"]))) for _ in FIVE)

        write(name, rf"""\begin{{table}}[htbp]\centering
\def\sym#1{{\ifmmode^{{#1}}\else\(^{{#1}}\)\fi}}
\caption{{{title}. Primary specification: full control set,
predecessor-filled pre-COVID inspection grade, late-entry schools excluded ---
identical to the trio reported in the chapter body, extended to all five
Progress~8 components.}}
\label{{{label}}}
\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{l*{{5}}{{c}}}}
\toprule
                    &     Overall         &     English         &       Maths         &        EBaC         &        Open         \\
\midrule
{(chr(10) + chr(92) + "addlinespace" + chr(10)).join(blocks)}
\midrule
$N$                 &{ns}\\
$R^2$               &{r2}\\
\bottomrule
\multicolumn{{6}}{{l}}{{\footnotesize Standard errors in parentheses}}\\
\multicolumn{{6}}{{l}}{{\footnotesize \sym{{*}} \(p<0.10\), \sym{{**}} \(p<0.05\), \sym{{***}} \(p<0.01\)}}\\
\end{{tabular}}%
}}
\end{{table}}
""")


def main() -> int:
    df = load()
    spec_ladder(df)
    univariate_ws(df)
    stages23_trio(df)
    main_results(df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
