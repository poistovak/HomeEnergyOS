from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from heos.digital_twin import TwinControl, trace_from_dict, trace_to_dict

from .models import (
    StrategyCandidate,
    StrategyDecision,
    StrategyEvaluation,
    StrategyMetrics,
    StrategyObjective,
)


def _control_to_dict(control: TwinControl) -> dict[str, float]:
    return {
        "hvac_thermal_kw": control.hvac_thermal_kw,
        "battery_power_kw": control.battery_power_kw,
        "ev_charge_kw": control.ev_charge_kw,
        "pv_curtailment_kw": control.pv_curtailment_kw,
    }


def _candidate_to_dict(candidate: StrategyCandidate) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "name": candidate.name,
        "controls": [_control_to_dict(item) for item in candidate.controls],
        "objective": candidate.objective.value,
        "tags": list(candidate.tags),
    }


def _candidate_from_dict(data: Mapping[str, Any]) -> StrategyCandidate:
    raw_controls = data["controls"]
    if not isinstance(raw_controls, list):
        raise ValueError("controls must be a list")
    controls = tuple(
        TwinControl(**{key: float(value) for key, value in dict(item).items()})
        for item in raw_controls
    )
    return StrategyCandidate(
        candidate_id=str(data["candidate_id"]),
        name=str(data["name"]),
        controls=controls,
        objective=StrategyObjective(str(data["objective"])),
        tags=tuple(str(item) for item in data.get("tags", [])),
    )


def _evaluation_to_dict(evaluation: StrategyEvaluation) -> dict[str, Any]:
    metrics = {
        name: getattr(evaluation.metrics, name)
        for name in evaluation.metrics.__dataclass_fields__
    }
    return {
        "candidate": _candidate_to_dict(evaluation.candidate),
        "trace": trace_to_dict(evaluation.trace),
        "metrics": metrics,
        "feasible": evaluation.feasible,
        "rank": evaluation.rank,
        "explanation": evaluation.explanation,
    }


def _evaluation_from_dict(data: Mapping[str, Any]) -> StrategyEvaluation:
    return StrategyEvaluation(
        candidate=_candidate_from_dict(data["candidate"]),
        trace=trace_from_dict(data["trace"]),
        metrics=StrategyMetrics(**dict(data["metrics"])),
        feasible=bool(data["feasible"]),
        rank=int(data["rank"]),
        explanation=str(data["explanation"]),
    )


def decision_to_dict(decision: StrategyDecision) -> dict[str, Any]:
    return {
        "decision_id": decision.decision_id,
        "generated_at": decision.generated_at.isoformat(),
        "selected_candidate_id": decision.selected.candidate.candidate_id,
        "alternatives": [_evaluation_to_dict(item) for item in decision.alternatives],
        "policy_version": decision.policy_version,
        "parameter_version": decision.parameter_version,
        "explanation": decision.explanation,
    }


def decision_from_dict(data: Mapping[str, Any]) -> StrategyDecision:
    raw_alternatives = data["alternatives"]
    if not isinstance(raw_alternatives, list):
        raise ValueError("alternatives must be a list")
    alternatives = tuple(_evaluation_from_dict(item) for item in raw_alternatives)
    selected_id = str(data["selected_candidate_id"])
    try:
        selected = next(item for item in alternatives if item.candidate.candidate_id == selected_id)
    except StopIteration as exc:
        raise ValueError("selected candidate is not present in alternatives") from exc
    return StrategyDecision(
        decision_id=str(data["decision_id"]),
        generated_at=datetime.fromisoformat(str(data["generated_at"])),
        selected=selected,
        alternatives=alternatives,
        policy_version=str(data["policy_version"]),
        parameter_version=str(data["parameter_version"]),
        explanation=str(data["explanation"]),
    )


def dumps_decision(decision: StrategyDecision) -> str:
    return json.dumps(decision_to_dict(decision), sort_keys=True, separators=(",", ":"))


def loads_decision(payload: str) -> StrategyDecision:
    data = json.loads(payload)
    if not isinstance(data, Mapping):
        raise ValueError("strategy JSON must contain an object")
    return decision_from_dict(data)
