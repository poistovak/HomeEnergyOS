from heos.brains.ev_charging import EVChargingBrain
from heos.decision import Action
from heos.orchestrator import BrainOrchestrator, BrainRegistration
from heos.state import HouseState


def test_orchestrator_returns_selected_decision() -> None:
    orchestrator = BrainOrchestrator(
        registrations=(
            BrainRegistration(
                brain=EVChargingBrain(),
                priority=80,
                utility=0.5,
            ),
        ),
    )
    state = HouseState(
        pv_power_w=5000,
        house_power_w=1200,
        grid_power_w=-3800,
        ev_soc_percent=42,
        ev_connected=True,
    )

    result = orchestrator.evaluate(state)

    assert result.decision is not None
    assert result.decision.action is Action.CHARGE
