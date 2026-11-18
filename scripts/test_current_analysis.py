"""Regression checks for rare-category handling and numeric multi-strata fitting."""
import unittest
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import pandas as pd

from current_analysis import fit_cox, pool_icu_categories
from render_current_report import generate


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


class ReportProvenance(unittest.TestCase):
    def fixture(self, root):
        repo = Path(__file__).resolve().parents[1]
        (root / "docs").mkdir()
        (root / "reports").mkdir()
        for name in ["CURRENT_ANALYSIS.json", "INDEPENDENT_COX_CROSSCHECK.json"]:
            shutil.copy2(repo / "docs" / name, root / "docs" / name)

    def test_matching_current_record_supports_agreement_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            current = root / "docs/CURRENT_ANALYSIS.json"
            record = json.loads((root / "docs/INDEPENDENT_COX_CROSSCHECK.json").read_text())
            self.assertEqual(record["reference_sha256"], hashlib.sha256(current.read_bytes()).hexdigest())
            generate(root)
            report = (root / "reports/copd_raas_survival_report.qmd").read_text()
            self.assertIn("40 coefficients", report)
            self.assertIn("were independently recalculated", report)

    def test_stale_missing_or_failed_record_cannot_claim_agreement(self):
        for scenario in ["stale_reference", "missing_record", "failed_model"]:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.fixture(root)
                path = root / "docs/INDEPENDENT_COX_CROSSCHECK.json"
                if scenario == "stale_reference":
                    with (root / "docs/CURRENT_ANALYSIS.json").open("a") as output:
                        output.write("\n")
                elif scenario == "missing_record":
                    path.unlink()
                else:
                    record = json.loads(path.read_text())
                    next(iter(record["models"].values()))["passed"] = False
                    path.write_text(json.dumps(record))
                generate(root)
                report = (root / "reports/copd_raas_survival_report.qmd").read_text()
                self.assertIn("has not been established for this exact", report)
                self.assertNotIn("were independently recalculated", report)



if __name__ == "__main__":
    unittest.main()
