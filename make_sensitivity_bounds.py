r"""Regenerate tab_sensitivity_bounds.tex and snippets/sensitivity_numbers.tex from
thesis/tables/ch3_estimates.csv (the sens_* rows written by ch3_estimates.do).

Oster's delta and the equal-selection bound come straight from psacalc (Oster 2019,
rmax = 1.3 x the controlled R2, capped at 1; each score is the single treatment with
the other score among the controls). The E-values are computed here from the primary
coefficients and the outcome SD on the estimation sample, using VanderWeele and
Ding's approximate conversion for a continuous outcome: d = beta / sd(outcome),
RR = exp(0.91 d), E = RR + sqrt(RR (RR - 1)).

Every number in the table and the snippet comes from the CSV; nothing is typed in.
Run with --check to compare against the files on disk without writing.
"""
import argparse
import math
import os
import sys

import pandas as pd

from fix_tables import caption_to_title, move_caption_below

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "tables", "ch3_estimates.csv")

W, S = "z_gs_warmth_enacted", "z_gs_strictness_enacted"


def evalue(rr):
    if rr < 1:
        rr = 1.0 / rr
    if rr <= 1:
        return 1.0
    return rr + math.sqrt(rr * (rr - 1.0))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    df = pd.read_csv(CSV)

    def row(spec, term):
        r = df[(df.spec == spec) & (df.outcome == "overall") & (df.term == term)]
        assert len(r) == 1, (spec, term)
        return r.iloc[0]

    sd_y = row("sens_sd", "p8mea_avg").b
    short_w, short_s = row("sens_short", W), row("sens_short", S)
    eal_w, eal_s = row("sens_shorteal", W), row("sens_shorteal", S)
    wald = row("wald_ws", "diff")
    out = {}
    for name, term in [("W", W), ("S", S)]:
        prim = row("primary_stage1", term)
        short = row("sens_short", term)
        delta = row("sens_delta", term)
        betaone = row("sens_betaone", term)
        d_point = prim.b / sd_y
        d_lo = prim.lo / sd_y
        ev_point = evalue(math.exp(0.91 * d_point))
        ev_ci = 1.0 if prim.lo <= 0 else evalue(math.exp(0.91 * d_lo))
        out[name] = dict(b=prim.b, lo=prim.lo, hi=prim.hi, n=int(prim.n),
                         short=short.b, delta=delta.b, betaone=betaone.b,
                         rmax=delta.r2, ev=ev_point, evci=ev_ci)

    rmax = out["W"]["rmax"]
    assert abs(rmax - out["S"]["rmax"]) < 1e-9

    def line(lab, k):
        o = out[k]
        return (f"{lab} & {o['b']:.3f} & {o['short']:.3f} & {o['delta']:.2f} & "
                f"{o['betaone']:.3f} & {o['ev']:.2f} & {o['evci']:.2f} \\\\")

    table = rf"""\begin{{table}}[htbp]\centering
\caption{{Sensitivity of the primary estimates to unmeasured confounding:
Oster's $\delta$ and E-values}}
\label{{tab:sensitivity_bounds}}
\small
\begin{{tabular}}{{lcccccc}}
\toprule
 & Controlled & No controls & $\delta$ for & $\beta$ at & E-value & E-value \\
 & $\beta$ & $\beta$ & $\beta = 0$ & $\delta = 1$ & (point) & (CI bound) \\
\midrule
{line("Warmth ($W$)", "W")}
{line("Strictness ($S$)", "S")}
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{\linewidth}}
\smallskip
\footnotesize\textit{{Notes:}} Primary specification on overall Progress~8
($n = {out['W']['n']}$); coefficients per standard deviation of the enacted
scores. Oster's $\delta$ (Oster 2019, via \texttt{{psacalc}}) is the strength of
selection on unobservables, relative to selection on the full control set, that
would drive the coefficient to zero given $R_{{\max}} = 1.3 \tilde{{R}}^2 =
{rmax:.2f}$; $\beta$ at $\delta = 1$ is the coefficient that survives when
unobservables are assumed to matter exactly as much as the controls. Each score
is treated as the single treatment with the other score among the controls. The
E-value converts the coefficient to an approximate risk ratio using the outcome
standard deviation on the estimation sample ({sd_y:.2f}) and reports the minimum
association a confounder would need with both the score and the outcome to
explain the estimate away; the CI-bound column applies the same conversion to
the boundary of the 95 per cent confidence interval nearer zero.
\end{{minipage}}
\end{{table}}
"""

    snippet = "\n".join([
        "% written by make_sensitivity_bounds.py -- do not edit",
        rf"\newcommand{{\OsterDeltaW}}{{{out['W']['delta']:.2f}}}",
        rf"\newcommand{{\OsterDeltaS}}{{{out['S']['delta']:.2f}}}",
        rf"\newcommand{{\OsterBetaEqualW}}{{{out['W']['betaone']:.3f}}}",
        rf"\newcommand{{\OsterBetaEqualS}}{{{out['S']['betaone']:.3f}}}",
        rf"\newcommand{{\EValW}}{{{out['W']['ev']:.2f}}}",
        rf"\newcommand{{\EValS}}{{{out['S']['ev']:.2f}}}",
        rf"\newcommand{{\EValWCI}}{{{out['W']['evci']:.2f}}}",
        rf"\newcommand{{\EValSCI}}{{{out['S']['evci']:.2f}}}",
        rf"\newcommand{{\SensRmax}}{{{rmax:.2f}}}",
        rf"\newcommand{{\SensShortW}}{{{short_w.b:.3f}}}",
        rf"\newcommand{{\SensShortWP}}{{{short_w.pval:.2f}}}",
        rf"\newcommand{{\SensShortS}}{{{short_s.b:.3f}}}",
        rf"\newcommand{{\SensShortSP}}{{{short_s.pval:.3f}}}",
        rf"\newcommand{{\SensShortEalW}}{{{eal_w.b:.3f}}}",
        rf"\newcommand{{\SensShortEalS}}{{{eal_s.b:.3f}}}",
        rf"\newcommand{{\WaldWSP}}{{{wald.pval:.2f}}}",
    ]) + "\n"

    table, _ = move_caption_below(table)
    # caption convention (PIPELINE.md, 29 Aug 2026)
    table = caption_to_title(table, 'Sensitivity to unmeasured confounding')
    targets = [
        (os.path.join(HERE, "tables", "tab_sensitivity_bounds.tex"), table),
        (os.path.join(HERE, "snippets", "sensitivity_numbers.tex"), snippet),
    ]
    changed = []
    for path, text in targets:
        if a.check:
            on_disk = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if on_disk != text:
                changed.append(os.path.basename(path))
        else:
            open(path, "w", encoding="utf-8", newline="\n").write(text)
            print("wrote", os.path.relpath(path, HERE))
    print(f"delta W {out['W']['delta']:.2f} S {out['S']['delta']:.2f}; "
          f"beta at delta=1 W {out['W']['betaone']:.3f} S {out['S']['betaone']:.3f}; "
          f"E-values W {out['W']['ev']:.2f}/{out['W']['evci']:.2f} "
          f"S {out['S']['ev']:.2f}/{out['S']['evci']:.2f}; rmax {rmax:.2f}")
    if a.check:
        if changed:
            print("DIFFER:", changed)
            return 1
        print("sensitivity table and snippet match their CSV")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
