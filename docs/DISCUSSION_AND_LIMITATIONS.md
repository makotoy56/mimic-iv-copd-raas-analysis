# Discussion and Limitations

This document contains the extended interpretation and limitation discussion for the README. The findings should be read as observational, hypothesis-generating associations rather than causal estimates.

## Interpretation of Findings

Pre-ICU RAAS inhibitor exposure was associated with lower observed in-hospital mortality among ICU-admitted COPD patients. The association was visible in Kaplan-Meier analyses and remained directionally consistent in adjusted Cox proportional hazards models.

When RAAS inhibitors were evaluated by subclass, ACE inhibitor exposure showed a more pronounced association with lower observed mortality than ARB exposure. This pattern is consistent with the rationale for evaluating RAAS inhibitor subclasses separately, but it should not be interpreted as evidence that ACE inhibitors are clinically superior to ARBs in this setting.

Sensitivity analyses attenuated the association after additional adjustment, including ICU type and acute illness severity measures. This suggests that ICU-level case mix, organ dysfunction, and clinical severity may contribute to the observed signal.

## Comparison With Prior Studies

The findings are directionally consistent with prior observational COPD literature, including the Veterans Affairs cohort reported by Mortensen et al., which found lower observed short-term mortality among patients hospitalized for acute COPD exacerbations who were receiving ACE inhibitors or ARBs before admission.

This project extends that general research question into an ICU COPD cohort, where illness severity, treatment intensity, and competing clinical risks differ from general hospitalized COPD populations. It also evaluates ACE inhibitors and ARBs both as a combined exposure and as separate subclasses, motivated by mechanistic RAAS literature and comparative COPD studies.

Differences between this analysis and prior studies should be interpreted carefully. MIMIC-IV is a single-center critical care database, the exposure definition is based on inpatient medication orders before ICU admission, and the outcome is in-hospital mortality after ICU admission. These design choices improve reproducibility within the database but may limit comparability with studies based on outpatient medication lists or broader hospitalized populations.

## Limitations

This analysis is observational and cannot establish causality. Despite strict temporal ordering of exposure before ICU admission and extensive covariate adjustment, residual confounding by indication and unmeasured severity factors may remain.

RAAS inhibitor use likely reflects underlying cardiovascular comorbidity, chronic disease management, outpatient access to care, prescribing preferences, and medication continuation or withholding decisions that are not fully captured in EHR data.

The exposure definition uses inpatient prescription orders before or at ICU admission. It does not directly measure outpatient chronic use, adherence, dose, duration, medication discontinuation before hospitalization, or patient-level indication for RAAS inhibitor therapy.

COPD status is identified using ICD-9 and ICD-10 diagnosis codes recorded during hospitalization. This supports reproducible EHR cohort construction but may introduce misclassification compared with spirometry-confirmed COPD.

The analysis uses MIMIC-IV ICU admissions from a specific health system. Results may not generalize to other hospitals, non-ICU COPD populations, outpatient cohorts, or current prescribing contexts.

Subclass comparisons between ACE inhibitors and ARBs are especially hypothesis-generating. Patients receiving these medication classes may differ in contraindications, comorbidities, prescribing history, and tolerance of therapy. Observed differences between ACE inhibitor and ARB groups should be treated as signals for future study rather than causal evidence.

## Bottom Line

The project demonstrates a transparent clinical data analysis workflow using MIMIC-IV, BigQuery SQL, Python, Jupyter, and SAS. The clinical finding is best summarized as an observational association: pre-ICU RAAS inhibitor exposure was associated with lower observed in-hospital mortality among ICU-admitted COPD patients, with a more pronounced observed association for ACE inhibitors than for ARBs.

These findings are hypothesis-generating and cannot establish causality. Prospective, quasi-experimental, or externally validated analyses would be needed before making clinical conclusions about RAAS inhibitor treatment effects in ICU COPD populations.
