"""Regenerate thesis/tables/tab_irr_classroom.tex and tab_irr_outside.tex from the raw
visit workbook (Novel Data/School visit data_with_urns.xlsx).

19 Aug 2026 (verification finding C2-9): the two tables had no surviving producer.
N, r, MAD, exact and within-one agreement reproduced exactly from the workbook; the
weighted-kappa column could not be reproduced by any standard implementation (it was
0.01-0.09 off), so it is recomputed here with a stated method and the tables become
regenerable.

Method: for every item, pool all pairwise comparisons between observers who rated
the same lesson (or the same school day for the outside-of-lessons form); ratings
1-5 only (0 = not rated). r = Pearson; MAD = mean absolute difference; Exact and W1 =
per cent of pairs agreeing exactly / within one point; kappa_w = linearly weighted
Cohen's kappa over the categories 1-5 (sklearn, labels 1..5).

Run with --check to compare against disk without writing.
"""
import argparse, itertools, os, sys
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from fix_tables import caption_to_title, move_caption_above

ROOT = r"C:\Users\damia\OneDrive\Documents\Schools Project"
TAB = os.path.join(ROOT, "thesis", "tables")
XLSX = os.path.join(ROOT, "Novel Data", "School visit data_with_urns.xlsx")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# display names for the outside-of-lessons items (the sheet headers are terse)
OUT_LABELS = {
    "Sanction": "Sanctions", "Reward": "Rewards", "Verbal": "Verbal feedback", "Differentiation": "Differentiation",
    "Corridors": "Corridors", "Arrival": "Arrival", "Students": "Students (transitions)", "Displays": "Displays",
    "Alignment": "Alignment", "Interactions": "Interactions (break)", "Relationships": "Relationships (break)",
    "Canteen": "Canteen", "Recreational": "Recreational",
}


def compute(sheet, n_meta):
    raw = pd.read_excel(XLSX, sheet_name=sheet, header=None)
    r0, r1 = raw.iloc[0].tolist(), raw.iloc[1].tolist()
    blocks = [j for j, v in enumerate(r0) if isinstance(v, str) and v.startswith("Observer")]
    items = [str(v).strip() for v in r1[n_meta:blocks[1]] if isinstance(v, str)]
    data = raw.iloc[2:]
    rows = []
    for k, it in enumerate(items):
        a, b = [], []
        for i1, i2 in itertools.combinations([bl + k for bl in blocks], 2):
            x = pd.to_numeric(data.iloc[:, i1], errors="coerce")
            y = pd.to_numeric(data.iloc[:, i2], errors="coerce")
            m = x.between(1, 5) & y.between(1, 5)
            a += x[m].tolist(); b += y[m].tolist()
        a = np.array(a); b = np.array(b)
        if len(a) < 5:
            continue
        rows.append(dict(item=it, n=len(a), r=np.corrcoef(a, b)[0, 1], mad=np.abs(a - b).mean(),
                         exact=100 * (a == b).mean(), w1=100 * (np.abs(a - b) <= 1).mean(),
                         kw=cohen_kappa_score(a.astype(int), b.astype(int), weights="linear", labels=[1, 2, 3, 4, 5])))
    return pd.DataFrame(rows)


def tex(df, label, caption, labels=None):
    lines = []
    for _, r in df.iterrows():
        nm = (labels or {}).get(r["item"], r["item"])
        lines.append(f"{nm} & {int(r.n)} & {r.r:.3f} & {r.mad:.2f} & {r.exact:.0f} & {r.w1:.0f} & {r.kw:.3f} \\\\")
    return rf"""\begin{{table}}[htbp]
\centering
\caption{{{caption}}}
\label{{{label}}}
\small
\begin{{tabular}}{{lrrrrrr}}
\toprule
Item & $N$ & $r$ & MAD & Exact\% & W1\% & $\kappa_w$ \\
\midrule
{chr(10).join(lines)}
\bottomrule
\end{{tabular}}
\end{{table}}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cls = compute("Classroom observations", 6)
    out = compute("Outside of classroom ", 4)
    files = {
        "tab_irr_classroom.tex": tex(cls, "tab:irr_classroom",
            "Inter-rater reliability for classroom observation items.\nEach row pools all pairwise comparisons across lessons observed by two or\nthree researchers simultaneously. $r$: Pearson correlation; MAD: mean\nabsolute difference; Exact: exact agreement; W1: within-one-point agreement;\n$\\kappa_w$: weighted Cohen's $\\kappa$ (linear weights, categories 1--5)."),
        "tab_irr_outside.tex": tex(out, "tab:irr_outside",
            "Inter-rater reliability for outside-of-lesson observation items.\nEach row pools all pairwise comparisons across school days observed by two or\nthree researchers simultaneously. $r$: Pearson correlation; MAD: mean\nabsolute difference; Exact: exact agreement; W1: within-one-point agreement;\n$\\kappa_w$: weighted Cohen's $\\kappa$ (linear weights, categories 1--5).", OUT_LABELS),
    }
    # the caption is composed here as title-plus-detail; the house convention
    # is a short title with the detail in the notes
    titles = {
        "tab_irr_classroom.tex":
            "Inter-rater reliability: classroom observation items",
        "tab_irr_outside.tex":
            "Inter-rater reliability: outside-of-lesson items",
    }
    rc = 0
    for name, body in files.items():
        body, _ = move_caption_above(body)
        body = caption_to_title(body, titles[name])
        p = os.path.join(TAB, name)
        cur = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
        if cur == body:
            print("unchanged", name); continue
        if a.check:
            print("DIFFERS", name); rc = 1
        else:
            open(p, "w", encoding="utf-8", newline="\n").write(body); print("wrote", name)
    print(f"classroom r range {cls.r.min():.2f}-{cls.r.max():.2f}; outside {out.r.min():.2f}-{out.r.max():.2f}; "
          f"W1 min {min(cls.w1.min(), out.w1.min()):.0f}%")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
