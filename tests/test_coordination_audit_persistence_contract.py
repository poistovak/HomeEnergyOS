from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from heos.coordination import JsonlCoordinationAuditTrail

NOW = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)


def append_two_records(
    trail: JsonlCoordinationAuditTrail,
) -> None:
    trail.issue_and_append(
        cycle_id="persist-cycle",
        requested_mode="autonomous",
        effective_mode="supervised",
        downgraded=True,
        operator_approved=False,
        autonomy_authorized=False,
        release_status="held",
        release_id="release-1",
        recorded_at=NOW,
    )

    trail.issue_and_append(
        cycle_id="persist-cycle",
        requested_mode="autonomous",
        effective_mode="supervised",
        downgraded=True,
        operator_approved=True,
        autonomy_authorized=False,
        release_status="released",
        release_id="release-2",
        approval_resume=True,
        recorded_at=NOW + timedelta(seconds=1),
    )


def test_jsonl_audit_persists_records(tmp_path):
    path = tmp_path / "coordination-audit.jsonl"
    trail = JsonlCoordinationAuditTrail(path)

    append_two_records(trail)

    assert path.exists()
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_jsonl_audit_reloads_records(tmp_path):
    path = tmp_path / "coordination-audit.jsonl"

    first = JsonlCoordinationAuditTrail(path)
    append_two_records(first)

    restored = JsonlCoordinationAuditTrail(path)

    assert len(restored.records()) == 2


def test_reloaded_audit_chain_verifies(tmp_path):
    path = tmp_path / "coordination-audit.jsonl"

    first = JsonlCoordinationAuditTrail(path)
    append_two_records(first)

    restored = JsonlCoordinationAuditTrail(path)

    assert restored.verify_chain() is True


def test_reloaded_records_preserve_chain_link(tmp_path):
    path = tmp_path / "coordination-audit.jsonl"

    first = JsonlCoordinationAuditTrail(path)
    append_two_records(first)

    restored = JsonlCoordinationAuditTrail(path)
    records = restored.records()

    assert records[0].previous_digest is None
    assert records[1].previous_digest == records[0].digest


def test_reloaded_records_preserve_release_history(tmp_path):
    path = tmp_path / "coordination-audit.jsonl"

    first = JsonlCoordinationAuditTrail(path)
    append_two_records(first)

    restored = JsonlCoordinationAuditTrail(path)
    records = restored.records()

    assert records[0].release_status == "held"
    assert records[1].release_status == "released"
    assert records[1].approval_resume is True


def test_blank_jsonl_lines_are_ignored(tmp_path):
    path = tmp_path / "coordination-audit.jsonl"
    trail = JsonlCoordinationAuditTrail(path)

    trail.issue_and_append(
        cycle_id="blank-line-cycle",
        requested_mode="autonomous",
        effective_mode="advise",
        downgraded=True,
        operator_approved=False,
        autonomy_authorized=False,
        release_status="released",
        release_id="release-1",
        recorded_at=NOW,
    )

    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n\n")

    restored = JsonlCoordinationAuditTrail(path)

    assert len(restored.records()) == 1
    assert restored.verify_chain() is True


def test_tampered_persisted_record_is_rejected(tmp_path):
    path = tmp_path / "coordination-audit.jsonl"
    trail = JsonlCoordinationAuditTrail(path)

    append_two_records(trail)

    lines = path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[0])
    payload["release_status"] = "rejected"
    lines[0] = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="line 1",
    ):
        JsonlCoordinationAuditTrail(path)


def test_broken_persisted_chain_is_rejected(tmp_path):
    path = tmp_path / "coordination-audit.jsonl"
    trail = JsonlCoordinationAuditTrail(path)

    append_two_records(trail)

    lines = path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[1])
    payload["previous_digest"] = None
    lines[1] = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="line 2",
    ):
        JsonlCoordinationAuditTrail(path)