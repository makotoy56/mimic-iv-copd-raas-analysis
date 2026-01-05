-- 02_build_cohort_copd.sql
-- Build COPD ICU cohort by joining ICU stays with COPD diagnoses

CREATE OR REPLACE TABLE `mimic-iv-portfolio.copd_raas.cohort_copd` AS
WITH copd_hadm AS (
  SELECT DISTINCT
    d.subject_id,
    d.hadm_id
  FROM `physionet-data.mimiciv_3_1_hosp.diagnoses_icd` AS d
  WHERE
    -- COPD in ICD-9 (e.g., 491*, 492*, 496)
    (d.icd_version = 9 AND REGEXP_CONTAINS(d.icd_code, r'^491|^492|^496'))
    OR
    -- COPD in ICD-10 (e.g., J41*, J42, J43*, J44*)
    (d.icd_version = 10 AND REGEXP_CONTAINS(d.icd_code, r'^J41|^J42|^J43|^J44'))
),

copd_icu AS (
  SELECT
    i.*
  FROM `mimic-iv-portfolio.copd_raas.cohort_icu` AS i
  JOIN copd_hadm AS c
    ON i.subject_id = c.subject_id
   AND i.hadm_id  = c.hadm_id
)

SELECT
  subject_id,
  hadm_id,
  stay_id,
  intime,
  outtime,
  icu_los,
  age,
  gender,
  anchor_year,
  anchor_year_group
FROM copd_icu;