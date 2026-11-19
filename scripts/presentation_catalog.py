"""One ordered, per-notebook catalog for all public figure/table captions."""
MAIN = ("Shared Python model aggregates; saved main reference", "../docs/CURRENT_ANALYSIS.json")
SUPPLEMENT = ("Verified supplementary aggregates", "../docs/SURVIVAL_SENSITIVITY_RESULTS.json")
EXECUTION = ("Selected execution aggregates; stored-output provenance", "../docs/NOTEBOOK_PRESENTATION_VALIDATION.json")


def query_source(table, script):
    return (f"BigQuery mimic-iv-portfolio.copd_raas.{table}; {script}", '../sql/'+script)

# Titles and source definitions are editorial metadata; observed values and
# interpretations are computed separately from the selected result object.
CATALOG = {
    "01": {"tables": [("dimensions", "Base adult ICU cohort dimensions", query_source('cohort_icu','01_extract_base.sql'))], "figures": []},
    "02": {"tables": [
        ("binary", "Qualifying pre-ICU RAAS prescription orders", query_source('cohort_copd_raas','02_exposure_raas.sql')),
        ("integrity", "COPD cohort ICU-stay uniqueness", query_source('cohort_copd','02_build_cohort_copd.sql')),
        ("groups", "Four prescription-order groups", query_source('cohort_copd_raas_detailed','02_exposure_raas_detailed.sql'))], "figures": []},
    "03a": {"tables": [
        ("dimensions", "Baseline cohort dimensions", query_source('cohort_copd_baseline','03_build_baseline.sql')),
        ("age", "Estimated admission-age distribution", query_source('cohort_copd_baseline','03_build_baseline.sql')),
        ("binary", "Baseline qualifying RAAS prescription orders", query_source('cohort_copd_baseline','03_build_baseline.sql'))], "figures": []},
    "03b": {"tables": [
        ("merge", "Cohort row counts before and after the exposure merge", query_source('cohort_copd / cohort_copd_with_raas','03_merge_exposures.sql')),
        ("missing", "Missing derived exposure fields", query_source('cohort_copd_with_raas','03_merge_exposures.sql')),
        ("groups", "Merged prescription-order groups", query_source('cohort_copd_with_raas','03_merge_exposures.sql')),
        ("orders", "Qualifying prescription-order flag totals", query_source('cohort_copd_with_raas','03_merge_exposures.sql'))], "figures": []},
    "04a": {"tables": [
        ("coefficients", "Refined primary Cox coefficients", MAIN),
        ("ph", "Refined primary rank PH diagnostics", MAIN)],
        "figures": [("km", "Kaplan–Meier estimates", MAIN)]},
    "04b": {"tables": [
        ("coefficients", "ACEi-only and ARB-only Cox coefficients versus neither", MAIN),
        ("ph", "Prescription-order subclass rank PH diagnostics", MAIN)],
        "figures": [("subgroups", "ACEi-only and ARB-only orders versus neither", MAIN)]},
    "04c": {"tables": [
        ("models", "Exploratory first-day-SOFA and ICU Cox models", MAIN),
        ("icu", "Pooled ICU-category admission counts", MAIN),
        ("stratified", "Exploratory PH-stratified Cox models", MAIN),
        ("ph", "Exploratory stratified-model rank PH diagnostics", MAIN)],
        "figures": [("core", "Exploratory SOFA-core Cox estimates", MAIN),
                    ("sensitivity", "Model sensitivity comparison", MAIN)]},
    "04d": {"tables": [("coefficients", "Secondary Python logistic coefficients", MAIN)], "figures": []},
    "05a": {"tables": [
        ("saved_cohort", "Saved admissions and patient dependence", SUPPLEMENT),
        ("saved_models", "Saved ordinary and patient-cluster Cox inference", SUPPLEMENT),
        ("cohort", "Selected-execution admissions, patients and ties", EXECUTION),
        ("models", "Selected-execution ordinary and patient-cluster Cox inference", EXECUTION)],
        "figures": [("saved", "Ordinary and patient-cluster inference", SUPPLEMENT),
                    ("runtime", "Ordinary and patient-cluster inference — selected execution", EXECUTION)]},
    "05b": {"tables": [
        ("saved_cif", "Saved death and live-discharge cumulative incidence", SUPPLEMENT),
        ("saved_models", "Saved adjusted cause-specific Cox associations", SUPPLEMENT),
        ("cif", "Selected-execution death and live-discharge cumulative incidence", EXECUTION),
        ("models", "Selected-execution adjusted cause-specific Cox associations", EXECUTION)],
        "figures": [("saved", "Death and live-discharge cumulative incidence", SUPPLEMENT),
                    ("runtime", "Death and live-discharge cumulative incidence — selected execution", EXECUTION)]},
    "05c": {"tables": [
        ("saved_eligibility", "Saved sequential 24-hour landmark eligibility", SUPPLEMENT),
        ("saved_models", "Saved matched landmark Cox results", SUPPLEMENT),
        ("eligibility", "Selected-execution sequential landmark eligibility", EXECUTION),
        ("models", "Selected-execution matched landmark Cox results", EXECUTION)],
        "figures": [("saved", "24-hour landmark Cox models", SUPPLEMENT),
                    ("runtime", "Landmark ordinary and patient-cluster inference — selected execution", EXECUTION)]},
}


def metadata(notebook, kind, key):
    prefix = notebook.split("_", 1)[0]
    items = CATALOG[prefix][kind]
    for number, (item_key, title, source) in enumerate(items, 1):
        if key == item_key:
            return {"number": number, "title": title, "source_label": source[0], "source_href": source[1]}
    raise KeyError(f"Unknown {kind} key {prefix}/{key}")


def interval_position(lower, upper):
    """Classify boundaries inclusively: [1, x] and [x, 1] include 1."""
    import math
    if not (math.isfinite(lower) and math.isfinite(upper) and 0 < lower <= upper):
        raise ValueError("A positive, ordered finite HR/OR interval is required")
    if upper < 1:
        return "The interval lies below 1."
    if lower > 1:
        return "The interval lies above 1."
    return "The interval includes 1; this does not establish equivalence or absence of an association."


def relative_to_one(before, after):
    distance_before, distance_after = abs(before - 1), abs(after - 1)
    if distance_after < distance_before:
        return "The second point estimate is closer to 1."
    if distance_after > distance_before:
        return "The second point estimate is farther from 1."
    return "Both point estimates are equally distant from 1."
