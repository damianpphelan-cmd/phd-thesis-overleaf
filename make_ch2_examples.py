#!/usr/bin/env python3
r"""Producer: sentence-level validation examples for the Ch2 warmth and
teaching models, with topic tags to answer a validity worry: do the
models' strongest sentences concern the construct (relationships for
warmth, teaching for teaching) or merely general quality tone?

Every sentence in the visited schools' inspection reports is scored by the
fitted model (a sentence's score is the sum of its phrases' learned
weights). Sentences are tagged with topics (behaviour / relationships /
teaching / other) from ofsted_annotation_v1.jsonl, matched on normalised
text (lowercase, alphanumeric only, first 80 chars). Outputs:
  tables/tab_p1_examples.tex — main text: per dimension, the three
    highest- and three lowest-scoring ON-TOPIC sentences, two panels;
  snippets/exhibit_share.tex — \WarmTopShare, \WarmBaseShare,
    \TeachTopShare, \TeachBaseShare: on-topic share of the top-100
    tagged sentences vs the tagged-pool base rate;
  snippets/app_examples.tex — appendix: eight each on-topic raising /
    lowering sentences, plus the unfiltered top/bottom eight.
Sentences containing digits or under 60 / over 220 chars are excluded;
near-duplicates collapsed.
"""
from __future__ import annotations

import json
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
             .replace("\u201c", "``").replace("\u201d", "''")
             .replace("\u2013", "--").replace("\u2014", "---"))


def norm_key(s: str) -> str:
    """Normalised sentence key: lowercase, alphanumeric only, first 80."""
    return re.sub(r"[^a-z0-9]+", "", s.lower())[:80]


def load_topic_lookup() -> dict[str, str]:
    """normalised sentence text -> topic, across all annotation records."""
    lookup: dict[str, str] = {}
    with open(ROOT / "ofsted_annotation_v1.jsonl", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            sents = rec["sentences"]
            for tag in rec["tags"]:
                i = tag["i"]
                if 0 <= i < len(sents):
                    lookup[norm_key(sents[i])] = tag["topic"]
    return lookup


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

    # topic tags
    lookup = load_topic_lookup()
    topics = [lookup.get(norm_key(s)) for s in pool]
    n_tagged = sum(t is not None for t in topics)
    print("pool: %d sentences, %d tagged (%.1f%%)"
          % (len(pool), n_tagged, 100.0 * n_tagged / len(pool)))
    if n_tagged < 0.5 * len(pool):
        raise SystemExit("tag lookup matched under half the pool -- "
                         "normalisation mismatch, fix before reporting")

    dims = {"Warmth": ("gs_warmth_enacted", "relationships"),
            "Teaching": ("gs_teaching_enacted", "teaching")}
    panels, app_parts, shares = {}, [], {}
    for name, (col, topic) in dims.items():
        y = yv.loc[urns, col].to_numpy(float)
        m = ok & ~np.isnan(y)
        A = np.column_stack([np.ones(int(m.sum())), C[m]])
        beta, *_ = np.linalg.lstsq(A, y[m], rcond=None)
        yr = y[m] - A @ beta
        model = Ridge(alpha=0.01, fit_intercept=True).fit(X[m], yr)
        sc = S @ np.asarray(model.coef_).ravel()
        order = np.argsort(sc)[::-1]

        # share statistics: of the 100 highest-scoring sentences that
        # carry a tag, how many are on-topic? vs the tagged-pool base rate
        top_tags = [topics[i] for i in order[:100] if topics[i] is not None]
        top_share = 100.0 * sum(t == topic for t in top_tags) / len(top_tags)
        all_tags = [t for t in topics if t is not None]
        base_share = 100.0 * sum(t == topic for t in all_tags) / len(all_tags)
        shares[name] = (top_share, base_share)

        # on-topic rankings
        on_idx = [i for i in range(len(pool)) if topics[i] == topic]
        on_order = sorted(on_idx, key=lambda i: sc[i], reverse=True)
        hi_on = [pool[i] for i in on_order[:8]]
        lo_on = [pool[i] for i in on_order[::-1][:8]]
        panels[name] = (hi_on[:3], lo_on[:3])

        # unfiltered rankings (regardless of topic)
        hi_all = [pool[i] for i in order[:8]]
        lo_all = [pool[i] for i in order[::-1][:8]]

        app_parts.append("\\subsection*{%s}" % name)
        app_parts.append("\\paragraph{Sentences that raise the score.}")
        app_parts.append("\\begin{itemize}")
        app_parts += ["  \\item ``%s''" % esc(s) for s in hi_on]
        app_parts.append("\\end{itemize}")
        app_parts.append("\\paragraph{Sentences that lower the score.}")
        app_parts.append("\\begin{itemize}")
        app_parts += ["  \\item ``%s''" % esc(s) for s in lo_on]
        app_parts.append("\\end{itemize}")
        app_parts.append(
            "\\paragraph{Unfiltered listing.} The eight highest- and "
            "eight lowest-scoring sentences regardless of topic.")
        app_parts.append("\\begin{itemize}")
        app_parts += ["  \\item ``%s''" % esc(s) for s in hi_all]
        app_parts.append("\\end{itemize}")
        app_parts.append("\\begin{itemize}")
        app_parts += ["  \\item ``%s''" % esc(s) for s in lo_all]
        app_parts.append("\\end{itemize}")

    # share macros
    (w_top, w_base), (t_top, t_base) = shares["Warmth"], shares["Teaching"]
    share_tex = (
        "%% generated by make_ch2_examples.py -- do not edit\n"
        "\\newcommand{\\WarmTopShare}{%.0f\\%%}\n"
        "\\newcommand{\\WarmBaseShare}{%.0f\\%%}\n"
        "\\newcommand{\\TeachTopShare}{%.0f\\%%}\n"
        "\\newcommand{\\TeachBaseShare}{%.0f\\%%}\n"
        % (w_top, w_base, t_top, t_base))
    (HERE / "snippets" / "exhibit_share.tex").write_text(
        share_tex, encoding="utf-8")

    # main-text table: two panels, two columns, three rows each
    def panel(name: str) -> str:
        hi, lo = panels[name]
        rows = "\n".join(
            "``%s'' & ``%s'' \\\\\n\\addlinespace" % (esc(h), esc(l))
            for h, l in zip(hi, lo))
        return (
            "\\multicolumn{2}{l}{\\emph{Panel: %s}} \\\\\n\\midrule\n"
            "Raises the score & Lowers the score \\\\\n\\midrule\n"
            % name + rows)

    table = (
        "% generated by make_ch2_examples.py -- do not edit\n"
        "\\begin{table}[htbp]\n\\centering\n"
        "\\caption{Sentences from the visited schools' inspection reports "
        "that most raise or lower the models' scores. A sentence's score "
        "is the sum of its phrases' learned weights. Shown are the "
        "highest- and lowest-scoring sentences among those tagged as "
        "being about staff-pupil relationships (warmth panel) or teaching "
        "(teaching panel); the share statistics in the text report how "
        "often the models' strongest sentences are on-topic. The full "
        "listing, including an unfiltered one, is in "
        "\\cref{sec:p1_app_examples}.}\n"
        "\\label{tab:p1_examples}\n"
        "{\\small\\begin{tabular}{p{0.45\\textwidth}p{0.45\\textwidth}}\n"
        "\\toprule\n"
        + panel("Warmth") + "\n\\midrule\n" + panel("Teaching") +
        "\n\\bottomrule\n\\end{tabular}}\n\\end{table}\n")
    (HERE / "tables" / "tab_p1_examples.tex").write_text(
        table, encoding="utf-8")
    (HERE / "snippets" / "app_examples.tex").write_text(
        "\n".join(app_parts) + "\n", encoding="utf-8")

    print("WarmTopShare %.0f%%  WarmBaseShare %.0f%%  "
          "TeachTopShare %.0f%%  TeachBaseShare %.0f%%"
          % (w_top, w_base, t_top, t_base))
    print("examples table + share macros + appendix snippet written")


if __name__ == "__main__":
    main()
