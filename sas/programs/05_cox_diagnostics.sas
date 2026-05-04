/* 05_cox_diagnostics.sas */
/* Lightweight diagnostics for Cox proportional hazards model */

options nodate nonumber;
ods noproctitle;

%let output_path=/home/u64438249/portfolio/output;
libname data "/home/u64438249/portfolio/data";

ods pdf file="&output_path/05_cox_diagnostics.pdf" style=journal startpage=yes;

title1 "COPD Cohort Study Using MIMIC-IV Data";
title2 "Cox Model Diagnostics";

/* Fit Cox model and assess PH assumption without resampling */
proc phreg data=data.copd_cohort;
    class
        gender(ref='F')
        chf(ref='0')
        ckd(ref='0')
        diabetes(ref='0')
        / param=ref;

    model time_to_event_days*death_event(0) =
        raas_pre_icu
        age
        gender
        sofa_score
        charlson_comorbidity_index
        chf
        ckd
        diabetes
        / ties=efron;

    strata anchor_year_group;

    assess ph;
run;

/* Kaplan-Meier curves by RAAS exposure */
title2 "Kaplan-Meier Curves by RAAS Exposure";

proc lifetest data=data.copd_cohort plots=survival;
    time time_to_event_days*death_event(0);
    strata raas_pre_icu;
run;

ods pdf close;

title;
footnote;
ods proctitle;