"""Re-execute presentation paths using versioned validated aggregates, without data access.

This is a presentation replay, not a clinical analysis rerun. Scientific loaders,
SQL execution and model fits are replaced explicitly by saved aggregate inputs.
All work is performed in an already isolated --repo copy and a fresh --output.
"""
import argparse
import ast
import copy
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def sha(data):return hashlib.sha256(data).hexdigest()


class TableRows(HTMLParser):
    def __init__(self):
        super().__init__();self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=[]
        if tag in ['th','td']:self.cell=''
    def handle_data(self,data):
        if self.cell is not None:self.cell+=data
    def handle_endtag(self,tag):
        if tag in ['th','td'] and self.cell is not None:self.row.append(self.cell.strip());self.cell=None
        if tag=='tr' and self.row is not None:self.rows.append(self.row);self.row=None


def parse_table(cell):
    import pandas as pd
    html=next(o['data']['text/html'] for o in cell.get('outputs',[]) if 'text/html' in o.get('data',{}))
    parser=TableRows();parser.feed(''.join(html))
    rows=parser.rows
    frame=pd.DataFrame([r[1:] for r in rows[1:]],columns=rows[0][1:],index=[r[0] for r in rows[1:]])
    for column in frame.columns:
        try:frame[column]=pd.to_numeric(frame[column])
        except (ValueError,TypeError):pass
    return frame


def normalized_query(query):return ' '.join(query.split())


def saved_inputs(source_repo, commit):
    from notebook_publication import approved
    def blob(name):return subprocess.check_output(['git','show',commit+':'+name],cwd=source_repo)
    main_bytes=blob('docs/CURRENT_ANALYSIS.json');supp_bytes=blob('docs/SURVIVAL_SENSITIVITY_RESULTS.json')
    record_bytes=blob('docs/NOTEBOOK_EXECUTION_VALIDATION.json')
    record=json.loads(record_bytes);main=json.loads(main_bytes);supp=json.loads(supp_bytes)
    files=[row['notebook'] for row in record['notebooks']]
    fixtures={};books={};source_hashes={}
    for name in files:
        raw=blob('notebooks/'+name);book=json.loads(raw);assert approved(book,record)
        source_hashes[name]=sha(raw);books[name]=book;queries={}
        for cell in book['cells']:
            if cell['cell_type']!='code':continue
            code=''.join(cell['source'])
            try:tree=ast.parse(code)
            except SyntaxError:continue
            strings={}
            for node in ast.walk(tree):
                if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
                    for target in node.targets:
                        if isinstance(target,ast.Name):strings[target.id]=node.value.value
            for node in ast.walk(tree):
                if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name) or node.func.id!='query_to_df':continue
                arg=node.args[0];query=arg.value if isinstance(arg,ast.Constant) else strings[arg.id]
                streams=''.join(''.join(o.get('text','')) for o in cell.get('outputs',[]))
                if re.search(r'SELECT\s+\*',query,re.I):
                    match=re.search(r'Shape:\s*\((\d+),\s*(\d+)\)',streams);assert match
                    info=streams.split('Shape:',1)[0]
                    age={}
                    for output in cell.get('outputs',[]):
                        text=''.join(output.get('data',{}).get('text/plain',''))
                        for key,value in re.findall(r'^(count|mean|std|min|25%|50%|75%|max)\s+([-+\d.eE]+)',text,re.M):age[key]=float(value)
                    queries[normalized_query(query)]={'kind':'shape','shape':[int(match[1]),int(match[2])],'info':info,'age':age}
                else:
                    frame=parse_table(cell)
                    if 'raas_pre_icu' in query and 'exposure_group' in frame.columns:
                        frame['raas_pre_icu']=[0 if str(v).startswith('No ') else 1 for v in frame['exposure_group']]
                        frame=frame[['raas_pre_icu','n']]
                    queries[normalized_query(query)]={'kind':'table','columns':list(frame.columns),'data':frame.values.tolist(),'index':list(frame.index)}
        fixtures[name]=queries
    # Only published RAAS estimates/counts are reconstructed; no nuisance
    # covariance or patient records are required for these presentation paths.
    cluster_extra=parse_table(books['05a_patient_cluster_sensitivity.ipynb']['cells'][10])
    def model(m,extra=None):
        return {'n':m['n'],'events':m['events'],'patients':m['patients'],
                'estimates':{'raas_pre_icu':{k:copy.deepcopy(m[k]) for k in ['hr','ordinary','patient_cluster']}},**(extra or {})}
    cluster={'models':{name:model(m,{key:int(cluster_extra.loc[name,key]) for key in ['patients_with_multiple_admissions','admissions_from_repeat_patients','tied_event_sets_within_era']}) for name,m in supp['cluster']['models'].items()}}
    competing=copy.deepcopy(supp['competing']);competing['cause_specific_cox']={name:model(m) for name,m in competing['cause_specific_cox'].items()}
    landmark=copy.deepcopy(supp['landmark']);landmark['models']={name:model(m) for name,m in landmark['models'].items()}
    bundles={analysis:{'supplement_version':supp['supplement_version'],'data_origin':'authorized_local_current_cohort',
                       'main_analysis_updated':False,'_presentation_replay':True,'results':{analysis:result}}
             for analysis,result in [('cluster',cluster),('competing',competing),('landmark',landmark)]}
    return {'main':main,'bundles':bundles,'queries':fixtures,
            'provenance':{'source_commit':commit,'source_execution_record_sha256':sha(record_bytes),
                          'main_reference_sha256':sha(main_bytes),'supplement_reference_sha256':sha(supp_bytes),'notebook_input_sha256':source_hashes}}


def install_replay(input_path, notebook):
    """Used only by the replay kernel's explicit, unexported setup cell."""
    import pandas as pd
    import notebook_bq_runtime as bq
    import current_analysis as main
    import survival_sensitivity as sensitivity
    inputs=json.loads(Path(input_path).read_text())
    class AgeSummary:
        def __init__(self,values):self.values=values
        def describe(self):return pd.Series(self.values,dtype=float)
    class AggregateShape:
        def __init__(self,saved):self.saved=saved;self.shape=tuple(saved['shape'])
        def info(self):print(self.saved['info'],end='')
        def __getitem__(self,key):
            if key!='age':raise ValueError('Replay exposes aggregate age descriptors only')
            return AgeSummary(self.saved['age'])
    def query(query):
        saved=inputs['queries'][notebook][normalized_query(query)]
        if saved['kind']=='shape':return AggregateShape(saved)
        return pd.DataFrame(saved['data'],columns=saved['columns'],index=saved['index']).reset_index(drop=True)
    def refresh(repo):
        print('Presentation replay: saved main aggregates; no data retrieval or model refitting.')
        return copy.deepcopy(inputs['main'])
    def run(analysis,**kwargs):
        if not kwargs.get('clinical'):raise ValueError('The replay explicitly uses saved clinical aggregates')
        return copy.deepcopy(inputs['bundles'][analysis])
    bq.client_for_notebook=lambda:None
    bq.query_to_df=query
    bq.run_sql_script=lambda path:print('Presentation replay of saved construction evidence:',Path(path).name,'(SQL not executed)')
    main.refresh=refresh
    main.load_current_data=lambda:(None,{'presentation_replay':True})
    main.fit_secondary_logistic=lambda frame:(pd.DataFrame(inputs['main']['secondary_python_logistic']['parameters']),copy.deepcopy(inputs['main']['secondary_python_logistic']['manifest']))
    sensitivity.run_supplement=run


def render(repo,source_repo,commit,output):
    import nbformat
    from nbclient import NotebookClient
    from notebook_figure_layout import validate_layout,validate_tables
    from notebook_publication import source_hash,output_hash
    from datetime import datetime,timezone
    if repo==source_repo:raise ValueError('Use an isolated checkout; the source repository is never overwritten by replay')
    if output.exists():raise ValueError('A fresh replay output directory is required')
    output.mkdir(parents=True)
    inputs=saved_inputs(source_repo,commit)
    for name,expected in [('CURRENT_ANALYSIS.json','main_reference_sha256'),('SURVIVAL_SENSITIVITY_RESULTS.json','supplement_reference_sha256'),('NOTEBOOK_EXECUTION_VALIDATION.json','source_execution_record_sha256')]:
        if sha((repo/'docs'/name).read_bytes())!=inputs['provenance'][expected]:raise ValueError('Replay inputs differ from the validated publication')
    input_path=output/'aggregate_inputs.json';input_path.write_text(json.dumps(inputs,indent=2,allow_nan=False)+'\n')
    kernel_name='copd-presentation-replay';kernel_dir=output/'jupyter/kernels'/kernel_name;kernel_dir.mkdir(parents=True)
    (kernel_dir/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Python aggregate presentation replay','language':'python'}))
    os.environ.update(JUPYTER_PATH=str(output/'jupyter'),JUPYTER_RUNTIME_DIR=str(output/'jupyter/runtime'),MPLCONFIGDIR=str(output/'matplotlib'),COPD_NOTEBOOK_DATA_MODE='current',PYTHONDONTWRITEBYTECODE='1')
    records=[]
    for path in sorted((repo/'notebooks').glob('*.ipynb')):
        if path.name.startswith('00_'):continue
        book=nbformat.read(path,as_version=4)
        for c in book.cells:
            if c.cell_type=='code':c.outputs=[];c.execution_count=None
        setup=nbformat.v4.new_code_cell('import sys\nsys.path.insert(0,'+repr(str(repo/'scripts'))+')\nfrom render_notebook_presentations import install_replay\ninstall_replay('+repr(str(input_path))+','+repr(path.name)+')')
        book.cells.insert(0,setup)
        print('START presentation replay:',path.name,flush=True)
        try:NotebookClient(book,timeout=180,kernel_name=kernel_name,resources={'metadata':{'path':str(path.parent)}},record_timing=False,allow_errors=False).execute()
        except Exception as error:
            import traceback
            (output/'failure.txt').write_text(traceback.format_exc());nbformat.write(book,output/'failed_notebook.ipynb')
            print('FAILED:',path.name,type(error).__name__,flush=True)
            raise RuntimeError('Presentation replay failed; inspect its private failure record') from None
        del book.cells[0]
        figures=validate_layout(book);tables=validate_tables(book,path.stem)
        nbformat.validate(book);nbformat.write(book,path)
        records.append({'notebook':path.name,'status':'passed','source_sha256':source_hash(book),'output_sha256':output_hash(book),
                        'code_cells':sum(c.cell_type=='code' for c in book.cells),'figures':len(figures),'tables':len(tables),'errors':0,
                        'execution_kind':'offline_presentation_replay_from_verified_aggregates'})
        print('PASSED:',path.name,'figures',len(figures),'tables',len(tables),flush=True)
    modules=['presentation_catalog.py','notebook_presentation.py','notebook_figure_layout.py','figure_interpretation.py','render_main_figure_guides.py','render_supplement_notebook_summaries.py','render_landmark_summary.py','render_notebook_presentations.py']
    record={'schema_version':1,'status':'passed','kind':'presentation_refresh_from_saved_validated_aggregates',
            'checked_at_utc':datetime.now(timezone.utc).isoformat(),**inputs['provenance'],
            'new_clinical_data_retrieved':False,'bigquery_jobs':0,'statistical_models_refit':False,'tables_rebuilt':False,
            'presentation_script_sha256':{name:sha((repo/'scripts'/name).read_bytes()) for name in modules},'notebooks':records,
            'scope':'All public notebooks; same validated aggregate values, generated captions/summaries and result-dependent CI interpretation.',
            'limitations':['This is not a new clinical reanalysis or independent statistical revalidation.','The source defaults of 05a–05c remain synthetic; stored clinical aggregate replay outputs identify their origin.']}
    (repo/'docs/NOTEBOOK_PRESENTATION_VALIDATION.json').write_text(json.dumps(record,indent=2)+'\n')
    print('All 11 presentation paths passed; no BigQuery queries or model fits',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True,help='Isolated checkout to update')
    parser.add_argument('--source-repo',type=Path,required=True,help='Git history containing the validated aggregate notebook outputs')
    parser.add_argument('--source-commit',required=True)
    parser.add_argument('--output',type=Path,required=True,help='Fresh ignored replay/audit directory')
    args=parser.parse_args();render(args.repo.resolve(),args.source_repo.resolve(),args.source_commit,args.output.resolve())


if __name__=='__main__':main()
