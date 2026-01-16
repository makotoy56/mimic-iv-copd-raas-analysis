# 02 - Cohort and Exposure Construction (SHORT)

## Overview
This step constructs the foundational ICU cohort of patients with COPD and defines pre-ICU exposure to renin–angiotensin–aldosterone system (RAAS) inhibitors based on inpatient prescription orders prior to ICU admission (not outpatient medication history).
All cohort and exposure definitions are implemented fully in BigQuery SQL to ensure transparency, reproducibility, and correct temporal ordering.

---

## Purpose
- Identify ICU admissions associated with COPD
- Define RAAS inhibitor exposure initiated prior to or at ICU admission
- Create standardized cohort and exposure tables used consistently across downstream
  cohort assembly and survival analyses (03a–04c)

---

## Data Sources
- MIMIC-IV v3.1 (BigQuery public dataset)
- Project: mimic-iv-portfolio
- Working schema: copd_raas

---

## Sanity Checks
The correctness of cohort and exposure construction was validated through a series
of targeted sanity checks executed in BigQuery.

These checks confirmed:
- One row per ICU stay in the COPD cohort
- Correct distribution of binary pre-ICU RAAS inhibitor exposure
- Logical consistency between binary and detailed exposure definitions
  (ACEi only / ARB only / both / neither)

All sanity checks were performed directly against the BigQuery tables to ensure
that SQL-based cohort and exposure definitions behaved as intended prior to
downstream modeling.

---

## Outputs and Downstream Use
The tables created in this step serve as standardized and reproducible inputs for:

- 03a: Baseline cohort assembly and verification
- 03b: Exposure merging and creation of the final analysis-ready dataset
- 04a: Combined RAAS inhibitor survival analysis
- 04b: ACEi vs. ARB subgroup analysis
- 04c: Extended Cox models and sensitivity analyses

This modular design ensures consistent exposure definitions, reproducible cohort
construction, and comparability across all downstream modeling stages.
