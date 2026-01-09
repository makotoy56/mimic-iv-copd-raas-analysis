# 04c - RAAS Inhibitors and In-Hospital Mortality in ICU Patients With COPD (SHORT)

---

## 1. Study Question
Is the exposure to RAAS inhibitors before or at ICU admission associated with reduced in-hospital mortality among ICU-admitted patients with COPD?

---

## 2. Cohort & Variables

* **Data:** MIMIC-IV v3.1, 11,964 ICU stays with COPD
* **Exposure:** Pre-ICU use of RAAS inhibitors (binary indicator)
* **Outcome:** In-hospital mortality, analyzed as time-to-event from ICU admission
* **Core covariates:** Age, sex, CHF, CKD, diabetes, and SOFA score
* **Sensitivity covariates:** ICU type (one-hot encoded categories)

The SOFA score at ICU admission was treated as a baseline confounder rather than a mediator, given the temporal ordering in which chronic RAAS exposure precedes acute illness severity.

---

## 3. Methods
- Cox proportional hazards models fitted using *lifelines*  
- Baseline hazards stratified by calendar time (`anchor_year_group`) to account for temporal variation in ICU mortality and practice patterns  
- **Primary analysis:** unpenalized Cox model (penalizer = 0.0)  
- Two model specifications:
  - **Core model:** demographic factors, baseline severity, and comorbidities  
  - **ICU-extended model:** core model plus ICU type indicators  
- Proportional hazards assumptions assessed using Schoenfeld residual–based tests and visual diagnostics

---

## 4. Key Results
- **Core model:**  
  - Pre-ICU RAAS inhibitor use was associated with a lower risk of in-hospital mortality  
  - HR ≈ **0.81–0.90**, with confidence intervals narrowly excluding or approaching unity depending on specification

- **ICU-extended model:**  
  - The association between RAAS exposure and mortality was attenuated and no longer statistically significant  
  - HR ≈ **0.89–0.94**, 95% CI crossing 1.0

- Across models, the estimated hazard ratios consistently favored RAAS exposure, but statistical significance was sensitive to adjustment for ICU type.

---

## 5. Interpretation
Adjustment for ICU type substantially reduced the apparent protective association of pre-ICU RAAS inhibitor use, suggesting that ICU-level factors and case-mix differences explain part of the observed signal in simpler models.

The stability of effect direction across specifications supports robustness of the estimate, while the attenuation after ICU type adjustment cautions against strong causal interpretation.

Proportional hazards diagnostics showed no major violations that would invalidate the primary model conclusions.

---

## 6. Next Steps
- Subclass-specific analyses comparing **ACE inhibitors vs ARBs**  
- Propensity score–based approaches (IPTW or matching) to address confounding by indication  
- Exploration of effect heterogeneity across severity strata or ventilatory status

---

## 7. Files
- **Full analysis notebook:** `04c_extended_covariate_cox_model.ipynb`  
- **Full report:** `04c_extended_covariate_cox_model.md`  
- **This short summary:** `04c_extended_covariate_cox_model_SHORT.md`