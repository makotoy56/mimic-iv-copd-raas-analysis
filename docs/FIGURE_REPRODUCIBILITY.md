# Figure Reproducibility

Current result figures are written to stable paths under `assets/` and copied to `docs/assets/` by `scripts/current_analysis.py`. Notebooks 04a/b/c call the same shared computation and export workflow. It also updates aggregate JSON and the Quarto source, preventing manual coefficient drift. Run `.venv/bin/python scripts/build_report.py` after the refresh to regenerate HTML.

## Notebook-Generated Result Figures

| Figure | Primary use | Exporting notebook | Output path |
| --- | --- | --- | --- |
| Kaplan-Meier survival curve | README and Quarto report | `notebooks/04a_outcomes_and_modeling.ipynb` | `assets/kaplan_meier_curve.png` |
| Extended core Cox model forest plot | README and Quarto report | `notebooks/04c_extended_covariate_cox_model.ipynb` | `assets/cox_forest_plot.png` |
| ACEi-only and ARB-only orders, each versus neither | Quarto report | `notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb` | `assets/raas_subgroup_forest_plot.svg` |
| Extended covariate sensitivity comparison | Quarto report | `notebooks/04c_extended_covariate_cox_model.ipynb` | `assets/cox_model_sensitivity_comparison.svg` |

Run the shared refresh or rerun a 04a/b/c notebook after the upstream cohort tables have been regenerated. The figure-export code uses existing notebook analysis objects and does not simulate or invent results.

## Manually Curated Architecture And Lineage Figures

- `assets/workflow_diagram.svg`: manually curated workflow overview used by the README and Quarto report.
- `assets/copd_table_lineage_dataset_flow.svg`: manually curated source-table-to-analysis-dataset lineage figure used by the Quarto report.

The COPD table-lineage SVG contains no patient-level data. It documents table provenance and the analysis workflow, and should be refreshed manually if the SQL table structure or report architecture changes.

The core and ICU plots are exploratory first-day-SOFA sensitivity analyses: SOFA can include information through 24 hours after follow-up begins. Subclass forest-plot rows each compare qualifying orders with neither; they are not a direct ACEi-versus-ARB comparison. The current audit corrects SVG wording and captions using existing published artifacts without fitting new models.

## Data Protection

The figure files contain only aggregate, presentation-level, or schematic workflow content. No patient-level records, local analysis extracts, credentials, individual model-input files, or protected health information are stored in `assets/`.
