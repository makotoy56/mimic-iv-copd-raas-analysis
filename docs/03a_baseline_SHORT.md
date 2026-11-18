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
This cohort table feeds `sql/04_build_outcomes.sql`; run that script and then `sql/04_build_outcomes_extended.sql` after phase 03 and before 04a. The shared model loader reads the resulting extended outcome table.

## Key Methods and Checks
- Preserves the cohort admission-age estimate and raw/topcoded-age fields; adds sex, calendar-time variables, hospital length of stay, and date-of-death information.
- Merges the binary pre-ICU RAAS exposure flag at the ICU-stay level.
- Treats missing RAAS exposure records as non-exposure.
- Checks cohort size and exposure distribution before downstream modeling.

## Next Step
Next: [03b - Merge COPD Cohort with RAAS Exposures](03b_merge_exposures_SHORT.md)
