# 04b - Class-Specific Effects of ACE Inhibitors vs ARBs on In-Hospital Mortality in ICU COPD Patients (SHORT)

Full notebook:
[04b - Class-Specific Effects of ACE Inhibitors vs ARBs on In-Hospital Mortality in ICU COPD Patients](../notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb)

## Objective
Evaluate ACE inhibitor and ARB subclass-specific associations with in-hospital mortality among ICU patients with COPD.

## Input Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes`
- `mimic-iv-portfolio.copd_raas.cohort_copd_raas_detailed`

## Output Dataset
- No new persistent dataset; results are produced within the notebook.

## Downstream Usage
Subclass findings provide context for the extended covariate models in `04c_extended_covariate_cox_model.ipynb`.

## Key Methods
- Joins outcome data with detailed RAAS subclass exposure indicators.
- Constructs mutually exclusive ACE inhibitor and ARB monotherapy indicators.
- Excludes rare dual ACE inhibitor plus ARB exposure from monotherapy Cox modeling.
- Fits Kaplan-Meier curves and stratified Cox proportional hazards models.
- Evaluates proportional hazards assumptions using Schoenfeld residual tests.

## Key Results Summary
- ACE inhibitor monotherapy was associated with lower observed in-hospital mortality in the subclass Cox model.
- ARB monotherapy had a directionally lower-hazard but statistically non-significant estimate.
- Results are interpreted as observational associations and may be affected by residual confounding.

## Next Step
Next: [04c - Extended Covariate Cox Model](04c_extended_covariate_cox_model_SHORT.md)
