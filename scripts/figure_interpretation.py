"""Reader-facing explanations derived only from saved public aggregate results."""
from notebook_figure_layout import bullet_guide, format_guide


def hr(e):
    return f"{e['hr']:.3f} (95% CI {e['lower_95']:.3f}–{e['upper_95']:.3f})"


def main_notes(r):
    core = r["models"]["core"]["estimates"]["raas_pre_icu"]
    primary = r["models"]["primary_refined"]["estimates"]["raas_pre_icu"]
    sub = r["models"]["subgroups"]["estimates"]
    notes = {
        "km": "\n".join([
            "**How to read the Kaplan–Meier figure**", "",
            "- The horizontal axis is elapsed days since ICU entry; the vertical axis is the unadjusted Kaplan–Meier survival estimate. Blue represents qualifying pre-ICU RAAS orders and orange represents no qualifying orders. Shading shows pointwise 95% confidence intervals.",
            "- Live discharge is censored. Consequently, one minus this curve is not the observed cumulative probability of hospital death when discharge is a competing event; use the separate CIF figure for that question.",
            f"- The overall two-group log-rank p-value is {r['logrank']['p']:.5f}. It compares the unadjusted survival experience over follow-up, rather than testing every plotted day or controlling for age, severity and other confounding.",
            "- Wider intervals in the late tail indicate less precise estimates. Visual separation is an observational association and does not establish a medication benefit. The curve is not an adjusted Cox prediction."]),
        "core": "\n".join([
            "**How to read the exploratory core forest plot**", "",
            "- Each dot is an adjusted hazard ratio; its horizontal bar is an ordinary admission-level 95% confidence interval. Colors distinguish covariate rows, not statistical significance. The dashed line at HR=1 represents equal hazards under the fitted model. The horizontal scale is linear.",
            "- Read the unit of each row: age is per year, SOFA is per point, male sex is relative to female sex, and the binary RAAS/CHF/CKD/diabetes rows compare flag 1 with flag 0. Different units mean that distance from 1 cannot be used to rank clinical importance across rows.",
            f"- The RAAS row is HR {hr(core)} in the era-stratified, unpenalized SOFA-core model. Its interval includes 1, so it does not establish a clear association in this specification; it does not prove equal hazards or no association.",
            "- This is the exploratory 04c model, not the refined primary 04a model or the separate patient-cluster analysis. First-day SOFA may include post-start information. The estimates are conditional associations and cannot establish treatment effects."]),
        "sensitivity": "\n".join([
            "**How to read the model sensitivity comparison**", "",
            "- Every row estimates the same qualifying-RAAS-orders versus no-qualifying-orders contrast under a different Cox specification. Dots are HRs and horizontal bars are that specification's original 95% intervals on a linear scale. Colors separate model rows for readability; these are not different medication groups.",
            f"- The primary estimate is {hr(primary)}; the exploratory SOFA-core estimate is {hr(core)}. The results depend on the specification, and several intervals include HR=1. These plotted intervals use the original inference, not the later patient-cluster intervals or 24-hour landmark population.",
            "- L2 rows use penalization; the ICU and PH-stratified rows change covariates or baseline-hazard strata. Their differences cannot isolate a single confounder, and one interval crossing 1 while another does not is not a test of the difference between estimates.",
            "- SOFA-containing rows are exploratory and can use post-start information. The set of models is a sensitivity analysis of an observational association, not independent replications of a causal treatment effect."]),
        "subgroups": "\n".join([
            "**How to read the ACEi/ARB forest plot**", "",
            "- Both rows use neither qualifying order as the reference. The blue dot is ACEi-only and the orange dot is ARB-only. Each is an age/sex-adjusted, era-stratified HR with an ordinary admission-level 95% interval on a linear scale. HR=1 is the reference line; records with both class flags positive are excluded.",
            f"- ACEi-only orders: {hr(sub['acei_pre_icu'])}; ARB-only orders: {hr(sub['arb_pre_icu'])}. The ACEi interval lies below 1, whereas the ARB interval includes 1.",
            "- Different point estimates or p-value thresholds do not establish a difference between classes. This plot contains no direct ACEi-versus-ARB contrast and does not establish superiority or equivalence.",
            "- The flags describe prescription orders, not verified administration or adherence. These associations do not estimate causal drug effects."]),
    }

    groups = {"km": ((0, 1), (2,), (3,)), "core": ((0, 1), (2,), (3,)),
              "sensitivity": ((0,), (1,), (2, 3)), "subgroups": ((0,), (1,), (2, 3))}
    return {key: bullet_guide(value, *groups[key]) for key,value in notes.items()}


def supplement_notes(data):
    models = data["cluster"]["models"]
    primary, core = models["primary_refined"], models["core"]
    groups = {g["raas_order_group"]: g for g in data["competing"]["groups"]}
    yes, no = groups[1]["curve"][-1], groups[0]["curve"][-1]
    notes = {
        "cluster": "\n".join([
            "**How to read the saved patient-cluster comparison**", "",
            "- Gray circles show ordinary admission-level 95% intervals; blue squares show patient-cluster 95% intervals. Colors distinguish inference methods, not exposure groups. Each pair shares one fitted RAAS HR and the same complete cases; its vertical offset is only for readability.",
            "- The dashed HR=1 line represents equal hazards. Patient clustering allows dependence among repeated admissions from one patient when estimating uncertainty; it does not fit a frailty model, remove confounding or change the exposure definition. A cluster interval can be wider or narrower.",
            f"- The primary HR remains {primary['hr']:.3f}, with patient-cluster CI {primary['patient_cluster']['lower_95']:.3f}–{primary['patient_cluster']['upper_95']:.3f}. The exploratory SOFA-core HR remains {core['hr']:.3f}, with cluster CI {core['patient_cluster']['lower_95']:.3f}–{core['patient_cluster']['upper_95']:.3f}, which includes 1. The core result does not establish equal hazards or equivalence.",
            "- Compare uncertainty methods within a model. The two covariate specifications are not a formal between-model test or evidence of causal treatment benefit; the SOFA timing limitation remains."]),
        "competing": "\n".join([
            "**How to read the saved competing-event figure**", "",
            "- The horizontal axis is days since ICU entry. The left panel is the unadjusted cumulative incidence of hospital death and the right panel is live discharge, treating the other endpoint as competing. Blue denotes qualifying RAAS orders; orange denotes no qualifying orders. Each curve's height is an absolute cumulative probability, not a hazard ratio.",
            "- Shading shows pointwise patient-bootstrap 95% intervals on the saved daily grid. These are not simultaneous confidence bands. The published death panel spans 0–20%, while the discharge panel spans 0–100%; compare the printed percentages rather than line heights between panels.",
            f"- At day 28, death CIF is {100*yes['death_cif']:.2f}% with qualifying orders and {100*no['death_cif']:.2f}% without. Live-discharge CIF is {100*yes['discharge_cif']:.2f}% and {100*no['discharge_cif']:.2f}%, respectively. The saved estimates indicate different observed endpoint patterns between the groups.",
            "- These curves are unadjusted associations and do not establish a treatment effect. They answer a different question from the adjusted cause-specific HRs and from Kaplan–Meier curves that censor discharge. No Fine–Gray model is shown."]),
    }

    return {key: bullet_guide(value, (0, 1), (2,), (3,)) for key,value in notes.items()}


RUNTIME_CLUSTER_NOTE = "\n".join([
    "**How to read this runtime figure**", "",
    "- Check the title and the printed `data_origin` first. A SYNTHETIC demonstration uses artificial data and is not a clinical MIMIC finding.",
    "- In this runtime layout, blue circles show ordinary 95% intervals and orange squares show patient-cluster 95% intervals. These colors differ from the saved public figure's styling; in both figures the legend identifies uncertainty methods, not exposure groups.",
    "- Within each model, both markers have the same fitted HR. Their vertical separation is for visibility; changes in bar length or p-value reflect uncertainty estimation. The dashed line is HR=1. Read model row labels because the runtime layout can use a different row order.",
    "- An interval including 1 does not prove no association or equivalence. Clustering addresses within-patient dependence in inference; it does not validate a causal effect or remove the first-day-SOFA timing limitation."])

RUNTIME_COMPETING_NOTE = "\n".join([
    "**How to read this runtime figure**", "",
    "- Check the title and printed `data_origin`: SYNTHETIC values demonstrate software behavior only. The clinical results are the separately labeled saved aggregate figure above.",
    "- Blue represents qualifying RAAS orders and orange represents no qualifying orders. The left curve is death CIF and the right is live-discharge CIF; shading shows pointwise patient-bootstrap 95% intervals. Read each curve as an unadjusted cumulative probability by time, not as a hazard ratio.",
    "- This runtime plot uses a 0–100% vertical range for both panels, while the saved public death panel uses 0–20%. The scale difference changes appearance, not the definition of the probability. The default synthetic bootstrap uses fewer draws than the saved clinical run.",
    "- Treat death and discharge as competing endpoints. The separate adjusted cause-specific Cox table estimates rates among admissions still alive and hospitalized. Curve separation or HR differences do not establish a causal treatment effect."])


RUNTIME_CLUSTER_NOTE = bullet_guide(RUNTIME_CLUSTER_NOTE, (1,), (2,), (0, 3))
_runtime_competing_bullets = [line for line in RUNTIME_COMPETING_NOTE.splitlines() if line.startswith("- ")]
RUNTIME_COMPETING_NOTE = format_guide(
    "\n".join(_runtime_competing_bullets[i] for i in (1, 2)),
    "The curves and table describe cumulative incidence for the selected execution input. Read its day-specific values from the table above.",
    "\n".join(_runtime_competing_bullets[i] for i in (0, 3)))


RUNTIME_LANDMARK_NOTE = """**How to read this execution figure**

- Read the title and the `data_origin` printed for this execution first. If the title says **SYNTHETIC demonstration**, the numerical values are artificial software examples, not MIMIC findings. The saved clinical estimates are in Figure 1 above.
- `landmark_age_sex` is the age/sex model with era strata. `landmark_first_day_sofa_core` additionally includes first-day SOFA, CHF, CKD and diabetes. Use the row labels to identify the models; this runtime plot uses its own row order and a linear horizontal scale.
- **Blue circles** show ordinary admission-level 95% intervals; **orange squares** show patient-cluster 95% intervals. The colors distinguish uncertainty methods, not RAAS-exposed and unexposed groups. Each horizontal bar is a confidence interval.
- Within one model, the two methods share the same fitted RAAS HR. Their vertical offsets only separate the symbols visually. Only the uncertainty calculation changes; clustering allows dependence among repeated admissions from the same patient. A cluster interval can be wider or narrower, so clustering does not guarantee a particular p-value change.
- The dashed line is HR=1. An interval crossing it does not establish equal hazards or absence of an association. This plot compares variance methods within each model; it is not an independent clinical validation or a causal treatment comparison."""
RUNTIME_LANDMARK_NOTE = bullet_guide(RUNTIME_LANDMARK_NOTE, (1, 2), (3,), (0, 4))
