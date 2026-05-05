/* 07_logistic_validation_export.sas */
/* Export SAS logistic regression parameters for SAS-Python validation */

options nodate nonumber;
ods noproctitle;

%let output_path=/home/u64438249/portfolio/output;
libname data "/home/u64438249/portfolio/data";

/* Complete-case dataset aligned with the Python statsmodels validation model. */
data work.validation_logistic;
	set data.copd_cohort;

	charlson_comorbidity = charlson_comorbidity_index;

	if nmiss(death_event, raas_pre_icu, age, sofa_score,
		charlson_comorbidity, chf, ckd, diabetes)=0 and not missing(gender);
run;

ods output ParameterEstimates=work.sas_logistic_parameters;

proc logistic data=work.validation_logistic descending;
	class gender(ref='F') chf(ref='0') ckd(ref='0') diabetes(ref='0') / param=ref;
	model death_event=raas_pre_icu age gender sofa_score
		charlson_comorbidity chf ckd diabetes / clodds=wald;
run;

ods output close;

proc export data=work.sas_logistic_parameters
	outfile="&output_path/sas_logistic_parameters.csv"
	dbms=csv
	replace;
run;

title;
footnote;
ods proctitle;
