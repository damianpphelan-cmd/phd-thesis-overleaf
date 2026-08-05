"""Regenerate fig_warmth_strict_joint.pdf.

The PDF in thesis/figures/ had no generator in the repo. It was produced before
the 60/40 composite was withdrawn (5 Aug 2026), so it plotted the blended score
and its caption reported r = 0.480. The chapter now defines enacted and espoused
scores separately, and the quadrant figure belongs to the ENACTED pair --- the
two dimensions as an independent observer recorded them, which is what
\\cref{ch:paper2} regresses on.

Run:  python thesis/make_fig_warmth_strict_joint.py
"""

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "figures" / "fig_warmth_strict_joint.pdf"

X, Y = "gs_strictness_enacted", "gs_warmth_enacted"

df = pd.read_csv(BASE / "analysis_dataset.csv", low_memory=False)
d = df[[X, Y]].dropna()
n = len(d)

r, _ = stats.pearsonr(d[X], d[Y])
# scipy >= 1.18 returns nan for p on underflow; recompute from t.
t = r * np.sqrt((n - 2) / (1 - r**2))
p = float(2 * stats.t.sf(abs(t), n - 2))

mx, my = d[X].mean(), d[Y].mean()

fig, ax = plt.subplots(figsize=(6.4, 5.4))
ax.scatter(d[X], d[Y], s=34, facecolor="#4a6b8a", edgecolor="white",
           linewidth=0.6, alpha=0.85, zorder=3)

ax.axvline(mx, ls="--", lw=0.9, color="#555555", zorder=1)
ax.axhline(my, ls="--", lw=0.9, color="#555555", zorder=1)

# least-squares line, for the direction of the association only
b, a = np.polyfit(d[X], d[Y], 1)
xs = np.linspace(d[X].min(), d[X].max(), 50)
ax.plot(xs, a + b * xs, color="#b03a2e", lw=1.4, zorder=2)

lo, hi = 3.8, 9.6
ax.set_xlim(lo, hi)
ax.set_ylim(lo, hi)
ax.set_xlabel("Enacted strictness $S^{\\mathrm{enac}}$  [0--10]")
ax.set_ylabel("Enacted warmth $W^{\\mathrm{enac}}$  [0--10]")

pad = 0.18
quads = [
    (hi - pad, hi - pad, "warm / strict", "right", "top"),
    (lo + pad, hi - pad, "warm / relaxed", "left", "top"),
    (hi - pad, lo + pad, "cold / strict", "right", "bottom"),
    (lo + pad, lo + pad, "cold / relaxed", "left", "bottom"),
]
for qx, qy, lab, ha, va in quads:
    ax.text(qx, qy, lab, ha=ha, va=va, fontsize=8.5, color="#777777",
            style="italic")

ax.text(0.03, 0.965, f"$r = {r:.3f}$   ($n = {n}$)", transform=ax.transAxes,
        ha="left", va="top", fontsize=9.5)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.tick_params(labelsize=9)
fig.tight_layout()
fig.savefig(OUT)

print(f"{OUT.name}: n={n}  r={r:.3f}  p={p:.3g}  "
       f"mean S={mx:.2f} W={my:.2f}")
