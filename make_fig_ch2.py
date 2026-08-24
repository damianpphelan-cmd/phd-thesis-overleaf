"""Build the three Chapter 2 figures as PDFs in thesis/figures/.

Figures:
  1. fig_ch2_validation.pdf  - LOO warmth prediction + rubric strictness band, each vs observed.
  2. fig_ch2_bands.pdf       - national distribution of rubric strictness bands.
  3. fig_ch2_pv.pdf          - binned national predicted warmth vs Parent View warmth.

Run from anywhere; paths resolve relative to this file (project root = parent of thesis/).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIGDIR = Path(__file__).resolve().parent / "figures"
FIGDIR.mkdir(exist_ok=True)

# ---- style -----------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9.5,
    "axes.edgecolor": "#4A4A4A",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": "#4A4A4A",
    "ytick.color": "#4A4A4A",
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "figure.dpi": 150,
})

POINT = "#5B7DA6"   # muted blue for scatter marks
LINE = "#9A6A4E"    # muted brown for fit lines
BAR = "#7A93AE"     # muted blue-grey for bars


def pearson_r(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return float(np.corrcoef(x, y)[0, 1])


def fit_line(ax, x, y, **kw):
    """Least-squares line over the span of x."""
    b, a = np.polyfit(np.asarray(x, float), np.asarray(y, float), 1)
    xs = np.array([np.min(x), np.max(x)], dtype=float)
    ax.plot(xs, b * xs + a, color=LINE, lw=1.4, zorder=3, **kw)


def annotate_r(ax, r, n=None, loc="upper left"):
    txt = f"$r = {r:.2f}$" + (f"\n$n = {n}$" if n is not None else "")
    xy = {"upper left": (0.04, 0.96), "lower right": (0.96, 0.05)}[loc]
    ha = "left" if loc == "upper left" else "right"
    va = "top" if loc == "upper left" else "bottom"
    ax.text(*xy, txt, transform=ax.transAxes, ha=ha, va=va, fontsize=9,
            color="#333333")


# ---- Figure 1: validation panels -------------------------------------------
def figure_validation():
    loo = pd.read_csv(ROOT / "text_prediction_loo_preds_r2_minilm.csv")
    sel = loo[(loo["target"] == "enacted_warmth") & (loo["arm"] == "tfidf")
              & (loo["block"] == "ofsted") & (loo["sample"] == "enacted")
              & (loo["leg"] == "deconf")].dropna(subset=["y", "pred"])

    grid = pd.read_csv(ROOT / "rubric_grid_scores_gpt-4o-mini.csv")
    grid = grid[(grid["source"] == "ofsted") & (grid["dimension"] == "strictness")]
    spine = pd.read_csv(ROOT / "text_spine.csv")
    merged = grid.merge(spine[["urn", "gs_strictness_enacted"]], on="urn", how="inner")
    merged = merged.dropna(subset=["band", "gs_strictness_enacted"])

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(6.6, 3.0))

    # Panel A: LOO predicted vs observed warmth
    r_a = pearson_r(sel["pred"], sel["y"])
    axA.scatter(sel["pred"], sel["y"], s=16, color=POINT, alpha=0.75,
                edgecolors="white", linewidths=0.4, zorder=2)
    fit_line(axA, sel["pred"], sel["y"])
    axA.set_xlabel("Model prediction (held-out)")
    axA.set_ylabel("Observed warmth (residual)")
    annotate_r(axA, r_a, n=len(sel))

    # Panel B: rubric band vs observed strictness (jittered x)
    r_b = pearson_r(merged["band"], merged["gs_strictness_enacted"])
    rng = np.random.default_rng(42)
    jx = merged["band"] + rng.uniform(-0.12, 0.12, size=len(merged))
    axB.scatter(jx, merged["gs_strictness_enacted"], s=16, color=POINT,
                alpha=0.75, edgecolors="white", linewidths=0.4, zorder=2)
    fit_line(axB, merged["band"], merged["gs_strictness_enacted"])
    axB.set_xlabel("Marking-scheme band")
    axB.set_ylabel("Observed strictness")
    axB.set_xticks(sorted(merged["band"].unique()))
    annotate_r(axB, r_b, n=len(merged))

    for ax, tag in ((axA, "A"), (axB, "B")):
        ax.text(-0.18, 1.02, tag, transform=ax.transAxes, fontsize=11,
                fontweight="bold", va="bottom")

    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_ch2_validation.pdf")
    plt.close(fig)
    return r_a, len(sel), r_b, len(merged)


# ---- Figure 2: national band distribution ----------------------------------
def figure_bands():
    nat = pd.read_csv(ROOT / "rubric_strictness_national.csv")
    n_raw = len(nat)
    nat = nat.drop_duplicates(subset="urn")
    counts = nat["band"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)

    fig, ax = plt.subplots(figsize=(4.2, 2.9))
    ax.bar(counts.index, counts.values, width=0.62, color=BAR, zorder=2)
    for b, c in counts.items():
        ax.text(b, c, f"{c:,}", ha="center", va="bottom", fontsize=8,
                color="#333333")
    ax.set_xlabel("Marking-scheme strictness band")
    ax.set_ylabel("Number of schools")
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.yaxis.grid(True, color="#DDDDDD", lw=0.6, zorder=0)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_ch2_bands.pdf")
    plt.close(fig)
    return counts, n_raw, len(nat)


# ---- Figure 3: predicted warmth vs Parent View -----------------------------
def figure_pv():
    pred = pd.read_csv(ROOT / "national_warmth_text_predictions.csv")
    pred = pred[pred["in_training"] == False]  # noqa: E712

    ads = pd.read_csv(ROOT / "analysis_dataset.csv", low_memory=False,
                      usecols=["urn", "pv_warmth"])
    ads["urn"] = pd.to_numeric(ads["urn"], errors="coerce")
    ads["pv_warmth"] = pd.to_numeric(ads["pv_warmth"], errors="coerce")
    ads = ads.dropna(subset=["urn", "pv_warmth"])
    ads["urn"] = ads["urn"].astype(int)

    df = pred.merge(ads, on="urn", how="inner").dropna(
        subset=["warmth_text_pred", "pv_warmth"])

    r = pearson_r(df["warmth_text_pred"], df["pv_warmth"])
    n = len(df)

    bins = pd.qcut(df["warmth_text_pred"], 20, duplicates="drop")
    g = df.groupby(bins, observed=True).agg(
        x=("warmth_text_pred", "mean"), y=("pv_warmth", "mean"))

    fig, ax = plt.subplots(figsize=(4.4, 3.1))
    fit_line(ax, df["warmth_text_pred"], df["pv_warmth"])  # unbinned fit, light
    ax.lines[-1].set_alpha(0.55)
    ax.scatter(g["x"], g["y"], s=30, color=POINT, edgecolors="white",
               linewidths=0.5, zorder=3)
    ax.set_xlabel("Predicted warmth (from inspection report)")
    ax.set_ylabel("Parent View warmth (share positive)")
    # A few extreme predictions stretch the axis far beyond the binned means;
    # clip the view to the central 99% of predictions (the fit line clips too).
    lo, hi = df["warmth_text_pred"].quantile([0.005, 0.995])
    pad = 0.05 * (hi - lo)
    ax.set_xlim(lo - pad, hi + pad)
    ys = g["y"]
    ypad = 0.25 * (ys.max() - ys.min())
    ax.set_ylim(ys.min() - ypad, ys.max() + ypad)
    annotate_r(ax, r, n=n)

    fig.tight_layout()
    fig.savefig(FIGDIR / "fig_ch2_pv.pdf")
    plt.close(fig)
    return r, n, len(g)


if __name__ == "__main__":
    r_a, n_a, r_b, n_b = figure_validation()
    counts, n_raw, n_dedup = figure_bands()
    r_pv, n_pv, n_bins = figure_pv()

    print(f"Panel A (LOO warmth):        r = {r_a:+.3f}  (n = {n_a})")
    print(f"Panel B (band vs strict):    r = {r_b:+.3f}  (n = {n_b})")
    print(f"Bands: {counts.to_dict()}  (rows {n_raw} -> {n_dedup} unique URNs)")
    print(f"Figure 3 (pred vs PV):       r = {r_pv:+.3f}  (n = {n_pv}, bins = {n_bins})")
    print(f"Written to: {FIGDIR}")
