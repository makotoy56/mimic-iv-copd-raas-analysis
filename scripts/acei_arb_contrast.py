"""Unpublished, post-hoc ACEi-only / ARB-only contrast from the existing Cox model.

Default and --aggregate modes never read clinical inputs. --refit-current is an
explicit local-user operation: existing authorized BigQuery access, memory-only
model rows, and ordinary model-based inference matching the public reference.
No primary result, table, figure, notebook or public report is updated.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm

PARAMETERS = ['acei_pre_icu', 'arb_pre_icu', 'age', 'gender_M']
STRATA = ['anchor_year_group']
VERSION = 'admission_age_elapsed_time_los_v2'
TOLERANCE = 1e-4


class ContrastError(ValueError):
    """Messages are fixed status codes, never row values or credentials."""


def require(condition, code):
    if not condition:
        raise ContrastError(code)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def linear_contrast(parameters, covariance_order, covariance):
    """Wald inference for beta_ACEi - beta_ARB, including their covariance."""
    order = list(covariance_order)
    require(len(order) == len(set(order)) and set(order) in [set(PARAMETERS), {'acei_pre_icu','arb_pre_icu'}], 'PARAMETER_KEYS_MISMATCH')
    require(set(parameters) == set(order), 'COEFFICIENT_KEYS_MISMATCH')
    beta = np.array([parameters[name] for name in order], dtype=float)
    matrix = np.asarray(covariance, dtype=float)
    require(matrix.shape == (len(order), len(order)), 'COVARIANCE_SHAPE_MISMATCH')
    require(np.isfinite(matrix).all() and np.isfinite(beta).all(), 'NONFINITE_COEFFICIENT_OR_COVARIANCE')
    require(np.allclose(matrix, matrix.T, rtol=1e-10, atol=1e-12), 'ASYMMETRIC_COVARIANCE')
    require(np.linalg.eigvalsh(matrix).min() >= -1e-10, 'INVALID_COVARIANCE')
    c = np.array([1.0 if p == 'acei_pre_icu' else -1.0 if p == 'arb_pre_icu' else 0.0 for p in order])
    difference = float(c @ beta)
    variance = float(c @ matrix @ c)
    require(variance > 0 and np.isfinite(variance), 'NONPOSITIVE_CONTRAST_VARIANCE')
    se = float(np.sqrt(variance))
    zcrit = float(norm.ppf(0.975))
    bounds = [difference - zcrit * se, difference + zcrit * se]
    result = {'numerator': 'ACEi-only qualifying prescription orders',
              'denominator': 'ARB-only qualifying prescription orders',
              'log_hazard_ratio': difference, 'variance': variance, 'standard_error': se,
              'hazard_ratio': float(np.exp(difference)),
              'lower_95': float(np.exp(bounds[0])), 'upper_95': float(np.exp(bounds[1])),
              'two_sided_wald_p': float(2 * norm.sf(abs(difference / se))),
              'ACEi_ARB_coefficient_covariance': float(matrix[order.index('acei_pre_icu'), order.index('arb_pre_icu')]),
              'contrast': {'acei_pre_icu': 1, 'arb_pre_icu': -1}}
    require(np.isfinite([result[k] for k in ['hazard_ratio','lower_95','upper_95','two_sided_wald_p']]).all(), 'NONFINITE_CONTRAST')
    return result


def model_frame(frame):
    """Exactly the production subgroup exclusion and complete-case variables."""
    encoded = frame.copy()
    encoded['gender_M'] = (encoded.gender == 'M').astype(int)
    excluded_both = (encoded.acei_pre_icu == 1) & (encoded.arb_pre_icu == 1)
    columns = ['time_to_event_days', 'death_event'] + PARAMETERS + STRATA
    complete = encoded.loc[~excluded_both, columns].dropna().copy()
    for name in columns:
        complete[name] = complete[name].astype(str) if name in STRATA else complete[name].astype(float)
    require(complete.death_event.isin([0, 1]).all(), 'INVALID_EVENT_FLAG')
    require((complete.time_to_event_days > 0).all(), 'INVALID_FOLLOWUP')
    require(complete.acei_pre_icu.isin([0, 1]).all() and complete.arb_pre_icu.isin([0, 1]).all(), 'INVALID_ORDER_FLAG')
    require(((complete.acei_pre_icu + complete.arb_pre_icu) <= 1).all(), 'BOTH_CLASSES_REMAIN')
    groups = {'ACEi_only': int(complete.acei_pre_icu.eq(1).sum()),
              'ARB_only': int(complete.arb_pre_icu.eq(1).sum()),
              'neither': int((complete.acei_pre_icu.eq(0) & complete.arb_pre_icu.eq(0)).sum())}
    require(all(value > 0 for value in groups.values()), 'ALL_THREE_GROUPS_REQUIRED')
    require(sum(groups.values()) == len(complete), 'GROUP_COUNT_MISMATCH')
    return complete, {'n': len(complete), 'events': int(complete.death_event.sum()),
                      'strata_count': int(complete.groupby(STRATA, observed=True).ngroups),
                      'order_groups': groups, 'both_flag_rows_excluded_before_complete_cases': int(excluded_both.sum())}


def fit_pair(complete):
    """Keep every row, including neither, in both equivalent parameterizations."""
    from lifelines import CoxPHFitter
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        original = CoxPHFitter(penalizer=0.0).fit(
            complete, 'time_to_event_days', 'death_event', strata=STRATA, robust=False)
        reparam = complete[['time_to_event_days','death_event','age','gender_M'] + STRATA].copy()
        reparam['ACEi_vs_ARB'] = complete.acei_pre_icu
        reparam['neither_vs_ARB'] = 1 - complete.acei_pre_icu - complete.arb_pre_icu
        reparam = reparam[['time_to_event_days','death_event','ACEi_vs_ARB','neither_vs_ARB','age','gender_M'] + STRATA]
        other = CoxPHFitter(penalizer=0.0).fit(
            reparam, 'time_to_event_days', 'death_event', strata=STRATA, robust=False)
    require(not caught, 'FIT_WARNING_REQUIRES_REVIEW')
    require(original.robust is False and other.robust is False, 'INFERENCE_CHANGED')
    require(original.cluster_col is None and other.cluster_col is None, 'CLUSTERING_CHANGED')
    require(original._n_examples == other._n_examples == len(complete), 'REPARAMETERIZATION_DROPPED_ROWS')
    return original, other


def bundle_from_fit(model, cohort, reference_hash, data_origin):
    import lifelines
    require(not model.robust and model.cluster_col is None, 'ORDINARY_COVARIANCE_REQUIRED')
    order = list(model.params_.index)
    return {'analysis_version': VERSION, 'model_name': 'subgroups', 'data_origin': data_origin,
            'source_reference_sha256': reference_hash,
            'specification': {'covariates': PARAMETERS, 'strata': STRATA, 'ties': 'efron',
                              'penalizer': 0.0, 'robust': False, 'cluster_col': None,
                              'variance_estimator': 'ordinary_model_based'},
            'cohort': cohort, 'parameters': {p: float(model.params_[p]) for p in order},
            'covariance': {'coefficient_order': order,
                           'matrix': model.variance_matrix_.loc[order,order].to_numpy().tolist()},
            'software': {'implementation': 'lifelines.CoxPHFitter', 'version': lifelines.__version__}}


def verify_reference(bundle, reference, reference_hash):
    allowed = {'analysis_version','model_name','data_origin','source_reference_sha256','specification','cohort','parameters','covariance','software'}
    require(set(bundle) == allowed, 'UNEXPECTED_AGGREGATE_SCHEMA')
    require(bundle['analysis_version'] == reference['analysis_version'] == VERSION, 'ANALYSIS_VERSION_MISMATCH')
    require(bundle['model_name'] == 'subgroups', 'WRONG_SOURCE_MODEL')
    require(bundle['source_reference_sha256'] == reference_hash, 'REFERENCE_HASH_MISMATCH')
    require(bundle['data_origin'] == 'authorized_local_current_cohort', 'CLINICAL_AGGREGATE_ORIGIN_REQUIRED')
    spec = bundle['specification']
    require(spec == {'covariates': PARAMETERS, 'strata': STRATA, 'ties':'efron', 'penalizer':0.0,
                     'robust':False, 'cluster_col':None, 'variance_estimator':'ordinary_model_based'}, 'SOURCE_INFERENCE_OR_SPECIFICATION_MISMATCH')
    require(bundle['software']['implementation'] == 'lifelines.CoxPHFitter', 'SOURCE_IMPLEMENTATION_MISMATCH')
    saved = reference['models']['subgroups']
    cohort = bundle['cohort']
    require(set(cohort) <= {'n','events','strata_count','order_groups','both_flag_rows_excluded_before_complete_cases'}, 'UNEXPECTED_COHORT_METADATA')
    require(set(bundle['covariance']) == {'coefficient_order','matrix'}, 'UNEXPECTED_COVARIANCE_METADATA')
    require(set(bundle['software']) == {'implementation','version'}, 'UNEXPECTED_SOFTWARE_METADATA')
    require((cohort['n'],cohort['events'],cohort['strata_count']) == (saved['n'],saved['deaths'],saved['strata_count']), 'SOURCE_COHORT_MISMATCH')
    if 'order_groups' in cohort:
        require(set(cohort['order_groups']) == {'ACEi_only','ARB_only','neither'} and all(v>0 for v in cohort['order_groups'].values()), 'NEITHER_OR_CLASS_GROUP_MISSING')
        require(sum(cohort['order_groups'].values()) == cohort['n'], 'GROUP_COUNT_MISMATCH')
    result = linear_contrast(bundle['parameters'], bundle['covariance']['coefficient_order'], bundle['covariance']['matrix'])
    order = bundle['covariance']['coefficient_order'];matrix=np.asarray(bundle['covariance']['matrix'])
    zcrit=norm.ppf(.975);maximum=0.0
    for name in order:
        beta=float(bundle['parameters'][name]);se=float(np.sqrt(matrix[order.index(name),order.index(name)]))
        require(se>0 and np.isfinite(se), 'INVALID_COEFFICIENT_SE')
        actual={'hr':np.exp(beta),'lower_95':np.exp(beta-zcrit*se),'upper_95':np.exp(beta+zcrit*se),'p':2*norm.sf(abs(beta/se))}
        maximum=max(maximum,*(abs(float(actual[k])-saved['estimates'][name][k]) for k in actual))
    require(maximum <= TOLERANCE, 'SAVED_COEFFICIENT_OR_INTERVAL_MISMATCH')
    return result, maximum


def verify_reparameterization(original, reparameterized):
    direct=linear_contrast(original.params_.to_dict(),list(original.params_.index),original.variance_matrix_.to_numpy())
    beta=float(reparameterized.params_['ACEi_vs_ARB'])
    variance=float(reparameterized.variance_matrix_.loc['ACEi_vs_ARB','ACEi_vs_ARB'])
    other=linear_contrast({'acei_pre_icu':beta,'arb_pre_icu':0.0,'age':0.0,'gender_M':0.0},PARAMETERS,
                          np.diag([variance,0.0,1.0,1.0]))
    differences={key:abs(direct[key]-other[key]) for key in ['log_hazard_ratio','standard_error','hazard_ratio','lower_95','upper_95','two_sided_wald_p']}
    differences['partial_log_likelihood']=abs(float(original.log_likelihood_)-float(reparameterized.log_likelihood_))
    require(max(differences.values())<=TOLERANCE, 'REPARAMETERIZATION_CHECK_FAILED')
    return differences


def synthetic_frame(tied=False):
    rng=np.random.default_rng(7319);n=1200
    group=rng.choice(4,n,p=[.65,.17,.16,.02])
    age=rng.uniform(25,85,n);male=rng.integers(0,2,n);era=np.array(['a','b','c'])[np.arange(n)%3]
    linear=.20*(group==1)-.10*(group==2)+.012*(age-55)+.15*male
    failure=rng.exponential(8/np.exp(linear));censor=rng.exponential(12,n)
    time=np.minimum(failure,censor)+.01
    if tied:time=np.floor(time*4)/4+.01
    return pd.DataFrame({'acei_pre_icu':np.isin(group,[1,3]).astype(int),
                         'arb_pre_icu':np.isin(group,[2,3]).astype(int),'age':age,
                         'gender':np.where(male,'M','F'),'anchor_year_group':era,
                         'time_to_event_days':time,'death_event':(failure<=censor).astype(int)})


def synthetic_check():
    from statsmodels.duration.hazard_regression import PHReg
    checks=[]
    for tied in [False,True]:
        complete,cohort=model_frame(synthetic_frame(tied));a,b=fit_pair(complete)
        differences=verify_reparameterization(a,b)
        comparison=PHReg(complete.time_to_event_days,complete[PARAMETERS],status=complete.death_event,
                         strata=complete.anchor_year_group,ties='efron').fit(maxiter=200,tol=1e-10,disp=False)
        independent=linear_contrast(dict(zip(PARAMETERS,comparison.params)),PARAMETERS,comparison.cov_params())
        actual=linear_contrast(a.params_.to_dict(),list(a.params_.index),a.variance_matrix_.to_numpy())
        independent_differences={k:abs(actual[k]-independent[k]) for k in ['log_hazard_ratio','standard_error','hazard_ratio','lower_95','upper_95','two_sided_wald_p']}
        require(max(independent_differences.values())<=TOLERANCE,'SYNTHETIC_INDEPENDENT_CHECK_FAILED')
        require(cohort['both_flag_rows_excluded_before_complete_cases']>0 and cohort['order_groups']['neither']>0,'SYNTHETIC_GROUP_COVERAGE_FAILED')
        checks.append({'tied_times':tied,'cohort':cohort,'reparameterization_differences':differences,'PHReg_differences':independent_differences,'passed':True})
    return {'status':'passed','data_origin':'fully_synthetic_not_MIMIC','clinical_contrast_computed':False,
            'absolute_tolerance':TOLERANCE,'checks':checks}


def local_refit(repo, reference, reference_hash):
    """Only called by the explicit --refit-current user command; no row export."""
    spec=importlib.util.spec_from_file_location('current_contrast_source',repo/'scripts/current_analysis.py')
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
    require(source.ANALYSIS_VERSION==VERSION,'SOURCE_VERSION_CHANGED')
    require(hashlib.sha256(source.QUERY.encode()).hexdigest()==reference['execution']['query_sha256'],'SOURCE_QUERY_CHANGED')
    frame,query=source.load_current_data()
    manifest=reference['secondary_python_logistic']['manifest']
    actual={'n':len(frame),'events':int(frame.death_event.sum()),'age_sum':float(frame.age.sum()),'duration_sum':float(frame.time_to_event_days.sum())}
    require(all(np.isclose(actual[k],manifest[k],rtol=1e-10,atol=1e-5) for k in actual),'CURRENT_COHORT_REFERENCE_MISMATCH')
    complete,cohort=model_frame(frame)
    # This is the same ordinary, nonpenalized, era-stratified Cox likelihood.
    original,other=fit_pair(complete)
    bundle=bundle_from_fit(original,cohort,reference_hash,'authorized_local_current_cohort')
    result,agreement=verify_reference(bundle,reference,reference_hash)
    reparam=verify_reparameterization(original,other)
    return bundle,result,{'saved_reference_max_absolute_difference':agreement,
                         'ARB_reference_refit_differences':reparam,'query_execution':query,
                         'neither_group_retained':True,'same_rows_in_both_parameterizations':True}


def write_verified(output,bundle,result,verification):
    output.mkdir(parents=True,exist_ok=False)
    record={'status':'verified','analysis_role':'post_hoc_exploratory_single_contrast',
            'direction':'ACEi-only prescription orders / ARB-only prescription orders',
            'variance_estimator':'ordinary_model_based','inference':'two_sided_Wald_95_percent',
            'cohort':bundle['cohort'],'contrast':result,'verification':verification,
            'limitations':['Prescription records do not verify administration, treatment overlap or adherence.',
                           'Observational association; no causal superiority or equivalence claim.',
                           'Post-hoc single contrast; no multiplicity correction; original admission-level, nonclustered design retained.']}
    (output/'aggregate_model.json').write_text(json.dumps(bundle,indent=2,allow_nan=False)+'\n')
    (output/'contrast.json').write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')
    (output/'supplement.md').write_text(
        '# Local exploratory ACEi / ARB contrast\n\n'
        'Post-hoc single contrast in the existing subgroup Cox model; primary analyses are unchanged.\n\n'
        f"ACEi-only qualifying prescription orders / ARB-only qualifying prescription orders: adjusted HR {result['hazard_ratio']:.6g} "
        f"(95% CI {result['lower_95']:.6g}–{result['upper_95']:.6g}); two-sided Wald p={result['two_sided_wald_p']:.6g}.\n\n"
        'The full original subgroup cohort is retained, including neither qualifying order; records with both class flags are excluded as before. '
        'Age/sex adjustment, era strata, ICU-entry time zero, in-hospital event/censoring rules and ordinary model-based inference are unchanged. '
        'Variance includes the ACEi–ARB coefficient covariance.\n\n'
        'This is an association of prescription-order groups, not verified administration, causal treatment superiority or evidence of equivalence. '
        'It was added after the main analysis and has no multiplicity correction.\n')
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--synthetic',action='store_true')
    mode.add_argument('--aggregate',type=Path,help='Already permitted aggregate coefficients and labelled covariance; no clinical read')
    mode.add_argument('--refit-current',action='store_true',help='Explicit authorized local-user BigQuery read/refit; never prints model rows')
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out',type=Path,help='New directory under reports/local_supplements for clinical results')
    args=parser.parse_args()
    if args.synthetic:
        record=synthetic_check()
        if args.out:
            args.out.mkdir(parents=True,exist_ok=False)
            (args.out/'synthetic_check.json').write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')
        print(json.dumps({'status':record['status'],'data_origin':record['data_origin'],'clinical_contrast_computed':False,'synthetic_scenarios':len(record['checks'])}))
        return
    require(args.out is not None,'LOCAL_OUTPUT_DIRECTORY_REQUIRED')
    repo=args.repo.resolve();output=args.out.resolve()
    require(output.is_relative_to((repo/'reports/local_supplements').resolve()),'UNPUBLISHED_LOCAL_OUTPUT_REQUIRED')
    require(not output.exists(),'OUTPUT_ALREADY_EXISTS')
    reference_path=repo/'docs/CURRENT_ANALYSIS.json'
    reference=json.loads(reference_path.read_text());reference_hash=sha(reference_path)
    if args.aggregate:
        require(args.aggregate.stat().st_size<=100000,'AGGREGATE_INPUT_TOO_LARGE')
        bundle=json.loads(args.aggregate.read_text())
        result,agreement=verify_reference(bundle,reference,reference_hash)
        verification={'saved_reference_max_absolute_difference':agreement,
                      'source':'permitted_full_precision_aggregate_coefficients_and_covariance',
                      'clinical_refit_performed':False,'source_three_group_model_cohort_matches':True,
                      'coefficient_count_checked':len(bundle['parameters']),
                      'note':'Wald linear contrast; reparameterization/refit implementation validated on synthetic data only in this mode.'}
    else:
        bundle,result,verification=local_refit(repo,reference,reference_hash)
    write_verified(output,bundle,result,verification)
    print(json.dumps({'status':'verified','direction':'ACEi-only / ARB-only qualifying prescription orders',
                      'hazard_ratio':result['hazard_ratio'],'lower_95':result['lower_95'],'upper_95':result['upper_95'],
                      'two_sided_wald_p':result['two_sided_wald_p'],'patient_rows_saved_or_printed':False}))


if __name__=='__main__':
    try:
        main()
    except ContrastError as error:
        print(json.dumps({'status':'not_calculated','reason_code':str(error),'clinical_result_written':False}))
        sys.exit(2)
    except Exception as error:
        # Unknown third-party exceptions must not echo data, SQL results or credentials.
        print(json.dumps({'status':'not_calculated','reason_code':'LOCAL_EXECUTION_FAILED',
                          'error_type':type(error).__name__,'clinical_result_available':'not_confirmed'}))
        sys.exit(2)
