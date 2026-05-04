/* 02_baseline_table.sas */
/* Generate publication-style baseline summary tables for the COPD cohort */

options nodate nonumber;
ods noproctitle;

%let input_path=/home/u64438249/portfolio/input;
%let output_path=/home/u64438249/portfolio/output;

/* Import the analysis-ready cohort dataset */
proc import datafile="&input_path/copd_raas__cohort_copd_outcomes_extended.csv"
    out=work.copd_cohort
    dbms=csv
    replace;
    guessingrows=max;
    getnames=yes;
run;

/* Create a publication-style PDF report */
ods pdf file="&output_path/02_baseline_table.pdf" style=journal startpage=yes;

title1 "Baseline Characteristics of the COPD Cohort";
footnote1 "Source: BigQuery table mimic-iv-portfolio.copd_raas.cohort_copd_outcomes_extended";

/* Overall continuous variable summary */
title2 "Table 1A. Overall Summary of Continuous Variables";

proc means data=work.copd_cohort n mean std median q1 q3 min max maxdec=2;
    var age icu_los hosp_los sofa_score charlson_comorbidity_index;
run;

ods pdf startpage=now;

/* Continuous variables stratified by mortality outcome */
title2 "Table 1B. Continuous Variables Stratified by In-Hospital Mortality";

proc means data=work.copd_cohort n mean std median q1 q3 min max maxdec=2;
    class death_event;
    var age icu_los hosp_los sofa_score charlson_comorbidity_index;
run;

ods pdf startpage=now;

/* Overall categorical variable summary */
title2 "Table 1C. Overall Summary of Categorical Variables";

proc freq data=work.copd_cohort;
    tables gender
           raas_pre_icu
           chf
           ckd
           diabetes
           copd_comorbidity
           htn
           icu_type / missing;
run;

ods pdf startpage=now;

/* Categorical variables stratified by mortality outcome */
title2 "Table 1D. Categorical Variables Stratified by In-Hospital Mortality";

proc freq data=work.copd_cohort;
    tables gender*death_event
           raas_pre_icu*death_event
           chf*death_event
           ckd*death_event
           diabetes*death_event
           copd_comorbidity*death_event
           htn*death_event
           icu_type*death_event / missing chisq;
run;

ods pdf close;

title;
footnote;
ods proctitle;