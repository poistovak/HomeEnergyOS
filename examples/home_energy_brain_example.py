from heos.brains.home_energy_brain import HomeEnergyBrain
from heos.house_state import HouseState, PredictionWindow, SafetyConstraints
from heos.twin import (
    Availability,
    ChargerState,
    DeviceHealth,
    DigitalTwin,
    EVState,
    PowerFlow,
    SourceQuality,
)

state = HouseState(
    twin=DigitalTwin(
        power=PowerFlow(
            pv_w=6800,
            house_w=1500,
            grid_w=-5300,
            quality=SourceQuality(
                confidence=0.98,
                age_seconds=4,
                source="home_assistant",
            ),
        ),
        ev=EVState(
            soc_percent=42,
            connected=True,
            availability=Availability.ONLINE,
        ),
        charger=ChargerState(
            connected=True,
            charging=False,
            power_w=0,
            maximum_current_a=16,
            phases=1,
            availability=Availability.ONLINE,
        ),
        health=DeviceHealth(
            states={
                "fronius": Availability.ONLINE,
                "wattpilot": Availability.ONLINE,
                "omoda": Availability.ONLINE,
            }
        ),
    ),
    constraints=SafetyConstraints(
        main_breaker_a=25,
        phases=3,
        minimum_ev_current_a=6,
        maximum_ev_current_a=16,
    ),
    predictions=PredictionWindow(
        expected_cloud_risk_percent=80,
    ),
)

decision = HomeEnergyBrain().decide(state)

print(decision.explain())
print(decision.parameters)
