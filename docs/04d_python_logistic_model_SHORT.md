# 04d - Secondary Python Logistic Validation Model (SHORT)

## Purpose
Fit the secondary logistic regression model in Python using `statsmodels` only to generate parameter estimates for SAS-Python reproducibility validation.

## Input Dataset
- `sas/inputs/copd_raas__cohort_copd_outcomes_extended.csv`

## Output Dataset
- `python/outputs/python_logistic_parameters.csv`

## Downstream Usage
The exported Python parameter file is used by `05_sas_python_validation.ipynb`.

## Key Point
- The generated CSV is ignored by Git and reproduced locally.
- This notebook fits the secondary Python logistic validation model used for comparison against SAS output.

## Next Step
Next: [05 - SAS-Python Validation](05_sas_python_validation_SHORT.md)
