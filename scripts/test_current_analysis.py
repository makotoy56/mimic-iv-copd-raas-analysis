"""Regression checks for rare-category and stale-validation failures."""
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from current_analysis import ANALYSIS_VERSION, LOGISTIC_SPEC, fit_cox, pool_icu_categories, validate_sas_comparison


class AnalysisGuards(unittest.TestCase):
    def test_nullable_numeric_data_fits_multiple_strata(self):
        import numpy as np
        rng = np.random.default_rng(42)
        frame = pd.DataFrame({"time_to_event_days": rng.exponential(5, 200),
                              "death_event": pd.Series(rng.integers(0, 2, 200), dtype="Int64"),
                              "x": rng.normal(size=200),
                              "sofa": pd.Series(rng.integers(0, 3, 200), dtype="Int64"),
                              "era": ["a", "b"] * 100})
        _, info = fit_cox(frame, ["x"], ["era", "sofa"])
        self.assertEqual(info["n"], 200)
        self.assertEqual(info["strata_count"], 6)

    def test_pooling_uses_frequency_and_preserves_missing(self):
        x = pd.Series(["A"] * 50 + ["B"] * 49 + [None])
        pooled, names = pool_icu_categories(x)
        self.assertEqual(names, ["B"])
        self.assertEqual((pooled == "A").sum(), 50)
        self.assertEqual((pooled == "Other (rare ICU types)").sum(), 49)
        self.assertTrue(pd.isna(pooled.iloc[-1]))

    def test_missing_provenance_fails_before_comparing_old_files(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "fresh cohort/model provenance"):
                validate_sas_comparison(Path(temp)/"sas.csv", Path(temp)/"py.csv")

    def fixture(self, root):
        sas, py = root/"sas.csv", root/"py.csv"
        pd.DataFrame({"Variable": ["Intercept", "age"], "Estimate": [0.0, 0.01]}).to_csv(sas, index=False)
        pd.DataFrame({"Variable": ["Intercept", "age"], "Python_Estimate": [0.0, 0.01001]}).to_csv(py, index=False)
        meta = {"analysis_version": ANALYSIS_VERSION, "model_spec": LOGISTIC_SPEC,
                "n": 100, "events": 10, "age_sum": 7000, "duration_sum": 1000.5}
        pd.DataFrame([meta]).to_csv(sas.with_suffix(".manifest.csv"), index=False)
        py.with_suffix(".manifest.json").write_text(json.dumps(meta))
        return sas, py

    def test_parameter_loss_and_duplicate_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            sas, py = self.fixture(Path(temp))
            pd.DataFrame({"Variable": ["age"], "Python_Estimate": [0.01]}).to_csv(py, index=False)
            with self.assertRaisesRegex(ValueError, "match exactly"):
                validate_sas_comparison(sas, py)
            pd.DataFrame({"Variable": ["age", "age"], "Python_Estimate": [0.01, 0.01]}).to_csv(py, index=False)
            with self.assertRaisesRegex(ValueError, "unique"):
                validate_sas_comparison(sas, py)

    def test_stale_cohort_is_rejected_and_zero_relative_error_is_undefined(self):
        with tempfile.TemporaryDirectory() as temp:
            sas, py = self.fixture(Path(temp))
            good = validate_sas_comparison(sas, py)
            self.assertTrue(pd.isna(good.loc[good.Variable == "Intercept", "Relative difference (%)"]).all())
            meta = json.loads(py.with_suffix(".manifest.json").read_text())
            meta["age_sum"] += 1
            py.with_suffix(".manifest.json").write_text(json.dumps(meta))
            with self.assertRaisesRegex(ValueError, "age_sum"):
                validate_sas_comparison(sas, py)


if __name__ == "__main__":
    unittest.main()
