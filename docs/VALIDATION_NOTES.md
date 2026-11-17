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

## Admission-age and follow-up correction validation

`scripts/revalidate_age_time.py` extracts the SELECT bodies from the version-controlled cohort, exposure, baseline, outcome, and extended SQL into a single read-only query. It does not execute their CREATE/REPLACE statements. Adult selection is deferred in this audit query so both age definitions can be compared from the population before filtering.

```bash
# Compile the source query and inspect its dry-run estimate (default).
.venv/bin/python scripts/revalidate_age_time.py

# Test the actual SQL and outcome QA on 12 artificial edge cases; reads 0 source bytes.
.venv/bin/python scripts/revalidate_age_time.py --synthetic --execute

# Explicitly execute the source SELECT and fit comparison models in memory.
# Choose a new aggregate output path; the script refuses to overwrite an existing file.
.venv/bin/python scripts/revalidate_age_time.py --execute --output docs/AGE_TIME_REVALIDATION.json
```

The per-query billed-byte limit defaults to 2 GB. The script first performs a dry run and stops if that estimate exceeds the limit. It projects no patient identifiers or individual dates into the model inputs, retains model rows only in memory, and writes only aggregate counts, estimates, PH diagnostics, fixed-day Kaplan-Meier estimates, and query/SQL provenance.

The comparisons are legacy definitions, time correction only, age correction only, and both corrections. Refined 04a, monotherapy/neither 04b, and all four core/ICU 04c specifications use the notebook covariates, era strata, penalties, and complete-case rules. Rank-transformed Schoenfeld tests are reported per covariate. A supplemental corrected 04a model excludes the anchor-age topcoded group. These analyses retain the existing admission-level design and do not add patient clustering or competing risks.

This comparison validates source SQL and model effects without requiring saved analysis tables. It does not refresh notebook outputs, local SAS exports, curated figures, or the rendered report. See [the correction report](AGE_TIME_REVALIDATION.md) for results and scope.

## Current figure/report refresh and independent SAS guard

```bash
.venv/bin/python -m unittest discover -s scripts -p test_current_analysis.py
.venv/bin/python scripts/current_analysis.py
.venv/bin/python scripts/build_report.py
```

The shared refresh reads only explicit model columns from corrected BigQuery tables (200 MB job cap after dry run), creates CURRENT_ANALYSIS.json, regenerates all four statistical figures and their docs/assets copies, refreshes the Quarto source and RESULTS_SUMMARY.md, and writes current aggregate Python logistic coefficients plus their manifest. Notebooks 04a/b/c call that same workflow; 04d uses the same current-data loader and logistic function. Notebook outputs remain stripped.

Notebook 05 requires matching analysis version, model specification, sample/event counts, age/duration sums and exact unique parameter keys. Missing or historical SAS provenance stops comparison instead of silently joining a subset of old parameters. A relative difference against a zero SAS coefficient is undefined. SAS 07 exports independent primary 04a and extended-core 04c results with the correct era strata. SAS 01 omits patient previews. The versioned private input query is sql/06_export_sas_validation.sql; no private SAS input export or SAS execution was performed here because a local SAS runtime is unavailable.

Independent cross-platform validation is pending. Historical SAS PDFs/CSVs are retained locally but are not current validation evidence. Fresh SAS input and an independent SAS rerun are required before notebook 05 can pass.
