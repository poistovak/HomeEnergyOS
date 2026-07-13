"""First deterministic HEOS decision engine."""

from __future__ import annotations

from datetime import timedelta

from .decision import Action, Decision, DecisionReason
from .state import HouseState


def recommend_ev_charging(
    state: HouseState,
    *,
    target_soc_percent: float = 80.0,
    voltage_v: float = 230.0,
    min_current_a: int = 6,
    max_current_a: int = 16,
    reserve_w: float = 250.0,
) -> Decision:
    if state.ev_soc_percent is None:
        return Decision(
            Action.WAIT,
            0.45,
            (DecisionReason("missing_ev_soc", "EV state of charge is unavailable."),),
        )

    if state.ev_soc_percent >= target_soc_percent:
        return Decision(
            Action.STOP,
            0.99,
            (DecisionReason("target_soc_reached", "EV target state of charge is reached."),),
        )

    if state.ev_connected is False:
        return Decision(
            Action.WAIT,
            0.98,
            (DecisionReason("ev_disconnected", "The EV is not connected."),),
        )

    available_w = state.grid_export_w + (state.ev_charging_power_w or 0.0) - reserve_w
    raw_current_a = int(max(available_w, 0.0) / voltage_v)

    if raw_current_a < min_current_a:
        return Decision(
            Action.WAIT,
            0.85,
            (DecisionReason("insufficient_surplus", f"Available surplus is {max(available_w, 0.0):.0f} W."),),
            valid_for=timedelta(seconds=30),
        )

    current_a = min(raw_current_a, max_current_a)
    return Decision(
        Action.CHARGE,
        0.94,
        (
            DecisionReason("pv_surplus_available", f"Solar surplus supports {current_a} A."),
            DecisionReason("ev_soc_below_target", "EV state of charge is below target."),
        ),
        parameters={"current_a": current_a},
        valid_for=timedelta(seconds=45),
    )
