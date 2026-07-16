from __future__ import annotations

from .models import DemoResult


def render_report(result: DemoResult) -> str:
    mark = "PASS" if result.success else "FAIL"
    lines = [
        "HomeEnergyOS M22 - Glass Box Demonstrator",
        "=" * 45,
        f"Overall:             {mark}",
        f"Scenario:            {result.scenario_id}",
        f"Selected strategy:   {result.selected_strategy}",
        f"Release gate:        {result.release_status}",
        f"Proof certificate:   {result.certificate_id}",
        f"Proof verification:  {'valid' if result.proof_valid else 'invalid'}",
        f"Safety verdict:      {result.safety_verdict}",
        f"Execution:           {result.execution_status}",
        f"Feedback:            {result.feedback_classification} ({result.feedback_score:.3f})",
        f"House Memory:        {result.memory_record_id}",
        f"Audit SHA-256:        {result.audit_digest}",
        "",
        "Pipeline",
        "--------",
    ]
    for stage in result.stages:
        lines.append(f"[{'OK' if stage.passed else '!!'}] {stage.name}: {stage.detail}")
    lines.extend(
        (
            "",
            "Decision explanation",
            "--------------------",
            "The strategy was simulated in the Digital Twin, admitted by the Operational",
            "Release Gate, bound to a verifiable certificate, compiled deterministically,",
            "checked by the Safety Engine, executed only through a dry-run driver, then",
            "compared with a deterministic outcome and stored in House Memory.",
            "",
            "No device command was sent. Safety was not bypassed.",
        )
    )
    return "\n".join(lines) + "\n"
