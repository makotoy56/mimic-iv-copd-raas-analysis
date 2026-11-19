"""Offline input-policy regressions; no credential lookup, network or clinical fit."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from google.api_core.exceptions import BadRequest, Forbidden, NotFound, PermissionDenied, Unauthorized
from google.auth.exceptions import DefaultCredentialsError, RefreshError

import current_analysis as source
import survival_sensitivity as sensitivity
import supplement_notebook_runtime as runtime


ROOT = Path(__file__).resolve().parents[1]


def bundle(analysis="cluster", origin="authorized_local_current_cohort"):
    return {"data_origin": origin, "clinical_records_exported": False, "results": {analysis: {}}}


class NotebookInputPolicy(unittest.TestCase):
    def test_unset_mode_selects_current_and_explicit_modes_are_normalized(self):
        self.assertEqual(runtime.resolve_mode(environ={}), "current")
        for value in ["current", "local", "synthetic"]:
            with self.subTest(mode=value):
                self.assertEqual(runtime.resolve_mode(" " + value.upper() + " "), value)
                self.assertEqual(runtime.resolve_mode(environ={"COPD_NOTEBOOK_DATA_MODE": value}), value)

    def test_empty_unknown_and_nonstring_modes_stop(self):
        for value in ["", "auto", "CURRENT_OR_SYNTHETIC", 0]:
            with self.subTest(value=value), self.assertRaises(runtime.NotebookInputError) as caught:
                runtime.resolve_mode(environ={"COPD_NOTEBOOK_DATA_MODE": value})
            self.assertEqual(caught.exception.code, "UNKNOWN_MODE")

    def test_default_current_announces_before_loading_and_uses_clinical_guard(self):
        messages = []
        def loaded(*args, **kwargs):
            self.assertEqual(len(messages), 1)
            self.assertIn("Input mode = current", messages[0])
            self.assertIn("US dry run and 200 MB", messages[0])
            self.assertTrue(kwargs["clinical"])
            self.assertEqual(kwargs["bootstrap_replicates"], 1000)
            return bundle()
        with patch.dict(os.environ, {}, clear=True), patch.object(sensitivity, "run_supplement", side_effect=loaded) as run, patch.object(sensitivity, "synthetic_data") as fake:
            self.assertEqual(runtime.run_notebook_supplement("cluster", repo=ROOT, emit=messages.append), bundle())
        run.assert_called_once()
        fake.assert_not_called()

    def test_missing_reference_stops_before_loader_or_credentials(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(sensitivity, "run_supplement") as run, patch("google.auth.default") as credentials:
            messages = []
            with self.assertRaises(runtime.NotebookInputError) as caught:
                runtime.run_notebook_supplement("cluster", repo=Path(temporary), mode="current", emit=messages.append)
            self.assertEqual(caught.exception.code, "CURRENT_CONFIGURATION_MISSING")
            self.assertEqual(len(messages), 1)
        run.assert_not_called()
        credentials.assert_not_called()

    def test_malformed_reference_and_missing_query_stop_before_access(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(sensitivity, "run_supplement") as run, patch("google.auth.default") as credentials:
            root = Path(temporary); (root / "docs").mkdir()
            for content in ["{", "{}"]:
                (root / "docs/CURRENT_ANALYSIS.json").write_text(content)
                with self.assertRaises(runtime.NotebookInputError) as caught:
                    runtime.run_notebook_supplement("cluster", repo=root, mode="current", emit=lambda _: None)
                self.assertEqual(caught.exception.code, "CURRENT_CONFIGURATION_MISSING")
            with patch.object(source, "QUERY", ""):
                with self.assertRaises(runtime.NotebookInputError) as caught:
                    runtime.run_notebook_supplement("cluster", repo=ROOT, mode="current", emit=lambda _: None)
                self.assertEqual(caught.exception.code, "CURRENT_CONFIGURATION_MISSING")
        run.assert_not_called(); credentials.assert_not_called()

    def test_provider_failures_through_existing_wrapper_never_fall_back(self):
        cases = [
            (DefaultCredentialsError("DO_NOT_PRINT_CREDENTIAL"), "CURRENT_CREDENTIALS_MISSING"),
            (RefreshError("DO_NOT_PRINT_CREDENTIAL"), "CURRENT_CREDENTIALS_INVALID"),
            (Unauthorized("DO_NOT_PRINT_CREDENTIAL"), "CURRENT_CREDENTIALS_INVALID"),
            (Forbidden("DO_NOT_PRINT_CREDENTIAL"), "CURRENT_ACCESS_DENIED"),
            (PermissionDenied("DO_NOT_PRINT_CREDENTIAL"), "CURRENT_ACCESS_DENIED"),
            (NotFound("DO_NOT_PRINT_CREDENTIAL"), "CURRENT_SOURCE_NOT_FOUND"),
            (BadRequest("DO_NOT_PRINT_CREDENTIAL"), "CURRENT_QUERY_INVALID"),
            (ValueError("Current analysis SELECT exceeds the 200 MB limit"), "CURRENT_BYTE_LIMIT"),
            (TimeoutError("DO_NOT_PRINT_CREDENTIAL"), "CURRENT_EXECUTION_FAILED"),
            (ValueError({"credential": "DO_NOT_PRINT_CREDENTIAL"}), "CURRENT_EXECUTION_FAILED"),
        ]
        for error, code in cases:
            with self.subTest(code=code), patch.object(source, "load_current_data", side_effect=error) as load, patch.object(sensitivity, "synthetic_data") as fake, patch.object(sensitivity, "fit_clustered_cox") as fit:
                messages = []
                with self.assertRaises(runtime.NotebookInputError) as caught:
                    runtime.run_notebook_supplement("cluster", repo=ROOT, mode="current", emit=messages.append)
                self.assertEqual(caught.exception.code, code)
                self.assertIn("Next:", str(caught.exception))
                self.assertNotIn("DO_NOT_PRINT_CREDENTIAL", str(caught.exception) + " ".join(messages))
                self.assertTrue(caught.exception.__suppress_context__)
                load.assert_called_once_with(include_cluster_keys=True)
                fake.assert_not_called(); fit.assert_not_called()

    def test_reference_mismatch_stops_before_data_access(self):
        with patch.object(source, "QUERY", source.QUERY + " "), patch.object(source, "load_current_data") as load, patch.object(sensitivity, "synthetic_data") as fake:
            with self.assertRaises(runtime.NotebookInputError) as caught:
                runtime.run_notebook_supplement("cluster", repo=ROOT, mode="current", emit=lambda _: None)
            self.assertEqual(caught.exception.code, "CURRENT_REFERENCE_MISMATCH")
        load.assert_not_called(); fake.assert_not_called()

    def test_current_rejects_accidentally_returned_synthetic_results(self):
        with patch.object(sensitivity, "run_supplement", return_value=bundle(origin="fully_synthetic_not_MIMIC")) as run:
            with self.assertRaises(runtime.NotebookInputError) as caught:
                runtime.run_notebook_supplement("cluster", repo=ROOT, mode="current", emit=lambda _: None)
            self.assertEqual(caught.exception.code, "INPUT_ORIGIN_MISMATCH")
        self.assertTrue(run.call_args.kwargs["clinical"])

    def test_explicit_synthetic_never_checks_current_source(self):
        result = bundle("landmark", "fully_synthetic_not_MIMIC"); messages = []
        with patch.object(runtime, "_preflight_current") as check, patch.object(sensitivity, "run_supplement", return_value=result) as run, patch.object(source, "load_current_data") as load:
            self.assertEqual(runtime.run_notebook_supplement("landmark", repo=ROOT, mode="synthetic", emit=messages.append), result)
        check.assert_not_called(); load.assert_not_called()
        self.assertFalse(run.call_args.kwargs["clinical"])
        self.assertEqual(run.call_args.kwargs["bootstrap_replicates"], 200)
        self.assertIn("explicitly selected", messages[0])

    def test_explicit_local_reads_verified_bundle_without_query_or_fit(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(sensitivity, "run_supplement") as run, patch.object(source, "load_current_data") as load:
            root = Path(temporary); path = root / "reports/local_supplements/saved/aggregate_results.json"
            path.parent.mkdir(parents=True); (root / "docs").mkdir()
            reference = root / "docs/CURRENT_ANALYSIS.json"
            reference.write_text('{"mock_reference": true}')
            for origin in ["fully_synthetic_not_MIMIC", "authorized_local_current_cohort"]:
                # Protocol fixtures contain no clinical values or model rows.
                result = bundle("landmark", origin)
                result.update(supplement_version=sensitivity.VERSION, source_script_sha256=hashlib.sha256(Path(sensitivity.__file__).read_bytes()).hexdigest(), reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest())
                path.write_text(json.dumps(result))
                with self.subTest(origin=origin):
                    self.assertEqual(runtime.run_notebook_supplement("landmark", repo=root, mode="local", local_result=path, emit=lambda _: None), result)
        run.assert_not_called(); load.assert_not_called()

    def test_local_missing_or_invalid_file_stops_without_mode_change(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(sensitivity, "run_supplement") as run, patch.object(sensitivity, "synthetic_data") as fake:
            root = Path(temporary); path = root / "reports/local_supplements/saved/aggregate_results.json"
            for selected, expected in [(None, "LOCAL_FILE_REQUIRED"), (path, "LOCAL_FILE_NOT_FOUND")]:
                with self.assertRaises(runtime.NotebookInputError) as caught:
                    runtime.run_notebook_supplement("cluster", repo=root, mode="local", local_result=selected, emit=lambda _: None)
                self.assertEqual(caught.exception.code, expected)
            path.parent.mkdir(parents=True); path.write_text("{}")
            with self.assertRaises(runtime.NotebookInputError) as caught:
                runtime.run_notebook_supplement("cluster", repo=root, mode="local", local_result=path, emit=lambda _: None)
            self.assertEqual(caught.exception.code, "LOCAL_RESULT_INVALID")
        run.assert_not_called(); fake.assert_not_called()

    def test_current_bootstrap_minimum_is_not_weakened(self):
        for count in [200, 999, True, -1]:
            with self.subTest(count=count), patch.object(sensitivity, "run_supplement") as run:
                with self.assertRaises(runtime.NotebookInputError) as caught:
                    runtime.run_notebook_supplement("competing", repo=ROOT, mode="current", bootstrap_replicates=count, emit=lambda _: None)
                self.assertEqual(caught.exception.code, "INVALID_BOOTSTRAP_COUNT")
                run.assert_not_called()

    def test_missing_dependency_has_fixed_actionable_message(self):
        original = runtime.importlib.import_module
        def importing(name):
            if name == "survival_sensitivity":
                raise ModuleNotFoundError("DO_NOT_PRINT_PACKAGE_PATH")
            return original(name)
        with patch.object(runtime.importlib, "import_module", side_effect=importing):
            with self.assertRaises(runtime.NotebookInputError) as caught:
                runtime.run_notebook_supplement("cluster", repo=ROOT, mode="current", emit=lambda _: None)
            self.assertEqual(caught.exception.code, "DEPENDENCIES_MISSING")
            self.assertIn("Python 3.12", str(caught.exception))
            self.assertNotIn("DO_NOT_PRINT_PACKAGE_PATH", str(caught.exception))

    def test_invalid_aggregate_result_stops_before_display(self):
        for bad in [None, {}, {"clinical_records_exported": True, "results": {"cluster": {}}}, {"clinical_records_exported": False, "results": None}]:
            with self.subTest(result=bad), patch.object(sensitivity, "run_supplement", return_value=bad):
                with self.assertRaises(runtime.NotebookInputError) as caught:
                    runtime.run_notebook_supplement("cluster", repo=ROOT, mode="current", emit=lambda _: None)
                self.assertEqual(caught.exception.code, "INVALID_AGGREGATE_RESULT")

    def test_all_three_input_cells_clear_stale_results_on_current_failure(self):
        paths = sorted((ROOT / "notebooks").glob("05*.ipynb"))
        self.assertEqual(len(paths), 3)
        for path in paths:
            book = json.loads(path.read_text())
            cell = next("".join(c["source"]) for c in book["cells"] if c["cell_type"] == "code" and "bundle = notebook_runtime.run_notebook_supplement(" in "".join(c["source"]))
            shown = []; namespace = {"REPO_ROOT": ROOT, "notebook_runtime": runtime, "bundle": {"stale": True}, "result": {"stale": True}, "presentation": SimpleNamespace(display_input_context=lambda *a, **k: shown.append(a))}
            with self.subTest(notebook=path.name), patch.dict(os.environ, {"COPD_NOTEBOOK_DATA_MODE": "current"}), patch.object(runtime, "run_notebook_supplement", side_effect=runtime.NotebookInputError("CURRENT_ACCESS_DENIED")):
                with self.assertRaises(runtime.NotebookInputError):
                    exec(compile(cell, path.name + ":input-cell", "exec"), namespace)
            self.assertEqual(namespace["DATA_MODE"], "current")
            self.assertIsNone(namespace["bundle"]); self.assertIsNone(namespace["result"])
            self.assertFalse(shown)

    def test_policy_guidance_refresh_preserves_outputs_and_other_notebooks(self):
        from render_supplement_notebook_policy import generate, NAMES
        from notebook_figure_layout import input_context_section
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / "notebooks").mkdir()
            snapshots = {}
            for name in NAMES:
                book = json.loads((ROOT / "notebooks" / name).read_text())
                snapshots[name] = book
                for cell in book["cells"]:
                    if cell["cell_type"] == "markdown" and "".join(cell["source"]).startswith("<!-- Generated notebook input context -->"):
                        cell["source"] = input_context_section(name).splitlines(keepends=True)
                (root / "notebooks" / name).write_text(json.dumps(book))
            untouched = root / "notebooks/04a_outcomes_and_modeling.ipynb"
            shutil.copy2(ROOT / "notebooks/04a_outcomes_and_modeling.ipynb", untouched)
            protected = untouched.read_bytes()
            generate(root)
            self.assertEqual(untouched.read_bytes(), protected)
            for name in NAMES:
                updated = json.loads((root / "notebooks" / name).read_text())
                self.assertIn("New execution defaults to current clinical data", "\n".join("".join(c["source"]) for c in updated["cells"]))
                for before, after in zip(snapshots[name]["cells"], updated["cells"]):
                    for field in ["outputs", "execution_count", "metadata", "id"]:
                        self.assertEqual(before.get(field), after.get(field))

    def test_policy_guidance_rejects_old_source_before_writing(self):
        from render_supplement_notebook_policy import generate, NAMES
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / "notebooks").mkdir()
            for name in NAMES:
                raw = (ROOT / "notebooks" / name).read_bytes()
                if name == NAMES[-1]:
                    raw = raw.replace(b"bundle = notebook_runtime.run_notebook_supplement(", b"bundle = old_synthetic_entry_point(")
                (root / "notebooks" / name).write_bytes(raw)
            before = {name: (root / "notebooks" / name).read_bytes() for name in NAMES}
            with self.assertRaisesRegex(ValueError, "Current-mode notebook source is required"):
                generate(root)
            self.assertEqual(before, {name: (root / "notebooks" / name).read_bytes() for name in NAMES})


if __name__ == "__main__":
    unittest.main()
