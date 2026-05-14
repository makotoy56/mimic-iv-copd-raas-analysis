# 03a - Baseline Cohort Construction (SHORT)

Full notebook:
[03a - Baseline Cohort Construction](../notebooks/03a_baseline.ipynb)

## Objective
Construct the baseline COPD ICU cohort with demographic characteristics, pre-ICU RAAS exposure, and core cohort eligibility fields.

## Input Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd`
- `mimic-iv-portfolio.copd_raas.cohort_copd_raas`
- MIMIC-IV patient and admission tables in BigQuery

## Output Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd_baseline`

## Downstream Usage
This baseline cohort table is the primary input for outcome construction and downstream mortality modeling in `04a_outcomes_and_modeling.ipynb`.

## Key Methods and Checks
- Adds age, sex, calendar-time variables, hospital length of stay, and date-of-death information.
- Merges the binary pre-ICU RAAS exposure flag at the ICU-stay level.
- Treats missing RAAS exposure records as non-exposure.
- Checks cohort size and exposure distribution before downstream modeling.

## Next Step
Next: [03b - Merge COPD Cohort with RAAS Exposures](03b_merge_exposures_SHORT.md)
