# Validation Notes

The current portfolio covers BigQuery source extraction, cohort construction, Python modeling, independent Cox calculations, aggregate figures and Quarto reporting. [The reproducible scope](REPRODUCIBLE_SCOPE.md) defines the complete workflow and evidence.

## Source extraction and cohort definitions

`scripts/revalidate_age_time.py` extracts the SELECT bodies from version-controlled cohort, exposure, baseline and outcome SQL into a read-only source query. It does not execute CREATE/REPLACE statements. Adult selection is deferred for the age-boundary audit.

```bash
# Source-query compilation and dry-run estimate; no source query is executed.
.venv/bin/python scripts/revalidate_age_time.py

# Actual BigQuery SQL on artificial edge cases; reads zero source-table bytes.
.venv/bin/python scripts/revalidate_age_time.py --synthetic --execute

# Source extraction and model comparison; choose a new aggregate output path.
.venv/bin/python scripts/revalidate_age_time.py --execute --output /tmp/icu_copd_source_revalidation_new.json
```

The source-query billed-byte limit defaults to 2 GB and is checked by a dry run. Model rows stay in memory; only aggregate results and query/SQL provenance are written. This audit compares legacy, time-only, age-only and fully corrected definitions. Existing admission-level design, discharge censoring and lack of patient clustering are retained. See [the source validation report](AGE_TIME_REVALIDATION.md).

Table content and lineage QA are recorded in `AGE_TIME_TABLE_QUALITY.json` and `LOS_TABLE_QUALITY.json`. `scripts/validation_checklist.py` checks table existence only.

## Current models, figures and report

```bash
.venv/bin/python -m unittest discover -s scripts -p test_current_analysis.py
.venv/bin/python scripts/current_analysis.py
.venv/bin/python scripts/build_report.py
```

The model refresh reads explicit columns from corrected BigQuery tables after a capped dry run (200 MB per query). It generates `CURRENT_ANALYSIS.json`, four statistical figures and their `docs/assets/` copies, and optional secondary Python logistic coefficients with aggregate provenance. Notebooks 04a–04c call the shared workflow; 04d is an optional Python parameter export. Saved notebook outputs remain stripped.

`build_report.py` reads saved aggregate JSON and figures and renders the Quarto source and HTML without executing notebook or model code. This report-only step needs no clinical data transfer or BigQuery connection. It does not independently reproduce extraction or modeling.

## Independent Cox calculation

```bash
.venv/bin/python scripts/independent_cox_crosscheck.py --repo . --output /tmp/icu_copd_crosscheck_new.json
```

The script independently fits six unpenalized Cox specifications (40 coefficients) with statsmodels PHReg. It checks cohort aggregates, complete cases, strata, parameter keys, convergence, coefficients, HRs, confidence-interval endpoints and p-values against the saved lifelines reference with an absolute tolerance of `1e-4`. A dry run and 200 MB billed-byte cap precede data retrieval. No tables are created and no individual rows are saved or uploaded.

See [the numerical record](INDEPENDENT_COX_CROSSCHECK.json) and [the scope and limitations](INDEPENDENT_REVALIDATION.md). The report only presents successful independent agreement when the recorded reference hash matches the exact current aggregate analysis JSON. After a model refresh, review a new successful comparison before replacing the published aggregate record.

This checks an independent statistical implementation on shared corrected inputs. It does not independently re-extract source records or validate penalized models, PH tests, patient clustering, competing risks or causal interpretation.

## Interpretation limits checked separately

Successful numerical comparison does not validate covariate timing. SOFA-containing core/ICU models can use information through 24 hours after ICU follow-up begins and remain exploratory sensitivity analyses. Subclass estimates each use neither qualifying prescription order as reference; no direct ACEi-versus-ARB contrast is reported in the main analysis. [Timing limitations and separate reanalysis options](ANALYSIS_TIMING_LIMITATIONS.md).

The [2026-11-18 documentation audit](GITHUB_AUDIT_20261118.md) records these offline corrections and the checks that did not require source-data access.
