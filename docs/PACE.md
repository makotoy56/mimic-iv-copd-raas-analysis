# PACE Framework

This document describes the project design using the **PACE framework** (Plan → Acquire → Construct → Execute), providing a concise and structured　overview of how this clinical data science project was conceived and implemented.

---

## P — Plan

### Research Objective
To evaluate whether **pre-ICU exposure to RAAS inhibitors**
(ACE inhibitors and angiotensin receptor blockers) is associated with
clinical outcomes among **ICU-admitted patients with COPD**.

### Primary Question
Among adult ICU patients with COPD in MIMIC-IV:
- Is pre-ICU RAAS exposure associated with differences in in-hospital mortality?

### Secondary Questions
- Do ACE inhibitors and ARBs show similar or distinct associations?
- Are results robust to extended covariate adjustment?
- Does the association remain stable across modeling strategies?

### Study Design
- Retrospective observational cohort study
- Real-world evidence using MIMIC-IV v3.1
- ICU stay–level analysis with strict temporal ordering

---

## A — Acquire

### Data Source
- **MIMIC-IV v3.1**
- Accessed via **BigQuery**

### Core Tables Utilized
- ICU stays: `mimiciv_icu.icustays`
- Diagnoses: `mimiciv_hosp.diagnoses_icd`
- Patients: `mimiciv_hosp.patients`
- Admissions: `mimiciv_hosp.admissions`
- Prescriptions: `mimiciv_hosp.prescriptions`

### Cohort Acquisition Strategy
1. Build a standardized adult ICU cohort (age ≥ 18)
2. Restrict to first ICU stay per hospital admission
3. Identify COPD admissions using ICD-9 and ICD-10 codes
4. Preserve ICU-stay–level granularity throughout

All cohort extraction and exposure derivation steps are implemented
**entirely in SQL** to ensure reproducibility.

---

## C — Construct

### Exposure Definition
RAAS exposure is defined **strictly before or at ICU admission** using inpatient
prescription orders. This does not directly capture outpatient chronic use and is
intended as a proximal pre-ICU exposure proxy.

Exposure variables include:
- `acei_pre_icu`
- `arb_pre_icu`
- `raas_any_pre_icu`
- Monotherapy and mutually exclusive exposure groups

Detailed exposure logic is derived from medication names in
`physionet-data.mimiciv_3_1_hosp.prescriptions`, aggregated at the ICU-stay level.

### Baseline Covariates
Constructed prior to outcome modeling:
- Demographics (age, sex)
- Comorbidities
- Severity indicators (e.g., SOFA where available)
- ICU and hospital length of stay metrics

### Data Integrity Principles
- One row per ICU stay
- Explicit handling of missing exposure as non-exposure
- No Python-side merging required for cohort construction
- SQL pipelines serve as the single source of truth

---

## E — Execute

### Modeling Strategy
Primary analyses:
- Kaplan–Meier survival curves
- Cox proportional hazards models

Model progression:
1. Unadjusted RAAS exposure model
2. ACEi vs ARB subgroup comparison
3. Extended covariate Cox model

### Model Diagnostics
- Proportional hazards assessment
- Forest plots with confidence intervals
- Sensitivity to covariate inclusion

### Outputs
- Hazard ratios with 95% confidence intervals
- Survival curves
- Interpretable, publication-ready figures
- Analysis-ready datasets for reproducibility

---

## Reproducibility & Governance

- All datasets generated via versioned SQL scripts (`/sql`)
- All analyses documented in modular notebooks (`/notebooks`)
- No PHI stored or committed
- Credential files excluded via `.gitignore`

---

## Intended Use

This project is designed as:
- A **clinical data science portfolio project**
- A demonstration of end-to-end real-world evidence workflow
- A reproducible template for ICU-based observational studies

No clinical or medical recommendations are implied.

---
