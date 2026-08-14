#!/usr/bin/env python3
"""The three figures added 14 Aug 2026 (Damian's approval): the warmth-by-
strictness quadrant scatter, the academisation event-time plot, and the
espoused/enacted crossover dot plot. Zero API calls; reads the dataset and the
14-Aug batch outputs. Writes PDFs into thesis/figures/.

The academisation CSV lives in the session scratchpad; a durable copy is made
into scores/ the first time this runs so the figure stays reproducible.
"""
from __future__ import annotations

import shutil
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
SCRATCH = Path(r"C:\Users\damia\AppData\Local\Temp\claude"
               r"\c--Users-damia-OneDrive-Documents-Schools-Project"
               r"\6c321e97-ffa1-4b68-b7cc-6d2b479f6561\scratchpad\ch3_batch")

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.spines.top": False,
    "axes.spines.right": False, "figure.dpi": 150,
})

d = pd.read_csv(ROOT / "analysis_dataset.csv", low_memory=False,
                encoding="utf-8-sig")

# ── 1. Quadrant scatter ──────────────────────────────────────────────────────
full = d[(d["gs_data_tier"] == "full") & (d["late_entry"] != 1)].copy()
for c in ["gs_warmth_enacted", "gs_strictness_enacted", "p8mea_avg"]:
    full[c] = pd.to_numeric(full[c], errors="coerce")
full = full.dropna(subset=["gs_warmth_enacted", "gs_strictness_enacted",
                           "p8mea_avg"])
w, s, p8 = (full["gs_warmth_enacted"], full["gs_strictness_enacted"],
            full["p8mea_avg"])
fig, ax = plt.subplots(figsize=(5.6, 4.4))
sc = ax.scatter(s, w, c=p8, cmap="RdYlBu", s=34, edgecolor="0.35",
                linewidth=0.4, vmin=-np.nanmax(np.abs(p8)),
                vmax=np.nanmax(np.abs(p8)))
ax.axvline(s.median(), color="0.6", lw=0.8, ls="--")
ax.axhline(w.median(), color="0.6", lw=0.8, ls="--")
for (xq, yq, lab, ha, va) in [
        (0.98, 0.98, "warm and strict", "right", "top"),
        (0.02, 0.98, "warm, less strict", "left", "top"),
        (0.98, 0.02, "strict, less warm", "right", "bottom"),
        (0.02, 0.02, "neither", "left", "bottom")]:
    ax.text(xq, yq, lab, transform=ax.transAxes, ha=ha, va=va,
            fontsize=8, color="0.35", style="italic")
ax.set_xlabel("Enacted strictness (visit score, 0–10)")
ax.set_ylabel("Enacted warmth (visit score, 0–10)")
cb = fig.colorbar(sc, ax=ax, shrink=0.85)
cb.set_label("Progress 8 (two-year average)")
fig.tight_layout()
fig.savefig(FIGS / "fig_quadrant_ws.pdf")
plt.close(fig)
print(f"fig_quadrant_ws.pdf  n={len(full)}")

# ── 2. Academisation event time ──────────────────────────────────────────────
src = SCRATCH / "academisation_event_time.csv"
dst = ROOT / "scores" / "academisation_event_time.csv"
if src.exists() and not dst.exists():
    shutil.copy(src, dst)
ev = pd.read_csv(dst if dst.exists() else src)
fig, ax = plt.subplots(figsize=(5.6, 3.6))
for typ, style in [("converter", dict(color="#155e63", marker="o")),
                   ("sponsor", dict(color="#b3574b", marker="s"))]:
    sub = ev[ev["atype"].astype(str).str.contains(typ, case=False)] \
        .sort_values("event_t")
    label = ("Converter academies" if typ == "converter"
             else "Sponsor-led academies")
    ax.plot(sub["event_t"], sub["mean"], lw=1.4, ms=4, label=label, **style)
ax.axvline(0, color="0.6", lw=0.8, ls="--")
ax.axhline(0, color="0.85", lw=0.8)
ax.text(0.05, 0.05, "conversion year", transform=ax.get_xaxis_transform(),
        fontsize=8, color="0.4", rotation=90, va="bottom")
ax.set_xlabel("Years since conversion")
ax.set_ylabel("Mean Progress 8")
ax.legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(FIGS / "fig_academisation_event.pdf")
plt.close(fig)
print("fig_academisation_event.pdf")

# ── 3. The crossover dot plot ────────────────────────────────────────────────
def corr(a, b, frame):
    x = frame[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < 30:
        return np.nan, len(x)
    return stats.pearsonr(x[a], x[b])[0], len(x)

pv_col = "pv_warmth" if "pv_warmth" in d.columns else None
sources = [
    ("Ofsted report", "ofsted_LLMWarmthScore"),
    ("Behaviour policy", "bp_LLMWarmthScore"),
    ("School website", "web_LLMWarmthScore_v18"),
]
if pv_col:
    sources.append(("Parent survey", pv_col))
rows = []
for label, col in sources:
    if col not in d.columns:
        continue
    r_esp, n1 = corr(col, "gs_warmth_espoused", d)
    r_en, n2 = corr(col, "gs_warmth_enacted", d)
    rows.append((label, r_esp, r_en, n1, n2))
    print(f"  {label:18} espoused r={r_esp:+.3f} (n={n1})  "
          f"enacted r={r_en:+.3f} (n={n2})")

fig, ax = plt.subplots(figsize=(5.6, 3.2))
ys = np.arange(len(rows))[::-1]
for y, (label, r_esp, r_en, _, _) in zip(ys, rows):
    ax.plot([r_en, r_esp], [y, y], color="0.75", lw=1.2, zorder=1)
    ax.scatter([r_esp], [y], color="#155e63", s=46, zorder=2,
               label="vs espoused warmth (what heads say)" if y == ys[0] else None)
    ax.scatter([r_en], [y], facecolor="white", edgecolor="#b3574b",
               linewidth=1.6, s=46, zorder=2,
               label="vs enacted warmth (what observers record)" if y == ys[0] else None)
ax.axvline(0, color="0.6", lw=0.8)
ax.set_yticks(ys)
ax.set_yticklabels([r[0] for r in rows])
ax.set_xlabel("Correlation with the warmth criterion")
ax.legend(frameon=False, fontsize=8, loc="lower right")
fig.tight_layout()
fig.savefig(FIGS / "fig_crossover_warmth.pdf")
plt.close(fig)
print("fig_crossover_warmth.pdf")
