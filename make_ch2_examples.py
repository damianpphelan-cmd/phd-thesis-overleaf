#!/usr/bin/env python3
r"""Producer: sentence-level validation examples for the Ch2 warmth and
teaching models (Damian's request, 24 Aug 2026: two-word snippets are not
persuasive; show the phrases and sentences that raise or lower scores).

Every sentence in the visited schools' inspection reports is scored by the
fitted model (a sentence's score is the sum of its phrases' learned
weights). Outputs:
  tables/tab_p1_examples.tex — main text: four high- and four low-scoring
    sentences per dimension;
  snippets/app_examples.tex — appendix: twelve each, plus the strongest
    three-to-four-word phrases from a wide-phrase refit.
Sentences containing digits or under 60 / over 220 chars are excluded;
near-duplicates collapsed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
CONTROLS = ["fsm", "eal", "ks2", "years_since_ofsted"]


def esc(s: str) -> str:
    return (s.replace("\\", "").replace("&", "\\&").replace("%", "\\%")
             .replace("#", "\\#").replace("_", "\\_")
             .replace("\u2019", "'").replace("\u2018", "`")
             .replace("\u2013", "--").replace("\u2014", "---"))


def main() -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import Ridge

    spine = pd.read_csv(ROOT / "text_spine.csv")
    spine["urn"] = spine["urn"].astype(int)
    ds = pd.read_csv(ROOT / "analysis_dataset.csv", low_memory=False)
    ds["urn"] = pd.to_numeric(ds["urn"], errors="coerce")
    ds = ds.dropna(subset=["urn"]).set_index("urn")
    ctrl = pd.DataFrame({c: pd.to_numeric(
        ds[c].astype(str).str.rstrip("%"), errors="coerce")
        for c in CONTROLS})

    vis = spine[spine["visited"] & spine["has_all3"]]
    urns = vis["urn"].to_numpy(int)
    texts = [(ROOT / "text_corpus_r2" / "ofsted" / f"{u}.txt"
              ).read_text(encoding="utf-8") for u in urns]
    C = ctrl.reindex(urns).to_numpy(float)
    ok = ~np.isnan(C).any(axis=1)
    yv = spine.set_index("urn")

    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2),
                          min_df=5, max_df=0.9, sublinear_tf=True)
    X = np.asarray(vec.fit_transform(texts).todense())
    wide = TfidfVectorizer(stop_words="english", ngram_range=(3, 4),
                           min_df=5, max_df=0.9, sublinear_tf=True)
    XW = np.asarray(wide.fit_transform(texts).todense())
    wvocab = np.array(wide.get_feature_names_out())

    # sentence pool
    split = re.compile(r"(?<=[.!?])\s+")
    pool, seen = [], set()
    for tx in texts:
        for s in split.split(tx):
            s = re.sub(r"\s+", " ", s).strip()
            if not (60 <= len(s) <= 220) or any(c.isdigit() for c in s):
                continue
            k = re.sub(r"\W+", "", s.lower())[:80]
            if k in seen:
                continue
            seen.add(k)
            pool.append(s)
    S = vec.transform(pool)

    dims = {"Warmth": "gs_warmth_enacted", "Teaching": "gs_teaching_enacted"}
    main_rows, app_parts = {}, []
    for name, col in dims.items():
        y = yv.loc[urns, col].to_numpy(float)
        m = ok & ~np.isnan(y)
        A = np.column_stack([np.ones(int(m.sum())), C[m]])
        beta, *_ = np.linalg.lstsq(A, y[m], rcond=None)
        yr = y[m] - A @ beta
        model = Ridge(alpha=0.01, fit_intercept=True).fit(X[m], yr)
        sc = S @ np.asarray(model.coef_).ravel()
        hi = [pool[i] for i in np.argsort(sc)[::-1][:12]]
        lo = [pool[i] for i in np.argsort(sc)[:12]]
        main_rows[name] = (hi[:4], lo[:4])

        wm = Ridge(alpha=0.01, fit_intercept=True).fit(XW[m], yr)
        wc = np.asarray(wm.coef_).ravel()
        keep = ~np.array([any(ch.isdigit() for ch in v) for v in wvocab])
        wc = np.where(keep, wc, 0)
        ptop = wvocab[np.argsort(wc)[::-1][:8]]
        pbot = wvocab[np.argsort(wc)[:8]]

        app_parts.append("\\subsection*{%s}" % name)
        app_parts.append("\\paragraph{Sentences that raise the score.}")
        app_parts.append("\\begin{itemize}")
        app_parts += ["  \\item ``%s''" % esc(s) for s in hi]
        app_parts.append("\\end{itemize}")
        app_parts.append("\\paragraph{Sentences that lower the score.}")
        app_parts.append("\\begin{itemize}")
        app_parts += ["  \\item ``%s''" % esc(s) for s in lo]
        app_parts.append("\\end{itemize}")
        app_parts.append(
            "\\paragraph{The strongest longer phrases.} Raising: %s. "
            "Lowering: %s." % (
                "; ".join("``%s''" % esc(v) for v in ptop),
                "; ".join("``%s''" % esc(v) for v in pbot)))

    rows = []
    for name in dims:
        hi, lo = main_rows[name]
        rows.append("\\multicolumn{1}{l}{\\emph{%s --- raises the score}} \\\\"
                    % name)
        rows += ["``%s'' \\\\" % esc(s) for s in hi]
        rows.append("\\addlinespace")
        rows.append("\\multicolumn{1}{l}{\\emph{%s --- lowers the score}} \\\\"
                    % name)
        rows += ["``%s'' \\\\" % esc(s) for s in lo]
        rows.append("\\addlinespace")
    table = (
        "% generated by make_ch2_examples.py -- do not edit\n"
        "\\begin{table}[htbp]\n\\centering\n"
        "\\caption{Sentences from the visited schools' inspection reports "
        "that most raise or lower the models' scores. A sentence's score is "
        "the sum of its phrases' learned weights; the full listing is in "
        "\\cref{sec:p1_app_examples}.}\n"
        "\\label{tab:p1_examples}\n"
        "{\\small\\begin{tabular}{p{0.93\\textwidth}}\n\\toprule\n"
        + "\n".join(rows) +
        "\n\\bottomrule\n\\end{tabular}}\n\\end{table}\n")
    (HERE / "tables" / "tab_p1_examples.tex").write_text(
        table, encoding="utf-8")
    (HERE / "snippets" / "app_examples.tex").write_text(
        "\n".join(app_parts) + "\n", encoding="utf-8")
    print("examples table + appendix snippet written")


if __name__ == "__main__":
    main()
