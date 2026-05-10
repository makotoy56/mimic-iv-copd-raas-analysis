# Validation Notes

This document summarizes reproducibility and validation scope for the repository.

## Primary Analysis Versus Validation

The primary clinical analysis is Cox proportional hazards survival modeling in the 04-series notebooks.

The `04d_python_logistic_model.ipynb` notebook is a secondary Python logistic validation model. It exists to generate parameter estimates for comparison with SAS output and should not be interpreted as the primary clinical analysis.

The `05_sas_python_validation.ipynb` notebook compares precomputed SAS and Python secondary logistic validation outputs. It does not refit the primary Cox models and is not a new clinical analysis.

## SAS Workflow

SAS programs are stored in `sas/programs/`:

- `01_import_cohort.sas`
- `02_baseline_characteristics.sas`
- `03_univariate_analysis.sas`
- `04_cox_regression.sas`
- `05_cox_diagnostics.sas`
- `06_sensitivity_analysis.sas`
- `07_export_validation_tables.sas`

SAS OnDemand-style paths may require local adjustment before execution.

## Python Validation Output

`04d_python_logistic_model.ipynb` generates `python/outputs/python_logistic_parameters.csv`. Generated Python CSV outputs are ignored by Git and can be reproduced locally.

## BigQuery Checklist

`scripts/validation_checklist.py` performs lightweight BigQuery `INFORMATION_SCHEMA` table-existence checks. It does not perform data quality validation and does not validate table contents.

Run after configuring Google Cloud Application Default Credentials:

```text
gcloud auth application-default login
python scripts/validation_checklist.py
```
