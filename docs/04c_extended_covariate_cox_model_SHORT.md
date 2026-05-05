# 04c - Extended Covariate Cox Models for Pre-ICU RAAS Exposure in ICU COPD Patients (SHORT)

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
- Fits core and ICU-extended Cox proportional hazards models.
- Evaluates unpenalized and penalized model specifications.
- Assesses proportional hazards assumptions using Schoenfeld residual-based diagnostics.

## Key Results Summary
- In the unpenalized core Cox model, pre-ICU RAAS exposure had HR 0.809 (95% CI 0.654-1.000, p = 0.050).
- In the penalized core model, the point estimate remained below 1 but was not statistically significant.
- After adding ICU type, the RAAS estimate was attenuated and was not statistically significant.
- Results suggest sensitivity to severity, care setting, and ICU-level case mix, and should be interpreted as observational associations.
