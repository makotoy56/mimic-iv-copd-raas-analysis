/* 07_export_validation_tables.sas */
/* Export SAS result tables for Python-vs-SAS validation. */
/* Cox proportional hazards outputs are the primary survival model artifacts. */
/* Logistic outputs are retained only as secondary binary-outcome validation artifacts. */
options nodate nonumber;
ods noproctitle;
%let output_path=/home/u64438249/portfolio-ICU/output;
libname data "/home/u64438249/portfolio-ICU/data";

/* -------------------------------------------------- */
/* 1. Baseline continuous summary                     */
/* -------------------------------------------------- */
proc means data=data.copd_cohort n mean std median q1 q3 min max noprint;
	var age icu_los hosp_los sofa_score charlson_comorbidity_index;
	output out=work.sas_baseline_continuous n=mean=std=median=q1=q3=min=max= / 
		autoname;
run;

/* -------------------------------------------------- */
/* 2. Primary Cox proportional hazards model results  */
/* -------------------------------------------------- */
ods output ParameterEstimates=work.sas_primary_cox_parameters 
	FitStatistics=work.sas_primary_cox_fit_statistics 
	GlobalTests=work.sas_primary_cox_global_tests;

proc phreg data=data.copd_cohort;
	class gender(ref='F') chf(ref='0') ckd(ref='0') diabetes(ref='0') / param=ref;
	model time_to_event_days*death_event(0)=raas_pre_icu age gender sofa_score 
		charlson_comorbidity_index chf ckd diabetes / ties=efron;
run;

proc export data=work.sas_primary_cox_parameters 
		outfile="&output_path/sas_primary_cox_parameters.csv" dbms=csv replace;
run;

proc export data=work.sas_primary_cox_fit_statistics 
		outfile="&output_path/sas_primary_cox_fit_statistics.csv" dbms=csv replace;
run;

proc export data=work.sas_primary_cox_global_tests 
		outfile="&output_path/sas_primary_cox_global_tests.csv" dbms=csv replace;
run;

/* -------------------------------------------------- */
/* 3. Secondary logistic validation model results     */
/* -------------------------------------------------- */
ods output ParameterEstimates=work.sas_secondary_logistic_validation_parameters 
	Association=work.sas_secondary_logistic_validation_association 
	LackFitChiSq=work.sas_secondary_logistic_validation_hosmer_lemeshow;

proc logistic data=data.copd_cohort descending;
	class gender(ref='F') chf(ref='0') ckd(ref='0') diabetes(ref='0') / param=ref;
	model death_event=raas_pre_icu age gender sofa_score 
		charlson_comorbidity_index chf ckd diabetes / clodds=wald lackfit;
run;

proc export data=work.sas_secondary_logistic_validation_parameters 
		outfile="&output_path/sas_secondary_logistic_validation_parameters.csv" dbms=csv replace;
run;

proc export data=work.sas_secondary_logistic_validation_association 
		outfile="&output_path/sas_secondary_logistic_validation_association.csv" dbms=csv replace;
run;

proc export data=work.sas_secondary_logistic_validation_hosmer_lemeshow 
		outfile="&output_path/sas_secondary_logistic_validation_hosmer_lemeshow.csv" dbms=csv replace;
run;

title;
footnote;
ods proctitle;
