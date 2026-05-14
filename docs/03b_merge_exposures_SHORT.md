# 03b - Merge COPD Cohort with RAAS Exposures (SHORT)

## Objective
Merge the COPD ICU cohort with ACE inhibitor, ARB, and combined RAAS exposure indicators and validate the resulting exposure-enhanced cohort.

## Input Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd`
- `mimic-iv-portfolio.copd_raas.cohort_copd_raas_detailed`

## Output Dataset
- `mimic-iv-portfolio.copd_raas.cohort_copd_with_raas`

## Downstream Usage
This exposure-enhanced cohort table supports exposure distribution checks and documents the detailed ACE inhibitor, ARB, and combined RAAS exposure merge.

## Key Methods and Checks
- Left-joins detailed RAAS exposure flags to the COPD ICU cohort using ICU-stay identifiers.
- Includes ACE inhibitor, ARB, any RAAS, dual-exposure, and mutually exclusive exposure categories.
- Validates row counts, missing exposure fields, exposure distributions, and cross-tabulated RAAS counts.

## Next Step
Next: [04a - Outcomes and Primary Modeling](04a_outcomes_and_modeling_SHORT.md)
