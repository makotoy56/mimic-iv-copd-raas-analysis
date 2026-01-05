-- 01_extract_base_icu.sql
-- Build a base adult ICU cohort from MIMIC-IV v3.1 (first ICU stay per hospital admission)

CREATE OR REPLACE TABLE `mimic-iv-portfolio.copd_raas.cohort_icu` AS
WITH base_stays AS (
  SELECT
    i.subject_id,
    i.hadm_id,
    i.stay_id,
    i.intime,
    i.outtime,
    -- ICU length of stay in days (continuous)
    DATETIME_DIFF(i.outtime, i.intime, HOUR) / 24.0 AS icu_los
  FROM `physionet-data.mimiciv_3_1_icu.icustays` AS i
),

with_age AS (
  SELECT
    b.subject_id,
    b.hadm_id,
    b.stay_id,
    b.intime,
    b.outtime,
    b.icu_los,
    p.gender,
    p.anchor_age AS age,
    p.anchor_year,
    p.anchor_year_group
  FROM base_stays AS b
  JOIN `physionet-data.mimiciv_3_1_hosp.patients` AS p
    ON b.subject_id = p.subject_id
),

-- Keep only adults (age >= 18) and the first ICU stay per subject_id + hadm_id
adult_first_icu AS (
  SELECT *
  FROM (
    SELECT
      w.*,
      ROW_NUMBER() OVER (
        PARTITION BY w.subject_id, w.hadm_id
        ORDER BY w.intime
      ) AS rn
    FROM with_age AS w
    WHERE w.age >= 18
  )
  WHERE rn = 1
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
FROM adult_first_icu;