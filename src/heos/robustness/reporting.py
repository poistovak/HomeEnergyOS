from __future__ import annotations

from .models import RobustnessRun


def render_report(run: RobustnessRun) -> str:
    certificate = run.certificate
    summary = certificate.summary
    status = "ROBUST" if certificate.robust else "NOT ROBUST"
    lines = [
        "HomeEnergyOS M23 - Robustness Envelope",
        "=" * 43,
        f"Result:                    {status}",
        f"Scenario:                  {certificate.scenario_id}",
        f"Baseline candidate:         {certificate.baseline_candidate_id}",
        f"Variants evaluated:         {summary.variant_count}",
        f"Feasible ratio:             {summary.feasible_ratio:.3f}",
        f"Selection stability:        {summary.selection_stability:.3f}",
        f"Worst regret:               {summary.worst_regret:.6f}",
        f"Worst objective score:      {summary.worst_objective_score:.6f}",
        f"Peak grid import:           {summary.peak_grid_import_kw:.3f} kW",
        f"Minimum final battery SOC:  {summary.minimum_final_battery_soc:.3f}",
        f"Minimum final EV SOC:       {summary.minimum_final_ev_soc:.3f}",
        f"Variants SHA-256:           {certificate.variants_digest}",
        f"Certificate SHA-256:        {certificate.certificate_digest}",
        "",
        "Policy verdict",
        "--------------",
    ]
    if certificate.reasons:
        lines.extend(f"[FAIL] {item}" for item in certificate.reasons)
    else:
        lines.append("[PASS] The selected strategy survived the bounded uncertainty envelope.")
    lines.extend(
        (
            "",
            "The envelope is deterministic and advisory. It sends no device commands and",
            "does not bypass the Operational Release Gate, Safety Engine, or Execution Runtime.",
        )
    )
    return "\n".join(lines) + "\n"
