# Figure Reproducibility

Notebook-generated result figures are written to stable paths under `assets/`. Rerunning the relevant notebooks refreshes the statistical figures used by the README and Quarto report.

## Notebook-Generated Result Figures

| Figure | Primary use | Exporting notebook | Output path |
| --- | --- | --- | --- |
| Kaplan-Meier survival curve | README and Quarto report | `notebooks/04a_outcomes_and_modeling.ipynb` | `assets/kaplan_meier_curve.png` |
| Cox hazard ratio forest plot | README and Quarto report | `notebooks/04c_extended_covariate_cox_model.ipynb` | `assets/cox_forest_plot.png` |
| ACE inhibitor versus ARB subgroup forest plot | Quarto report | `notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb` | `assets/raas_subgroup_forest_plot.svg` |
| Extended covariate sensitivity comparison | Quarto report | `notebooks/04c_extended_covariate_cox_model.ipynb` | `assets/cox_model_sensitivity_comparison.svg` |

Rerun the notebooks after the upstream cohort and modeling cells have completed. The figure-export code uses existing notebook analysis objects and does not simulate or invent results.

## Manually Curated Architecture And Lineage Figures

- `assets/workflow_diagram.svg`: manually curated workflow overview used by the README and Quarto report.
- `assets/copd_table_lineage_dataset_flow.svg`: manually curated source-table-to-analysis-dataset lineage figure used by the Quarto report.

The COPD table-lineage SVG contains no patient-level data. It documents table provenance and the analysis workflow, and should be refreshed manually if the SQL table structure or report architecture changes.

## Data Protection

The figure files contain only aggregate, presentation-level, or schematic workflow content. No patient-level records, local analysis extracts, credentials, SAS input files, or protected health information are stored in `assets/`.
