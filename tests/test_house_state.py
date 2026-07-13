from heos.house_state import ControlMode, HouseState, SafetyConstraints, UserIntent
from heos.twin import Availability, ChargerState, DeviceHealth, DigitalTwin, EVState, PowerFlow, SourceQuality

def make_twin() -> DigitalTwin:
    return DigitalTwin(
        power=PowerFlow(
            pv_w=5000, house_w=1200, grid_w=-3800,
            quality=SourceQuality(confidence=0.95, age_seconds=10, source="home_assistant"),
        ),
        ev=EVState(soc_percent=42, connected=True, availability=Availability.ONLINE),
        charger=ChargerState(
            connected=True, charging=False, power_w=0,
            availability=Availability.ONLINE,
        ),
        health=DeviceHealth(states={
            "fronius": Availability.ONLINE,
            "wattpilot": Availability.ONLINE,
            "omoda": Availability.ONLINE,
        }),
    )

def test_house_state_is_ready() -> None:
    state = HouseState(twin=make_twin())
    assert state.decision_ready is True
    assert state.can_execute_automatically is False

def test_autopilot_requires_mode() -> None:
    state = HouseState(
        twin=make_twin(),
        intent=UserIntent(control_mode=ControlMode.AUTOPILOT),
        constraints=SafetyConstraints(main_breaker_a=25, phases=3),
    )
    assert state.can_execute_automatically is True
