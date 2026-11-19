# Figure Reproducibility

The README displays two result figures and one workflow diagram. The Quarto report displays the four main result figures and the supplementary competing-event figure listed below. The 05c notebook and its SHORT guide also display a landmark forest plot. Result images are stored under `assets/`; images used in the Quarto report have matching copies under `docs/assets/`.

## Main Result Figures

| Figure | Current use | Notebook entry point | Output path |
| --- | --- | --- | --- |
| Kaplan-Meier survival curve | README and Quarto report | [04a outcomes and modeling](../notebooks/04a_outcomes_and_modeling.ipynb) | `assets/kaplan_meier_curve.png` |
| Exploratory extended core Cox forest plot | README and Quarto report | [04c extended covariate Cox model](../notebooks/04c_extended_covariate_cox_model.ipynb) | `assets/cox_forest_plot.png` |
| ACEi-only and ARB-only orders, each versus neither | Quarto report | [04b RAAS subgroups](../notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb) | `assets/raas_subgroup_forest_plot.svg` |
| Cox model sensitivity comparison | Quarto report | [04c extended covariate Cox model](../notebooks/04c_extended_covariate_cox_model.ipynb) | `assets/cox_model_sensitivity_comparison.svg` |

Notebooks 04a/b/c call the shared refresh in [scripts/current_analysis.py](../scripts/current_analysis.py). The refresh reads the existing corrected cohort tables, fits the models, exports all four figures through `export_figures`, copies them to `docs/assets/`, and updates [CURRENT_ANALYSIS.json](CURRENT_ANALYSIS.json) and the Quarto source. The notebook column identifies the analytical entry point; the figure-generation code is shared.

After upstream cohort tables have been regenerated, rerun the shared refresh only in an authorized MIMIC/BigQuery environment:

```bash
.venv/bin/python scripts/current_analysis.py
.venv/bin/python scripts/build_report.py
```

This command reruns clinical models. See [the full reproduction steps](../REPRODUCIBILITY.md) for source access, SQL execution order and table dependencies. Rendering the report alone uses saved aggregate records and images; it does not rerun the clinical analysis.

## Supplementary Competing-Event Figure

| Figure | Current use | Published input | Generator | Output path |
| --- | --- | --- | --- | --- |
| Unadjusted death and live-discharge cumulative incidence through day 28 | Quarto supplementary section | [SURVIVAL_SENSITIVITY_RESULTS.json](SURVIVAL_SENSITIVITY_RESULTS.json) | `export_figure` in [scripts/report_survival_supplement.py](../scripts/report_survival_supplement.py) | `assets/supplementary_competing_risks.svg` and `docs/assets/supplementary_competing_risks.svg` |

The public record contains two exposure groups on a fixed daily grid from day 0 to day 28, with pointwise patient-bootstrap 95% intervals. It comes from the verified local supplementary run described in [the supplement guide](SURVIVAL_SENSITIVITY_SUPPLEMENTS.md); the related analysis notebook is [05b competing risks](../notebooks/05b_competing_risks.ipynb).

To redraw this figure from the already published aggregate record without querying BigQuery, rerunning a bootstrap or fitting models, run the following from the repository root:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("scripts").resolve()))
from report_survival_supplement import load_public, export_figure

repo = Path.cwd()
data = load_public(repo)
if data is None:
    raise SystemExit("Published supplementary results are missing")
export_figure(repo, data)
PY
.venv/bin/python scripts/build_report.py
```

`load_public` checks the selected record against its validation, source and main-reference hashes before plotting. `export_figure` writes both asset copies. `build_report.py` renders the Quarto source and HTML using the saved assets; it does not regenerate the supplementary image itself. Preparing a new selected record from a verified local run is a separate step documented in [the supplement guide](SURVIVAL_SENSITIVITY_SUPPLEMENTS.md#prepare-and-rebuild-the-public-supplementary-section).

## Saved 05a and 05b Clinical Results

The [05a notebook](../notebooks/05a_patient_cluster_sensitivity.ipynb) and [SHORT guide](05a_patient_cluster_sensitivity_SHORT.md) show the saved admission/patient counts, ordinary and patient-cluster intervals, and [supplementary_cluster_forest.png](../assets/supplementary_cluster_forest.png). The [05b notebook](../notebooks/05b_competing_risks.ipynb) and [SHORT guide](05b_competing_risks_SHORT.md) reuse the published competing-event figure above and display its fixed-day tables; the notebook also shows the saved cause-specific Cox table.

[scripts/render_supplement_notebook_summaries.py](../scripts/render_supplement_notebook_summaries.py) rebuilds the marked Markdown and cluster figure from the verified public aggregate record. These are displays of the saved clinical execution, separate from selected runtime outputs (synthetic by default; current clinical data in the verified 2026-11-19 rerun). The generator preserves existing code, outputs and notebook metadata. `scripts/build_report.py` refreshes these summaries together with 05c and the SHORT guides; it does not rerun clinical models.

## 05c Landmark Notebook Preview

The [05c notebook](../notebooks/05c_time_aligned_severity.ipynb) and [its SHORT guide](05c_time_aligned_severity_SHORT.md) contain the published eligibility and model tables and [supplementary_landmark_forest.png](../assets/supplementary_landmark_forest.png). The forest plot compares the two matched landmark models using patient-cluster 95% intervals; it does not depict the original ICU-entry models or a formal difference between model estimates.

[scripts/render_landmark_summary.py](../scripts/render_landmark_summary.py) regenerates the notebook's marked Markdown cells and figure from the same hash-checked public aggregate record. Reviewed aggregate code-cell outputs are retained;  the clinical preview is visible without executing the default synthetic demonstration. The SHORT guide uses the same summary function.

```bash
.venv/bin/python scripts/build_report.py
```

This offline build refreshes the 05c preview, its image and SHORT guide alongside the report. To refresh only the notebook preview and image, run `.venv/bin/python scripts/render_landmark_summary.py`. Neither command queries clinical data or changes model estimates.

## Manually Curated Architecture and Lineage Figures

- [workflow_diagram.svg](../assets/workflow_diagram.svg): the workflow overview currently displayed in the README; it is not embedded in the Quarto report.
- [copd_table_lineage_dataset_flow.svg](../assets/copd_table_lineage_dataset_flow.svg): a maintained source-table-to-analysis-dataset schematic, currently not embedded in either the README or the Quarto report. The report presents its source dependencies in a table instead.

These diagrams document the workflow rather than statistical estimates. Update them manually if the SQL table structure or report architecture changes.

## Reading the Figures

### Notebook layout and figure numbering

All figure-bearing notebooks use the same order: `Figure N — title`, the image (or its execution cell/output), then **How to read**, **What the results show**, and **Interpretation limits**. Numbering restarts at 1 in each notebook and continues across saved clinical figures and runtime figures. Source references and input modes are collected at notebook/section level; they are not repeated in every caption. Tables do not consume figure numbers. Figure-free notebooks receive no placeholder figures.

| Notebook | Figure 1 | Figure 2 |
| --- | --- | --- |
| 04a | Kaplan–Meier survival | — |
| 04b | ACEi-only and ARB-only orders versus neither | — |
| 04c | Exploratory SOFA-core Cox model | Model sensitivity comparison |
| 05a | Saved ordinary/patient-cluster comparison | Selected-execution comparison |
| 05b | Saved competing-event curves | Selected-execution curves |
| 05c | Saved landmark Cox models | Selected-execution uncertainty comparison |

[scripts/notebook_figure_layout.py](../scripts/notebook_figure_layout.py) defines the layout and validates consecutive numbering and caption placement. The generators preserve existing code/output cells, metadata and cell IDs. SHORT guides use the matching saved-figure numbers. README and Quarto retain their own document structure and share the same three explanation headings; notebook-local numbers are not treated as global report references.

Detailed figure explanations are generated by [scripts/figure_interpretation.py](../scripts/figure_interpretation.py). They explain axes, units, symbols, intervals, saved estimates and interpretation limits alongside the figures in 04a–04c, 05a/05b, their SHORT guides, the README and the report. [scripts/render_main_figure_guides.py](../scripts/render_main_figure_guides.py) reuses the saved main images in 04a–04c without model execution. Both modules are included in the offline report build. Runtime 05a/05b plots carry separate notes identifying synthetic execution and any differences in legends or axis scales.

The Kaplan-Meier and supplementary cumulative-incidence figures use the same exposure colors: qualifying RAAS orders are blue (`#1f77b4`), and no qualifying RAAS orders are orange (`#ff7f0e`). Kaplan-Meier estimates censor live discharge; the supplementary figure treats live discharge as a competing event. Their curves represent different quantities.

The core and ICU plots are exploratory first-day-SOFA sensitivity analyses: SOFA can include information through 24 hours after follow-up begins. The core forest plot shows the original unpenalized model with ordinary admission-level intervals, rather than the refined primary model or the separate patient-cluster intervals. Subclass forest-plot rows each compare qualifying orders with neither; they are not a direct ACEi-versus-ARB comparison.

The supplementary cumulative-incidence figure is unadjusted. Its two panels use different vertical scales, and its pointwise bootstrap intervals are not simultaneous confidence bands. The patient-cluster Cox and separate 24-hour landmark results are reported in Quarto tables, not in this figure.

## Data Protection

The figure files contain only aggregate, presentation-level, or schematic workflow content. No patient-level records, local analysis extracts, credentials, individual model-input files, or protected health information are stored in `assets/`.


## Unified notebook presentation

All 11 notebooks use the [common figure/table catalog and numerical summaries](NOTEBOOK_PRESENTATION.md). The [presentation record](NOTEBOOK_PRESENTATION_VALIDATION.json) separately validates the current saved displays regenerated from previous clinical aggregates. The original clinical execution record is retained unchanged; this presentation refresh performs no new clinical query, model refit or bootstrap. There are 10 figures and 32 numbered tables. Selected-execution figure captions and result-specific numerical explanations are generated in the display call; saved-public sections are regenerated by the report-only build.

Source references and execution modes are now shown once per notebook/section rather than repeated beneath every figure/table. Numbers, titles and numerical summaries remain generated from the same aggregates. See [the concise source-display convention](NOTEBOOK_PRESENTATION.md#concise-source-display).
