"""Reader-facing layout contracts, independent of figure-generation templates."""
from pathlib import Path
import copy
import re
import unittest

import nbformat

from notebook_figure_layout import validate_layout, GUIDE_HEADINGS

REPO=Path(__file__).resolve().parents[1]
EXPECTED={'04a_outcomes_and_modeling':1,'04b_outcomes_and_modeling_raas_subgroups':1,
          '04c_extended_covariate_cox_model':2,'05a_patient_cluster_sensitivity':2,
          '05b_competing_risks':2,'05c_time_aligned_severity':2}


class NotebookFigureLayoutTests(unittest.TestCase):
    def test_all_published_notebooks_follow_the_same_figure_contract(self):
        for path in (REPO/'notebooks').glob('*.ipynb'):
            if path.stem=='00_setup':continue
            with self.subTest(notebook=path.stem):
                book=nbformat.read(path,as_version=4)
                self.assertEqual(validate_layout(book),list(range(1,EXPECTED.get(path.stem,0)+1)))
                if path.stem in EXPECTED:
                    self.assertEqual(sum(c.cell_type=='markdown' and re.search(r'^## Saved clinical results$',c.source,re.M) is not None for c in book.cells),1)
                    self.assertEqual(sum(c.cell_type=='markdown' and re.search(r'^## Runtime execution$',c.source,re.M) is not None for c in book.cells),1)

    def test_duplicate_numbers_and_misplaced_explanations_are_rejected(self):
        book=nbformat.read(REPO/'notebooks/04c_extended_covariate_cox_model.ipynb',as_version=4)
        wrong=copy.deepcopy(book)
        figure=next(c for c in wrong.cells if c.cell_type=='markdown' and '### Figure 2 —' in c.source)
        figure.source=figure.source.replace('### Figure 2 —','### Figure 1 —',1)
        with self.assertRaises(ValueError):validate_layout(wrong)
        wrong=copy.deepcopy(book)
        figure=next(c for c in wrong.cells if c.cell_type=='markdown' and '### Figure 1 —' in c.source)
        figure.source=figure.source.replace(GUIDE_HEADINGS[0],'',1)
        with self.assertRaises(ValueError):validate_layout(wrong)


if __name__=='__main__':unittest.main()
