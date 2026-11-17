-- 01_extract_base.sql
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
    DATETIME_DIFF(i.outtime, i.intime, MICROSECOND) / 86400000000.0 AS icu_los
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
    -- Approximate age at hospital admission, using the deidentified admission year.
    -- anchor_age = 91 is an aggregated >89 group; year adjustment is still a proxy.
    p.anchor_age + EXTRACT(YEAR FROM a.admittime) - p.anchor_year AS age,
    p.anchor_age,
    CAST(p.anchor_age = 91 AS INT64) AS age_anchor_topcoded,
    p.anchor_year,
    p.anchor_year_group
  FROM base_stays AS b
  JOIN `physionet-data.mimiciv_3_1_hosp.patients` AS p
    ON b.subject_id = p.subject_id
  JOIN `physionet-data.mimiciv_3_1_hosp.admissions` AS a
    ON b.subject_id = a.subject_id
   AND b.hadm_id = a.hadm_id
),

-- Keep only adults (estimated admission age >= 18) and the first ICU stay per subject_id + hadm_id
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
  anchor_age,
  age_anchor_topcoded,
  gender,
  anchor_year,
  anchor_year_group
FROM adult_first_icu;
