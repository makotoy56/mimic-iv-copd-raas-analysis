/* 01_import.sas */
/* Import BigQuery-exported COPD cohort dataset */

options nodate nonumber;

%let input_path=/home/u64438249/portfolio/input;
%let output_path=/home/u64438249/portfolio/output;

ods pdf file="&output_path/01_import_results.pdf";

/* Main title */
title1 "COPD Cohort Dataset - Initial Data Exploration";

/* Import CSV dataset */
title2 "Step 1: Import Dataset from CSV";
proc import datafile="&input_path/copd_raas__cohort_copd_outcomes_extended.csv"
    out=work.copd_cohort
    dbms=csv
    replace;
    guessingrows=max;
    getnames=yes;
run;

/* Dataset structure */
title2 "Step 2: Dataset Structure (PROC CONTENTS)";
proc contents data=work.copd_cohort varnum;
run;

/* First 20 observations */
title2 "Step 3: First 20 Observations (PROC PRINT)";
proc print data=work.copd_cohort(obs=20);
run;

/* Categorical variables */
title2 "Step 4: Frequency Distribution of Key Variables";
proc freq data=work.copd_cohort;
    tables gender death_event raas_pre_icu / missing;
run;

/* Continuous variables */
title2 "Step 5: Summary Statistics for Continuous Variables";
proc means data=work.copd_cohort n mean std median min max;
    var age icu_los hosp_los;
run;

/* Clear titles */
title;
title2;

ods pdf close;