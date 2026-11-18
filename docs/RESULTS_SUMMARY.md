# Current Results (2026-11-18)

Analysis version: `admission_age_elapsed_time_los_v2`. These estimates and the figures use regenerated analysis tables and continuous elapsed follow-up.

The cohort contains 11,964 admissions and 1,692 in-hospital deaths. Refined primary RAAS HR: 0.732 (0.592–0.904), p=0.00383. Extended core RAAS HR: 0.833 (0.673–1.030), p=0.09122.

| Model | RAAS HR (95% CI) | p |
| --- | --- | ---: |
| Primary refined | 0.732 (0.592–0.904) | 0.00383 |
| Extended core | 0.833 (0.673–1.030) | 0.09122 |
| Core + L2 (0.1) | 0.886 (0.766–1.025) | 0.10376 |
| ICU adjusted (rare types pooled) | 0.958 (0.772–1.187) | 0.69262 |
| ICU pooled + L2 (0.01) | 0.910 (0.743–1.115) | 0.36324 |
| Core CHF/SOFA strata (exploratory) | 0.830 (0.666–1.034) | 0.09666 |
| ICU CHF/SOFA/type strata (exploratory) | 1.127 (0.880–1.443) | 0.34395 |

Subclass estimates compare ACEi or ARB monotherapy with no exposure; dual exposure is excluded.

| Subclass | HR (95% CI) | p |
| --- | --- | ---: |
| ACEi | 0.683 (0.521–0.894) | 0.00550 |
| ARB | 0.805 (0.573–1.131) | 0.21116 |

## Diagnostics and interpretation

The core and pooled ICU models retain their original covariate structure. Additional exploratory models stratify baseline hazards by era, CHF and exact SOFA; the ICU variant also stratifies by pooled ICU type. These models do not estimate CHF or SOFA coefficients. They supplement the primary analysis and are not chosen by searching for non-significant PH tests.

| Model | Number of strata | Rank PH tests with p<0.05 | Model warnings |
| --- | ---: | --- | --- |
| Primary refined | 5 | None detected | None |
| Extended core | 5 | chf (<0.00001), sofa_score (0.01924) | None |
| Core + L2 (0.1) | 5 | chf (0.00126) | None |
| ICU adjusted (rare types pooled) | 5 | chf (0.00008), sofa_score (0.00157) | None |
| ICU pooled + L2 (0.01) | 5 | chf (0.00018), sofa_score (0.00318) | None |
| Core CHF/SOFA strata (exploratory) | 191 | None detected | None |
| ICU CHF/SOFA/type strata (exploratory) | 1118 | diabetes (0.02879) | None |

A non-significant PH test does not establish that the PH assumption is true. The exploratory ICU-stratified RAAS point estimate is above 1 while its confidence interval includes 1, demonstrating sensitivity to adjustment structure. The ICU-stratified model retains a diabetes PH flag, so the diagnostic issues are not universally resolved. Stratified models permit different baseline hazards for the stratifying covariates; their estimates are conditional on these strata, some of which are sparse. The sensitivity specifications are exploratory responses to diagnostics in this dataset.

Rare ICU labels with fewer than 50 admissions are pooled using admission counts alone, independently of outcome. The pooled labels are: Intensive Care Unit (ICU), Medicine, PACU, Surgery/Trauma, Surgery/Vascular/Intermediate.

This observational admission-level analysis retains discharge censoring and does not account for within-patient correlation or implement competing risks. Year-based age remains approximate, especially for the anchor-age 91 group. Residual confounding remains possible.

## Reproducibility checks

Six unpenalized Cox specifications (40 coefficients) were independently recalculated with statsmodels PHReg using matched complete cases, era/additional strata and Efron ties. Coefficients, HRs, confidence-interval endpoints and p-values matched the lifelines reference within an absolute tolerance of 1e-4. The saved comparison is bound to this exact aggregate analysis snapshot by its reference hash. See [the calculation record](INDEPENDENT_COX_CROSSCHECK.json) and [the scope and limitations](INDEPENDENT_REVALIDATION.md).

This checks a separate statistical implementation on the same corrected model inputs. Source-SQL extraction is evaluated separately. Penalized fits, PH diagnostics, patient clustering, competing risks and causal validity are not established by this numerical comparison.

The reproducible workflow covers authorized MIMIC source access, version-controlled BigQuery extraction and cohort construction, explicit model-column retrieval, Python modeling, independent numerical comparison, figure generation and Quarto reporting. Only aggregate results are published; no external analysis-service upload is part of this workflow. See [the full reproduction steps](https://github.com/makotoy56/mimic-iv-copd-raas-analysis/blob/main/REPRODUCIBILITY.md).

The refreshed figures contain aggregate results only. Full estimates and PH p-values are in [CURRENT_ANALYSIS.json](CURRENT_ANALYSIS.json). The earlier age/time comparison remains an archived validation snapshot in [AGE_TIME_REVALIDATION.md](AGE_TIME_REVALIDATION.md).

PH methods reference: [lifelines stratification documentation](https://lifelines.readthedocs.io/en/latest/jupyter_notebooks/Proportional%20hazard%20assumption.html#Stratification).
