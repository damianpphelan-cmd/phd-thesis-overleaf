"""Build thesis/tables/ch3_appendix_input.csv — one row per school (URN) carrying
everything thesis/ch3_appendix.do needs to re-estimate the Chapter 3 appendix
tables on the PRIMARY specification (19 Aug 2026, Damian's Option A).

Python prepares, Stata estimates, Python formats. This script only assembles and
derives variables; it runs no regression that a table reports.

Sources (the canonical one for each family):
  analysis_dataset.csv                      -- outcomes, controls, culture scores,
                                               instrument columns, late_entry,
                                               grade2019_filled, Parent View
  Novel Data/School visit data_with_urns.xlsx -- per-school means of the 33
                                               observation items (FINAL block, the
                                               scorer's transforms applied) and the
                                               pooled pairwise observer r per item
  panel/school_panel_...ofsted.csv (2023-24)  -- EBacc / humanities / languages
                                               entry rates from pupil counts
  panel/performance_ks4_normalised.csv        -- P8 by year for the stability table
  scores/_duplicate_documents.csv             -- shared-document digest (333 schools
                                               in 90 trust-template groups) for
                                               clustering the BP rows
  scratchpad p8_proxy/p8_proxy_2425.csv       -- the 2024/25 pseudo-progress measure
                                               (build_p8_proxy_2425.py); re-run that
                                               script if the file is missing

Writes:
  thesis/tables/ch3_appendix_input.csv
  thesis/tables/ch3_appendix_items_irr.csv   (item -> sub-score, observer r, pairs)
  thesis/tables/ch3_appendix_stability.csv   (within-school P8 SD + adjacent moves)
"""
from __future__ import annotations
import os, re, sys, itertools
import numpy as np
import pandas as pd

ROOT = r"C:\Users\damia\OneDrive\Documents\Schools Project"
TAB = os.path.join(ROOT, "thesis", "tables")
SP = (r"C:\Users\damia\AppData\Local\Temp\claude"
      r"\c--Users-damia-OneDrive-Documents-Schools-Project"
      r"\6c321e97-ffa1-4b68-b7cc-6d2b479f6561\scratchpad")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

d = pd.read_csv(os.path.join(ROOT, "analysis_dataset.csv"), encoding="utf-8-sig", low_memory=False)
d["urn_num"] = pd.to_numeric(d["urn"], errors="coerce")
for c in d.columns:
    if c in ("urn", "gs_data_tier", "web_id_LLMFaithProminence", "web_id_LLMTeachingPhilosophy",
             "web_crawl_verdict", "ofsted_date", "type", "admissions", "urban", "year",
             "gias_religious_character", "gias_religious_ethos", "gias_faith_source",
             "pv_release_year", "web_id_LLMReligiousCharacter", "web_LLMReligiousCharacter_repair138",
             "web_LLMFaithProminence_repair138", "web_id_LLMTeachingConfidence", "web_crawl_gen",
             "ofsted_HeadteacherChanged"):
        continue
    d[c] = pd.to_numeric(d[c].astype(str).str.replace("%", "", regex=False), errors="coerce")

keep = ["urn", "urn_num", "gs_data_tier", "late_entry", "grade2019_filled", "ofsted_grade_2019",
        "p8mea_avg", "p8meaeng_avg", "p8meamat_avg", "p8meaebac_avg", "p8meaopen_avg", "p8mea_2324",
        "ks2", "fsm", "eal", "sen", "log_size", "years_since_ofsted", "academy", "urban_bin", "selective",
        "gs_warmth_enacted", "gs_strictness_enacted", "gs_teaching_enacted",
        "gs_warmth_espoused", "gs_strictness_espoused",
        "gs_W1", "gs_W2", "gs_S1", "gs_S2", "gs_T1",
        "ofsted_LLMWarmthScore", "ofsted_LLMStrictnessScore", "ofsted_LLMTeachingScore",
        "bp_LLMStrictnessScore_v4", "bp_LLMWarmthScore_v4",
        "web_LLMWarmthScore_v18", "web_LLMWarmthScore_v13", "web_LLMStrictnessScore_v13",
        "web_LLMStrictnessScore_v15", "web_TradEthos_v2", "web_TradPedagogy_v1b",
        "trx_LLMStrictnessScore_v13", "trx_LLMTeachingScore_v3", "trx_LLMWarmthScore_v15",
        "trx_LLMWarmthScore_counts", "pv_warmth", "semh_baseline_2016", "semh_current",
        ]
out = d[keep].copy()
# head-teacher continuity flag from GIAS snapshots (1 Sep 2022 vs
# 1 Jul 2025), built by build_head_continuity.py: 1 = same head,
# 0 = changed. Replaces the retired report-based flag.
hc = pd.read_csv(os.path.join(ROOT, "head_continuity.csv"),
                 usecols=["urn", "head_same"])
hc["urn"] = pd.to_numeric(hc["urn"], errors="coerce")
hc = hc.dropna(subset=["urn"])
hc["head_same"] = pd.to_numeric(hc["head_same"], errors="coerce")
out = out.merge(hc.rename(columns={"urn": "urn_num"}),
                on="urn_num", how="left")

# SEMH shares of the roll (the dataset carries pupil COUNTS; the mechanism table
# is specified in shares). Both use the current roll as denominator because the
# 2015/16 roll is not in the dataset; stated in the table notes.
sz = d["size"].where(d["size"] > 0)
out["semh_share_current"] = 100 * d["semh_current"] / sz
out["semh_share_2016"] = 100 * d["semh_baseline_2016"] / sz

# faith prominence as an ordinal 0-3 (none < incidental < present < central)
fp = d["web_id_LLMFaithProminence"].astype(str).str.lower().map(
    {"none": 0, "incidental": 1, "present": 2, "central": 3})
out["faith_prominence"] = fp

# ── 1. Observation items: per-school means + observer IRR ────────────────────
X = pd.ExcelFile(os.path.join(ROOT, "Novel Data", "School visit data_with_urns.xlsx"))
SHEETS = {"Classroom observations": 6, "Outside of classroom ": 4}
SUBSCORE_MAP = {
    "Classroom|Misbehaviour": "S1", "Classroom|Response": "S1", "Classroom|Disruption": "S1",
    "Classroom|Concentration": "S1", "Classroom|Respectfully": "S1",
    "Classroom|Names": "W1", "Classroom|Praise": "W1", "Classroom|Interactions": "W1",
    "Classroom|Student": "W1", "Classroom|Motivation": "W1", "Classroom|Teacher": "T1",
    "Classroom|Questioning": "T1", "Classroom|Verbal": "T1", "Classroom|Discussion": "T1",
    "Classroom|Differentiation": "T1", "Classroom|Explanation": "T1", "Classroom|Outcomes": "T1",
    "Classroom|Methods": "T1", "Classroom|Structure": "T1", "Classroom|Resource": "T1",
}
item_cols = {}
irr_rows = []
for sheet, n_meta in SHEETS.items():
    raw = pd.read_excel(X, sheet_name=sheet, header=None)
    r0, r1 = raw.iloc[0].tolist(), raw.iloc[1].tolist()
    blocks = [j for j, v in enumerate(r0) if isinstance(v, str) and v.startswith("Observer")]
    final = next(j for j, v in enumerate(r0) if isinstance(v, str) and "Final" in v)
    urn_col = next(j for j, v in enumerate(r1) if str(v).strip().upper() == "URN")
    items = [str(v).strip() for v in r1[n_meta:blocks[1]] if isinstance(v, str)]
    data = raw.iloc[2:].reset_index(drop=True)
    urn = pd.to_numeric(data.iloc[:, urn_col], errors="coerce")
    short = "Classroom" if sheet.startswith("Classroom") else "Outside"
    for k, it in enumerate(items):
        # observer blocks
        cols = [b + k for b in blocks]
        a, b2 = [], []
        for i1, i2 in itertools.combinations(cols, 2):
            x = pd.to_numeric(data.iloc[:, i1], errors="coerce")
            y = pd.to_numeric(data.iloc[:, i2], errors="coerce")
            m = x.between(1, 5) & y.between(1, 5)
            a += x[m].tolist(); b2 += y[m].tolist()
        irr_r = np.corrcoef(a, b2)[0, 1] if len(a) > 2 else np.nan
        # final block, scorer transforms (as warm_strict_scorer / analyse_ch3_batch)
        v = pd.to_numeric(data.iloc[:, final + k], errors="coerce")
        if short == "Classroom":
            if it in ("Misbehaviour", "Disruption"):
                v = 6 - v
            if it == "Response":
                dis = pd.to_numeric(data.iloc[:, final + items.index("Disruption")], errors="coerce")
                v = v.where(v != 0, 6 - dis)
            if it == "Discussion":
                v = 1 + 4 * v / 5
        key = f"{short}|{it}"
        per_school = pd.DataFrame({"urn_num": urn, "v": v}).dropna().groupby("urn_num")["v"].mean()
        var = "it_" + re.sub(r"[^A-Za-z0-9]", "", short.lower() + "_" + it.lower())
        item_cols[var] = per_school
        sub = SUBSCORE_MAP.get(key)
        if sub is None:
            nm2 = it.lower()
            if any(k2 in nm2 for k2 in ["sanction", "corridor", "arrival", "canteen", "recreational"]):
                sub = "S2"
            elif any(k2 in nm2 for k2 in ["students", "interactions", "relationships"]):
                sub = "W2"
            else:
                sub = "unused"
        irr_rows.append(dict(var=var, item=key, subscore=sub, irr_r=irr_r, irr_pairs=len(a)))
items_df = pd.DataFrame(item_cols)
items_df.index.name = "urn_num"
out = out.merge(items_df.reset_index(), on="urn_num", how="left")
pd.DataFrame(irr_rows).to_csv(os.path.join(TAB, "ch3_appendix_items_irr.csv"), index=False)
print(f"items: {len(item_cols)} columns; schools with items: {items_df.shape[0]}")

# ── 2. Entry rates (2023-24 panel) ────────────────────────────────────────────
PANEL = os.path.join(ROOT, "panel", "school_panel_with_performance_pupil_sen_workforce_financial_and_ofsted.csv")
pc = ["urn", "academic_year", "perf_ks4_tpup", "perf_ks4_tebacc_e_ptq_ee",
      "perf_ks4_tebachum_e_ptq_ee", "perf_ks4_tebaclan_e_ptq_ee"]
pan = pd.read_csv(PANEL, usecols=pc, low_memory=False)
pan = pan[pan["academic_year"] == "2023-2024"].copy()
for c in pc[2:]:
    pan[c] = pd.to_numeric(pan[c], errors="coerce")
pan["urn_num"] = pd.to_numeric(pan["urn"], errors="coerce")
pan = pan.dropna(subset=["urn_num"]).drop_duplicates("urn_num")
tp = pan["perf_ks4_tpup"].where(pan["perf_ks4_tpup"] > 0)
pan["ebacc_entry"] = pan["perf_ks4_tebacc_e_ptq_ee"] / tp
pan["hum_entry"] = pan["perf_ks4_tebachum_e_ptq_ee"] / tp
pan["lang_entry"] = pan["perf_ks4_tebaclan_e_ptq_ee"] / tp
out = out.merge(pan[["urn_num", "ebacc_entry", "hum_entry", "lang_entry"]], on="urn_num", how="left")
print("entry rates: non-null", out.ebacc_entry.notna().sum())

# ── 3. BP document digest (clustering) ────────────────────────────────────────
# scores/_duplicate_documents.csv lists the 333 schools whose selected policy is
# byte-identical to another school's (90 digests, the trust-template clusters of
# memory project_bp_document_integrity). Every other school is its own cluster.
dup = pd.read_csv(os.path.join(ROOT, "scores", "_duplicate_documents.csv"), encoding="utf-8-sig")
dup["urn_num"] = pd.to_numeric(dup["URN"], errors="coerce")
dup = dup.dropna(subset=["urn_num"]).drop_duplicates("urn_num")[["urn_num", "digest"]]
out = out.merge(dup, on="urn_num", how="left")
dig = out["digest"].fillna("solo_" + out["urn_num"].astype("Int64").astype(str))
out["bp_digest_id"] = pd.factorize(dig)[0] + 1
out = out.drop(columns=["digest"])
print("bp digest groups:", out.bp_digest_id.nunique(), " schools sharing a digest:",
      (out.groupby("bp_digest_id").urn_num.transform("size") > 1).sum())

# ── 4. Pseudo-P8 2024/25 ──────────────────────────────────────────────────────
pp = os.path.join(SP, "p8_proxy", "p8_proxy_2425.csv")
if not os.path.exists(pp):
    raise SystemExit("p8_proxy_2425.csv missing -- run build_p8_proxy_2425.py first")
px = pd.read_csv(pp)
px["urn_num"] = pd.to_numeric(px["urn"], errors="coerce")
pcol = next(c for c in px.columns if "pseudo" in c.lower() or c.lower().startswith("p8_proxy") or c.lower() == "proxy")
print("pseudo-P8 column:", pcol, "| columns:", [c for c in px.columns][:8])
px = px.dropna(subset=["urn_num"]).drop_duplicates("urn_num")
ren = {pcol: "pseudo_p8_2425", "p8_proxy_2425_eng": "pseudo_p8_2425_eng", "p8_proxy_2425_mat": "pseudo_p8_2425_mat"}
out = out.merge(px[["urn_num"] + [c for c in ren if c in px.columns]].rename(columns=ren), on="urn_num", how="left")
# validation numbers from the back-test summary, carried for the table notes
vs = os.path.join(SP, "p8_proxy", "validation_summary.csv")
if os.path.exists(vs):
    pd.read_csv(vs).to_csv(os.path.join(TAB, "ch3_appendix_p8proxy_validation.csv"), index=False)
print("pseudo-P8 non-null:", out.pseudo_p8_2425.notna().sum())

# ── 5. Stability descriptives (P8 across years) ───────────────────────────────
perf = pd.read_csv(os.path.join(ROOT, "panel", "performance_ks4_normalised.csv"),
                   usecols=["urn", "academic_year", "perf_ks4_p8mea"], low_memory=False)
perf["p8"] = pd.to_numeric(perf["perf_ks4_p8mea"], errors="coerce")
perf["urn"] = pd.to_numeric(perf["urn"], errors="coerce")
YEARS = ["2017-2018", "2018-2019", "2021-2022", "2022-2023", "2023-2024"]
pw = perf[perf["academic_year"].isin(YEARS)].pivot_table(index="urn", columns="academic_year", values="p8")
pw = pw.dropna(thresh=3)
sd = pw.std(axis=1, ddof=1)
rows = [dict(stat="within_school_sd_mean", value=sd.mean(), n=len(pw)),
        dict(stat="within_school_sd_median", value=sd.median(), n=len(pw)),
        dict(stat="within_school_sd_p10", value=sd.quantile(.1), n=len(pw)),
        dict(stat="within_school_sd_p90", value=sd.quantile(.9), n=len(pw)),
        dict(stat="between_school_sd_2324", value=pw["2023-2024"].std(), n=pw["2023-2024"].notna().sum())]
ADJ = [("2017-2018", "2018-2019"), ("2021-2022", "2022-2023"), ("2022-2023", "2023-2024")]
allm = []
for a, b in ADJ:
    dif = (pw[b] - pw[a]).dropna().abs(); allm.append(dif)
    rows.append(dict(stat=f"share_gt_0.3|{a}->{b}", value=(dif > 0.3).mean(), n=len(dif)))
    rows.append(dict(stat=f"share_gt_0.5|{a}->{b}", value=(dif > 0.5).mean(), n=len(dif)))
allm = pd.concat(allm)
rows.append(dict(stat="share_gt_0.3|pooled", value=(allm > 0.3).mean(), n=len(allm)))
rows.append(dict(stat="share_gt_0.5|pooled", value=(allm > 0.5).mean(), n=len(allm)))
pd.DataFrame(rows).to_csv(os.path.join(TAB, "ch3_appendix_stability.csv"), index=False)
print("stability: within-school SD mean %.3f (n=%d)" % (sd.mean(), len(pw)))

# ── 6. Academisation event-time means (Panel B of tab_stability_p8) ───────────
bridge = pd.read_csv(os.path.join(ROOT, "urn_bridging_table.csv"))
gias = pd.read_csv(os.path.join(ROOT, "edubasealldata20260709.csv"), encoding="latin-1",
                   usecols=["URN", "TypeOfEstablishment (name)"], low_memory=False)
gias["URN"] = pd.to_numeric(gias["URN"], errors="coerce")
br = bridge.copy()
br["succ"] = pd.to_numeric(br["successor_urn"], errors="coerce")
br["pred"] = pd.to_numeric(br["predecessor_urn"], errors="coerce")
br["conv_end"] = pd.to_numeric(br["conversion_academic_year"].astype(str).str.split("-").str[-1], errors="coerce")
br = br.merge(gias.rename(columns={"URN": "succ", "TypeOfEstablishment (name)": "gias_type"}), on="succ", how="left")
def atype(t):
    t = str(t).lower()
    return "sponsor-led" if "sponsor" in t else ("converter" if "converter" in t else "other")
br["atype"] = br["gias_type"].apply(atype)
perf["year_end"] = pd.to_numeric(perf["academic_year"].str.split("-").str[-1], errors="coerce")
ev_rows = []
for _, r in br.dropna(subset=["succ", "pred", "conv_end"]).iterrows():
    if r["atype"] == "other":
        continue
    for src, u in (("predecessor", r["pred"]), ("successor", r["succ"])):
        sub = perf[(perf["urn"] == u) & perf["p8"].notna()]
        for _, x in sub.iterrows():
            ev_rows.append(dict(succ=r["succ"], atype=r["atype"], event_t=x["year_end"] - r["conv_end"], p8=x["p8"], src=src))
ev = pd.DataFrame(ev_rows)
ev = ev.sort_values("src", key=lambda s_: s_.ne("successor")).drop_duplicates(["succ", "event_t"])
evt = ev.groupby(["atype", "event_t"])["p8"].agg(["mean", "count"]).reset_index()
evt = evt[(evt["event_t"] >= -5) & (evt["event_t"] <= 8) & (evt["count"] >= 5)]
evt.to_csv(os.path.join(TAB, "ch3_appendix_academisation.csv"), index=False)
print("academisation: bridging rows", len(br), br["atype"].value_counts().to_dict())

out.to_csv(os.path.join(TAB, "ch3_appendix_input.csv"), index=False, encoding="utf-8-sig")
print("wrote", os.path.join(TAB, "ch3_appendix_input.csv"), out.shape)
