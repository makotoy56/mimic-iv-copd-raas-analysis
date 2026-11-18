"""Cross-check unpenalized ICU-COPD Cox estimates with statsmodels PHReg.

Reads the existing approved BigQuery tables after a capped dry run. Individual
model rows stay in memory; only aggregate provenance and coefficients are saved.
Does not create tables, refresh reports or fit penalized/PH-test models.
"""
import argparse
import hashlib
import importlib.util
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
import statsmodels
from statsmodels.duration.hazard_regression import PHReg


def run(repo):
    # Reuse only the explicitly projected, dry-run/billing-capped data access.
    # Preparation and model fitting below do not call production fit functions.
    spec = importlib.util.spec_from_file_location("production_data_access", repo / "scripts/current_analysis.py")
    access = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(access)
    saved = json.loads((repo / "docs/CURRENT_ANALYSIS.json").read_text())
    if saved["analysis_version"] != access.ANALYSIS_VERSION:
        raise ValueError("Current reference analysis version does not match")
    query_sha256 = hashlib.sha256(access.QUERY.encode()).hexdigest()
    if query_sha256 != saved["execution"]["query_sha256"]:
        raise ValueError("Current data query differs from reference provenance")
    frame, query = access.load_current_data()
    cohort = {"n": len(frame), "events": int(frame.death_event.sum()),
              "age_sum": float(frame.age.sum()), "duration_sum": float(frame.time_to_event_days.sum())}
    manifest = saved["secondary_python_logistic"]["manifest"]
    for key in ["n", "events", "age_sum", "duration_sum"]:
        if not np.isclose(cohort[key], manifest[key], rtol=1e-10, atol=1e-5):
            raise ValueError(f"Cohort reference differs: {key}")

    frame["gender_M"] = (frame.gender == "M").astype(int)
    counts = frame.icu_type.value_counts(dropna=True)
    rare = sorted(str(k) for k, count in counts.items() if count < 50)
    if rare != saved["rare_icu_rule"]["pooled_labels"]:
        raise ValueError("Rare ICU category set differs from reference")
    frame["icu_type_group"] = frame.icu_type.astype("string").replace(
        {label: "Other (rare ICU types)" for label in rare})
    dummy = pd.get_dummies(frame.icu_type_group, prefix="icu_group", drop_first=True, dtype=float)
    frame = pd.concat([frame, dummy], axis=1)
    base = ["raas_pre_icu", "age", "gender_M"]
    core = base + ["sofa_score", "chf", "ckd", "diabetes"]
    era = ["anchor_year_group"]
    specs = [
        ("primary_refined", frame, base, era),
        ("subgroups", frame.loc[~((frame.acei_pre_icu == 1) & (frame.arb_pre_icu == 1))],
         ["acei_pre_icu", "arb_pre_icu", "age", "gender_M"], era),
        ("core", frame, core, era),
        ("icu_pooled", frame, core + list(dummy), era),
        ("core_ph_stratified", frame, base + ["ckd", "diabetes"], era + ["chf", "sofa_score"]),
        ("icu_ph_stratified", frame, base + ["ckd", "diabetes"], era + ["chf", "sofa_score", "icu_type_group"]),
    ]
    comparisons = {}
    zcrit = norm.ppf(0.975)
    tolerance = 1e-4
    for name, data, covariates, strata_columns in specs:
        columns = list(dict.fromkeys(["time_to_event_days", "death_event"] + covariates + strata_columns))
        complete = data[columns].dropna().copy()
        strata_index = pd.MultiIndex.from_frame(complete[strata_columns].astype(str))
        strata_codes, levels = pd.factorize(strata_index, sort=True)
        production = saved["models"][name]
        if (len(complete), int(complete.death_event.sum()), len(levels)) != (
                production["n"], production["deaths"], production["strata_count"]):
            raise ValueError(f"Complete-case cohort or strata differ: {name}")
        if set(covariates) != set(production["estimates"]):
            raise ValueError(f"Parameter names differ: {name}")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = PHReg(complete.time_to_event_days.to_numpy(dtype=float),
                          complete[covariates].to_numpy(dtype=float),
                          status=complete.death_event.to_numpy(dtype=int), strata=strata_codes,
                          ties="efron", missing="raise")
            fit = model.fit(maxiter=200, tol=1e-10, disp=False)
        if caught:
            raise ValueError(f"Independent fit produced warnings: {name}: " + "; ".join(str(w.message) for w in caught))
        score_per_admission = float(np.max(np.abs(model.score(fit.params))) / len(complete))
        if not np.isfinite(fit.params).all() or not np.isfinite(fit.bse).all() or score_per_admission > 1e-8:
            raise ValueError(f"Independent fit did not converge adequately: {name}")
        estimates, maxima = {}, {key: 0.0 for key in ["log_coefficient", "hr", "lower_95", "upper_95", "p"]}
        for index, parameter in enumerate(covariates):
            coefficient = float(fit.params[index])
            se = float(fit.bse[index])
            actual = {"log_coefficient": coefficient, "standard_error": se,
                      "hr": float(np.exp(coefficient)),
                      "lower_95": float(np.exp(coefficient - zcrit * se)),
                      "upper_95": float(np.exp(coefficient + zcrit * se)),
                      "p": float(2 * norm.sf(abs(coefficient / se)))}
            reference = production["estimates"][parameter]
            differences = {key: abs(actual[key] - (np.log(reference["hr"]) if key == "log_coefficient" else reference[key]))
                           for key in maxima}
            estimates[parameter] = {**actual, "absolute_differences_from_lifelines": differences}
            for key, value in differences.items():
                maxima[key] = max(maxima[key], float(value))
        passed = max(maxima.values()) <= tolerance
        comparisons[name] = {"n": len(complete), "events": int(complete.death_event.sum()),
                             "strata": strata_columns, "strata_count": len(levels),
                             "parameter_count": len(covariates), "score_per_admission": score_per_admission,
                             "max_absolute_differences": maxima, "passed": passed, "estimates": estimates}
        print(json.dumps({"model": name, "n": len(complete), "events": int(complete.death_event.sum()),
                          "max_absolute_differences": maxima, "passed": passed}), flush=True)
    return {"analysis_version": access.ANALYSIS_VERSION,
            "validation": "statsmodels_PHReg_vs_saved_lifelines_unpenalized_Efron_Cox",
            "status": "passed" if all(v["passed"] for v in comparisons.values()) else "failed",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "data_handling": "approved_BigQuery_read_in_memory_aggregate_output_only",
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "statsmodels_version": statsmodels.__version__, "cohort": cohort,
            "query_execution": query, "query_sha256": query_sha256,
            "reference_sha256": hashlib.sha256((repo / "docs/CURRENT_ANALYSIS.json").read_bytes()).hexdigest(),
            "absolute_tolerance": tolerance,
            "excluded": ["penalized models", "PH diagnostic tests", "secondary logistic", "source SQL revalidation"],
            "limitations": ["Shared corrected BigQuery inputs; independent statistical implementation only.",
                            "Existing admission-level design and ordinary model-based standard errors retained.",
                            "No new patient clustering, competing-risk model or causal validation."],
            "models": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Refusing to overwrite an existing independent validation result")
    result = run(args.repo)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    if result["status"] != "passed":
        raise SystemExit("Independent Cox estimates did not meet the comparison tolerance")
    print(json.dumps({"status": result["status"], "models": len(result["models"])}))


if __name__ == "__main__":
    main()
