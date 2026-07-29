-- 04_build_outcomes.sql
-- Build in-hospital mortality outcomes for COPD ICU cohort

-- Stage the outcome table so QA assertions run before the production replacement.
CREATE TEMP TABLE cohort_copd_outcomes_staged AS
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
    a.deathtime,
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
    -- Death: ICU admission → hospital death (discharge fallback only if death time is missing)
    -- Survival: ICU admission → hospital discharge
    CASE
      WHEN hospital_expire_flag = 1 THEN
        TIMESTAMP_DIFF(COALESCE(deathtime, dischtime), intime, HOUR) / 24.0
      ELSE
        TIMESTAMP_DIFF(dischtime, intime, HOUR) / 24.0
    END AS time_to_event_days,

    -- Explicitly identify deaths that use discharge time as a fallback
    CASE
      WHEN hospital_expire_flag = 1 AND deathtime IS NULL THEN 1
      ELSE 0
    END AS death_time_fallback_flag
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
  deathtime,
  death_time_fallback_flag,
  dod
FROM events;

-- Outcome construction QA checks
ASSERT (
  SELECT COUNTIF(time_to_event_days IS NULL) = 0
  FROM cohort_copd_outcomes_staged
) AS 'Outcome QA failed: time_to_event_days contains NULL values';

ASSERT (
  SELECT COUNTIF(time_to_event_days < 0) = 0
  FROM cohort_copd_outcomes_staged
) AS 'Outcome QA failed: negative time_to_event_days detected';

ASSERT (
  SELECT COUNTIF(
    death_event = 1
    AND COALESCE(deathtime, dischtime) < intime
  ) = 0
  FROM cohort_copd_outcomes_staged
) AS 'Outcome QA failed: death event timestamp precedes ICU admission';

-- Replace the production table only after all outcome QA assertions pass.
CREATE OR REPLACE TABLE `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes` AS
SELECT *
FROM cohort_copd_outcomes_staged;

-- Return a compact QA summary, including the number of fallback deaths
SELECT
  COUNTIF(time_to_event_days < 0) AS negative_time_to_event_count,
  COUNTIF(
    death_event = 1
    AND COALESCE(deathtime, dischtime) < intime
  ) AS death_before_icu_count,
  COUNTIF(death_time_fallback_flag = 1) AS fallback_death_count
FROM cohort_copd_outcomes_staged;
