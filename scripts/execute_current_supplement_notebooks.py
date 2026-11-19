"""Execute only 05a–05c with the current-data default; emit a private review candidate.

Requires explicit --current-data. Existing bounded read-only loaders are used
unchanged. Patient rows stay inside each local kernel; only aggregate bundles
are saved under the ignored output directory. No publication record is approved
or overwritten by this command.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import sys
import threading
import time

NAMES = {
    "05a_patient_cluster_sensitivity.ipynb": "cluster",
    "05b_competing_risks.ipynb": "competing",
    "05c_time_aligned_severity.ipynb": "landmark",
}
LIMIT = 200_000_000


def event(status, **fields):
    print(json.dumps({"status": status, **fields}), flush=True)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def compare_numeric(actual, expected):
    comparisons = []
    def walk(a, e):
        if isinstance(e, dict):
            require(isinstance(a, dict), "AGGREGATE_SCHEMA_MISMATCH")
            for key, value in e.items():
                if isinstance(value, str) or value is None:
                    continue
                require(key in a, "AGGREGATE_SCHEMA_MISMATCH")
                walk(a[key], value)
        elif isinstance(e, list):
            require(isinstance(a, list) and len(a) == len(e), "AGGREGATE_SCHEMA_MISMATCH")
            for x, y in zip(a, e):
                walk(x, y)
        elif isinstance(e, bool):
            require(a is e, "AGGREGATE_REFERENCE_MISMATCH")
        elif isinstance(e, (int, float)):
            require(math.isfinite(float(a)) and math.isclose(float(a), e, rel_tol=1e-10, abs_tol=1e-10), "AGGREGATE_REFERENCE_MISMATCH")
            if isinstance(e, int):
                require(a == e, "AGGREGATE_REFERENCE_COUNT_MISMATCH")
            comparisons.append(abs(float(a) - e))
    walk(actual, expected)
    return {"passed": True, "numeric_values_checked": len(comparisons),
            "maximum_absolute_difference": max(comparisons, default=0.0),
            "relative_tolerance": 1e-10, "absolute_tolerance": 1e-10}


def compact_model(model):
    estimate = model["estimates"]["raas_pre_icu"]
    return {**{key: model[key] for key in ["n", "events", "patients"]}, "hr": estimate["hr"],
            **{kind: {key: estimate[kind][key] for key in ["lower_95", "upper_95", "p"]}
               for kind in ["ordinary", "patient_cluster"]}}


def compare_bundle(bundle, reference, analysis):
    require(bundle["data_origin"] == "authorized_local_current_cohort", "CURRENT_ORIGIN_REQUIRED")
    require(bundle["clinical_records_exported"] is False and bundle["main_analysis_updated"] is False, "INVALID_RESULT_SCOPE")
    require(all(row["passed"] for row in bundle["ordinary_reference_checks"].values()), "ORDINARY_REFERENCE_FAILED")
    result = bundle["results"][analysis]
    if analysis == "cluster":
        actual = {key: compact_model(value) for key, value in result["models"].items()}
        checked = compare_numeric(actual, reference["cluster"]["models"])
        primary = result["models"]["primary_refined"]
        compare_numeric(primary, reference["cohort"])
    elif analysis == "landmark":
        actual = {"eligibility": result["eligibility"],
                  "models": {key: compact_model(value) for key, value in result["models"].items()}}
        checked = compare_numeric(actual, {key: reference["landmark"][key] for key in ["eligibility", "models"]})
    else:
        actual = {**result, "cause_specific_cox": {key: compact_model(value) for key, value in result["cause_specific_cox"].items()}}
        checked = compare_numeric(actual, reference["competing"])
        require(result["bootstrap_replicates"] >= 1000 and result["bootstrap_seed"] == 20261118, "CLINICAL_BOOTSTRAP_GUARD_FAILED")
    return checked


class TableHeaders(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_header = False; self.text = []; self.headers = []
    def handle_starttag(self, tag, attrs):
        if tag == "th": self.in_header = True; self.text = []
    def handle_data(self, data):
        if self.in_header: self.text.append(data)
    def handle_endtag(self, tag):
        if tag == "th" and self.in_header:
            self.headers.append("".join(self.text).strip().lower()); self.in_header = False


def check_outputs(book):
    from PIL import Image
    from notebook_publication import normalized_outputs
    forbidden = {"subject_id", "hadm_id", "stay_id", "admittime", "dischtime", "deathtime", "intime", "outtime"}
    secret = re.compile(r"-----BEGIN .*PRIVATE KEY-----|ya29\.[A-Za-z0-9_-]+|gh[pousr]_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{30,}")
    outputs = images = 0
    for cell in normalized_outputs(book):
        for output in cell["outputs"]:
            outputs += 1
            data = output.get("data", {})
            visible = "\n".join(data.get(key, "") for key in ["text/html", "text/plain"]) + output.get("text", "")
            require(not secret.search(visible), "SENSITIVE_OUTPUT_REQUIRES_REVIEW")
            require(not re.search(r"/Users/|/Volumes/|file://|file\+\.vscode", visible), "LOCAL_PATH_OUTPUT_REQUIRES_REVIEW")
            require(not re.search(r"^\s*(?:\d+\s+)?subject_id\s+hadm_id\b", visible, re.M), "ROW_OUTPUT_REQUIRES_REVIEW")
            parser = TableHeaders(); parser.feed(data.get("text/html", ""))
            require(not forbidden.intersection(parser.headers), "ROW_OUTPUT_REQUIRES_REVIEW")
            if "image/png" in data:
                with Image.open(io.BytesIO(base64.b64decode(data["image/png"]))) as picture:
                    picture.verify()
                images += 1
    return {"passed": True, "output_blocks": outputs, "png_outputs": images,
            "patient_rows_identifiers_credentials_local_paths_and_errors_detected": False}


def execute(repo, output):
    import nbformat
    import nbclient
    from nbclient import NotebookClient
    from notebook_figure_layout import validate_layout, validate_tables
    from notebook_publication import source_hash, output_hash
    from supplement_notebook_runtime import GUIDANCE
    repo = Path(repo).resolve(); output = Path(output).resolve()
    allowed = repo / "reports/local_supplements"
    require(output.is_relative_to(allowed) and output != allowed and not output.exists(), "FRESH_IGNORED_OUTPUT_DIRECTORY_REQUIRED")
    require(sys.version_info[:2] == (3, 12), "REPOSITORY_PYTHON_312_REQUIRED")
    output.mkdir(parents=True)
    (output / "before").mkdir(); (output / "executed").mkdir()
    kernel = "copd-current-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    kernel_dir = output / "jupyter/kernels" / kernel; kernel_dir.mkdir(parents=True)
    (kernel_dir / "kernel.json").write_text(json.dumps({"argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                                                     "display_name": "ICU-COPD Python 3.12", "language": "python"}))
    os.environ.update(JUPYTER_PATH=str(output / "jupyter"), JUPYTER_RUNTIME_DIR=str(output / "jupyter/runtime"),
                      MPLCONFIGDIR=str(output / "matplotlib"), PYTHONDONTWRITEBYTECODE="1")
    os.environ.pop("COPD_NOTEBOOK_DATA_MODE", None)  # Prove the actual unset/default path is current.
    reference = json.loads((repo / "docs/SURVIVAL_SENSITIVITY_RESULTS.json").read_text())
    records = []
    for name, analysis in NAMES.items():
        path = repo / "notebooks" / name
        (output / "before" / name).write_bytes(path.read_bytes())
        book = nbformat.read(path, as_version=4)
        for cell in book.cells:
            if cell.cell_type == "code": cell.outputs = []; cell.execution_count = None
        run_dir = output / analysis; run_dir.mkdir()
        os.environ["COPD_NOTEBOOK_RUN_DIR"] = str(run_dir)
        started = time.monotonic(); stop = threading.Event()
        def heartbeat():
            while not stop.wait(30): event("running", notebook=name, elapsed_seconds=round(time.monotonic() - started))
        thread = threading.Thread(target=heartbeat, daemon=True); thread.start()
        def cell_start(cell, cell_index, **kwargs):
            if cell.cell_type == "code": event("cell_started", notebook=name, cell_index=cell_index)
        event("started", notebook=name, mode="current", mode_environment_override=False)
        try:
            NotebookClient(book, timeout=1800, kernel_name=kernel, resources={"metadata": {"path": str(path.parent)}},
                           record_timing=False, allow_errors=False, on_cell_start=cell_start).execute()
            bundle = json.loads((run_dir / "supplement_bundle.json").read_text())
            require(bundle["reference_sha256"] == digest(repo / "docs/CURRENT_ANALYSIS.json"), "MAIN_REFERENCE_CHANGED")
            require(bundle["source_script_sha256"] == digest(repo / "scripts/survival_sensitivity.py"), "SCIENTIFIC_SOURCE_CHANGED")
            query = bundle["execution"]
            require(0 <= query["dry_run_bytes"] <= LIMIT and 0 <= query["processed_bytes"] <= LIMIT, "READ_GUARD_FAILED")
            comparison = compare_bundle(bundle, reference, analysis)
            privacy = check_outputs(book)
            figures, tables = len(validate_layout(book)), len(validate_tables(book, path.stem))
            nbformat.validate(book)
            nbformat.write(book, output / "executed" / name)
            records.append({"notebook": name, "analysis": analysis, "status": "passed", "mode": "current",
                            "data_origin": bundle["data_origin"], "execution_kind": "authorized_read_only_current_data",
                            "source_sha256": source_hash(book), "output_sha256": output_hash(book),
                            "code_cells": sum(c.cell_type == "code" for c in book.cells), "figures": figures, "tables": tables,
                            "errors": 0, "query": {key: query[key] for key in ["job_id", "dry_run_bytes", "processed_bytes", "billed_bytes"]},
                            "query_sha256": bundle["query_sha256"], "location": "US", "maximum_bytes_billed": LIMIT,
                            "ordinary_reference_checks_passed": True, "supplement_reference_comparison": comparison,
                            "aggregate_output_safety": privacy, "elapsed_seconds": round(time.monotonic() - started, 2)})
            event("passed", notebook=name, figures=figures, tables=tables, reference_comparison=True,
                  dry_run_bytes=query["dry_run_bytes"], elapsed_seconds=round(time.monotonic() - started, 2))
        except Exception as error:
            nbformat.write(book, output / "failed_notebook.ipynb")
            # Provider/cell exception text may contain details; never send it to stdout.
            message = str(error)
            code = next((key for key in GUIDANCE if re.search(r"\b" + key + r"\b", message)), "CURRENT_NOTEBOOK_EXECUTION_OR_REVIEW_FAILED")
            (output / "failure.json").write_text(json.dumps({"notebook": name, "code": code, "error_type": type(error).__name__}))
            event("failed", notebook=name, code=code, error_type=type(error).__name__)
            raise RuntimeError(code) from None
        finally:
            stop.set(); thread.join(timeout=1)
    candidate = {"schema_version": 1, "status": "pending_review", "kind": "current_data_supplement_notebook_execution",
                 "executed_at_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
                 "nbclient": nbclient.__version__, "mode": "current", "mode_environment_override": False,
                 "maximum_bytes_per_query": LIMIT, "location": "US", "patient_rows_or_identifiers_published": False,
                 "main_analysis_updated": False, "clinical_data_retrieved": True, "tables_rebuilt": False,
                 "original_records_rewritten": False, "notebooks": records,
                 "limitations": ["These are observational prescription-order associations, not causal treatment effects.",
                                 "The original first-day-SOFA timing and landmark-population limitations remain.",
                                 "Numerical reproduction is not a new independent statistical implementation check."]}
    (output / "review_candidate.json").write_text(json.dumps(candidate, indent=2) + "\n")
    event("execution_complete_review_pending", notebooks=len(records), table_writes=0)
    return candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--current-data", action="store_true", required=True)
    args = parser.parse_args()
    try:
        execute(args.repo, args.output)
    except Exception as error:
        event("stopped", error_type=type(error).__name__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
