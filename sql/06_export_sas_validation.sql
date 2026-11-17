-- Private SAS validation input: export only to an authorized local analysis environment.
-- Do not commit, publish, or display these individual model inputs.
SELECT
  'admission_age_elapsed_time_los_v2' AS analysis_version,
  age, anchor_age, age_anchor_topcoded, gender, anchor_year_group,
  raas_pre_icu, death_event, time_to_event_days, death_time_fallback_flag,
  icu_los, hosp_los, sofa_score, charlson_comorbidity_index, chf, ckd, diabetes, icu_type
FROM `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes_extended`;
