"""Synthetic protocol fixtures for mixed historical/current output approval."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from notebook_publication import (CURRENT_BINDINGS, CURRENT_SUPPLEMENT_RECORD, CURRENT_SUPPLEMENTS,
                                  PRESENTATION_RECORD, RECORD, approved, load_record, output_hash, source_hash)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True))


def book(label):
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": [
        {"cell_type": "code", "id": "fixture", "source": repr(label), "metadata": {}, "execution_count": 1,
         "outputs": [{"output_type": "display_data", "data": {"text/plain": "synthetic fixture"}, "metadata": {}}]}]}


class CurrentNotebookPublicationTests(unittest.TestCase):
    def fixture(self, root):
        books = {"04a.ipynb": book("historical"), **{name: book(name) for name in CURRENT_SUPPLEMENTS}}
        for name in CURRENT_BINDINGS:
            target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("{}" if name.startswith("docs/") else "# synthetic protocol source\n")
        query = "SELECT e.age FROM `fixture_project.fixture_dataset.fixture_table` e"
        (root / "scripts/current_analysis.py").write_text("QUERY = " + repr(query) + "\n")
        for name in [RECORD, "docs/CURRENT_ANALYSIS.json", "docs/SURVIVAL_SENSITIVITY_RESULTS.json"]:
            write(root / name, {})
        historical = {"status": "passed", "presentation_script_sha256": {},
                      "notebooks": [{"notebook": name, "status": "passed", "source_sha256": source_hash(value), "output_sha256": output_hash(value)} for name, value in books.items()]}
        for name, key in [(RECORD, "source_execution_record_sha256"), ("docs/CURRENT_ANALYSIS.json", "main_reference_sha256"), ("docs/SURVIVAL_SENSITIVITY_RESULTS.json", "supplement_reference_sha256")]:
            historical[key] = hashlib.sha256((root / name).read_bytes()).hexdigest()
        write(root / PRESENTATION_RECORD, historical)
        current = {"schema_version": 1, "status": "passed", "kind": "current_data_supplement_notebook_execution", "mode": "current",
                   "mode_environment_override": False, "reviewed_aggregate_outputs": True, "clinical_data_retrieved": True,
                   "patient_rows_or_identifiers_published": False, "main_analysis_updated": False, "tables_rebuilt": False,
                   "original_records_rewritten": False, "maximum_bytes_per_query": 200_000_000, "location": "US",
                   "source_file_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in CURRENT_BINDINGS}, "notebooks": []}
        query_sha = hashlib.sha256(query.replace("SELECT e.age", "SELECT e.subject_id,e.hadm_id,e.stay_id,e.age", 1).encode()).hexdigest()
        for name, analysis in CURRENT_SUPPLEMENTS.items():
            current["notebooks"].append({"notebook": name, "analysis": analysis, "status": "passed", "mode": "current",
                "data_origin": "authorized_local_current_cohort", "execution_kind": "authorized_read_only_current_data", "errors": 0,
                "figures": 2, "tables": 4, "code_cells": 5, "location": "US", "maximum_bytes_billed": 200_000_000,
                "ordinary_reference_checks_passed": True, "source_sha256": source_hash(books[name]), "output_sha256": output_hash(books[name]),
                "query_sha256": query_sha, "query": {"job_id": "synthetic_protocol_fixture_not_a_real_job", "dry_run_bytes": 12, "processed_bytes": 12, "billed_bytes": 12},
                "supplement_reference_comparison": {"passed": True, "numeric_values_checked": 1, "maximum_absolute_difference": 0.0, "relative_tolerance": 1e-10, "absolute_tolerance": 1e-10},
                "aggregate_output_safety": {"passed": True, "patient_rows_identifiers_credentials_local_paths_and_errors_detected": False}})
        write(root / CURRENT_SUPPLEMENT_RECORD, current)
        return books, current

    def test_reviewed_current_run_composes_without_rewriting_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); books, _ = self.fixture(root)
            before = (root / PRESENTATION_RECORD).read_bytes()
            record = load_record(root)
            self.assertEqual(record["current_supplement_record_status"], "passed")
            self.assertTrue(all(approved(value, record) for value in books.values()))
            self.assertEqual((root / PRESENTATION_RECORD).read_bytes(), before)

    def test_pending_review_cannot_fall_back_to_old_05_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); books, current = self.fixture(root)
            current["reviewed_aggregate_outputs"] = False; write(root / CURRENT_SUPPLEMENT_RECORD, current)
            record = load_record(root)
            self.assertTrue(approved(books["04a.ipynb"], record))
            self.assertTrue(all(not approved(books[name], record) for name in CURRENT_SUPPLEMENTS))

    def test_changed_runtime_helper_invalidates_only_current_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); books, _ = self.fixture(root)
            (root / "scripts/supplement_notebook_runtime.py").write_text("# changed fixture\n")
            record = load_record(root)
            self.assertTrue(approved(books["04a.ipynb"], record))
            self.assertTrue(all(not approved(books[name], record) for name in CURRENT_SUPPLEMENTS))

    def test_bad_mode_scope_query_guard_and_safety_are_rejected(self):
        for change in ["synthetic", "table_write", "over_budget", "wrong_query", "unsafe_output", "incomplete", "large_difference", "bool_as_int"]:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); books, current = self.fixture(root)
                if change == "synthetic": current["notebooks"][0]["mode"] = "synthetic"
                elif change == "table_write": current["tables_rebuilt"] = True
                elif change == "over_budget": current["notebooks"][0]["query"]["processed_bytes"] = 200_000_001
                elif change == "wrong_query": current["notebooks"][0]["query_sha256"] = "0" * 64
                elif change == "unsafe_output": current["notebooks"][0]["aggregate_output_safety"]["patient_rows_identifiers_credentials_local_paths_and_errors_detected"] = True
                elif change == "incomplete": current["notebooks"].pop()
                elif change == "large_difference": current["notebooks"][0]["supplement_reference_comparison"]["maximum_absolute_difference"] = .1
                else: current["reviewed_aggregate_outputs"] = 1
                write(root / CURRENT_SUPPLEMENT_RECORD, current)
                record = load_record(root)
                self.assertTrue(approved(books["04a.ipynb"], record))
                self.assertTrue(all(not approved(books[name], record) for name in CURRENT_SUPPLEMENTS))

    def test_malformed_record_does_not_break_historical_approval(self):
        for value in [[], {}, {"status": "passed", "source_file_sha256": []}]:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); books, _ = self.fixture(root)
                write(root / CURRENT_SUPPLEMENT_RECORD, value)
                record = load_record(root)
                self.assertTrue(approved(books["04a.ipynb"], record))
                self.assertFalse(approved(books[next(iter(CURRENT_SUPPLEMENTS))], record))

    def test_changed_notebook_output_still_fails_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); books, _ = self.fixture(root)
            record = load_record(root); value = copy.deepcopy(books[next(iter(CURRENT_SUPPLEMENTS))])
            value["cells"][0]["outputs"][0]["data"]["text/plain"] = "changed synthetic fixture"
            self.assertFalse(approved(value, record))


if __name__ == "__main__": unittest.main()
