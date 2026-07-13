from heos.house_state import HouseState, SafetyConstraints, UserIntent
from heos.twin import ChargerState, DigitalTwin, EVState, PowerFlow

state = HouseState(
    twin=DigitalTwin(
        power=PowerFlow(pv_w=6800, house_w=1500, grid_w=-5300),
        ev=EVState(soc_percent=42, connected=True),
        charger=ChargerState(connected=True, charging=False, power_w=0),
    ),
    intent=UserIntent(ev_target_soc_percent=80),
    constraints=SafetyConstraints(main_breaker_a=25, phases=3),
)

print(state.summary())
