/* 04_cox_regression.sas */
/* Primary Cox proportional hazards model for mortality */
options nodate nonumber;
ods noproctitle;
%let output_path=/home/u64438249/portfolio/output;
libname data "/home/u64438249/portfolio/data";

/* Create PDF report */
ods pdf file="&output_path/04_cox_regression.pdf" style=journal startpage=yes;
title1 "COPD Cohort Study Using MIMIC-IV Data";
title2 "Table 4. Cox Proportional Hazards Regression";
title3 "Adjusted hazard ratios for RAAS exposure and clinical covariates";
footnote1 "Source: MIMIC-IV derived dataset (BigQuery)";
footnote2 "Cox proportional hazards regression was used to estimate adjusted hazard ratios (HRs) and 95% confidence intervals.";
footnote3 
	"The model adjusted for age, sex, illness severity, CHF, CKD, and diabetes.";

/* Check key variables */
proc contents data=data.copd_cohort;
run;

proc freq data=data.copd_cohort;
	tables death_event raas_pre_icu gender chf ckd diabetes / missing;
run;

proc means data=data.copd_cohort n mean median min max;
	var time_to_event_days age sofa_score;
run;

/* Prepare analysis dataset aligned with Python dropna() */
data work.analysis_dataset;
	set data.copd_cohort;

	if nmiss(time_to_event_days, death_event, raas_pre_icu, age, sofa_score, chf, 
		ckd, diabetes)=0;
run;

/* Primary Cox proportional hazards model */
proc phreg data=work.analysis_dataset;
	class gender(ref='F') chf(ref='0') ckd(ref='0') diabetes(ref='0') 
		anchor_year_group / param=ref;
	model time_to_event_days*death_event(0)=raas_pre_icu age gender sofa_score chf 
		ckd diabetes / ties=efron risklimits;
	strata anchor_year_group;
	hazardratio raas_pre_icu;
	hazardratio age;
	hazardratio sofa_score;
run;

ods pdf close;
title;
footnote;
ods proctitle;