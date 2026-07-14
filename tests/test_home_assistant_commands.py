from heos.brains.energy_models import (
    DecisionReason,
    EnergyAction,
    EnergyDecision,
)
from heos.infrastructure.home_assistant.commands import (
    decision_to_command,
)


def test_charge_decision_translates_to_current_then_start() -> None:
    decision = EnergyDecision(
        action=EnergyAction.CHARGE_EV,
        confidence=0.95,
        score=90,
        reasons=(
            DecisionReason(
                code="surplus",
                message="Solar surplus available.",
                weight=1.0,
            ),
        ),
        parameters={"current_a": 12},
    )

    commands = decision_to_command(
        decision,
        charger_switch_entity="switch.wattpilot_charging",
        charger_current_entity="number.wattpilot_current",
    )

    assert len(commands) == 2
    assert commands[0].service == "set_value"
    assert commands[0].data["value"] == 12
    assert commands[1].service == "turn_on"


def test_hold_decision_creates_no_command() -> None:
    decision = EnergyDecision(
        action=EnergyAction.HOLD,
        confidence=0.99,
        score=100,
        reasons=(),
    )

    commands = decision_to_command(
        decision,
        charger_switch_entity="switch.wattpilot_charging",
        charger_current_entity="number.wattpilot_current",
    )

    assert commands == ()
