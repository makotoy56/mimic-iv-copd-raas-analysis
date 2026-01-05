-- 04_build_outcomes_extended.sql
-- Build extended outcome table for the COPD cohort.
-- Adds severity (SOFA), comorbidities (Charlson-based), and ICU type.
-- Hypertension (htn) is kept as a placeholder column for compatibility.

CREATE OR REPLACE TABLE `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes_extended` AS
WITH base AS (
  -- Base outcome table from 04_build_outcomes.sql
  SELECT
    o.subject_id,
    o.hadm_id,
    o.stay_id,
    o.intime,
    o.outtime,
    o.icu_los,
    o.age,
    o.gender,
    o.anchor_year,
    o.anchor_year_group,
    o.hosp_los,
    o.raas_pre_icu,
    o.death_event,
    o.time_to_event_days,
    o.admittime,
    o.dischtime,
    o.dod
  FROM `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes` AS o
),

-- First-day SOFA score (severity)
sofa AS (
  SELECT
    stay_id,
    sofa AS sofa_score
  FROM `physionet-data.mimiciv_3_1_derived.first_day_sofa`
),

-- Charlson comorbidity index and key components
charlson AS (
  SELECT
    hadm_id,
    charlson_comorbidity_index,
    -- Map Charlson components to simpler binary flags
    CAST(congestive_heart_failure AS INT64)     AS chf,
    CAST(renal_disease AS INT64)                AS ckd,
    -- Treat any diabetes component as "diabetes = 1"
    CASE
      WHEN diabetes_without_cc = 1 OR diabetes_with_cc = 1 THEN 1
      ELSE 0
    END                                         AS diabetes,
    CAST(chronic_pulmonary_disease AS INT64)    AS copd_comorbidity,
    -- Placeholder for hypertension: kept for compatibility with existing code.
    -- There is no direct hypertension flag in the Charlson table.
    NULL                                        AS htn
  FROM `physionet-data.mimiciv_3_1_derived.charlson`
),

-- ICU type / care unit information
icu AS (
  SELECT
    stay_id,
    -- Use first_careunit as a readable ICU type label
    first_careunit AS icu_type
  FROM `physionet-data.mimiciv_3_1_icu.icustays`
)

SELECT
  b.subject_id,
  b.hadm_id,
  b.stay_id,
  b.intime,
  b.outtime,
  b.icu_los,
  b.age,
  b.gender,
  b.anchor_year,
  b.anchor_year_group,
  b.hosp_los,
  b.raas_pre_icu,
  b.death_event,
  b.time_to_event_days,
  b.admittime,
  b.dischtime,
  b.dod,

  -- Severity
  s.sofa_score,

  -- Charlson index and components
  c.charlson_comorbidity_index,
  c.chf,
  c.ckd,
  c.diabetes,
  c.copd_comorbidity,
  c.htn,

  -- ICU type
  i.icu_type
FROM base AS b
LEFT JOIN sofa     AS s ON b.stay_id = s.stay_id
LEFT JOIN charlson AS c ON b.hadm_id = c.hadm_id
LEFT JOIN icu      AS i ON b.stay_id = i.stay_id;