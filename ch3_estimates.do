* ================================================================
* Tidy export of every Chapter 3 estimate the prose quotes.
*
* The esttab tables carry coefficients and standard errors, but the Results
* section also quotes p-values, 95% confidence intervals and R-squared. Those
* were previously read off the Stata log by hand and retyped into the chapter,
* which is why the audit kept finding coefficients that had moved in the tables
* but not in the text. This writes them all to one CSV so the prose can be
* checked against it mechanically.
*
* Specification is identical to chapter3_analysis.ipynb: HC3 robust standard
* errors, the pre-COVID Ofsted grade as the primary control, and the enacted
* (visit) gold-standard scores as the culture measures.
*
* Run headlessly through nbstata (GUI batch mode hangs on this machine), or:
*   "C:\Program Files\StataNow19\StataMP-64.exe" /e do "<absolute path>"
*
* Writes: thesis/tables/ch3_estimates.csv
* ================================================================

clear all
set more off

adopath ++ "C:\Users\damia\ado\plus"

local ROOT "C:/Users/damia/OneDrive/Documents/Schools Project"

import delimited "`ROOT'/analysis_dataset.csv", clear stringcols(_all) case(lower)

* share of a school's observed lessons rated by one researcher (written by
* thesis/make_reliability_and_age.py); merged here so the robustness rows can use it
preserve
import delimited "`ROOT'/scores/visit_single_rated_share.csv", clear stringcols(1) case(lower)
tempfile srs
save `srs'
restore
merge 1:1 urn using `srs', keep(master match) nogenerate

* London indicator (written from GIAS GOR by the referee close-out, 21 Aug 2026);
* merged for the region robustness row -- the warmth result works through the EAL
* control and EAL is concentrated in London, so the region check is owed.
preserve
import delimited "`ROOT'/scores/gias_london_flag.csv", clear stringcols(1) case(lower)
tempfile lnd
save `lnd'
restore
merge 1:1 urn using `lnd', keep(master match) nogenerate
destring london, replace force

foreach v of varlist eal sen {
    replace `v' = subinstr(`v', "%", "", .)
    destring `v', replace
}

local numvars gs_warmth_visit gs_strictness_visit gs_teaching_visit ///
    gs_warmth_espoused gs_strictness_espoused gs_teaching_espoused ///
    gs_warmth_enacted gs_strictness_enacted gs_teaching_enacted ///
    p8mea_avg p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg ///
    p8mea_2324 att8screng_2425 att8scrmat_2425 att8screbac_2425 att8scropen_2425 ///
    semh_baseline_2016 ///
    trx_warmth trx_strictness trx_management ///
    ks2 fsm log_size academy urban_bin selective ///
    years_since_ofsted ofsted_grade_2019 size ///
    grade2019_filled late_entry
destring `numvars', replace force

global ctrl_cont "ks2 fsm eal sen log_size years_since_ofsted"
global ctrl_bin  "academy urban_bin selective"
global ctrl_ofsted "2.ofsted_grade_2019 3.ofsted_grade_2019 4.ofsted_grade_2019"
global controls        "$ctrl_cont $ctrl_bin $ctrl_ofsted"
global controls_ngrade "$ctrl_cont $ctrl_bin"

* Teaching-philosophy dummies. The classification is a string column; both
* dummies are missing where the website was never classified, so the unmarked
* base category is "classified and marked neither", not "no website".
gen byte trad = (web_id_llmteachingphilosophy == "traditional") ///
    if !missing(web_id_llmteachingphilosophy)
gen byte prog = (web_id_llmteachingphilosophy == "progressive") ///
    if !missing(web_id_llmteachingphilosophy)

* ---- Standardisation (19 Aug 2026, Damian's decision (b) after the number
* verification). The chapter reports coefficients per STANDARD DEVIATION; until
* this date the do-file regressed on the raw 0-10 scores, which mattered for
* strictness (SD 0.88). The enacted scores are z-standardised ONCE over the
* visited schools that enter any primary-specification regression (late-entry
* excluded, score non-missing), so every row of every table shares one scale;
* the espoused scores likewise over the interviewed, late-entry-excluded schools.
foreach v in gs_warmth_enacted gs_strictness_enacted gs_teaching_enacted {
    quietly summarize `v' if late_entry != 1
    gen double z_`v' = (`v' - r(mean)) / r(sd)
}
foreach v in gs_warmth_espoused gs_strictness_espoused {
    quietly summarize `v' if late_entry != 1
    gen double z_`v' = (`v' - r(mean)) / r(sd)
}
global W  z_gs_warmth_enacted
global S  z_gs_strictness_enacted
global T  z_gs_teaching_enacted
global WE z_gs_warmth_espoused
global SE z_gs_strictness_espoused

* A named handle, not `tempname'. A tempname is scoped to the do-file that
* created it, and when this is run through nbstata the scope does not survive to
* the first post -- "post __000000 not found", with every regression still
* printing correctly above it, so the failure is easy to miss.
capture postclose ch3pf
local pf ch3pf
postfile `pf' str24 spec str14 outcome str24 term ///
    double(b se pval lo hi n r2) ///
    using "`ROOT'/thesis/tables/ch3_estimates.dta", replace

* Post every culture term from the regression currently in memory.
capture program drop postterms
program define postterms
    args pf spec outcome terms
    foreach t of local terms {
        local b  = _b[`t']
        local se = _se[`t']
        local p  = 2*ttail(e(df_r), abs(`b'/`se'))
        local ci = invttail(e(df_r), 0.025)*`se'
        post `pf' ("`spec'") ("`outcome'") ("`t'") ///
            (`b') (`se') (`p') (`b'-`ci') (`b'+`ci') (e(N)) (e(r2))
    }
end

* ---- Stages 1-3, all five outcomes ----
* SUPERSEDED (19 Aug 2026): the stage1-3, nograde, singleyear, att8, semh,
* semh_sample, wxs and espoused(_t1) rows below predate the primary
* specification and feed no table or sentence; the chapter reads only the
* primary_*, rob_*, ladder_*, sens_*, wald_ws and primary_espoused rows.
* They are kept so the CSV stays append-stable across reruns.
foreach outcome in p8mea_avg p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg {
    local lbl = cond("`outcome'"=="p8mea_avg",     "overall", ///
                cond("`outcome'"=="p8meaeng_avg",  "english", ///
                cond("`outcome'"=="p8meamat_avg",  "maths",   ///
                cond("`outcome'"=="p8meaebac_avg", "ebac",    "open"))))

    regress `outcome' $W $S $controls, vce(hc3)
    postterms `pf' "stage1" "`lbl'" "$W $S"

    regress `outcome' $T $controls, vce(hc3)
    postterms `pf' "stage2" "`lbl'" "$T"

    regress `outcome' $W $S $T $controls, vce(hc3)
    postterms `pf' "stage3" "`lbl'" "$W $S $T"
}

* ---- Robustness columns quoted in the text (overall P8) ----
regress p8mea_avg $W $S $controls_ngrade, vce(hc3)
postterms `pf' "nograde" "overall" "$W $S"

regress p8mea_2324 $W $S $controls, vce(hc3)
postterms `pf' "singleyear" "overall" "$W $S"

regress att8screng_2425 $W $S $controls, vce(hc3)
postterms `pf' "att8" "overall" "$W $S"

capture confirm variable semh_baseline_2016
if !_rc {
    regress p8mea_avg $W $S semh_baseline_2016 $controls, vce(hc3)
    * Freeze the sample BEFORE anything else touches e(), then post.
    gen byte semh_smpl = e(sample)
    postterms `pf' "semh" "overall" "$W $S"

    * The SEMH control also costs five schools, so comparing "semh" against the
    * headline confounds two changes at once. Re-estimate the headline on
    * exactly the SEMH estimation sample, so the gap between "semh_sample" and
    * "semh" is attributable to the control alone.
    regress p8mea_avg $W $S $controls if semh_smpl, vce(hc3)
    postterms `pf' "semh_sample" "overall" "$W $S"
}

gen wxs = $W * $S
regress p8mea_avg $W $S wxs $controls, vce(hc3)
postterms `pf' "wxs" "overall" "$W $S wxs"

* ---- Espoused counterpart, for the enacted-espoused contrast ----
* Two versions, because they answer different questions and the chapter quotes
* both. "espoused" is the extended tier: every interviewed school, which is what
* the espoused measure is FOR. "espoused_t1" holds the sample fixed at the visited
* schools, which is the only version comparable term-for-term with stage1 and is
* what tab_enacted_espoused.tex reports.
gen byte tier1 = !missing($W)

foreach outcome in p8mea_avg p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg {
    local lbl = cond("`outcome'"=="p8mea_avg",     "overall", ///
                cond("`outcome'"=="p8meaeng_avg",  "english", ///
                cond("`outcome'"=="p8meamat_avg",  "maths",   ///
                cond("`outcome'"=="p8meaebac_avg", "ebac",    "open"))))
    regress `outcome' $WE $SE $controls, vce(hc3)
    postterms `pf' "espoused" "`lbl'" "$WE $SE"

    regress `outcome' $WE $SE $controls if tier1, vce(hc3)
    postterms `pf' "espoused_t1" "`lbl'" "$WE $SE"
}

* ---- Exploratory extensions, whose p-values the prose also quotes ----
* Both are national/extended-tier specifications and use the no-grade control set,
* matching chapter3_analysis.ipynb. They are here only so that every figure in the
* Results section has a machine-readable source; the LaTeX tables still come from
* the notebook.
foreach outcome in p8mea_avg p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg {
    local lbl = cond("`outcome'"=="p8mea_avg",     "overall", ///
                cond("`outcome'"=="p8meaeng_avg",  "english", ///
                cond("`outcome'"=="p8meamat_avg",  "maths",   ///
                cond("`outcome'"=="p8meaebac_avg", "ebac",    "open"))))

    regress `outcome' trx_warmth trx_strictness trx_management ///
        $controls_ngrade if !missing(trx_management), vce(hc3)
    postterms `pf' "mgmt" "`lbl'" "trx_warmth trx_strictness trx_management"

    regress `outcome' trad prog $controls_ngrade, vce(hc3)
    postterms `pf' "teachphil" "`lbl'" "trad prog"
}


* ================================================================
* THE PRIMARY SPECIFICATION (added 14 Aug 2026, Damian's rulings).
* Differs from the blocks above in three ways, and they are the reason these
* are posted as separate rows rather than replacing them:
*   (i)  schools whose statutory entry age is 13+ are excluded (P8 charges them
*        for progress from age 11 they cannot have caused);
*   (ii) the pre-COVID grade control is the predecessor-filled version, which
*        recovers five visited schools that converted after 2019;
*   (iii) all five outcomes -- the trio is reported in the chapter body and the
*        five-outcome versions in the appendix, so both sit on ONE spec.
* Everything else -- controls, HC3, the enacted culture scores -- is unchanged,
* so a difference between these rows and the Python estimates in
* analyse_ch3_batch.py is a specification difference, not a software one.
* ================================================================
* The 2019 grade enters with grade 2 (Good) as the factor base: 2. is
* listed FIRST because Stata merges same-variable factor specs and takes
* the first listed level as the base, so the 2. term is the omitted base
* and the estimated indicators are for grades 3 and 4. Grade 1 is
* unlisted and pools with the base (Outstanding schools were exempt from
* routine inspection before 2020, so that label is the stalest category).
* Do NOT shorten the list to 3./4. only: that silently rebases to grade 3
* and pools the grade-3 schools into the base (the 25 Aug 2026 mistake,
* caught 28 Aug before any published number was regenerated under it).
global ctrl_ofsted_f "2.grade2019_filled 3.grade2019_filled 4.grade2019_filled"
global controls_primary "$ctrl_cont $ctrl_bin $ctrl_ofsted_f"

preserve
keep if late_entry != 1

foreach outcome in p8mea_avg p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg {
    local lbl = cond("`outcome'"=="p8mea_avg",     "overall", ///
                cond("`outcome'"=="p8meaeng_avg",  "english", ///
                cond("`outcome'"=="p8meamat_avg",  "maths",   ///
                cond("`outcome'"=="p8meaebac_avg", "ebac",    "open"))))

    regress `outcome' $W $S $controls_primary, vce(hc3)
    postterms `pf' "primary_stage1" "`lbl'" "$W $S"

    regress `outcome' $W $controls_primary, vce(hc3)
    postterms `pf' "primary_warmthonly" "`lbl'" "$W"

    regress `outcome' $S $controls_primary, vce(hc3)
    postterms `pf' "primary_strictonly" "`lbl'" "$S"

    regress `outcome' $T $controls_primary, vce(hc3)
    postterms `pf' "primary_stage2" "`lbl'" "$T"

    regress `outcome' $W $S $T $controls_primary, vce(hc3)
    postterms `pf' "primary_stage3" "`lbl'" "$W $S $T"
}

* ---- Sensitivity to unobservables (Oster delta; E-value inputs) ----
* Short regressions for the Oster comparison, run on the primary estimation
* sample itself (an earlier version ran on n=101 because the sample
* restrictions bind only through the controls), and the outcome SD for the
* E-value conversion in thesis/make_sensitivity_bounds.py. psacalc is
* Oster (2019), installed from SSC.
regress p8mea_avg $W $S $controls_primary, vce(hc3)
local nprim = e(N)
local rmax = min(1.3*e(r2), 1)
gen byte prim_smp = e(sample)
summarize p8mea_avg if prim_smp
post `pf' ("sens_sd") ("overall") ("p8mea_avg") (r(sd)) (.) (.) (.) (.) (r(N)) (.)

regress p8mea_avg $W $S if prim_smp, vce(hc3)
postterms `pf' "sens_short" "overall" "$W $S"

* The one-control diagnostic behind the suppression discussion: the EAL share
* alone moves the warmth coefficient most of the way to its full-control value.
regress p8mea_avg $W $S eal if prim_smp, vce(hc3)
postterms `pf' "sens_shorteal" "overall" "$W $S"

* Wald test of equal warmth and strictness coefficients, primary specification.
regress p8mea_avg $W $S $controls_primary, vce(hc3)
test $W = $S
post `pf' ("wald_ws") ("overall") ("diff") (_b[$W]-_b[$S]) (.) (r(p)) (.) (.) (`nprim') (.)

* Each score as the single treatment, the other score among the controls;
* rmax = 1.3 x the controlled R2 (Oster's convention), capped at 1.
foreach t in $W $S {
    regress p8mea_avg $W $S $controls_primary, vce(hc3)
    psacalc delta `t', rmax(`rmax')
    post `pf' ("sens_delta") ("overall") ("`t'") (r(delta)) (.) (.) (.) (.) (`nprim') (`rmax')
    regress p8mea_avg $W $S $controls_primary, vce(hc3)
    psacalc beta `t', rmax(`rmax') delta(1)
    post `pf' ("sens_betaone") ("overall") ("`t'") (r(beta)) (.) (.) (.) (.) (`nprim') (`rmax')
}

* ---- The specification ladder on overall P8 (tab_spec_ladder.tex) ----
* Four treatments of the pre-COVID inspection grade, everything else held at the
* primary spec (late-entry excluded throughout -- that is why this sits inside
* the same preserve block). The rungs differ ONLY in how a school with no 2019
* grade under its current URN is handled, so the estimation sample is part of
* the result and is reported alongside each rung.
*   A  grade as recorded -- schools missing it are dropped by the dummies
*   B  predecessor-filled grade (the primary specification)
*   C  filled, with "no pre-COVID grade" kept as its own category rather than
*      dropped, so no school leaves the sample for want of a grade
*   D  no grade control at all
gen byte grade2019_cat = cond(missing(grade2019_filled), 5, grade2019_filled)
global ctrl_ofsted_c "2.grade2019_cat 3.grade2019_cat 4.grade2019_cat 5.grade2019_cat"

regress p8mea_avg $W $S $ctrl_cont $ctrl_bin $ctrl_ofsted, vce(hc3)
postterms `pf' "ladder_a" "overall" "$W $S"

regress p8mea_avg $W $S $controls_primary, vce(hc3)
postterms `pf' "ladder_b" "overall" "$W $S"

regress p8mea_avg $W $S $ctrl_cont $ctrl_bin $ctrl_ofsted_c, vce(hc3)
postterms `pf' "ladder_c" "overall" "$W $S"

regress p8mea_avg $W $S $controls_ngrade, vce(hc3)
postterms `pf' "ladder_d" "overall" "$W $S"

* Espoused scores substituted for the enacted ones on the same schools, primary
* spec (quoted in Results; the old 'espoused_t1' rows were the pre-primary spec).
foreach outcome in p8mea_avg p8meaeng_avg p8meamat_avg {
    local lbl = cond("`outcome'"=="p8mea_avg","overall",cond("`outcome'"=="p8meaeng_avg","english","maths"))
    regress `outcome' $WE $SE $controls_primary if !missing($W), vce(hc3)
    postterms `pf' "primary_espoused" "`lbl'" "$WE $SE"
}
restore

* ================================================================
* ROBUSTNESS UNDER THE PRIMARY SPECIFICATION (added 17 Aug 2026).
* tab_robustness_overall.tex used to be built from the notebook under the OLD
* specification (original grades, no late-entry exclusion, n=96) and its Att8
* column regressed on the SUM of the four Attainment-8 buckets, while the
* 'att8' row above regresses on the English bucket alone -- which is why the
* two disagreed by a factor of ~4 (1.273 vs 0.337). Both were correct answers
* to different questions. From here the table is regenerated from THESE rows,
* all on the primary spec, and the Att8 outcome is named explicitly.
* ================================================================
preserve
keep if late_entry != 1
gen att8_total_2425 = att8screng_2425 + att8scrmat_2425 + att8screbac_2425 + att8scropen_2425

regress p8mea_avg $W $S $ctrl_cont $ctrl_bin, vce(hc3)
postterms `pf' "rob_nograde" "overall" "$W $S"

regress p8mea_2324 $W $S $controls_primary, vce(hc3)
postterms `pf' "rob_singleyear" "overall" "$W $S"

regress att8_total_2425 $W $S $controls_primary, vce(hc3)
postterms `pf' "rob_att8total" "overall" "$W $S"

regress att8screng_2425 $W $S $controls_primary, vce(hc3)
postterms `pf' "rob_att8eng" "overall" "$W $S"

gen wxs_p = $W * $S
regress p8mea_avg $W $S wxs_p $controls_primary, vce(hc3)
postterms `pf' "rob_wxs" "overall" "$W $S wxs_p"

* Single-rated lessons (20 Aug 2026, Chapter 2 referee round three). About a
* third of observed lessons were rated by one researcher, those lessons score
* a little lower, and the share of such lessons correlates -0.25 with a
* school's in-lesson warmth. Two checks: the share as a control, and the
* primary spec on schools with no single-rated lesson.
* London control (referee close-out, 21 Aug 2026)
regress p8mea_avg $W $S london $controls_primary, vce(hc3)
postterms `pf' "rob_london" "overall" "$W $S london"

capture confirm variable share_single_rated
if !_rc {
    regress p8mea_avg $W $S share_single_rated $controls_primary, vce(hc3)
    postterms `pf' "rob_singlerater_ctrl" "overall" "$W $S share_single_rated"
    regress p8mea_avg $W $S $controls_primary if share_single_rated == 0, vce(hc3)
    postterms `pf' "rob_doublerated" "overall" "$W $S"
}

capture confirm variable semh_baseline_2016
if !_rc {
    regress p8mea_avg $W $S semh_baseline_2016 $controls_primary, vce(hc3)
    postterms `pf' "rob_semh" "overall" "$W $S semh_baseline_2016"
    * The SEMH control costs schools. Re-estimate the primary spec on exactly
    * the schools the SEMH row uses, so attenuation from the CONTROL is
    * separable from attenuation from the SAMPLE.
    regress p8mea_avg $W $S $controls_primary if !missing(semh_baseline_2016), vce(hc3)
    postterms `pf' "rob_semh_sample" "overall" "$W $S"
}
restore

* The primary spec with the late-entry schools PUT BACK. Quoted in the notes to
* tab_spec_ladder.tex as the reassurance that the exclusion is not doing the work.
regress p8mea_avg $W $S $controls_primary, vce(hc3)
postterms `pf' "primary_late" "overall" "$W $S"

postclose `pf'

use "`ROOT'/thesis/tables/ch3_estimates.dta", clear
export delimited using "`ROOT'/thesis/tables/ch3_estimates.csv", replace
list spec outcome term b pval n r2 if spec=="stage1", clean noobs
display "ch3_estimates.csv written."
