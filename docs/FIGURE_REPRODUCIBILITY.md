# Figure Reproducibility

The README displays two result figures and one workflow diagram. The Quarto report displays the four main result figures and the supplementary competing-event figure listed below. Result images are stored under `assets/`, with matching copies under `docs/assets/` for the published report.

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

## Manually Curated Architecture and Lineage Figures

- [workflow_diagram.svg](../assets/workflow_diagram.svg): the workflow overview currently displayed in the README; it is not embedded in the Quarto report.
- [copd_table_lineage_dataset_flow.svg](../assets/copd_table_lineage_dataset_flow.svg): a maintained source-table-to-analysis-dataset schematic, currently not embedded in either the README or the Quarto report. The report presents its source dependencies in a table instead.

These diagrams document the workflow rather than statistical estimates. Update them manually if the SQL table structure or report architecture changes.

## Reading the Figures

The Kaplan-Meier and supplementary cumulative-incidence figures use the same exposure colors: qualifying RAAS orders are blue (`#1f77b4`), and no qualifying RAAS orders are orange (`#ff7f0e`). Kaplan-Meier estimates censor live discharge; the supplementary figure treats live discharge as a competing event. Their curves represent different quantities.

The core and ICU plots are exploratory first-day-SOFA sensitivity analyses: SOFA can include information through 24 hours after follow-up begins. The core forest plot shows the original unpenalized model with ordinary admission-level intervals, rather than the refined primary model or the separate patient-cluster intervals. Subclass forest-plot rows each compare qualifying orders with neither; they are not a direct ACEi-versus-ARB comparison.

The supplementary cumulative-incidence figure is unadjusted. Its two panels use different vertical scales, and its pointwise bootstrap intervals are not simultaneous confidence bands. The patient-cluster Cox and separate 24-hour landmark results are reported in Quarto tables, not in this figure.

## Data Protection

The figure files contain only aggregate, presentation-level, or schematic workflow content. No patient-level records, local analysis extracts, credentials, individual model-input files, or protected health information are stored in `assets/`.
