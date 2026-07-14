"""Translate HEOS decisions into generic Home Assistant commands."""

from __future__ import annotations

from heos.brains.energy_models import EnergyAction, EnergyDecision

from .executor import HomeAssistantServiceCommand


def decision_to_command(
    decision: EnergyDecision,
    *,
    charger_switch_entity: str,
    charger_current_entity: str,
) -> tuple[HomeAssistantServiceCommand, ...]:
    """Translate a decision without executing it."""
    if decision.action is EnergyAction.HOLD:
        return ()

    if decision.action is EnergyAction.STOP_EV_CHARGING:
        return (
            HomeAssistantServiceCommand(
                domain="switch",
                service="turn_off",
                data={"entity_id": charger_switch_entity},
                reason=decision.explain(),
            ),
        )

    if decision.action is EnergyAction.CHARGE_EV:
        current_a = int(decision.parameters["current_a"])
        return (
            HomeAssistantServiceCommand(
                domain="number",
                service="set_value",
                data={
                    "entity_id": charger_current_entity,
                    "value": current_a,
                },
                reason=decision.explain(),
            ),
            HomeAssistantServiceCommand(
                domain="switch",
                service="turn_on",
                data={"entity_id": charger_switch_entity},
                reason=decision.explain(),
            ),
        )

    return ()
