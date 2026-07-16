from __future__ import annotations

import json
import shutil
from pathlib import Path

from .models import RobustnessRun
from .reporting import render_report


def default_output_directory() -> Path:
    return Path.home() / ".heos" / "robustness" / "latest"


def write_artifacts(run: RobustnessRun, output_directory: Path) -> tuple[Path, ...]:
    destination = Path(output_directory).expanduser().resolve()
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    report_path = destination / "report.txt"
    json_path = destination / "robustness.json"
    digest_path = destination / "certificate.sha256"
    report_path.write_text(render_report(run), encoding="utf-8", newline="\n")
    json_path.write_text(
        json.dumps(run.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    digest_path.write_text(
        f"ROBUSTNESS_CERTIFICATE_SHA256={run.certificate.certificate_digest}\n",
        encoding="utf-8",
        newline="\n",
    )
    return report_path, json_path, digest_path
