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

All tables report standard errors in parentheses and star at 0.10/0.05/0.01
(unified 21 Aug 2026 on referee advice; tab_stages23_trio and
tab_robustness_overall previously starred at 0.05/0.01/0.001, with the trio
table showing p-values in parentheses).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from fix_tables import move_caption_below

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "thesis" / "tables"
CSV = TABLES / "ch3_estimates.csv"

W = "z_gs_warmth_enacted"
S = "z_gs_strictness_enacted"
T = "z_gs_teaching_enacted"

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


def cell(r: pd.Series, stars=stars_010, minus: str = "-") -> str:
    return num(r["b"], minus) + stars(r["pval"])


def write(name: str, body: str) -> None:
    # Float convention: tabular first, then \caption + \label, then notes.
    body, _ = move_caption_below(body)
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
\caption{{The primary specification on the visited schools under four treatments of the pre-COVID
inspection-grade control. Each row is the same regression of average Progress 8 on
enacted warmth ($W$) and enacted strictness ($S$), each per standard deviation, with the
full control set; the rows
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
lacked a 2019 grade under their current URN; of the five in the estimation sample,
four are filled from the predecessor school's grade (a fifth predecessor grade
belongs to a school excluded for a missing control). Including the late-entry
schools leaves the primary estimates essentially unchanged ($W = {lw['b']:.3f}$, $p = {lw['pval']:.3f}$;
$S = {ls['b']:.3f}$, $p = {ls['pval']:.3f}$; $N = {int(lw['n'])}$ --- one of the two late-entry
schools lacks a fillable grade, so $N$ rises by one). The filled and category-retained
rows print identical estimates because the retained category contains a single school,
which its own dummy fits exactly.
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
        line("$S$ only", "Strictness ($S$)", "primary_strictonly", S),
        line("$W$ only", "Warmth ($W$)", "primary_warmthonly", W)])
    joint = "\n\\addlinespace\n".join([
        line("Joint", "Warmth ($W$)", "primary_stage1", W),
        line("Joint", "Strictness ($S$)", "primary_stage1", S)])

    write("tab_univariate_ws.tex", rf"""\begin{{table}}[htbp]\centering
\def\sym#1{{\ifmmode^{{#1}}\else\(^{{#1}}\)\fi}}
\small
\caption{{Warmth and strictness entered alone and together. Each column is a Progress 8
outcome; the first two rows enter one culture dimension at a time and the final two
rows enter both jointly (coefficients per standard deviation), always with the full
control set and the predecessor-filled
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
Visited sample, late-entry schools excluded. EBacc and Open components
are reported in the chapter appendix.
\end{{minipage}}
\end{{table}}
""")


# ── tab_stages23_trio ────────────────────────────────────────────────────────
def stages23_trio(df: pd.DataFrame) -> None:
    def rows(label: str, spec: str, term: str) -> str:
        rs = [get(df, spec, o, term) for o in TRIO]
        top = (f"{label:<12s} & "
               + " & ".join(cell(r, stars_010, "$-$") for r in rs) + " \\\\")
        bot = ("             & "
               + " & ".join(f"({r['se']:.3f})" for r in rs) + " \\\\")
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
\textit{{Notes}}: Standard errors in parentheses. \sym{{*}} \(p<0.10\),
\sym{{**}} \(p<0.05\), \sym{{***}} \(p<0.01\). Primary specification throughout: full
control set, predecessor-filled pre-COVID grade, late-entry schools
excluded.
\end{{minipage}}
\end{{table}}
""")


# ── tab_main_results_s1 / s2 / s3 ────────────────────────────────────────────
def main_results(df: pd.DataFrame) -> None:
    specs = [
        ("tab_main_results_s1.tex", "primary_stage1", "tab:main_results_s1",
         "Stage 1: Total culture association ($W + S$)",
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
                    &     Overall         &     English         &       Maths         &       EBacc         &        Open         \\
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


# ── tab_enacted_espoused ─────────────────────────────────────────────────────
def enacted_espoused(df: pd.DataFrame) -> None:
    """Rebuilt 25 Aug 2026 from ch3_estimates.csv, replacing the stale esttab
    version (old instrument, no Overall column, n=96 throughout, W12/S34
    notation). The chapter prose quotes the primary_espoused overall row
    (warmth 0.051, p=0.29; strictness 0.120, p=0.018; n=99).

    ch3_estimates.csv carries the espoused models under two specs: the primary
    specification (predecessor-filled pre-COVID grade; n=99) exists for
    overall, english and maths only; ebac and open exist only under the
    unfilled-grade variant of the same control set (espoused_t1; n=96). The
    N row and the notes state both.
    """
    WE, SE = "z_gs_warmth_espoused", "z_gs_strictness_espoused"
    spec_for = {"overall": "primary_espoused", "english": "primary_espoused",
                "maths": "primary_espoused", "ebac": "espoused_t1",
                "open": "espoused_t1"}

    def col(text: str, star: str = " " * 9) -> str:
        return f"{text:>12}{star}"

    def starfield(p: float) -> str:
        for cut, mark in ((0.01, "***"), (0.05, "**"), (0.10, "*")):
            if p < cut:
                return f"\\sym{{{mark}}}".ljust(9)
        return " " * 9

    blocks = []
    for term_label, term in [("Espoused warmth", WE),
                             ("Espoused strictness", SE)]:
        rs = [get(df, spec_for[o], o, term) for o in FIVE]
        top = (f"{term_label:<20s}&"
               + "&".join(col(num(r["b"]), starfield(r["pval"]))
                          for r in rs) + "\\\\")
        bot = (f"{'':<20s}&"
               + "&".join(col(f"({r['se']:.3f})") for r in rs) + "\\\\")
        blocks.append(top + "\n" + bot)
    r2 = "&".join(col(f"{get(df, spec_for[o], o, WE)['r2']:.3f}")
                  for o in FIVE)
    ns = "&".join(col(str(int(get(df, spec_for[o], o, WE)["n"])))
                  for o in FIVE)

    write("tab_enacted_espoused.tex", rf"""\begin{{table}}[htbp]\centering
\def\sym#1{{\ifmmode^{{#1}}\else\(^{{#1}}\)\fi}}
\caption{{Espoused culture and Progress~8. Each column regresses the named
Progress~8 component on espoused warmth and espoused strictness --- the
standardised headteacher-interview statement-battery scores --- with the full
control set, on the visited schools. The Overall, English and Maths columns
use the primary specification (predecessor-filled pre-COVID inspection grade,
late-entry schools excluded; $n=99$); the EBacc and Open columns are estimated
on the same control set before the predecessor-grade fill ($n=96$), the only
form in which those components are available.}}
\label{{tab:enacted_espoused}}
\resizebox{{\textwidth}}{{!}}{{%
\begin{{tabular}}{{l*{{5}}{{c}}}}
\toprule
                    &     Overall         &     English         &       Maths         &       EBacc         &        Open         \\
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


# ── tab_robustness_overall ───────────────────────────────────────────────────
def robustness_overall(df: pd.DataFrame) -> None:
    """Regenerated 17 Aug 2026 from the primary-spec rob_* rows.

    The previous version was built from the notebook under the OLD spec (n=96,
    original grades, no late-entry exclusion), and its 'Att8 2425' column was
    the SUM of the four Attainment-8 buckets while the do-file's 'att8' row was
    the English bucket alone -- the source of a factor-of-four disagreement.
    Both outcomes are now named explicitly and estimated on one specification.
    """
    cols = [("primary_stage1", "Primary", "p8mea_avg"),
            ("rob_nograde", "No grade", "p8mea_avg"),
            ("rob_singleyear", "2023--24 only", "p8mea_2324"),
            ("rob_semh", "SEMH ctrl", "p8mea_avg"),
            ("rob_wxs", r"W$\times$S", "p8mea_avg"),
            ("rob_att8total", "Att8 total 24/25", "att8_total_2425"),
            ("rob_att8eng", "Att8 English 24/25", "att8screng_2425"),
            ("rob_london", "London ctrl", "p8mea_avg"),
            ("rob_singlerater_ctrl", "Single-rater ctrl", "p8mea_avg"),
            ("rob_doublerated", "Double-rated only", "p8mea_avg")]
    W, S = "z_gs_warmth_enacted", "z_gs_strictness_enacted"
    def row(term, label):
        cells, ses = [], []
        for spec, _, _ in cols:
            r = get(df, spec, "overall", term)
            cells.append(f"{num(r.b)}{stars_010(r.pval)}")
            ses.append(f"({r.se:.3f})")
        return (f"{label:<20}& " + " & ".join(f"{c:>18}" for c in cells) + r" \\" + "\n"
                f"{'':<20}& " + " & ".join(f"{s:>18}" for s in ses) + r" \\" + "\n")
    ns = [f"{int(get(df, s, 'overall', W).n):>18}" for s, _, _ in cols]
    r2 = [f"{get(df, s, 'overall', W).r2:>18.3f}" for s, _, _ in cols]
    heads = " & ".join(rf"\multicolumn{{1}}{{c}}{{{h}}}" for _, h, _ in cols)
    body = "\n".join([
        r"\begin{table}[htbp]\centering",
        r"\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}",
        r"\small",
        r"\caption{Robustness of the primary estimate (overall Progress~8 unless "
        r"stated). All columns use the primary specification: full controls, "
        r"predecessor-filled 2019 grade, late-entry schools excluded. The two "
        r"Attainment~8 columns use the 2024/25 cohort, which has no Progress~8; "
        r"the first is the sum of the four Attainment~8 buckets and the second "
        r"the English bucket alone, so their coefficients are in points rather "
        r"than grades.}",
        r"\label{tab:robustness_overall}",
        r"\footnotesize\setlength{\tabcolsep}{4pt}",
        r"\resizebox{\linewidth}{!}{%",
        r"\begin{tabular}{l*{10}{c}}",
        r"\toprule",
        f"                    & {heads} \\\\",
        r"\midrule",
        row(W, "$W$") + r"\addlinespace" + "\n" + row(S, "$S$"),
        r"\midrule",
        f"{'N':<20}& " + " & ".join(ns) + r" \\",
        f"{'$R^2$':<20}& " + " & ".join(r2) + r" \\",
        r"\bottomrule",
        r"\end{tabular}}",
        r"\begin{minipage}{\linewidth}\vspace{4pt}\scriptsize",
        r"\textit{Notes}: HC3 standard errors in parentheses. \sym{*} \(p<0.10\), "
        r"\sym{**} \(p<0.05\), \sym{***} \(p<0.01\). The W$\times$S column adds the "
        r"interaction of the two standardised scores; its main effects are not "
        r"interpretable alone. The single-rater column adds the share of a "
        r"school's observed lessons that were rated by one researcher rather "
        r"than two; the double-rated column keeps only schools in which every "
        r"lesson was rated by at least two.",
        r"\end{minipage}",
        r"\end{table}",
        ""])
    write("tab_robustness_overall.tex", body)


def main() -> int:
    df = load()
    spec_ladder(df)
    univariate_ws(df)
    stages23_trio(df)
    main_results(df)
    enacted_espoused(df)
    robustness_overall(df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
