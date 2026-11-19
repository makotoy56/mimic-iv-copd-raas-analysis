"""Public notebook previews must preserve execution and reject stale results."""
from pathlib import Path
import shutil
import tempfile
import unittest

import nbformat

from render_landmark_summary import generate, FIGURE, MARKER, NOTEBOOK

REPO = Path(__file__).resolve().parents[1]


class LandmarkPreviewTests(unittest.TestCase):
    def fixture(self, root):
        for name in ["docs/CURRENT_ANALYSIS.json", "docs/SURVIVAL_SENSITIVITY_RESULTS.json",
                     "docs/SURVIVAL_SUPPLEMENTS_VALIDATION.json", "scripts/survival_sensitivity.py",
                     "notebooks/" + NOTEBOOK]:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / name, target)

    def test_regeneration_preserves_execution_cells_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            path = root / "notebooks" / NOTEBOOK
            original = nbformat.read(path, as_version=4)
            def execution_cells(book):
                return [cell for cell in book.cells if cell.cell_type == "code"]
            execution = execution_cells(original)
            generate(root)
            once = path.read_bytes()
            figure = (root / "assets" / FIGURE).read_bytes()
            updated = nbformat.read(path, as_version=4)
            self.assertEqual(execution, execution_cells(updated))
            self.assertEqual(sum(c.cell_type == "markdown" and c.source.startswith(MARKER) for c in updated.cells), 4)
            generate(root)
            self.assertEqual(once, path.read_bytes())
            self.assertEqual(figure, (root / "assets" / FIGURE).read_bytes())

    def test_changed_aggregate_record_fails_before_replacing_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            path = root / "notebooks" / NOTEBOOK
            original = path.read_bytes()
            record = root / "docs/SURVIVAL_SENSITIVITY_RESULTS.json"
            record.write_text(record.read_text() + "\n")
            with self.assertRaises(ValueError):
                generate(root)
            self.assertEqual(original, path.read_bytes())
            self.assertFalse((root / "assets" / FIGURE).exists())


if __name__ == "__main__":
    unittest.main()
