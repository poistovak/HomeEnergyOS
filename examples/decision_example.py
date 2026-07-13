from heos.engine import recommend_ev_charging
from heos.state import HouseState

state = HouseState(
    pv_power_w=6800,
    house_power_w=1500,
    grid_power_w=-5300,
    ev_soc_percent=42,
    ev_connected=True,
)

decision = recommend_ev_charging(state)
print(decision.action)
print(decision.parameters)
print(decision.explain())
