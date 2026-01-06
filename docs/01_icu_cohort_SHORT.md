# 01 - ICU Cohort Construction (SHORT)

This step constructs a standardized adult ICU cohort from MIMIC-IV, serving as the foundational input for all downstream cohort, exposure, and survival analyses.

Using ICU stay–level data, the cohort is restricted to adult patients (age ≥ 18) and limited to the first ICU stay per hospital admission to ensure independent observations.

The resulting table (`copd_raas.cohort_icu`) provides a clean and reproducible ICU backbone used in subsequent disease-specific cohort construction and RAAS inhibitor exposure analyses (02–04).