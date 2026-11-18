"""Synthetic-only regression checks for the post-hoc contrast and its guards."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.stats import norm

import acei_arb_contrast as contrast


class ContrastTests(unittest.TestCase):
    def fixture(self):
        parameters=dict(zip(contrast.PARAMETERS,[.4,-.2,.01,-.03]))
        covariance=np.array([[.04,.025,0,0],[.025,.09,0,0],[0,0,.0001,0],[0,0,0,.01]])
        return parameters,covariance

    def bundle(self):
        parameters,matrix=self.fixture()
        bundle={'analysis_version':contrast.VERSION,'model_name':'subgroups',
                'data_origin':'authorized_local_current_cohort','source_reference_sha256':'0'*64,
                'specification':{'covariates':contrast.PARAMETERS,'strata':contrast.STRATA,'ties':'efron',
                                 'penalizer':0.0,'robust':False,'cluster_col':None,'variance_estimator':'ordinary_model_based'},
                'cohort':{'n':6,'events':3,'strata_count':2,'order_groups':{'ACEi_only':2,'ARB_only':2,'neither':2}},
                'parameters':parameters,'covariance':{'coefficient_order':contrast.PARAMETERS,'matrix':matrix.tolist()},
                'software':{'implementation':'lifelines.CoxPHFitter','version':'synthetic_fixture'}}
        estimates={}
        for i,p in enumerate(contrast.PARAMETERS):
            beta=parameters[p];se=np.sqrt(matrix[i,i]);z=norm.ppf(.975)
            estimates[p]={'hr':np.exp(beta),'lower_95':np.exp(beta-z*se),'upper_95':np.exp(beta+z*se),'p':2*norm.sf(abs(beta/se))}
        reference={'analysis_version':contrast.VERSION,'models':{'subgroups':{'n':6,'deaths':3,'strata_count':2,'estimates':estimates}}}
        return bundle,reference

    def test_contrast_uses_cross_covariance_and_ACEi_over_ARB_direction(self):
        parameters,matrix=self.fixture()
        result=contrast.linear_contrast(parameters,contrast.PARAMETERS,matrix)
        self.assertAlmostEqual(result['log_hazard_ratio'],.6)
        self.assertAlmostEqual(result['variance'],.04+.09-2*.025)
        self.assertNotAlmostEqual(result['standard_error'],np.sqrt(.04+.09))
        self.assertAlmostEqual(result['hazard_ratio'],np.exp(.6))
        self.assertAlmostEqual(result['lower_95'],np.exp(.6-norm.ppf(.975)*np.sqrt(.08)))
        self.assertAlmostEqual(result['upper_95'],np.exp(.6+norm.ppf(.975)*np.sqrt(.08)))

    def test_labelled_covariance_order_can_be_permuted_without_changing_result(self):
        parameters,matrix=self.fixture();order=[2,1,3,0]
        expected=contrast.linear_contrast(parameters,contrast.PARAMETERS,matrix)
        actual=contrast.linear_contrast(parameters,[contrast.PARAMETERS[i] for i in order],matrix[np.ix_(order,order)])
        for key in ['log_hazard_ratio','variance','hazard_ratio','lower_95','upper_95','two_sided_wald_p']:
            self.assertAlmostEqual(expected[key],actual[key])

    def test_minimum_same_model_ACEi_ARB_covariance_block_is_sufficient(self):
        bundle,reference=self.bundle()
        full,_=contrast.verify_reference(bundle,reference,'0'*64)
        bundle['parameters']={p:bundle['parameters'][p] for p in contrast.PARAMETERS[:2]}
        bundle['covariance']={'coefficient_order':contrast.PARAMETERS[:2],
                              'matrix':np.asarray(bundle['covariance']['matrix'])[:2,:2].tolist()}
        # The original four-covariate model specification and its full cohort
        # still match; no restriction to the two medication groups is made.
        bundle['cohort'].pop('order_groups')
        minimum,_=contrast.verify_reference(bundle,reference,'0'*64)
        for key in ['hazard_ratio','lower_95','upper_95','variance']:
            self.assertAlmostEqual(full[key],minimum[key])

    def test_invalid_or_unlabelled_covariance_is_rejected(self):
        parameters,matrix=self.fixture()
        asymmetric=matrix.copy();asymmetric[0,1]=0
        indefinite=matrix.copy();indefinite[0,1]=indefinite[1,0]=1
        for value,code in [(matrix[:2,:2],'COVARIANCE_SHAPE'),(asymmetric,'ASYMMETRIC'),(indefinite,'INVALID_COVARIANCE')]:
            with self.subTest(code=code),self.assertRaisesRegex(contrast.ContrastError,code):
                contrast.linear_contrast(parameters,contrast.PARAMETERS,value)
        with self.assertRaisesRegex(contrast.ContrastError,'PARAMETER_KEYS'):
            contrast.linear_contrast(parameters,['acei_pre_icu']*4,matrix)

    def test_source_selection_keeps_neither_and_only_excludes_both_and_missing(self):
        frame=pd.DataFrame({'acei_pre_icu':[0,1,0,1,0,1,0,0],
                            'arb_pre_icu':[0,0,1,1,0,0,1,0],
                            'age':[50,60,55,70,np.nan,40,80,50],
                            'gender':['F','M','F','M','F','M','F','M'],
                            'anchor_year_group':['a','a','b','b','a','a','b','b'],
                            'time_to_event_days':np.arange(1,9,dtype=float),
                            'death_event':[0,1,1,1,0,0,1,0]})
        complete,cohort=contrast.model_frame(frame)
        self.assertEqual(list(complete.index),[0,1,2,5,6,7])
        self.assertEqual(cohort['n'],6)
        self.assertEqual(cohort['events'],3)
        self.assertEqual(cohort['order_groups'],{'ACEi_only':2,'ARB_only':2,'neither':2})
        self.assertEqual(cohort['both_flag_rows_excluded_before_complete_cases'],1)

    def test_aggregate_requires_same_model_reference_and_ordinary_inference(self):
        bundle,reference=self.bundle()
        result,difference=contrast.verify_reference(bundle,reference,'0'*64)
        self.assertAlmostEqual(result['log_hazard_ratio'],.6)
        self.assertAlmostEqual(difference,0)
        cases=[]
        changed=copy.deepcopy(bundle);changed['specification']['robust']=True;cases.append((changed,'INFERENCE_OR_SPECIFICATION'))
        changed=copy.deepcopy(bundle);changed['source_reference_sha256']='1'*64;cases.append((changed,'REFERENCE_HASH'))
        changed=copy.deepcopy(bundle);changed['model_name']='core';cases.append((changed,'WRONG_SOURCE_MODEL'))
        changed=copy.deepcopy(bundle);changed['cohort']['order_groups']['neither']=0;cases.append((changed,'GROUP_MISSING'))
        changed=copy.deepcopy(bundle);changed['parameters']['age']+=1;cases.append((changed,'COEFFICIENT_OR_INTERVAL'))
        changed=copy.deepcopy(bundle);changed['rows']=[];cases.append((changed,'UNEXPECTED_AGGREGATE_SCHEMA'))
        changed=copy.deepcopy(bundle);changed['cohort']['rows']=[];cases.append((changed,'UNEXPECTED_COHORT_METADATA'))
        for changed,code in cases:
            with self.subTest(code=code),self.assertRaisesRegex(contrast.ContrastError,code):
                contrast.verify_reference(changed,reference,'0'*64)

    def test_public_output_path_is_rejected_before_any_real_data_loader(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with patch('sys.argv',['contrast','--refit-current','--repo',str(root),'--out',str(root/'docs/public')]),patch.object(contrast,'local_refit') as loader:
                with self.assertRaisesRegex(contrast.ContrastError,'UNPUBLISHED_LOCAL_OUTPUT_REQUIRED'):
                    contrast.main()
                loader.assert_not_called()

    def test_existing_supplement_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'result';output.mkdir();marker=output/'keep';marker.write_text('unchanged')
            bundle,reference=self.bundle();result,_=contrast.verify_reference(bundle,reference,'0'*64)
            with self.assertRaises(FileExistsError):
                contrast.write_verified(output,bundle,result,{'synthetic_fixture':True})
            self.assertEqual(marker.read_text(),'unchanged')


if __name__=='__main__':
    unittest.main()
