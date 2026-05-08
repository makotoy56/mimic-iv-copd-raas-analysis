# Study Background

This document contains the extended biologic and literature rationale for the portfolio README. It is intentionally separated from the README so the project entry point stays focused on the clinical data analysis workflow.

## RAAS Biology and Lung Disease Rationale

RAAS signaling has biologic relevance to lung injury, pulmonary inflammation, and vascular regulation. Experimental studies implicate ACE2 and angiotensin II signaling in acute lung injury pathways, including work showing that ACE2 can protect against severe acute lung failure and may influence lung injury mechanisms in viral respiratory illness.

In this context, ACE inhibitors and angiotensin receptor blockers are clinically relevant because they act on related but distinct points of the RAAS pathway. ACE inhibitors reduce conversion of angiotensin I to angiotensin II, while ARBs block angiotensin II receptor signaling. These differences motivate cautious subclass analysis rather than treating RAAS inhibitors as a fully homogeneous exposure.

COPD is a chronic inflammatory lung disease with frequent cardiovascular comorbidity. Reviews have proposed that RAAS modulation may influence chronic pulmonary inflammation, airway remodeling, and respiratory outcomes in COPD. These mechanisms are plausible but do not establish that RAAS inhibitor exposure improves outcomes in ICU-admitted COPD patients.

## Prior Observational Evidence

Prior observational clinical studies have reported favorable outcomes among COPD or severe respiratory illness populations exposed to ACE inhibitors or ARBs. For example, studies of patients hospitalized for acute COPD exacerbations reported lower observed short-term mortality among patients receiving ACE inhibitors or ARBs before admission.

Other observational work has examined RAAS inhibitors in severe respiratory illness populations, including COVID-19 cohorts. These studies help motivate the research question but are not directly interchangeable with an ICU COPD cohort because disease context, treatment intensity, confounding structure, and outcome timing may differ.

Comparative COPD research also suggests that ACE inhibitors and ARBs may have distinct respiratory associations. This supports evaluating ACE inhibitor and ARB exposure both together and separately, while retaining cautious interpretation because observational subclass comparisons may be especially vulnerable to confounding by indication, prescribing patterns, and comorbidity profiles.

## Rationale for This Analysis

This project addresses a focused evidence gap: whether pre-ICU RAAS inhibitor exposure is associated with in-hospital mortality among ICU-admitted COPD patients in MIMIC-IV, and whether ACE inhibitor and ARB subclasses show different observed associations.

COPD was defined using established ICD-9 and ICD-10 diagnosis codes recorded during hospitalization, consistent with prior administrative and EHR-based COPD research. This supports reproducible cohort construction and clear temporal ordering between chronic COPD status, pre-ICU medication exposure, and ICU outcomes.

The analysis remains hypothesis-generating. It evaluates observational associations in EHR data and cannot establish causality.

## References

1. Imai Y, Kuba K, Rao S, et al. Angiotensin-converting enzyme 2 protects from severe acute lung failure. *Nature*. 2005;436:112-116. doi:10.1038/nature03712.

2. Kuba K, Imai Y, Rao S, et al. A crucial role of angiotensin converting enzyme 2 (ACE2) in SARS coronavirus-induced lung injury. *Nature Medicine*. 2005;11:875-879. doi:10.1038/nm1267.

3. Khodneva Y, Malla G, Clarkson S, et al. What is the association of renin-angiotensin-aldosterone system inhibitors with COVID-19 outcomes: retrospective study of racially diverse patients? *BMJ Open*. 2022;12:e053961. doi:10.1136/bmjopen-2021-053961.

4. Mortensen EM, Pugh MJ, Copeland LA, et al. Impact of statins and angiotensin-converting enzyme inhibitors on mortality after COPD exacerbations. *Respiratory Research*. 2009;10:45. doi:10.1186/1465-9921-10-45.

5. Lai CC, Wang YH, Wang CY, et al. Comparative effects of angiotensin-converting enzyme inhibitors and angiotensin II receptor blockers on the risk of pneumonia and severe exacerbations in patients with COPD. *International Journal of Chronic Obstructive Pulmonary Disease*. 2018;13:867-874. doi:10.2147/COPD.S154803.

6. Vasileiadis I, et al. Angiotensin-converting enzyme inhibitors and angiotensin receptor blockers: A promising medication for chronic obstructive pulmonary disease. *COPD: Journal of Chronic Obstructive Pulmonary Disease*. 2018;15(2):148-156. doi:10.1080/15412555.2018.1430498.

7. Mapel DW, Hurley JS, Frost FJ, Petersen HV, Picchi MA, Coultas DB. Validity of a COPD diagnosis in administrative data. *International Journal of Chronic Obstructive Pulmonary Disease*. 2011;6:273-281. doi:10.2147/COPD.S17851.

8. Stein BD, Bautista A, Schumock GT, et al. Identifying patients with chronic obstructive pulmonary disease using administrative data. *Chest*. 2012;141(3):605-613. doi:10.1378/chest.11-2442.
