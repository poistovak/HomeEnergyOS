from heos.decision import Action
from heos.engine import recommend_ev_charging
from heos.state import HouseState


def test_engine_recommends_charging() -> None:
    state = HouseState(
        pv_power_w=5000,
        house_power_w=1200,
        grid_power_w=-3800,
        ev_soc_percent=42,
        ev_connected=True,
    )
    decision = recommend_ev_charging(state)
    assert decision.action is Action.CHARGE
    assert decision.parameters["current_a"] == 15
