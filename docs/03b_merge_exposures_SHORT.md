# 03b - RAAS Exposure Definition and Merging (SHORT)

This notebook constructs the final analysis-ready dataset by merging the COPD ICU
cohort with detailed pre-ICU RAAS inhibitor exposure flags.

This step constructs the standardized cohort table `copd_raas.cohort_copd_with_raas`, which serves as the common input for downstream survival analyses (04a–04c), using the SQL script `03_merge_exposures.sql`.
- It starts from the COPD ICU cohort (`copd_raas.cohort_copd`) and enriches each ICU stay with detailed pre-ICU RAAS inhibitor exposure flags by left-joining `copd_raas.cohort_copd_raas_detailed` on ICU stay identifiers.
- The merged exposure variables include:
  - ACE inhibitor (ACEi) use before or at ICU admission
  - Angiotensin receptor blocker (ARB) use before or at ICU admission
  - Any RAAS inhibitor use, dual exposure, and mutually exclusive exposure categories for subgroup analyses
  

Specifically, it integrates medication-derived indicators to define mutually
exclusive exposure categories, including ACE inhibitor (ACEi) use, angiotensin
receptor blocker (ARB) use, combined RAAS inhibitor exposure, and non-exposure.

All RAAS inhibitor exposure variables are defined strictly before or at ICU
admission to preserve temporal ordering and minimize the risk of reverse
causation.

The resulting dataset provides a standardized and interpretable exposure framework
used consistently across all downstream survival analyses (04a–04c).