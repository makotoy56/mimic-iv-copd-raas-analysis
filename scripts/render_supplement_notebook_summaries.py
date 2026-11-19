"""Display saved 05a/05b clinical aggregates without executing clinical models."""
from pathlib import Path

from report_survival_supplement import load_public, interval, probability
from figure_interpretation import supplement_notes, RUNTIME_CLUSTER_NOTE, RUNTIME_COMPETING_NOTE
from notebook_figure_layout import saved_intro, saved_figure_block, normalize_runtime, validate_layout, normalize_input_context
from notebook_presentation import table_block, model_sentence, cif_summary

MARKER = "<!-- Generated saved clinical supplement: "
CLUSTER_FIGURE = "supplementary_cluster_forest.png"
NOTEBOOKS = {"cluster": "05a_patient_cluster_sensitivity.ipynb",
             "competing": "05b_competing_risks.ipynb"}


def pvalue(value):
    return f"{value:.5f}" if value >= .00001 else "<0.00001"


def sections(data, analysis):
    intro = saved_intro('../docs/SURVIVAL_SENSITIVITY_RESULTS.json')
    if analysis == "cluster":
        cohort = data["cohort"]
        counts = ["| Measure | Count |", "| --- | ---: |"]
        for key, label in [("n", "Admissions"), ("events", "In-hospital deaths"),
                           ("patients", "Patients"), ("patients_with_multiple_admissions", "Patients with repeated admissions"),
                           ("admissions_from_repeat_patients", "Admissions contributed by repeat patients")]:
            counts.append(f"| {label} | {cohort[key]:,} |")
        table = ["| Model | HR | Ordinary 95% CI | Patient-cluster 95% CI | Ordinary p | Cluster p |",
                 "| --- | ---: | --- | --- | ---: | ---: |"]
        for key, label in [("primary_refined", "Primary age/sex/era"), ("core", "Exploratory first-day SOFA core")]:
            model = data["cluster"]["models"][key]
            table.append(f"| {label} | {model['hr']:.3f} | {interval(model['ordinary'])} | {interval(model['patient_cluster'])} | {pvalue(model['ordinary']['p'])} | {pvalue(model['patient_cluster']['p'])} |")
        counts=table_block('05a','saved_cohort','\n'.join(counts),
                           f"{cohort['n']:,} admissions represent {cohort['patients']:,} patients; "
                           f"{cohort['patients_with_multiple_admissions']:,} patients contributed "
                           f"{cohort['admissions_from_repeat_patients']:,} admissions across repeated hospitalizations.")
        table=table_block('05a','saved_models','\n'.join(table),
                          ' '.join(model_sentence(label,data['cluster']['models'][key],'patient_cluster') for key,label in [('primary_refined','Primary age/sex/era'),('core','Exploratory SOFA core')]))
        table+='\n\n'+saved_figure_block('05a','saved',f'../assets/{CLUSTER_FIGURE}',supplement_notes(data)['cluster'])
        return [("intro", intro), ("cohort", counts), ("estimates", table)]

    result = data["competing"]
    table = ["| Qualifying RAAS orders | Day | Death CIF %, 95% CI | Live-discharge CIF %, 95% CI |",
             "| --- | ---: | --- | --- |"]
    for group in result["groups"]:
        for row in group["curve"]:
            if row["day"] in [7, 14, 28]:
                table.append(f"| {'Yes' if group['raas_order_group'] else 'No'} | {row['day']} | {probability(row, 'death')} | {probability(row, 'discharge')} |")
    difference = result["death_cif_difference_raas_minus_no_raas"][-1]
    table=[table_block('05b','saved_cif','\n'.join(table),cif_summary(result))]
    table += ["", f"Day-28 death-CIF difference, RAAS minus no RAAS: {100*difference['difference']:.2f} percentage points "
              f"(95% CI {100*difference['lower_95']:.2f} to {100*difference['upper_95']:.2f}).", "",
              saved_figure_block('05b','saved','../assets/supplementary_competing_risks.svg',supplement_notes(data)['competing'])]
    adjusted = ["| Endpoint | HR | Patient-cluster 95% CI | p |", "| --- | ---: | --- | ---: |"]
    for key, label in [("death", "In-hospital death"), ("discharge", "Live discharge")]:
        model = result["cause_specific_cox"][key]
        adjusted.append(f"| {label} | {model['hr']:.3f} | {interval(model['patient_cluster'])} | {pvalue(model['patient_cluster']['p'])} |")
    adjusted=[table_block('05b','saved_models','\n'.join(adjusted),
                          ' '.join(model_sentence(key,model,'patient_cluster',event_label='live discharges' if key=='discharge' else 'deaths') for key,model in result['cause_specific_cox'].items()))]
    adjusted += ["", "The age/sex/era cause-specific models describe rates while alive and hospitalized. "
                 "Their adjusted HRs and the unadjusted CIFs answer different questions. "
                 "No Fine–Gray model or causal treatment effect is claimed."]
    return [("intro", intro), ("cif", "\n".join(table)), ("adjusted", "\n".join(adjusted))]


def export_cluster_figure(repo, data):
    import matplotlib.pyplot as plt
    with plt.rc_context({"font.size": 10}):
        fig, ax = plt.subplots(figsize=(9, 3.9))
        for i, key in enumerate(["primary_refined", "core"]):
            model = data["cluster"]["models"][key]
            for offset, kind, color, marker in [(-.10, "ordinary", "#777777", "o"), (.10, "patient_cluster", "#1f77b4", "s")]:
                hr, ci = model["hr"], model[kind]
                ax.errorbar(hr, i+offset, xerr=[[hr-ci['lower_95']], [ci['upper_95']-hr]],
                            fmt=marker, color=color, capsize=3,
                            label={"ordinary":"Ordinary 95% CI", "patient_cluster":"Patient-cluster 95% CI"}[kind] if i == 0 else None)
        ax.axvline(1, color="#999999", ls="--", lw=1)
        ax.set(yticks=[0, 1], yticklabels=["Primary age/sex/era", "Exploratory SOFA core"],
               xlabel="RAAS hazard ratio (95% CI)", title="Same fitted HR; ordinary and patient-cluster uncertainty",
               xlim=(.5, 1.1), ylim=(1.6, -.6))
        ax.legend(loc="lower left", fontsize=9)
        fig.text(.02, .025, "Saved clinical execution results; same complete cases and Efron ties. Observational associations.", fontsize=9)
        fig.subplots_adjust(left=.27, right=.97, top=.86, bottom=.22)
        (repo/'assets').mkdir(parents=True,exist_ok=True)
        fig.savefig(repo/'assets'/CLUSTER_FIGURE,dpi=180)
        plt.close(fig)


def style_competing_figure(figure, result):
    """Match public exposure colors while keeping all plotted values unchanged."""
    colors = {0: "#ff7f0e", 1: "#1f77b4"}
    labels = {"No qualifying RAAS orders": colors[0], "Qualifying RAAS orders": colors[1]}
    for ax in figure.axes:
        for line in ax.lines:
            if line.get_label() in labels:
                line.set_color(labels[line.get_label()])
        if len(ax.collections) != len(result["groups"]):
            raise ValueError("Unexpected competing-curve interval collections")
        for band, group in zip(ax.collections, result["groups"]):
            band.set_color(colors[group["raas_order_group"]])
        ax.legend(fontsize=8)
    return figure


def generate(repo):
    import nbformat
    data = load_public(repo)
    if data is None:
        raise ValueError("Verified public supplement required for saved notebook summaries")
    for analysis, name in NOTEBOOKS.items():
        path = repo / "notebooks" / name
        notebook = nbformat.read(path, as_version=4)
        cells = [c for c in notebook.cells if not (c.cell_type == "markdown" and c.source.startswith(MARKER))]
        index = next(i for i,c in enumerate(cells) if c.cell_type == "markdown" and c.source.startswith("## Context & Methods"))
        inserts = [nbformat.v4.new_markdown_cell(
            f"{MARKER}{analysis}/{part}; edit scripts/render_supplement_notebook_summaries.py -->\n\n{text}",
            id=f"saved-{analysis}-{part}") for part,text in sections(data,analysis)]
        notebook.cells = cells[:index] + inserts + cells[index:]
        normalize_input_context(notebook,name)
        normalize_runtime(notebook,analysis,RUNTIME_CLUSTER_NOTE if analysis=='cluster' else RUNTIME_COMPETING_NOTE)
        validate_layout(notebook)
        nbformat.validate(notebook)
        nbformat.write(notebook,path)
    export_cluster_figure(repo,data)


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[1])
    print("Updated saved 05a/05b clinical summaries; no clinical data retrieval or model execution.")
