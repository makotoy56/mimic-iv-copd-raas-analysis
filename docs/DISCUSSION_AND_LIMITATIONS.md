# Discussion and Limitations

Current estimates below use the 2026-11-18 admission-age and continuous follow-up corrections; see [the validation report](AGE_TIME_REVALIDATION.md). Current figures and the local report have been regenerated. Independent Cox calculation records are linked from [validation notes](VALIDATION_NOTES.md).

This document contains the extended interpretation and limitation discussion for the README. The findings should be read as observational, hypothesis-generating associations rather than causal estimates.

## Interpretation of Findings

Pre-ICU RAAS inhibitor exposure was associated with lower observed in-hospital mortality among ICU-admitted COPD patients. The association was visible in Kaplan-Meier analyses and in the primary and core Cox models. It was sensitive to additional adjustment; the exploratory ICU/CHF/SOFA-stratified point estimate crossed above 1 with a confidence interval including 1.

ACEi-only and ARB-only prescription-order groups are each compared with neither qualifying order. Records with both class flags positive are excluded from this subclass analysis. The main analysis reports no direct ACEi-versus-ARB contrast or interaction test. Different point estimates, or one p-value below 0.05 and the other above it, do not establish a difference between the classes.

Exploratory SOFA-containing models produced different estimates from the age/sex/era primary model. Because first-day severity can use information after follow-up begins, this attenuation cannot be attributed solely to control of pre-ICU confounding. `sofa_score` comes from `mimiciv_3_1_derived.first_day_sofa`. Its published definition can use information through 24 hours after ICU entry, while follow-up starts at ICU entry. All SOFA-containing core, ICU-adjusted and CHF/SOFA-stratified models are therefore exploratory sensitivity analyses that can use post-start information, not baseline-only severity adjustment. Temporal leakage or adjustment for post-exposure information may affect interpretation; its impact has not been quantified here. The primary age/sex model with era strata is unchanged. The separate exploratory 24-hour landmark supplement changes the population and follow-up origin; it does not reconstruct pre-ICU severity or independently verify component measurement times.

The unpenalized extended core Cox estimate (HR 0.833, 95% CI 0.673-1.030; p = 0.09122) did not meet conventional statistical significance. The further attenuation in penalized and ICU-type-adjusted specifications reinforces the sensitivity of the association to model specification and case-mix adjustment.

## Comparison With Prior Studies

The findings are directionally consistent with prior observational COPD literature, including the Veterans Affairs cohort reported by Mortensen et al., which found lower observed short-term mortality among patients hospitalized for acute COPD exacerbations who were receiving ACE inhibitors or ARBs before admission.

This project extends that general research question into an ICU COPD cohort, where illness severity, treatment intensity, and competing clinical risks differ from general hospitalized COPD populations. It also evaluates ACE inhibitors and ARBs both as a combined exposure and as separate subclasses, motivated by mechanistic RAAS literature and comparative COPD studies.

Differences between this analysis and prior studies should be interpreted carefully. MIMIC-IV is a single-center critical care database, the exposure definition is based on inpatient medication orders before ICU admission, and the outcome is in-hospital mortality after ICU admission. These design choices improve reproducibility within the database but may limit comparability with studies based on outpatient medication lists or broader hospitalized populations.

## Limitations

Age is approximated from admission year and the anchor year. Admissions whose anchor age is the aggregated 91 group retain additional age uncertainty. Corrected core/ICU models also retain PH violations for some covariates; these are not resolved by the age/time corrections.

This analysis is observational and cannot establish causality. Prescription flags are defined by records with start time before or at ICU entry, but the first-day severity covariate need not precede follow-up or exposure. Residual confounding and post-exposure adjustment remain concerns.

RAAS inhibitor use likely reflects underlying cardiovascular comorbidity, chronic disease management, outpatient access to care, prescribing preferences, and medication continuation or withholding decisions that are not fully captured in EHR data.

Exposure flags identify inpatient prescription records in the same hospital admission with `starttime <= intime`. They do not verify actual administration, continued treatment at ICU entry, adherence or concurrent ACEi/ARB administration. Both positive class flags mean qualifying records for both classes; they do not establish simultaneous treatment. Neither means no qualifying prescription record for either class, not proven absence of all medication use. Outpatient use, dose, duration and indication are also not directly measured.

COPD status is identified using ICD-9 and ICD-10 diagnosis codes recorded during hospitalization. This supports reproducible EHR cohort construction but may introduce misclassification compared with spirometry-confirmed COPD.

The analysis uses MIMIC-IV ICU admissions from a specific health system. Results may not generalize to other hospitals, non-ICU COPD populations, outpatient cohorts, or current prescribing contexts.

Live discharge was treated as censoring in the primary Cox analysis. Because discharge may alter the opportunity to observe in-hospital death, this censoring assumption should be considered when interpreting the survival estimates. The [separate post hoc supplementary analyses](SURVIVAL_SENSITIVITY_SUPPLEMENTS.md) estimate unadjusted Aalen–Johansen cumulative incidence with live discharge as a competing event and fit cause-specific death and live-discharge Cox models. These analyses answer different questions from the original discharge-censored main models and do not replace them. No Fine–Gray model is reported.

Each analytic record represents a qualifying hospital admission anchored to its first ICU stay. Patients may contribute more than one qualifying admission. The original main Cox models use ordinary admission-level inference without patient clustering or frailty. The separate patient-cluster supplement uses sandwich inference, retaining the corresponding original point estimates while allowing confidence intervals and p-values to change. It does not remove between-admission confounding or provide a frailty model.

The fitted subclass coefficients each use neither qualifying order as reference. A direct between-class contrast with its covariance and uncertainty would require a separate analysis; none is reported here.

## Interpretation scope

The project demonstrates a transparent clinical data analysis workflow using MIMIC-IV, BigQuery SQL, Python, Jupyter, and Quarto. The clinical finding is best summarized as an observational association: pre-ICU RAAS inhibitor exposure was associated with lower observed in-hospital mortality among ICU-admitted COPD patients, with separate subclass-versus-neither estimates and no direct between-class test.

These findings are hypothesis-generating and cannot establish causality. Prospective, quasi-experimental, or externally validated analyses would be needed before making clinical conclusions about RAAS inhibitor treatment effects in ICU COPD populations.

The follow-up workflow pools rare ICU types by admission count and adds exploratory CHF/SOFA baseline-hazard strata. Core PH diagnostics no longer flagged the remaining covariates in that sensitivity model. The ICU-stratified sensitivity model still flagged diabetes, and 1,118 strata include sparse groups; it must not be presented as a universally PH-compliant replacement. See [current estimates and diagnostics](RESULTS_SUMMARY.md).
