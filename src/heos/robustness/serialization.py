from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from .models import (
    Perturbation,
    RobustnessCertificate,
    RobustnessRun,
    RobustnessSummary,
    VariantEvaluation,
)


def run_to_dict(run: RobustnessRun) -> dict[str, Any]:
    return run.to_dict()


def _summary_from_dict(data: Mapping[str, Any]) -> RobustnessSummary:
    return RobustnessSummary(
        variant_count=int(data["variant_count"]),
        feasible_ratio=float(data["feasible_ratio"]),
        selection_stability=float(data["selection_stability"]),
        worst_regret=float(data["worst_regret"]),
        worst_objective_score=float(data["worst_objective_score"]),
        peak_grid_import_kw=float(data["peak_grid_import_kw"]),
        minimum_final_battery_soc=float(data["minimum_final_battery_soc"]),
        minimum_final_ev_soc=float(data["minimum_final_ev_soc"]),
    )


def _variant_from_dict(data: Mapping[str, Any]) -> VariantEvaluation:
    raw = data["perturbation"]
    if not isinstance(raw, Mapping):
        raise ValueError("perturbation must be an object")
    return VariantEvaluation(
        variant_id=str(data["variant_id"]),
        perturbation=Perturbation(
            pv_multiplier=float(raw["pv_multiplier"]),
            load_multiplier=float(raw["load_multiplier"]),
            outdoor_temp_delta_c=float(raw["outdoor_temp_delta_c"]),
            tariff_multiplier=float(raw["tariff_multiplier"]),
        ),
        baseline_candidate_id=str(data["baseline_candidate_id"]),
        selected_candidate_id=str(data["selected_candidate_id"]),
        baseline_feasible=bool(data["baseline_feasible"]),
        selected_feasible=bool(data["selected_feasible"]),
        selection_stable=bool(data["selection_stable"]),
        baseline_score=float(data["baseline_score"]),
        best_score=float(data["best_score"]),
        regret=float(data["regret"]),
        peak_grid_import_kw=float(data["peak_grid_import_kw"]),
        final_battery_soc=float(data["final_battery_soc"]),
        final_ev_soc=float(data["final_ev_soc"]),
        trace_id=str(data["trace_id"]),
    )


def run_from_dict(data: Mapping[str, Any]) -> RobustnessRun:
    raw_certificate = data["certificate"]
    raw_variants = data["variants"]
    if not isinstance(raw_certificate, Mapping):
        raise ValueError("certificate must be an object")
    if not isinstance(raw_variants, list):
        raise ValueError("variants must be a list")
    raw_metadata = raw_certificate.get("metadata", {})
    if not isinstance(raw_metadata, Mapping):
        raise ValueError("metadata must be an object")
    certificate = RobustnessCertificate(
        certificate_id=str(raw_certificate["certificate_id"]),
        generated_at=datetime.fromisoformat(str(raw_certificate["generated_at"])),
        scenario_id=str(raw_certificate["scenario_id"]),
        baseline_decision_id=str(raw_certificate["baseline_decision_id"]),
        baseline_candidate_id=str(raw_certificate["baseline_candidate_id"]),
        strategy_policy_version=str(raw_certificate["strategy_policy_version"]),
        parameter_version=str(raw_certificate["parameter_version"]),
        robustness_policy_version=str(raw_certificate["robustness_policy_version"]),
        robust=bool(raw_certificate["robust"]),
        reasons=tuple(str(item) for item in raw_certificate["reasons"]),
        summary=_summary_from_dict(raw_certificate["summary"]),
        variants_digest=str(raw_certificate["variants_digest"]),
        certificate_digest=str(raw_certificate["certificate_digest"]),
        metadata={str(key): str(value) for key, value in raw_metadata.items()},
    )
    return RobustnessRun(
        certificate=certificate,
        variants=tuple(_variant_from_dict(item) for item in raw_variants),
    )


def dumps_run(run: RobustnessRun, *, indent: int | None = None) -> str:
    return json.dumps(run_to_dict(run), sort_keys=True, separators=(",", ":"), indent=indent)


def loads_run(payload: str) -> RobustnessRun:
    data = json.loads(payload)
    if not isinstance(data, Mapping):
        raise ValueError("robustness JSON must contain an object")
    return run_from_dict(data)
