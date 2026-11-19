# Notebook captions, numerical summaries and provenance

All 11 public notebooks use one presentation catalog and result-driven display functions. Figure and table numbering each restart at 1 within a notebook, continuing across its saved-public and selected-execution sections. A notebook without a figure has no placeholder figure.

| Notebook | Figures | Tables |
| --- | ---: | ---: |
| 01 | 0 | 1 |
| 02 | 0 | 3 |
| 03a | 0 | 3 |
| 03b | 0 | 4 |
| 04a | 1 | 2 |
| 04b | 1 | 2 |
| 04c | 2 | 4 |
| 04d | 0 | 1 |
| 05a | 2 | 4 |
| 05b | 2 | 4 |
| 05c | 2 | 4 |

The 32 tables include newly structured cohort-dimension and age-statistic outputs. Their numbers are unchanged from the corresponding previously saved aggregate checks; the additional tables do not add a cohort, endpoint or model. Age counts have admission units, while age descriptors have year units.

## One display path

- [presentation_catalog.py](../scripts/presentation_catalog.py) defines stable component keys, ordering, editorial titles and source references. These are metadata, not estimated statistics.
- [notebook_presentation.py](../scripts/notebook_presentation.py) generates each table's caption and numerical summary from the displayed aggregate DataFrame/result. It also generates the three selected-execution figures and result-specific guides. Input provenance is shown once at the beginning of each section, and again only if the selected input changes. Patient identifiers and oversized aggregate tables are rejected by the display function.
- [notebook_figure_layout.py](../scripts/notebook_figure_layout.py) supplies saved figure blocks and verifies numbering, section-level source context and explanations. `validate_tables()` checks all table declarations and retained HTML outputs.
- [figure_interpretation.py](../scripts/figure_interpretation.py) and the saved-summary builders use the public main/supplement aggregates. Their HR/CI values and CI-side interpretations share those inputs. Exact CI endpoints equal to 1 are classified as including 1.
- The SHORT guides reuse the same catalog and saved-summary functions. The report-only build preserves executed notebook outputs while regenerating the saved public sections.

Selected-execution summaries use that execution's `results` or `bundle`. They do not substitute the public clinical estimate for synthetic inputs. Clinical and synthetic origins are explicitly labeled. Cohort counts, merge checks, missingness, prescription-order totals, PH diagnostic counts, HR/CI/p-values, CIF percentages and landmark eligibility are calculated rather than manually transcribed into prose. CI inclusion does not establish equivalence, and observational associations do not establish treatment effects.

## Two different records

1. [NOTEBOOK_EXECUTION_VALIDATION.json](NOTEBOOK_EXECUTION_VALIDATION.json) retains the original clinical top-to-bottom execution evidence at Git commit `27e6743edd973ec4bf461f56cc3872b41a880546`.
2. [NOTEBOOK_PRESENTATION_VALIDATION.json](NOTEBOOK_PRESENTATION_VALIDATION.json) binds the current notebook sources/outputs to that evidence and the unchanged public aggregate records. The presentation refresh does not retrieve clinical data, execute BigQuery SQL, rebuild tables, fit models or perform another bootstrap. Its setup explicitly replaces these operations with the versioned validated aggregate inputs, while executing all current notebook presentation paths.

The original clinical record is not rewritten to claim a new clinical run. The Git output filter checks the presentation record and its source/evidence bindings before retaining current aggregate outputs; otherwise it strips them. This does not grant approval to publish arbitrary new outputs. Complete local originals remain backed up under ignored `reports/local_supplements/`.

## Reproduce the presentation without clinical access

Use a fresh isolated copy and output directory. From a checkout containing these changes:

```bash
mkdir -p reports/local_supplements
mkdir reports/local_supplements/presentation_copy
git archive HEAD | tar -x -C reports/local_supplements/presentation_copy
.venv/bin/python scripts/render_notebook_presentations.py \
  --repo reports/local_supplements/presentation_copy \
  --source-repo . \
  --source-commit 27e6743edd973ec4bf461f56cc3872b41a880546 \
  --output reports/local_supplements/presentation_replay
```

The source commit must be available in local Git history. The renderer validates its notebooks against the original execution record, reads only retained aggregate outputs/public aggregate JSON, and refuses to overwrite the source repository or reuse an output directory. It uses no clinical credentials. It does not write private covariance or patient data into public files.

To regenerate the saved-public Markdown sections and SHORT guides, run the report-only build in the isolated copy with the existing environment. In normal authorized clinical notebook execution, the replay setup is absent: original bounded SQL/loaders and model functions remain in use. The 05-series default is still synthetic. A new clinical run and a presentation replay must continue to be recorded separately.

## Concise source display

Source references and stored-output evidence are collected in each notebook's **Inputs and execution mode** section. The saved-clinical section identifies its public aggregate record once; the selected-execution section displays its current/local/synthetic origin once after selection. Figure and table captions contain their number, title and result-derived summary, without repeating a `Data source` line. If a display call receives a different input origin or execution provenance, its context is shown again automatically. The catalog retains machine-readable source definitions.
