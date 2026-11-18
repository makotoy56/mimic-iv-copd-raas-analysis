# Timing, prescription-order groups and separate reanalysis options

## Current interpretation

`sofa_score` comes from `mimiciv_3_1_derived.first_day_sofa`. Its published definition can use information through 24 hours after ICU entry, while follow-up starts at ICU entry. All SOFA-containing core, ICU-adjusted and CHF/SOFA-stratified models are therefore exploratory sensitivity analyses that can use post-start information, not baseline-only severity adjustment. Temporal leakage or adjustment for post-exposure information may affect interpretation; its impact has not been quantified here. The primary age/sex model with era strata is unchanged. Time-aligned severity adjustment or a separate landmark design would require reanalysis.

Exposure flags identify inpatient prescription records in the same hospital admission with `starttime <= intime`. They do not verify actual administration, continued treatment at ICU entry, adherence or concurrent ACEi/ARB administration. Both positive class flags mean qualifying records for both classes; they do not establish simultaneous treatment. Neither means no qualifying prescription record for either class, not proven absence of all medication use.

ACEi-only and ARB-only prescription-order groups are each compared with neither qualifying order. Records with both class flags positive are excluded from this subclass analysis. The main analysis reports no direct ACEi-versus-ARB contrast or interaction test. Different point estimates, or one p-value below 0.05 and the other above it, do not establish a difference between the classes.

The [published first-day SOFA SQL](https://github.com/MIT-LCP/mimic-code/blob/main/mimic-iv/concepts/firstday/first_day_sofa.sql) includes windows extending to ICU entry plus one day; some components also allow pre-entry observations. This public definition supports the timing caution. This audit did not inspect the exact deployed v3.1 derived-table materialization or individual measurement times, and does not estimate how much the timing affects results. The presence or magnitude of a specific bias has not been established by this documentation change.

## Options requiring a separate design and analysis

1. **Severity available at ICU entry:** define an explicit pre-entry measurement window, reconstruct severity only from information available by the original time zero, and specify missing-data and treatment-variable handling before refitting. The existing first-day SOFA must not simply be relabeled as baseline severity.
2. **A 24-hour landmark:** define eligibility among patients alive and still under observation at the landmark, begin risk follow-up at that landmark, and specify the exposure and covariate windows. Early deaths and early discharges would be handled under that new design; the study population and estimand would differ from the current ICU-entry analysis.
3. **A direct ACEi-versus-ARB contrast:** prespecify the between-class comparison and estimate its uncertainty from a suitable refit or the joint coefficient covariance. Separate comparisons with neither, or different significance levels, are not that test.
4. **Actual administration or concurrent treatment:** use an appropriately timed administration source and an explicit overlap definition. Prescription start records alone cannot establish either condition.

None of these analyses was implemented or run in this audit. They may require new extraction, model fitting and diagnostics in an authorized environment. Current primary age/sex/era estimates, existing subgroup/core/ICU numbers, cohort construction and all SQL statements are unchanged.

A later local post-hoc direct contrast is documented in the [local supplement workflow](ACEI_ARB_SUPPLEMENT_LOCAL.md). Its numerical output is excluded from the public report; it does not implement time-aligned severity or a landmark analysis.
