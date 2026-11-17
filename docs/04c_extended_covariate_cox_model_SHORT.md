# 04c - Extended Covariate Cox Models for Pre-ICU RAAS Exposure in ICU COPD Patients (SHORT)

Current estimates below use the 2026-11-18 admission-age and continuous follow-up corrections; see [the validation report](AGE_TIME_REVALIDATION.md). Figures and the local rendered report are refreshed through the shared current-analysis workflow; independent SAS validation remains pending.

Full notebook:
[04c - Extended Covariate Cox Models for Pre-ICU RAAS Exposure in ICU COPD Patients](../notebooks/04c_extended_covariate_cox_model.ipynb)

## Objective
Evaluate whether the association between pre-ICU RAAS exposure and in-hospital mortality remains after adjustment for additional severity, comorbidity, and ICU type variables.

## Input Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes`

## Output Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes_extended`

## Downstream Usage
The extended outcome table supports adjusted Cox models with SOFA score, comorbidities, and ICU type. It is also exported for the SAS/Python logistic validation workflow.

## Key Methods
- Adds first-day SOFA score, Charlson-derived comorbidity indicators, and ICU type.
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
- Results suggest sensitivity to severity, care setting, and ICU-level case mix, and should be interpreted as observational associations.

## Next Step
Next: [04d - Python Logistic Validation Model](04d_python_logistic_model_SHORT.md)
