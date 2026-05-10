# Methods Overview

This document holds the methods detail that was shortened in the README. It preserves the analytic design and definitions used across the notebooks.

## Study Design And Data Source

This is a retrospective observational cohort study using MIMIC-IV v3.1, a de-identified ICU electronic health record database. The analysis is intended for reproducible clinical analytics and real-world evidence workflow demonstration.

## Cohort Construction

Adult ICU patients with COPD were identified using ICD-9 and ICD-10 diagnosis codes recorded during hospitalization. Cohort construction is performed at the ICU-stay/admission level using reproducible BigQuery SQL and notebook-based checks.

Primary workflow:

- `01_icu_cohort.ipynb`: adult ICU cohort extraction
- `02_cohort_and_exposures.ipynb`: COPD cohort and RAAS exposure construction
- `03a_baseline.ipynb`: baseline covariate table
- `03b_merge_exposures.ipynb`: detailed exposure merge

## Exposure Definition

The primary exposure is pre-ICU RAAS inhibitor use, defined from inpatient prescription orders for ACE inhibitors or ARBs before or at ICU admission. This definition does not directly measure outpatient chronic medication use, adherence, dose, duration, or medication discontinuation before hospitalization.

Detailed exposure indicators include ACE inhibitor exposure, ARB exposure, dual exposure, and mutually exclusive ACE inhibitor or ARB monotherapy indicators for subgroup analysis.

## Outcome Definition

The primary outcome is time-to-in-hospital mortality, measured from ICU admission until in-hospital death or hospital discharge. Patients discharged alive are censored at discharge.

## Covariates

Covariates were selected a priori based on a conceptual clinical framework and include demographics, cardiovascular comorbidities, chronic kidney disease, diabetes, and SOFA score. Extended sensitivity models include ICU type and additional clinical variables.

## Statistical Analysis

The primary clinical analysis uses Kaplan-Meier survival curves and Cox proportional hazards regression. Proportional hazards assumptions are assessed using Schoenfeld residual-based diagnostics. Sensitivity analyses evaluate extended covariates, ICU type, and penalized Cox specifications.

The `04d_python_logistic_model.ipynb` notebook is secondary validation only. It fits a logistic model to generate parameters for SAS-Python reproducibility comparison and does not replace the Cox survival analysis.

## Reproducibility

Data extraction uses version-controlled SQL and notebooks. SAS programs reproduce selected outputs and export validation tables. The `05_sas_python_validation.ipynb` notebook compares precomputed SAS and Python secondary logistic validation outputs; it is not a new clinical analysis.
