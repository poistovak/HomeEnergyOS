from heos.twin import (
    Availability,
    ChargerState,
    DeviceHealth,
    DigitalTwin,
    EVState,
    PowerFlow,
    SourceQuality,
)

twin = DigitalTwin(
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
        range_km=52,
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
            "daikin": Availability.ONLINE,
        }
    ),
)

print(twin.summary())
