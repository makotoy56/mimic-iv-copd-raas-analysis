/* 07_export_validation_tables.sas */
/* Export SAS result tables for Python-vs-SAS validation. */
/* Cox proportional hazards outputs are the primary survival model artifacts. */
/* Logistic outputs are retained only as secondary binary-outcome validation artifacts. */
options nodate nonumber;
ods noproctitle;
%let output_path=/home/u64438249/portfolio-ICU/output;
libname data "/home/u64438249/portfolio-ICU/data";

/* Fresh exports must carry the analysis version; historical inputs cannot pass. */
%macro require_current_input;
    %local dsid version_col rc;
    %let dsid=%sysfunc(open(data.copd_cohort));
    %if &dsid=0 %then %do;
        %put ERROR: Current cohort input is unavailable.;
        %abort cancel;
    %end;
    %let version_col=%sysfunc(varnum(&dsid,analysis_version));
    %let rc=%sysfunc(close(&dsid));
    %if &version_col=0 %then %do;
        %put ERROR: Re-export the corrected BigQuery cohort with analysis_version.;
        %abort cancel;
    %end;
    %local bad_versions;
    proc sql noprint;
        select count(*) into :bad_versions from data.copd_cohort
        where missing(analysis_version) or analysis_version ne 'admission_age_elapsed_time_los_v2';
    quit;
    %if &bad_versions>0 %then %do;
        %put ERROR: Historical cohort version cannot be validated as current.;
        %abort cancel;
    %end;
%mend;
%require_current_input;

/* -------------------------------------------------- */
/* 1. Baseline continuous summary                     */
/* -------------------------------------------------- */
proc means data=data.copd_cohort n mean std median q1 q3 min max noprint;
	var age icu_los hosp_los sofa_score charlson_comorbidity_index;
	output out=work.sas_baseline_continuous n=mean=std=median=q1=q3=min=max= / 
		autoname;
run;

/* -------------------------------------------------- */
/* 2. Era-stratified 04a refined and 04c core Cox outputs. */
/* -------------------------------------------------- */
ods output ParameterEstimates=work.sas_primary_cox_parameters;
proc phreg data=data.copd_cohort;
    class gender(ref='F') / param=ref;
    model time_to_event_days*death_event(0)=raas_pre_icu age gender / ties=efron;
    strata anchor_year_group;
run;
proc export data=work.sas_primary_cox_parameters
    outfile="&output_path/sas_primary_cox_parameters.csv" dbms=csv replace;
run;

ods output ParameterEstimates=work.sas_core_cox_parameters;
proc phreg data=data.copd_cohort;
    class gender(ref='F') / param=ref;
    model time_to_event_days*death_event(0)=raas_pre_icu age gender sofa_score chf ckd diabetes / ties=efron;
    strata anchor_year_group;
run;
proc export data=work.sas_core_cox_parameters
    outfile="&output_path/sas_core_cox_parameters.csv" dbms=csv replace;
run;

/* -------------------------------------------------- */
/* 3. Secondary logistic validation model results     */
/* -------------------------------------------------- */
ods output ParameterEstimates=work.sas_secondary_logistic_validation_parameters 
	Association=work.sas_secondary_logistic_validation_association 
	LackFitChiSq=work.sas_secondary_logistic_validation_hosmer_lemeshow;

data work.secondary_validation_input;
    set data.copd_cohort;
    if nmiss(death_event,raas_pre_icu,age,sofa_score,charlson_comorbidity_index,chf,ckd,diabetes)=0
       and not missing(gender);
run;
proc logistic data=work.secondary_validation_input descending;
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

/* Aggregate provenance for exact-key Python comparison. */
proc sql;
    create table work.validation_manifest as
    select 'admission_age_elapsed_time_los_v2' as analysis_version length=80,
           'raas_pre_icu+age+gender+sofa_score+charlson_comorbidity+chf+ckd+diabetes' as model_spec length=160,
           count(*) as n, sum(death_event) as events, sum(age) as age_sum format=best32.,
           sum(time_to_event_days) as duration_sum format=best32.
    from work.secondary_validation_input;
quit;
proc export data=work.validation_manifest
    outfile="&output_path/sas_secondary_logistic_validation_parameters.manifest.csv" dbms=csv replace;
run;

title;
footnote;
ods proctitle;
