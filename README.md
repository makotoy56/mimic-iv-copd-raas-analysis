# RAAS Blockers and Clinical Outcomes in COPD ICU Admissions
*An ICU Hospital Cohort Study of COPD Patients Using MIMIC-IV*

Maintained by <br>
Makoto Yoshida, PhD <br>
Clinical Data Analytics Portfolio <br>
LinkedIn: https://www.linkedin.com/in/makoto-yoshida/ <br>

## Project Overview

This project is a reproducible EHR-based observational cohort study using MIMIC-IV. It evaluates whether pre-ICU RAAS inhibitor exposure is associated with in-hospital mortality among ICU patients with COPD.

The portfolio emphasis is the end-to-end clinical analytics workflow: cohort construction, exposure and outcome definition, survival modeling, sensitivity analysis, and reproducibility validation.

## What this project demonstrates

- EHR-based observational cohort construction using BigQuery SQL
- Clinically informed exposure, outcome, and covariate definitions
- Kaplan-Meier and Cox proportional hazards survival analysis
- ACE inhibitor vs ARB subgroup comparison
- Sensitivity analyses with extended covariates
- Python and SAS reproducibility validation of key model outputs

## Skills Demonstrated

- EHR cohort construction using BigQuery SQL
- Clinical exposure and outcome definition
- Survival analysis with Kaplan-Meier and Cox regression
- Subgroup and sensitivity analysis
- Cross-platform reproducibility validation using Python and SAS
- Observational study interpretation with cautious causal language
- Reproducible clinical analytics workflow design

## Clinical Data Analysis Workflow

```text
01_icu_cohort.ipynb                         ICU cohort extraction
02_cohort_and_exposures.ipynb               COPD cohort + RAAS exposure definition
03a_baseline.ipynb                          Baseline covariates
03b_merge_exposures.ipynb                   Detailed exposure merge
04a_outcomes_and_modeling.ipynb             Primary survival analysis
04b_outcomes_and_modeling_raas_subgroups.ipynb  ACEi vs ARB subgroup analysis
04c_extended_covariate_cox_model.ipynb      Extended covariate Cox models
04d_python_logistic_model.ipynb             Python logistic validation model
05_sas_python_validation.ipynb              SAS-Python reproducibility validation
```

## Technical Snapshot

- **Data**: MIMIC-IV v3.1 (PhysioNet), ICU admissions
- **Design**: EHR-based retrospective observational cohort study
- **Population**: Adult ICU patients with COPD
- **Exposure**: Pre-ICU RAAS inhibitor use (ACE inhibitors [ACEi] / ARBs) based on inpatient prescription orders before ICU admission; not outpatient medication history
- **Outcome**: Time-to-in-hospital mortality
- **Methods**: Kaplan-Meier survival analysis, Cox proportional hazards regression, subgroup and sensitivity analyses
- **Tools**: BigQuery SQL, Python, Jupyter, SAS
- **Key finding**: RAAS inhibitor exposure was associated with lower observed mortality, with a stronger observed signal for ACE inhibitors than ARBs.
- **Interpretation**: Hypothesis-generating observational association; cannot establish causality.

## Start Here

- **Cohort setup**: [01_icu_cohort.ipynb](notebooks/01_icu_cohort.ipynb), [02_cohort_and_exposures.ipynb](notebooks/02_cohort_and_exposures.ipynb)
- **Baseline/exposure build**: [03a_baseline.ipynb](notebooks/03a_baseline.ipynb), [03b_merge_exposures.ipynb](notebooks/03b_merge_exposures.ipynb)
- **Modeling**: [04a_outcomes_and_modeling.ipynb](notebooks/04a_outcomes_and_modeling.ipynb), [04b RAAS subgroups](notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb), [04c extended Cox](notebooks/04c_extended_covariate_cox_model.ipynb)
- **Validation**: [04d Python logistic model](notebooks/04d_python_logistic_model.ipynb), [05 SAS-Python validation](notebooks/05_sas_python_validation.ipynb)
- **Context**: [Study background](docs/STUDY_BACKGROUND.md), [Discussion and limitations](docs/DISCUSSION_AND_LIMITATIONS.md), [PACE](docs/PACE.md)
- **Pipelines and docs**: [sql/](sql/), [docs/](docs/)

## Background and Rationale

COPD is frequently complicated by cardiovascular comorbidity, and ICU-admitted COPD patients represent a high-risk population. This project evaluates RAAS inhibitor exposure in that setting while keeping interpretation explicitly observational.

The rationale is grounded in RAAS biology, prior COPD literature, and the possibility of different ACE inhibitor and ARB associations. Details are in [docs/STUDY_BACKGROUND.md](docs/STUDY_BACKGROUND.md).

## Methods Overview

This study used a pre-specified analytic plan grounded in a causal inference framework.

### Study Design and Data Source
We performed a retrospective observational cohort study using MIMIC-IV v3.1, a de-identified ICU electronic health record database. All analyses were conducted within approved data use environments.

### Cohort Construction
Adult ICU patients with COPD were identified using established ICD-9 and ICD-10 diagnosis codes. The cohort was constructed at the ICU-stay/admission level using reproducible BigQuery SQL.

### Exposure Definition
The primary exposure was pre-ICU RAAS inhibitor use, defined from inpatient prescription orders for ACE inhibitors or ARBs before or at ICU admission. This does not directly capture outpatient chronic use.

### Outcome
The primary outcome was time to in-hospital mortality, measured from ICU admission until death or hospital discharge. Patients discharged alive were censored at discharge.

### Covariate Selection
Covariates were selected a priori based on a conceptual causal framework and included demographics, cardiovascular comorbidities, chronic kidney disease, diabetes, and SOFA score. Sensitivity models added ICU type and extended clinical variables.

### Statistical Analysis
Survival analyses used Kaplan-Meier curves and Cox proportional hazards regression with pre-specified covariate adjustment. Proportional hazards assumptions were evaluated using Schoenfeld residuals; sensitivity analyses assessed extended covariates, ICU type, and penalized Cox models.

### Reproducibility
Data extraction used version-controlled SQL scripts. Modeling was conducted in Jupyter notebooks, with SAS used to verify cross-platform consistency of selected model outputs.

## Key Findings

- Pre-ICU RAAS inhibitor exposure was associated with lower observed mortality in time-to-event analyses.
- ACE inhibitor exposure showed a stronger observed signal than ARB exposure, with overlapping uncertainty.
- Extended adjustment, including ICU type, attenuated the association but preserved the overall direction.

These findings are hypothesis-generating and cannot establish causality. See [docs/DISCUSSION_AND_LIMITATIONS.md](docs/DISCUSSION_AND_LIMITATIONS.md) for interpretation and limitations.

## Reproducibility / Validation

### Environment

`requirements.txt` provides a minimal environment for the validation script and analysis notebooks.

Install the minimal environment:
```text
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Local Python setup, Google Cloud authentication, MIMIC-IV/PhysioNet BigQuery access, and application default credentials must be configured separately before running the workflow.

### SAS-Python validation
Model fitting occurs in the 04-series notebooks; the 05 notebook performs SAS-Python reproducibility validation of selected statistical outputs, not a new clinical analysis.

For SAS/Python logistic validation:

1. Run `notebooks/04d_python_logistic_model.ipynb` to generate `python/outputs/python_logistic_parameters.csv`.
2. Run `notebooks/05_sas_python_validation.ipynb` to compare the SAS and Python parameter outputs.

SAS programs use SAS OnDemand-style paths and may require local path adjustment. Generated CSV outputs under `python/outputs/` are ignored by Git and can be reproduced.

### Validation checklist
`scripts/validation_checklist.py` performs a lightweight table-existence check using BigQuery `INFORMATION_SCHEMA`.

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

## Data Source and Compliance

This project uses MIMIC-IV v3.1, maintained by the MIT Laboratory for Computational Physiology and made available via PhysioNet.

According to the PhysioNet data use requirements, the following citation should be used when referencing MIMIC-IV:
Johnson A., Bulgarelli L., Pollard T., Gow B., Moody B., Horng S., Celi L.A., & Mark R. (2024). *MIMIC-IV (version 3.1)*. PhysioNet. RRID:SCR_007345. https://doi.org/10.13026/kpb9-mt58.

Access was granted after required training and approval under the PhysioNet data use agreement. This repository contains no patient-level data; only code and aggregate descriptions are shared.
