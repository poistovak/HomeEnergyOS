from __future__ import annotations

import json
import shutil
from pathlib import Path

from heos.proof_carrying import dumps_certified_decision

from .pipeline import DemoRun
from .reporting import render_report


def default_output_directory() -> Path:
    return Path.home() / ".heos" / "demo" / "latest"


def write_artifacts(run: DemoRun, output_directory: Path) -> tuple[Path, ...]:
    destination = Path(output_directory).expanduser().resolve()
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    report_path = destination / "report.txt"
    audit_path = destination / "audit.json"
    certificate_path = destination / "certificate.json"
    digest_path = destination / "audit.sha256"

    report_path.write_text(render_report(run.result), encoding="utf-8", newline="\n")
    audit_document = {**run.audit_payload, "audit_digest": run.result.audit_digest}
    audit_path.write_text(
        json.dumps(audit_document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    certificate_path.write_text(
        dumps_certified_decision(run.certified_decision) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    digest_path.write_text(
        f"CANONICAL_AUDIT_SHA256={run.result.audit_digest}\n",
        encoding="utf-8",
        newline="\n",
    )
    return report_path, audit_path, certificate_path, digest_path
