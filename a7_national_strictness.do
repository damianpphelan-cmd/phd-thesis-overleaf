* ================================================================
* A7: national extension with and without the pre-COVID Ofsted grade
*
* The published spec omits the Ofsted grade "to avoid conditioning on a
* downstream confounder". That is defensible, but it is not the conservative
* choice: the LLM strictness score is read from a report about a school that
* Ofsted judged, and Ofsted grades correlate with P8. The obvious examiner
* challenge is that the coefficient partly measures "Ofsted approved of this
* school".
*
* ofsted_grade_2019 is the pre-COVID grade already used as $ctrl_ofsted in the
* primary Tier 1 specification, so this adds no new variable to the thesis --
* it applies an existing control to a specification that omitted it.
*
* Writes a tidy CSV of estimates; thesis/make_national_strictness.py builds
* the LaTeX table from it.
*
* Run (the do-file path must be ABSOLUTE -- with a relative path Stata cannot
* find it, silently drops out of batch mode and sits in the GUI forever):
*   "C:\Program Files\StataNow19\StataMP-64.exe" /e do "C:\full\path\thesis\a7_national_strictness.do"
* ================================================================

clear all
set more off

adopath ++ "C:\Users\damia\ado\plus"

* ---- Load data (identical to chapter3_analysis.ipynb cell 1) ----
import delimited "C:/Users/damia/OneDrive/Documents/Schools Project/analysis_dataset.csv", ///
    clear stringcols(_all) case(lower)

foreach v of varlist eal sen {
    replace `v' = subinstr(`v', "%", "", .)
    destring `v', replace
}

local numvars gs_warmth_visit gs_strictness_visit gs_teaching_visit ///
    gs_warmth_espoused gs_strictness_espoused gs_teaching_espoused ///
    p8mea_avg p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg ///
    ks2 fsm log_size academy urban_bin selective ///
    years_since_ofsted ofsted_grade_2019 ///
    ofsted_llmstrictnessscore size
destring `numvars', replace force

* ---- Macros (identical to cell 2) ----
global ctrl_cont "ks2 fsm eal sen log_size years_since_ofsted"
global ctrl_bin  "academy urban_bin selective"
global ctrl_ofsted "2.ofsted_grade_2019 3.ofsted_grade_2019 4.ofsted_grade_2019"
global controls        "$ctrl_cont $ctrl_bin $ctrl_ofsted"
global controls_ngrade "$ctrl_cont $ctrl_bin"

* ---- Collect estimates ----
tempname pf
postfile `pf' str12 outcome str8 spec double(b se pval n r2) ///
    using "C:/Users/damia/OneDrive/Documents/Schools Project/thesis/tables/a7_estimates.dta", replace

foreach outcome in p8mea_avg p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg {
    local lbl = cond("`outcome'"=="p8mea_avg",     "Overall", ///
                cond("`outcome'"=="p8meaeng_avg",  "English", ///
                cond("`outcome'"=="p8meamat_avg",  "Maths",   ///
                cond("`outcome'"=="p8meaebac_avg", "EBaC",    "Open"))))

    * Panel A: published specification, no Ofsted grade
    regress `outcome' ofsted_llmstrictnessscore $controls_ngrade, vce(hc3)
    local b  = _b[ofsted_llmstrictnessscore]
    local se = _se[ofsted_llmstrictnessscore]
    local p  = 2*ttail(e(df_r), abs(`b'/`se'))
    post `pf' ("`lbl'") ("nograde") (`b') (`se') (`p') (e(N)) (e(r2))
    display "A `lbl': b=" %7.4f `b' " se=" %6.4f `se' " N=" e(N) " R2=" %6.4f e(r2)

    * Panel B: adding the pre-COVID (2019) Ofsted grade
    regress `outcome' ofsted_llmstrictnessscore $controls, vce(hc3)
    local b  = _b[ofsted_llmstrictnessscore]
    local se = _se[ofsted_llmstrictnessscore]
    local p  = 2*ttail(e(df_r), abs(`b'/`se'))
    post `pf' ("`lbl'") ("grade19") (`b') (`se') (`p') (e(N)) (e(r2))
    display "B `lbl': b=" %7.4f `b' " se=" %6.4f `se' " N=" e(N) " R2=" %6.4f e(r2)
}

postclose `pf'

use "C:/Users/damia/OneDrive/Documents/Schools Project/thesis/tables/a7_estimates.dta", clear
export delimited using ///
    "C:/Users/damia/OneDrive/Documents/Schools Project/thesis/tables/a7_estimates.csv", ///
    replace
list, clean

display "A7 estimates written."

exit, clear
