"""Chapter 2 referee round three (20 Aug 2026): two free analyses the chapter lacked.

(1) SCHOOL-LEVEL RELIABILITY of the enacted scores. The chapter reported only
    item-pair rater agreement; what the claims rest on is how much of the variance
    in a school's score is between schools rather than between lessons or raters.
    Lesson-level, per-observer sub-scores are rebuilt from the visit workbook
    exactly as warm_strict_scorer.py builds them (same items, same reverse-scoring,
    same response fill rule), then decomposed school / lesson-within-school /
    rater-within-lesson by nested method-of-moments ANOVA, and the reliability of
    the school mean over its actual lessons and raters is computed (ICC(1,k) with
    the harmonic-mean design). The outside-of-lessons form has one rating per rater
    per school, so it decomposes school / rater only.

(2) REPORT AGE. Inspection reports predate the fieldwork by varying amounts. The
    anchor is the VISIT date (Novel Data/School Visits.xlsx, 'Date of Visit'; names
    joined to URN through the two lookups plus three hand matches). Reports the
    distribution of report age and the strictness / warmth validity correlations by
    age band.

(3) DISATTENUATION. Composite reliability of each enacted score from its two
    halves (Spearman-Brown on the in-lesson / out-of-lesson correlation), Cronbach
    alpha of the espoused statement scales, and the split and criterion
    correlations corrected for unreliability.

Also writes bootstrap 95% CIs for the headline correlations and a bootstrap test
of the warmth-vs-strictness split difference, as macros.

Outputs: thesis/tables/tab_score_reliability.tex, thesis/snippets/reliability_numbers.tex
Run with --check to compare without writing. Zero API calls.
"""
from __future__ import annotations
import argparse, io, os, re, sys, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\damia\OneDrive\Documents\Schools Project")
VISIT = ROOT / "Novel Data" / "School visit data.xlsx"
IV = ROOT / "Novel Data" / "Headteacher Interview - Responses.xlsx"
TAB_OUT = ROOT / "thesis" / "tables" / "tab_score_reliability.tex"
NUM_OUT = ROOT / "thesis" / "snippets" / "reliability_numbers.tex"
rng = np.random.default_rng(20260820)

def norm_name(s):
    return "" if pd.isna(s) else " ".join(str(s).strip().lower().split())

def read_excel_safe(path, sheet_name, header=0):
    with zipfile.ZipFile(path, "r") as zin:
        names = zin.namelist(); patched = {}
        if "xl/styles.xml" in names:
            raw = zin.read("xl/styles.xml").decode("utf-8")
            raw = re.sub(r'<family\s+val="(?:1[5-9]|[2-9]\d+)"\s*/>', "", raw)
            patched["xl/styles.xml"] = raw.encode("utf-8")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for n in names:
                zout.writestr(n, patched.get(n, zin.read(n)))
    buf.seek(0)
    return pd.read_excel(buf, sheet_name=sheet_name, header=header)

# ── (1) lesson-level per-observer sub-scores ─────────────────────────────────
cl = pd.read_excel(VISIT, sheet_name="Classroom observations", header=None).iloc[2:].reset_index(drop=True)
cl.columns = [f"c{i}" for i in range(cl.shape[1])]
cl["school"] = cl["c0"].map(norm_name)
cl = cl[cl["school"] != ""].reset_index(drop=True)
cl["lesson"] = np.arange(len(cl))
# observer blocks: obs1 c6..c25, obs2 c26..c45, obs3 c46..c65; item order within a block:
ITEMS = ["Misbehav", "Response", "Disruption", "Concentration", "Teacher", "Student", "Motivation",
         "Respectful", "Names", "Praise", "Interact", "Questioning", "Verbal", "Discussion", "DiffObs",
         "Explain", "Outcomes", "Methods", "Structure", "Resource"]
rows = []
for k, start in enumerate((6, 26, 46), start=1):
    blk = cl[[f"c{start + j}" for j in range(20)]].apply(pd.to_numeric, errors="coerce")
    blk.columns = ITEMS
    if blk.notna().sum(axis=1).eq(0).all():
        continue
    # response fill rule, as in the scorer
    m = blk["Response"] == 0
    blk.loc[m, "Response"] = 6 - blk.loc[m, "Disruption"]
    W1 = blk[["Names", "Praise", "Interact", "Student", "Motivation"]].mean(axis=1)
    S1 = pd.concat([6 - blk["Misbehav"], 6 - blk["Disruption"], blk["Response"],
                    blk["Respectful"], blk["Concentration"]], axis=1).mean(axis=1)
    T1 = blk[["Questioning", "Verbal", "Discussion", "DiffObs", "Explain", "Outcomes", "Methods",
              "Structure", "Resource", "Teacher"]].mean(axis=1)
    rows.append(pd.DataFrame({"school": cl["school"], "lesson": cl["lesson"], "rater": k,
                              "W1": W1, "S1": S1, "T1": T1}))
L = pd.concat(rows, ignore_index=True).dropna(subset=["W1", "S1"], how="all")

def nested_decomp(df, y):
    """school / lesson(school) / rater(lesson) variance components, method of moments,
    unbalanced design (Searle's approximation using harmonic-mean group sizes)."""
    d = df.dropna(subset=[y])
    g = d.groupby(["school", "lesson"])[y]
    lesson_means = g.mean(); lesson_n = g.size()
    within_lesson = ((d[y] - d.groupby(["school", "lesson"])[y].transform("mean")) ** 2).sum()
    df_within = (lesson_n - 1).sum()
    s2_rater = within_lesson / df_within if df_within > 0 else np.nan
    lm = lesson_means.reset_index()
    lm["n"] = lesson_n.values
    sg = lm.groupby("school")["lesson"].size()
    school_means = lm.groupby("school")[y].mean()
    between_lessons = ((lm[y] - lm.groupby("school")[y].transform("mean")) ** 2).sum()
    df_lesson = (sg - 1).sum()
    m_r = stats.hmean(lm["n"])  # raters per lesson (harmonic)
    ms_lesson = between_lessons / df_lesson
    s2_lesson = max(ms_lesson - s2_rater / m_r, 0.0)
    grand = lm[y].mean()
    between_schools = (sg * (school_means - grand) ** 2).sum()
    df_school = len(sg) - 1
    m_l = stats.hmean(sg)      # lessons per school (harmonic)
    ms_school = between_schools / df_school
    s2_school = max(ms_school - ms_lesson, 0.0) / m_l
    tot = s2_school + s2_lesson + s2_rater
    # reliability of the school mean over m_l lessons and m_r raters
    rel = s2_school / (s2_school + s2_lesson / m_l + s2_rater / (m_l * m_r))
    return dict(school=s2_school / tot, lesson=s2_lesson / tot, rater=s2_rater / tot, rel=rel,
                m_l=m_l, m_r=m_r, n_school=len(sg), n_lesson=len(lm))

dec = {y: nested_decomp(L, y) for y in ("W1", "S1", "T1")}

# outside-of-lessons: one rating per rater per school
ou = pd.read_excel(VISIT, sheet_name="Outside of classroom ", header=None).iloc[2:].reset_index(drop=True)
ou.columns = [f"c{i}" for i in range(ou.shape[1])]
ou["school"] = ou["c0"].map(norm_name); ou = ou[ou["school"] != ""]
OITEMS = ["Sanction", "Reward", "Verbal", "Differentiation", "Corridors", "Arrival", "Students",
          "Displays", "Alignment", "Interactions", "Relationships", "Canteen", "Recreational"]
orows = []
for k, start in enumerate((4, 17, 30), start=1):
    blk = ou[[f"c{start + j}" for j in range(13)]].apply(pd.to_numeric, errors="coerce"); blk.columns = OITEMS
    if blk.notna().sum(axis=1).eq(0).all():
        continue
    W2 = blk[["Students", "Interactions", "Relationships", "Reward"]].mean(axis=1)
    S2 = blk[["Sanction", "Corridors", "Arrival", "Canteen", "Recreational"]].mean(axis=1)
    orows.append(pd.DataFrame({"school": ou["school"], "rater": k, "W2": W2, "S2": S2}))
O = pd.concat(orows, ignore_index=True)

def oneway_decomp(df, y):
    d = df.dropna(subset=[y]); g = d.groupby("school")[y]
    n = g.size(); means = g.mean(); grand = d[y].mean()
    ms_w = ((d[y] - d.groupby("school")[y].transform("mean")) ** 2).sum() / (n - 1).sum()
    ms_b = (n * (means - grand) ** 2).sum() / (len(n) - 1)
    m = stats.hmean(n)
    s2_school = max(ms_b - ms_w, 0) / m
    rel = s2_school / (s2_school + ms_w / m)
    return dict(school=s2_school / (s2_school + ms_w), rater=ms_w / (s2_school + ms_w), rel=rel, m_r=m, n_school=len(n))
odec = {y: oneway_decomp(O, y) for y in ("W2", "S2")}

# enacted score reliability: mean of two sub-scores with independent-ish error -> report both halves;
# plus the correlation between the two halves (in-lesson vs out-of-lesson) as a split-half check
vlk = pd.read_csv(ROOT / "visit_urn_lookup.csv"); vlk["visit_name"] = vlk["visit_name"].map(norm_name)
vmap = dict(zip(vlk["visit_name"], vlk["urn"].astype(str)))
sch_L = L.assign(urn=L["school"].map(vmap)).groupby("urn")[["W1", "S1"]].mean()
sch_O = O.assign(urn=O["school"].map(vmap)).groupby("urn")[["W2", "S2"]].mean()
halves = sch_L.join(sch_O, how="inner")
n_raters_lesson = L.groupby("lesson")["rater"].nunique().value_counts().sort_index().to_dict()
n_raters_day = O.groupby("school")["rater"].nunique().value_counts().sort_index().to_dict()
print("raters per lesson", n_raters_lesson, "raters per day", n_raters_day)
r_w_halves = stats.pearsonr(halves["W1"], halves["W2"])[0]
r_s_halves = stats.pearsonr(halves["S1"], halves["S2"])[0]

# ── (2) report age and headline CIs ──────────────────────────────────────────
d = pd.read_csv(ROOT / "analysis_dataset.csv", encoding="utf-8-sig", low_memory=False)
d["urn"] = d["urn"].astype(str)
for c in ["gs_warmth_enacted", "gs_strictness_enacted", "gs_warmth_espoused", "gs_strictness_espoused",
          "ofsted_LLMWarmthScore", "ofsted_LLMStrictnessScore", "web_LLMStrictnessScore_v15"]:
    d[c] = pd.to_numeric(d[c], errors="coerce")
d["ofsted_dt"] = pd.to_datetime(d["ofsted_date"], dayfirst=True, errors="coerce")
import difflib
vis = pd.read_excel(ROOT / "Novel Data" / "School Visits.xlsx", sheet_name="Sheet1")[["School Name", "Date of Visit"]]
vis = vis.dropna(subset=["School Name"])
vis["school"] = vis["School Name"].map(lambda x: " ".join(str(x).replace("\n", " ").strip().lower().split()))
vis["visit_dt"] = pd.to_datetime(vis["Date of Visit"], errors="coerce")
lkv = pd.read_csv(ROOT / "visit_urn_lookup.csv"); lki = pd.read_csv(ROOT / "interview_urn_lookup.csv")
names = {**dict(zip(lki.interview_name, lki.urn.astype(str))), **dict(zip(lkv.visit_name, lkv.urn.astype(str)))}
HAND = {"trinity church of england school, belvedere": "136538", "marylebone school": "140884",
        "framwellgate school durham": "137696"}
def _strip(x): return re.sub(r"[^a-z0-9 ]", "", x.replace("saint ", "st ").replace("the ", "").replace(" school", "").replace(" academy", ""))
pool = {_strip(k): u for k, u in names.items()}
def to_urn(x):
    if x in HAND: return HAND[x]
    if x in names: return names[x]
    c = difflib.get_close_matches(_strip(x), list(pool), n=1, cutoff=0.85)
    return pool[c[0]] if c else None
vis["urn"] = vis["school"].map(to_urn)
assert vis["urn"].notna().all(), vis.loc[vis.urn.isna(), "school"].tolist()
d = d.merge(vis[["urn", "visit_dt"]].drop_duplicates("urn"), on="urn", how="left")
d["age_y"] = (d["visit_dt"] - d["ofsted_dt"]).dt.days / 365.25
# espoused scale reliability (Cronbach alpha) from the statement battery
iv = read_excel_safe(IV, "Scoring"); iv.columns = [f"c{i}" for i in range(iv.shape[1])]
def alpha(cols):
    X = iv[cols].apply(pd.to_numeric, errors="coerce").dropna(); k = X.shape[1]
    return k / (k - 1) * (1 - X.var(ddof=1).sum() / X.sum(axis=1).var(ddof=1))
alpha_w3, alpha_s4 = alpha(["c68", "c73", "c74"]), alpha(["c67", "c71", "c72", "c75"])
# composite reliability of the enacted scores (Spearman-Brown on the two halves)
rel_enW = 2 * r_w_halves / (1 + r_w_halves); rel_enS = 2 * r_s_halves / (1 + r_s_halves)
v = d[d.gs_strictness_enacted.notna() & d.ofsted_LLMStrictnessScore.notna() & d.age_y.notna()].copy()
age_q = v["age_y"].quantile([0.25, 0.5, 0.75]).round(1).tolist()
age_share_3y = float((v["age_y"] > 3).mean())
med = v["age_y"].median()
recent, older = v[v.age_y <= med], v[v.age_y > med]
r_s_recent = stats.pearsonr(recent.ofsted_LLMStrictnessScore, recent.gs_strictness_enacted)[0]
r_s_older = stats.pearsonr(older.ofsted_LLMStrictnessScore, older.gs_strictness_enacted)[0]
r_w_recent = stats.pearsonr(recent.ofsted_LLMWarmthScore, recent.gs_warmth_enacted)[0]
r_w_older = stats.pearsonr(older.ofsted_LLMWarmthScore, older.gs_warmth_enacted)[0]

def boot_r(x, y, n=4000):
    x, y = np.asarray(x, float), np.asarray(y, float); k = len(x); out = np.empty(n)
    for i in range(n):
        idx = rng.integers(0, k, k); out[i] = np.corrcoef(x[idx], y[idx])[0, 1]
    return np.nanpercentile(out, [2.5, 97.5])
vs = d[d.gs_strictness_enacted.notna() & d.ofsted_LLMStrictnessScore.notna()]
ci_ofs = boot_r(vs.ofsted_LLMStrictnessScore, vs.gs_strictness_enacted)
vw = d[d.gs_strictness_enacted.notna() & d.web_LLMStrictnessScore_v15.notna()]
ci_web = boot_r(vw.web_LLMStrictnessScore_v15, vw.gs_strictness_enacted)
# split difference: both on the 103 schools with both gold-standard halves
b = d.dropna(subset=["gs_warmth_enacted", "gs_warmth_espoused", "gs_strictness_enacted", "gs_strictness_espoused"])
k = len(b); diffs = np.empty(4000)
for i in range(4000):
    idx = rng.integers(0, k, k); s = b.iloc[idx]
    diffs[i] = (np.corrcoef(s.gs_strictness_enacted, s.gs_strictness_espoused)[0, 1]
                - np.corrcoef(s.gs_warmth_enacted, s.gs_warmth_espoused)[0, 1])
split_ci = np.percentile(diffs, [2.5, 97.5]); split_p = 2 * min((diffs <= 0).mean(), (diffs >= 0).mean())
# LOO r CI: bootstrap over the LOO predictions saved by build_ridge_models.py, if present
loo_ci = None
loo_path = ROOT / "ridge_loo_predictions.csv"
if loo_path.exists():
    lp = pd.read_csv(loo_path)
    if {"model", "dimension", "y", "y_loo"} <= set(lp.columns):
        sub = lp[(lp.model == "B") & (lp.dimension == "Strictness")]
        if len(sub):
            loo_ci = boot_r(sub.y, sub.y_loo)

# disattenuated correlations
r_split_w = stats.pearsonr(b.gs_warmth_enacted, b.gs_warmth_espoused)[0] if False else None
bb = d.dropna(subset=["gs_warmth_enacted", "gs_warmth_espoused", "gs_strictness_enacted", "gs_strictness_espoused"])
rw = stats.pearsonr(bb.gs_warmth_enacted, bb.gs_warmth_espoused)[0]
rs = stats.pearsonr(bb.gs_strictness_enacted, bb.gs_strictness_espoused)[0]
dis_w = rw / np.sqrt(rel_enW * alpha_w3); dis_s = rs / np.sqrt(rel_enS * alpha_s4)
vs0 = d[d.gs_strictness_enacted.notna() & d.ofsted_LLMStrictnessScore.notna()]
r_ofs = stats.pearsonr(vs0.ofsted_LLMStrictnessScore, vs0.gs_strictness_enacted)[0]
dis_ofs = r_ofs / np.sqrt(rel_enS)
print(f"alphas W3 {alpha_w3:.2f} S4 {alpha_s4:.2f}; composite rel W {rel_enW:.2f} S {rel_enS:.2f}; "
      f"disattenuated split W {dis_w:.2f} S {dis_s:.2f}; ofsted S {dis_ofs:.2f}")
print(f"in-lesson W1 {dec['W1']}\nin-lesson S1 {dec['S1']}\nteaching T1 {dec['T1']}")
print(f"outside W2 {odec['W2']}\noutside S2 {odec['S2']}")
print(f"halves r: warmth {r_w_halves:.3f}, strictness {r_s_halves:.3f}; n={len(halves)}")
print(f"report age (years) quartiles {age_q}; share >3y {age_share_3y:.2f}; n={len(v)}; median {med:.1f}")
print(f"strictness r recent {r_s_recent:.3f} (n={len(recent)}) older {r_s_older:.3f} (n={len(older)}); warmth {r_w_recent:.3f}/{r_w_older:.3f}")
print(f"CI ofsted S {ci_ofs.round(3)}, web S {ci_web.round(3)}; split diff CI {split_ci.round(3)} p={split_p:.3f}; LOO CI {loo_ci}")

def pct(x): return f"{100*x:.0f}"
tab = rf"""\begin{{table}}[htbp]
\centering
\small
\caption{{Where the variance in the enacted sub-scores lies, and the reliability
of each school's score. Lesson sub-scores are decomposed into between-school,
between-lesson-within-school and between-rater-within-lesson components;
the outside-of-lessons sub-scores, rated once per rater per school, into
between-school and between-rater. Reliability is the share of variance in a
school's mean score, over its own lessons and raters, that is between schools.}}
\label{{tab:score_reliability}}
\begin{{tabular}}{{lccccc}}
\toprule
 & \multicolumn{{3}}{{c}}{{\textit{{Share of variance (\%)}}}} & & \\
\cmidrule(lr){{2-4}}
Sub-score & School & Lesson & Rater & Design & Reliability of school mean \\
\midrule
In-lesson warmth ($W1$) & {pct(dec['W1']['school'])} & {pct(dec['W1']['lesson'])} & {pct(dec['W1']['rater'])} & {dec['W1']['m_l']:.1f} lessons $\times$ {dec['W1']['m_r']:.1f} raters & {dec['W1']['rel']:.2f} \\
In-lesson strictness ($S1$) & {pct(dec['S1']['school'])} & {pct(dec['S1']['lesson'])} & {pct(dec['S1']['rater'])} & {dec['S1']['m_l']:.1f} lessons $\times$ {dec['S1']['m_r']:.1f} raters & {dec['S1']['rel']:.2f} \\
Teaching practice ($T1$) & {pct(dec['T1']['school'])} & {pct(dec['T1']['lesson'])} & {pct(dec['T1']['rater'])} & {dec['T1']['m_l']:.1f} lessons $\times$ {dec['T1']['m_r']:.1f} raters & {dec['T1']['rel']:.2f} \\
\addlinespace[3pt]
Out-of-lesson warmth ($W2$) & {pct(odec['W2']['school'])} & --- & {pct(odec['W2']['rater'])} & {odec['W2']['m_r']:.1f} raters & {odec['W2']['rel']:.2f} \\
Out-of-lesson strictness ($S2$) & {pct(odec['S2']['school'])} & --- & {pct(odec['S2']['rater'])} & {odec['S2']['m_r']:.1f} raters & {odec['S2']['rel']:.2f} \\
\bottomrule
\end{{tabular}}
\begin{{minipage}}{{0.92\linewidth}}
\vspace{{4pt}}\scriptsize
\textit{{Notes}}: Method-of-moments components from nested one-way analyses of
variance on {dec['S1']['n_lesson']} lesson observations in {dec['S1']['n_school']} schools
(lesson sub-scores) and {odec['S2']['n_school']} schools (outside-of-lessons sub-scores);
design sizes are harmonic means. Reliability is $\sigma^2_{{\mathrm{{school}}}} /
(\sigma^2_{{\mathrm{{school}}}} + \sigma^2_{{\mathrm{{lesson}}}}/m_l + \sigma^2_{{\mathrm{{rater}}}}/m_l m_r)$.
The in-lesson and out-of-lesson halves of the enacted score, rated in different
settings, are correlated at $r = {r_w_halves:.2f}$ for warmth and ${r_s_halves:.2f}$ for
strictness across schools.
\end{{minipage}}
\end{{table}}
"""
def mac(name, val): return f"\\newcommand{{\\{name}}}{{{val}}}\n"
nums = ("% Auto-generated by thesis/make_reliability_and_age.py -- do not edit by hand.\n"
        + mac("RelW1", f"{dec['W1']['rel']:.2f}") + mac("RelS1", f"{dec['S1']['rel']:.2f}")
        + mac("RelT1", f"{dec['T1']['rel']:.2f}") + mac("RelW2", f"{odec['W2']['rel']:.2f}") + mac("RelS2", f"{odec['S2']['rel']:.2f}")
        + mac("ShareSchoolW", pct(dec['W1']['school'])) + mac("ShareSchoolS", pct(dec['S1']['school']))
        + mac("ShareLessonW", pct(dec['W1']['lesson'])) + mac("ShareLessonS", pct(dec['S1']['lesson']))
        + mac("HalvesW", f"{r_w_halves:.2f}") + mac("HalvesS", f"{r_s_halves:.2f}") + mac("NHalves", str(len(halves)))
        + mac("LessonsOneRater", str(n_raters_lesson.get(1, 0))) + mac("LessonsTwoRaters", str(n_raters_lesson.get(2, 0)))
        + mac("LessonsThreeRaters", str(n_raters_lesson.get(3, 0)))
        + mac("DaysOneRater", str(n_raters_day.get(1, 0))) + mac("DaysTwoPlusRaters", str(n_raters_day.get(2, 0) + n_raters_day.get(3, 0)))
        + mac("AlphaWThree", f"{alpha_w3:.2f}") + mac("AlphaSFour", f"{alpha_s4:.2f}")
        + mac("RelEnactedW", f"{rel_enW:.2f}") + mac("RelEnactedS", f"{rel_enS:.2f}")
        + mac("DisSplitW", f"{dis_w:.2f}") + mac("DisSplitS", f"{dis_s:.2f}") + mac("DisOfstedS", f"{dis_ofs:.2f}")
        + mac("AgeQOne", f"{age_q[0]:.1f}") + mac("AgeMedian", f"{age_q[1]:.1f}") + mac("AgeQThree", f"{age_q[2]:.1f}")
        + mac("AgeShareOverThree", pct(age_share_3y))
        + mac("RStrictRecent", f"{r_s_recent:.2f}") + mac("RStrictOlder", f"{r_s_older:.2f}")
        + mac("RWarmRecent", f"{r_w_recent:.2f}") + mac("RWarmOlder", f"{r_w_older:.2f}")
        + mac("NRecent", str(len(recent))) + mac("NOlder", str(len(older)))
        + mac("CIOfstedStrictLo", f"{ci_ofs[0]:.2f}") + mac("CIOfstedStrictHi", f"{ci_ofs[1]:.2f}")
        + mac("CIWebStrictLo", f"{ci_web[0]:.2f}") + mac("CIWebStrictHi", f"{ci_web[1]:.2f}")
        + mac("SplitDiffLo", f"{split_ci[0]:.2f}") + mac("SplitDiffHi", f"{split_ci[1]:.2f}")
        + mac("SplitDiffP", f"{split_p:.2f}")
        + (mac("CILooStrictLo", f"{loo_ci[0]:.2f}") + mac("CILooStrictHi", f"{loo_ci[1]:.2f}") if loo_ci is not None else ""))

ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
rc = 0
for path, body in ((TAB_OUT, tab), (NUM_OUT, nums)):
    cur = path.read_text(encoding="utf-8") if path.exists() else ""
    if cur == body:
        print("unchanged", path.name); continue
    if a.check:
        print("DIFFERS", path.name); rc = 1
    else:
        path.write_text(body, encoding="utf-8", newline="\n"); print("wrote", path.name)
raise SystemExit(rc)
