# RAAS Blockers and Clinical Outcomes in COPD ICU Admissions  
*An ICU Hospital Cohort Study of COPD Patients Using MIMIC-IV*

---

Maintained by <br>
Makoto Yoshida, PhD <br>
Clinical Data Analytics Portfolio <br>
LinkedIn: https://www.linkedin.com/in/makoto-yoshida/ <br>

---

## Project Overview

This project is a reproducible real-world clinical data analysis using MIMIC-IV, BigQuery, Python, and SAS. It evaluates the association between pre-ICU RAAS inhibitor exposure and in-hospital mortality among ICU patients with COPD.

## What this project demonstrates

- EHR-based cohort construction using SQL and BigQuery
- Clinically informed exposure and outcome definitions
- Survival analysis using Kaplan-Meier curves and Cox proportional hazards models
- Subgroup and sensitivity analyses
- Cross-platform reproducibility validation using Python and SAS

## Clinical Data Analysis Workflow

```text
01_icu_cohort.ipynb
ICU Cohort Extraction
    ↓

02_cohort_and_exposures.ipynb
COPD Cohort + RAAS Exposure Definition
    ↓

03a_baseline.ipynb
Baseline Cohort Construction
    ↓

03b_merge_exposures.ipynb
Detailed RAAS Exposure Merge
    ↓

04a_outcomes_and_modeling.ipynb
Primary Survival Analysis
    ↓

├─ 04b_outcomes_and_modeling_raas_subgroups.ipynb
│      ACEi vs ARB Subgroup Analysis
│
├─ 04c_extended_covariate_cox_model.ipynb
│      Extended Covariate Cox Models
│
└─ 04d_python_logistic_model.ipynb
       Python Logistic Validation Model
           ↓

05_sas_python_validation.ipynb
SAS-Python Reproducibility Validation
```

---

## Technical Snapshot

- **Data**: MIMIC-IV v3.1 (PhysioNet), ICU admissions
- **Design**: Retrospective observational cohort study
- **Population**: Adult ICU patients with COPD
- **Exposure**: Pre-ICU RAAS inhibitor use (ACE inhibitors [ACEi] / ARBs) based on inpatient prescription orders before ICU admission; not outpatient medication history
- **Outcome**: Time-to-in-hospital mortality
- **Methods**:
  - BigQuery SQL for reproducible cohort construction
  - Kaplan–Meier survival analysis
  - Cox proportional hazards regression
  - Sensitivity analyses with extended covariates
- **Tools**: BigQuery, Python (pandas, lifelines, statsmodels, pandas-gbq), Jupyter, SAS
- **Key finding**: Pre-ICU RAAS inhibitor exposure was associated with lower observed in-hospital mortality; the association was more pronounced for ACE inhibitors than for ARBs.
- **Interpretation**: Observational association; hypothesis-generating.

---

## Start Here

- **ICU COPD cohort construction**: [01_icu_cohort.ipynb](notebooks/01_icu_cohort.ipynb)
- **Cohort and exposure definition**: [02_cohort_and_exposures.ipynb](notebooks/02_cohort_and_exposures.ipynb)
- **Baseline covariates**: [03a_baseline.ipynb](notebooks/03a_baseline.ipynb)
- **Merge exposures**: [03b_merge_exposures.ipynb](notebooks/03b_merge_exposures.ipynb)
- **Outcomes and modeling**: [04a_outcomes_and_modeling.ipynb](notebooks/04a_outcomes_and_modeling.ipynb)
- **RAAS subgroup analyses**: [04b_outcomes_and_modeling_raas_subgroups.ipynb](notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb)
- **Extended Cox model analyses**: [04c_extended_covariate_cox_model.ipynb](notebooks/04c_extended_covariate_cox_model.ipynb)
- **Python logistic validation model**: [04d_python_logistic_model.ipynb](notebooks/04d_python_logistic_model.ipynb)
- **SAS-Python validation**: [05_sas_python_validation.ipynb](notebooks/05_sas_python_validation.ipynb)
- **SQL pipelines (BigQuery)**: [sql/](sql/)
- **Stepwise short documentation**: [docs/](docs/)
- **Analytic framework (PACE)**: [PACE.md](docs/PACE.md)

---

## Introduction

Chronic obstructive pulmonary disease (COPD) is frequently complicated by cardiovascular comorbidity, and ICU-admitted COPD patients represent a high-risk population. This project uses MIMIC-IV electronic health record data to evaluate whether pre-ICU RAAS inhibitor exposure is associated with time-to-in-hospital mortality, while explicitly treating the findings as observational and hypothesis-generating.

---

## Background and Rationale

RAAS signaling has biologic relevance to lung injury and pulmonary inflammation. Experimental studies implicate ACE2 and angiotensin II signaling in acute lung injury pathways [1,2], and reviews have proposed that RAAS modulation may influence chronic pulmonary inflammation and airway remodeling in COPD [6].

Observational clinical studies have reported favorable outcomes among COPD or severe respiratory illness populations exposed to ACE inhibitors or ARBs [3,4]. Comparative COPD research also suggests that ACE inhibitors and ARBs may have distinct respiratory associations [5].

This analysis addresses a focused evidence gap: whether pre-ICU RAAS inhibitor exposure is associated with in-hospital mortality among ICU-admitted COPD patients, and whether ACE inhibitor and ARB subclasses show different observed associations.

COPD was defined using established ICD-9 and ICD-10 diagnosis codes recorded during hospitalization, consistent with prior administrative and EHR-based COPD research [7,8]. This supports reproducible cohort construction and clear temporal ordering between chronic COPD status, pre-ICU medication exposure, and ICU outcomes.

## Methods Overview

This study was conducted using a pre-specified analytic plan grounded in a causal inference framework to evaluate the association between pre-ICU RAAS inhibitor exposure and in-hospital mortality among ICU-admitted patients with COPD.

### Study Design and Data Source

We performed a retrospective observational cohort study using the MIMIC-IV database (version 3.1), which contains detailed, de-identified electronic health record data from ICU admissions at Beth Israel Deaconess Medical Center. All analyses were conducted within approved data use environments.

### Cohort Construction

Adult patients admitted to the ICU with a diagnosis of COPD were identified using validated ICD-9 and ICD-10 diagnosis codes recorded during hospitalization. The cohort was constructed at the ICU-stay/admission level. Multiple eligible admissions per patient may be retained when they correspond to distinct hospital or ICU stays. Cohort construction and variable derivation were implemented using reproducible BigQuery-compatible SQL pipelines.

### Exposure Definition

The primary exposure was pre-ICU use of RAAS inhibitors, defined using inpatient prescription orders for ACE inhibitors or ARBs recorded before or at ICU admission. This does not directly capture outpatient chronic use. Patients were categorized as RAAS-exposed or non-exposed. Subgroup analyses further distinguished ACE inhibitor and ARB use to explore potential class-specific effects.

### Outcome

The primary outcome was time to in-hospital mortality, measured from ICU admission until death or hospital discharge. Patients discharged alive were censored at discharge.

### Covariate Selection

Covariates were selected a priori based on a conceptual causal framework to address confounding. These included:

* Demographics (age, sex)
* Cardiovascular comorbidities (e.g., congestive heart failure, chronic kidney disease, diabetes)
* Illness severity (SOFA score at ICU admission)

Additional sensitivity models incorporated ICU type and extended clinical variables.

### Statistical Analysis

Survival analyses were performed using Kaplan–Meier curves and Cox proportional hazards regression. Multivariable models adjusted for pre-specified covariates to estimate adjusted hazard ratios and 95% confidence intervals. Proportional hazards assumptions were evaluated using Schoenfeld residuals.

Sensitivity analyses assessed model robustness by incorporating extended covariates and ICU type stratification. Penalized Cox models were explored to evaluate potential collinearity and overfitting.

### Reproducibility

All data extraction and transformation steps were implemented using version-controlled SQL scripts. Statistical modeling was conducted in structured Jupyter notebooks using Python (pandas, lifelines, statsmodels, pandas-gbq). The full analytic workflow is documented and reproducible within this repository. An independent SAS workflow is included to reproduce key statistical models and verify cross-platform consistency of the results.

---

## Results

The results summarized below highlight the primary directional findings; detailed estimates and diagnostic outputs are provided in the accompanying notebooks.

### Cohort characteristics

The final analytic cohort consisted of ICU-admitted patients with a diagnosis of COPD identified from the MIMIC-IV database. Baseline characteristics differed between patients with and without pre-ICU exposure to RAAS inhibitors, reflecting the high prevalence of cardiovascular comorbidities among RAAS inhibitor users. These differences were addressed through multivariable adjustment in subsequent survival models.

### Association between RAAS inhibitor use and in-hospital mortality

In time-to-event analyses, pre-ICU exposure to RAAS inhibitors was associated with lower observed in-hospital mortality compared with no RAAS inhibitor exposure. This association was observed in Kaplan–Meier survival curves and remained directionally consistent after adjustment for demographic factors, illness severity, and major comorbidities in Cox proportional hazards models.

### ACE inhibitor and ARB subclass analyses

When RAAS inhibitors were evaluated by drug class, ACE inhibitor use demonstrated a more pronounced association with lower observed in-hospital mortality compared with ARB use. Although confidence intervals overlapped and causal inference cannot be established, this pattern was consistent across multiple model specifications. These findings suggest potential heterogeneity within RAAS inhibitor subclasses that warrants further investigation.

### Sensitivity analyses

The association between RAAS inhibitor exposure and lower observed in-hospital mortality was attenuated but remained directionally consistent in sensitivity analyses incorporating additional covariates, including ICU type. Model diagnostics did not identify violations that materially affected the interpretation of the primary findings.

### Key Finding

Pre-ICU RAAS inhibitor exposure was associated with lower observed in-hospital mortality, with a more pronounced association for ACE inhibitors than for ARBs. This association was attenuated after further adjustment for ICU type and acute illness severity, suggesting that differences in ICU-level case mix and organ dysfunction may contribute to the observed signal.

---

## Discussion

The findings should be interpreted in the context of prior observational studies, including the Veterans Affairs cohort reported by Mortensen et al., which found lower observed short-term mortality among patients hospitalized for acute COPD exacerbations who were receiving ACE inhibitors or ARBs before admission [4].

This project extends that line of evidence into an ICU COPD cohort, where illness severity, competing risks, and treatment intensity differ from general hospitalized populations. It also evaluates ACE inhibitors and ARBs both as a combined exposure and as separate subclasses, motivated by mechanistic RAAS literature [1,2] and comparative COPD evidence [5].

### Limitations and interpretation

This analysis is observational and cannot establish causal effects of RAAS inhibitors on mortality. Despite strict temporal ordering of exposure before ICU admission and extensive covariate adjustment, residual confounding by indication and unmeasured severity factors may remain. RAAS inhibitor use likely reflects underlying cardiovascular comorbidity and outpatient care patterns that are not fully captured in EHR data. Accordingly, the findings should be interpreted as evidence of association rather than causation, and primarily as hypothesis-generating results that motivate further prospective or quasi-experimental studies.

---

## Reproducibility / Validation

### Environment

`requirements.txt` provides a minimal, portable environment specification for running the validation script and analysis notebooks.

Install the minimal environment:
````text
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
````

Environment setup steps are intentionally not included as a tracked notebook. Local configuration, including Python environment creation, Google Cloud authentication, MIMIC-IV/PhysioNet BigQuery access, and application default credentials, must be configured separately before running the workflow.

### SAS-Python validation

This project separates model fitting in the 04-series notebooks from validation in the 05 notebook, supporting reproducibility across statistical environments.

For SAS/Python logistic validation:

1. Run `notebooks/04d_python_logistic_model.ipynb` to generate `python/outputs/python_logistic_parameters.csv`.
2. Run `notebooks/05_sas_python_validation.ipynb` to compare the SAS and Python parameter outputs.

SAS programs use SAS OnDemand-style paths and may require local path adjustment before execution. Generated CSV outputs under `python/outputs/` are ignored by Git and can be reproduced from the notebooks.

### Validation checklist

`scripts/validation_checklist.py` performs a lightweight sanity check by enumerating candidate tables in the BigQuery dataset used for this COPD ICU RAAS analysis. It uses `INFORMATION_SCHEMA` and checks table existence only.

Run the checklist:
````text
python scripts/validation_checklist.py
````

Authenticate first with Application Default Credentials:
````text
gcloud auth application-default login
````

Important scope note:

- This script only checks table existence.
- It does not perform data quality validation.
- It does not validate table contents.

---

## Project Structure
````text
mimic-iv-copd-raas-analysis/
├── notebooks/
│   ├── 01_icu_cohort.ipynb
│   ├── 02_cohort_and_exposures.ipynb
│   ├── 03a_baseline.ipynb
│   ├── 03b_merge_exposures.ipynb
│   ├── 04a_outcomes_and_modeling.ipynb
│   ├── 04b_outcomes_and_modeling_raas_subgroups.ipynb
│   ├── 04c_extended_covariate_cox_model.ipynb
│   ├── 04d_python_logistic_model.ipynb
│   └── 05_sas_python_validation.ipynb
│
├── sql/
│   ├── 01_extract_base.sql
│   ├── 02_build_cohort_copd.sql
│   ├── 02_exposure_raas*.sql
│   ├── 03_build_baseline.sql
│   ├── 03_merge_exposures.sql
│   └── 04_build_outcomes*.sql
│
├── docs/
│   ├── 01_icu_cohort_SHORT.md
│   ├── 02_cohort_and_exposures_SHORT.md
│   ├── 03a_baseline_SHORT.md
│   ├── 03b_merge_exposures_SHORT.md
│   ├── 04a_outcomes_and_modeling_SHORT.md
│   ├── 04b_outcomes_and_modeling_raas_subgroups_SHORT.md
│   ├── 04c_extended_covariate_cox_model_SHORT.md
│   ├── 04d_python_logistic_model_SHORT.md
│   ├── 05_sas_python_validation_SHORT.md
│   └── PACE.md
│
├── data/
│   ├── interim/
│   └── processed/
├── scripts/
│   └── validation_checklist.py
├── sas/
│   ├── README.md
│   └── programs/
├── .github/
├── .gitignore
└── README.md
````

---

## Data Source and Compliance

This project uses data from the Medical Information Mart for Intensive Care IV (MIMIC-IV) database (version 3.1), which is maintained by the MIT Laboratory for Computational Physiology and made available via PhysioNet.

According to the PhysioNet data use requirements, the following citation should be used when referencing MIMIC-IV:
Johnson A., Bulgarelli L., Pollard T., Gow B., Moody B., Horng S., Celi L.A., & Mark R. (2024). *MIMIC-IV (version 3.1)*. PhysioNet. RRID:SCR_007345. https://doi.org/10.13026/kpb9-mt58.

Access to the MIMIC-IV database was granted following completion of the required training and approval under the PhysioNet data use agreement.  
This repository contains no patient-level data. All analyses were conducted within approved MIMIC-IV environments, and only code and aggregate descriptions are shared.

---

## References

1. Imai Y, Kuba K, Rao S, et al. Angiotensin-converting enzyme 2 protects from severe acute lung failure. *Nature*. 2005;436:112–116. doi:10.1038/nature03712.

2. Kuba K, Imai Y, Rao S, et al. A crucial role of angiotensin converting enzyme 2 (ACE2) in SARS coronavirus–induced lung injury. *Nature Medicine*. 2005;11:875–879. doi:10.1038/nm1267.

3. Khodneva Y, Malla G, Clarkson S, et al. What is the association of renin–angiotensin–aldosterone system inhibitors with COVID-19 outcomes: retrospective study of racially diverse patients? *BMJ Open*. 2022;12:e053961. doi:10.1136/bmjopen-2021-053961.

4. Mortensen EM, Pugh MJ, Copeland LA, et al. Impact of statins and angiotensin-converting enzyme inhibitors on mortality after COPD exacerbations. *Respiratory Research*. 2009;10:45. doi:10.1186/1465-9921-10-45.

5. Lai CC, Wang YH, Wang CY, et al. Comparative effects of angiotensin-converting enzyme inhibitors and angiotensin II receptor blockers on the risk of pneumonia and severe exacerbations in patients with COPD. *International Journal of Chronic Obstructive Pulmonary Disease*. 2018;13:867–874. doi:10.2147/COPD.S154803.

6. Vasileiadis I, et al. Angiotensin-converting enzyme inhibitors and angiotensin receptor blockers: A promising medication for chronic obstructive pulmonary disease. *COPD: Journal of Chronic Obstructive Pulmonary Disease*. 2018;15(2):148–156. doi:10.1080/15412555.2018.1430498.

7. Mapel DW, Hurley JS, Frost FJ, Petersen HV, Picchi MA, Coultas DB. 
Validity of a COPD diagnosis in administrative data. 
*International Journal of Chronic Obstructive Pulmonary Disease*. 2011;6:273–281. 
doi:10.2147/COPD.S17851.

8. Stein BD, Bautista A, Schumock GT, et al. 
Identifying patients with chronic obstructive pulmonary disease using administrative data. 
*Chest*. 2012;141(3):605–613. 
doi:10.1378/chest.11-2442.
