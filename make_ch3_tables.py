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

from fix_tables import caption_to_title, move_caption_below

# Caption convention (29 Aug 2026): short title in the caption, all
# detail in the notes. (title, keep_first_sentence_of_old_caption)
TITLES = {
    "tab_spec_ladder.tex":
        ("Four treatments of the inspection-grade control", False),
    "tab_univariate_ws.tex":
        ("Warmth and strictness alone and together", False),
    "tab_stages23_trio.tex":
        ("Stages 2 and 3 under the primary specification", True),
    "tab_main_results_s1.tex":
        ("Stage 1: total culture association, five outcomes", False),
    "tab_main_results_s2.tex":
        ("Stage 2: teaching quality benchmark, five outcomes", False),
    "tab_main_results_s3.tex":
        ("Stage 3: culture net of teaching, five outcomes", False),
    "tab_enacted_espoused.tex":
        ("Espoused culture and Progress~8", False),
    "tab_robustness_overall.tex":
        ("Robustness of the visited estimates", False),
}

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
    if name in TITLES:
        body = caption_to_title(body, *TITLES[name])
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
belongs to a school excluded for a missing control). The filled and category-retained
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
    overall, english and maths only; ebac and open exist only under an earlier
    vintage of the same control set (espoused_t1; n=96): grade as recorded
    rather than filled AND the late-entry exclusion not yet applied. Rerunning
    that regression with late entry excluded gives n=95 (verified in Python,
    25 Aug 2026), so the 96th school is a late-entry school with a recorded
    grade. The caption states both. The stage1/stage2/stage3 rows of the CSV
    (n=96) are the same stale vintage; the ladder_a row (n=95) is the
    current-spec version.
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
on the same control set before the predecessor-grade fill and before the
late-entry exclusion ($n=96$; with that exclusion applied the unfilled-grade
sample has 95 schools), the only form in which those components are
available.}}
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
    rows = [("primary_stage1", "Primary specification", "p8mea_avg"),
            ("rob_nograde", "No grade control", "p8mea_avg"),
            ("rob_singleyear", "2023--24 results only", "p8mea_2324"),
            ("rob_semh", "SEMH share controlled", "p8mea_avg"),
            ("rob_wxs", r"Warmth $\times$ strictness added", "p8mea_avg"),
            ("rob_att8total", "Attainment~8 total, 2024/25", "att8_total_2425"),
            ("rob_att8eng", "Attainment~8 English, 2024/25", "att8screng_2425"),
            ("rob_london", "London controlled", "p8mea_avg"),
            ("rob_singlerater_ctrl", "Single-rater share controlled",
             "p8mea_avg"),
            ("rob_doublerated", "Double-rated schools only", "p8mea_avg")]
    W, S = "z_gs_warmth_enacted", "z_gs_strictness_enacted"

    def line(spec: str, label: str) -> str:
        w = get(df, spec, "overall", W)
        s = get(df, spec, "overall", S)
        wc = f"{num(w.b)}{stars_010(w.pval)} ({w.se:.3f})"
        sc = f"{num(s.b)}{stars_010(s.pval)} ({s.se:.3f})"
        return (f"{label:<34}& {int(w.n):>4} & {wc:>24} & {sc:>24} "
                f"& {w.r2:.3f} \\\\")

    body = "\n".join([
        r"\begin{table}[htbp]\centering",
        r"\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}",
        r"\small",
        r"\caption{Robustness of the primary estimate. Each row is one check, "
        r"and reports the warmth and strictness coefficients from a single "
        r"regression. The outcome is the two-year average of overall "
        r"Progress~8 unless the row says otherwise, and every row uses the "
        r"primary specification: full controls, predecessor-filled 2019 "
        r"grade, late-entry schools excluded. The two Attainment~8 rows use "
        r"the 2024/25 cohort, which has no Progress~8; the first takes the "
        r"sum of the four Attainment~8 buckets and the second the English "
        r"bucket alone, so their coefficients are in points rather than "
        r"grades.}",
        r"\label{tab:robustness_overall}",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        f"{'Check':<34}& {'$N$':>4} & {'Warmth ($W$)':>24} & "
        f"{'Strictness ($S$)':>24} & $R^2$ \\\\",
        r"\midrule",
        line(*rows[0][:2]),
        r"\addlinespace",
        "\n".join(line(spec, label) for spec, label, _ in rows[1:]),
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{minipage}{\linewidth}\vspace{4pt}\scriptsize",
        r"\textit{Notes}: HC3 standard errors in parentheses. \sym{*} "
        r"\(p<0.10\), \sym{**} \(p<0.05\), \sym{***} \(p<0.01\). The "
        r"warmth $\times$ strictness row adds the interaction of the two "
        r"standardised scores; the two coefficients shown are then main "
        r"effects, which are not interpretable on their own. The "
        r"single-rater row adds the share of a school's observed lessons "
        r"that were rated by one researcher rather than two; the "
        r"double-rated row keeps only schools in which every lesson was "
        r"rated by at least two.",
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
