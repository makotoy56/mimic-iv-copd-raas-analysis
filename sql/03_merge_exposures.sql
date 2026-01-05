-- 03_merge_exposures.sql
-- Merge COPD ICU cohort with detailed RAAS exposure flags
-- Input tables:
--   mimic-iv-portfolio.copd_raas.cohort_copd
--   mimic-iv-portfolio.copd_raas.cohort_copd_raas_detailed
-- Output table:
--   mimic-iv-portfolio.copd_raas.cohort_copd_with_raas

CREATE OR REPLACE TABLE `mimic-iv-portfolio.copd_raas.cohort_copd_with_raas` AS
SELECT
  c.*,
  r.acei_pre_icu,
  r.arb_pre_icu,
  r.raas_any_pre_icu,
  r.raas_both_pre_icu,
  r.exposure_group_4cat,
  r.exposure_group_3cat_monotherapy,
  r.is_monotherapy
FROM `mimic-iv-portfolio.copd_raas.cohort_copd` AS c
LEFT JOIN `mimic-iv-portfolio.copd_raas.cohort_copd_raas_detailed` AS r
USING (subject_id, hadm_id, stay_id);