# RAAS Blockers and Clinical Outcomes in COPD ICU Admissions
*An ICU Hospital Cohort Study of COPD Patients Using MIMIC-IV*

---

Maintained by <br>
Makoto Yoshida, PhD <br>
Clinical Data Analytics Portfolio <br>
LinkedIn: https://www.linkedin.com/in/makoto-yoshida/ <br>

---

## Project Overview

This project is a reproducible real-world clinical data analysis using MIMIC-IV, BigQuery SQL, Python, Jupyter, and SAS. It evaluates the observational association between pre-ICU RAAS inhibitor exposure and in-hospital mortality among ICU patients with COPD.

The portfolio emphasis is on end-to-end clinical data workflow: EHR cohort construction, clinically motivated exposure and outcome definitions, survival analysis, sensitivity analysis, and cross-platform reproducibility validation.

## What this project demonstrates

- EHR-based observational cohort construction using BigQuery SQL
- Clinically informed exposure, outcome, and covariate definitions
- Kaplan-Meier and Cox proportional hazards survival analysis
- ACE inhibitor vs ARB subgroup comparison
- Sensitivity analyses with extended covariates
- Python and SAS reproducibility validation of key model outputs

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
- **Design**: EHR-based retrospective observational cohort study
- **Population**: Adult ICU patients with COPD
- **Exposure**: Pre-ICU RAAS inhibitor use (ACE inhibitors [ACEi] / ARBs) based on inpatient prescription orders before ICU admission; not outpatient medication history
- **Outcome**: Time-to-in-hospital mortality
- **Methods**: Kaplan-Meier survival analysis, Cox proportional hazards regression, sensitivity analyses with extended covariates
- **Tools**: BigQuery SQL, Python (pandas, lifelines, statsmodels, pandas-gbq), Jupyter, SAS
- **Key finding**: Pre-ICU RAAS inhibitor exposure was associated with lower observed in-hospital mortality; the association was more pronounced for ACE inhibitors than for ARBs.
- **Interpretation**: Observational association; hypothesis-generating; cannot establish causality.

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
- **Study background**: [docs/STUDY_BACKGROUND.md](docs/STUDY_BACKGROUND.md)
- **Discussion and limitations**: [docs/DISCUSSION_AND_LIMITATIONS.md](docs/DISCUSSION_AND_LIMITATIONS.md)
- **SQL pipelines (BigQuery)**: [sql/](sql/)
- **Stepwise short documentation**: [docs/](docs/)
- **Analytic framework (PACE)**: [docs/PACE.md](docs/PACE.md)

---

## Background and Rationale

COPD is frequently complicated by cardiovascular comorbidity, and ICU-admitted COPD patients represent a high-risk population. This project uses MIMIC-IV electronic health record data to evaluate whether pre-ICU RAAS inhibitor exposure is associated with time-to-in-hospital mortality.

The rationale is grounded in RAAS biology, prior COPD and respiratory literature, and the possibility that ACE inhibitors and ARBs may have different observed associations in COPD populations. The README keeps this context brief for portfolio readability; detailed biologic and literature background is provided in [docs/STUDY_BACKGROUND.md](docs/STUDY_BACKGROUND.md).

This analysis is observational and hypothesis-generating. It is designed to demonstrate a transparent clinical data analysis workflow, not to estimate a causal treatment effect.

## Methods Overview

This study was conducted using a pre-specified analytic plan grounded in a causal inference framework to evaluate the association between pre-ICU RAAS inhibitor exposure and in-hospital mortality among ICU-admitted patients with COPD.

### Study Design and Data Source

We performed a retrospective observational cohort study using the MIMIC-IV database (version 3.1), which contains detailed, de-identified electronic health record data from ICU admissions at Beth Israel Deaconess Medical Center. All analyses were conducted within approved data use environments.

### Cohort Construction

Adult patients admitted to the ICU with a diagnosis of COPD were identified using established ICD-9 and ICD-10 diagnosis codes recorded during hospitalization. The cohort was constructed at the ICU-stay/admission level. Multiple eligible admissions per patient may be retained when they correspond to distinct hospital or ICU stays.

### Exposure Definition

The primary exposure was pre-ICU use of RAAS inhibitors, defined using inpatient prescription orders for ACE inhibitors or ARBs recorded before or at ICU admission. This does not directly capture outpatient chronic use. Subgroup analyses further distinguished ACE inhibitor and ARB use to explore potential class-specific associations.

### Outcome

The primary outcome was time to in-hospital mortality, measured from ICU admission until death or hospital discharge. Patients discharged alive were censored at discharge.

### Covariate Selection

Covariates were selected a priori based on a conceptual causal framework to address confounding. These included demographics, cardiovascular comorbidities, chronic kidney disease, diabetes, and SOFA score at ICU admission. Additional sensitivity models incorporated ICU type and extended clinical variables.

### Statistical Analysis

Survival analyses were performed using Kaplan-Meier curves and Cox proportional hazards regression. Multivariable models adjusted for pre-specified covariates to estimate adjusted hazard ratios and 95% confidence intervals. Proportional hazards assumptions were evaluated using Schoenfeld residuals.

Sensitivity analyses assessed model robustness by incorporating extended covariates and ICU type stratification. Penalized Cox models were explored to evaluate potential collinearity and overfitting.

### Reproducibility

Data extraction and transformation steps were implemented using version-controlled SQL scripts. Statistical modeling was conducted in structured Jupyter notebooks using Python. A SAS workflow is included to reproduce key statistical models and verify cross-platform consistency of selected results.

---

## Key Findings

The results summarized below highlight the primary directional findings; detailed estimates and diagnostic outputs are provided in the accompanying notebooks.

- Pre-ICU RAAS inhibitor exposure was associated with lower observed in-hospital mortality compared with no RAAS inhibitor exposure.
- This association was observed in Kaplan-Meier survival curves and remained directionally consistent after adjustment for demographic factors, illness severity, and major comorbidities in Cox proportional hazards models.
- ACE inhibitor use demonstrated a more pronounced association with lower observed in-hospital mortality compared with ARB use, although confidence intervals overlapped and causal inference cannot be established.
- Sensitivity analyses incorporating additional covariates, including ICU type, attenuated the association but did not change its overall direction.

These findings are best interpreted as an observational association and a hypothesis-generating signal. See [docs/DISCUSSION_AND_LIMITATIONS.md](docs/DISCUSSION_AND_LIMITATIONS.md) for extended interpretation, comparison with prior studies, and limitations.

---

## Reproducibility / Validation

### Environment

`requirements.txt` provides a minimal, portable environment specification for running the validation script and analysis notebooks.

Install the minimal environment:
```text
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Environment setup steps are intentionally not included as a tracked notebook. Local configuration, including Python environment creation, Google Cloud authentication, MIMIC-IV/PhysioNet BigQuery access, and application default credentials, must be configured separately before running the workflow.

### SAS-Python validation

This project separates model fitting in the 04-series notebooks from validation in the 05 notebook. SAS-Python validation is reproducibility validation of selected statistical outputs, not a new clinical analysis.

For SAS/Python logistic validation:

1. Run `notebooks/04d_python_logistic_model.ipynb` to generate `python/outputs/python_logistic_parameters.csv`.
2. Run `notebooks/05_sas_python_validation.ipynb` to compare the SAS and Python parameter outputs.

SAS programs use SAS OnDemand-style paths and may require local path adjustment before execution. Generated CSV outputs under `python/outputs/` are ignored by Git and can be reproduced from the notebooks.

### Validation checklist

`scripts/validation_checklist.py` performs a lightweight sanity check by enumerating candidate tables in the BigQuery dataset used for this COPD ICU RAAS analysis. It uses `INFORMATION_SCHEMA` and checks table existence only.

Run the checklist:
```text
python scripts/validation_checklist.py
```

Authenticate first with Application Default Credentials:
```text
gcloud auth application-default login
```

Important scope note:

- This script only checks table existence.
- It does not perform data quality validation.
- It does not validate table contents.

---

## Project Structure

```text
mimic-iv-copd-raas-analysis/
├── notebooks/        # 01-05 analysis notebooks
├── sql/              # BigQuery cohort, exposure, baseline, and outcome SQL
├── docs/
│   ├── STUDY_BACKGROUND.md
│   ├── DISCUSSION_AND_LIMITATIONS.md
│   ├── *_SHORT.md
│   └── PACE.md
├── scripts/          # validation_checklist.py
├── sas/              # SAS validation README and programs
├── data/             # local ignored data directories
└── README.md
```

---

## Data Source and Compliance

This project uses data from the Medical Information Mart for Intensive Care IV (MIMIC-IV) database (version 3.1), which is maintained by the MIT Laboratory for Computational Physiology and made available via PhysioNet.

According to the PhysioNet data use requirements, the following citation should be used when referencing MIMIC-IV:
Johnson A., Bulgarelli L., Pollard T., Gow B., Moody B., Horng S., Celi L.A., & Mark R. (2024). *MIMIC-IV (version 3.1)*. PhysioNet. RRID:SCR_007345. https://doi.org/10.13026/kpb9-mt58.

Access to the MIMIC-IV database was granted following completion of the required training and approval under the PhysioNet data use agreement. This repository contains no patient-level data. All analyses were conducted within approved MIMIC-IV environments, and only code and aggregate descriptions are shared.
