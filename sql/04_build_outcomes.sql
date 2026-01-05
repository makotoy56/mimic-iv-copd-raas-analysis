-- 04_build_outcomes.sql
-- Build in-hospital mortality outcomes for COPD ICU cohort

CREATE OR REPLACE TABLE `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes` AS
WITH base AS (
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
    b.dod,
    a.admittime,
    a.dischtime,
    a.hospital_expire_flag
  FROM `mimic-iv-portfolio.copd_raas.cohort_copd_baseline` AS b
  LEFT JOIN `physionet-data.mimiciv_3_1_hosp.admissions` AS a
    ON b.hadm_id = a.hadm_id
),

events AS (
  SELECT
    *,
    -- In-hospital death indicator
    hospital_expire_flag AS death_event,

    -- Time-to-event (days)
    -- Death: ICU admission → hospital death
    -- Survival: ICU admission → hospital discharge
    DATE_DIFF(
      DATE(dischtime),
      DATE(intime),
      DAY
    ) AS time_to_event_days
  FROM base
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
  anchor_year_group,
  hosp_los,
  raas_pre_icu,
  death_event,
  time_to_event_days,
  admittime,
  dischtime,
  dod
FROM events;