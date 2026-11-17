"""Render in an isolated Quarto project, then copy the finished local report to docs."""
from pathlib import Path
import shutil
import subprocess
import tempfile

from render_current_report import generate


def build(repo):
    generate(repo)
    with tempfile.TemporaryDirectory(prefix="copd-quarto-") as temp:
        project = Path(temp)
        (project / "_quarto.yml").write_text("project:\n  type: default\n  output-dir: _site\n")
        shutil.copy2(repo / "reports/copd_raas_survival_report.qmd", project)
        shutil.copytree(repo / "assets", project / "assets")
        subprocess.run(["quarto", "render", "copd_raas_survival_report.qmd", "--no-execute"], cwd=project, check=True)
        rendered = project / "_site"
        shutil.copy2(rendered / "copd_raas_survival_report.html", repo / "docs")
        shutil.copytree(rendered / "copd_raas_survival_report_files", repo / "docs/copd_raas_survival_report_files", dirs_exist_ok=True)
    print("Updated docs/copd_raas_survival_report.html without changing the published site")


if __name__ == "__main__":
    build(Path(__file__).resolve().parents[1])
