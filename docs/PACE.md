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
- What are the ACEi-only-order and ARB-only-order associations, each versus neither qualifying order? The main analysis does not report a direct between-class contrast.
- Are results robust to extended covariate adjustment?
- Does the association remain stable across modeling strategies?

### Study Design
- Retrospective observational cohort study
- Real-world evidence using MIMIC-IV v3.1
- One qualifying hospital admission per record, anchored to its first ICU stay; first-day severity may be measured after follow-up begins

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
4. Preserve one qualifying admission anchored to its first ICU stay throughout

All cohort extraction and exposure derivation steps are implemented
**entirely in SQL** to ensure reproducibility.

---

## C — Construct

### Exposure Definition
RAAS exposure is defined **strictly before or at ICU admission** using inpatient
prescription orders. This does not directly capture outpatient chronic use and is
intended as a proximal pre-ICU prescription-record proxy. Qualifying records have `starttime <= intime` in the same admission; actual administration, continuing treatment and simultaneous ACEi/ARB administration are not verified.

Exposure variables include:
- `acei_pre_icu`
- `arb_pre_icu`
- `raas_any_pre_icu`
- Mutually exclusive ACEi-only, ARB-only, both-class and neither prescription-order flags; legacy monotherapy names do not verify administration

Detailed exposure logic is derived from medication names in
`physionet-data.mimiciv_3_1_hosp.prescriptions`, aggregated at the ICU-stay level.

### Timing of analysis fields
- The primary model uses age and sex with era strata.
- Core/ICU sensitivity specifications include first-day SOFA, which can use information through 24 hours after ICU follow-up starts. They are exploratory, not baseline-only severity adjustment.
- Charlson-derived comorbidities supplement exploratory models.
- ICU and hospital lengths of stay are descriptive outcome-related fields, not baseline severity adjustment.
- [Timing limitations and separate reanalysis options](ANALYSIS_TIMING_LIMITATIONS.md)

### Data Integrity Principles
- One row per qualifying hospital admission, anchored to its first ICU stay
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
1. Kaplan–Meier/log-rank summaries and the age/sex/era primary Cox model
2. ACEi-only orders versus neither and ARB-only orders versus neither; no direct between-class test
3. Exploratory first-day-SOFA core/ICU, penalized and additional-strata sensitivity models

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
