"""Presentation follows selected aggregate values, including CI boundary cases."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from presentation_catalog import CATALOG,metadata,interval_position,relative_to_one
from notebook_presentation import (dimensions_frame,dimensions_summary,binary_orders,merge_summary,
                                  missing_summary,integrity_summary,render_table,model_sentence,
                                  runtime_figure_guide,logistic_summary)
from notebook_presentation import age_statistics_frame,age_table,age_summary
import notebook_presentation as presentation
from notebook_publication import load_record
from figure_interpretation import main_notes
from render_landmark_summary import summary_sections

ROOT=Path(__file__).resolve().parents[1]


class PresentationTests(unittest.TestCase):
    def test_catalog_covers_every_notebook_and_component_once(self):
        self.assertEqual(len(CATALOG),11)
        self.assertEqual(sum(len(x['figures']) for x in CATALOG.values()),10)
        self.assertEqual(sum(len(x['tables']) for x in CATALOG.values()),32)
        for prefix,item in CATALOG.items():
            for kind in ['tables','figures']:
                keys=[x[0] for x in item[kind]];self.assertEqual(len(keys),len(set(keys)))
                self.assertEqual([metadata(prefix,kind,key)['number'] for key in keys],list(range(1,len(keys)+1)))

    def test_ci_sides_and_exact_boundaries(self):
        self.assertIn('below 1',interval_position(.5,.9))
        self.assertIn('above 1',interval_position(1.1,1.5))
        for low,high in [(.5,1),(1,1.5),(1,1),(.9,1.1)]:
            self.assertIn('includes 1',interval_position(low,high))
        for low,high in [(0,1),(2,1),(float('nan'),2)]:
            with self.assertRaises(ValueError):interval_position(low,high)

    def test_dimensions_and_zero_exposure_are_computed(self):
        self.assertIn('17 rows and 4 columns',dimensions_summary(dimensions_frame((17,4))))
        frame,summary=binary_orders(pd.DataFrame({'raas_pre_icu':[0],'n':[17]}))
        self.assertIn('0 admissions have qualifying RAAS orders',summary)
        self.assertEqual(frame.iloc[0,0],'No qualifying RAAS orders')

    def test_integrity_merge_and_missingness_do_not_assert_fixed_success(self):
        self.assertIn('2 excess rows',integrity_summary(pd.DataFrame({'n_rows':[7],'n_unique_stays':[5]})))
        self.assertIn('+2',merge_summary(pd.DataFrame({'table_name':['cohort_copd','cohort_copd_with_raas'],'n':[7,9]})))
        self.assertIn('3 missing-field occurrences',missing_summary(pd.DataFrame({'a':[1],'b':[2]})))

    def test_table_contains_title_and_summary_without_repeated_source(self):
        html=render_table('01','dimensions',dimensions_frame((17,4)),dimensions_summary(dimensions_frame((17,4)))).data
        for value in ['Table 1 — Base adult ICU cohort dimensions','Summary:','17 rows and 4 columns']:
            self.assertIn(value,html)
        self.assertNotIn('Data source:',html)
        self.assertLess(html.index('Table 1'),html.index('<thead>'))
        self.assertLess(html.index('</table>'),html.index('Summary:'))

    def test_identifier_columns_or_oversized_tables_are_rejected(self):
        for frame in [pd.DataFrame({'subject_id':[1]}),pd.DataFrame({'n':range(101)})]:
            with self.assertRaises(ValueError):render_table('01','dimensions',frame,'summary')

    def test_age_count_has_admission_units_not_years(self):
        frame=age_statistics_frame(pd.Series({'count':17.,'50%':62.,'min':18.,'max':91.}))
        self.assertEqual(frame.set_index('Statistic').loc['count','Unit'],'admissions')
        self.assertIn('17 nonmissing ages',age_summary(frame))
        self.assertIn('Table 2',render_table('03a','age',age_table(frame),age_summary(frame)).data)

    def test_synthetic_origin_does_not_link_to_clinical_evidence(self):
        bundle={'data_origin':'fully_synthetic_not_MIMIC'}
        html=presentation.render_input_context(bundle).data
        self.assertIn('Fully synthetic',html)
        self.assertNotIn('NOTEBOOK_EXECUTION_VALIDATION.json',html)

    def test_context_is_shown_once_and_reappears_when_input_changes(self):
        synthetic={'data_origin':'fully_synthetic_not_MIMIC'}
        clinical={'data_origin':'authorized_local_current_cohort','_presentation_replay':True}
        frame=pd.DataFrame({'Admissions':[17]})
        with patch.object(presentation,'_ACTIVE_INPUT',None),patch('IPython.display.display') as display:
            presentation.display_input_context(synthetic)
            presentation.display_table('05a','cohort',frame,'17 artificial admissions.',synthetic)
            presentation.display_table('05a','models',frame,'17 artificial admissions.',synthetic)
            presentation.display_table('05a','cohort',frame,'17 saved admissions.',clinical)
            html=[call.args[0].data for call in display.call_args_list]
        self.assertEqual(sum('Input context:' in item for item in html),2)
        self.assertEqual(sum('Data source:' in item for item in html),0)
        self.assertEqual(sum('Fully synthetic' in item for item in html),1)
        self.assertEqual(sum('Saved clinically validated' in item for item in html),1)

    def test_primary_and_subclass_interpretations_follow_changed_intervals(self):
        data=json.loads((ROOT/'docs/CURRENT_ANALYSIS.json').read_text())
        data['models']['core']['estimates']['raas_pre_icu'].update(hr=1.25,lower_95=1.1,upper_95=1.4)
        data['models']['subgroups']['estimates']['acei_pre_icu'].update(hr=1.25,lower_95=1.1,upper_95=1.4)
        notes=main_notes(data)
        self.assertIn('1.250 (95% CI 1.100–1.400)',notes['core']);self.assertIn('above 1',notes['core'])
        self.assertNotIn('Its interval includes 1',notes['core'])
        self.assertIn('above 1',notes['subgroups'])

    def test_landmark_interpretation_follows_the_selected_ci(self):
        data=json.loads((ROOT/'docs/SURVIVAL_SENSITIVITY_RESULTS.json').read_text())
        data['landmark']['models']['landmark_age_sex']['hr']=1.25
        data['landmark']['models']['landmark_age_sex']['patient_cluster'].update(lower_95=1.1,upper_95=1.4)
        note=dict(summary_sections(data))['figure']
        self.assertIn('above 1',note);self.assertNotIn('The interval lies below 1',note)
        self.assertIn('closer',relative_to_one(.5,.9));self.assertIn('farther',relative_to_one(.9,.5))

    def test_runtime_summary_uses_its_input_not_public_clinical_values(self):
        model={'n':17,'events':3,'patients':16,'estimates':{'raas_pre_icu':{'hr':1.25,'ordinary':{'lower_95':1.1,'upper_95':1.4,'p':.02},'patient_cluster':{'lower_95':1.,'upper_95':1.5,'p':.05}}}}
        bundle={'data_origin':'fully_synthetic_not_MIMIC','results':{'cluster':{'models':{'artificial':model}}}}
        note=runtime_figure_guide(bundle,'cluster')
        self.assertIn('HR 1.250',note);self.assertIn('17 admissions',note);self.assertIn('includes 1',note)
        self.assertNotIn('11,964',note)

    def test_discharge_event_count_is_not_called_deaths(self):
        model={'n':17,'events':9,'hr':1.1,'patient_cluster':{'lower_95':.9,'upper_95':1.3,'p':.2}}
        note=model_sentence('discharge',model,'patient_cluster',event_label='live discharges')
        self.assertIn('9 live discharges',note);self.assertNotIn('9 deaths',note)

    def test_logistic_summary_uses_an_odds_ratio(self):
        frame=pd.DataFrame([{'Variable':'raas_pre_icu','Python_OR':.8,'Python_CI_Lower':.6,'Python_CI_Upper':1.1,'Python_pvalue':.2}])
        note=logistic_summary(frame,{'n':17,'events':3})
        self.assertIn('OR 0.800',note);self.assertIn('not a survival HR',note)

    def test_presentation_record_rejects_changed_bound_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'docs').mkdir();(root/'scripts').mkdir()
            mapping={'NOTEBOOK_EXECUTION_VALIDATION.json':'source_execution_record_sha256','CURRENT_ANALYSIS.json':'main_reference_sha256','SURVIVAL_SENSITIVITY_RESULTS.json':'supplement_reference_sha256'}
            record={'status':'passed','presentation_script_sha256':{}}
            for name,key in mapping.items():
                raw=b'{}';(root/'docs'/name).write_bytes(raw);record[key]=hashlib.sha256(raw).hexdigest()
            (root/'docs/NOTEBOOK_PRESENTATION_VALIDATION.json').write_text(json.dumps(record))
            self.assertEqual(load_record(root)['status'],'passed')
            (root/'docs/CURRENT_ANALYSIS.json').write_text('{"changed":true}')
            self.assertEqual(load_record(root)['status'],'stale')


if __name__=='__main__':unittest.main()
