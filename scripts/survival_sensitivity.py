"""Patient clustering, competing events, and a 24-hour landmark supplement.

Default inputs are wholly synthetic. Explicit current-data mode uses the existing
bounded BigQuery loader; pseudonymous keys and model rows stay in local memory.
Only aggregate output is returned or saved, under ignored local_supplements/.
No existing model, table, figure, report, or result record is refreshed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.duration.hazard_regression import PHReg

VERSION = "patient_cluster_competing_landmark_v1"
BASE = ["raas_pre_icu", "age", "gender_M"]
CORE = BASE + ["sofa_score", "chf", "ckd", "diabetes"]
GRID = np.arange(0.0, 29.0)  # Fixed elapsed-day grid; never export event-level times.
SEED = 20261118


class SensitivityError(ValueError):
    """Fixed error codes only; no row values or authentication details."""


def require(condition, code):
    if not condition:
        raise SensitivityError(code)


def synthetic_data(tied=False):
    """Independent artificial admissions, clustered by artificial patient labels."""
    rng = np.random.default_rng(91273)
    patients = 180
    keys = np.repeat(np.arange(patients), rng.integers(2, 5, patients))
    n = len(keys)
    frailty = rng.normal(0, 0.6, patients)[keys]
    age = rng.uniform(35, 85, patients)[keys]
    male = rng.integers(0, 2, patients)[keys]
    exposure = rng.binomial(1, 0.35, n)
    sofa = rng.integers(0, 10, n)
    chf, ckd, diabetes = rng.binomial(1, 0.3, (3, n))
    linear = -0.25 * exposure + 0.015 * (age - 65) + 0.12 * male + 0.06 * sofa + frailty
    death = rng.exponential(20 / np.exp(linear))
    discharge = rng.exponential(9, n)
    duration = np.minimum(death, discharge) + 0.001
    if tied:
        duration = np.floor(duration * 4) / 4 + 0.125
    return pd.DataFrame({
        "subject_id": keys, "hadm_id": np.arange(n), "stay_id": np.arange(n),
        "gender": np.where(male, "M", "F"), "age": age,
        "anchor_year_group": np.array(["a", "b", "c"])[np.arange(n) % 3],
        "raas_pre_icu": exposure, "death_event": (death <= discharge).astype(int),
        "time_to_event_days": duration, "death_time_fallback_flag": np.zeros(n, dtype=int),
        "sofa_score": sofa, "chf": chf, "ckd": ckd, "diabetes": diabetes,
    })


def validate_frame(frame):
    required = ["subject_id", "hadm_id", "stay_id", "gender", "age", "anchor_year_group",
                "raas_pre_icu", "death_event", "time_to_event_days", "death_time_fallback_flag",
                "sofa_score", "chf", "ckd", "diabetes"]
    require(set(required) <= set(frame), "MISSING_INPUT_COLUMNS")
    require(len(frame) > 0, "EMPTY_COHORT")
    require(frame[["subject_id", "hadm_id", "stay_id"]].notna().all().all(), "MISSING_CLUSTER_KEYS")
    require(frame.hadm_id.is_unique and frame.stay_id.is_unique, "DUPLICATE_ADMISSION_OR_STAY")
    duration = frame.time_to_event_days.to_numpy(dtype=float)
    require(np.isfinite(duration).all() and (duration > 0).all(), "INVALID_FOLLOWUP")
    for column in ["death_event", "raas_pre_icu", "death_time_fallback_flag"]:
        require(frame[column].notna().all() and frame[column].isin([0, 1]).all(), "INVALID_BINARY_FLAG")
    require(frame.gender.notna().all() and frame.gender.isin(["M", "F"]).all(), "INVALID_OR_MISSING_SEX")
    require(not ((frame.death_time_fallback_flag == 1) & (frame.death_event != 1)).any(), "INVALID_DEATH_FALLBACK")


def complete_frame(frame, covariates):
    data = frame.copy()
    data["gender_M"] = (data.gender == "M").astype(float)
    columns = ["subject_id", "time_to_event_days", "death_event", "anchor_year_group"] + covariates
    data = data[list(dict.fromkeys(columns))].dropna().copy()
    require(len(data) > 0, "NO_COMPLETE_CASES")
    for name in ["time_to_event_days", "death_event"] + covariates:
        data[name] = data[name].astype(float)
    require(np.isfinite(data[["time_to_event_days", "death_event"] + covariates]).all().all(), "NONFINITE_MODEL_INPUT")
    data["anchor_year_group"] = data.anchor_year_group.astype(str)
    require(data[covariates].nunique().min() > 1, "ZERO_VARIANCE_COVARIATE")
    return data


def efron_score_residuals(time, event, design, strata, beta):
    """Unweighted right-censored Efron scores, including tied death/censor times.

    For each tied-event substep f=l/d, subtract the risk-weighted centered
    covariate contribution using S0-f*E0 and S1-f*E1. Event rows receive 1/d
    of their centered observed score and the fractional-risk correction.
    Scores sum to the Efron partial-likelihood gradient, also away from the MLE.
    No jitter, case weights, delayed entry, or recurrent-event counting process.
    """
    residuals = np.zeros_like(design, dtype=float)
    for level in np.unique(strata):
        rows = np.flatnonzero(strata == level)
        t, e, x = time[rows], event[rows], design[rows]
        eta = x @ beta
        risk = np.exp(eta - eta.max())
        local = np.zeros_like(x)
        for instant in np.unique(t[e == 1]):
            at_risk = t >= instant
            deaths = (t == instant) & (e == 1)
            d = int(deaths.sum())
            xr, xe = x[at_risk], x[deaths]
            rr, re = risk[at_risk], risk[deaths]
            s0, e0 = rr.sum(), re.sum()
            s1, e1 = rr @ xr, re @ xe
            for fraction in np.arange(d) / d:
                denominator = s0 - fraction * e0
                mean = (s1 - fraction * e1) / denominator
                local[at_risk] -= rr[:, None] * (xr - mean) / denominator
                local[deaths] += (xe - mean) / d + fraction * re[:, None] * (xe - mean) / denominator
        residuals[rows] = local
    return residuals


def fit_clustered_cox(frame, covariates, event_of_interest=1):
    data = complete_frame(frame, covariates)
    time = data.time_to_event_days.to_numpy(dtype=float)
    event = data.death_event.to_numpy(dtype=int)
    if event_of_interest == 2:
        event = 1 - event
    require(event_of_interest in [1, 2], "INVALID_CAUSE")
    x = data[covariates].to_numpy(dtype=float)
    strata = pd.factorize(data.anchor_year_group, sort=True)[0]
    cluster_codes, patients = pd.factorize(data.subject_id, sort=True)
    require(len(patients) >= 2 and event.sum() > len(covariates), "INSUFFICIENT_EVENTS_OR_CLUSTERS")
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = PHReg(time, x, status=event, strata=strata, ties="efron", missing="raise")
            fitted = model.fit(maxiter=200, tol=1e-10, disp=False)
        require(not caught, "COX_WARNING_REQUIRES_REVIEW")
        beta = np.asarray(fitted.params)
        ordinary = np.asarray(fitted.cov_params())
        scores = efron_score_residuals(time, event, x, strata, beta)
        gradient = model.score(beta)
        require(np.allclose(scores.sum(axis=0), gradient, atol=1e-7, rtol=1e-7), "EFRON_SCORE_IDENTITY_FAILED")
        require(np.max(np.abs(gradient)) / len(data) < 1e-8, "COX_NOT_CONVERGED")
        cluster_scores = np.zeros((len(patients), len(covariates)))
        np.add.at(cluster_scores, cluster_codes, scores)
        covariance = ordinary @ (cluster_scores.T @ cluster_scores) @ ordinary
        covariance = (covariance + covariance.T) / 2
        require(np.isfinite(beta).all() and np.isfinite(covariance).all(), "NONFINITE_COX_RESULT")
        require(np.linalg.eigvalsh(covariance).min() >= -1e-10, "INVALID_CLUSTER_COVARIANCE")
        estimates = {}
        for index, name in enumerate(covariates):
            estimates[name] = {"log_coefficient": float(beta[index]), "hr": float(np.exp(beta[index]))}
            for label, matrix in [("ordinary", ordinary), ("patient_cluster", covariance)]:
                se = float(np.sqrt(matrix[index, index]))
                require(se > 0 and np.isfinite(se), "INVALID_COX_SE")
                estimates[name][label] = {"se": se, "lower_95": float(np.exp(beta[index] - norm.ppf(.975) * se)),
                                          "upper_95": float(np.exp(beta[index] + norm.ppf(.975) * se)),
                                          "p": float(2 * norm.sf(abs(beta[index] / se)))}
    except SensitivityError:
        raise
    except Exception:
        raise SensitivityError("COX_FIT_FAILED") from None
    sizes = data.groupby("subject_id").size()
    tied = data.assign(event=event).loc[event == 1].groupby(["anchor_year_group", "time_to_event_days"]).size()
    return {"n": len(data), "events": int(event.sum()), "patients": len(patients),
            "patients_with_multiple_admissions": int((sizes > 1).sum()),
            "admissions_from_repeat_patients": int(sizes.loc[sizes > 1].sum()),
            "maximum_admissions_per_patient": int(sizes.max()), "dropped_missing": len(frame) - len(data),
            "tied_event_sets_within_era": int((tied > 1).sum()), "strata_count": int(len(np.unique(strata))),
            "cause": "in_hospital_death" if event_of_interest == 1 else "live_discharge",
            "covariates": covariates, "strata": ["anchor_year_group"], "ties": "efron", "penalizer": 0.0,
            "variance": "patient_cluster_HC0_sandwich_Efron_scores", "small_sample_correction": False,
            "estimates": estimates, "ordinary_covariance": ordinary.tolist(),
            "patient_cluster_covariance": covariance.tolist(),
            "score_identity_max_error": float(np.max(np.abs(scores.sum(axis=0) - gradient)))}


def aalen_johansen(time, event, grid, weights=None):
    """Two-cause product integral; event codes 0=censor, 1=death, 2=discharge.

    All events and censors at a shared time use the risk set just before it.
    Censoring reduces subsequent risk sets only. No random tie breaking.
    """
    time, event, grid = np.asarray(time, float), np.asarray(event), np.asarray(grid, float)
    weight = np.ones(len(time)) if weights is None else np.asarray(weights, float)
    require(len(time) == len(event) == len(weight) and len(time) > 0, "INVALID_AJ_SHAPE")
    require(np.isfinite(time).all() and (time > 0).all() and np.isin(event, [0, 1, 2]).all(), "INVALID_AJ_INPUT")
    require(np.isfinite(weight).all() and (weight >= 0).all() and weight.sum() > 0, "INVALID_AJ_WEIGHT")
    require(np.isfinite(grid).all() and (grid >= 0).all() and (np.diff(grid) >= 0).all(), "INVALID_AJ_GRID")
    times, inverse = np.unique(time, return_inverse=True)
    total = np.bincount(inverse, weights=weight)
    death = np.bincount(inverse, weights=weight * (event == 1), minlength=len(times))
    discharge = np.bincount(inverse, weights=weight * (event == 2), minlength=len(times))
    risk = np.cumsum(total[::-1])[::-1]
    step = np.divide(death + discharge, risk, out=np.zeros_like(risk), where=risk > 0)
    survival_after = np.cumprod(1 - np.clip(step, 0, 1))
    survival_before = np.r_[1.0, survival_after[:-1]]
    cif1 = np.cumsum(survival_before * np.divide(death, risk, out=np.zeros_like(risk), where=risk > 0))
    cif2 = np.cumsum(survival_before * np.divide(discharge, risk, out=np.zeros_like(risk), where=risk > 0))
    indices = np.searchsorted(times, grid, side="right")
    return np.column_stack([np.r_[0.0, cif1][indices], np.r_[0.0, cif2][indices], np.r_[1.0, survival_after][indices]])


def competing_risks(frame, replicates=1000, seed=SEED, grid=GRID):
    require(replicates >= 20, "TOO_FEW_BOOTSTRAP_REPLICATES")
    time = frame.time_to_event_days.to_numpy(dtype=float)
    event = np.where(frame.death_event.to_numpy(dtype=int) == 1, 1, 2)
    exposure = frame.raas_pre_icu.to_numpy(dtype=int)
    codes, patients = pd.factorize(frame.subject_id, sort=True)
    require(len(patients) >= 2 and set(exposure) == {0, 1}, "BOTH_GROUPS_AND_CLUSTERS_REQUIRED")
    masks = [exposure == group for group in (0, 1)]
    curves = [aalen_johansen(time[m], event[m], grid) for m in masks]
    rng = np.random.default_rng(seed)
    draws = np.empty((replicates, 2, len(grid), 2))
    completed = 0
    for _ in range(replicates * 2):
        counts = np.bincount(rng.integers(0, len(patients), len(patients)), minlength=len(patients))
        weights = counts[codes]
        if any(weights[m].sum() == 0 for m in masks):
            continue
        for group, m in enumerate(masks):
            draws[completed, group] = aalen_johansen(time[m], event[m], grid, weights[m])[:, :2]
        completed += 1
        if completed == replicates:
            break
    require(completed == replicates, "BOOTSTRAP_INCOMPLETE")
    bounds = np.quantile(draws, [.025, .975], axis=0)
    differences = draws[:, 1, :, 0] - draws[:, 0, :, 0]
    difference_bounds = np.quantile(differences, [.025, .975], axis=0)
    output = []
    for group, m in enumerate(masks):
        output.append({"raas_order_group": group, "admissions": int(m.sum()),
                       "death_events": int((event[m] == 1).sum()), "discharge_events": int((event[m] == 2).sum()),
                       "curve": [{"day": float(day), "death_cif": float(curves[group][i, 0]),
                                  "discharge_cif": float(curves[group][i, 1]), "still_hospitalized": float(curves[group][i, 2]),
                                  "death_lower_95": float(bounds[0, group, i, 0]), "death_upper_95": float(bounds[1, group, i, 0]),
                                  "discharge_lower_95": float(bounds[0, group, i, 1]), "discharge_upper_95": float(bounds[1, group, i, 1])}
                                 for i, day in enumerate(grid)]})
    return {"estimand": "unadjusted_admission_level_cumulative_incidence", "groups": output,
            "uncertainty": "pointwise_percentile_patient_cluster_bootstrap",
            "bootstrap_replicates": replicates, "bootstrap_seed": seed,
            "death_cif_difference_raas_minus_no_raas": [
                {"day": float(day), "difference": float(curves[1][i, 0] - curves[0][i, 0]),
                 "lower_95": float(difference_bounds[0, i]), "upper_95": float(difference_bounds[1, i])}
                for i, day in enumerate(grid)],
            "cause_specific_cox": {"death": fit_clustered_cox(frame, BASE, 1), "discharge": fit_clustered_cox(frame, BASE, 2)},
            "limitations": ["CIF curves and their differences are unadjusted associations, not treatment effects.",
                            "Pointwise intervals are not simultaneous confidence bands.",
                            "Discharge ends the hospital episode; subsequent out-of-hospital death is outside the outcome."]}


def landmark_frame(frame, days=1.0):
    require(np.isfinite(days) and days > 0, "INVALID_LANDMARK")
    before = frame.time_to_event_days <= days
    fallback = frame.death_time_fallback_flag == 1
    eligible = ~before & ~fallback
    data = frame.loc[eligible].copy()
    data["time_to_event_days"] = data.time_to_event_days.astype(float) - days
    require((data.time_to_event_days > 0).all(), "INVALID_LANDMARK_FOLLOWUP")
    flow = {"original_admissions": len(frame), "landmark_days": days,
            "deaths_at_or_before_landmark": int((before & frame.death_event.eq(1)).sum()),
            "discharges_at_or_before_landmark": int((before & frame.death_event.eq(0)).sum()),
            "additional_fallback_deaths_excluded": int((~before & fallback).sum()),
            "eligible_alive_and_hospitalized": len(data),
            "eligible_missing_core_covariates": len(data) - len(complete_frame(data, CORE))}
    require(flow["original_admissions"] == flow["deaths_at_or_before_landmark"] + flow["discharges_at_or_before_landmark"] + flow["additional_fallback_deaths_excluded"] + len(data), "LANDMARK_FLOW_MISMATCH")
    return data, flow


def landmark_analysis(frame):
    selected, flow = landmark_frame(frame)
    encoded = selected.assign(gender_M=(selected.gender == "M").astype(float))
    common = encoded[CORE + ["anchor_year_group"]].notna().all(axis=1)
    matched = selected.loc[common].copy()
    return {"eligibility": flow, "risk_origin": "24_hours_after_first_ICU_entry_within_admission",
            "exposure_window": "unchanged_prescription_order_starttime_at_or_before_original_ICU_entry",
            "models": {"landmark_age_sex": fit_clustered_cox(matched, BASE), "landmark_first_day_sofa_core": fit_clustered_cox(matched, CORE)},
            "same_complete_cases_in_both_landmark_models": True,
            "sofa_window_basis": "published_first_day_definition_through_ICU_entry_plus_24h",
            "individual_measurement_times_independently_verified": False,
            "limitations": ["Conditional on surviving and remaining hospitalized beyond 24h; this changes the population and estimand.",
                            "Endpoints exactly at 24h and unknown death times are excluded before resetting follow-up.",
                            "The deployed component measurement windows were not independently reconstructed.",
                            "First-day severity is post-exposure and may mediate effects or introduce selection/collider bias; this is not a causal correction.",
                            "This does not reconstruct pre-ICU severity; complete-case missingness can affect selection."]}


def _load_input(repo, clinical):
    if not clinical:
        return synthetic_data(tied=True), {"data_origin": "fully_synthetic_not_MIMIC"}, None
    import current_analysis as source
    reference_path = repo / "docs/CURRENT_ANALYSIS.json"
    reference = json.loads(reference_path.read_text())
    require(source.ANALYSIS_VERSION == reference["analysis_version"], "REFERENCE_VERSION_MISMATCH")
    require(hashlib.sha256(source.QUERY.encode()).hexdigest() == reference["execution"]["query_sha256"], "REFERENCE_SOURCE_QUERY_MISMATCH")
    try:
        frame, execution = source.load_current_data(include_cluster_keys=True)
    except Exception:
        raise SensitivityError("APPROVED_SOURCE_ACCESS_FAILED_NO_ROWS_EXPORTED") from None
    manifest = reference["secondary_python_logistic"]["manifest"]
    actual = {"n": len(frame), "events": int(frame.death_event.sum()), "age_sum": float(frame.age.sum()),
              "duration_sum": float(frame.time_to_event_days.sum())}
    require(all(np.isclose(actual[k], manifest[k], rtol=1e-10, atol=1e-5) for k in actual), "CURRENT_COHORT_REFERENCE_MISMATCH")
    query = source.QUERY.replace("SELECT e.age", "SELECT e.subject_id,e.hadm_id,e.stay_id,e.age", 1)
    return frame, {"data_origin": "authorized_local_current_cohort", "reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
                   "query_sha256": hashlib.sha256(query.encode()).hexdigest(), "execution": execution}, reference


def run_supplement(analysis="all", *, repo=None, clinical=False, bootstrap_replicates=1000):
    repo = Path(repo) if repo else Path(__file__).resolve().parents[1]
    require(analysis in ["all", "cluster", "competing", "landmark"], "UNKNOWN_ANALYSIS")
    frame, provenance, reference = _load_input(repo, clinical)
    validate_frame(frame)
    # BigQuery does not promise row order; fix fitting/bootstrap reproducibility.
    frame = frame.sort_values(["subject_id", "hadm_id", "stay_id"], kind="stable").reset_index(drop=True)
    results = {}
    if analysis in ["all", "cluster"]:
        results["cluster"] = {"models": {"primary_refined": fit_clustered_cox(frame, BASE), "core": fit_clustered_cox(frame, CORE)}}
    if analysis in ["all", "competing"]:
        results["competing"] = competing_risks(frame, bootstrap_replicates)
    if analysis in ["all", "landmark"]:
        results["landmark"] = landmark_analysis(frame)
    if reference:
        comparisons = {}
        candidates = results.get("cluster", {}).get("models", {}).copy()
        if "competing" in results:
            candidates["primary_refined"] = results["competing"]["cause_specific_cox"]["death"]
        # Landmark-only execution still verifies the original primary cohort/fit.
        if not candidates:
            candidates["primary_refined"] = fit_clustered_cox(frame, BASE)
        for name, model in candidates.items():
            saved = reference["models"][name]
            require((model["n"], model["events"], model["strata_count"]) == (saved["n"], saved["deaths"], saved["strata_count"]), "MODEL_REFERENCE_COHORT_MISMATCH")
            differences = []
            for term, estimate in model["estimates"].items():
                actual = {"hr": estimate["hr"], **{k: estimate["ordinary"][k] for k in ["lower_95", "upper_95", "p"]}}
                differences.extend(abs(actual[k] - saved["estimates"][term][k]) for k in actual)
            require(max(differences) <= 1e-4, "ORDINARY_REFERENCE_ESTIMATES_MISMATCH")
            comparisons[name] = {"maximum_absolute_difference": float(max(differences)), "passed": True}
        provenance["ordinary_reference_checks"] = comparisons
    import lifelines, statsmodels
    return {"supplement_version": VERSION, **provenance, "analysis_role": "additional_exploratory_sensitivity_analysis",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "software": {"numpy": np.__version__, "pandas": pd.__version__, "statsmodels": statsmodels.__version__, "lifelines": lifelines.__version__},
            "clinical_records_exported": False, "main_analysis_updated": False, "results": results}


def plot_supplement(bundle, analysis):
    import matplotlib.pyplot as plt
    origin = "SYNTHETIC demonstration" if bundle["data_origin"] == "fully_synthetic_not_MIMIC" else "Local exploratory MIMIC supplement"
    result = bundle["results"][analysis]
    if analysis == "competing":
        fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharex=True)
        for group in result["groups"]:
            rows = pd.DataFrame(group["curve"])
            label = "Qualifying RAAS orders" if group["raas_order_group"] else "No qualifying RAAS orders"
            for ax, cause in zip(axes, ["death", "discharge"]):
                ax.step(rows.day, rows[cause + "_cif"], where="post", label=label)
                ax.fill_between(rows.day, rows[cause + "_lower_95"], rows[cause + "_upper_95"], step="post", alpha=.15)
        for ax, title in zip(axes, ["In-hospital death", "Live discharge"]):
            ax.set(title=title, xlabel="Days since ICU admission", ylabel="Unadjusted cumulative incidence", ylim=(0, 1))
            ax.legend(fontsize=8)
        fig.suptitle(origin + " · patient-bootstrap pointwise 95% intervals")
    else:
        models = result["models"]
        fig, ax = plt.subplots(figsize=(8, 4))
        for i, (name, model) in enumerate(models.items()):
            estimate = model["estimates"]["raas_pre_icu"]
            for offset, label, marker in [(-.12, "ordinary", "o"), (.12, "patient_cluster", "s")]:
                ci = estimate[label]; hr = estimate["hr"]
                ax.errorbar(hr, i + offset, xerr=[[hr-ci["lower_95"]], [ci["upper_95"]-hr]], fmt=marker,
                            color="#1f77b4" if label == "ordinary" else "#d95f02",
                            capsize=3, label=label.replace("_", " ") if i == 0 else None)
        ax.axvline(1, color="gray", ls="--")
        ax.set(xlabel="RAAS hazard ratio (95% CI)", yticks=range(len(models)), yticklabels=list(models), title=origin)
        ax.legend()
    fig.tight_layout()
    return fig


def save_local_bundle(bundle, output, repo):
    output = Path(output).resolve()
    allowed = (Path(repo) / "reports/local_supplements").resolve()
    require(output.is_relative_to(allowed) and output != allowed, "OUTPUT_MUST_BE_NEW_IGNORED_SUPPLEMENT_DIRECTORY")
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    serialized = json.dumps(bundle, indent=2, allow_nan=False)
    output.mkdir(parents=True)
    (output / "aggregate_results.json").write_text(serialized + "\n")
    import matplotlib.pyplot as plt
    for name in bundle["results"]:
        fig = plot_supplement(bundle, name)
        fig.savefig(output / (name + ".png"), dpi=160)
        plt.close(fig)


def load_local_bundle(path, repo, analysis):
    """Read an aggregate-only local run with source/reference provenance checks."""
    path, repo = Path(path).resolve(), Path(repo).resolve()
    require(path.is_relative_to(repo / "reports/local_supplements"), "LOCAL_RESULT_OUTSIDE_IGNORED_DIRECTORY")
    bundle = json.loads(path.read_text())
    require(bundle["supplement_version"] == VERSION, "LOCAL_RESULT_VERSION_MISMATCH")
    require(bundle["source_script_sha256"] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "LOCAL_RESULT_SCRIPT_CHANGED")
    require(analysis in bundle["results"] and bundle["clinical_records_exported"] is False, "INVALID_LOCAL_RESULT")
    if bundle["data_origin"] == "authorized_local_current_cohort":
        require(bundle["reference_sha256"] == hashlib.sha256((repo / "docs/CURRENT_ANALYSIS.json").read_bytes()).hexdigest(), "LOCAL_REFERENCE_CHANGED")
    else:
        require(bundle["data_origin"] == "fully_synthetic_not_MIMIC", "UNKNOWN_LOCAL_DATA_ORIGIN")
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", choices=["all", "cluster", "competing", "landmark"], default="all")
    parser.add_argument("--current-data", action="store_true", help="Explicit approved local MIMIC/BigQuery execution; no row export")
    parser.add_argument("--bootstrap-replicates", type=int, default=1000)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        require(not args.current_data or args.bootstrap_replicates >= 1000, "CLINICAL_BOOTSTRAP_REQUIRES_AT_LEAST_1000_REPLICATES")
        # Validate the destination before authentication or computation.
        allowed = (args.repo / "reports/local_supplements").resolve()
        require(args.output.resolve().is_relative_to(allowed) and args.output.resolve() != allowed and not args.output.exists(), "INVALID_OR_EXISTING_LOCAL_OUTPUT")
        bundle = run_supplement(args.analysis, repo=args.repo, clinical=args.current_data, bootstrap_replicates=args.bootstrap_replicates)
        save_local_bundle(bundle, args.output, args.repo)
    except SensitivityError as exc:
        print(json.dumps({"status": "failed", "code": str(exc), "clinical_rows_exported": False}))
        return 1
    except Exception:
        print(json.dumps({"status": "failed", "code": "UNEXPECTED_ERROR_NO_ROWS_EXPORTED"}))
        return 1
    print(json.dumps({"status": "completed", "data_origin": bundle["data_origin"], "analyses": list(bundle["results"]), "main_analysis_updated": False}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
