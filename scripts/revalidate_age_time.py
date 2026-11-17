#!/usr/bin/env python3
"""Compare age/time corrections using SELECT-only source reconstruction.

Default: dry run. --execute fits models in memory and emits aggregate JSON only.
--synthetic exercises the actual pipeline SQL and its outcome QA on artificial data.
No persistent BigQuery tables or patient-level local exports are created.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import warnings
from datetime import datetime, timezone
from pathlib import Path

PROJECT = "mimic-iv-portfolio"
PREFIX = f"{PROJECT}.copd_raas."
STAGES = [
    ("cohort_icu", "01_extract_base.sql"),
    ("cohort_copd", "02_build_cohort_copd.sql"),
    ("cohort_copd_raas", "02_exposure_raas.sql"),
    ("cohort_copd_raas_detailed", "02_exposure_raas_detailed.sql"),
    ("cohort_copd_baseline", "03_build_baseline.sql"),
    ("cohort_copd_outcomes", "04_build_outcomes.sql"),
    ("cohort_copd_outcomes_extended", "04_build_outcomes_extended.sql"),
]


def stage_select(text: str) -> str:
    """Extract one SELECT, never submit the production DDL to BigQuery."""
    body = re.split(r"CREATE (?:OR REPLACE TABLE `[^`]+`|TEMP TABLE \w+) AS\s*", text, maxsplit=1)
    if len(body) != 2:
        raise ValueError("Expected one pipeline table definition")
    select = re.sub(r"--[^\n]*", "", body[1]).split(";", 1)[0].strip()
    if not select.startswith(("WITH ", "SELECT")):
        raise ValueError("Expected a SELECT or WITH body")
    executable = re.sub(r"--[^\n]*", "", select)
    if re.search(r"\b(CREATE|INSERT|UPDATE|DELETE|MERGE|EXPORT|DROP|ALTER)\b", executable, re.I):
        raise ValueError("A pipeline SELECT contains an unexpected statement")
    return select


def source_ctes(repo: Path, replacements: dict[str, str] | None = None) -> str:
    ctes = []
    for table, name in STAGES:
        body = stage_select((repo / "sql" / name).read_text())
        if table == "cohort_icu":
            # Audit both age definitions on the population BEFORE adult selection.
            if body.count("WHERE w.age >= 18") != 1:
                raise ValueError("Adult selection changed; review audit reconstruction")
            body = body.replace("WHERE w.age >= 18", "WHERE TRUE")
        for previous, _ in STAGES:
            body = body.replace(f"`{PREFIX}{previous}`", f"audit_{previous}")
        for table_name, replacement in (replacements or {}).items():
            body = body.replace(f"`{table_name}`", f"({replacement})")
        ctes.append(f"audit_{table} AS (\n{body}\n)")
    return "WITH " + ",\n".join(ctes)


def model_query(repo: Path) -> str:
    # Project no identifiers or individual dates into the in-memory model dataset.
    return source_ctes(repo) + """
SELECT e.age AS admission_age_est, e.anchor_age, e.age_anchor_topcoded,
 e.gender, e.anchor_year_group, e.raas_pre_icu, e.death_event,
 e.time_to_event_days AS elapsed_days,
 TIMESTAMP_DIFF(CASE WHEN e.death_event=1 THEN COALESCE(e.deathtime,e.dischtime)
                     ELSE e.dischtime END,e.intime,HOUR)/24.0 AS legacy_days,
 e.death_time_fallback_flag, e.sofa_score, e.chf, e.ckd, e.diabetes,
 r.acei_pre_icu, r.arb_pre_icu, e.icu_type
FROM audit_cohort_copd_outcomes_extended e
LEFT JOIN audit_cohort_copd_raas_detailed r USING(subject_id,hadm_id,stay_id)
"""


def synthetic_sources() -> dict[str, str]:
    # case 1 crosses an hour in 2 minutes; case 2 is 10 minutes in one hour;
    # case 3 retains one microsecond; cases 4-9 cover fallback and invalid outcomes;
    # cases 10-11 cross the adult boundary in opposite directions; case 12 is topcoded.
    rows = []
    for case in range(1, 13):
        age, year = (17, 2019) if case == 10 else ((18, 2021) if case == 11 else ((91, 2018) if case == 12 else (60, 2019)))
        start = "2020-01-01 00:59:00" if case == 1 else "2020-01-01 00:10:00"
        end = {1: "2020-01-01 01:01:00", 2: "2020-01-01 00:20:00", 3: "2020-01-01 00:10:00.000001",
               5: start, 6: "2020-01-01 00:09:59", 7: "2020-01-01 00:09:59"}.get(case, "2020-01-02 01:00:00")
        death = case in (1, 3, 4, 7)
        dt = f"DATETIME '{end}'" if death and case != 4 else "CAST(NULL AS DATETIME)"
        discharge = "CAST(NULL AS DATETIME)" if case == 8 else f"DATETIME '{end}'"
        flag = "CAST(NULL AS INT64)" if case == 9 else str(int(death))
        rows.append(f"SELECT {case} AS subject_id,{case} AS hadm_id,{case} AS stay_id,"
                    f"DATETIME '{start}' AS intime,DATETIME '2020-01-02 00:00:00' AS outtime,"
                    f"{age} AS anchor_age,{year} AS anchor_year,{discharge} AS dischtime,"
                    f"{dt} AS deathtime,{flag} AS hospital_expire_flag")
    cases = " UNION ALL ".join(rows)
    src = {
        "physionet-data.mimiciv_3_1_icu.icustays": f"SELECT subject_id,hadm_id,stay_id,intime,outtime,'Medical Intensive Care Unit (MICU)' AS first_careunit FROM ({cases})",
        "physionet-data.mimiciv_3_1_hosp.patients": f"SELECT subject_id,'F' AS gender,anchor_age,anchor_year,'2017 - 2019' AS anchor_year_group,CAST(NULL AS DATE) AS dod FROM ({cases})",
        "physionet-data.mimiciv_3_1_hosp.admissions": f"SELECT subject_id,hadm_id,DATETIME '2020-01-01 00:00:00' AS admittime,dischtime,deathtime,hospital_expire_flag FROM ({cases})",
        "physionet-data.mimiciv_3_1_hosp.diagnoses_icd": f"SELECT subject_id,hadm_id,10 AS icd_version,'J440' AS icd_code FROM ({cases})",
        "physionet-data.mimiciv_3_1_hosp.prescriptions": "SELECT 0 AS subject_id,0 AS hadm_id,DATETIME '2020-01-01 00:00:00' AS starttime,'lisinopril' AS drug FROM UNNEST([1]) AS unused WHERE FALSE",
        "physionet-data.mimiciv_3_1_derived.first_day_sofa": f"SELECT stay_id,3 AS sofa FROM ({cases})",
        "physionet-data.mimiciv_3_1_derived.charlson": f"SELECT hadm_id,1 AS charlson_comorbidity_index,0 AS congestive_heart_failure,0 AS renal_disease,0 AS diabetes_without_cc,0 AS diabetes_with_cc,1 AS chronic_pulmonary_disease FROM ({cases})",
    }
    return src


def synthetic_query(repo: Path) -> tuple[str, list[str]]:
    text = (repo / "sql/04_build_outcomes.sql").read_text()
    assertions = re.findall(r"ASSERT \(\s*(SELECT.*?)\s*\) AS '([^']+)';", text, re.S)
    if len(assertions) < 6:
        raise ValueError("Expected the production outcome QA assertions")
    parts = [source_ctes(repo, synthetic_sources())]
    for i, (query, _) in enumerate(assertions):
        query = query.replace("SELECT ", f"SELECT stay_id, ", 1).replace(" = 0\n", f" = 0 AS qa_{i}\n")
        query = query.replace("FROM cohort_copd_outcomes_staged", "FROM audit_cohort_copd_outcomes GROUP BY stay_id")
        parts.append(f",qa_{i} AS ({query})")
    parts.append("\nSELECT o.stay_id AS synthetic_case,o.age,o.anchor_age,o.age_anchor_topcoded,"
                 "o.time_to_event_days,o.death_time_fallback_flag,o.icu_los,o.hosp_los," + ",".join(f"q{i}.qa_{i}" for i in range(len(assertions))) +
                 " FROM audit_cohort_copd_outcomes o " + " ".join(f"JOIN qa_{i} q{i} USING(stay_id)" for i in range(len(assertions))) + " ORDER BY synthetic_case")
    return "\n".join(parts), [message for _, message in assertions]


def check_synthetic(rows: list[dict], qa_names: list[str]) -> dict:
    import math
    cases = {r["synthetic_case"]: r for r in rows}
    assert set(cases) == set(range(1, 13)), "Synthetic cases were lost or duplicated"
    for case, seconds in {1: 120, 2: 600, 3: 0.000001, 4: 89400, 5: 0, 6: -1, 7: -1}.items():
        assert math.isclose(cases[case]["time_to_event_days"], seconds / 86400.0, abs_tol=1e-18), f"Duration case {case}"
    assert math.isclose(cases[1]["icu_los"], 82860 / 86400.0)
    assert math.isclose(cases[1]["hosp_los"], 3660 / 86400.0)
    assert math.isclose(cases[3]["hosp_los"], 600.000001 / 86400.0)
    assert cases[4]["death_time_fallback_flag"] == 1
    assert cases[8]["time_to_event_days"] is None
    assert cases[10]["age"] == 18 and cases[10]["anchor_age"] == 17
    assert cases[11]["age"] == 17 and cases[11]["anchor_age"] == 18
    assert cases[12]["age"] == 93 and cases[12]["age_anchor_topcoded"] == 1
    def failures(case):
        return [qa_names[i] for i in range(len(qa_names)) if not cases[case][f"qa_{i}"]]
    for case in (1, 2, 3, 4, 10, 11, 12):
        assert not failures(case), f"Valid case {case} failed QA"
    expected = {5: "true zero", 6: "endpoint precedes", 7: "endpoint precedes", 8: "missing ICU", 9: "death_event must"}
    for case, fragment in expected.items():
        assert any(fragment in msg for msg in failures(case)), f"Invalid case {case} escaped QA"
    return {"synthetic_cases_passed": 12, "production_qa_assertions_exercised": len(qa_names)}


def analyze(frame) -> dict:
    import numpy as np
    import pandas as pd
    import lifelines
    from lifelines import CoxPHFitter, KaplanMeierFitter
    from lifelines.statistics import logrank_test, proportional_hazard_test
    output = {"versions": {"lifelines": lifelines.__version__, "pandas": pd.__version__, "numpy": np.__version__}, "scenarios": {}}
    for name, age_col, time_col in [
        ("legacy", "anchor_age", "legacy_days"),
        ("time_only", "anchor_age", "elapsed_days"),
        ("age_only", "admission_age_est", "legacy_days"),
        ("both", "admission_age_est", "elapsed_days"),
    ]:
        df = frame.loc[frame[age_col] >= 18].copy()
        df["age"] = df[age_col].astype(float)
        df["time_to_event_days"] = df[time_col].astype(float)
        if df["death_event"].isna().any() or not df["death_event"].isin([0, 1]).all():
            raise ValueError("Missing or invalid event indicators")
        if df["elapsed_days"].isna().any() or (df["elapsed_days"] <= 0).any():
            raise ValueError("Corrected follow-up is missing, reversed, or truly zero")
        result = {"n": len(df), "deaths": int(df.death_event.sum()), "mean_age": float(df.age.mean()),
                  "zero_duration_n": int((df.time_to_event_days == 0).sum()),
                  "positive_subhour_n": int(((df.time_to_event_days > 0) & (df.time_to_event_days < 1/24)).sum()),
                  "fallback_deaths": int(df.death_time_fallback_flag.sum()), "models": {}}
        km = {}
        km_data = df[["raas_pre_icu", "time_to_event_days", "death_event"]].dropna()
        for group in (0, 1):
            g = km_data.loc[km_data.raas_pre_icu == group]
            fit = KaplanMeierFitter().fit(g.time_to_event_days, g.death_event)
            km[str(group)] = {"n": len(g), "deaths": int(g.death_event.sum()),
                              "survival": {str(t): float(fit.predict(t)) for t in (0, 1, 7, 14, 28, 30)}}
        g0, g1 = [km_data.loc[km_data.raas_pre_icu == group] for group in (0, 1)]
        logrank = logrank_test(g0.time_to_event_days, g1.time_to_event_days, g0.death_event, g1.death_event)
        result["km"] = km
        result["logrank_p"] = float(logrank.p_value)
        encoded = pd.get_dummies(df, columns=["gender", "icu_type"], drop_first=True)
        base = ["raas_pre_icu", "age", "gender_M"]
        core = base + ["sofa_score", "chf", "ckd", "diabetes"]
        icu = core + [c for c in encoded.columns if c.startswith("icu_type_")]
        # Same formulas, complete-case selection, strata and penalties as 04a/b/c.
        subgroup = encoded.loc[~((encoded.acei_pre_icu == 1) & (encoded.arb_pre_icu == 1))].copy()
        specs = [("04a_refined", encoded, base, 0.0),
                 ("04b_subgroups", subgroup, ["acei_pre_icu", "arb_pre_icu", "age", "gender_M"], 0.0),
                 ("04c_core", encoded, core, 0.0), ("04c_core_penalty_0.1", encoded, core, 0.1),
                 ("04c_icu", encoded, icu, 0.0), ("04c_icu_penalty_0.01", encoded, icu, 0.01)]
        if name == "both":
            specs.append(("04a_excluding_anchor_topcoded", encoded.loc[encoded.age_anchor_topcoded == 0], base, 0.0))
        for model_name, data, covariates, penalty in specs:
            cols = ["time_to_event_days", "death_event", "anchor_year_group"] + covariates
            fit_df = data[cols].dropna().copy()
            for c in cols:
                if c != "anchor_year_group":
                    fit_df[c] = fit_df[c].astype(float)
            cph = CoxPHFitter(penalizer=penalty)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                cph.fit(fit_df, duration_col="time_to_event_days", event_col="death_event", strata=["anchor_year_group"])
                ph = proportional_hazard_test(cph, fit_df, time_transform="rank").summary
            summary = cph.summary
            result["models"][model_name] = {
                "n": len(fit_df), "deaths": int(fit_df.death_event.sum()), "penalizer": penalty,
                "estimates": {c: {"hr": float(summary.loc[c, "exp(coef)"]),
                                  "lower_95": float(summary.loc[c, "exp(coef) lower 95%"]),
                                  "upper_95": float(summary.loc[c, "exp(coef) upper 95%"]),
                                  "p": float(summary.loc[c, "p"])} for c in covariates},
                "ph_rank_p": {str(c): float(ph.loc[c, "p"]) for c in ph.index},
                "warnings": sorted({str(w.message) for w in caught}),
            }
        output["scenarios"][name] = result
        print(f"Completed {name}: admissions={len(df)}, deaths={result['deaths']}", flush=True)
    output["age_eligibility"] = {
        "excluded_legacy_but_adult_corrected": int(((frame.anchor_age < 18) & (frame.admission_age_est >= 18)).sum()),
        "included_legacy_but_minor_corrected": int(((frame.anchor_age >= 18) & (frame.admission_age_est < 18)).sum()),
        "anchor_topcoded_n": int(frame.age_anchor_topcoded.sum()),
        "changed_age_n": int((frame.anchor_age != frame.admission_age_est).sum()),
    }
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--execute", action="store_true", help="Run the SELECT and fit in-memory models after a dry run")
    parser.add_argument("--synthetic", action="store_true", help="Run only artificial cases against the actual pipeline SQL and QA")
    parser.add_argument("--maximum-bytes-billed", type=int, default=2_000_000_000)
    parser.add_argument("--output", type=Path, help="New aggregate JSON file; refuses to overwrite an existing file")
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("Choose a new output file; existing outputs are preserved")
    import google.auth
    from google.auth.transport.requests import Request
    from google.cloud import bigquery
    class BoundedRequest(Request):
        def __call__(self, *a, **kw):
            kw["timeout"] = 20
            return super().__call__(*a, **kw)
    creds, _ = google.auth.default()
    creds.refresh(BoundedRequest())
    client = bigquery.Client(project=PROJECT, credentials=creds)
    if args.synthetic:
        query, qa_names = synthetic_query(args.repo)
    else:
        query = model_query(args.repo)
    dry = client.query(query, location="US", job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False), timeout=30, retry=None)
    print(json.dumps({"dry_run_bytes": dry.total_bytes_processed, "statement_type": dry.statement_type}), flush=True)
    if not args.execute:
        return
    if dry.total_bytes_processed > args.maximum_bytes_billed:
        raise ValueError("Dry-run estimate exceeds the per-query limit")
    job = client.query(query, location="US", job_config=bigquery.QueryJobConfig(use_query_cache=False, maximum_bytes_billed=args.maximum_bytes_billed), timeout=30, retry=None, job_retry=None)
    print(json.dumps({"job_id": job.job_id}), flush=True)
    rows = job.result(timeout=180, retry=None)
    if args.synthetic:
        result = check_synthetic([dict(r) for r in rows], qa_names)
    else:
        # Query result has no patient identifiers. Keep the individual model inputs in memory.
        result = analyze(rows.to_dataframe(create_bqstorage_client=False))
    result["execution"] = {
        "executed_at_utc": datetime.now(timezone.utc).isoformat(), "project": PROJECT,
        "job_id": job.job_id, "processed_bytes": job.total_bytes_processed,
        "billed_bytes": job.total_bytes_billed, "query_sha256": hashlib.sha256(query.encode()).hexdigest(),
        "pipeline_sha256": {name: hashlib.sha256((args.repo / "sql" / name).read_bytes()).hexdigest() for _, name in STAGES},
    }
    text = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)
    if args.output:
        with args.output.open("x") as f:
            f.write(text + "\n")
        print(f"Aggregate validation saved: {args.output}", flush=True)
    else:
        print(text)


if __name__ == "__main__":
    main()
