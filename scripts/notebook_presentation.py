"""Shared result-driven captions, bounded aggregate tables and runtime figures."""
import copy
from html import escape
import re
import pandas as pd
from presentation_catalog import metadata, interval_position
_ACTIVE_INPUT = None


def model_sentence(label, model, inference=None, term='raas_pre_icu', event_label='deaths'):
    estimate = model.get('estimates', {}).get(term, model)
    ci = estimate[inference] if inference else estimate
    n = model.get('n'); events = model.get('events', model.get('deaths'))
    cohort = f" {n:,} admissions" if n is not None else ''
    if events is not None:cohort += f", {events:,} {event_label}"
    if cohort:cohort += '.'
    return (f"{label}: HR {estimate['hr']:.3f} (95% CI {ci['lower_95']:.3f}–{ci['upper_95']:.3f}); "
            f"p={ci['p']:.4g}.{cohort} {interval_position(ci['lower_95'], ci['upper_95'])}")


def selected_origin(bundle):
    origin = bundle['data_origin']
    if origin == 'fully_synthetic_not_MIMIC':
        return 'Fully synthetic demonstration; these numbers are not clinical MIMIC findings.'
    if origin == 'authorized_local_current_cohort':
        if bundle.get('_presentation_replay'):
            return 'Saved clinically validated aggregate input; presentation refreshed without queries or model refitting.'
        return 'Selected clinical aggregate results from the authorized corrected cohort; prescription-order associations.'
    raise ValueError('Unknown result origin')


def source_markdown(meta, bundle=None, source_href=None):
    if bundle is not None and bundle['data_origin']=='fully_synthetic_not_MIMIC':
        return selected_origin(bundle)
    href=source_href or meta['source_href']
    base=f"[{meta['source_label']}]({href})"
    return (selected_origin(bundle)+' '+base) if bundle is not None else base


def _html(markdown):
    from nbconvert.filters.markdown import markdown2html
    return str(markdown2html(markdown))


def _input_signature(bundle):
    return tuple(str(bundle.get(key,'')) for key in ['data_origin','_presentation_replay','generated_at_utc','reference_sha256','source_script_sha256'])


def render_input_context(bundle, mode=None):
    from IPython.display import HTML
    origin=selected_origin(bundle)
    if mode=='local' and not bundle.get('_presentation_replay'):
        origin='Local saved aggregate input; no new query or refit. '+origin
    return HTML(_html('**Input context:** '+origin))


def display_input_context(bundle, mode=None):
    from IPython.display import display
    global _ACTIVE_INPUT
    display(render_input_context(bundle,mode))
    _ACTIVE_INPUT=_input_signature(bundle)


def _ensure_input_context(bundle):
    if bundle is not None and _ACTIVE_INPUT!=_input_signature(bundle):
        display_input_context(bundle)


def table_block(notebook, key, body, summary, source_href=None):
    """Markdown representation used by the saved public aggregate sections."""
    meta=metadata(notebook,'tables',key)
    return (f"### Table {meta['number']} — {meta['title']}\n\n"
            + body.strip()+"\n\n**Summary:** "+summary)


def render_table(notebook, key, frame, summary, bundle=None):
    """Return portable HTML with metadata and summary tied to one result input."""
    from IPython.display import HTML
    from pandas.io.formats.style import Styler
    meta=metadata(notebook,'tables',key)
    data=frame.data if isinstance(frame,Styler) else frame
    if not isinstance(data,pd.DataFrame):raise TypeError('Expected an aggregate DataFrame')
    forbidden={'subject_id','hadm_id','stay_id','admittime','dischtime','deathtime','intime','outtime'}
    names={str(x).lower() for x in data.columns}|{str(x).lower() for x in data.index.names}
    if names & forbidden or len(data)>100 or len(data.columns)>20:
        raise ValueError('Only bounded, identifier-free aggregate tables can be displayed')
    caption=f"Table {meta['number']} — {meta['title']}"
    caption_id='table_'+notebook+'_'+key
    heading='<h3 id="'+caption_id+'">'+escape(caption)+'</h3>'
    if isinstance(frame,Styler):
        rendered=copy.deepcopy(frame).set_uuid(notebook+'_'+key).to_html()
    else:
        rendered=data.to_html(index=not isinstance(data.index,pd.RangeIndex),border=0,escape=True)
    rendered=re.sub(r'<caption[^>]*>.*?</caption>','',rendered,flags=re.S)
    rendered=rendered.replace('<table','<table aria-labelledby="'+caption_id+'"',1)
    return HTML(f'<section class="notebook-table" data-table-number="{meta["number"]}">'
                +heading+rendered+_html('**Summary:** '+summary)+'</section>')


def display_table(notebook, key, frame, summary, bundle=None):
    from IPython.display import display
    _ensure_input_context(bundle)
    display(render_table(notebook,key,frame,summary,bundle))


def dimensions_summary(frame):
    values=dict(zip(frame['Measure'],frame['Value']))
    return f"The cohort contains {int(values['Rows']):,} rows and {int(values['Columns']):,} columns."


def dimensions_frame(shape):
    return pd.DataFrame({'Measure':['Rows','Columns'],'Value':[int(shape[0]),int(shape[1])]})


def merge_summary(frame):
    counts={row['table_name']:int(row['n']) for _,row in frame.iterrows()}
    before,after=counts['cohort_copd'],counts['cohort_copd_with_raas']
    relation='The counts match.' if before==after else f'The row-count difference is {after-before:+,}; review the merge before analysis.'
    return f"Before merge: {before:,} admissions; after merge: {after:,}. "+relation


def missing_summary(frame):
    counts=frame.iloc[0]
    total=int(counts.sum())
    return (f"There are {total:,} missing-field occurrences across {len(counts):,} derived exposure columns. "
            +('No missing values were found in these columns.' if total==0 else 'Review the affected fields before analysis.'))


def orders_summary(frame):
    row=frame.iloc[0]
    return (f"Qualifying orders: ACEi {int(row['acei_users']):,}, ARB {int(row['arb_users']):,}, "
            f"any RAAS class {int(row['any_users']):,}. Class flags may overlap; these are not verified administration counts.")


def integrity_summary(frame):
    row=frame.iloc[0];n,unique=int(row['n_rows']),int(row['n_unique_stays'])
    return (f"{n:,} rows and {unique:,} distinct ICU stays. "
            +('There is one row per ICU stay.' if n==unique else f'There are {n-unique:,} excess rows; investigate duplicate stays.'))


def logistic_summary(parameters, manifest):
    row=parameters.set_index('Variable').loc['raas_pre_icu']
    return (f"Secondary RAAS-order OR {row['Python_OR']:.3f} "
            f"(95% CI {row['Python_CI_Lower']:.3f}–{row['Python_CI_Upper']:.3f}); "
            f"p={row['Python_pvalue']:.4g}; {manifest['n']:,} admissions and {manifest['events']:,} deaths. "
            +interval_position(row['Python_CI_Lower'],row['Python_CI_Upper'])
            +' This binary-outcome model is secondary and its OR is not a survival HR.')


def supplement_models_frame(result, cause_specific=False):
    models=result['cause_specific_cox'] if cause_specific else result['models']
    rows=[]
    for name,model in models.items():
        e=model['estimates']['raas_pre_icu']
        rows.append({'Model':name,'Admissions':model['n'],'Patients':model['patients'],
                     'RAAS HR':e['hr'],
                     'Ordinary 95% CI':f"{e['ordinary']['lower_95']:.3f}–{e['ordinary']['upper_95']:.3f}",
                     'Patient-cluster 95% CI':f"{e['patient_cluster']['lower_95']:.3f}–{e['patient_cluster']['upper_95']:.3f}",
                     'Ordinary p':e['ordinary']['p'],'Patient-cluster p':e['patient_cluster']['p']})
    return pd.DataFrame(rows).style.format({'RAAS HR':'{:.3f}','Ordinary p':'{:.4g}','Patient-cluster p':'{:.4g}'})


def supplement_models_summary(result, cause_specific=False):
    models=result['cause_specific_cox'] if cause_specific else result['models']
    return ' '.join(model_sentence(name,model,'patient_cluster',event_label='live discharges' if cause_specific and name=='discharge' else 'deaths') for name,model in models.items())


def cif_frame(result):
    rows=[]
    for group in result['groups']:
        for row in group['curve']:
            if row['day'] not in [7,14,28]:continue
            rows.append({'Qualifying RAAS orders':'Yes' if group['raas_order_group'] else 'No','Day':int(row['day']),
                         'Death CIF %, 95% CI':f"{100*row['death_cif']:.2f} ({100*row['death_lower_95']:.2f}–{100*row['death_upper_95']:.2f})",
                         'Live-discharge CIF %, 95% CI':f"{100*row['discharge_cif']:.2f} ({100*row['discharge_lower_95']:.2f}–{100*row['discharge_upper_95']:.2f})"})
    return pd.DataFrame(rows)


def binary_orders(frame, count='n'):
    values=frame.set_index('raas_pre_icu')[count]
    yes,no=int(values.get(1,0)),int(values.get(0,0))
    display=frame.rename(columns={count:'Admissions'}).copy()
    display['raas_pre_icu']=display['raas_pre_icu'].map({0:'No qualifying RAAS orders',1:'Qualifying RAAS orders'})
    display=display.rename(columns={'raas_pre_icu':'Prescription-order group'})
    return display,(f"{yes:,} admissions have qualifying RAAS orders and {no:,} have no qualifying orders "
                    f"({yes+no:,} admissions in total). These flags do not verify medication administration.")


def group_summary(frame):
    counts=frame['n']
    return f"The {len(frame):,} prescription-order groups contain {int(counts.sum()):,} admissions in total. Both-class flags do not establish simultaneous treatment."


def ph_summary(frame):
    n=len(frame);significant=int((frame['Rank PH p']<.05).sum())
    return f"All {n:,} covariate-level rank PH tests are shown; {significant:,} have unadjusted p<0.05. These are diagnostic tests, not treatment-effect estimates."


def age_summary(frame):
    values=frame.set_index('Statistic')['Value']
    return (f"Estimated admission age: median {values['50%']:.1f} years, "
            f"range {values['min']:.1f}–{values['max']:.1f}; {int(values['count']):,} nonmissing ages. "
            "Age is approximate; the oldest anchor-age group is aggregated.")


def age_statistics_frame(statistics):
    frame=statistics.rename_axis('Statistic').reset_index(name='Value')
    frame['Unit']=frame['Statistic'].map(lambda key:'admissions' if key=='count' else 'years')
    return frame


def age_table(frame):
    return frame.style.format({'Value':'{:.1f}'}).format('{:,.0f}',subset=(frame.index[frame['Statistic']=='count'],['Value']))


def cif_summary(result):
    rows={g['raas_order_group']:next(r for r in g['curve'] if r['day']==28) for g in result['groups']}
    yes,no=rows[1],rows[0]
    return (f"At day 28, unadjusted death CIF is {100*yes['death_cif']:.2f}% with qualifying RAAS orders "
            f"and {100*no['death_cif']:.2f}% without; live-discharge CIF is "
            f"{100*yes['discharge_cif']:.2f}% and {100*no['discharge_cif']:.2f}%, respectively. "
            f"Intervals use {result['bootstrap_replicates']:,} patient-cluster bootstrap draws and are pointwise, not simultaneous. "
            "These unadjusted associations do not establish treatment effects.")


def eligibility_summary(flow, model=None):
    text=(f"Of {flow['original_admissions']:,} original admissions, "
          f"{flow['deaths_at_or_before_landmark']:,} deaths and {flow['discharges_at_or_before_landmark']:,} live discharges "
          f"occurred at or before {24*flow['landmark_days']:g} hours; "
          f"{flow['additional_fallback_deaths_excluded']:,} remaining deaths with unknown times were excluded. "
          f"{flow['eligible_alive_and_hospitalized']:,} admissions remained eligible, with "
          f"{flow['eligible_missing_core_covariates']:,} subsequently excluded for missing core covariates.")
    if model:text+=f" Both matched models use {model['n']:,} admissions ({model['patients']:,} patients)."
    return text


def runtime_figure_guide(bundle, analysis):
    from figure_interpretation import RUNTIME_CLUSTER_NOTE, RUNTIME_COMPETING_NOTE, RUNTIME_LANDMARK_NOTE
    base={'cluster':RUNTIME_CLUSTER_NOTE,'competing':RUNTIME_COMPETING_NOTE,'landmark':RUNTIME_LANDMARK_NOTE}[analysis]
    result=bundle['results'][analysis]
    if analysis=='competing':summary=cif_summary(result)
    else:
        summary='\n'.join('- '+model_sentence(name,m,'patient_cluster') for name,m in result['models'].items())
        summary+='\n\nThe shared point estimates are compared under ordinary and patient-cluster uncertainty; this is not a treatment comparison.'
    before,tail=base.split('**What the results show**',1)
    _,limits=tail.split('**Interpretation limits**',1)
    return before+'**What the results show**\n\n'+summary+'\n\n**Interpretation limits**'+limits


def display_runtime_figure(bundle, analysis):
    from IPython.display import HTML,display
    import matplotlib.pyplot as plt
    from survival_sensitivity import plot_supplement
    from render_supplement_notebook_summaries import style_competing_figure
    prefix={'cluster':'05a','competing':'05b','landmark':'05c'}[analysis]
    meta=metadata(prefix,'figures','runtime')
    _ensure_input_context(bundle)
    heading=f"### Figure {meta['number']} — {meta['title']}"
    figure=plot_supplement(bundle,analysis)
    if analysis=='competing':figure=style_competing_figure(figure,bundle['results'][analysis])
    origin=('SYNTHETIC demonstration' if bundle['data_origin']=='fully_synthetic_not_MIMIC' else
            'Saved clinical aggregates — presentation replay' if bundle.get('_presentation_replay') else 'Selected clinical aggregate results')
    if analysis=='competing':figure.suptitle(meta['title']+'\n'+origin,fontsize=11)
    else:figure.axes[0].set_title(meta['title']+'\n'+origin,fontsize=11)
    figure.tight_layout()
    display(HTML(_html(heading)))
    display(figure)
    plt.close(figure)
    display(HTML(_html(runtime_figure_guide(bundle,analysis))))


def estimates_table(result,key):
    frame=pd.DataFrame.from_dict(result['models'][key]['estimates'],orient='index')
    frame.index.name='Covariate'
    return frame.rename(columns={'hr':'HR','lower_95':'95% CI lower','upper_95':'95% CI upper','p':'p'}).style.format(
        {'HR':'{:.3f}','95% CI lower':'{:.3f}','95% CI upper':'{:.3f}','p':'{:.4g}'})


def raas_models_table(result,keys):
    rows=[]
    for key in keys:
        m=result['models'][key];e=m['estimates']['raas_pre_icu']
        rows.append({'Model':key,'Admissions':m['n'],'Deaths':m['deaths'],'HR':e['hr'],
                     '95% CI lower':e['lower_95'],'95% CI upper':e['upper_95'],'p':e['p']})
    return pd.DataFrame(rows).style.format({'HR':'{:.3f}','95% CI lower':'{:.3f}','95% CI upper':'{:.3f}','p':'{:.4g}'})


def ph_table(result,keys):
    return pd.DataFrame([{'Model':key,'Covariate':term,'Rank PH p':value}
                         for key in keys for term,value in result['models'][key]['ph_rank_p'].items()]).style.format({'Rank PH p':'{:.4g}'})
