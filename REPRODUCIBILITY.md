# Reproducibility and Analytical Environment

## Project Purpose

This project is a retrospective observational MIMIC-IV clinical analytics workflow evaluating whether pre-ICU renin-angiotensin-aldosterone system (RAAS) inhibitor exposure is associated with time-to-in-hospital mortality among adult ICU patients with chronic obstructive pulmonary disease (COPD).

The primary analytical purpose is to demonstrate reproducible cohort construction, exposure definition, time-to-event modeling, sensitivity analysis, independent Cox calculations, and clinical reporting for an ICU real-world evidence question. The findings are hypothesis-generating associations and are not causal treatment-effect estimates.

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
3. **Cohort descriptors and merge step**: demographic fields and prescription-order indicators are prepared and merged. The later first-day SOFA score is not assumed to be known at ICU entry.
   - `sql/03_build_baseline.sql`
   - `sql/03_merge_exposures.sql`
   - `notebooks/03a_baseline.ipynb`
   - `notebooks/03b_merge_exposures.ipynb`
4. **Outcome construction**: for in-hospital deaths, follow-up runs from ICU admission to `admissions.deathtime`, with `admissions.dischtime` used as a flagged fallback only when death time is unavailable. For live discharges, follow-up runs from ICU admission to discharge and is censored at discharge. This is the original cause-specific main analysis; supplementary cumulative-incidence analyses treat live discharge as a competing event.
   - `sql/04_build_outcomes.sql`
   - `sql/04_build_outcomes_extended.sql`
5. **Primary statistical analysis**: Kaplan-Meier survival curves and Cox proportional hazards models are run in Python.
   - `notebooks/04a_outcomes_and_modeling.ipynb`
6. **Subclass analysis**: ACEi-only and ARB-only prescription-order groups are each compared with neither; no direct between-class contrast is reported in the main analysis.
   - `notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb`
7. **Exploratory sensitivity analysis**: extended covariate, ICU-type, penalized and CHF/SOFA-stratified Cox specifications can include first-day information through 24 hours after ICU entry; they are not baseline-only severity adjustment.
   - `notebooks/04c_extended_covariate_cox_model.ipynb`
8. **Independent calculation**: statsmodels PHReg independently fits six unpenalized Cox specifications and compares 40 coefficients, HRs, confidence intervals and p-values with the current lifelines reference.
   - `scripts/independent_cox_crosscheck.py`
   - `docs/INDEPENDENT_COX_CROSSCHECK.json`
   - `docs/INDEPENDENT_REVALIDATION.md`
   - `notebooks/04d_python_logistic_model.ipynb` is an optional secondary Python parameter export, not the primary clinical model or evidence of independent clinical validation.
9. **Reporting**: the narrative clinical report is authored in Quarto and rendered to `docs/`.
   - `reports/copd_raas_survival_report.qmd`
   - `reports/_quarto.yml`
   - `docs/copd_raas_survival_report.html`

## Environment Summary

- **Python environment**: Analyses were developed and executed in a local Python virtual environment. The project now targets Python 3.12 through `pyproject.toml` and `.python-version`. Project dependencies are documented in `pyproject.toml` and locked in `uv.lock`; they include pandas, NumPy, statsmodels, lifelines, matplotlib, and Google BigQuery client libraries.
- **Quarto version**: 1.9.38 detected locally with `quarto --version`. The report source and render configuration are stored under `reports/`.
- **Version control**: Git/GitHub are used for code, documentation, SQL definitions, notebooks, Python validation scripts, curated figures, and rendered portfolio materials.

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

4. Initialize a BigQuery client with your existing Application Default Credentials before running the SQL-building notebook cells:

   ```python
   from google.cloud import bigquery
   client = bigquery.Client(project="mimic-iv-portfolio")
   ```

   The SQL currently targets `mimic-iv-portfolio.copd_raas` in US. A reproducer using a different authorized project must update the project/dataset references in the SQL and Python loaders. No private setup notebook or key file is required. Run the notebooks in workflow order:
   - `notebooks/01_icu_cohort.ipynb`
   - `notebooks/02_cohort_and_exposures.ipynb`
   - `notebooks/03a_baseline.ipynb`
   - `notebooks/03b_merge_exposures.ipynb`

   **Before 04a, run the following entire BigQuery scripts in US, in this order, and wait for each to finish:**

   1. `sql/04_build_outcomes.sql`: reads `cohort_copd_baseline` and source `admissions`, runs endpoint/follow-up QA, then writes `cohort_copd_outcomes`.
   2. `sql/04_build_outcomes_extended.sql`: reads `cohort_copd_outcomes`, joins `first_day_sofa`, `charlson` and ICU type, then writes `cohort_copd_outcomes_extended`.

   `03_merge_exposures.sql` writes `cohort_copd_with_raas`; that table does not replace either outcome table. The shared loader used by 04a–04d reads `cohort_copd_outcomes_extended` and joins `cohort_copd_raas_detailed`, so even the age/sex-only primary model requires the extended table to exist. The notebooks do not create either outcome table. See [the dependency map](docs/METHODS_OVERVIEW.md#outcome-table-dependencies).

   Then continue with:

   - `notebooks/04a_outcomes_and_modeling.ipynb`
   - `notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb`
   - `notebooks/04c_extended_covariate_cox_model.ipynb`
   - `notebooks/04d_python_logistic_model.ipynb`
5. Refresh the current models and figures from the corrected BigQuery tables:

   ```bash
   .venv/bin/python scripts/current_analysis.py
   ```

6. Independently refit the six unpenalized Cox specifications using a new aggregate output path. The script checks the dry-run estimate, caps billed bytes at 200 MB, and refuses to overwrite an existing result:

   ```bash
   .venv/bin/python scripts/independent_cox_crosscheck.py --repo . --output /tmp/icu_copd_crosscheck_new.json
   ```

   Review the result before replacing `docs/INDEPENDENT_COX_CROSSCHECK.json` with a newly generated aggregate record. The renderer displays a successful independent comparison only when the recorded analysis-reference hash matches `docs/CURRENT_ANALYSIS.json`.

7. Rebuild and review `docs/copd_raas_survival_report.html`:

   ```bash
   .venv/bin/python scripts/build_report.py
   ```

   This report-only step reads the saved aggregate JSON and figures. It does not query BigQuery, transfer clinical data, or rerun the models.

   The GitHub Pages root uses the static landing page `docs/index.html`, which links to the report. Supporting Markdown documents in the generated report link to their rendered GitHub pages, preserving heading anchors. The PH diagnostic summary lists rank tests with p<0.05 and model warnings; complete covariate-level rank PH p-values are in each model's `ph_rank_p` field in `docs/CURRENT_ANALYSIS.json`.

See [the reproducible scope and evidence](docs/REPRODUCIBLE_SCOPE.md) for what each step establishes and the remaining scientific limitations.

## Additional survival sensitivity notebooks

The 05a–05c companions use `scripts/survival_sensitivity.py` and do not call `refresh()` or overwrite main-analysis results. Default notebook runs are wholly synthetic. Use the [supplement guide](docs/SURVIVAL_SENSITIVITY_SUPPLEMENTS.md) for patient-cluster inference, competing-risk cumulative incidence, and the separate 24-hour landmark design. It includes the explicit authorized local-data command and no-query review of a saved aggregate run.

Pseudonymous patient/admission/stay keys are requested only by the supplementary loader option, after the same US dry run and 200 MB cap, and stay in memory. Run output is aggregate-only under ignored `reports/local_supplements/`. Tracked notebooks keep stripped outputs; execute and retain clinical notebook copies only inside that ignored directory. R `survival` is an optional independent synthetic checker; normal analysis remains Python. New clinical estimates are not automatically promoted into README or Quarto.

The Quarto supplementary section and the short README summary are generated from `docs/SURVIVAL_SENSITIVITY_RESULTS.json`, validated against `docs/SURVIVAL_SUPPLEMENTS_VALIDATION.json`. The selected public record contains aggregate counts, RAAS estimates and a fixed daily CIF grid; full local results and covariance matrices remain ignored. `scripts/report_survival_supplement.py` prepares this record from an explicitly supplied, hash-verified local aggregate run. Normal report builds require only the public aggregate records and tracked figures. See the [publication/rebuild procedure](docs/SURVIVAL_SENSITIVITY_SUPPLEMENTS.md#prepare-and-rebuild-the-public-supplementary-section).

Notebook SHORT guides are generated by `scripts/render_short_notes.py` from the same public main and selected supplement records. `scripts/build_report.py` refreshes all 11 guides as part of the report-only build. Regenerate the guides directly with `.venv/bin/python scripts/render_short_notes.py`; this performs no data retrieval or analysis execution.
