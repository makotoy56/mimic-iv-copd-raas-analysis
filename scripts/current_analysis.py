"""Current ICU-COPD results and figures from one versioned, aggregate-only workflow."""
from __future__ import annotations

import argparse
import hashlib
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test, proportional_hazard_test

ANALYSIS_VERSION = "admission_age_elapsed_time_los_v2"
LOGISTIC_SPEC = "raas_pre_icu+age+gender+sofa_score+charlson_comorbidity+chf+ckd+diabetes"
RARE_ICU_MIN_N = 50
QUERY = """SELECT e.age,e.anchor_age,e.age_anchor_topcoded,e.gender,e.anchor_year_group,
 e.raas_pre_icu,e.death_event,e.time_to_event_days,e.death_time_fallback_flag,
 e.icu_los,e.hosp_los,e.sofa_score,e.charlson_comorbidity_index,e.chf,e.ckd,e.diabetes,e.icu_type,
 r.acei_pre_icu,r.arb_pre_icu
FROM `mimic-iv-portfolio.copd_raas.cohort_copd_outcomes_extended` e
LEFT JOIN `mimic-iv-portfolio.copd_raas.cohort_copd_raas_detailed` r USING(subject_id,hadm_id,stay_id)
"""


def load_current_data(*, include_cluster_keys=False):
    import google.auth
    from google.auth.transport.requests import Request
    from google.cloud import bigquery
    class BoundedRequest(Request):
        def __call__(self, *a, **kw):
            kw["timeout"] = 20
            return super().__call__(*a, **kw)
    creds, _ = google.auth.default()
    creds.refresh(BoundedRequest())
    client = bigquery.Client(project="mimic-iv-portfolio", credentials=creds)
    # Supplementary analyses use pseudonymous keys in memory for validation and
    # patient clustering. The ordinary projection and its saved hash stay fixed.
    query = QUERY.replace("SELECT e.age", "SELECT e.subject_id,e.hadm_id,e.stay_id,e.age", 1) if include_cluster_keys else QUERY
    dry = client.query(query, location="US", job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False), timeout=30, retry=None)
    if dry.total_bytes_processed > 200_000_000:
        raise ValueError("Current analysis SELECT exceeds the 200 MB limit")
    job = client.query(query, location="US", job_config=bigquery.QueryJobConfig(maximum_bytes_billed=200_000_000, use_query_cache=False), timeout=30, retry=None, job_retry=None)
    df = job.result(timeout=90, retry=None).to_dataframe(create_bqstorage_client=False)
    if df.time_to_event_days.isna().any() or (df.time_to_event_days <= 0).any():
        raise ValueError("Invalid follow-up in current analysis table")
    if df.death_event.isna().any() or not df.death_event.isin([0, 1]).all():
        raise ValueError("Invalid event indicator")
    return df, {"job_id": job.job_id, "dry_run_bytes": dry.total_bytes_processed,
                "processed_bytes": job.total_bytes_processed, "billed_bytes": job.total_bytes_billed}


def pool_icu_categories(values: pd.Series, minimum_n: int = RARE_ICU_MIN_N):
    """Pool by admission frequency alone, independently of outcome or model estimates."""
    counts = values.value_counts(dropna=True)
    rare = sorted(str(k) for k, n in counts.items() if n < minimum_n)
    grouped = values.astype("string").replace({k: "Other (rare ICU types)" for k in rare})
    return grouped, rare


def fit_cox(data, covariates, strata, penalty=0.0, formula=None):
    cols = ["time_to_event_days", "death_event"] + list(dict.fromkeys(strata + covariates))
    fit_df = data[cols].dropna().copy()
    for col in fit_df.columns:
        fit_df[col] = fit_df[col].astype(str) if col in strata else fit_df[col].astype(float)
    if any(fit_df[c].nunique() < 2 for c in covariates):
        raise ValueError("A Cox covariate has zero variance")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model = CoxPHFitter(penalizer=penalty).fit(fit_df, "time_to_event_days", "death_event", strata=strata or None, formula=formula)
        ph = proportional_hazard_test(model, fit_df, time_transform="rank").summary
    summary = model.summary
    grouped = fit_df.groupby(strata, observed=True) if strata else None
    sizes = grouped.size() if grouped is not None else pd.Series([len(fit_df)])
    events = grouped.death_event.sum() if grouped is not None else pd.Series([fit_df.death_event.sum()])
    info = {"n": len(fit_df), "deaths": int(fit_df.death_event.sum()), "penalizer": penalty,
            "strata": strata, "strata_count": int(fit_df.groupby(strata, observed=True).ngroups) if strata else 1,
            "single_admission_strata": int((sizes == 1).sum()), "zero_event_strata": int((events == 0).sum()),
            "admissions_in_zero_event_strata": int(sizes.loc[events == 0].sum()),
            "estimates": {str(c): {"hr": float(row["exp(coef)"]), "lower_95": float(row["exp(coef) lower 95%"]),
                                    "upper_95": float(row["exp(coef) upper 95%"]), "p": float(row.p)} for c, row in summary.iterrows()},
            "ph_rank_p": {str(c): float(row.p) for c, row in ph.iterrows()},
            "warnings": sorted({str(w.message) for w in caught})}
    return model, info


def fit_secondary_logistic(df):
    import statsmodels.api as sm
    cols = ["death_event", "raas_pre_icu", "age", "gender", "sofa_score", "charlson_comorbidity_index", "chf", "ckd", "diabetes"]
    data = df[cols].dropna().copy()
    data["gender_M"] = (data.gender == "M").astype(int)
    xs = ["raas_pre_icu", "age", "gender_M", "sofa_score", "charlson_comorbidity_index", "chf", "ckd", "diabetes"]
    model = sm.Logit(data.death_event.astype(float), sm.add_constant(data[xs].astype(float))).fit(disp=False)
    ci = model.conf_int()
    names = {"const": "Intercept", "gender_M": "gender", "charlson_comorbidity_index": "charlson_comorbidity"}
    params = pd.DataFrame([{"Variable": names.get(c, c), "Python_Estimate": float(v), "Python_OR": float(np.exp(v)),
                            "Python_pvalue": float(model.pvalues[c]), "Python_CI_Lower": float(np.exp(ci.loc[c, 0])),
                            "Python_CI_Upper": float(np.exp(ci.loc[c, 1]))} for c, v in model.params.items()])
    # Retain aggregate cohort provenance with the optional secondary Python fit.
    manifest = {"analysis_version": ANALYSIS_VERSION, "model_spec": LOGISTIC_SPEC, "n": len(data),
                "events": int(data.death_event.sum()), "age_sum": float(data.age.sum()),
                "duration_sum": float(df.loc[data.index, "time_to_event_days"].sum())}
    return params, manifest



def compute_current(df):
    encoded = df.copy()
    encoded["gender_M"] = (encoded.gender == "M").astype(int)
    encoded["icu_type_group"], rare = pool_icu_categories(encoded.icu_type)
    icu_dummies = pd.get_dummies(encoded.icu_type_group, prefix="icu_group", drop_first=True, dtype=float)
    encoded = pd.concat([encoded, icu_dummies], axis=1)
    base = ["raas_pre_icu", "age", "gender_M"]
    core = base + ["sofa_score", "chf", "ckd", "diabetes"]
    icu = core + list(icu_dummies)
    era = ["anchor_year_group"]
    specs = [("primary_refined", encoded, base, era, 0.0),
             ("subgroups", encoded.loc[~((encoded.acei_pre_icu == 1) & (encoded.arb_pre_icu == 1))], ["acei_pre_icu", "arb_pre_icu", "age", "gender_M"], era, 0.0),
             ("core", encoded, core, era, 0.0), ("core_penalized", encoded, core, era, 0.1),
             ("icu_pooled", encoded, icu, era, 0.0), ("icu_pooled_penalized", encoded, icu, era, 0.01),
             # Exploratory response to the diagnosed non-PH nuisance covariates.
             # Exact SOFA strata remove a linear functional-form assumption for SOFA.
             ("core_ph_stratified", encoded, base + ["ckd", "diabetes"], era + ["chf", "sofa_score"], 0.0),
             ("icu_ph_stratified", encoded, base + ["ckd", "diabetes"], era + ["chf", "sofa_score", "icu_type_group"], 0.0)]
    result = {"analysis_version": ANALYSIS_VERSION, "n": len(df), "deaths": int(df.death_event.sum()),
              "fallback_deaths": int(df.death_time_fallback_flag.sum()), "models": {},
              "rare_icu_rule": {"minimum_admissions": RARE_ICU_MIN_N, "pooled_labels": rare,
                                "group_counts": {str(k): int(v) for k, v in encoded.icu_type_group.value_counts().items()}}}
    models = {}
    for name, data, covs, strata, penalty in specs:
        model, info = fit_cox(data, covs, strata, penalty)
        models[name] = model
        result["models"][name] = info
    # Initial 04a treats era as a covariate; keep this distinct from refined 04a.
    initial = encoded[["time_to_event_days", "death_event", "raas_pre_icu", "age", "gender_M", "anchor_year_group"]].dropna()
    for col in initial.columns:
        if col != "anchor_year_group":
            initial[col] = initial[col].astype(float)
    model = CoxPHFitter().fit(initial, "time_to_event_days", "death_event", formula="raas_pre_icu+age+gender_M+C(anchor_year_group)")
    s = model.summary.loc["raas_pre_icu"]
    result["initial_primary"] = {"hr": float(s["exp(coef)"]), "lower_95": float(s["exp(coef) lower 95%"]), "upper_95": float(s["exp(coef) upper 95%"]), "p": float(s.p)}
    kms = {}
    for group in (0, 1):
        g = df.loc[df.raas_pre_icu == group]
        kms[group] = KaplanMeierFitter().fit(g.time_to_event_days, g.death_event, label=f"{'RAAS exposure' if group else 'No RAAS exposure'} (n={len(g):,})")
    g0, g1 = [df.loc[df.raas_pre_icu == group] for group in (0, 1)]
    lr = logrank_test(g0.time_to_event_days, g1.time_to_event_days, g0.death_event, g1.death_event)
    sub = df.loc[~((df.acei_pre_icu == 1) & (df.arb_pre_icu == 1))].copy()
    groups = np.select([sub.acei_pre_icu.eq(1).to_numpy(dtype=bool, na_value=False), sub.arb_pre_icu.eq(1).to_numpy(dtype=bool, na_value=False)], ["ACEi", "ARB"], default="Neither")
    sub_lr = multivariate_logrank_test(sub.time_to_event_days, groups, sub.death_event)
    result["logrank"] = {"statistic": float(lr.test_statistic), "p": float(lr.p_value)}
    result["subgroup_logrank"] = {"statistic": float(sub_lr.test_statistic), "p": float(sub_lr.p_value)}
    result["baseline"] = {}
    for label, g in [("overall", df), ("no_raas", g0), ("raas", g1)]:
        result["baseline"][label] = {"n": len(g), "deaths": int(g.death_event.sum()), "male": int((g.gender == "M").sum()),
            "chf": int(g.chf.sum()), "ckd": int(g.ckd.sum()), "diabetes": int(g.diabetes.sum()),
            "quantiles": {c: [float(g[c].quantile(q)) for q in (.25, .5, .75)] for c in ["age", "icu_los", "hosp_los", "sofa_score", "charlson_comorbidity_index"]}}
    params, manifest = fit_secondary_logistic(df)
    result["secondary_python_logistic"] = {"manifest": manifest, "parameters": params.to_dict(orient="records")}
    return result, models, kms, params


def export_figures(result, models, kms, assets: Path):
    import matplotlib.pyplot as plt
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["svg.hashsalt"] = ANALYSIS_VERSION
    assets.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    for group in (1, 0):
        kms[group].plot_survival_function(ax=ax, ci_show=True)
    ax.set(xlabel="Days since ICU admission", ylabel="Survival probability", title="In-hospital survival by pre-ICU RAAS exposure")
    ax.text(.98, .08, f"Log-rank p = {result['logrank']['p']:.5f}", transform=ax.transAxes, ha="right")
    fig.text(.01, .005, f"N = {result['n']:,}; live discharge censored; continuous elapsed days; age/time corrections applied.", fontsize=9)
    fig.tight_layout(rect=(0, .03, 1, 1))
    fig.savefig(assets / "kaplan_meier_curve.png", dpi=200)
    plt.close(fig)

    def forest(rows, title, path):
        fig, ax = plt.subplots(figsize=(9, max(3, .55 * len(rows))))
        for i, (label, e) in enumerate(rows):
            ax.errorbar(e["hr"], i, xerr=[[e["hr"]-e["lower_95"]], [e["upper_95"]-e["hr"]]], fmt="o", capsize=3)
            p_text = f"p={e['p']:.5f}" if e['p'] >= .00001 else "p<0.00001"
            ax.text(1.02, i, f"{e['hr']:.3f} ({e['lower_95']:.3f}–{e['upper_95']:.3f}); {p_text}", transform=ax.get_yaxis_transform(), va="center", fontsize=9)
        ax.axvline(1, ls="--", color="grey")
        ax.set_yticks(range(len(rows)), [label for label, _ in rows])
        ax.invert_yaxis()
        ax.set(xlabel="Hazard ratio (95% CI)", title=title)
        fig.subplots_adjust(left=.29, right=.65, bottom=.2)
        svg_options = {"metadata": {"Date": None}} if path.suffix == ".svg" else {}
        fig.savefig(path, dpi=200, bbox_inches="tight", **svg_options)
        if path.suffix == ".svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
        plt.close(fig)
    labels = {"raas_pre_icu": "Pre-ICU RAAS", "age": "Age (per year)", "gender_M": "Male sex", "sofa_score": "SOFA (per point)", "chf": "CHF", "ckd": "CKD", "diabetes": "Diabetes"}
    forest([(labels.get(k,k),v) for k,v in result["models"]["core"]["estimates"].items()], "Extended core Cox model", assets / "cox_forest_plot.png")
    forest([(label, result["models"]["subgroups"]["estimates"][cov]) for label, cov in [("ACEi-only orders", "acei_pre_icu"), ("ARB-only orders", "arb_pre_icu")]], "ACEi-only and ARB-only orders versus neither", assets / "raas_subgroup_forest_plot.svg")
    keys = [("Primary refined", "primary_refined"), ("Extended core", "core"), ("Core + L2 (0.1)", "core_penalized"), ("ICU pooled", "icu_pooled"), ("ICU pooled + L2 (0.01)", "icu_pooled_penalized"), ("Core PH strata (exploratory)", "core_ph_stratified"), ("ICU PH strata (exploratory)", "icu_ph_stratified")]
    forest([(label, result["models"][key]["estimates"]["raas_pre_icu"]) for label, key in keys], "RAAS estimates across model specifications", assets / "cox_model_sensitivity_comparison.svg")


def refresh(repo: Path):
    import shutil
    df, provenance = load_current_data()
    result, models, kms, params = compute_current(df)
    result["execution"] = {**provenance, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "query_sha256": hashlib.sha256(QUERY.encode()).hexdigest()}
    export_figures(result, models, kms, repo / "assets")
    for name in ["kaplan_meier_curve.png", "cox_forest_plot.png", "raas_subgroup_forest_plot.svg", "cox_model_sensitivity_comparison.svg"]:
        shutil.copy2(repo / "assets" / name, repo / "docs/assets" / name)
    (repo / "docs/CURRENT_ANALYSIS.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    out = repo / "python/outputs/python_logistic_parameters.csv"
    params.to_csv(out, index=False)
    out.with_suffix(".manifest.json").write_text(json.dumps(result["secondary_python_logistic"]["manifest"], indent=2) + "\n")
    from render_current_report import generate
    generate(repo)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    r = refresh(args.repo)
    print(json.dumps({"n": r["n"], "deaths": r["deaths"], "models": len(r["models"]), "rare_icu_rule": r["rare_icu_rule"], "execution": r["execution"]}, indent=2))
