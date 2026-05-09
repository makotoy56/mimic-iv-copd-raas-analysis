/* 06_sensitivity_analysis.sas */
/* Sensitivity analyses to assess robustness of the primary Cox model */
/* Includes binary mortality sensitivity analysis using logistic regression */
options nodate nonumber;
ods noproctitle;
%let output_path=/home/u64438249/portfolio-ICU/output;
libname data "/home/u64438249/portfolio-ICU/data";

/* Create PDF */
ods pdf file="&output_path/06_sensitivity_analysis.pdf" style=journal 
	startpage=yes;

/* title */
title1 "COPD Cohort Study Using MIMIC-IV Data";
title2 "Table 5. Sensitivity Analyses";

/* ========================= */
/* Model 1: Additional adjustment for ICU type */
/* ========================= */
title3 "Model 1. Binary mortality sensitivity analysis (ICU type adjusted)";

proc logistic data=data.copd_cohort descending;
	class gender(ref='F') chf(ref='0') ckd(ref='0') diabetes(ref='0') icu_type / 
		param=ref;
	model death_event=raas_pre_icu age gender sofa_score 
		charlson_comorbidity_index chf ckd diabetes icu_type / clodds=wald;
run;

/* ========================= */
/* Model 2: Complete case */
/* ========================= */
title3 "Model 2. Binary mortality sensitivity analysis (complete case)";

data work.complete_case;
	set data.copd_cohort;

	if nmiss(death_event, raas_pre_icu, age, sofa_score, 
		charlson_comorbidity_index, chf, ckd, diabetes)=0 and not missing(gender);
run;

proc sql;
	select count(*) as complete_case_n from work.complete_case;
quit;

proc logistic data=work.complete_case descending;
	class gender(ref='F') chf(ref='0') ckd(ref='0') diabetes(ref='0') / param=ref;
	model death_event=raas_pre_icu age gender sofa_score 
		charlson_comorbidity_index chf ckd diabetes / clodds=wald;
run;

/* ========================= */
/* Model 3: Without SOFA score */
/* ========================= */
title3 "Model 3. Binary mortality sensitivity analysis (without SOFA score)";

proc logistic data=data.copd_cohort descending;
	class gender(ref='F') chf(ref='0') ckd(ref='0') diabetes(ref='0') / param=ref;
	model death_event=raas_pre_icu age gender charlson_comorbidity_index chf ckd 
		diabetes / clodds=wald;
run;

ods pdf close;
title;
footnote;
ods proctitle;