# Discussion and Limitations

Current estimates below use the 2026-11-18 admission-age and continuous follow-up corrections; see [the validation report](AGE_TIME_REVALIDATION.md). Current figures and the local report have been regenerated. SAS validation is pending an independent rerun.

This document contains the extended interpretation and limitation discussion for the README. The findings should be read as observational, hypothesis-generating associations rather than causal estimates.

## Interpretation of Findings

Pre-ICU RAAS inhibitor exposure was associated with lower observed in-hospital mortality among ICU-admitted COPD patients. The association was visible in Kaplan-Meier analyses and in the primary and core Cox models. It was sensitive to additional adjustment; the exploratory ICU/CHF/SOFA-stratified point estimate crossed above 1 with a confidence interval including 1.

When RAAS inhibitors were evaluated by subclass, ACE inhibitor exposure showed a more pronounced association with lower observed mortality than ARB exposure. This pattern is consistent with the rationale for evaluating RAAS inhibitor subclasses separately, but it should not be interpreted as evidence that ACE inhibitors are clinically superior to ARBs in this setting.

Sensitivity analyses attenuated the association after additional adjustment, including ICU type and acute illness severity measures. This suggests that ICU-level case mix, organ dysfunction, and clinical severity may contribute to the observed signal.

The unpenalized extended core Cox estimate (HR 0.833, 95% CI 0.673-1.030; p = 0.09122) did not meet conventional statistical significance. The further attenuation in penalized and ICU-type-adjusted specifications reinforces the sensitivity of the association to model specification and case-mix adjustment.

## Comparison With Prior Studies

The findings are directionally consistent with prior observational COPD literature, including the Veterans Affairs cohort reported by Mortensen et al., which found lower observed short-term mortality among patients hospitalized for acute COPD exacerbations who were receiving ACE inhibitors or ARBs before admission.

This project extends that general research question into an ICU COPD cohort, where illness severity, treatment intensity, and competing clinical risks differ from general hospitalized COPD populations. It also evaluates ACE inhibitors and ARBs both as a combined exposure and as separate subclasses, motivated by mechanistic RAAS literature and comparative COPD studies.

Differences between this analysis and prior studies should be interpreted carefully. MIMIC-IV is a single-center critical care database, the exposure definition is based on inpatient medication orders before ICU admission, and the outcome is in-hospital mortality after ICU admission. These design choices improve reproducibility within the database but may limit comparability with studies based on outpatient medication lists or broader hospitalized populations.

## Limitations

Age is approximated from admission year and the anchor year. Admissions whose anchor age is the aggregated 91 group retain additional age uncertainty. Corrected core/ICU models also retain PH violations for some covariates; these are not resolved by the age/time corrections.

This analysis is observational and cannot establish causality. Despite strict temporal ordering of exposure before ICU admission and extensive covariate adjustment, residual confounding by indication and unmeasured severity factors may remain.

RAAS inhibitor use likely reflects underlying cardiovascular comorbidity, chronic disease management, outpatient access to care, prescribing preferences, and medication continuation or withholding decisions that are not fully captured in EHR data.

The exposure definition uses inpatient prescription orders before or at ICU admission. It does not directly measure outpatient chronic use, adherence, dose, duration, medication discontinuation before hospitalization, or patient-level indication for RAAS inhibitor therapy.

COPD status is identified using ICD-9 and ICD-10 diagnosis codes recorded during hospitalization. This supports reproducible EHR cohort construction but may introduce misclassification compared with spirometry-confirmed COPD.

The analysis uses MIMIC-IV ICU admissions from a specific health system. Results may not generalize to other hospitals, non-ICU COPD populations, outpatient cohorts, or current prescribing contexts.

Live discharge was treated as censoring in the primary Cox analysis. Because discharge may alter the opportunity to observe in-hospital death, this censoring assumption should be considered when interpreting the survival estimates. A competing-risk framework was not implemented.

Each analytic record represents a qualifying hospital admission anchored to its first ICU stay. Patients may contribute more than one qualifying admission, and the Cox models do not account for within-patient correlation with a clustering or frailty term.

Subclass comparisons between ACE inhibitors and ARBs are especially hypothesis-generating. Patients receiving these medication classes may differ in contraindications, comorbidities, prescribing history, and tolerance of therapy. Observed differences between ACE inhibitor and ARB groups should be treated as signals for future study rather than causal evidence.

## Bottom Line

The project demonstrates a transparent clinical data analysis workflow using MIMIC-IV, BigQuery SQL, Python, Jupyter, and SAS. The clinical finding is best summarized as an observational association: pre-ICU RAAS inhibitor exposure was associated with lower observed in-hospital mortality among ICU-admitted COPD patients, with a more pronounced observed association for ACE inhibitors than for ARBs.

These findings are hypothesis-generating and cannot establish causality. Prospective, quasi-experimental, or externally validated analyses would be needed before making clinical conclusions about RAAS inhibitor treatment effects in ICU COPD populations.

The follow-up workflow pools rare ICU types by admission count and adds exploratory CHF/SOFA baseline-hazard strata. Core PH diagnostics no longer flagged the remaining covariates in that sensitivity model. The ICU-stratified sensitivity model still flagged diabetes, and 1,118 strata include sparse groups; it must not be presented as a universally PH-compliant replacement. See [current estimates and diagnostics](RESULTS_SUMMARY.md).
