# 04d - Python Logistic Model (SHORT)

## Purpose
Fit a logistic regression model in Python using `statsmodels` to generate parameter estimates for SAS-Python reproducibility validation.

## Input Dataset
- `sas/inputs/copd_raas__cohort_copd_outcomes_extended.csv`

## Output Dataset
- `python/outputs/python_logistic_parameters.csv`

## Downstream Usage
The exported Python parameter file is used by `05_sas_python_validation.ipynb`.

## Key Point
- The generated CSV is ignored by Git and reproduced locally.
- This notebook fits the Python logistic model used for validation against SAS output.
