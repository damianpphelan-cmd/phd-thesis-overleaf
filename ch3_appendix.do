* ================================================================
* Chapter 3 APPENDIX estimates on the PRIMARY specification.
* 19 Aug 2026, Damian's Option A: the eleven appendix tables that were built on
* 14 Aug from Python batch output (mixed specifications: n=100 without
* years_since_ofsted; n=103/96 without the late-entry exclusion) are
* re-estimated here on the same footing as the body:
*   - late-entry schools (statutory entry age 13+) excluded everywhere
*   - controls: ks2 fsm eal sen log_size years_since_ofsted academy urban_bin
*     selective, plus the predecessor-filled pre-COVID grade as dummies
*   - HC3 robust SEs, except the behaviour-policy rows, clustered on the shared
*     document digest (trust templates)
*   - predictors z-standardised WITHIN the estimation sample (as the appendix
*     captions state). The body tables (ch3_estimates.do) regress on the raw 0-10
*     scores; a 'primary_z' block at the end gives the body spec per SD so the
*     two scalings can be compared (verification finding C3-1).
* Input:  thesis/tables/ch3_appendix_input.csv  (build_ch3_appendix_input.py)
* Output: thesis/tables/ch3_appendix_estimates.csv
* Run:    "C:\Program Files\StataNow19\StataMP-64.exe" -e do "<abs path>"
* ================================================================
clear all
set more off
local ROOT "C:/Users/damia/OneDrive/Documents/Schools Project"
import delimited "`ROOT'/thesis/tables/ch3_appendix_input.csv", clear case(lower) ///
    stringcols(_all)
foreach v of varlist _all {
    capture destring `v', replace
}

global ctrl "ks2 fsm eal sen log_size years_since_ofsted academy urban_bin selective"
* The 2019 grade enters with grade 2 (Good) as the factor base: 2. is
* listed FIRST because Stata merges same-variable factor specs and takes
* the first listed level as the base, so the 2. term is the omitted base
* and the estimated indicators are for grades 3 and 4. Grade 1 is
* unlisted and pools with the base (Outstanding schools were exempt from
* routine inspection before 2020, so that label is the stalest category).
* Do NOT shorten the list to 3./4. only: that silently rebases to grade 3
* and pools the grade-3 schools into the base (the 25 Aug 2026 mistake,
* caught 28 Aug before any published number was regenerated under it).
global gradef "2.grade2019_filled 3.grade2019_filled 4.grade2019_filled"
global ctrlg "$ctrl $gradef"

keep if late_entry != 1
gen byte gold = gs_data_tier == "full"

* One scale for the gold scores across body and appendix (decision (b)): z over
* the late-entry-excluded visited schools, exactly as ch3_estimates.do does.
foreach v in gs_warmth_enacted gs_strictness_enacted gs_teaching_enacted gs_warmth_espoused gs_strictness_espoused {
    quietly summarize `v'
    gen double g_`v' = (`v' - r(mean)) / r(sd)
}

capture postclose apf
postfile apf str24 table str24 panel str30 model str20 outcome str40 term ///
    double(b se pval n r2) str8 vce using "`ROOT'/thesis/tables/ch3_appendix_estimates.dta", replace

* z-standardise a variable within a sample marker; returns z_<var>
capture program drop zwithin
program define zwithin
    args v smp
    capture drop z_`v'
    quietly summarize `v' if `smp'
    gen double z_`v' = (`v' - r(mean)) / r(sd) if `smp'
end

* post named terms from the model in memory
capture program drop postapp
program define postapp
    args table panel model outcome terms vce
    foreach t of local terms {
        local b = _b[`t']
        local se = _se[`t']
        local p = 2*ttail(e(df_r), abs(`b'/`se'))
        post apf ("`table'") ("`panel'") ("`model'") ("`outcome'") ("`t'") ///
            (`b') (`se') (`p') (e(N)) (e(r2)) ("`vce'")
    }
end

* ---------------------------------------------------------------
* 1. SUB-SCORES jointly (tab_subscores): gold, three outcomes, + VIFs
* ---------------------------------------------------------------
foreach y in p8mea_avg p8meaeng_avg p8meamat_avg {
    local lbl = cond("`y'"=="p8mea_avg","overall",cond("`y'"=="p8meaeng_avg","english","maths"))
    quietly regress `y' gs_w1 gs_w2 gs_s1 gs_s2 gs_t1 $ctrlg if gold, vce(hc3)
    gen byte smp = e(sample)
    foreach v in gs_w1 gs_w2 gs_s1 gs_s2 gs_t1 {
        zwithin `v' smp
    }
    regress `y' z_gs_w1 z_gs_w2 z_gs_s1 z_gs_s2 z_gs_t1 $ctrlg if smp, vce(hc3)
    postapp "subscores" "" "joint" "`lbl'" "z_gs_w1 z_gs_w2 z_gs_s1 z_gs_s2 z_gs_t1" "hc3"
    if "`lbl'" == "overall" {
        quietly regress `y' z_gs_w1 z_gs_w2 z_gs_s1 z_gs_s2 z_gs_t1 $ctrlg if smp
        estat vif
        * VIFs for the five sub-scores are printed; capture into the postfile
        matrix V = r(vif)
        foreach v in gs_w1 gs_w2 gs_s1 gs_s2 gs_t1 {
            local others ""
            foreach o in gs_w1 gs_w2 gs_s1 gs_s2 gs_t1 {
                if "`o'" != "`v'" local others "`others' z_`o'"
            }
            quietly regress z_`v' `others' $ctrlg if smp
            local vif = 1/(1-e(r2))
            post apf ("subscores") ("vif") ("joint") ("overall") ("z_`v'") (`vif') (.) (.) (e(N)) (.) ("")
        }
    }
    drop smp z_gs_w1 z_gs_w2 z_gs_s1 z_gs_s2 z_gs_t1
}

* ---------------------------------------------------------------
* 2. ITEMS (tab_items_fdr): each item alone + controls, overall P8, gold
* ---------------------------------------------------------------
foreach v of varlist it_* {
    quietly regress p8mea_avg `v' $ctrlg if gold, vce(hc3)
    gen byte smp = e(sample)
    zwithin `v' smp
    regress p8mea_avg z_`v' $ctrlg if smp, vce(hc3)
    postapp "items" "" "single" "overall" "z_`v'" "hc3"
    drop smp z_`v'
}

* ---------------------------------------------------------------
* 3. TYPOLOGY (tab_typology): gold (filled grade) and national Ofsted (A: no
*    grade, B: grade). Quadrants = median splits within the estimation sample.
* ---------------------------------------------------------------
capture program drop typology
program define typology
    args wv sv smpcond usegrade label
    if `usegrade' local ctrls "$ctrlg"
    else local ctrls "$ctrl"
    quietly regress p8mea_avg `wv' `sv' `ctrls' if `smpcond', vce(hc3)
    gen byte smp = e(sample)
    zwithin `wv' smp
    zwithin `sv' smp
    gen double z_wxs = z_`wv' * z_`sv' if smp
    regress p8mea_avg z_`wv' z_`sv' z_wxs `ctrls' if smp, vce(hc3)
    postapp "typology" "`label'" "interaction" "overall" "z_`wv' z_`sv' z_wxs" "hc3"
    * quadrants: median splits within the estimation sample
    quietly summarize `wv' if smp, detail
    local mw = r(p50)
    quietly summarize `sv' if smp, detail
    local ms = r(p50)
    gen byte hw = `wv' > `mw' if smp
    gen byte hs = `sv' > `ms' if smp
    gen byte quad = cond(hw & hs, 1, cond(!hw & hs, 2, cond(hw & !hs, 3, 4))) if smp
    * adjusted means: quadrant dummies without constant + demeaned controls
    local dem ""
    foreach c of global ctrl {
        quietly summarize `c' if smp
        gen double dm_`c' = `c' - r(mean) if smp
        local dem "`dem' dm_`c'"
    }
    if `usegrade' {
        foreach g in 2 3 4 {
            gen double gd`g' = grade2019_filled == `g' if smp
            quietly summarize gd`g' if smp
            replace gd`g' = gd`g' - r(mean) if smp
            local dem "`dem' gd`g'"
        }
    }
    regress p8mea_avg ibn.quad `dem' if smp, noconstant vce(hc3)
    * The HC3 leverage adjustment is undefined when a covariate cell contains a
    * single school (h_ii = 1), in which case Stata returns a missing VCE and
    * _se[] reads 0. Fall back to HC1 for the adjusted means and record it.
    local vlbl "hc3"
    if missing(_se[1.quad]) | _se[1.quad] == 0 {
        regress p8mea_avg ibn.quad `dem' if smp, noconstant vce(robust)
        local vlbl "hc1"
    }
    foreach q in 1 2 3 4 {
        local b = _b[`q'.quad]
        local se = _se[`q'.quad]
        quietly count if quad == `q' & smp
        post apf ("typology") ("`label'") ("quadrant_adjmean") ("overall") ("quad`q'") (`b') (`se') (.) (r(N)) (.) ("`vlbl'")
    }
    gen byte auth = quad == 1 if smp
    regress p8mea_avg auth `ctrls' if smp, vce(hc3)
    postapp "typology" "`label'" "auth_vs_rest" "overall" "auth" "hc3"
    drop smp z_`wv' z_`sv' z_wxs hw hs quad auth dm_*
    capture drop gd2 gd3 gd4
end
typology gs_warmth_enacted gs_strictness_enacted "gold" 1 "gold"
typology ofsted_llmwarmthscore ofsted_llmstrictnessscore "1" 0 "natA"
typology ofsted_llmwarmthscore ofsted_llmstrictnessscore "1" 1 "natB"

* ---------------------------------------------------------------
* 4. GAPS (tab_gaps): z within instrument; signed, absolute, absolute+quadratics
* ---------------------------------------------------------------
capture program drop gapmod
program define gapmod
    args enac doc smpcond label vce
    quietly regress p8mea_avg `enac' `doc' $ctrlg if `smpcond', vce(hc3)
    gen byte smp = e(sample)
    zwithin `enac' smp
    zwithin `doc' smp
    gen double sgap = z_`doc' - z_`enac' if smp
    gen double agap = abs(sgap) if smp
    gen double zd2 = z_`doc'^2 if smp
    gen double ze2 = z_`enac'^2 if smp
    if "`vce'" == "cluster" local vopt "vce(cluster bp_digest_id)"
    else local vopt "vce(hc3)"
    regress p8mea_avg z_`enac' sgap $ctrlg if smp, `vopt'
    postapp "gaps" "`label'" "signed" "overall" "z_`enac' sgap" "`vce'"
    regress p8mea_avg z_`enac' agap $ctrlg if smp, `vopt'
    postapp "gaps" "`label'" "absolute" "overall" "z_`enac' agap" "`vce'"
    regress p8mea_avg z_`enac' agap zd2 ze2 $ctrlg if smp, `vopt'
    postapp "gaps" "`label'" "absolute_quad" "overall" "z_`enac' agap zd2 ze2" "`vce'"
    drop smp z_`enac' z_`doc' sgap agap zd2 ze2
end
gapmod gs_warmth_enacted gs_warmth_espoused "gold" "gold_warmth" "hc3"
gapmod gs_strictness_enacted gs_strictness_espoused "gold" "gold_strictness" "hc3"
gapmod ofsted_llmwarmthscore bp_llmwarmthscore_v4 "1" "nat_bp_warmth" "cluster"
gapmod ofsted_llmstrictnessscore bp_llmstrictnessscore_v4 "1" "nat_bp_strictness" "cluster"
gapmod ofsted_llmwarmthscore web_llmwarmthscore_v18 "1" "nat_web_warmth" "hc3"
gapmod ofsted_llmstrictnessscore web_llmstrictnessscore_v15 "1" "nat_web_strictness" "hc3"

* ---------------------------------------------------------------
* 5. PARENT VIEW (tab_parentview)
* ---------------------------------------------------------------
foreach v in web_llmwarmthscore_v18 web_llmwarmthscore_v13 bp_llmwarmthscore_v4 ofsted_llmwarmthscore {
    quietly regress pv_warmth `v' $ctrl, vce(hc3)
    gen byte smp = e(sample)
    zwithin `v' smp
    if "`v'" == "bp_llmwarmthscore_v4" local vopt "vce(cluster bp_digest_id)"
    else local vopt "vce(hc3)"
    regress pv_warmth z_`v' $ctrl if smp, `vopt'
    postapp "parentview" "A" "`v'" "pv_warmth" "z_`v'" "`=cond("`v'"=="bp_llmwarmthscore_v4","cluster","hc3")'"
    * correlations on the same sample
    quietly correlate pv_warmth `v' if smp
    post apf ("parentview") ("A_corr") ("`v'") ("pv_warmth") ("pearson") (r(rho)) (.) (.) (r(N)) (.) ("")
    quietly spearman pv_warmth `v' if smp
    post apf ("parentview") ("A_corr") ("`v'") ("pv_warmth") ("spearman") (r(rho)) (.) (r(p)) (r(N)) (.) ("")
    drop smp z_`v'
}
foreach y in p8mea_avg p8meaeng_avg p8meamat_avg {
    local lbl = cond("`y'"=="p8mea_avg","overall",cond("`y'"=="p8meaeng_avg","english","maths"))
    quietly regress `y' pv_warmth $ctrlg, vce(hc3)
    gen byte smp = e(sample)
    zwithin pv_warmth smp
    regress `y' z_pv_warmth $ctrlg if smp, vce(hc3)
    postapp "parentview" "B" "pv_to_p8" "`lbl'" "z_pv_warmth" "hc3"
    drop smp z_pv_warmth
}

* ---------------------------------------------------------------
* 6. LLM x P8 MATRIX (tab_llm_p8_matrix): 15 predictors x 5 outcomes, grade
*    panel (B) and no-grade panel (A); BP rows clustered
* ---------------------------------------------------------------
local preds ofsted_llmstrictnessscore ofsted_llmwarmthscore ofsted_llmteachingscore ///
    bp_llmstrictnessscore_v4 bp_llmwarmthscore_v4 web_llmwarmthscore_v13 ///
    web_llmstrictnessscore_v13 web_llmstrictnessscore_v15 web_tradethos_v2 ///
    web_tradpedagogy_v1b faith_prominence trx_llmstrictnessscore_v13 ///
    trx_llmteachingscore_v3 trx_llmwarmthscore_v15 trx_llmwarmthscore_counts
foreach pr of local preds {
    foreach y in p8mea_avg p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg {
        local lbl = cond("`y'"=="p8mea_avg","overall",cond("`y'"=="p8meaeng_avg","english", ///
                    cond("`y'"=="p8meamat_avg","maths",cond("`y'"=="p8meaebac_avg","ebac","open"))))
        if strpos("`pr'", "bp_") local vopt "vce(cluster bp_digest_id)"
        else local vopt "vce(hc3)"
        local vc = cond(strpos("`pr'", "bp_"), "cluster", "hc3")
        foreach panel in A B {
            local cc = cond("`panel'"=="A", "$ctrl", "$ctrlg")
            quietly regress `y' `pr' `cc', vce(hc3)
            gen byte smp = e(sample)
            zwithin `pr' smp
            regress `y' z_`pr' `cc' if smp, `vopt'
            postapp "llm_matrix" "`panel'" "`pr'" "`lbl'" "z_`pr'" "`vc'"
            drop smp z_`pr'
        }
    }
}

* ---------------------------------------------------------------
* 7. ENTRY RATES (tab_entry_rates): Panel A no grade / B grade; gold W,S and
*    national Ofsted S on ebacc/hum/lang entry; channel decomposition on EBaC P8
* ---------------------------------------------------------------
foreach panel in A B {
    local cc = cond("`panel'"=="A", "$ctrl", "$ctrlg")
    foreach y in ebacc_entry hum_entry lang_entry {
        quietly regress `y' gs_warmth_enacted gs_strictness_enacted `cc' if gold, vce(hc3)
        gen byte smp = e(sample)
        zwithin gs_warmth_enacted smp
        zwithin gs_strictness_enacted smp
        regress `y' z_gs_warmth_enacted z_gs_strictness_enacted `cc' if smp, vce(hc3)
        postapp "entry" "`panel'" "gold" "`y'" "z_gs_warmth_enacted z_gs_strictness_enacted" "hc3"
        drop smp z_gs_warmth_enacted z_gs_strictness_enacted
        quietly regress `y' ofsted_llmstrictnessscore `cc', vce(hc3)
        gen byte smp = e(sample)
        zwithin ofsted_llmstrictnessscore smp
        regress `y' z_ofsted_llmstrictnessscore `cc' if smp, vce(hc3)
        postapp "entry" "`panel'" "national" "`y'" "z_ofsted_llmstrictnessscore" "hc3"
        drop smp z_ofsted_llmstrictnessscore
    }
    * channel: national
    quietly regress p8meaebac_avg ofsted_llmstrictnessscore ebacc_entry `cc', vce(hc3)
    gen byte smp = e(sample)
    zwithin ofsted_llmstrictnessscore smp
    regress p8meaebac_avg z_ofsted_llmstrictnessscore `cc' if smp, vce(hc3)
    postapp "channel" "`panel'" "national_without" "ebac" "z_ofsted_llmstrictnessscore" "hc3"
    regress p8meaebac_avg z_ofsted_llmstrictnessscore ebacc_entry `cc' if smp, vce(hc3)
    postapp "channel" "`panel'" "national_with" "ebac" "z_ofsted_llmstrictnessscore ebacc_entry" "hc3"
    drop smp z_ofsted_llmstrictnessscore
    * channel: gold (S alone, as the batch did)
    quietly regress p8meaebac_avg gs_strictness_enacted ebacc_entry `cc' if gold, vce(hc3)
    gen byte smp = e(sample)
    zwithin gs_strictness_enacted smp
    regress p8meaebac_avg z_gs_strictness_enacted `cc' if smp, vce(hc3)
    postapp "channel" "`panel'" "gold_without" "ebac" "z_gs_strictness_enacted" "hc3"
    regress p8meaebac_avg z_gs_strictness_enacted ebacc_entry `cc' if smp, vce(hc3)
    postapp "channel" "`panel'" "gold_with" "ebac" "z_gs_strictness_enacted ebacc_entry" "hc3"
    drop smp z_gs_strictness_enacted
}

* ---------------------------------------------------------------
* 8. PSEUDO-P8 2024/25 (tab_p8_proxy): gold W,S (z within sample) on the pseudo
*    outcomes and on real P8 for the same schools; national Ofsted S likewise.
*    Panel A without the grade control, Panel B with (primary).
* ---------------------------------------------------------------
foreach panel in A B {
    local cc = cond("`panel'"=="A", "$ctrl", "$ctrlg")
    quietly regress pseudo_p8_2425 gs_warmth_enacted gs_strictness_enacted `cc' if gold, vce(hc3)
    gen byte smp = e(sample)
    zwithin gs_warmth_enacted smp
    zwithin gs_strictness_enacted smp
    foreach y in pseudo_p8_2425 pseudo_p8_2425_eng pseudo_p8_2425_mat p8mea_avg {
        regress `y' z_gs_warmth_enacted z_gs_strictness_enacted `cc' if smp, vce(hc3)
        postapp "p8proxy" "`panel'" "gold" "`y'" "z_gs_warmth_enacted z_gs_strictness_enacted" "hc3"
    }
    drop smp z_gs_warmth_enacted z_gs_strictness_enacted
    quietly regress pseudo_p8_2425 ofsted_llmstrictnessscore `cc', vce(hc3)
    gen byte smp = e(sample)
    zwithin ofsted_llmstrictnessscore smp
    foreach y in pseudo_p8_2425 pseudo_p8_2425_eng pseudo_p8_2425_mat p8mea_avg {
        regress `y' z_ofsted_llmstrictnessscore `cc' if smp, vce(hc3)
        postapp "p8proxy" "`panel'" "national" "`y'" "z_ofsted_llmstrictnessscore" "hc3"
    }
    drop smp z_ofsted_llmstrictnessscore
}
* raw-scale twin for the body's 'within 0.04' sentence
regress pseudo_p8_2425 g_gs_warmth_enacted g_gs_strictness_enacted $ctrlg if gold, vce(hc3)
gen byte smp = e(sample)
postapp "p8proxy" "z" "gold_pseudo" "overall" "g_gs_warmth_enacted g_gs_strictness_enacted" "hc3"
regress p8mea_avg g_gs_warmth_enacted g_gs_strictness_enacted $ctrlg if smp, vce(hc3)
postapp "p8proxy" "z" "gold_real" "overall" "g_gs_warmth_enacted g_gs_strictness_enacted" "hc3"
drop smp
quietly correlate pseudo_p8_2425 p8mea_avg if !missing(pseudo_p8_2425, p8mea_avg)
post apf ("p8proxy") ("") ("corr_pseudo_vs_real_p8avg") ("overall") ("pearson") (r(rho)) (.) (.) (r(N)) (.) ("")

* ---------------------------------------------------------------
* 9. SEMH MECHANISM (tab_semh_mechanism): current SEMH SHARE of roll on culture
*    (z within sample) + 2015/16 SEMH share, primary controls. Both shares use the
*    current roll as denominator (2015/16 roll not in the dataset).
* ---------------------------------------------------------------
foreach spec in tier1_S tier1_W national_S {
    local pr = cond("`spec'"=="tier1_S","gs_strictness_enacted",cond("`spec'"=="tier1_W","gs_warmth_enacted","ofsted_llmstrictnessscore"))
    local cnd = cond(strpos("`spec'","tier1"), "gold", "1")
    quietly regress semh_share_current `pr' semh_share_2016 $ctrlg if `cnd', vce(hc3)
    gen byte smp = e(sample)
    zwithin `pr' smp
    regress semh_share_current z_`pr' semh_share_2016 $ctrlg if smp, vce(hc3)
    postapp "semh" "" "`spec'" "semh_share" "z_`pr' semh_share_2016" "hc3"
    drop smp z_`pr'
}

* ---------------------------------------------------------------
* 10. HEADTEACHER CONTINUITY (tab_continuity_robustness): primary spec, full
*     gold sample and the two GIAS-continuity subsamples (head_same from
*     build_head_continuity.py: same head 1 Sep 2022 and 1 Jul 2025)
* ---------------------------------------------------------------
foreach y in p8mea_avg p8meaeng_avg p8meamat_avg p8meaebac_avg p8meaopen_avg {
    local lbl = cond("`y'"=="p8mea_avg","overall",cond("`y'"=="p8meaeng_avg","english", ///
                cond("`y'"=="p8meamat_avg","maths",cond("`y'"=="p8meaebac_avg","ebac","open"))))
    regress `y' g_gs_warmth_enacted g_gs_strictness_enacted $ctrlg if gold, vce(hc3)
    postapp "continuity" "all" "z" "`lbl'" "g_gs_warmth_enacted g_gs_strictness_enacted" "hc3"
    regress `y' g_gs_warmth_enacted g_gs_strictness_enacted $ctrlg if gold & head_same == 1, vce(hc3)
    postapp "continuity" "unchanged" "z" "`lbl'" "g_gs_warmth_enacted g_gs_strictness_enacted" "hc3"
    regress `y' g_gs_warmth_enacted g_gs_strictness_enacted $ctrlg if gold & head_same == 0, vce(hc3)
    postapp "continuity" "changed" "z" "`lbl'" "g_gs_warmth_enacted g_gs_strictness_enacted" "hc3"
}
quietly count if gold & head_same == 1
post apf ("continuity") ("count") ("unchanged") ("") ("n") (r(N)) (.) (.) (.) (.) ("")
quietly count if gold & head_same == 0
post apf ("continuity") ("count") ("changed") ("") ("n") (r(N)) (.) (.) (.) (.) ("")
quietly count if gold & !missing(head_same)
post apf ("continuity") ("count") ("determined") ("") ("n") (r(N)) (.) (.) (.) (.) ("")

* ---------------------------------------------------------------
* 11. ESPOUSED on the primary spec, same schools as the body (prose check C3-3)
* ---------------------------------------------------------------
foreach y in p8mea_avg p8meaeng_avg p8meamat_avg {
    local lbl = cond("`y'"=="p8mea_avg","overall",cond("`y'"=="p8meaeng_avg","english","maths"))
    regress `y' g_gs_warmth_espoused g_gs_strictness_espoused $ctrlg if gold, vce(hc3)
    postapp "espoused_primary" "" "z" "`lbl'" "g_gs_warmth_espoused g_gs_strictness_espoused" "hc3"
}

* ---------------------------------------------------------------
* 12. THE BODY SPEC PER SD (finding C3-1): z within sample, overall/eng/maths
* ---------------------------------------------------------------
foreach y in p8mea_avg p8meaeng_avg p8meamat_avg {
    local lbl = cond("`y'"=="p8mea_avg","overall",cond("`y'"=="p8meaeng_avg","english","maths"))
    quietly regress `y' gs_warmth_enacted gs_strictness_enacted $ctrlg if gold, vce(hc3)
    gen byte smp = e(sample)
    zwithin gs_warmth_enacted smp
    zwithin gs_strictness_enacted smp
    zwithin gs_teaching_enacted smp
    regress `y' z_gs_warmth_enacted z_gs_strictness_enacted $ctrlg if smp, vce(hc3)
    postapp "primary_z" "" "stage1" "`lbl'" "z_gs_warmth_enacted z_gs_strictness_enacted" "hc3"
    regress `y' z_gs_warmth_enacted $ctrlg if smp, vce(hc3)
    postapp "primary_z" "" "warmthonly" "`lbl'" "z_gs_warmth_enacted" "hc3"
    regress `y' z_gs_strictness_enacted $ctrlg if smp, vce(hc3)
    postapp "primary_z" "" "strictonly" "`lbl'" "z_gs_strictness_enacted" "hc3"
    regress `y' z_gs_teaching_enacted $ctrlg if smp, vce(hc3)
    postapp "primary_z" "" "stage2" "`lbl'" "z_gs_teaching_enacted" "hc3"
    regress `y' z_gs_warmth_enacted z_gs_strictness_enacted z_gs_teaching_enacted $ctrlg if smp, vce(hc3)
    postapp "primary_z" "" "stage3" "`lbl'" "z_gs_warmth_enacted z_gs_strictness_enacted z_gs_teaching_enacted" "hc3"
    quietly summarize gs_warmth_enacted if smp
    post apf ("primary_z") ("sd") ("sd_in_sample") ("`lbl'") ("gs_warmth_enacted") (r(sd)) (.) (.) (r(N)) (.) ("")
    quietly summarize gs_strictness_enacted if smp
    post apf ("primary_z") ("sd") ("sd_in_sample") ("`lbl'") ("gs_strictness_enacted") (r(sd)) (.) (.) (r(N)) (.) ("")
    drop smp z_gs_warmth_enacted z_gs_strictness_enacted z_gs_teaching_enacted
}

postclose apf
use "`ROOT'/thesis/tables/ch3_appendix_estimates.dta", clear
export delimited using "`ROOT'/thesis/tables/ch3_appendix_estimates.csv", replace
display "ch3_appendix_estimates.csv written."
