#!/usr/bin/env python3
"""Chapter 2 quadrant scatter: enacted warmth against enacted strictness for
every visited school, with the four quadrants (split at the medians) labelled
and counted. No outcome overlay -- Chapter 3 carries the Progress 8-coloured
version (fig_quadrant_ws.pdf, make_figures_aug14.py). Zero API calls.

Writes thesis/figures/fig_quadrants_ch2.pdf and prints the counts and the
correlation so the caption can be checked against the text.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "thesis" / "figures"

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.spines.top": False,
    "axes.spines.right": False, "figure.dpi": 150,
})

d = pd.read_csv(ROOT / "analysis_dataset.csv", low_memory=False,
                encoding="utf-8-sig")
for c in ["gs_warmth_enacted", "gs_strictness_enacted"]:
    d[c] = pd.to_numeric(d[c], errors="coerce")
v = d.dropna(subset=["gs_warmth_enacted", "gs_strictness_enacted"])
w, s = v["gs_warmth_enacted"], v["gs_strictness_enacted"]
wm, sm = w.median(), s.median()
r, p = stats.pearsonr(s, w)

counts = {
    "warm and strict": int(((w >= wm) & (s >= sm)).sum()),
    "warm, less strict": int(((w >= wm) & (s < sm)).sum()),
    "strict, less warm": int(((w < wm) & (s >= sm)).sum()),
    "neither": int(((w < wm) & (s < sm)).sum()),
}

fig, ax = plt.subplots(figsize=(5.2, 4.2))
ax.scatter(s, w, s=30, facecolor="white", edgecolor="0.25", linewidth=0.7)
ax.axvline(sm, color="0.6", lw=0.8, ls="--")
ax.axhline(wm, color="0.6", lw=0.8, ls="--")
for (xq, yq, lab, ha, va) in [
        (0.98, 0.98, "warm and strict", "right", "top"),
        (0.02, 0.98, "warm, less strict", "left", "top"),
        (0.98, 0.02, "strict, less warm", "right", "bottom"),
        (0.02, 0.02, "neither", "left", "bottom")]:
    ax.text(xq, yq, f"{lab}\n(n = {counts[lab]})", transform=ax.transAxes,
            ha=ha, va=va, fontsize=8, color="0.35", style="italic")
ax.set_xlabel("Enacted strictness (visit score, 0–10)")
ax.set_ylabel("Enacted warmth (visit score, 0–10)")
fig.tight_layout()
FIGS.mkdir(exist_ok=True)
fig.savefig(FIGS / "fig_quadrants_ch2.pdf")
plt.close(fig)
print(f"fig_quadrants_ch2.pdf  n={len(v)}  r={r:.3f} p={p:.4f}  "
      f"medians W={wm:.2f} S={sm:.2f}  counts={counts}")
