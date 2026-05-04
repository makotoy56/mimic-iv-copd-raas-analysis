/* 02_baseline_table.sas */
/* Generate publication-style baseline summary tables for the COPD cohort */

options nodate nonumber;
ods noproctitle;

%let output_path=/home/u64438249/portfolio/output;
libname data "/home/u64438249/portfolio/data";

/* Create a publication-style PDF report */
ods pdf file="&output_path/02_baseline_table.pdf" style=journal startpage=yes;

/* Main title */
title1 "COPD Cohort Study Using MIMIC-IV Data";
footnote1 "Source: MIMIC-IV derived dataset (BigQuery)";
footnote2 "Continuous variables are presented as mean ± standard deviation or median (IQR).";
footnote3 "Categorical variables are presented as counts and percentages; missing values are included where specified.";

/* Overall continuous variable summary */
title2 "Table 1A. Overall Summary of Continuous Variables";

proc means data=data.copd_cohort n mean std median q1 q3 min max maxdec=2;
    var age icu_los hosp_los sofa_score charlson_comorbidity_index;
run;

/* Continuous variables stratified by mortality outcome */
title2 "Table 1B. Continuous Variables Stratified by In-Hospital Mortality";

proc means data=data.copd_cohort n mean std median q1 q3 min max maxdec=2;
    class death_event;
    var age icu_los hosp_los sofa_score charlson_comorbidity_index;
run;

/* Overall categorical variable summary */
title2 "Table 1C. Overall Summary of Categorical Variables";

proc freq data=data.copd_cohort;
    tables gender
           raas_pre_icu
           chf
           ckd
           diabetes
           icu_type / missing;
run;

ods pdf close;

title;
footnote;
ods proctitle;