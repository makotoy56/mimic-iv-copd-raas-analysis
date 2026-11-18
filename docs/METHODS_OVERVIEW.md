# Methods Overview

This document holds the methods detail that was shortened in the README. It preserves the analytic design and definitions used across the notebooks.

## Study Design And Data Source

This is a retrospective observational cohort study using MIMIC-IV v3.1, a de-identified ICU electronic health record database. The analysis is intended for reproducible clinical analytics and real-world evidence workflow demonstration.

## Cohort Construction

Adult ICU patients with COPD were identified using ICD-9 and ICD-10 diagnosis codes recorded during hospitalization. Each analytic record represents one qualifying hospital admission, anchored to the first ICU stay within that admission; subsequent ICU stays during the same hospital admission are excluded. A patient may contribute more than one qualifying hospital admission. Cohort construction uses reproducible BigQuery SQL and notebook-based checks.

Age is estimated at hospital admission as `anchor_age + EXTRACT(YEAR FROM admittime) - anchor_year`; the adult threshold is applied to this estimate. The baseline and outcome tables preserve that same `age` instead of resetting it to `anchor_age`. Raw `anchor_age` and `age_anchor_topcoded` are retained throughout the pipeline. An `anchor_age` of 91 represents the grouped ages above 89 in the anchor year; the year-adjusted value for these admissions remains a proxy, not a recovered exact age. Year-based age is approximate for all admissions because an exact birthday is unavailable.

Primary workflow:

- `01_icu_cohort.ipynb`: adult ICU cohort extraction
- `02_cohort_and_exposures.ipynb`: COPD cohort and RAAS exposure construction
- `03a_baseline.ipynb`: baseline covariate table
- `03b_merge_exposures.ipynb`: detailed exposure merge
- Run both outcome SQL scripts below before any 04-series notebook.

## Outcome-table dependencies

| Script | Input | Persistent output | Downstream use |
| --- | --- | --- | --- |
| `sql/03_merge_exposures.sql` | `cohort_copd` and `cohort_copd_raas_detailed` | `cohort_copd_with_raas` | Exposure distribution checks; does not create the outcomes used by the shared model loader |
| `sql/04_build_outcomes.sql` | `cohort_copd_baseline` and source hospital `admissions` | `cohort_copd_outcomes` | Endpoint/follow-up QA; mandatory input to the extended-outcome SQL |
| `sql/04_build_outcomes_extended.sql` | `cohort_copd_outcomes`, derived `first_day_sofa` and `charlson`, and source ICU stays | `cohort_copd_outcomes_extended` | The shared `load_current_data()` reads this table and joins `cohort_copd_raas_detailed` for notebooks 04a–04d |

Run the full outcome scripts sequentially in US after phase 03 and before 04a. Even the primary age/sex model reads the shared extended input; joining SOFA into that input does not mean SOFA is included in the primary model formula. The 04-series notebooks refresh model results and figures, not BigQuery tables.

## Exposure Definition

Exposure flags identify inpatient prescription records in the same hospital admission with `starttime <= intime`. They do not verify actual administration, continued treatment at ICU entry, adherence or concurrent ACEi/ARB administration. Both positive class flags mean qualifying records for both classes; they do not establish simultaneous treatment. Neither means no qualifying prescription record for either class, not proven absence of all medication use.

Detailed indicators identify ACEi-only orders, ARB-only orders, records for both classes, and neither. Legacy field names such as `is_monotherapy` and `exposure_group_3cat_monotherapy` are order-flag labels, not verified medication administration. ACEi-only and ARB-only prescription-order groups are each compared with neither qualifying order. Records with both class flags positive are excluded from this subclass analysis. The main analysis reports no direct ACEi-versus-ARB contrast or interaction test. Different point estimates, or one p-value below 0.05 and the other above it, do not establish a difference between the classes.

## Outcome Definition

The primary outcome is time to in-hospital death, with follow-up beginning at ICU admission. For a death event, `time_to_event_days` is measured from ICU admission (`intime`) to the recorded in-hospital death time (`admissions.deathtime`); discharge time (`admissions.dischtime`) is used as an explicitly flagged fallback only when death time is unavailable. For a patient discharged alive, follow-up is measured from ICU admission to discharge time and the record is censored at discharge.

Follow-up is calculated as `DATETIME_DIFF(endpoint, intime, MICROSECOND) / 86400000000.0`, using the source DATETIME values. This preserves positive sub-hour intervals and avoids integer-hour boundary counting. Before replacing the outcome table, QA rejects missing timestamps, invalid event indicators, reversed death or discharge endpoints, and true zero follow-up requiring adjudication. The death-time fallback flag is preserved in both primary and extended datasets.

## Covariates

The refined primary model adjusts for admission-age estimate and sex, stratified by anchor-year group. Its formula is unchanged. Extended core models add first-day SOFA, CHF, CKD and diabetes; ICU models add pooled ICU type. `sofa_score` comes from `mimiciv_3_1_derived.first_day_sofa`. Its published definition can use information through 24 hours after ICU entry, while follow-up starts at ICU entry. All SOFA-containing core, ICU-adjusted and CHF/SOFA-stratified models are therefore exploratory sensitivity analyses that can use post-start information, not baseline-only severity adjustment. Temporal leakage or adjustment for post-exposure information may affect interpretation; its impact has not been quantified here. The primary age/sex model with era strata is unchanged. Time-aligned severity adjustment or a separate landmark design would require reanalysis.

The source for this timing caution is the [published MIMIC first-day SOFA SQL](https://github.com/MIT-LCP/mimic-code/blob/main/mimic-iv/concepts/firstday/first_day_sofa.sql). This audit did not inspect the deployed derived table or individual measurement times. See [separate reanalysis options](ANALYSIS_TIMING_LIMITATIONS.md).

## Statistical Analysis

The primary clinical analysis uses Kaplan-Meier survival curves and Cox proportional hazards regression. Proportional hazards assumptions are assessed using Schoenfeld residual-based diagnostics. Exploratory sensitivity analyses evaluate first-day covariates, ICU type, penalized fits and CHF/SOFA strata, with the post-start information limitation above.

Live discharge is treated as censoring in the primary Cox analysis. A competing-risk framework was not implemented. The Cox models analyze admission-level records and do not include a patient-level clustering or frailty term for patients with more than one qualifying admission.

The `04d_python_logistic_model.ipynb` notebook optionally fits and exports a secondary Python logistic model with aggregate cohort provenance. It is not the primary clinical model or evidence of independent clinical validation.

## Reproducibility

Data extraction uses version-controlled BigQuery SQL and notebooks. Source-SQL and downstream-table QA are documented separately. The independent Python script fits six unpenalized Cox specifications with statsmodels PHReg and compares 40 coefficients with lifelines. It uses the same corrected model inputs, so it checks the statistical implementation rather than independently reconstructing the source data. See [validation notes](VALIDATION_NOTES.md).

## Follow-up implementation corrections

ICU and hospital LOS now use DATETIME microsecond differences divided by 86,400,000,000, consistently with follow-up. ICU categories with fewer than 50 admissions are pooled using counts alone. Additional exploratory models stratify by era, CHF and exact SOFA; the ICU version also stratifies by pooled ICU category. These change the adjustment structure and supplement the unchanged primary age/sex/era model. PH tests, warnings and sparse-stratum counts are recorded in CURRENT_ANALYSIS.json.
