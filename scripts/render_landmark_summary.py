"""Make 05c readable without execution using verified, public aggregates only."""
from pathlib import Path

from report_survival_supplement import load_public, interval
from figure_interpretation import RUNTIME_LANDMARK_NOTE
from notebook_figure_layout import saved_intro, saved_figure_block, normalize_runtime, validate_layout, normalize_input_context
from notebook_presentation import table_block, model_sentence, eligibility_summary
from presentation_catalog import interval_position, relative_to_one

NOTEBOOK = "05c_time_aligned_severity.ipynb"
FIGURE = "supplementary_landmark_forest.png"
MARKER = "<!-- Generated public landmark summary: "
MODELS = [("landmark_age_sex", "Age/sex/era"),
          ("landmark_first_day_sofa_core", "Exploratory SOFA core")]


def summary_sections(data, source_href="SURVIVAL_SENSITIVITY_RESULTS.json"):
    landmark = data["landmark"]
    flow = landmark["eligibility"]
    first = landmark["models"][MODELS[0][0]]
    steps = [("Original ICU-entry cohort", flow["original_admissions"]),
             ("Excluded: death at or before 24 hours", flow["deaths_at_or_before_landmark"]),
             ("Excluded: live discharge at or before 24 hours", flow["discharges_at_or_before_landmark"]),
             ("Excluded: remaining death with unknown death time", flow["additional_fallback_deaths_excluded"]),
             ("Eligible: alive and hospitalized beyond 24 hours", flow["eligible_alive_and_hospitalized"]),
             ("Excluded: missing core covariates among eligible admissions", flow["eligible_missing_core_covariates"]),
             ("Analyzed in each matched landmark model", first["n"])]
    intro = saved_intro(source_href)
    eligibility = ["| Eligibility step | Admissions |", "| --- | ---: |"]
    eligibility += [f"| {label} | {count:,} |" for label, count in steps]
    eligibility=[table_block('05c','saved_eligibility','\n'.join(eligibility),eligibility_summary(flow,first),source_href)]
    models = ["| Model | Admissions | Deaths | Adjusted HR | Patient-cluster 95% CI | p |",
              "| --- | ---: | ---: | ---: | --- | ---: |"]
    for key, label in MODELS:
        model = landmark["models"][key]
        ci = model["patient_cluster"]
        p = f"{ci['p']:.5f}" if ci["p"] >= .00001 else "<0.00001"
        models.append(f"| {label} | {model['n']:,} | {model['events']:,} | {model['hr']:.3f} | {interval(ci)} | {p} |")
    models=[table_block('05c','saved_models','\n'.join(models),
                        ' '.join(model_sentence(label,landmark['models'][key],'patient_cluster') for key,label in MODELS),source_href)]
    age_sex = landmark["models"]["landmark_age_sex"]
    core = landmark["models"]["landmark_first_day_sofa_core"]
    guide = ("**How to read**\n\n"
              "- Each blue dot is the adjusted hazard ratio for qualifying pre-ICU RAAS orders versus no qualifying orders. "
              "Each horizontal line is its patient-cluster 95% confidence interval; it is not a distribution of patient outcomes.\n"
              "- The dashed line at HR=1 represents equal hazards under the fitted model. Points to its left indicate a lower estimated death hazard, "
              "and points to its right indicate a higher estimated hazard. This is a hazard comparison, not an absolute mortality probability. "
              "The horizontal axis uses a logarithmic scale.\n"
              "- The first row adjusts for age and sex with era strata. The second additionally includes first-day SOFA, CHF, CKD and diabetes. "
              f"Both use the same {first['n']:,} admissions alive and hospitalized beyond 24 hours, with follow-up beginning at that landmark.\n\n"
              "**What the results show**\n\n"
              f"- Age/sex/era: HR {age_sex['hr']:.3f} (95% CI {interval(age_sex['patient_cluster'])}). "
              f"{interval_position(age_sex['patient_cluster']['lower_95'],age_sex['patient_cluster']['upper_95'])}\n"
              f"- Exploratory SOFA core: HR {core['hr']:.3f} (95% CI {interval(core['patient_cluster'])}). "
              f"{relative_to_one(age_sex['hr'],core['hr'])} {interval_position(core['patient_cluster']['lower_95'],core['patient_cluster']['upper_95'])}\n\n"
              "**Interpretation limits**\n\n"
              "The two rows are different adjustment specifications, not separate treatment groups or a formal test between model estimates. "
              "Differences in whether intervals include 1 do not establish a statistically significant difference between the estimates. "
              "Their change cannot be attributed solely to controlling baseline severity: first-day SOFA is post-exposure, "
              "and individual component times remain independently unverified. The landmark also changes the population and time origin "
              "relative to the original ICU-entry analysis. Neither row establishes a causal treatment effect.")
    figure=saved_figure_block('05c','saved',f'../assets/{FIGURE}',guide,source_href)
    return [("intro", intro), ("eligibility", "\n".join(eligibility)),
            ("models", "\n".join(models)), ("figure", figure)]


def export_figure(repo, data):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import NullLocator
    first = data["landmark"]["models"][MODELS[0][0]]
    with plt.rc_context({"font.size": 11}):
        fig, ax = plt.subplots(figsize=(10, 3.8))
        for i, (key, _) in enumerate(MODELS):
            model = data["landmark"]["models"][key]
            hr, ci = model["hr"], model["patient_cluster"]
            ax.errorbar(hr, i, xerr=[[hr-ci["lower_95"]], [ci["upper_95"]-hr]],
                        fmt="o", color="#1f77b4", capsize=4, markersize=7)
            ax.text(1.04, i, f"{hr:.3f} ({interval(ci)})", transform=ax.get_yaxis_transform(),
                    va="center", fontsize=11)
        ax.axvline(1, color="#777777", ls="--", lw=1)
        ax.set_xscale("log")
        ax.set_xlim(.5, 1.2)
        ax.set_xticks([.5, .75, 1., 1.2], ["0.50", "0.75", "1.00", "1.20"])
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_yticks(range(len(MODELS)), [label for _, label in MODELS])
        ax.set_ylim(1.6, -.6)
        ax.set_xlabel("Adjusted RAAS hazard ratio (patient-cluster 95% CI)")
        ax.grid(axis="x", color="#dddddd", lw=.6)
        ax.set_axisbelow(True)
        fig.suptitle("24-hour landmark: RAAS prescription-order association", y=.98, fontsize=14)
        fig.text(.03, .86, f"Qualifying orders vs no qualifying orders; {first['n']:,} admissions, "
                 f"{first['events']:,} deaths; matched complete cases", fontsize=10)
        fig.text(.03, .035, "Follow-up begins 24 hours after ICU entry. Exploratory observational results; no causal inference.", fontsize=9)
        fig.subplots_adjust(left=.28, right=.69, top=.75, bottom=.25)
        folder = repo / "assets"
        folder.mkdir(parents=True, exist_ok=True)
        fig.savefig(folder / FIGURE, dpi=180)
        plt.close(fig)


def generate(repo):
    import nbformat
    data = load_public(repo)
    if data is None:
        raise ValueError("Published supplementary results required for the 05c preview")
    path = repo / "notebooks" / NOTEBOOK
    notebook = nbformat.read(path, as_version=4)
    # Replace only this generator's markdown; preserve all execution cells and outputs.
    existing_ids = {cell.source[len(MARKER):].split(";", 1)[0]: cell.id
                    for cell in notebook.cells if cell.cell_type == "markdown" and cell.source.startswith(MARKER)}
    cells = [cell for cell in notebook.cells if not
             (cell.cell_type == "markdown" and cell.source.startswith(MARKER))]
    insert_at = next(i for i,cell in enumerate(cells) if cell.cell_type == "markdown"
                     and cell.source.startswith("## Context & Methods"))
    preview = []
    for name, text in summary_sections(data, "../docs/SURVIVAL_SENSITIVITY_RESULTS.json"):
        preview.append(nbformat.v4.new_markdown_cell(
            f"{MARKER}{name}; edit scripts/render_landmark_summary.py -->\n\n{text}",
            id=existing_ids.get(name, "public-landmark-" + name)))
    notebook.cells = cells[:insert_at] + preview + cells[insert_at:]
    normalize_input_context(notebook,NOTEBOOK)
    normalize_runtime(notebook,'landmark',RUNTIME_LANDMARK_NOTE)
    validate_layout(notebook)
    nbformat.validate(notebook)
    export_figure(repo, data)
    nbformat.write(notebook, path)


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[1])
    print("Updated 05c public tables and figure from verified aggregates; no clinical data access.")
