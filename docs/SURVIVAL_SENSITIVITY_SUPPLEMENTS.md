# Additional survival sensitivity notebooks

These companion analyses preserve the current 04a–04d workflow and its saved estimates. They examine patient dependence, competing hospital endpoints and a later severity landmark. They do not establish causal treatment effects or automatically replace the published primary model.

| Notebook | Scope | Short guide |
| --- | --- | --- |
| [05a patient-cluster sensitivity](../notebooks/05a_patient_cluster_sensitivity.ipynb) | Refined primary and exploratory SOFA-core models; same admissions and coefficients, ordinary versus patient-cluster uncertainty | [SHORT](05a_patient_cluster_sensitivity_SHORT.md) |
| [05b competing risks](../notebooks/05b_competing_risks.ipynb) | Unadjusted death/discharge cumulative incidence, patient-bootstrap intervals, and age/sex/era cause-specific Cox models | [SHORT](05b_competing_risks_SHORT.md) |
| [05c severity landmark](../notebooks/05c_time_aligned_severity.ipynb) | Exploratory 24-hour landmark using matched complete cases and patient-cluster inference | [SHORT](05c_time_aligned_severity_SHORT.md) |

## Execution and data handling

Run `uv sync --locked` and select the repository Python 3.12 kernel. New 05a–05c executions default to current clinical data. [supplement_notebook_runtime.py](../scripts/supplement_notebook_runtime.py) announces the selected input mode and stops on configuration/access failures; it never substitutes synthetic data. Calculations and plotting remain in [survival_sensitivity.py](../scripts/survival_sensitivity.py). Synthetic estimates are artificial software checks, not MIMIC findings.

To run all supplements once in an already authorized local MIMIC/BigQuery environment:

```bash
.venv/bin/python scripts/survival_sensitivity.py \
  --current-data --analysis all --bootstrap-replicates 1000 \
  --output reports/local_supplements/sensitivity_run02
```

Use a new output directory for every run. The existing loader performs a US dry run and enforces the existing 200 MB billing cap. Its supplementary projection adds `subject_id`, `hadm_id` and `stay_id` to the existing explicit columns. These pseudonymous keys and admission-level model rows remain in memory: never display them, save a row export, or upload them to an external analysis service. Missing keys, duplicated admissions/stays, invalid flags and nonpositive follow-up fail before fitting. Counts, duration/age sums and ordinary model estimates must match the saved current reference.

Only aggregate JSON and figures are written, under the Git-ignored `reports/local_supplements/` directory. Existing tables, `CURRENT_ANALYSIS.json`, primary figures and report estimates are not updated. Full local results remain excluded from Git. Selected, verified aggregate results are published in [SURVIVAL_SENSITIVITY_RESULTS.json](SURVIVAL_SENSITIVITY_RESULTS.json) and the [Quarto supplementary section](https://makotoy56.github.io/mimic-iv-copd-raas-analysis/copd_raas_survival_report.html#supplementary-sensitivity-analyses). Tracked notebooks retain only reviewed aggregate execution outputs bound in the original [execution record](NOTEBOOK_EXECUTION_VALIDATION.json), [presentation record](NOTEBOOK_PRESENTATION_VALIDATION.json), or later [current-default execution record](SUPPLEMENT_NOTEBOOK_EXECUTION_VALIDATION.json); full local bundles remain under the ignored directory.

For a no-query notebook review of a completed run, set `DATA_MODE = "local"` and `LOCAL_RESULT` to its `aggregate_results.json`. The reader checks the supplement version, source-script hash and current reference hash. `DATA_MODE = "current"` is the default and runs that notebook's analysis through the same bounded loader. Set `COPD_NOTEBOOK_DATA_MODE=synthetic` before starting Jupyter, or explicitly set `DATA_MODE = "synthetic"`, to request an artificial demonstration.

The low-level CLI retains its separate synthetic demonstration default: when deliberately requesting that CLI demonstration, omit `--current-data` and choose a fresh ignored directory. Notebook execution uses the current-data default above and never invokes the CLI as a fallback. The Python supplement calculations do not require R. The optional independent validation command requires R and its `survival` package:

```bash
.venv/bin/python scripts/validate_survival_sensitivity_r.py \
  --output /tmp/survival_synthetic_reference.json
.venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
```

## 05a: Patient dependence

The notebook and SHORT guide display saved clinical counts, interval comparisons and a forest plot from the verified public aggregate record. Their marked clinical summary is separate from the selected runtime results (current by default for new execution; stored outputs retain their earlier origin labels). See [the figure reproduction steps](FIGURE_REPRODUCIBILITY.md#saved-05a-and-05b-clinical-results).

Fit unpenalized Efron Cox models with unchanged age, sex and era strata; the core additionally retains first-day SOFA, CHF, CKD and diabetes. Complete cases are fixed before comparing covariance methods. Sum Efron score residuals across all admissions of a patient, including across era strata, and form an HC0 sandwich covariance. Use normal Wald 95% intervals and two-sided p-values, with no finite-cluster correction. This handles within-patient dependence for inference, but does not model frailty or a recurrent-event process.

Ties are not jittered or rounded. The installed statsmodels implementation's ordinary likelihood/Hessian is used for point estimates, while tie-aware score residuals are computed explicitly for the cluster covariance. [Synthetic reference checks](SURVIVAL_SUPPLEMENTS_SYNTHETIC_CHECK.json) compare coefficients, ordinary and cluster covariance with R `survival::coxph`, for tied and untied artificial times. An additional score-gradient identity is checked at each fit. This avoids assuming that a generic robust option handles Efron ties correctly.

## 05b: Competing hospital endpoints

The notebook displays the saved clinical day-7/14/28 CIF table, the published competing-event figure and the separate cause-specific Cox table. The SHORT guide includes the saved CIF table and figure. These displays do not re-execute a clinical bootstrap or fit and are labeled separately from the selected runtime outputs.

Death is event 1 and live discharge is event 2. The two-cause Aalen-Johansen product integral handles ties from both causes together, using the risk set just before the shared time. No jitter is applied. Export a fixed daily grid through day 28; no individual event times are serialized. The current complete hospital-episode data contain one of these two endpoints for each admission. Death-time fallbacks retain the original discharge-time proxy, so exact death timing remains uncertain for those admissions.

Uncertainty uses 1,000 patient-cluster bootstrap samples with fixed seed 20261118. Resample patients globally in a fixed patient-key order and carry all their admissions, so patients contributing to both exposure groups remain linked. Intervals are pointwise 95% percentile intervals, including for RAAS-minus-no-RAAS death-CIF differences. These are unadjusted curves and associations. Age/sex/era cause-specific Cox models for death and discharge are provided separately with patient-cluster inference. Cause-specific HRs and cumulative incidence answer different questions; neither is a causal treatment comparison. A Fine–Gray model is not implemented.

## 05c: A separate 24-hour landmark

The [05c notebook](../notebooks/05c_time_aligned_severity.ipynb) and [its SHORT guide](05c_time_aligned_severity_SHORT.md) show published clinical results without execution: a sequential eligibility table, a matched-model table and a forest plot with patient-cluster 95% intervals. These are generated from the hash-checked public aggregate record, separately from the selected runtime outputs (current by default for new execution; stored outputs retain their earlier origin labels). Rebuild them with `scripts/build_report.py`; see [the figure reproduction steps](FIGURE_REPRODUCIBILITY.md#05c-landmark-notebook-preview).

Eligibility requires a recorded endpoint strictly later than 24 hours after original ICU entry. Endpoints at or before 24 hours are excluded. Remaining fallback deaths with unknown death timestamps are also excluded because survival to the landmark is not known. Subtract one day from eligible durations and retain the original prescription-order exposure window at or before ICU entry. Use the same core-complete admissions for both the age/sex and the first-day-SOFA core landmark model, with era strata and patient-cluster inference. Report early endpoints, fallback exclusions and missing core covariates.

This targets admissions alive and still hospitalized beyond 24 hours, rather than the original ICU-entry population. The published first-day-SOFA definition can use measurements through ICU entry plus one day, but the deployed component windows and individual measurement timestamps have not been independently reconstructed. The result is an exploratory landmark sensitivity under that definition, not verified pre-ICU severity adjustment. SOFA follows exposure and may mediate associations or induce selection/collider bias. Comorbidity-code timing is unchanged and remains a limitation. This analysis does not resolve residual confounding, selection bias, or causality. Reconstructing pre-ICU severity remains a separate design.

## Validation status and publication scope

The [execution and validation record](SURVIVAL_SUPPLEMENTS_VALIDATION.json) records the checked source/reference hashes, the original 25 analytical regression tests and the expanded 31-test report suite, notebook execution modes and retained limitations, including the separate selected-aggregate publication record.

The versioned synthetic record covers Efron coefficients and both covariance matrices against R `survival`, plus tied two-cause Aalen-Johansen estimates. Synthetic validation establishes numerical behavior, not clinical validity. See the local execution record for any current-data result; the selected aggregate estimates are reported in the separate Quarto supplementary section without replacing original main estimates.

On 2026-11-18 all three supplements were executed locally against the existing corrected cohort using one bounded, read-only SELECT. Ordinary reference estimates matched before the new results were saved. Each notebook also completed top-to-bottom on synthetic inputs and, separately, on the verified local aggregate result without another query. Full numerical outputs and executed clinical copies remain under ignored `reports/local_supplements/`; selected aggregate estimates are included in the public report; at that time, source notebooks defaulted to synthetic demonstrations. The current source-policy change applies to new executions and does not rewrite those historical run records. The later 2026-11-19 rerun retains reviewed clinical aggregate outputs as described below. The independent component-time validation and pre-ICU severity reconstruction described above remain unperformed.

## Full notebook rerun on 2026-11-19

All 11 public notebooks were executed top-to-bottom against the existing authorized BigQuery environment, including 05a–05c in `current` mode. The new main-model statistics and selected supplementary results matched the existing public records; the clinical competing-risk bootstrap used 1,000 replicates with the existing fixed seed. [The execution record](NOTEBOOK_EXECUTION_VALIDATION.json) binds the saved notebook sources and outputs. The existing main/supplement JSON records and analysis definitions were not replaced.

New notebook execution defaults to `current`. Set `COPD_NOTEBOOK_DATA_MODE=synthetic` or `local` before starting Jupyter only when explicitly selecting those modes; always read the announced mode, `data_origin` and plot title. Figure 1 displays the fixed published aggregate snapshot; Figure 2 and the runtime tables display their selected execution. Stored outputs can predate this source change and retain their earlier origin labels. The Git filter retains only outputs with matching reviewed source/output records. The later [current-default execution record](SUPPLEMENT_NOTEBOOK_EXECUTION_VALIDATION.json) augments the historical records for the new current-default sources without replacing them.

## Method references

- [R survival Cox documentation](https://stat.ethz.ch/R-manual/R-devel/library/survival/html/coxph.html)
- [R survival competing-risks and multistate vignette](https://cran.r-project.org/web/packages/survival/vignettes/compete.pdf)
- [Austin, Lee and Fine: competing-risk methods and interpretation](https://pmc.ncbi.nlm.nih.gov/articles/PMC4741409/)
- [Giobbie-Hurder et al.: conditional landmark analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC3732313/)
- [Published MIMIC first-day SOFA definition](https://github.com/MIT-LCP/mimic-code/blob/main/mimic-iv/concepts/firstday/first_day_sofa.sql)

## Prepare and rebuild the public supplementary section

The report reads the selected aggregate record and its validation hashes, never the ignored full run. Rebuild from a fresh checkout without clinical access using:

```bash
.venv/bin/python scripts/build_report.py
```

To prepare the selected record from the exact locally verified run:

```bash
.venv/bin/python scripts/report_survival_supplement.py \
  --input reports/local_supplements/sensitivity_run02/aggregate_results.json
.venv/bin/python scripts/build_report.py
```

The preparation command verifies the local run, analysis-source and main-reference hashes, selects only counts, RAAS estimates and the fixed daily CIF grid, and creates the public figure. It does not query BigQuery or refit models. A new analytical run needs its validation record reviewed and rebound before publication. The renderer rejects stale or modified records. README values and Quarto tables share this same selected record. Full local output and covariance matrices are not copied into the public record.

The 05-series SHORT guides summarize the published clinical results and distinguish them from new execution, which defaults to current data and stops on missing access/configuration. All 11 notebook SHORT guides are generated by `scripts/render_short_notes.py` from the current public aggregate records; `scripts/build_report.py` updates them during report builds.


## Unified notebook presentation

All 11 notebooks use the [common figure/table catalog and numerical summaries](NOTEBOOK_PRESENTATION.md). The [presentation record](NOTEBOOK_PRESENTATION_VALIDATION.json) separately validates the current saved displays regenerated from previous clinical aggregates. The original clinical execution record is retained unchanged; this presentation refresh performs no new clinical query, model refit or bootstrap. There are 10 figures and 32 numbered tables. Selected-execution figure captions and result-specific numerical explanations are generated in the display call; saved-public sections are regenerated by the report-only build.

Source references and execution modes are now shown once per notebook/section rather than repeated beneath every figure/table. Numbers, titles and numerical summaries remain generated from the same aggregates. See [the concise source-display convention](NOTEBOOK_PRESENTATION.md#concise-source-display).


## Notebook modes and access failures

| Selection | Behavior |
| --- | --- |
| Unset `COPD_NOTEBOOK_DATA_MODE`, or `current` | Existing approved current-data loader; read-only SELECT, US dry run, 200 MB guard. The clinical bootstrap setting is at least 1,000 (used for competing-event CIF intervals). Failure stops execution. |
| Explicit `synthetic` | Artificial software checks only, with the synthetic origin and figure title clearly labeled. |
| Explicit `local` | Read the explicitly selected `LOCAL_RESULT` aggregate JSON under `reports/local_supplements`; verify its version/source/reference provenance; no query or refit. |

The mode banner appears before loading. Missing ADC: configure your approved account using the environment instructions and restart the selected kernel. Expired credentials: renew ADC and restart. Permission denied: confirm query-project `bigquery.jobs.create` and analysis-table read access for the approved account. Missing table/project/dataset: verify source names and US location; the notebook does not recreate tables. A byte-guard or reference mismatch stops rather than increasing limits or substituting earlier results. Provider error details, credential values and patient rows are not printed.

The input cell clears earlier `bundle`/`result` variables before loading, so a failed current run cannot redisplay the previous synthetic/clinical result. Offline/mock tests cover failure handling and explicit mode selection. The subsequent [current-default execution record](SUPPLEMENT_NOTEBOOK_EXECUTION_VALIDATION.json) covers real-data execution of all three current-default notebook sources with the mode override unset, no errors, and exact agreement on 653 checked supplementary numerical values. Six figures and twelve tables were reviewed. Each query used a 2,736,972-byte US dry run under the existing 200 MB cap; no tables or scientific reference files were changed. Historical validation records remain intact. Changed sources or new outputs need matching reviewed execution/presentation provenance before publication.
