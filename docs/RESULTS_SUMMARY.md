# Current Results (2026-11-18)

Analysis version: `admission_age_elapsed_time_los_v2`. These estimates and the figures use regenerated analysis tables and continuous elapsed follow-up.

The cohort contains 11,964 admissions and 1,692 in-hospital deaths. Refined primary RAAS HR: 0.732 (0.592–0.904), p=0.00383. Exploratory first-day-SOFA core RAAS HR: 0.833 (0.673–1.030), p=0.09122.

| Model | RAAS HR (95% CI) | p |
| --- | --- | ---: |
| Primary refined | 0.732 (0.592–0.904) | 0.00383 |
| Exploratory core (first-day SOFA) | 0.833 (0.673–1.030) | 0.09122 |
| Exploratory core + L2 (0.1) | 0.886 (0.766–1.025) | 0.10376 |
| Exploratory ICU adjusted | 0.958 (0.772–1.187) | 0.69262 |
| Exploratory ICU + L2 (0.01) | 0.910 (0.743–1.115) | 0.36324 |
| Core CHF/SOFA strata (exploratory) | 0.830 (0.666–1.034) | 0.09666 |
| ICU CHF/SOFA/type strata (exploratory) | 1.127 (0.880–1.443) | 0.34395 |

ACEi-only and ARB-only prescription-order groups are each compared with neither qualifying order. Records with both class flags positive are excluded from this subclass analysis. The main analysis reports no direct ACEi-versus-ARB contrast or interaction test. Different point estimates, or one p-value below 0.05 and the other above it, do not establish a difference between the classes.

| Subclass | HR (95% CI) | p |
| --- | --- | ---: |
| ACEi-only orders vs neither | 0.683 (0.521–0.894) | 0.00550 |
| ARB-only orders vs neither | 0.805 (0.573–1.131) | 0.21116 |

## Timing of severity information

`sofa_score` comes from `mimiciv_3_1_derived.first_day_sofa`. Its published definition can use information through 24 hours after ICU entry, while follow-up starts at ICU entry. All SOFA-containing core, ICU-adjusted and CHF/SOFA-stratified models in the original ICU-entry workflow are therefore exploratory sensitivity analyses that can use post-start information, not baseline-only severity adjustment. Temporal leakage or adjustment for post-exposure information may affect interpretation; its impact has not been quantified here. The primary age/sex model with era strata is unchanged. A separate exploratory 24-hour landmark analysis is reported in the supplementary results; pre-ICU severity reconstruction remains unperformed.

Exposure flags identify inpatient prescription records in the same hospital admission with `starttime <= intime`. They do not verify actual administration, continued treatment at ICU entry, adherence or concurrent ACEi/ARB administration. Both positive class flags mean qualifying records for both classes; they do not establish simultaneous treatment. Neither means no qualifying prescription record for either class, not proven absence of all medication use.

See [timing limitations and separate reanalysis options](ANALYSIS_TIMING_LIMITATIONS.md).

## Diagnostics and interpretation

The core and pooled ICU models retain their original covariate structure. Additional exploratory models stratify baseline hazards by era, CHF and exact SOFA; the ICU variant also stratifies by pooled ICU type. These models do not estimate CHF or SOFA coefficients. They supplement the primary analysis and are not chosen by searching for non-significant PH tests.

| Model | Number of strata | Rank PH tests with p<0.05 | Model warnings |
| --- | ---: | --- | --- |
| Primary refined | 5 | None detected | None |
| Exploratory core (first-day SOFA) | 5 | chf (<0.00001), sofa_score (0.01924) | None |
| Exploratory core + L2 (0.1) | 5 | chf (0.00126) | None |
| Exploratory ICU adjusted | 5 | chf (0.00008), sofa_score (0.00157) | None |
| Exploratory ICU + L2 (0.01) | 5 | chf (0.00018), sofa_score (0.00318) | None |
| Core CHF/SOFA strata (exploratory) | 191 | None detected | None |
| ICU CHF/SOFA/type strata (exploratory) | 1118 | diabetes (0.02879) | None |

A non-significant PH test does not establish that the PH assumption is true. The exploratory ICU-stratified RAAS point estimate is above 1 while its confidence interval includes 1, demonstrating sensitivity to adjustment structure. The ICU-stratified model retains a diabetes PH flag, so the diagnostic issues are not universally resolved. Stratified models permit different baseline hazards for the stratifying covariates; their estimates are conditional on these strata, some of which are sparse. The sensitivity specifications are exploratory responses to diagnostics in this dataset.

Rare ICU labels with fewer than 50 admissions are pooled using admission counts alone, independently of outcome. The pooled labels are: Intensive Care Unit (ICU), Medicine, PACU, Surgery/Trauma, Surgery/Vascular/Intermediate.

The original main models retain ordinary admission-level inference and live-discharge censoring. Separate post hoc supplements provide patient-cluster sandwich inference for repeated admissions, unadjusted Aalen–Johansen cumulative incidence with live discharge as a competing event, and cause-specific death/live-discharge Cox models. These supplements preserve the original main estimates and do not establish treatment effects. Year-based age remains approximate, especially for the anchor-age 91 group. Residual confounding and first-day-SOFA timing limitations remain. See [supplementary methods and limitations](SURVIVAL_SENSITIVITY_SUPPLEMENTS.md).

## Reproducibility checks

Six unpenalized Cox specifications (40 coefficients) were independently recalculated with statsmodels PHReg using matched complete cases, era/additional strata and Efron ties. Coefficients, HRs, confidence-interval endpoints and p-values matched the lifelines reference within an absolute tolerance of 1e-4. The saved comparison is bound to this exact aggregate analysis snapshot by its reference hash. See [the calculation record](INDEPENDENT_COX_CROSSCHECK.json) and [the scope and limitations](INDEPENDENT_REVALIDATION.md).

This checks a separate statistical implementation on the same corrected model inputs. Source-SQL extraction is evaluated separately. Penalized fits, PH diagnostics, patient clustering, competing risks and causal validity are not established by this numerical comparison.

The reproducible workflow covers authorized MIMIC source access, version-controlled BigQuery extraction and cohort construction, explicit model-column retrieval, Python modeling, independent numerical comparison, figure generation and Quarto reporting. Only aggregate results are published; no external analysis-service upload is part of this workflow. See [the full reproduction steps](https://github.com/makotoy56/mimic-iv-copd-raas-analysis/blob/main/REPRODUCIBILITY.md).

The refreshed figures contain aggregate results only. Full estimates and PH p-values are in [CURRENT_ANALYSIS.json](CURRENT_ANALYSIS.json). The earlier age/time comparison remains an archived validation snapshot in [AGE_TIME_REVALIDATION.md](AGE_TIME_REVALIDATION.md).

PH methods reference: [lifelines stratification documentation](https://lifelines.readthedocs.io/en/latest/jupyter_notebooks/Proportional%20hazard%20assumption.html#Stratification).
