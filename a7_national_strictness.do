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
    ofsted_llmstrictnessscore size late_entry grade2019_filled
destring `numvars', replace force

* 19 Aug 2026 (verification finding C3-2): the national extension now follows the
* same sample rules as every other outcome regression in the chapter -- schools
* whose statutory entry age is 13+ are excluded, and the pre-COVID grade control
* is the predecessor-filled version. Before this the 3,147 included 95 late-entry
* schools and Panel B used the unfilled grade.
keep if late_entry != 1
* Standardised over the estimation sample (schools with an outcome), so the
* coefficient is per standard deviation of the score, as the chapter states
* (decision (b), 19 Aug 2026). The raw score is on a 1-5 scale with SD ~0.69.
quietly summarize ofsted_llmstrictnessscore if !missing(p8mea_avg)
scalar sd_ofs = r(sd)
replace ofsted_llmstrictnessscore = (ofsted_llmstrictnessscore - r(mean)) / r(sd)

* ---- Macros (identical to cell 2) ----
global ctrl_cont "ks2 fsm eal sen log_size years_since_ofsted"
global ctrl_bin  "academy urban_bin selective"
* The 2019 grade enters with grade 2 (Good) as the factor base: 2. is
* listed FIRST because Stata merges same-variable factor specs and takes
* the first listed level as the base, so the 2. term is the omitted base
* and the estimated indicators are for grades 3 and 4. Grade 1 is
* unlisted and pools with the base (Outstanding schools were exempt from
* routine inspection before 2020, so that label is the stalest category).
* Do NOT shorten the list to 3./4. only: that silently rebases to grade 3
* and pools the grade-3 schools into the base (the 25 Aug 2026 mistake,
* caught 28 Aug before any published number was regenerated under it).
global ctrl_ofsted "2.grade2019_filled 3.grade2019_filled 4.grade2019_filled"
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

* ---- Reports predating the outcome window (referee point, 21 Aug 2026) ----
* years_since_ofsted is measured from 31 Aug 2024, so > 2 means the report was
* published before 1 Sept 2022, i.e. before either outcome cohort's results
* existed. The subsample regression answers the reverse-causality reading of
* the national extension directly.
gen byte pre2022 = years_since_ofsted > 2 if !missing(years_since_ofsted)

regress p8mea_avg ofsted_llmstrictnessscore $controls_ngrade if pre2022 == 1, vce(hc3)
local b  = _b[ofsted_llmstrictnessscore]
local se = _se[ofsted_llmstrictnessscore]
local p  = 2*ttail(e(df_r), abs(`b'/`se'))
post `pf' ("Overall") ("pre22ng") (`b') (`se') (`p') (e(N)) (e(r2))
display "pre22 no-grade: b=" %7.4f `b' " N=" e(N)

regress p8mea_avg ofsted_llmstrictnessscore $controls if pre2022 == 1, vce(hc3)
local b  = _b[ofsted_llmstrictnessscore]
local se = _se[ofsted_llmstrictnessscore]
local p  = 2*ttail(e(df_r), abs(`b'/`se'))
post `pf' ("Overall") ("pre22gr") (`b') (`se') (`p') (e(N)) (e(r2))
display "pre22 grade19:  b=" %7.4f `b' " N=" e(N)

* Share of the no-grade estimation sample whose report predates the window.
regress p8mea_avg ofsted_llmstrictnessscore $controls_ngrade, vce(hc3)
summarize pre2022 if e(sample)
post `pf' ("Overall") ("pre22shr") (r(mean)) (.) (.) (r(N)) (.)

* Does the association decay with report age? Interaction of the standardised
* score with centred years-since-inspection, no-grade spec, overall P8. A
* persistent signal should show no decay (referee point, 21 Aug 2026).
quietly summarize years_since_ofsted if !missing(p8mea_avg, ofsted_llmstrictnessscore)
gen double ys_c = years_since_ofsted - r(mean)
gen double score_x_age = ofsted_llmstrictnessscore * ys_c
regress p8mea_avg ofsted_llmstrictnessscore score_x_age $controls_ngrade, vce(hc3)
local b  = _b[score_x_age]
local se = _se[score_x_age]
local p  = 2*ttail(e(df_r), abs(`b'/`se'))
post `pf' ("Overall") ("agexint") (`b') (`se') (`p') (e(N)) (e(r2))
display "score x age:   b=" %7.4f `b' " p=" %6.4f `p'

postclose `pf'

use "C:/Users/damia/OneDrive/Documents/Schools Project/thesis/tables/a7_estimates.dta", clear
export delimited using ///
    "C:/Users/damia/OneDrive/Documents/Schools Project/thesis/tables/a7_estimates.csv", ///
    replace
list, clean

display "A7 estimates written."

exit, clear
