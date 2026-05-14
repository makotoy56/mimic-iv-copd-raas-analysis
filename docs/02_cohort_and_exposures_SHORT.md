# 02 - Cohort and Exposure Construction (SHORT)

## Objective
Construct the COPD ICU cohort and derive pre-ICU RAAS inhibitor exposure indicators for downstream cohort assembly and analysis.

## Input Dataset
- `mimic-iv-portfolio.copd_raas.cohort_icu`
- MIMIC-IV diagnosis table in BigQuery
- MIMIC-IV prescription table in BigQuery

## Output Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd`
- `mimic-iv-portfolio.copd_raas.cohort_copd_raas`
- `mimic-iv-portfolio.copd_raas.cohort_copd_raas_detailed`

## Downstream Usage
These tables define the COPD ICU cohort and pre-ICU RAAS exposure indicators used by baseline cohort construction, subgroup analyses, and validation workflows.

## Key Methods and Checks
- Identifies ICU admissions associated with COPD diagnosis codes.
- Defines binary pre-ICU RAAS inhibitor exposure using medication records before ICU admission.
- Creates detailed ACE inhibitor, ARB, dual-exposure, and mutually exclusive exposure indicators.
- Checks exposure distributions and verifies one row per ICU stay.

## Next Step
Next: [03a - Baseline Cohort Construction](03a_baseline_SHORT.md)
