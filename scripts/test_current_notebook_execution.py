"""Offline checks for current-run aggregate review; never launches a kernel."""
import unittest

from execute_current_supplement_notebooks import check_outputs, compare_numeric


class CurrentExecutionReviewTests(unittest.TestCase):
    def test_numeric_review_checks_counts_and_intervals(self):
        data = {"count": 17, "rows": [{"hr": .8, "ci": [.6, 1.1]}]}
        result = compare_numeric(data, data)
        self.assertTrue(result["passed"])
        self.assertEqual(result["numeric_values_checked"], 4)
        self.assertEqual(result["maximum_absolute_difference"], 0)

    def test_numeric_review_rejects_drift_or_missing_values(self):
        for actual in [{"n": 18}, {}, {"n": float("nan")}]:
            with self.subTest(actual=actual), self.assertRaises(RuntimeError): compare_numeric(actual, {"n": 17})

    def test_output_review_rejects_identifiers_secrets_local_paths_and_errors(self):
        for content in ["<table><th>subject_id</th></table>", "file:///private/fixture", "ya29." + "X" * 24]:
            book = {"cells": [{"cell_type": "code", "execution_count": 1, "outputs": [{"output_type": "display_data", "data": {"text/html": content}}]}]}
            with self.subTest(content=content), self.assertRaises(RuntimeError): check_outputs(book)
        with self.assertRaises(ValueError):
            check_outputs({"cells": [{"cell_type": "code", "outputs": [{"output_type": "error", "ename": "fixture"}]}]})

    def test_output_review_accepts_bounded_aggregate_markup(self):
        result = check_outputs({"cells": [{"cell_type": "code", "execution_count": 1, "outputs": [{"output_type": "display_data", "data": {"text/html": "<table><th>Admissions</th><td>17</td></table>"}}]}]})
        self.assertTrue(result["passed"])
        self.assertEqual(result["output_blocks"], 1)


if __name__ == "__main__": unittest.main()
