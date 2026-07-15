from __future__ import annotations

from dataclasses import fields, is_dataclass
from math import isfinite
from typing import Any


def selected_evaluation(decision: Any) -> Any:
    return getattr(decision, "selected")


def selected_candidate(decision: Any) -> Any:
    return getattr(selected_evaluation(decision), "candidate")


def selected_metrics(decision: Any) -> Any:
    return getattr(selected_evaluation(decision), "metrics")


def decision_shape_errors(decision: Any, minimum_alternatives: int) -> tuple[str, ...]:
    errors: list[str] = []
    for name in (
        "decision_id",
        "generated_at",
        "selected",
        "alternatives",
        "policy_version",
        "parameter_version",
    ):
        if not hasattr(decision, name):
            errors.append(f"missing {name}")

    if errors:
        return tuple(errors)

    alternatives = tuple(getattr(decision, "alternatives"))
    if len(alternatives) < minimum_alternatives:
        errors.append(
            f"requires at least {minimum_alternatives} alternatives; got {len(alternatives)}"
        )

    selected = getattr(decision, "selected")
    if not hasattr(selected, "candidate"):
        errors.append("selected evaluation is missing candidate")
    if not hasattr(selected, "metrics"):
        errors.append("selected evaluation is missing metrics")
    if not hasattr(selected, "feasible"):
        errors.append("selected evaluation is missing feasible")

    if hasattr(selected, "candidate"):
        candidate = getattr(selected, "candidate")
        for name in ("candidate_id", "controls", "objective"):
            if not hasattr(candidate, name):
                errors.append(f"selected candidate is missing {name}")
        if hasattr(candidate, "controls") and not tuple(getattr(candidate, "controls")):
            errors.append("selected candidate controls must not be empty")

    if hasattr(selected, "metrics"):
        metrics = getattr(selected, "metrics")
        for name in ("objective_score", "violation_count", "violation_magnitude"):
            if not hasattr(metrics, name):
                errors.append(f"selected metrics are missing {name}")

    return tuple(errors)


def objective_value(decision: Any) -> str:
    objective = getattr(selected_candidate(decision), "objective")
    return str(getattr(objective, "value", objective))


def control_payload(control: Any) -> tuple[tuple[str, float], ...]:
    values: list[tuple[str, float]] = []

    if is_dataclass(control):
        names = [item.name for item in fields(control)]
    elif hasattr(control, "__dict__"):
        names = list(vars(control))
    else:
        names = [
            name
            for name in dir(control)
            if not name.startswith("_") and not callable(getattr(control, name))
        ]

    for name in names:
        value = getattr(control, name)
        if isinstance(value, bool):
            values.append((name, float(value)))
        elif isinstance(value, (int, float)):
            number = float(value)
            if not isfinite(number):
                raise ValueError(f"control field {name} must be finite")
            values.append((name, number))

    if not values:
        raise ValueError("control does not expose numeric fields")

    return tuple(sorted(values))
