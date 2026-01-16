# 03a - Baseline Cohort Assembly (SHORT)

This notebook assembles a standardized baseline cohort of COPD patients admitted
to the ICU, serving as the common analysis-ready input for all downstream survival
analyses (04a–04c).

The table `copd_raas.cohort_copd_baseline` is created from the predefined COPD ICU
cohort constructed upstream (01–02) using the SQL script `03_build_baseline.sql`.
This step integrates patient-level and hospitalization-level attributes derived
from MIMIC-IV hospital tables.

Hospital length of stay (`hosp_los`, in days) is computed, and a binary indicator
of pre-ICU RAAS inhibitor exposure (`raas_pre_icu`) is attached at the ICU-stay
level using medication-derived exposure flags from inpatient prescription orders
defined prior to or at ICU admission (not outpatient medication history).
Missing exposure records are explicitly treated as non-exposure
(`raas_pre_icu = 0`), preserving temporal ordering and avoiding reverse causation.

The baseline cohort table is generated in SQL as a core analysis-ready dataset,
with downstream feature engineering and survival modeling performed in Python,
ensuring consistent cohort construction across analyses.

The resulting table provides a reproducible and consistent foundation for
downstream modeling in 04, ensuring aligned covariate and exposure definitions
across analyses.
