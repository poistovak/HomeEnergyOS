from heos.house_state import HouseState, PredictionWindow
from heos.intelligence import IntelligenceLayer
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
            pv_w=6100,
            house_w=1400,
            grid_w=-4700,
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
    predictions=PredictionWindow(
        expected_cloud_risk_percent=70,
    ),
)

intelligence = IntelligenceLayer().analyze(
    state,
    pv_history_w=(6800, 6600, 6400, 6100),
    house_history_w=(1200, 1250, 1320, 1400),
)

print("PV trend:", intelligence.pv_trend.direction.value)
print("Projected PV:", round(intelligence.forecast.pv_15m_w), "W")
print("Projected surplus:", round(intelligence.forecast.surplus_15m_w), "W")
print("Confidence:", f"{intelligence.confidence.score:.0%}")
print("Ready:", intelligence.ready_for_decision)
