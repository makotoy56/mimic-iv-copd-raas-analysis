"""Offline checks for selected aggregate publication and stale-report guards."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from report_survival_supplement import curate, load_public, report_section, update_readme, RESULT_FILE, VALIDATION_FILE

REPO = Path(__file__).resolve().parents[1]


class SupplementPublicationTests(unittest.TestCase):
    def fixture(self, root):
        for rel in ["docs/CURRENT_ANALYSIS.json", "docs/" + RESULT_FILE, "docs/" + VALIDATION_FILE, "scripts/survival_sensitivity.py", "README.md"]:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, target)

    def test_public_schema_excludes_keys_and_full_covariance(self):
        data = load_public(REPO)
        def check(value):
            if isinstance(value, dict):
                self.assertFalse(set(value) & {"subject_id", "hadm_id", "stay_id", "parameters", "covariance", "ordinary_covariance", "patient_cluster_covariance"})
                for child in value.values(): check(child)
            elif isinstance(value, list):
                for child in value: check(child)
        check(data)
        self.assertEqual(len(data["cluster"]["models"]), 2)
        self.assertEqual(len(data["landmark"]["models"]), 2)
        for group in data["competing"]["groups"]:
            self.assertEqual([x["day"] for x in group["curve"]], list(range(29)))

    def test_report_distinguishes_estimands_and_reports_both_landmark_fits(self):
        text = "\n".join(report_section(REPO))
        self.assertIn("## Supplementary Sensitivity Analyses", text)
        self.assertIn("| Primary age/sex/era | 0.732 | 0.592–0.904 | 0.593–0.902 |", text)
        self.assertIn("Unadjusted", text)
        self.assertIn("pointwise", text)
        self.assertIn("| Age/sex/era | 11,530 | 1,436 | 0.771 |", text)
        self.assertIn("| Exploratory first-day-SOFA core | 11,530 | 1,436 | 0.854 |", text)
        self.assertIn("individual measurement times have not been independently reconstructed", text)
        self.assertIn("not a treatment effect", text)

    def test_stale_source_reference_or_modified_public_result_is_rejected(self):
        for rel in ["docs/CURRENT_ANALYSIS.json", "scripts/survival_sensitivity.py", "docs/" + RESULT_FILE]:
            with self.subTest(path=rel), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); self.fixture(root)
                with (root / rel).open("a") as out: out.write("\n")
                with self.assertRaises(ValueError): report_section(root)

    def test_unverified_input_hash_is_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root)
            source = root / "unverified.json"; source.write_text("{}")
            with self.assertRaisesRegex(ValueError, "hash mismatch"): curate(root, source)

    def test_readme_summary_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root)
            data = load_public(root)
            update_readme(root, data)
            first = (root / "README.md").read_text()
            update_readme(root, data)
            self.assertEqual(first, (root / "README.md").read_text())
            self.assertEqual(first.count("### Supplementary Sensitivity Analyses"), 1)

    def test_without_selected_public_record_no_supplement_claim_is_generated(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(report_section(Path(temp)), [])


if __name__ == "__main__":
    unittest.main()
