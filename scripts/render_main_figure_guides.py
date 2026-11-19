"""Keep saved main figures and their explanations visible in 04a–04c."""
from pathlib import Path
import json
import re

from figure_interpretation import main_notes
from notebook_figure_layout import saved_intro, saved_figure_block, validate_layout, normalize_input_context

MARKER = "<!-- Generated main figure guide: "
FIGURES = {"km": ("kaplan_meier_curve.png", "Saved Kaplan–Meier estimates"),
           "core": ("cox_forest_plot.png", "Saved exploratory SOFA-core Cox estimates"),
           "sensitivity": ("cox_model_sensitivity_comparison.svg", "Saved model sensitivity comparison"),
           "subgroups": ("raas_subgroup_forest_plot.svg", "Saved ACEi-only and ARB-only order estimates versus neither")}


def generate(repo):
    import nbformat
    data = json.loads((repo/'docs/CURRENT_ANALYSIS.json').read_text())
    notes = main_notes(data)
    for name, keys in [("04a_outcomes_and_modeling", ["km"]),
                       ("04b_outcomes_and_modeling_raas_subgroups", ["subgroups"]),
                       ("04c_extended_covariate_cox_model", ["core", "sensitivity"])]:
        path = repo/'notebooks'/f'{name}.ipynb'
        book = nbformat.read(path,as_version=4)
        ids = {c.source[len(MARKER):].split(';',1)[0]:c.id for c in book.cells
               if c.cell_type=='markdown' and c.source.startswith(MARKER)}
        cells = [c for c in book.cells if not (c.cell_type=='markdown' and c.source.startswith(MARKER))]
        intro=f'{MARKER}intro; edit scripts/render_main_figure_guides.py -->\n\n'+saved_intro('../docs/CURRENT_ANALYSIS.json')
        inserts=[nbformat.v4.new_markdown_cell(intro,id=ids.get('intro','main-figure-intro'))]
        for number,key in enumerate(keys,1):
            filename,title = FIGURES[key]
            assert (repo/'assets'/filename).is_file(),filename
            title=title.removeprefix('Saved ')
            title=title[:1].upper()+title[1:]
            text=(f'{MARKER}{key}; edit scripts/figure_interpretation.py -->\n\n'+
                  saved_figure_block(name.split('_',1)[0],key,f'../assets/{filename}',notes[key]))
            inserts.append(nbformat.v4.new_markdown_cell(text,id=ids.get(key,'main-figure-'+key)))
        runtime=(f'{MARKER}runtime; edit scripts/render_main_figure_guides.py -->\n\n'
                 '## Runtime execution\n\n'
                 'The following cells run the shared refresh in an authorized BigQuery environment. '
                 'They recompute the current models and exported figures; they are separate from the saved figures above.')
        inserts.append(nbformat.v4.new_markdown_cell(runtime,id=ids.get('runtime','main-runtime-workflow')))
        book.cells = cells[:1]+inserts+cells[1:]
        normalize_input_context(book,name)
        validate_layout(book)
        nbformat.validate(book)
        nbformat.write(book,path)
    update_readme(repo,notes)


def update_readme(repo,notes):
    path=repo/'README.md';text=path.read_text()
    for key,title in [('km','### Kaplan-Meier Survival Curve'),('core','### Exploratory Extended Core Cox Model Forest Plot')]:
        filename,_=FIGURES[key]
        pattern=(re.escape(title)+r'\n\n!\[[^\]]*\]\(assets/'+re.escape(filename)+r'\)\n\n')
        match=re.search(pattern,text)
        if not match:raise ValueError('README figure section missing: '+key)
        end=text.index('\n### Exploratory Extended Core Cox Model Forest Plot',match.end()) if key=='km' else text.index('\nAdditional portfolio figures',match.end())
        text=text[:match.end()]+notes[key]+'\n'+text[end:]
    old='The workflow moves from MIMIC-IV ICU tables to cohort construction, RAAS exposure definition, mortality outcome construction, baseline characterization, Kaplan-Meier and Cox survival analysis, sensitivity modeling, independent Cox calculations, and Quarto reporting.'
    addition='This diagram shows processing stages and their order. The arrows do not represent patient counts, medication effects or a causal diagram.'
    if addition not in text:
        if old not in text:raise ValueError('README workflow paragraph missing')
        text=text.replace(old,old+'\n\n'+addition,1)
    path.write_text(text)


if __name__=='__main__':
    generate(Path(__file__).resolve().parents[1])
    print('Updated saved main-figure guides from public aggregates; no model execution.')
