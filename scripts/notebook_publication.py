"""Keep only explicitly reviewed aggregate execution outputs in Git.

The clean filter retains outputs only when both source and output hashes match
the versioned execution record. All other notebook outputs are removed.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


RECORD = "docs/NOTEBOOK_EXECUTION_VALIDATION.json"
PRESENTATION_RECORD = "docs/NOTEBOOK_PRESENTATION_VALIDATION.json"
CURRENT_SUPPLEMENT_RECORD = "docs/SUPPLEMENT_NOTEBOOK_EXECUTION_VALIDATION.json"
CURRENT_SUPPLEMENTS = {
    "05a_patient_cluster_sensitivity.ipynb": "cluster",
    "05b_competing_risks.ipynb": "competing",
    "05c_time_aligned_severity.ipynb": "landmark",
}
CURRENT_BINDINGS = {
    "scripts/supplement_notebook_runtime.py", "scripts/render_supplement_notebook_policy.py",
    "scripts/execute_current_supplement_notebooks.py", "scripts/survival_sensitivity.py",
    "scripts/current_analysis.py", "scripts/notebook_bq_runtime.py", "scripts/notebook_presentation.py",
    "scripts/presentation_catalog.py", "scripts/notebook_figure_layout.py",
    RECORD, PRESENTATION_RECORD, "docs/CURRENT_ANALYSIS.json", "docs/SURVIVAL_SENSITIVITY_RESULTS.json",
}
MIMES = {"text/plain", "text/html", "image/png", "image/svg+xml"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def text(value):
    return "".join(value) if isinstance(value, list) else value


def source_hash(book):
    return digest([[cell["cell_type"], text(cell.get("source", ""))]
                   for cell in book["cells"]])


def normalized_outputs(book):
    result = []
    for cell in book["cells"]:
        if cell["cell_type"] != "code":
            continue
        outputs = []
        for output in cell.get("outputs", []):
            kind = output["output_type"]
            if kind == "stream":
                outputs.append({"output_type": kind, "name": output["name"],
                                "text": text(output["text"])})
            elif kind in {"execute_result", "display_data"}:
                data = output.get("data", {})
                if not set(data).issubset(MIMES):
                    raise ValueError("Unsupported output MIME type")
                item = {"output_type": kind, "data": {k:text(v) for k,v in data.items()}, "metadata": {}}
                if kind == "execute_result":
                    item["execution_count"] = output.get("execution_count")
                outputs.append(item)
            else:
                raise ValueError("Errors and interactive outputs cannot be published")
        result.append({"execution_count":cell.get("execution_count"), "outputs":outputs})
    return result


def output_hash(book):
    return digest(normalized_outputs(book))


def _historical_record(root):
    """A presentation refresh must stay bound to its original execution evidence."""
    path=root/PRESENTATION_RECORD
    if not path.exists():
        return json.loads((root/RECORD).read_text()) if (root/RECORD).exists() else {}
    try:
        record=json.loads(path.read_text())
        bindings={RECORD:'source_execution_record_sha256','docs/CURRENT_ANALYSIS.json':'main_reference_sha256',
                  'docs/SURVIVAL_SENSITIVITY_RESULTS.json':'supplement_reference_sha256'}
        for name,key in bindings.items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=record[key]:return {'status':'stale'}
        for name,expected in record['presentation_script_sha256'].items():
            if hashlib.sha256((root/'scripts'/name).read_bytes()).hexdigest()!=expected:return {'status':'stale'}
        return record
    except (OSError,KeyError,ValueError):
        return {'status':'invalid'}


def _valid_current_record(root, record):
    """A new current run augments, never rewrites, the historical evidence."""
    try:
        if not isinstance(record, dict): return False
        required = {"schema_version": 1, "status": "passed", "kind": "current_data_supplement_notebook_execution",
                    "mode": "current", "mode_environment_override": False, "reviewed_aggregate_outputs": True,
                    "clinical_data_retrieved": True, "patient_rows_or_identifiers_published": False,
                    "main_analysis_updated": False, "tables_rebuilt": False, "original_records_rewritten": False,
                    "maximum_bytes_per_query": 200_000_000, "location": "US"}
        if any((record.get(key) is not value if isinstance(value, bool) else record.get(key) != value)
               for key, value in required.items()): return False
        bindings = record["source_file_sha256"]
        if not isinstance(bindings, dict) or not CURRENT_BINDINGS.issubset(bindings): return False
        for name, expected in bindings.items():
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                return False
        query_tree = ast.parse((root / "scripts/current_analysis.py").read_text())
        source_query = next(ast.literal_eval(node.value) for node in query_tree.body
                            if isinstance(node, ast.Assign)
                            and any(isinstance(target, ast.Name) and target.id == "QUERY" for target in node.targets))
        if not isinstance(source_query, str): return False
        expected_query_sha = hashlib.sha256(source_query.replace("SELECT e.age", "SELECT e.subject_id,e.hadm_id,e.stay_id,e.age", 1).encode()).hexdigest()
        rows = record["notebooks"]
        if len(rows) != 3 or {row["notebook"] for row in rows} != set(CURRENT_SUPPLEMENTS): return False
        for row in rows:
            if (row["analysis"] != CURRENT_SUPPLEMENTS[row["notebook"]] or row["status"] != "passed"
                    or row["mode"] != "current" or row["data_origin"] != "authorized_local_current_cohort"
                    or row["execution_kind"] != "authorized_read_only_current_data" or row["errors"] != 0
                    or row["figures"] != 2 or row["tables"] != 4 or row["code_cells"] != 5
                    or row["location"] != "US" or row["maximum_bytes_billed"] != 200_000_000
                    or row["ordinary_reference_checks_passed"] is not True): return False
            comparison = row["supplement_reference_comparison"]
            if (comparison["passed"] is not True or type(comparison["numeric_values_checked"]) is not int
                    or comparison["numeric_values_checked"] <= 0
                    or not 0 <= comparison["maximum_absolute_difference"] <= 1e-8
                    or not 0 <= comparison["relative_tolerance"] <= 1e-8
                    or not 0 <= comparison["absolute_tolerance"] <= 1e-8): return False
            safety = row["aggregate_output_safety"]
            if (safety["passed"] is not True
                    or safety["patient_rows_identifiers_credentials_local_paths_and_errors_detected"] is not False): return False
            if not isinstance(row["query"]["job_id"], str) or not row["query"]["job_id"]: return False
            for key in ["dry_run_bytes", "processed_bytes", "billed_bytes"]:
                value = row["query"][key]
                if type(value) is not int or not 0 <= value <= 200_000_000: return False
            for key in ["source_sha256", "output_sha256", "query_sha256"]:
                value = row[key]
                if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value): return False
            if row["query_sha256"] != expected_query_sha: return False
        return True
    except (OSError, KeyError, TypeError, ValueError, SyntaxError, StopIteration):
        return False


def load_record(root):
    root = Path(root)
    historical = _historical_record(root)
    path = root / CURRENT_SUPPLEMENT_RECORD
    if not path.exists() or historical.get("status") != "passed": return historical
    combined = copy.deepcopy(historical)
    # Once a new current record is present, an invalid record cannot silently
    # fall back to the old 05-source/output approval. Unchanged 00–04 stay valid.
    for row in combined.get("notebooks", []):
        if row.get("notebook") in CURRENT_SUPPLEMENTS: row["status"] = "superseded_current_record"
    try:
        current = json.loads(path.read_text())
    except (OSError, ValueError):
        current = {}
    valid = _valid_current_record(root, current)
    combined["current_supplement_record_status"] = "passed" if valid else "invalid_or_stale"
    combined["kind"] = "historical_presentation_and_reviewed_current_supplements"
    if valid: combined["notebooks"].extend(current["notebooks"])
    return combined


def approved(book, record):
    if record.get("status") != "passed":
        return False
    source = source_hash(book)
    candidates = [row for row in record.get("notebooks", [])
                  if row.get("source_sha256") == source and row.get("status") == "passed"]
    if not candidates:
        return False
    try:
        output = output_hash(book)
    except ValueError:
        return False
    return any(row.get("output_sha256") == output for row in candidates)


def sanitize(book, retain):
    book = copy.deepcopy(book)
    book = {key:book[key] for key in ["nbformat", "nbformat_minor", "cells"]}
    # Local kernel paths, VS Code state and execution metadata stay on SSD only.
    book["metadata"] = {"kernelspec":{"display_name":"Python 3", "language":"python", "name":"python3"},
                        "language_info":{"name":"python"}}
    kept = iter(normalized_outputs(book)) if retain else None
    for number, cell in enumerate(book["cells"]):
        for key in list(cell):
            if key not in {"id", "cell_type", "source", "metadata", "outputs", "execution_count"}:
                del cell[key]
        cell["id"] = str(number)
        cell["metadata"] = {"tags":cell["metadata"]["tags"]} if cell.get("metadata", {}).get("tags") else {}
        if cell["cell_type"] == "code":
            if retain:
                cell.update(next(kept))
            else:
                cell["outputs"] = []
                cell["execution_count"] = None
    return book


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.repo.resolve()
    if args.install:
        command = shlex.join([sys.executable, str(root / "scripts/notebook_publication.py")])
        for key, value in [("clean", command), ("smudge", "cat"), ("required", "true")]:
            subprocess.run(["git", "config", "--local", "filter.portfolio-notebook."+key, value], cwd=root, check=True)
        print("Installed the local reviewed-output notebook filter")
        return
    record = load_record(root)
    if args.check:
        books = list((root / "notebooks").glob("*.ipynb"))
        names = {row["notebook"] for row in record.get("notebooks", [])}
        if record.get("status") != "passed" or not names:
            raise SystemExit("A passed notebook execution record is required")
        checked = [path for path in books if path.name in names]
        failed = [path.name for path in checked if not approved(json.loads(path.read_text()), record)]
        if len(checked) != len(names) or failed:
            raise SystemExit("Notebook execution record does not match saved outputs")
        print(f"Verified reviewed sources and outputs for {len(checked)} notebooks ({record.get('kind','clinical_execution')})")
        return
    book = json.load(sys.stdin)
    json.dump(sanitize(book, approved(book, record)), sys.stdout, indent=1, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
