"""Refresh 05-only mode guidance after the historical saved-summary generators.

No queries, fitting, output replacement or validation-record changes occur here.
Keep the historical presentation modules unchanged so their existing bindings
continue to validate the unchanged 00–04 notebook snapshots.
"""
from pathlib import Path
import json

from supplement_notebook_runtime import NOTEBOOK_INPUT_GUIDANCE, RUNTIME_GUIDANCE


NAMES = (
    "05a_patient_cluster_sensitivity.ipynb",
    "05b_competing_risks.ipynb",
    "05c_time_aligned_severity.ipynb",
)
CURRENT_EXECUTION_RECORD = "SUPPLEMENT_NOTEBOOK_EXECUTION_VALIDATION.json"


def generate(repo):
    repo = Path(repo)
    selected = []
    # Validate all three sources before writing any file. Do not apply new-mode
    # prose to an old source that still selects synthetic data by default.
    for name in NAMES:
        path = repo / "notebooks" / name
        book = json.loads(path.read_text())
        code = "\n".join("".join(c["source"]) for c in book["cells"] if c["cell_type"] == "code")
        if "bundle = notebook_runtime.run_notebook_supplement(" not in code:
            raise ValueError("Current-mode notebook source is required before refreshing input-policy guidance")
        selected.append((path, book))
    for path, book in selected:
        changed = False
        for cell in book["cells"]:
            if cell["cell_type"] != "markdown":
                continue
            original = "".join(cell["source"])
            text = original
            if text.startswith("<!-- Generated notebook input context -->"):
                evidence = text[text.index("Stored-output evidence:"):]
                if (repo / "docs" / CURRENT_EXECUTION_RECORD).is_file() and CURRENT_EXECUTION_RECORD not in evidence:
                    evidence += " · [current-mode execution](../docs/" + CURRENT_EXECUTION_RECORD + ")."
                text = "<!-- Generated notebook input context -->\n\n## Inputs and execution mode\n\n" + NOTEBOOK_INPUT_GUIDANCE + "\n\n" + evidence
            elif text.startswith("## Runtime execution"):
                text = "## Runtime execution\n\n" + RUNTIME_GUIDANCE
            if text != original:
                cell["source"] = text.splitlines(keepends=True)
                changed = True
        if changed:
            path.write_text(json.dumps(book, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[1])
