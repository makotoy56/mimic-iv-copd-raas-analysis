"""Keep only explicitly reviewed aggregate execution outputs in Git.

The clean filter retains outputs only when both source and output hashes match
the versioned execution record. All other notebook outputs are removed.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


RECORD = "docs/NOTEBOOK_EXECUTION_VALIDATION.json"
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
    record_path = root / RECORD
    record = json.loads(record_path.read_text()) if record_path.exists() else {}
    if args.check:
        books = list((root / "notebooks").glob("*.ipynb"))
        names = {row["notebook"] for row in record.get("notebooks", [])}
        if record.get("status") != "passed" or not names:
            raise SystemExit("A passed notebook execution record is required")
        checked = [path for path in books if path.name in names]
        failed = [path.name for path in checked if not approved(json.loads(path.read_text()), record)]
        if len(checked) != len(names) or failed:
            raise SystemExit("Notebook execution record does not match saved outputs")
        print(f"Verified reviewed sources and outputs for {len(checked)} notebooks")
        return
    book = json.load(sys.stdin)
    json.dump(sanitize(book, approved(book, record)), sys.stdout, indent=1, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
