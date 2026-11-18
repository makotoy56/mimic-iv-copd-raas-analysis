# 04b - ACEi-only and ARB-only Prescription Orders Versus Neither on In-Hospital Mortality in ICU COPD Patients (SHORT)

Current estimates below use the 2026-11-18 admission-age and continuous follow-up corrections; see [the validation report](AGE_TIME_REVALIDATION.md). Figures and the local rendered report are refreshed through the shared current-analysis workflow; independent Cox calculation records are linked from [validation notes](VALIDATION_NOTES.md).

Full notebook:
[04b - ACEi-only and ARB-only Prescription Orders Versus Neither on In-Hospital Mortality in ICU COPD Patients](../notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb)

## Objective
Evaluate ACE inhibitor and ARB subclass-specific associations with in-hospital mortality among ICU patients with COPD.

## Input Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes_extended` (shared loader; build both outcome SQL scripts before 04a)
- `mimic-iv-portfolio.copd_raas.cohort_copd_raas_detailed`

## Output Dataset
- No new persistent dataset; results are produced within the notebook.

## Downstream Usage
Subclass findings provide context for the extended covariate models in `04c_extended_covariate_cox_model.ipynb`.

## Key Methods
- Joins outcome data with detailed RAAS subclass exposure indicators.
- ACEi-only and ARB-only prescription-order groups are each compared with neither qualifying order. Records with both class flags positive are excluded from this subclass analysis. The main analysis reports no direct ACEi-versus-ARB contrast or interaction test. Different point estimates, or one p-value below 0.05 and the other above it, do not establish a difference between the classes.
- Exposure flags identify inpatient prescription records in the same hospital admission with `starttime <= intime`. They do not verify actual administration, continued treatment at ICU entry, adherence or concurrent ACEi/ARB administration. Both positive class flags mean qualifying records for both classes; they do not establish simultaneous treatment. Neither means no qualifying prescription record for either class, not proven absence of all medication use.
- Uses the corrected outcome timing: ICU admission to recorded in-hospital death time for events, with discharge-time fallback only when death time is unavailable; live discharge is censoring.
- Fits Kaplan-Meier curves and stratified Cox proportional hazards models.
- Evaluates proportional hazards assumptions using Schoenfeld residual tests.
- Does not implement a competing-risk framework.

## Key Results Summary
- ACEi-only prescription orders versus neither qualifying order had (HR 0.683, 95% CI 0.521-0.894; p = 0.00550).
- ARB-only prescription orders versus neither qualifying order had (HR 0.805, 95% CI 0.573-1.131; p = 0.21116).
- Results are interpreted as observational associations and may be affected by residual confounding.

## Next Step
Next: [04c - Extended Covariate Cox Model](04c_extended_covariate_cox_model_SHORT.md)
