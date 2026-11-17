# Methods Overview

This document holds the methods detail that was shortened in the README. It preserves the analytic design and definitions used across the notebooks.

## Study Design And Data Source

This is a retrospective observational cohort study using MIMIC-IV v3.1, a de-identified ICU electronic health record database. The analysis is intended for reproducible clinical analytics and real-world evidence workflow demonstration.

## Cohort Construction

Adult ICU patients with COPD were identified using ICD-9 and ICD-10 diagnosis codes recorded during hospitalization. Each analytic record represents one qualifying hospital admission, anchored to the first ICU stay within that admission; subsequent ICU stays during the same hospital admission are excluded. A patient may contribute more than one qualifying hospital admission. Cohort construction uses reproducible BigQuery SQL and notebook-based checks.

Age is estimated at hospital admission as `anchor_age + EXTRACT(YEAR FROM admittime) - anchor_year`; the adult threshold is applied to this estimate. The baseline and outcome tables preserve that same `age` instead of resetting it to `anchor_age`. Raw `anchor_age` and `age_anchor_topcoded` are retained throughout the pipeline. An `anchor_age` of 91 represents the grouped ages above 89 in the anchor year; the year-adjusted value for these admissions remains a proxy, not a recovered exact age. Year-based age is approximate for all admissions because an exact birthday is unavailable.

Primary workflow:

- `01_icu_cohort.ipynb`: adult ICU cohort extraction
- `02_cohort_and_exposures.ipynb`: COPD cohort and RAAS exposure construction
- `03a_baseline.ipynb`: baseline covariate table
- `03b_merge_exposures.ipynb`: detailed exposure merge

## Exposure Definition

The primary exposure is pre-ICU RAAS inhibitor use, defined from inpatient prescription orders for ACE inhibitors or ARBs before or at ICU admission. This definition does not directly measure outpatient chronic medication use, adherence, dose, duration, or medication discontinuation before hospitalization.

Detailed exposure indicators include ACE inhibitor exposure, ARB exposure, dual exposure, and mutually exclusive ACE inhibitor or ARB monotherapy indicators for subgroup analysis.

## Outcome Definition

The primary outcome is time to in-hospital death, with follow-up beginning at ICU admission. For a death event, `time_to_event_days` is measured from ICU admission (`intime`) to the recorded in-hospital death time (`admissions.deathtime`); discharge time (`admissions.dischtime`) is used as an explicitly flagged fallback only when death time is unavailable. For a patient discharged alive, follow-up is measured from ICU admission to discharge time and the record is censored at discharge.

Follow-up is calculated as `DATETIME_DIFF(endpoint, intime, MICROSECOND) / 86400000000.0`, using the source DATETIME values. This preserves positive sub-hour intervals and avoids integer-hour boundary counting. Before replacing the outcome table, QA rejects missing timestamps, invalid event indicators, reversed death or discharge endpoints, and true zero follow-up requiring adjudication. The death-time fallback flag is preserved in both primary and extended datasets.

## Covariates

Covariates were selected a priori based on a conceptual clinical framework and include demographics, cardiovascular comorbidities, chronic kidney disease, diabetes, and SOFA score. Extended sensitivity models include ICU type and additional clinical variables.

## Statistical Analysis

The primary clinical analysis uses Kaplan-Meier survival curves and Cox proportional hazards regression. Proportional hazards assumptions are assessed using Schoenfeld residual-based diagnostics. Sensitivity analyses evaluate extended covariates, ICU type, and penalized Cox specifications.

Live discharge is treated as censoring in the primary Cox analysis. A competing-risk framework was not implemented. The Cox models analyze admission-level records and do not include a patient-level clustering or frailty term for patients with more than one qualifying admission.

The `04d_python_logistic_model.ipynb` notebook is secondary validation only. It fits a logistic model to generate parameters for SAS-Python reproducibility comparison and does not replace the Cox survival analysis.

## Reproducibility

Data extraction uses version-controlled SQL and notebooks. SAS programs reproduce selected outputs and export validation tables. The `05_sas_python_validation.ipynb` notebook compares precomputed SAS and Python secondary logistic validation outputs; it is not a new clinical analysis.

## Follow-up implementation corrections

ICU and hospital LOS now use DATETIME microsecond differences divided by 86,400,000,000, consistently with follow-up. ICU categories with fewer than 50 admissions are pooled using counts alone. Additional exploratory models stratify by era, CHF and exact SOFA; the ICU version also stratifies by pooled ICU category. These change the adjustment structure and supplement the unchanged primary age/sex/era model. PH tests, warnings and sparse-stratum counts are recorded in CURRENT_ANALYSIS.json.
