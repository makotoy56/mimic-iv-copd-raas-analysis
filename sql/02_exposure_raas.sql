-- 02_exposure_raas.sql
CREATE OR REPLACE TABLE `mimic-iv-portfolio.copd_raas.cohort_copd_raas` AS
WITH raas_raw AS (
    SELECT
        pre.subject_id,
        pre.hadm_id,
        pre.starttime,
        pre.drug
    FROM `physionet-data.mimiciv_3_1_hosp.prescriptions` AS pre
    WHERE 
        LOWER(pre.drug) LIKE '%lisinopril%' OR
        LOWER(pre.drug) LIKE '%enalapril%' OR
        LOWER(pre.drug) LIKE '%ramipril%' OR
        LOWER(pre.drug) LIKE '%captopril%' OR
        LOWER(pre.drug) LIKE '%benazepril%' OR
        LOWER(pre.drug) LIKE '%fosinopril%' OR
        LOWER(pre.drug) LIKE '%perindopril%' OR
        LOWER(pre.drug) LIKE '%quinapril%' OR
        LOWER(pre.drug) LIKE '%trandolapril%' OR
        LOWER(pre.drug) LIKE '%losartan%' OR
        LOWER(pre.drug) LIKE '%valsartan%' OR
        LOWER(pre.drug) LIKE '%irbesartan%' OR
        LOWER(pre.drug) LIKE '%candesartan%' OR
        LOWER(pre.drug) LIKE '%olmesartan%' OR
        LOWER(pre.drug) LIKE '%telmisartan%' OR
        LOWER(pre.drug) LIKE '%azilsartan%'
),

raas_joined AS (
    SELECT
        c.subject_id,
        c.hadm_id,
        c.stay_id,
        c.intime,
        r.starttime AS raas_starttime
    FROM `mimic-iv-portfolio.copd_raas.cohort_copd` AS c
    LEFT JOIN raas_raw AS r
      ON c.subject_id = r.subject_id
     AND c.hadm_id   = r.hadm_id
     AND r.starttime <= c.intime
),

raas_flag_pre_icu AS (
    SELECT
        subject_id,
        hadm_id,
        stay_id,
        CASE WHEN COUNTIF(raas_starttime IS NOT NULL) > 0 THEN 1 ELSE 0 END AS raas_pre_icu
    FROM raas_joined
    GROUP BY subject_id, hadm_id, stay_id
)

SELECT
    subject_id,
    hadm_id,
    stay_id,
    raas_pre_icu
FROM raas_flag_pre_icu;