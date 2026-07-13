from heos.brains.ev_charging import EVChargingBrain
from heos.decision import Action
from heos.state import HouseState


def test_ev_brain_proposes_charge_from_surplus() -> None:
    state = HouseState(
        pv_power_w=5000,
        house_power_w=1200,
        grid_power_w=-3800,
        ev_soc_percent=42,
        ev_connected=True,
        ev_charging_power_w=0,
    )

    decision = EVChargingBrain().propose(state)[0]

    assert decision.action is Action.CHARGE
    assert decision.parameters["current_a"] == 15


def test_ev_brain_waits_below_six_amp_threshold() -> None:
    state = HouseState(
        pv_power_w=1700,
        house_power_w=700,
        grid_power_w=-1000,
        ev_soc_percent=42,
        ev_connected=True,
        ev_charging_power_w=0,
    )

    decision = EVChargingBrain().propose(state)[0]

    assert decision.action is Action.WAIT
    assert decision.parameters["required_power_w"] == 1630
