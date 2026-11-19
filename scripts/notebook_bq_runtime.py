"""Bounded BigQuery execution for the reproducible notebook pipeline."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

PROJECT = "mimic-iv-portfolio"
SELECT_LIMIT = 200_000_000
BUILD_LIMIT = 20_000_000_000
_client = None


def first_statement(sql):
    quote=None; line=False; block=False; i=0
    while i < len(sql):
        char=sql[i]; following=sql[i:i+2]
        if line:
            if char=='\n':line=False
        elif block:
            if following=='*/':block=False;i+=1
        elif quote:
            if char=='\\':i+=1
            elif char==quote:
                if i+1<len(sql) and sql[i+1]==quote:i+=1
                else:quote=None
        elif following=='--':line=True;i+=1
        elif following=='/*':block=True;i+=1
        elif char in ["'",'"','`']:quote=char
        elif char==';':return sql[:i]
        i+=1
    return sql


def construction_select(sql):
    match=re.search(r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP\s+)?TABLE\s+(?:`[^`]+`|\w+)\s+AS\s+',sql,re.I)
    if not match:raise ValueError("Expected a versioned CTAS script")
    return first_statement(sql[match.end():])


def client_for_notebook():
    global _client
    if _client is None:
        import google.auth
        from google.auth.transport.requests import Request
        from google.cloud import bigquery
        class BoundedRequest(Request):
            def __call__(self,*args,**kwargs):
                kwargs['timeout']=20
                return super().__call__(*args,**kwargs)
        credentials,_=google.auth.default()
        credentials.refresh(BoundedRequest())
        _client=bigquery.Client(project=PROJECT,credentials=credentials)
    return _client


def _audit(record):
    folder=os.environ.get('COPD_NOTEBOOK_RUN_DIR')
    if folder:
        path=Path(folder);path.mkdir(parents=True,exist_ok=True)
        record={'at_utc':datetime.now(timezone.utc).isoformat(),**record}
        with (path/'bigquery_jobs.jsonl').open('a') as stream:
            stream.write(json.dumps(record,allow_nan=False)+'\n')


def _dry_run(query,limit):
    from google.cloud import bigquery
    dry=client_for_notebook().query(query,location='US',job_config=bigquery.QueryJobConfig(dry_run=True,use_query_cache=False),timeout=30,retry=None)
    size=int(dry.total_bytes_processed or 0)
    if size>limit:raise ValueError('Notebook query exceeds its dry-run byte guard')
    return size


def run_sql_script(path):
    from google.cloud import bigquery
    path=Path(path);sql=path.read_text()
    size=_dry_run(construction_select(sql),BUILD_LIMIT)
    job=client_for_notebook().query(sql,location='US',job_config=bigquery.QueryJobConfig(maximum_bytes_billed=BUILD_LIMIT,use_query_cache=False),timeout=30,retry=None,job_retry=None)
    job.result(timeout=600,retry=None)
    _audit({'kind':'construction','script':path.name,'sql_sha256':hashlib.sha256(sql.encode()).hexdigest(),
            'dry_run_select_bytes':size,'processed_bytes':job.total_bytes_processed,'billed_bytes':job.total_bytes_billed,
            'job_id':job.job_id,'status':'passed'})
    print('Executed SQL script:',path.name)


def query_to_df(query):
    from google.cloud import bigquery
    size=_dry_run(query,SELECT_LIMIT)
    job=client_for_notebook().query(query,location='US',job_config=bigquery.QueryJobConfig(maximum_bytes_billed=SELECT_LIMIT,use_query_cache=False),timeout=30,retry=None,job_retry=None)
    result=job.result(timeout=180,retry=None).to_dataframe(create_bqstorage_client=False)
    _audit({'kind':'validation_select','query_sha256':hashlib.sha256(query.encode()).hexdigest(),
            'dry_run_bytes':size,'processed_bytes':job.total_bytes_processed,'billed_bytes':job.total_bytes_billed,
            'job_id':job.job_id,'status':'passed'})
    return result
