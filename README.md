# RAAS Blockers and Clinical Outcomes in COPD ICU Admissions  
*An ICU Hospital Cohort Study of COPD Patients Using MIMIC-IV*

---

## 🔍 Start Here (Analysis Entry Points)

➡️ **ICU COPD cohort construction**: [01_icu_cohort.ipynb](notebooks/01_icu_cohort.ipynb)<br>
➡️ **Cohort and exposure definition**: [02_cohort_and_exposures.ipynb](notebooks/02_cohort_and_exposures.ipynb)<br>
➡️ **Baseline covariates**: [03a_baseline.ipynb](notebooks/03a_baseline.ipynb)<br>
➡️ **Merge exposures**: [03b_merge_exposures.ipynb](notebooks/03b_merge_exposures.ipynb)<br>
➡️ **Outcomes and modeling**: [04a_outcomes_and_modeling.ipynb](notebooks/04a_outcomes_and_modeling.ipynb)<br>
➡️ **RAAS subgroup analyses**: [04b_outcomes_and_modeling_raas_subgroup.ipynb](notebooks/04b_outcomes_and_modeling_raas_subgroups.ipynb)<br>
➡️ **Extended Cox model analyses**: [04c_extended_covariate_cox_model.ipynb](notebooks/04c_extended_covariate_cox_model.ipynb)<br>

📁 **SQL pipelines (BigQuery)**: [sql/](sql/)<br>
📁 **Stepwise short documentation**: [docs/](docs/)<br>
📄 **Analytic framework (PACE)**: [PACE.md](docs/PACE.md)<br>

---

## Technical Snapshot

- **Data**: MIMIC-IV v3.1 (PhysioNet), ICU admissions
- **Cohort**: Adult ICU patients with COPD
- **Exposure**: Pre-ICU RAAS inhibitor use (ACE inhibitors [ACEi] / ARBs)
- **Outcome**: Time-to-in-hospital mortality
- **Methods**:
  - BigQuery SQL for reproducible cohort construction
  - Kaplan–Meier survival analysis
  - Cox proportional hazards regression
  - Sensitivity analyses with extended covariates
- **Tools**: BigQuery, Python (pandas, lifelines), Jupyter

---

## Project Snapshot

- **Population**: ICU-admitted adults with COPD (MIMIC-IV v3.1)
- **Exposure**: Pre-ICU RAAS inhibitor use (ACE inhibitors and/or ARBs)
- **Outcome**: Time to in-hospital mortality
- **Design**: Retrospective observational cohort study
- **Analysis**: Cox proportional hazards regression
- **Key Focus**: Time-to-event analysis of pre-ICU RAAS inhibitor exposure, including comparison of overall RAAS effects and ACE inhibitor vs ARB subclasses
- **Key Finding**: Pre-ICU RAAS inhibitor exposure was associated with lower in-hospital mortality; the association was more pronounced for ACE inhibitors than for ARBs
- **Interpretation**: Observational association; hypothesis-generating

---

## Introduction

Chronic obstructive pulmonary disease (COPD) is a leading cause of morbidity and mortality worldwide and is frequently complicated by cardiovascular comorbidities. Patients with COPD who require intensive care unit (ICU) admission represent a particularly high-risk population, with substantial in-hospital mortality despite advances in supportive care. Identifying clinically meaningful and potentially modifiable factors associated with outcomes in critically ill COPD patients remains an important challenge in both clinical medicine and translational research.

Renin–angiotensin–aldosterone system (RAAS) inhibitors, including angiotensin-converting enzyme inhibitors (ACE inhibitors; ACEi) and angiotensin II receptor blockers (ARBs), are widely prescribed for cardiovascular and metabolic diseases that commonly coexist with COPD. Although these agents are primarily used for cardiovascular protection, increasing evidence suggests that RAAS signaling also plays a significant role in pulmonary pathophysiology and acute lung injury [1,2].

This portfolio project evaluates the association between pre-ICU exposure to RAAS inhibitors and in-hospital mortality among ICU-admitted patients with COPD using a reproducible electronic health record (EHR)–based survival analysis framework applied to the MIMIC-IV database.

---

## Background and Rationale

### Biological rationale: RAAS and lung injury

Beyond its systemic role in blood pressure regulation, the RAAS functions as a local tissue signaling network in the lung. Experimental models of acute lung injury have demonstrated that angiotensin-converting enzyme 2 (ACE2) acts as a critical protective regulator by counterbalancing angiotensin II–mediated injury pathways. Loss of ACE2 leads to increased pulmonary vascular permeability, inflammation, and severe lung failure, whereas restoration of ACE2 activity mitigates lung injury severity [1].

Subsequent mechanistic studies have further shown that excessive angiotensin II signaling through the angiotensin II type 1 receptor (AT1R) is a key driver of acute lung injury. In a landmark in vivo study, SARS coronavirus–induced lung injury was mediated by ACE2 downregulation and augmented angiotensin II–AT1R signaling, and this injury could be attenuated by pharmacologic AT1 receptor blockade using losartan[2]. Together, these studies provide strong biological plausibility linking RAAS dysregulation to severe pulmonary injury, while highlighting potential mechanistic differences between classes of RAAS inhibitors.

Narrative reviews have further proposed that RAAS modulation may influence chronic pulmonary inflammation and airway remodeling in COPD, while emphasizing the lack of randomized evidence in this population [6].

---

### Definition of COPD in EHR data

In this analysis, COPD was defined using International Classification of Diseases (ICD) diagnosis codes recorded during hospital admissions. Specifically, COPD was identified based on established ICD-9 codes (491.*, 492.*, and 496) and ICD-10 codes (J41–J44), which have been widely used and validated in epidemiologic and health services research to identify patients with COPD in administrative and EHR data sources[7,8].

Prior studies have demonstrated that these ICD-based definitions capture clinically meaningful COPD populations with acceptable validity for observational analyses, particularly when the objective is to identify pre-existing chronic lung disease rather than acute exacerbation severity. Given the stability of COPD as a chronic diagnosis and its ascertainment prior to ICU admission, this approach allows for clear temporal ordering between baseline comorbidity status, pre-ICU medication exposure, and subsequent ICU outcomes.

Importantly, COPD represents a chronic pre-existing condition rather than an acute ICU-acquired syndrome, making ICD-based definitions particularly suitable for cohort construction in studies focused on pre-ICU exposures.

---

### Clinical evidence in COPD and hospitalized populations

Consistent with these mechanistic insights, observational studies have suggested that RAAS inhibitors may be associated with improved outcomes in patients with COPD. In a large Veterans Affairs cohort, prior outpatient use of ACE inhibitors or ARBs was associated with lower short-term mortality following hospitalization for acute COPD exacerbations[4]. However, this study was not limited to critically ill patients and evaluated ACE inhibitors and ARBs as a combined exposure.

More recent comparative analyses have highlighted important pharmacological differences between ACE inhibitors and ARBs in COPD populations. In a nationwide cohort study, ARB use was associated with a lower risk of pneumonia and severe COPD exacerbations compared with ACE inhibitor use, suggesting that the two drug classes may have distinct respiratory effects[5].

In hospitalized patients with severe systemic illness, baseline use of RAAS inhibitors has also been associated with improved survival. In a large retrospective cohort of racially diverse patients hospitalized with COVID-19, prior use of ACE inhibitors or ARBs was independently associated with a lower risk of in-hospital mortality after multivariable adjustment[3]. Although this study did not focus on COPD or ICU populations specifically, it provides additional clinical evidence that RAAS modulation may influence outcomes in severe respiratory illness.

---

### Knowledge gaps and study objective

Despite these findings, several important gaps remain. Most existing studies have evaluated RAAS inhibitors as a combined exposure, despite well-recognized pharmacological differences between ACE inhibitors and ARBs. Evidence specific to critically ill patients with COPD—particularly those admitted to the ICU and at high risk of in-hospital mortality—is limited. Moreover, the extent to which associations observed in general hospitalized or non-ICU populations translate to ICU settings with higher illness severity and competing risks remains unclear.

To address these gaps, this analysis investigates whether pre-ICU exposure to RAAS inhibitors is associated with in-hospital mortality among ICU-admitted patients with COPD. In addition to evaluating RAAS inhibitors as a combined exposure, this project explicitly explores potential differences between ACE inhibitor and ARB subclasses using time-to-event modeling. By integrating biologically grounded rationale with rigorous EHR-based survival analysis, this work aims to provide a transparent and reproducible assessment of RAAS inhibition in a high-risk ICU population.

## Research Question

Among adult ICU patients with COPD in MIMIC-IV, is pre-ICU exposure to ACEi or ARB associated with differences in time-to-in-hospital mortality and related clinical outcomes?

---

## Project Structure
````text
mimic-iv-copd-raas-analysis-private/
├── notebooks/        # Stepwise analysis notebooks (00–04c)
│   ├── 00a_setup.ipynb
│   ├── 01b_SQL Pipeline Verification.ipynb
│   ├── 01_icu_cohort.ipynb
│   ├── 02_cohort_and_exposures.ipynb
│   ├── 03a_baseline.ipynb
│   ├── 03b_merge_exposures.ipynb
│   ├── 04a_outcomes_and_modeling.ipynb
│   ├── 04b_outcomes_and_modeling_raas_subgroups.ipynb
│   └── 04c_extended_covariate_cox_model.ipynb
│
├── sql/              # Reproducible BigQuery SQL pipelines
│   ├── 01_extract_base_icu.sql
│   ├── 02_build_cohort_copd.sql
│   ├── 02_exposure_raas*.sql
│   ├── 03_build_baseline.sql
│   ├── 03_merge_exposures.sql
│   └── 04_build_outcomes*.sql
│
├── docs/             # Lightweight documentation (SHORT summaries)
│   ├── 01_icu_cohort_SHORT.md
│   ├── 02_cohort_and_exposures_SHORT.md
│   ├── 03a_baseline_SHORT.md
│   ├── 03b_merge_exposures_SHORT.md
│   ├── 04a_outcomes_and_modeling_SHORT.md
│   ├── 04b_outcomes_and_modeling_raas_subgroups_SHORT.md
│   ├── 04c_extended_covariate_cox_model_SHORT.md
│   └── PACE.md
│
├── data/             # Local analysis artifacts (excluded or minimal)
│   ├── interim/
│   └── processed/
│
├── .github/          # Repository configuration
├── .gitignore
└── README.md

````

## Methods Overview

Covariate selection was guided by a pre-specified conceptual causal framework, considering baseline demographics, cardiovascular comorbidities, and illness severity as potential confounders of the association between RAAS inhibitor exposure and in-hospital mortality.

Cohort construction, exposure definition, baseline covariate assembly, and outcome derivation were implemented using a combination of SQL (BigQuery-compatible) and Python-based processing.

The analytic pipeline was designed to be reproducible, with core cohort and outcome tables generated via project-specific SQL scripts and downstream modeling performed in structured notebooks.

Modeling choices were defined prior to outcome modeling and applied consistently across analyses.

---

## Results

The results summarized below highlight the primary directional findings; detailed estimates and diagnostic outputs are provided in the accompanying notebooks.

### Cohort characteristics

The final analytic cohort consisted of ICU-admitted patients with a diagnosis of COPD identified from the MIMIC-IV database. Baseline characteristics differed between patients with and without pre-ICU exposure to RAAS inhibitors, reflecting the high prevalence of cardiovascular comorbidities among RAAS inhibitor users. These differences were addressed through multivariable adjustment in subsequent survival models.

### Association between RAAS inhibitor use and in-hospital mortality

In time-to-event analyses, pre-ICU exposure to RAAS inhibitors was associated with a lower risk of in-hospital mortality compared with no RAAS inhibitor exposure. This association was observed in Kaplan–Meier survival curves and remained directionally consistent after adjustment for demographic factors, illness severity, and major comorbidities in Cox proportional hazards models.

### ACE inhibitor and ARB subclass analyses

When RAAS inhibitors were evaluated by drug class, ACE inhibitor use demonstrated a more pronounced association with reduced in-hospital mortality compared with ARB use. Although confidence intervals overlapped and causal inference cannot be established, this pattern was consistent across multiple model specifications. These findings suggest potential heterogeneity within RAAS inhibitor subclasses that warrants further investigation.

### Sensitivity analyses

The association between RAAS inhibitor exposure and lower in-hospital mortality was attenuated but remained directionally consistent in sensitivity analyses incorporating additional covariates, including ICU type. Model diagnostics did not identify major violations of proportional hazards assumptions, supporting the robustness of the primary findings within the limitations of an observational study.

---

### Key Finding:

Pre-ICU RAAS inhibitor exposure was associated with lower in-hospital mortality, with a more pronounced association for ACE inhibitors than for ARBs. This association was attenuated after further adjustment for ICU type and acute illness severity, suggesting that differences in ICU-level case mix and organ dysfunction may contribute to the observed signal.

---

## Discussion

The findings of this analysis should be interpreted in the context of prior observational studies, most notably the Veterans Affairs cohort reported by Mortensen et al., which demonstrated lower short-term mortality among patients hospitalized for acute COPD exacerbations who were receiving ACE inhibitors or ARBs prior to admission[4]. While that study provided important early evidence linking RAAS inhibition to improved outcomes in COPD, it differed from the present analysis in several key aspects. First, the Mortensen cohort was not restricted to critically ill patients and did not specifically focus on ICU-admitted populations, in whom illness severity, competing risks, and treatment intensity differ substantially. Second, ACE inhibitors and ARBs were evaluated as a combined exposure, precluding assessment of potential class-specific effects. In contrast, the current analysis focuses explicitly on ICU-admitted patients with COPD and explores ACE inhibitors and ARBs both as a combined exposure and as separate subclasses, motivated by established mechanistic differences in RAAS signaling[1,2] and emerging comparative evidence in COPD populations[5]. These distinctions allow the present study to address clinically relevant questions that were not directly examined in earlier work, while extending existing observational evidence into a higher-risk ICU setting.

---

## Limitations and interpretation

This analysis is observational and cannot establish causal effects of RAAS inhibitors on mortality. Despite strict temporal ordering of exposure before ICU admission and extensive covariate adjustment, residual confounding by indication and unmeasured severity factors may remain. RAAS inhibitor use likely reflects underlying cardiovascular comorbidity and outpatient care patterns that are not fully captured in EHR data. Accordingly, the findings should be interpreted as evidence of association rather than causation, and primarily as hypothesis-generating results that motivate further prospective or quasi-experimental studies.

---

## Data Source and Compliance

This project uses data from the Medical Information Mart for Intensive Care IV (MIMIC-IV) database (version 3.1), which is maintained by the MIT Laboratory for Computational Physiology and made available via PhysioNet.

According to the PhysioNet data use requirements, the following citation should be used when referencing MIMIC-IV:
Johnson A., Bulgarelli L., Pollard T., Gow B., Moody B., Horng S., Celi L.A., & Mark R. (2024). *MIMIC-IV (version 3.1)*. PhysioNet. RRID:SCR_007345. https://doi.org/10.13026/kpb9-mt58.

Access to the MIMIC-IV database was granted following completion of the required training and approval under the PhysioNet data use agreement.  
This repository contains no patient-level data. All analyses were conducted within approved MIMIC-IV environments, and only code and aggregate descriptions are shared.

---

## References

1. Imai Y, Kuba K, Rao S, et al. Angiotensin-converting enzyme 2 protects from severe acute lung failure. *Nature*. 2005;436:112–116. doi:10.1038/nature03712.

2. Kuba K, Imai Y, Rao S, et al. A crucial role of angiotensin converting enzyme 2 (ACE2) in SARS coronavirus–induced lung injury. *Nature Medicine*. 2005;11:875–879. doi:10.1038/nm1267.

3. Khodneva Y, Malla G, Clarkson S, et al. What is the association of renin–angiotensin–aldosterone system inhibitors with COVID-19 outcomes: retrospective study of racially diverse patients? *BMJ Open*. 2022;12:e053961. doi:10.1136/bmjopen-2021-053961.

4. Mortensen EM, Pugh MJ, Copeland LA, et al. Impact of statins and angiotensin-converting enzyme inhibitors on mortality after COPD exacerbations. *Respiratory Research*. 2009;10:45. doi:10.1186/1465-9921-10-45.

5. Lai CC, Wang YH, Wang CY, et al. Comparative effects of angiotensin-converting enzyme inhibitors and angiotensin II receptor blockers on the risk of pneumonia and severe exacerbations in patients with COPD. *International Journal of Chronic Obstructive Pulmonary Disease*. 2018;13:867–874. doi:10.2147/COPD.S154803.

6. Vasileiadis I, et al. Angiotensin-converting enzyme inhibitors and angiotensin receptor blockers: A promising medication for chronic obstructive pulmonary disease. *COPD: Journal of Chronic Obstructive Pulmonary Disease*. 2018;15(2):148–156. doi:10.1080/15412555.2018.1430498.

7. Mapel DW, Hurley JS, Frost FJ, Petersen HV, Picchi MA, Coultas DB. 
Validity of a COPD diagnosis in administrative data. 
*International Journal of Chronic Obstructive Pulmonary Disease*. 2011;6:273–281. 
doi:10.2147/COPD.S17851.

8. Stein BD, Bautista A, Schumock GT, et al. 
Identifying patients with chronic obstructive pulmonary disease using administrative data. 
*Chest*. 2012;141(3):605–613. 
doi:10.1378/chest.11-2442.