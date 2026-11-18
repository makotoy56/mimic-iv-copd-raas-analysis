"""Prepare and render selected verified aggregate sensitivity results.

Reads a saved aggregate run, never BigQuery or admission-level records. The public
record contains only an explicit selection of counts, RAAS estimates and fixed-day
CIF values. Full local output, nuisance coefficients and covariance remain local.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

RESULT_FILE = "SURVIVAL_SENSITIVITY_RESULTS.json"
VALIDATION_FILE = "SURVIVAL_SUPPLEMENTS_VALIDATION.json"
START = "<!-- BEGIN SUPPLEMENTARY SENSITIVITY SUMMARY -->"
END = "<!-- END SUPPLEMENTARY SENSITIVITY SUMMARY -->"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def model_summary(model):
    e = model["estimates"]["raas_pre_icu"]
    out = {key: int(model[key]) for key in ["n", "events", "patients"]}
    out["hr"] = float(e["hr"])
    require(math.isfinite(out["hr"]) and out["hr"] > 0, "Invalid aggregate HR")
    for kind in ["ordinary", "patient_cluster"]:
        out[kind] = {key: float(e[kind][key]) for key in ["lower_95", "upper_95", "p"]}
        values = out[kind]
        require(all(math.isfinite(v) for v in values.values()), "Nonfinite aggregate inference")
        require(0 < values["lower_95"] <= values["upper_95"] and 0 <= values["p"] <= 1, "Invalid aggregate inference")
    return out


def curate(repo, input_path):
    record = json.loads((repo / "docs" / VALIDATION_FILE).read_text())
    require(record["status"] == "passed", "Supplement validation did not pass")
    require(digest(input_path) == record["local_clinical_execution"]["final_aggregate_record_sha256"], "Local aggregate hash mismatch")
    b = json.loads(input_path.read_text())
    require(b["data_origin"] == "authorized_local_current_cohort", "Clinical aggregate origin required")
    require(b["clinical_records_exported"] is False and b["main_analysis_updated"] is False, "Unexpected analysis scope")
    require(b["source_script_sha256"] == record["source_script_sha256"] == digest(repo / "scripts/survival_sensitivity.py"), "Supplement source changed")
    require(b["reference_sha256"] == record["main_analysis_reference_sha256"] == digest(repo / "docs/CURRENT_ANALYSIS.json"), "Main reference changed")
    require(all(x["passed"] for x in b["ordinary_reference_checks"].values()), "Ordinary reference checks failed")
    r = b["results"]
    primary = r["cluster"]["models"]["primary_refined"]
    cluster = {name: model_summary(r["cluster"]["models"][name]) for name in ["primary_refined", "core"]}
    for model in cluster.values():
        require((model["n"], model["events"]) == (primary["n"], primary["events"]), "Cluster comparison cohorts differ")
    competing = r["competing"]
    require(competing["bootstrap_replicates"] >= 1000 and competing["bootstrap_seed"] == 20261118, "Unexpected bootstrap settings")
    fields = ["death_cif", "discharge_cif", "still_hospitalized", "death_lower_95", "death_upper_95", "discharge_lower_95", "discharge_upper_95"]
    groups = []
    for group in competing["groups"]:
        rows = []
        require([row["day"] for row in group["curve"]] == list(range(29)), "Only the fixed daily grid may be published")
        for row in group["curve"]:
            values = {key: float(row[key]) for key in fields}
            require(all(math.isfinite(v) and -1e-10 <= v <= 1 + 1e-10 for v in values.values()), "Invalid CIF probability")
            require(abs(sum(values[k] for k in fields[:3]) - 1) < 1e-8, "CIF probability mass mismatch")
            rows.append({"day": int(row["day"]), **values})
        groups.append({"raas_order_group": int(group["raas_order_group"]), "admissions": int(group["admissions"]), "curve": rows})
    require([g["raas_order_group"] for g in groups] == [0, 1], "Unexpected exposure groups")
    differences = [{"day": int(row["day"]), **{key: float(row[key]) for key in ["difference", "lower_95", "upper_95"]}}
                   for row in competing["death_cif_difference_raas_minus_no_raas"]]
    require([row["day"] for row in differences] == list(range(29)), "Difference grid mismatch")
    for i, row in enumerate(differences):
        require(abs(row["difference"] - (groups[1]["curve"][i]["death_cif"] - groups[0]["curve"][i]["death_cif"])) < 1e-10, "CIF contrast mismatch")
    landmark = r["landmark"]
    keys = ["original_admissions", "landmark_days", "deaths_at_or_before_landmark", "discharges_at_or_before_landmark", "additional_fallback_deaths_excluded", "eligible_alive_and_hospitalized", "eligible_missing_core_covariates"]
    flow = {key: landmark["eligibility"][key] for key in keys}
    require(flow["landmark_days"] == 1.0, "Unexpected landmark")
    require(flow["original_admissions"] == sum(flow[k] for k in ["deaths_at_or_before_landmark", "discharges_at_or_before_landmark", "additional_fallback_deaths_excluded", "eligible_alive_and_hospitalized"]), "Landmark flow mismatch")
    landmark_models = {name: model_summary(landmark["models"][name]) for name in ["landmark_age_sex", "landmark_first_day_sofa_core"]}
    require(len({(m["n"], m["events"]) for m in landmark_models.values()}) == 1, "Landmark complete cases differ")
    require(next(iter(landmark_models.values()))["n"] == flow["eligible_alive_and_hospitalized"] - flow["eligible_missing_core_covariates"], "Landmark sample mismatch")
    return {"schema_version": 1, "analysis_role": "post_hoc_exploratory_sensitivity_analyses", "supplement_version": b["supplement_version"],
            "generated_at_utc": b["generated_at_utc"], "publication_prepared_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_run_sha256": digest(input_path), "source_script_sha256": b["source_script_sha256"], "main_reference_sha256": b["reference_sha256"],
            "validation_record": VALIDATION_FILE,
            "cohort": {key: int(primary[key]) for key in ["n", "events", "patients", "patients_with_multiple_admissions", "admissions_from_repeat_patients"]},
            "cluster": {"inference": "patient_cluster_HC0_Efron_sandwich_normal_Wald", "models": cluster},
            "competing": {"estimand": "unadjusted_admission_level_cumulative_incidence", "intervals": "pointwise_patient_cluster_bootstrap_percentile_95",
                          "bootstrap_replicates": int(competing["bootstrap_replicates"]), "bootstrap_seed": int(competing["bootstrap_seed"]),
                          "groups": groups, "death_cif_difference_raas_minus_no_raas": differences,
                          "cause_specific_cox": {name: model_summary(competing["cause_specific_cox"][name]) for name in ["death", "discharge"]}},
            "landmark": {"eligibility": flow, "models": landmark_models,
                         "individual_measurement_times_independently_verified": False, "pre_ICU_severity_reconstructed": False},
            "limitations": ["Observational prescription-order associations; no causal treatment interpretation.",
                            "CIF curves are unadjusted and distinct from adjusted cause-specific HRs.",
                            "Landmark selection changes the population and time origin; first-day severity is post-exposure.",
                            "Individual SOFA component windows, pre-ICU severity and comorbidity-code timing remain unverified."]}


def load_public(repo):
    path = repo / "docs" / RESULT_FILE
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    validation = json.loads((repo / "docs" / VALIDATION_FILE).read_text())
    require(data["schema_version"] == 1 and validation["status"] == "passed", "Unverified supplementary record")
    require(digest(path) == validation["report_publication"]["results_sha256"], "Published supplementary record changed")
    require(data["main_reference_sha256"] == digest(repo / "docs/CURRENT_ANALYSIS.json"), "Published supplement has a stale main reference")
    require(data["source_script_sha256"] == validation["source_script_sha256"] == digest(repo / "scripts/survival_sensitivity.py"), "Published supplement has a stale source")
    require(data["source_run_sha256"] == validation["local_clinical_execution"]["final_aggregate_record_sha256"], "Published supplement has a different run")
    return data


def interval(value):
    return f"{value['lower_95']:.3f}–{value['upper_95']:.3f}"


def probability(row, cause):
    return f"{100*row[cause+'_cif']:.2f} ({100*row[cause+'_lower_95']:.2f}–{100*row[cause+'_upper_95']:.2f})"


def readme_summary(data):
    primary = data["cluster"]["models"]["primary_refined"]
    groups = data["competing"]["groups"]
    lm = data["landmark"]["models"]["landmark_first_day_sofa_core"]
    return "\n".join([
        "### Supplementary Sensitivity Analyses", "",
        f"- Patient-cluster inference retained the primary HR of {primary['hr']:.3f}, with 95% CI {interval(primary['patient_cluster'])}.",
        f"- Unadjusted day-28 in-hospital death cumulative incidence was {100*groups[1]['curve'][-1]['death_cif']:.1f}% with qualifying RAAS orders and {100*groups[0]['curve'][-1]['death_cif']:.1f}% without; live discharge was a competing event.",
        f"- In the separate 24-hour landmark cohort ({lm['n']:,} admissions), the exploratory SOFA-core HR was {lm['hr']:.3f} (patient-cluster 95% CI {interval(lm['patient_cluster'])}).",
        "", "These post hoc analyses preserve the original main estimates. The landmark changes the population; SOFA component times remain independently unverified. These findings do not establish treatment effects. See the [full supplementary results](https://makotoy56.github.io/mimic-iv-copd-raas-analysis/copd_raas_survival_report.html#supplementary-sensitivity-analyses).", "",
    ])


def report_section(repo):
    data = load_public(repo)
    if data is None:
        return []
    cohort, models = data["cohort"], data["cluster"]["models"]
    lines = ["## Supplementary Sensitivity Analyses {#supplementary-sensitivity-analyses}", "",
             "These post hoc analyses were added after the main analysis. They use the same corrected cohort and prescription-order exposure definition; the original main estimates remain unchanged. The [selected aggregate results](SURVIVAL_SENSITIVITY_RESULTS.json) are bound to the main reference and verified local run by hashes. Full methods and notebook links are in the [supplement guide](SURVIVAL_SENSITIVITY_SUPPLEMENTS.md).", "",
             "### Patient-cluster inference", "",
             f"The {cohort['n']:,} admissions represent {cohort['patients']:,} patients; {cohort['patients_with_multiple_admissions']:,} patients contributed {cohort['admissions_from_repeat_patients']:,} admissions across repeated hospitalizations. Unpenalized age/sex/era and SOFA-core Cox models retain their original complete cases, covariates and Efron ties. Patient-level HC0 sandwich inference sums tie-aware scores across all admissions of each patient. Point estimates are shared by the two variance methods; intervals and two-sided normal Wald p-values can change. No finite-cluster correction or frailty model is used.", "",
             "| Specification | HR | Ordinary 95% CI | Patient-cluster 95% CI | Cluster p |",
             "| --- | ---: | --- | --- | ---: |"]
    for name, label in [("primary_refined", "Primary age/sex/era"), ("core", "Exploratory first-day-SOFA core")]:
        m = models[name]
        lines.append(f"| {label} | {m['hr']:.3f} | {interval(m['ordinary'])} | {interval(m['patient_cluster'])} | {m['patient_cluster']['p']:.5f} |")
    lines += ["", "The primary interval changes little. The SOFA-core cluster interval includes HR=1; this does not establish equivalence or eliminate residual confounding.", "",
              "### Death and live discharge as competing events", "",
              f"A two-cause Aalen-Johansen estimate treats recorded in-hospital death and live discharge as competing endpoints. Curves are unadjusted admission-level cumulative incidence through day 28. Pointwise 95% percentile intervals use {data['competing']['bootstrap_replicates']:,} patient-cluster bootstrap samples, carrying all admissions and exposure groups of each sampled patient together, with fixed patient ordering and seed {data['competing']['bootstrap_seed']}. Tied endpoints use a shared pre-event risk set without jitter. The original discharge-time proxy is retained for the two deaths with missing death timestamps. These intervals are not simultaneous confidence bands.", "",
              "| Qualifying RAAS orders | Day | Death CIF %, 95% CI | Live-discharge CIF %, 95% CI |",
              "| --- | ---: | --- | --- |"]
    for group in data["competing"]["groups"]:
        for row in group["curve"]:
            if row["day"] in [7, 14, 28]:
                lines.append(f"| {'Yes' if group['raas_order_group'] else 'No'} | {row['day']} | {probability(row, 'death')} | {probability(row, 'discharge')} |")
    difference = data["competing"]["death_cif_difference_raas_minus_no_raas"][-1]
    discharge = data["competing"]["cause_specific_cox"]["discharge"]
    lines += ["", f"At day 28, the unadjusted death-CIF difference (qualifying RAAS orders minus no qualifying orders) was {100*difference['difference']:.2f} percentage points (95% CI {100*difference['lower_95']:.2f} to {100*difference['upper_95']:.2f}). This is an unadjusted association, not a treatment effect.", "",
              '![Unadjusted death and live-discharge cumulative incidence; shaded areas are pointwise patient-bootstrap 95% intervals. Panels use different vertical scales.](assets/supplementary_competing_risks.svg){fig-alt="Two panels show unadjusted cumulative incidence of death and live discharge through day 28, by qualifying RAAS prescription orders, with pointwise bootstrap intervals."}', "",
              f"Separate age/sex/era cause-specific Cox models describe rates among admissions still alive and hospitalized. The death HR equals the clustered primary estimate above. The live-discharge HR was {discharge['hr']:.3f} (patient-cluster 95% CI {interval(discharge['patient_cluster'])}; p={discharge['patient_cluster']['p']:.5f}). These adjusted hazard ratios and the unadjusted CIFs answer different questions. No Fine–Gray model is reported.", "",
              "### A separate 24-hour severity landmark", ""]
    flow = data["landmark"]["eligibility"]
    lines += [f"Follow-up starts 24 hours after the original ICU entry among admissions alive and still hospitalized beyond that point. Exclusions were {flow['deaths_at_or_before_landmark']:,} deaths and {flow['discharges_at_or_before_landmark']:,} live discharges at or before 24 hours, plus {flow['additional_fallback_deaths_excluded']:,} remaining deaths with unknown death times. This left {flow['eligible_alive_and_hospitalized']:,} eligible admissions; {flow['eligible_missing_core_covariates']:,} had missing core covariates. Both models use the same complete cases, unchanged pre-ICU prescription-order classification, era strata, and patient-cluster Efron inference; one day is subtracted from eligible follow-up.", "",
              "| Landmark specification | Admissions | Deaths | HR | Patient-cluster 95% CI | p |", "| --- | ---: | ---: | ---: | --- | ---: |"]
    for name, label in [("landmark_age_sex", "Age/sex/era"), ("landmark_first_day_sofa_core", "Exploratory first-day-SOFA core")]:
        m = data["landmark"]["models"][name]
        lines.append(f"| {label} | {m['n']:,} | {m['events']:,} | {m['hr']:.3f} | {interval(m['patient_cluster'])} | {m['patient_cluster']['p']:.5f} |")
    lines += ["", "This is a conditional analysis with a different population and time origin. It relies on the published first-day-SOFA definition through ICU entry plus one day; deployed component windows and individual measurement times have not been independently reconstructed. First-day severity follows exposure and may mediate associations or induce selection/collider bias. Comorbidity-code timing is unchanged. Differences from the ICU-entry analysis cannot isolate baseline severity adjustment. Pre-ICU severity reconstruction remains unperformed.", "",
              "### Validation and interpretation", "", "Ordinary estimates were checked against the saved main reference before these results were saved. Synthetic tied and untied calculations matched R survival for Cox coefficients, ordinary and patient-cluster covariance, and Aalen-Johansen probabilities. That synthetic comparison is not an independent clinical refit of these clustered estimates. The [supplement validation record](SURVIVAL_SUPPLEMENTS_VALIDATION.json) documents the checks and remaining limitations. All three analyses are reported regardless of significance; none establishes a causal treatment effect.", ""]
    return lines


def update_readme(repo, data):
    path = repo / "README.md"
    if not path.exists():
        return
    text = path.read_text()
    block = START + "\n" + readme_summary(data) + END
    if START in text:
        require(text.count(START) == text.count(END) == 1, "Ambiguous README summary markers")
        first, rest = text.split(START, 1)
        _, last = rest.split(END, 1)
        text = first + block + last
    else:
        require(text.count("## Workflow Overview") == 1, "README insertion point missing")
        text = text.replace("## Workflow Overview", block + "\n\n## Workflow Overview")
    path.write_text(text)


def export_figure(repo, data):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    plt.rcParams.update({"svg.fonttype": "none", "svg.hashsalt": "survival_supplement_report_v1", "font.size": 10})
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharex=True)
    for group, color in zip(data["competing"]["groups"], ["#1f77b4", "#d95f02"]):
        label = "Qualifying RAAS orders" if group["raas_order_group"] else "No qualifying RAAS orders"
        rows = group["curve"]; days = [r["day"] for r in rows]
        for ax, cause in zip(axes, ["death", "discharge"]):
            ax.step(days, [r[cause+"_cif"] for r in rows], where="post", color=color, label=label)
            ax.fill_between(days, [r[cause+"_lower_95"] for r in rows], [r[cause+"_upper_95"] for r in rows], step="post", color=color, alpha=.16)
    for ax, title, top in zip(axes, ["In-hospital death", "Live discharge"], [.2, 1.]):
        ax.set(title=title, xlabel="Days since ICU admission", ylabel="Unadjusted cumulative incidence", ylim=(0, top), xlim=(0, 28))
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    for folder in [repo / "assets", repo / "docs/assets"]:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "supplementary_competing_risks.svg"
        fig.savefig(path, metadata={"Date": None})
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


def prepare(repo, input_path):
    data = curate(repo, input_path)
    target = repo / "docs" / RESULT_FILE
    target.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    record_path = repo / "docs" / VALIDATION_FILE
    record = json.loads(record_path.read_text())
    record["local_clinical_execution"]["new_clinical_estimates_published"] = True
    record["report_publication"] = {"results_record": RESULT_FILE, "results_sha256": digest(target),
                                    "selected_aggregate_results_only": True, "main_estimates_replaced": False,
                                    "prepared_at_utc": data["publication_prepared_at_utc"]}
    record_path.write_text(json.dumps(record, indent=2) + "\n")
    export_figure(repo, data)
    update_readme(repo, load_public(repo))
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--input", type=Path, required=True, help="Existing verified aggregate_results.json; no data retrieval")
    args = parser.parse_args()
    prepare(args.repo.resolve(), args.input.resolve())
    print("Prepared selected aggregate report results and figure; no model execution or data retrieval.")
