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

global W  gs_warmth_enacted
global S  gs_strictness_enacted
global T  gs_teaching_enacted

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
    regress `outcome' gs_warmth_espoused gs_strictness_espoused $controls, vce(hc3)
    postterms `pf' "espoused" "`lbl'" "gs_warmth_espoused gs_strictness_espoused"

    regress `outcome' gs_warmth_espoused gs_strictness_espoused $controls if tier1, vce(hc3)
    postterms `pf' "espoused_t1" "`lbl'" "gs_warmth_espoused gs_strictness_espoused"
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
