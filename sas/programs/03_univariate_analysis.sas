/* 03_univariate_analysis.sas */
/* Generate univariate mortality association tables for the COPD cohort */

options nodate nonumber;
ods noproctitle;

%let input_path=/home/u64438249/portfolio-ICU/input;
%let output_path=/home/u64438249/portfolio-ICU/output;
libname data "/home/u64438249/portfolio-ICU/data";

/* Create a publication-style PDF report */
ods pdf file="&output_path/03_univariate_analysis.pdf" style=journal startpage=yes;

/* Main title */
title1 "COPD Cohort Study Using MIMIC-IV Data";
footnote1 "Source: MIMIC-IV derived dataset (BigQuery)";
footnote2 "Associations between categorical variables and in-hospital mortality were assessed using chi-square tests.";
footnote3 "P-values < 0.05 were considered statistically significant.";

/* Categorical variables stratified by mortality outcome */
title2 "Table 2. Univariate Associations Between Categorical Variables and In-Hospital Mortality";

proc freq data=data.copd_cohort;
    tables gender*death_event
           raas_pre_icu*death_event
           chf*death_event
           ckd*death_event
           diabetes*death_event
           icu_type*death_event / missing chisq;
run;
ods pdf close;

title;
footnote;
ods proctitle;
