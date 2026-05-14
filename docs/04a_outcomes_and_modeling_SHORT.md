# 04a - Pre-ICU RAAS Exposure and In-Hospital Mortality in ICU COPD Patients (SHORT)

## Objective
Evaluate the association between combined pre-ICU RAAS inhibitor exposure and in-hospital mortality among ICU patients with COPD.

## Input Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd_baseline`

## Output Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes`

## Downstream Usage
The outcome table is used by subclass analyses in `04b_outcomes_and_modeling_raas_subgroups.ipynb` and extended covariate models in `04c_extended_covariate_cox_model.ipynb`.

## Key Methods
- Builds in-hospital mortality outcome variables in BigQuery.
- Defines `death_event` as in-hospital death and `time_to_event_days` as ICU admission to death or hospital discharge.
- Fits Kaplan-Meier curves and Cox proportional hazards models.
- Uses Schoenfeld residual testing to assess proportional hazards assumptions.
- Uses a refined Cox model stratified by `anchor_year_group`.

## Key Results Summary
- Pre-ICU RAAS exposure was associated with lower observed in-hospital mortality in the primary and refined Cox models.
- The refined proportional hazards-compliant model estimated HR 0.71 (95% CI 0.58-0.88).
- Findings are interpreted as observational associations, not causal effects.

## Next Step
Next: [04b - RAAS Subgroup Modeling](04b_outcomes_and_modeling_raas_subgroups_SHORT.md)
