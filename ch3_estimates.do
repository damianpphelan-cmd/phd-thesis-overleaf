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
    p8mea_2324 att8screng_2425 semh_baseline_2016 ///
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
postfile `pf' str14 spec str14 outcome str24 term ///
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
*   (iii) the trio of outcomes reported in the chapter body.
* Everything else -- controls, HC3, the enacted culture scores -- is unchanged,
* so a difference between these rows and the Python estimates in
* analyse_ch3_batch.py is a specification difference, not a software one.
* ================================================================
global ctrl_ofsted_f "2.grade2019_filled 3.grade2019_filled 4.grade2019_filled"
global controls_primary "$ctrl_cont $ctrl_bin $ctrl_ofsted_f"

preserve
keep if late_entry != 1

foreach outcome in p8mea_avg p8meaeng_avg p8meamat_avg {
    local lbl = cond("`outcome'"=="p8mea_avg",    "overall", ///
                cond("`outcome'"=="p8meaeng_avg", "english", "maths"))

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
restore

postclose `pf'

use "`ROOT'/thesis/tables/ch3_estimates.dta", clear
export delimited using "`ROOT'/thesis/tables/ch3_estimates.csv", replace
list spec outcome term b pval n r2 if spec=="stage1", clean noobs
display "ch3_estimates.csv written."
