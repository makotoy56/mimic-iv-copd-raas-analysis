# 04a - Pre-ICU RAAS Exposure and In-Hospital Mortality in ICU COPD Patients (SHORT)

Current estimates below use the 2026-11-18 admission-age and continuous follow-up corrections; see [the validation report](AGE_TIME_REVALIDATION.md). Figures and the local rendered report are refreshed through the shared current-analysis workflow; independent Cox calculation records are linked from [validation notes](VALIDATION_NOTES.md).

Full notebook:
[04a - Pre-ICU RAAS Exposure and In-Hospital Mortality in ICU COPD Patients](../notebooks/04a_outcomes_and_modeling.ipynb)

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
- Defines `death_event` as recorded in-hospital death.
- For death events, measures `time_to_event_days` from ICU admission to `admissions.deathtime`, with `admissions.dischtime` used as a flagged fallback only when death time is unavailable.
- For live discharges, measures `time_to_event_days` from ICU admission to discharge and treats discharge as censoring.
- Fits Kaplan-Meier curves and Cox proportional hazards models.
- Uses Schoenfeld residual testing to assess proportional hazards assumptions.
- Uses a refined Cox model stratified by `anchor_year_group`.
- Does not implement a competing-risk framework.

## Key Results Summary
- Pre-ICU RAAS exposure was associated with lower observed in-hospital mortality in the primary and refined Cox models.
- The refined era-stratified model estimated HR 0.732 (95% CI 0.592-0.904; p = 0.00383).
- Findings are interpreted as observational associations, not causal effects.

## Next Step
Next: [04b - RAAS Subgroup Modeling](04b_outcomes_and_modeling_raas_subgroups_SHORT.md)
