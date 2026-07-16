from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from heos.demo import (
    DEMO_TIME,
    DEMO_VERSION,
    DemoStage,
    default_output_directory,
    render_report,
    run_demo,
    sunny_surplus_scenario,
    write_artifacts,
)
from heos.demo.cli import build_parser, main


def test_demo_succeeds() -> None:
    assert run_demo().result.success


def test_demo_version() -> None:
    assert run_demo().result.demo_version == DEMO_VERSION


def test_scenario_is_fixed() -> None:
    scenario = sunny_surplus_scenario()
    assert scenario.request.generated_at == DEMO_TIME
    assert scenario.scenario_id == "sunny-surplus-ev"


def test_scenario_has_three_candidates() -> None:
    assert len(sunny_surplus_scenario().candidates) == 3


def test_solar_ev_is_selected() -> None:
    assert run_demo().result.selected_strategy == "solar-ev"


def test_release_gate_releases() -> None:
    assert run_demo().result.release_status == "released"


def test_proof_is_valid() -> None:
    result = run_demo().result
    assert result.proof_valid
    assert result.certificate_id.startswith("pcd-")


def test_replay_token_is_present() -> None:
    assert run_demo().result.replay_token.startswith("replay-")


def test_compiler_uses_ev_scenario() -> None:
    result = run_demo().result
    assert result.compiler_scenario == "charge_ev_now"
    assert len(result.execution_steps) == 5


def test_safety_allows_plan() -> None:
    assert run_demo().result.safety_verdict == "allow"


def test_execution_completes() -> None:
    result = run_demo().result
    assert result.execution_status == "completed"
    assert len(result.execution_messages) == 5


def test_execution_is_dry_run() -> None:
    assert all(message.startswith("DRY-RUN:") for message in run_demo().result.execution_messages)


def test_feedback_score_is_high() -> None:
    assert run_demo().result.feedback_score >= 0.90


def test_memory_record_is_created() -> None:
    result = run_demo().result
    assert result.memory_record_id
    assert result.memory_fingerprint


def test_every_stage_passes() -> None:
    result = run_demo().result
    assert len(result.stages) == 8
    assert all(stage.passed for stage in result.stages)
    assert result.failed_stages == ()


def test_expected_stage_names() -> None:
    assert [stage.name for stage in run_demo().result.stages] == [
        "strategy",
        "release_gate",
        "proof",
        "compiler",
        "safety",
        "execution",
        "feedback",
        "memory",
    ]


def test_run_is_deterministic() -> None:
    first = run_demo().result
    second = run_demo().result
    assert first.audit_digest == second.audit_digest
    assert first.certificate_id == second.certificate_id
    assert first.strategy_decision_id == second.strategy_decision_id
    assert first.memory_record_id == second.memory_record_id


def test_audit_payload_is_deterministic() -> None:
    assert run_demo().audit_payload == run_demo().audit_payload


def test_audit_digest_is_sha256() -> None:
    digest = run_demo().result.audit_digest
    assert len(digest) == 64
    assert all(character in "0123456789ABCDEF" for character in digest)


def test_report_has_glass_box_title() -> None:
    assert "Glass Box Demonstrator" in render_report(run_demo().result)


@pytest.mark.parametrize(
    "phrase",
    [
        "Overall:             PASS",
        "Selected strategy:   solar-ev",
        "Release gate:        released",
        "Proof verification:  valid",
        "Safety verdict:      allow",
        "Execution:           completed",
        "No device command was sent.",
    ],
)
def test_report_contains_key_evidence(phrase: str) -> None:
    assert phrase in render_report(run_demo().result)


def test_result_to_dict_is_json_serializable() -> None:
    json.dumps(run_demo().result.to_dict())


def test_result_to_dict_contains_digest() -> None:
    data = run_demo().result.to_dict()
    assert data["audit_digest"] == run_demo().result.audit_digest


def test_write_artifacts_creates_four_files(tmp_path: Path) -> None:
    paths = write_artifacts(run_demo(), tmp_path / "out")
    assert len(paths) == 4
    assert all(path.is_file() for path in paths)


def test_artifact_names(tmp_path: Path) -> None:
    paths = write_artifacts(run_demo(), tmp_path / "out")
    assert {path.name for path in paths} == {
        "report.txt",
        "audit.json",
        "certificate.json",
        "audit.sha256",
    }


def test_audit_artifact_contains_digest(tmp_path: Path) -> None:
    run = run_demo()
    write_artifacts(run, tmp_path)
    document = json.loads((tmp_path / "audit.json").read_text(encoding="utf-8"))
    assert document["audit_digest"] == run.result.audit_digest


def test_certificate_artifact_contains_certificate_id(tmp_path: Path) -> None:
    run = run_demo()
    write_artifacts(run, tmp_path)
    content = (tmp_path / "certificate.json").read_text(encoding="utf-8")
    assert run.result.certificate_id in content


def test_digest_artifact_contains_digest(tmp_path: Path) -> None:
    run = run_demo()
    write_artifacts(run, tmp_path)
    assert run.result.audit_digest in (tmp_path / "audit.sha256").read_text(encoding="utf-8")


def test_writer_replaces_old_output(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    (output / "stale.txt").write_text("old", encoding="utf-8")
    write_artifacts(run_demo(), output)
    assert not (output / "stale.txt").exists()


def test_cli_human_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--output", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Overall:             PASS" in output
    assert "Artifacts:" in output


def test_cli_json_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--output", str(tmp_path), "--json"]) == 0
    document = json.loads(capsys.readouterr().out)
    assert document["success"] is True


def test_cli_quiet_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--output", str(tmp_path), "--quiet"]) == 0
    assert capsys.readouterr().out == ""
    assert (tmp_path / "report.txt").is_file()


def test_parser_default_output() -> None:
    assert build_parser().parse_args([]).output == default_output_directory()


def test_default_output_is_outside_current_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert default_output_directory() == tmp_path / ".heos" / "demo" / "latest"


def test_stage_is_immutable() -> None:
    stage = DemoStage("proof", "pass", "valid")
    with pytest.raises(FrozenInstanceError):
        stage.status = "fail"  # type: ignore[misc]


def test_stage_rejects_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        DemoStage("proof", "maybe", "unknown")


def test_result_is_immutable() -> None:
    result = run_demo().result
    with pytest.raises(FrozenInstanceError):
        result.success = False  # type: ignore[misc]


def test_result_rejects_empty_stages() -> None:
    result = run_demo().result
    with pytest.raises(ValueError, match="stages"):
        replace(result, stages=())


@pytest.mark.parametrize("field", ["feedback_score", "memory_quality"])
def test_result_rejects_invalid_scores(field: str) -> None:
    result = run_demo().result
    with pytest.raises(ValueError, match=field):
        replace(result, **{field: 1.1})


def test_metadata_is_sorted() -> None:
    result = replace(run_demo().result, metadata={"z": "2", "a": "1"})
    assert list(result.metadata) == ["a", "z"]


def test_alternatives_are_sorted() -> None:
    result = run_demo().result
    assert result.alternative_scores == tuple(sorted(result.alternative_scores))


def test_audit_records_all_proof_claims() -> None:
    claims = run_demo().audit_payload["proof"]["claims"]
    assert len(claims) >= 10
    assert all(item["passed"] for item in claims)


def test_audit_records_safety_findings() -> None:
    findings = run_demo().audit_payload["safety"]["findings"]
    assert {item["rule_id"] for item in findings} == {
        "kernel_health",
        "manual_lock",
        "grid_import_limit",
        "required_verification",
    }


def test_audit_records_rejected_alternatives() -> None:
    alternatives = run_demo().audit_payload["strategy"]["alternatives"]
    assert len(alternatives) == 3


def test_audit_has_no_runtime_timestamps() -> None:
    execution = run_demo().audit_payload["execution"]
    assert "created_at" not in execution


def test_demo_never_reports_device_execution() -> None:
    result = run_demo().result
    assert result.metadata["safety"] == "never bypassed"
    assert result.metadata["mode"] == "advise"
