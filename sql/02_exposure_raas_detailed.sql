-- 02_exposure_raas_detailed.sql
-- Create detailed RAAS exposure flags (ACEi / ARB / both / neither)
-- for COPD ICU cohort

CREATE OR REPLACE TABLE `mimic-iv-portfolio.copd_raas.cohort_copd_raas_detailed` AS
WITH raas_raw AS (
  -- Step 1: Extract candidate RAAS prescriptions (ACEi and ARB)
  SELECT
    pre.subject_id,
    pre.hadm_id,
    pre.starttime,
    pre.drug,
    -- Classify each prescription as ACEi or ARB
    CASE
      -- ACE inhibitors
      WHEN LOWER(pre.drug) LIKE '%lisinopril%'   THEN 'acei'
      WHEN LOWER(pre.drug) LIKE '%enalapril%'    THEN 'acei'
      WHEN LOWER(pre.drug) LIKE '%ramipril%'     THEN 'acei'
      WHEN LOWER(pre.drug) LIKE '%captopril%'    THEN 'acei'
      WHEN LOWER(pre.drug) LIKE '%benazepril%'   THEN 'acei'
      WHEN LOWER(pre.drug) LIKE '%fosinopril%'   THEN 'acei'
      WHEN LOWER(pre.drug) LIKE '%perindopril%'  THEN 'acei'
      WHEN LOWER(pre.drug) LIKE '%quinapril%'    THEN 'acei'
      WHEN LOWER(pre.drug) LIKE '%trandolapril%' THEN 'acei'

      -- ARBs
      WHEN LOWER(pre.drug) LIKE '%losartan%'     THEN 'arb'
      WHEN LOWER(pre.drug) LIKE '%valsartan%'    THEN 'arb'
      WHEN LOWER(pre.drug) LIKE '%irbesartan%'   THEN 'arb'
      WHEN LOWER(pre.drug) LIKE '%candesartan%'  THEN 'arb'
      WHEN LOWER(pre.drug) LIKE '%olmesartan%'   THEN 'arb'
      WHEN LOWER(pre.drug) LIKE '%telmisartan%'  THEN 'arb'
      WHEN LOWER(pre.drug) LIKE '%azilsartan%'   THEN 'arb'
      ELSE NULL
    END AS raas_class
  FROM `physionet-data.mimiciv_3_1_hosp.prescriptions` AS pre
  WHERE
    -- Pre-filter to obvious RAAS candidates to reduce noise
    LOWER(pre.drug) LIKE '%lisinopril%'   OR
    LOWER(pre.drug) LIKE '%enalapril%'    OR
    LOWER(pre.drug) LIKE '%ramipril%'     OR
    LOWER(pre.drug) LIKE '%captopril%'    OR
    LOWER(pre.drug) LIKE '%benazepril%'   OR
    LOWER(pre.drug) LIKE '%fosinopril%'   OR
    LOWER(pre.drug) LIKE '%perindopril%'  OR
    LOWER(pre.drug) LIKE '%quinapril%'    OR
    LOWER(pre.drug) LIKE '%trandolapril%' OR
    LOWER(pre.drug) LIKE '%losartan%'     OR
    LOWER(pre.drug) LIKE '%valsartan%'    OR
    LOWER(pre.drug) LIKE '%irbesartan%'   OR
    LOWER(pre.drug) LIKE '%candesartan%'  OR
    LOWER(pre.drug) LIKE '%olmesartan%'   OR
    LOWER(pre.drug) LIKE '%telmisartan%'  OR
    LOWER(pre.drug) LIKE '%azilsartan%'
),

raas_joined AS (
  -- Step 2: Join RAAS prescriptions to COPD ICU cohort
  -- and restrict to prescriptions started before ICU admission
  SELECT
    c.subject_id,
    c.hadm_id,
    c.stay_id,
    c.intime,
    r.starttime AS raas_starttime,
    r.raas_class
  FROM `mimic-iv-portfolio.copd_raas.cohort_copd` AS c
  LEFT JOIN raas_raw AS r
    ON c.subject_id = r.subject_id
   AND c.hadm_id   = r.hadm_id
   AND r.starttime <= c.intime  -- RAAS use before ICU admission
),

raas_flag_pre_icu AS (
  -- Step 3: Aggregate to ICU stay level
  SELECT
    subject_id,
    hadm_id,
    stay_id,
    -- Any ACEi use before ICU
    CASE 
      WHEN COUNTIF(raas_class = 'acei') > 0 THEN 1 
      ELSE 0 
    END AS acei_pre_icu,
    -- Any ARB use before ICU
    CASE 
      WHEN COUNTIF(raas_class = 'arb') > 0 THEN 1 
      ELSE 0 
    END AS arb_pre_icu
  FROM raas_joined
  GROUP BY subject_id, hadm_id, stay_id
)

-- Step 4: Create detailed exposure groups
SELECT
  subject_id,
  hadm_id,
  stay_id,
  acei_pre_icu,
  arb_pre_icu,
  -- Both ACEi and ARB before ICU (rare dual-therapy)
  CASE 
    WHEN acei_pre_icu = 1 AND arb_pre_icu = 1 THEN 1 
    ELSE 0 
  END AS raas_both_pre_icu,
  -- Any RAAS (ACEi or ARB) before ICU
  CASE 
    WHEN acei_pre_icu = 1 OR arb_pre_icu = 1 THEN 1 
    ELSE 0 
  END AS raas_any_pre_icu,
  -- 4-category exposure group
  -- acei_only / arb_only / both / neither
  CASE
    WHEN acei_pre_icu = 1 AND arb_pre_icu = 0 THEN 'acei_only'
    WHEN acei_pre_icu = 0 AND arb_pre_icu = 1 THEN 'arb_only'
    WHEN acei_pre_icu = 1 AND arb_pre_icu = 1 THEN 'both'
    ELSE 'neither'
  END AS exposure_group_4cat,
  -- 3-category exposure group for monotherapy analysis
  -- acei_only / arb_only / neither
  -- (dual-therapy "both" is set to NULL and can be excluded in primary analysis)
  CASE
    WHEN acei_pre_icu = 1 AND arb_pre_icu = 0 THEN 'acei_only'
    WHEN acei_pre_icu = 0 AND arb_pre_icu = 1 THEN 'arb_only'
    WHEN acei_pre_icu = 0 AND arb_pre_icu = 0 THEN 'neither'
    ELSE NULL  -- both or any unexpected pattern
  END AS exposure_group_3cat_monotherapy,
  -- Convenience flag: monotherapy (ACEi only or ARB only) vs others
  CASE
    WHEN (acei_pre_icu + arb_pre_icu) = 1 THEN 1
    ELSE 0
  END AS is_monotherapy
FROM raas_flag_pre_icu;