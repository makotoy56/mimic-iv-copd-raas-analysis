# 04b — Class-Specific Survival Effects of ACE Inhibitors and ARBs in ICU COPD Patients (SHORT)

---

## 0. Overview
This notebook evaluates whether the survival benefit associated with “any RAAS inhibitor” observed in analysis 04a is driven predominantly by ACE inhibitors (ACEi), angiotensin receptor blockers (ARB), or shared across both subclasses.

Analysis 04b applies the same core Cox modeling framework used in 04a, preserving cohort definitions, outcome construction, and calendar-time stratification to ensure full methodological comparability. The key analytic change is the exposure definition: separate ACEi and ARB indicators replace the combined RAAS exposure used in 04a.

---

## 1. Introduction

### 1.1 Background
ACE inhibitors and ARBs represent distinct pharmacological subclasses within the renin–angiotensin–aldosterone system (RAAS) pathway. Both attenuate angiotensin II–mediated vasoconstriction, inflammation, and sympathetic activation, but through different mechanisms (ACE inhibition vs. AT1 receptor blockade).

Analysis 04a demonstrated a protective association between RAAS inhibitor exposure (as a combined class) and in-hospital mortality, motivating a subclass-specific evaluation.

### 1.2 Rationale
Determining whether ACEi and ARBs exhibit similar or divergent survival associations is clinically relevant, as these drugs differ mechanistically and may be prescribed to distinct patient populations.

### 1.3 Objective
To estimate the independent associations of ACEi and ARB monotherapy with in-hospital mortality among ICU-admitted COPD patients using Cox proportional hazards modeling.

---

## 2. Methods

### 2.1 Study Cohort
The same ICU COPD cohort from MIMIC-IV v3.1 used in analysis 04a was retained to ensure direct comparability.

Outcome definitions were identical:
- `death_event`: in-hospital death
- `time_to_event_days`: ICU admission → death or discharge

### 2.2 Exposure Definition (Class-Specific)
RAAS subclassification was generated in analysis 03b using prescription records prior to or at ICU admission:

- Non-RAAS inhibitor users: 11,018 patients (92.1%)
- ACEi-only users: 643 patients (5.4%)
- ARB-only users: 290 patients (2.4%)
- Dual ACEi+ARB users: 13 patients (0.1%)

Because dual users cannot be attributed to a single subclass, the 13 dual-exposure cases were excluded from Cox modeling. The final monotherapy analysis sample included 11,951 ICU admissions.

### 2.3 Covariates
The Cox model adjusted for:
- age
- gender
- calendar time (`anchor_year_group`, used as a stratification variable)

### 2.4 Statistical Modeling
A stratified Cox proportional hazards model was fitted with:
- stratification by `anchor_year_group` to account for temporal heterogeneity
- exposure variables: `acei_user`, `arb_user`
- reference group: non-RAAS inhibitor users

This specification mirrors the time-stratified structure used in 04a while focusing on class-specific exposure effects.

### 2.5 Proportional Hazards Diagnostics
Schoenfeld residual tests were performed for the exposure variables (ACEi and ARB) to confirm proportional hazards assumptions.

---

## 3. Data Preparation

### 3.1 Loading Cohort with RAAS inhibitor Subclass Flags
The analysis-ready cohort was loaded directly from BigQuery, joining outcome data with RAAS inhibitor subclass indicators generated in analysis 03b.

### 3.2 Constructing Monotherapy Indicators
Binary exposure variables (`acei_user`, `arb_user`) were constructed to represent exclusive
ACEi or ARB use prior to or at ICU admission.

### 3.3 Preparing Cox-Ready Dataset
Final preprocessing included:
- encoding gender as a binary indicator
- retaining `anchor_year_group` for stratification
- excluding dual-exposure cases

---

## 4. Results

### 4.1 Cohort Distribution
Among the 11,951 patients included in the Cox model:
- 643 (5.4%) ACEi monotherapy
- 290 (2.4%) ARB monotherapy
- 11,018 (92.2%) non-RAAS users

### 4.2 Cox Model Results

| Exposure | HR | 95% CI | p-value |
|--------|-----|---------------|---------|
| ACEi | 0.86 | 0.76–0.96 | 0.01 |
| ARB | 0.80 | 0.57–1.12 | 0.19 |

ACE inhibitor exposure was significantly associated with reduced in-hospital mortality. ARB exposure showed a protective direction consistent with ACEi but did not reach
statistical significance.

### 4.3 Forest Plot
A forest plot visualizing class-specific hazard ratios and confidence intervals is shown in the notebook.

### 4.4 Proportional Hazards Diagnostics

| Covariate | Test Statistic | p-value |
|----------|----------------|---------|
| ACEi | 2.92 | 0.088 |
| ARB | 0.09 | 0.771 |

No violations of the proportional hazards assumption were detected for either exposure.

---

## 5. Discussion

### 5.1 Summary of Findings
ACE inhibitor use was independently associated with lower in-hospital mortality among ICU-admitted COPD patients. ARB exposure demonstrated a similar protective direction, although the association was not statistically significant.

The ACEi effect size closely aligns with the combined RAAS inhibitors estimate from 04a, indicating that the class-wide signal observed previously is not driven by a single anomalous subgroup.

### 5.2 Strengths and Limitations

**Strengths**
- Direct methodological comparability with analysis 04a
- Clear separation of RAAS inhibitor subclasses
- Formal assessment of proportional hazards assumptions

**Limitations**
- Dual ACEi+ARB exposure was rare and excluded
- Observational design with potential residual confounding
- Extended severity covariates were not included to preserve comparability with 04a

### 5.3 Implications for Further Analysis
Future analyses (e.g., 04c) may:
- incorporate clinical severity measures (SOFA, ventilation status)
- apply causal inference methods (PSM, IPTW, MSM)
- explore subgroup-specific treatment effects

---

## 6. Conclusion
ACE inhibitor use prior to or at ICU admission was associated with significantly reduced in-hospital mortality among ICU COPD patients. ARB exposure showed a consistent but non-significant protective trend.

These results refine the class-wide RAAS association observed in 04a and provide a clinically interpretable foundation for extended modeling in subsequent analyses.