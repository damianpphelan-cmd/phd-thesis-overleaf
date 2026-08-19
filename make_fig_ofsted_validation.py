"""Regenerate fig_A_score_distributions.pdf and fig_B_validation_scatter.pdf.

Neither PDF had a generator in the repo. Both were built against the 60/40
composite before it was withdrawn (5 Aug 2026), so both plotted a quantity the
chapter no longer defines and both captions quoted numbers that have since
moved. Figure A now shows the espoused scores (the interviewed tier, which is
what an Ofsted-scale comparison should be against); Figure B now validates
against the ENACTED score, which is the criterion the calibration models
actually target.

Run:  python thesis/make_fig_ofsted_validation.py
"""

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
FIGS = Path(__file__).resolve().parent / "figures"

BLUE, RED, GREY = "#4a6b8a", "#b03a2e", "#b8b8b8"

df = pd.read_csv(BASE / "analysis_dataset.csv", low_memory=False)


def rp(x, y):
    """Pearson r and p, recomputing p from t (scipy >=1.18 returns nan on
    underflow, which prints the strongest cells as non-significant)."""
    n = len(x)
    r, _ = stats.pearsonr(x, y)
    t = r * np.sqrt((n - 2) / (1 - r**2))
    return r, float(2 * stats.t.sf(abs(t), n - 2)), n


# ── Figure A: score distributions ────────────────────────────────────────────

# 19 Aug 2026 (Damian): Figure A now compares like with like -- the enacted
# (visit) and espoused (interview) scores on the SAME visited schools, warmth
# and strictness side by side, on one 0-10 axis. The national inspection-report
# distributions move to their own figure (fig_A2) for the appendix.
vis = df[df["gs_warmth_enacted"].notna() & df["gs_warmth_espoused"].notna()]
fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8), sharey=True)
stats_a = {}
for ax, dim, lab in [(axes[0], "warmth", "Warmth"), (axes[1], "strictness", "Strictness")]:
    en = vis[f"gs_{dim}_enacted"].dropna(); es = vis[f"gs_{dim}_espoused"].dropna()
    stats_a[dim] = (len(en), en.mean(), en.std(), es.mean(), es.std())
    bins = np.arange(3.0, 10.51, 0.5)
    ax.hist(en, bins=bins, color=RED, alpha=0.75, edgecolor="white", linewidth=0.5,
            label=f"Enacted (visit): mean {en.mean():.1f}, SD {en.std():.1f}")
    ax.hist(es, bins=bins, color=BLUE, alpha=0.55, edgecolor="white", linewidth=0.5,
            label=f"Espoused (interview): mean {es.mean():.1f}, SD {es.std():.1f}")
    ax.axvline(en.mean(), ls="--", lw=1.1, color=RED)
    ax.axvline(es.mean(), ls="--", lw=1.1, color=BLUE)
    ax.set_xlabel(f"{lab} score (0--10), the {len(en)} visited schools", fontsize=9)
    ax.set_ylabel("Schools", fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=8)
fig.tight_layout()
fig.savefig(FIGS / "fig_A_score_distributions.pdf")
plt.close(fig)

# Figure A2: the national inspection-report distributions (appendix)
fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6))
for ax, col, lab in [(axes[0], "ofsted_LLMWarmthScore", "Inspection-report warmth  [1--5]"),
                     (axes[1], "ofsted_LLMStrictnessScore", "Inspection-report strictness  [1--5]")]:
    v = df[col].dropna()
    ax.hist(v, bins=np.arange(0.75, 5.5, 0.5), color=RED, alpha=0.8, edgecolor="white", linewidth=0.5)
    ax.axvline(v.mean(), ls="--", lw=1.1, color="#333333")
    ax.set_xlabel(lab, fontsize=9); ax.set_ylabel("Schools", fontsize=9)
    ax.text(0.03, 0.93, f"$n = {len(v):,}$" + chr(10) + f"mean {v.mean():.2f}" + chr(10) + f"SD {v.std():.2f}",
            transform=ax.transAxes, ha="left", va="top", fontsize=8.5)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=8)
fig.tight_layout()
fig.savefig(FIGS / "fig_A2_ofsted_distributions.pdf")
plt.close(fig)

for dim, (n, m, sd, m2, sd2) in stats_a.items():
    print(f"   {dim:<12} n={n}  enacted {m:.2f} ({sd:.2f})  espoused {m2:.2f} ({sd2:.2f})")


# ── Figure B: validation scatter against the ENACTED criterion ───────────────

fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
rng = np.random.default_rng(20260805)
stats_b = {}

for ax, dim, of_col, lab in [
    (axes[0], "warmth",     "ofsted_LLMWarmthScore",     "warmth"),
    (axes[1], "strictness", "ofsted_LLMStrictnessScore", "strictness"),
]:
    gs_col = f"gs_{dim}_enacted"
    esp_col = f"gs_{dim}_espoused"

    gold = df[df[gs_col].notna() & df[of_col].notna()]
    # interviewed schools without a visit: plotted in grey against espoused,
    # for context only -- they are not part of the fit.
    other = df[df[gs_col].isna() & df[esp_col].notna() & df[of_col].notna()]

    jx = lambda s: s + rng.uniform(-0.08, 0.08, len(s))  # noqa: E731

    ax.scatter(jx(other[of_col]), other[esp_col], s=16, color=GREY,
               alpha=0.55, linewidth=0, zorder=2)
    ax.scatter(jx(gold[of_col]), gold[gs_col], s=34, facecolor=BLUE,
               edgecolor="white", linewidth=0.6, zorder=3)

    r, p, n = rp(gold[of_col].values, gold[gs_col].values)
    stats_b[dim] = (r, p, n, len(other))

    b, a = np.polyfit(gold[of_col], gold[gs_col], 1)
    xs = np.linspace(gold[of_col].min(), gold[of_col].max(), 50)
    ax.plot(xs, a + b * xs, color=RED, lw=1.6, zorder=4)

    ptxt = "p < 0.001" if p < 0.001 else f"p = {p:.3f}"
    ax.text(0.03, 0.96, f"$r = {r:+.3f}$  (${ptxt}$, $n = {n}$)",
            transform=ax.transAxes, ha="left", va="top", fontsize=9.5)
    ax.set_xlabel(f"Ofsted LLM {lab} score  [1--5]", fontsize=9.5)
    ax.set_ylabel(f"Enacted {lab}  [0--10]", fontsize=9.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=9)

fig.tight_layout()
fig.savefig(FIGS / "fig_B_validation_scatter.pdf")
plt.close(fig)

print("fig_B_validation_scatter.pdf")
for dim, (r, p, n, n_grey) in stats_b.items():
    print(f"   {dim:<11} r={r:+.3f}  p={p:.4f}  n={n} gold, {n_grey} interview-only")
