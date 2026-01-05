-- 03_build_baseline.sql
CREATE OR REPLACE TABLE `mimic-iv-portfolio.copd_raas.cohort_copd_baseline` AS
WITH base AS (
    SELECT
        c.subject_id,
        c.hadm_id,
        c.stay_id,
        c.intime,
        c.outtime,
        c.icu_los,
        p.anchor_age AS age,
        p.gender,
        p.anchor_year,
        p.anchor_year_group,
        TIMESTAMP_DIFF(a.dischtime, a.admittime, HOUR) / 24.0 AS hosp_los,
        p.dod
    FROM `mimic-iv-portfolio.copd_raas.cohort_copd` AS c
    LEFT JOIN `physionet-data.mimiciv_3_1_hosp.patients` AS p
      ON c.subject_id = p.subject_id
    LEFT JOIN `physionet-data.mimiciv_3_1_hosp.admissions` AS a
      ON c.hadm_id = a.hadm_id
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
    COALESCE(r.raas_pre_icu, 0) AS raas_pre_icu,
    b.dod
FROM base AS b
LEFT JOIN `mimic-iv-portfolio.copd_raas.cohort_copd_raas` AS r
  ON b.subject_id = r.subject_id
 AND b.hadm_id   = r.hadm_id
 AND b.stay_id   = r.stay_id;