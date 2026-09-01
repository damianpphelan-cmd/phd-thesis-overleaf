#!/usr/bin/env python3
"""Redirect the national legs of the Chapter 3 appendix tables onto the
marking-scheme bands.

`thesis/ch3_appendix.do` still estimates the national legs on the retired
`ofsted_LLMStrictnessScore` (and, for the typology, `ofsted_LLMWarmthScore`),
so `ch3_appendix_estimates.csv` carries retired numbers under those terms.
The current instruments are the prediction-model warmth and the marking-scheme
band, and the three rubric re-runs already estimate every affected leg:

    typology_rubric_results.csv        analyse_typology_rubric.py
    entry_rates_rubric_results.csv     analyse_entry_rates_rubric.py
    p8proxy_semh_rubric_results.csv    analyse_p8proxy_semh_rubric.py

`apply(E)` swaps those values into the estimates frame in place of the
retired ones, keeping the (table, panel, model, outcome, term) keys the
builders look up, so no builder has to change beyond its row labels. Rows
the rubric CSVs do not cover are left untouched.

Rewiring here rather than in the do-file is deliberate: the Stata leg remains
the record of the retired specification, and re-running it is not required to
rebuild the thesis.
"""
from __future__ import annotations

import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WARMTH = "z_ofsted_llmwarmthscore"
STRICT = "z_ofsted_llmstrictnessscore"


def _csv(name: str) -> pd.DataFrame | None:
    p = os.path.join(ROOT, name)
    return pd.read_csv(p) if os.path.exists(p) else None


def _set(E: pd.DataFrame, key: dict, b=None, se=None, p=None, n=None) -> int:
    """Overwrite the single row matching key. Returns 1 if it landed."""
    m = pd.Series(True, index=E.index)
    for k, v in key.items():
        m &= (E[k] == v)
    if m.sum() != 1:
        return 0
    for col, val in (("b", b), ("se", se), ("pval", p), ("n", n)):
        if val is not None:
            E.loc[m, col] = val
    return 1


def apply(E: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Return (estimates with the national legs on the bands, rows swapped)."""
    E = E.copy()
    hits = 0

    typ = _csv("typology_rubric_results.csv")
    if typ is not None:
        quad = {"authoritative": "quad1", "authoritarian": "quad2",
                "permissive": "quad3", "neglectful": "quad4"}
        for panel, tag in (("natA", "panelA"), ("natB", "panelB")):
            src = typ[typ.model == f"national_rubric_{tag}"]
            for term, key in ((WARMTH, "_zw"), (STRICT, "_zs"),
                              ("z_wxs", "_zwzs")):
                r = src[src.term == key]
                if len(r) == 1:
                    r = r.iloc[0]
                    hits += _set(E, dict(table="typology", panel=panel,
                                         model="interaction", outcome="overall",
                                         term=term),
                                 r.beta, r.se, r.p, r.n)
            r = src[src.term == "authoritative_vs_rest"]
            if len(r) == 1:
                r = r.iloc[0]
                hits += _set(E, dict(table="typology", panel=panel,
                                     model="auth_vs_rest", outcome="overall",
                                     term="auth"), r.beta, r.se, r.p, r.n)
            qs = src[src.analysis == "quadrant_adjmean"]
            for _, r in qs.iterrows():
                qk = quad.get(str(r.quadrant))
                if qk:
                    # analyse_typology_rubric writes the quadrant standard
                    # error into the p column and the mean into adj_mean.
                    hits += _set(E, dict(table="typology", panel=panel,
                                         model="quadrant_adjmean",
                                         outcome="overall", term=qk),
                                 r.adj_mean, r.p, None, r.n)

    ent = _csv("entry_rates_rubric_results.csv")
    if ent is not None:
        for _, r in ent[ent.analysis == "entry_rate"].iterrows():
            hits += _set(E, dict(table="entry", panel=r.panel,
                                 model="national", outcome=r.outcome,
                                 term=STRICT), r.beta, r.se, r.p, r.n)
        for _, r in ent[ent.analysis == "channel_decomp"].iterrows():
            hits += _set(E, dict(table="channel", panel=r.panel,
                                 model="national_without", outcome="ebac",
                                 term=STRICT), r.beta, r.se, r.p, r.n)
            hits += _set(E, dict(table="channel", panel=r.panel,
                                 model="national_with", outcome="ebac",
                                 term=STRICT),
                         r.beta_with_entry, r.se_with_entry,
                         r.p_with_entry, r.n)
            hits += _set(E, dict(table="channel", panel=r.panel,
                                 model="national_with", outcome="ebac",
                                 term="ebacc_entry"),
                         r.entry_beta, None, r.entry_p, r.n)

    px = _csv("p8proxy_semh_rubric_results.csv")
    if px is not None:
        band = px[px.leg == "national_band"]
        for _, r in band[band.table == "p8proxy"].iterrows():
            hits += _set(E, dict(table="p8proxy", panel=r.panel,
                                 model="national", outcome=r.outcome,
                                 term=STRICT), r.beta, r.se, r.p, r.n)
        for _, r in band[band.table == "semh"].iterrows():
            hits += _set(E, dict(table="semh", model="national_S",
                                 outcome="semh_share", term=STRICT),
                         r.beta, r.se, r.p, r.n)

    return E, hits


if __name__ == "__main__":
    e = pd.read_csv(os.path.join(ROOT, "thesis", "tables",
                                 "ch3_appendix_estimates.csv"))
    e["panel"] = e["panel"].fillna("")
    e["outcome"] = e["outcome"].fillna("")
    _, k = apply(e)
    print(f"{k} national rows redirected onto the marking-scheme bands")
