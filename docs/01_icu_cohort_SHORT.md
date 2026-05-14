# 01 - ICU Cohort Extraction (SHORT)

## Objective
Build the base adult ICU cohort from MIMIC-IV using BigQuery and verify the integrity of the extracted ICU-stay-level table.

## Input Dataset
- MIMIC-IV ICU stay table in BigQuery
- MIMIC-IV patient table in BigQuery

## Output Dataset
- `mimic-iv-portfolio.copd_raas.cohort_icu`

## Downstream Usage
This ICU-stay-level table is the base input for COPD cohort construction in `02_cohort_and_exposures.ipynb`.

## Key Methods and Checks
- Restricts to adult ICU patients.
- Keeps the first ICU stay per hospital admission.
- Carries ICU timing, demographics, age, and calendar-year grouping.
- Performs basic table preview and row-level sanity checks.

## Next Step
Next: [02 - Cohort and Exposure Construction](02_cohort_and_exposures_SHORT.md)
