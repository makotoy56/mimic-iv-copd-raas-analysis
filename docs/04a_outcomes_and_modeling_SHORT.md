# 04a. Survival Effects of RAAS Inhibitor Exposure Before or at ICU Admission in ICU COPD Patients (SHORT)

---

## 0. Overview
This notebook evaluates whether exposure to renin–angiotensin–aldosterone system (RAAS)
inhibitors **before or at ICU admission** is associated with in-hospital survival among
ICU-admitted COPD patients. The analysis follows a standard survival modeling workflow:

1. Kaplan–Meier curves (unadjusted)
2. Cox proportional hazards model (adjusted)
3. Proportional hazards (PH) diagnostics
4. Refined Cox model addressing detected PH violations

Analysis 04a serves as the foundational RAAS-vs-non-RAAS comparison and establishes the modeling framework subsequently applied in 04b for ACEi/ARB subclass analyses.

---

## 1. Introduction

### 1.1 Background
RAAS inhibitors—including ACE inhibitors (ACEi) and angiotensin receptor blockers (ARBs)—
are widely prescribed in patients with cardiovascular and pulmonary comorbidities.
Through effects on inflammation, endothelial function, vascular tone, and sympathetic
activation, chronic RAAS inhibition may plausibly influence outcomes during critical illness.

### 1.2 Rationale
Prior observational studies evaluating RAAS inhibitor use in respiratory failure or COPD
exacerbations have reported mixed results. A rigorous time-to-event analysis is required
to clarify the association between RAAS inhibitor exposure **before or at ICU admission**
and in-hospital mortality.

### 1.3 Objective
To evaluate whether RAAS inhibitor exposure before or at ICU admission is associated with
reduced in-hospital mortality among ICU-admitted COPD patients using Kaplan–Meier analysis
and multivariable Cox proportional hazards modeling.

---

## 2. Methods

### 2.1 Study Cohort
The cohort was derived from MIMIC-IV v3.1 and constructed in upstream analyses (01–03).
Key outcome variables include:

- `death_event`: indicator of in-hospital death
- `time_to_event_days`: time from ICU admission to death or hospital discharge

### 2.2 Exposure Definition
Pre-ICU RAAS inhibitor exposure (`raas_pre_icu = 1`) was defined using prescription records
initiated **before or at ICU admission**, as constructed in analysis 03b.

Exposure groups for 04a:
- RAAS inhibitor–exposed patients before or at ICU admission
- Non-exposed patients (reference)

### 2.3 Covariates
The primary Cox model adjusted for:
- age
- gender
- anchor_year_group (calendar-time categorical variable)

### 2.4 Statistical Modeling
The analysis proceeded as follows:
1. Kaplan–Meier survival curves comparing RAAS-exposed vs non-exposed patients
2. Multivariable Cox proportional hazards regression
3. Schoenfeld residual–based PH diagnostics
4. Refined Cox model incorporating:
   - stratification by `anchor_year_group`

The refined specification was used to address detected PH violations and was adopted
consistently in subsequent analyses (04b).

---

## 3. Data Preparation

### 3.1 Outcome Table Construction
The outcome dataset (`cohort_copd_outcomes`) was generated using:

run_sql_script("../sql/04_build_outcomes.sql")

This step computes `death_event` and `time_to_event_days` directly in BigQuery.

### 3.2 Cox-Ready Dataset Preparation
The following preprocessing steps were applied:
- gender encoded as `gender_male`
- `anchor_year_group` treated as categorical

---

## 4. Results

### 4.1 Kaplan–Meier Survival Analysis
(Unadjusted comparison)

RAAS inhibitor–exposed patients demonstrated improved survival compared with non-exposed
patients. The log-rank test indicated a statistically significant difference between groups.

### 4.2 Primary Cox Model
After adjustment for age, gender, and calendar time, RAAS inhibitor exposure before or at
ICU admission was associated with approximately **30% lower hazard of in-hospital mortality**
(HR ≈ 0.70, p < 0.005).

### 4.3 Proportional Hazards Diagnostics
Schoenfeld residual testing indicated:
- PH violations for `anchor_year_group`
- No meaningful PH violation for age, gender, or `raas_pre_icu`

Accordingly, a refined Cox model was specified.

### 4.4 Refined Cox Model (stratification)
After addressing PH violations via stratification:

| Variable | HR | 95% CI | Interpretation |
|--------|----|--------|----------------|
| RAAS exposure | **0.71** | **0.58–0.88** | Robust protective association |

Model refinement did not materially alter the estimated RAAS inhibitor effect.

---

## 5. Discussion

### 5.1 Summary of Findings
- Both unadjusted and adjusted analyses demonstrate improved survival among RAAS inhibitor–exposed patients.
- Detected PH violations were appropriately addressed using stratification.
- The refined Cox model yields a stable and clinically interpretable estimate of association.

### 5.2 Strengths and Limitations

**Strengths**
- Transparent, stepwise survival analysis workflow
- Explicit PH diagnostics and correction
- Cohort and exposure definitions derived from reproducible SQL pipelines

**Limitations**
- Observational design with potential residual confounding
- Medication exposure inferred from prescription records
- Severity indices (e.g., SOFA, APACHE II) not included to maintain comparability with 04b

### 5.3 Implications for Follow-Up Analyses
- The refined Cox specification serves as the modeling template for 04b and 04c.
- Subclass-specific evaluation of ACEi vs ARB is justified given the robust class-wide signal.
- Future extensions may incorporate comorbidities, physiologic markers, and causal methods.

---

## 6. Conclusion
RAAS inhibitor exposure before or at ICU admission is associated with significantly lower in-hospital mortality among ICU-admitted COPD patients. This association is consistent across Kaplan–Meier, Cox, and PH-compliant refined Cox models, providing a robust statistical foundation for subsequent subclass analyses in 04b.