# Reproducibility and Analytical Environment

## Project Purpose

This project is a retrospective observational MIMIC-IV clinical analytics workflow evaluating whether pre-ICU renin-angiotensin-aldosterone system (RAAS) inhibitor exposure is associated with time-to-in-hospital mortality among adult ICU patients with chronic obstructive pulmonary disease (COPD).

The primary analytical purpose is to demonstrate reproducible cohort construction, exposure definition, time-to-event modeling, sensitivity analysis, SAS/Python validation, and clinical reporting for an ICU real-world evidence question. The findings are hypothesis-generating associations and are not causal treatment-effect estimates.

## Data Source

The analysis uses MIMIC-IV v3.1, a de-identified electronic health record database distributed through PhysioNet and accessed through BigQuery.

Patient-level MIMIC-IV source tables, derived patient-level cohorts, credentials, and local BigQuery configuration are not included in this repository. Reproduction requires independent PhysioNet/MIMIC approval, Google Cloud authentication, and BigQuery access.

## Analytical Workflow

The workflow is organized as a stepwise clinical analysis pipeline:

1. **Cohort construction**: BigQuery SQL scripts under `sql/` define the ICU COPD cohort from MIMIC-IV source tables.
   - `sql/01_extract_base.sql`
   - `sql/02_build_cohort_copd.sql`
2. **Exposure definition**: RAAS inhibitor exposure is defined from inpatient prescription orders before or at ICU admission.
   - `sql/02_exposure_raas.sql`
   - `sql/02_exposure_raas_detailed.sql`
   - `notebooks/02_cohort_and_exposures.ipynb`
3. **Baseline covariates and merge step**: baseline variables and exposure indicators are prepared and merged for analysis.
   - `sql/03_build_baseline.sql`
   - `sql/03_merge_exposures.sql`
   - `notebooks/03a_baseline.ipynb`
   - `notebooks/03b_merge_exposures.ipynb`
4. **Outcome construction**: time-to-in-hospital mortality is built from ICU admission through death or discharge.
   - `sql/04_build_outcomes.sql`
   - `sql/04_build_outcomes_extended.sql`
5. **Primary statistical analysis**: Kaplan-Meier survival curves and Cox proportional hazards models are run in Python.
   - `notebooks/04a_outcomes_and_modeling.ipynb`
6. **Subgroup analysis**: ACE inhibitor and ARB monotherapy exposure groups are evaluated descriptively.
   - `notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb`
7. **Sensitivity analysis**: extended covariate, ICU-type, and penalized Cox specifications are evaluated.
   - `notebooks/04c_extended_covariate_cox_model.ipynb`
8. **Validation**: a secondary logistic model is used only to support SAS/Python reproducibility comparison; Cox survival modeling remains the primary clinical analysis.
   - `notebooks/04d_python_logistic_model.ipynb`
   - `notebooks/05_sas_python_validation.ipynb`
   - `sas/programs/01_import_cohort.sas`
   - `sas/programs/02_baseline_characteristics.sas`
   - `sas/programs/03_univariate_analysis.sas`
   - `sas/programs/04_cox_regression.sas`
   - `sas/programs/05_cox_diagnostics.sas`
   - `sas/programs/06_sensitivity_analysis.sas`
   - `sas/programs/07_export_validation_tables.sas`
9. **Reporting**: the narrative clinical report is authored in Quarto and rendered to `docs/`.
   - `reports/copd_raas_survival_report.qmd`
   - `reports/_quarto.yml`
   - `docs/copd_raas_survival_report.html`

## Environment Summary

- **Python environment**: Analyses were developed and executed in a local Python virtual environment. The project now targets Python 3.12 through `pyproject.toml` and `.python-version`. Project dependencies are documented in `pyproject.toml` and locked in `uv.lock`; they include pandas, NumPy, statsmodels, lifelines, matplotlib, and Google BigQuery client libraries.
- **SAS environment**: SAS® OnDemand for Academics was used for SAS validation workflows. The exact SAS maintenance release was not pinned in the repository.
- **Quarto version**: 1.9.38 detected locally with `quarto --version`. The report source and render configuration are stored under `reports/`.
- **Version control**: Git/GitHub are used for code, documentation, SQL definitions, notebooks, SAS programs, curated figures, and rendered portfolio materials.

## Notebook Output Policy

Jupyter notebooks may be rerun locally during development, but notebook outputs, execution counts, generated cell IDs, and volatile notebook metadata are stripped before commit.

The repository uses `nbstripout` as a uv development dependency and a Git clean filter for `*.ipynb` files. After cloning or recreating the environment, install the local Git filter from the repository root:

```bash
uv sync
uv run nbstripout --install --attributes .gitattributes
git config filter.nbstripout.extrakeys 'metadata.kernelspec metadata.language_info.version cell.metadata.execution cell.metadata.vscode cell.metadata.notebookRunGroups'
uv run nbstripout --status
```

To verify notebooks are clean before committing:

```bash
uv run nbstripout --verify notebooks/*.ipynb
```

## Major Analytical Libraries

The project dependency file and scripts indicate use of:

- pandas
- NumPy
- matplotlib
- lifelines
- statsmodels
- pyarrow
- google-cloud-bigquery
- pandas-gbq
- db-dtypes
- Jupyter

## AI-Assisted Development

This project was developed using an AI-assisted workflow that included ChatGPT and Codex. These tools were used for implementation support, debugging assistance, code review, documentation refinement, and workflow iteration. Final analytical decisions, statistical interpretation, quality control, and reporting remained under investigator review.

## Complete Dependency Specification

The project includes `pyproject.toml` and `uv.lock`. Exact version pins from the previous `requirements.txt` were preserved verbatim; previously unpinned packages remain unpinned in `pyproject.toml` and are resolved reproducibly in `uv.lock`.

```toml
dependencies = [
    "db-dtypes==1.5.1",
    "google-cloud-bigquery==3.41.0",
    "jupyter",
    "lifelines",
    "matplotlib==3.10.9",
    "numpy==2.2.6",
    "pandas==2.3.3",
    "pandas-gbq",
    "pyarrow==24.0.0",
    "statsmodels",
]
```

No `requirements.txt` or `environment.yml` file is required for the current uv-managed environment.

## Reproduction Steps

1. Obtain independent MIMIC-IV/PhysioNet approval and configure Google Cloud/BigQuery access for MIMIC-IV v3.1.
2. Install Python 3.12 and project dependencies with uv:

   ```bash
   uv sync --locked
   ```

3. Activate the uv-managed virtual environment:

   ```bash
   source .venv/bin/activate
   ```

4. Run the notebooks in workflow order:
   - `notebooks/00_setup.ipynb`
   - `notebooks/01_icu_cohort.ipynb`
   - `notebooks/02_cohort_and_exposures.ipynb`
   - `notebooks/03a_baseline.ipynb`
   - `notebooks/03b_merge_exposures.ipynb`
   - `notebooks/04a_outcomes_and_modeling.ipynb`
   - `notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb`
   - `notebooks/04c_extended_covariate_cox_model.ipynb`
   - `notebooks/04d_python_logistic_model.ipynb`
   - `notebooks/05_sas_python_validation.ipynb`
5. If SAS validation is being reproduced, run the SAS programs in SAS® OnDemand for Academics or another compatible SAS environment, updating library paths as needed.
6. Render the Quarto report from the `reports/` directory:

   ```bash
   quarto render copd_raas_survival_report.qmd
   ```

7. Review the rendered report at `docs/copd_raas_survival_report.html`.
