# 04c - Extended Covariate Cox Models for Pre-ICU RAAS Exposure in ICU COPD Patients (SHORT)

Current estimates below use the 2026-11-18 admission-age and continuous follow-up corrections; see [the validation report](AGE_TIME_REVALIDATION.md). Figures and the local rendered report are refreshed through the shared current-analysis workflow; independent Cox calculation records are linked from [validation notes](VALIDATION_NOTES.md).

Full notebook:
[04c - Extended Covariate Cox Models for Pre-ICU RAAS Exposure in ICU COPD Patients](../notebooks/04c_extended_covariate_cox_model.ipynb)

## Objective
Describe exploratory sensitivity to first-day severity, comorbidity, ICU type, penalties and additional strata. `sofa_score` comes from `mimiciv_3_1_derived.first_day_sofa`. Its published definition can use information through 24 hours after ICU entry, while follow-up starts at ICU entry. All SOFA-containing core, ICU-adjusted and CHF/SOFA-stratified models are therefore exploratory sensitivity analyses that can use post-start information, not baseline-only severity adjustment. Temporal leakage or adjustment for post-exposure information may affect interpretation; its impact has not been quantified here. The primary age/sex model with era strata is unchanged. Time-aligned severity adjustment or a separate landmark design would require reanalysis.

## Input Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes_extended`
- `mimic-iv-portfolio.copd_raas.cohort_copd_raas_detailed` (joined by the shared loader)

## Output
- Aggregate model results and figures only; this notebook does not create or replace a persistent BigQuery table.
- Run `sql/04_build_outcomes.sql` and then `sql/04_build_outcomes_extended.sql` before 04a. The second SQL script creates the extended input table.

## Downstream Usage
The extended outcome table supports adjusted Cox models with SOFA score, comorbidities, and ICU type.

## Key Methods
- Reads first-day SOFA, Charlson-derived comorbidity indicators and ICU type already joined by the extended-outcome SQL.
- Uses `raas_pre_icu` as the primary exposure.
- Does not include ACE inhibitor or ARB subclass indicators in the 04c Cox model specification.
- Carries forward the corrected outcome timing: ICU admission to recorded in-hospital death time for events, with discharge-time fallback only when death time is unavailable; live discharge is censoring.
- Fits core and ICU-extended Cox proportional hazards models; ICU types with fewer than 50 admissions are pooled using frequency alone.
- Adds exploratory CHF/exact-SOFA-stratified sensitivity models; the ICU version also stratifies by pooled ICU type. These do not replace the primary model.
- Evaluates unpenalized and penalized model specifications.
- Assesses proportional hazards assumptions using Schoenfeld residual-based diagnostics.
- Does not implement a competing-risk framework.

## Key Results Summary
- In the unpenalized core Cox model, pre-ICU RAAS exposure had HR 0.833 (95% CI 0.673-1.030; p = 0.09122). This estimate did not meet conventional statistical significance.
- In the penalized core model, the point estimate remained below 1 but was not statistically significant.
- After adding ICU type, the RAAS estimate was attenuated and was not statistically significant.
- These exploratory differences do not isolate baseline confounding; post-start SOFA information may affect interpretation. A time-aligned severity or landmark design requires [separate reanalysis](ANALYSIS_TIMING_LIMITATIONS.md).

## Next Step
Next: [04d - Python Logistic Validation Model](04d_python_logistic_model_SHORT.md)
