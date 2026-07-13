from heos.twin import (
    Availability,
    ChargerState,
    DeviceHealth,
    DigitalTwin,
    EVState,
    PowerFlow,
    SourceQuality,
)


def test_power_flow_calculates_export_and_self_sufficiency() -> None:
    power = PowerFlow(
        pv_w=5000,
        house_w=1200,
        grid_w=-3800,
    )

    assert power.grid_export_w == 3800
    assert power.grid_import_w == 0
    assert power.self_sufficiency_percent == 100.0


def test_digital_twin_reports_autopilot_readiness() -> None:
    twin = DigitalTwin(
        power=PowerFlow(
            pv_w=5000,
            house_w=1200,
            grid_w=-3800,
            quality=SourceQuality(
                confidence=0.95,
                age_seconds=10,
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
    )

    assert twin.usable_for_autopilot is True
    assert twin.summary()["health"] == "online"


def test_offline_device_blocks_autopilot() -> None:
    twin = DigitalTwin(
        power=PowerFlow(
            pv_w=5000,
            house_w=1200,
            grid_w=-3800,
            quality=SourceQuality(confidence=1.0, age_seconds=5),
        ),
        ev=EVState(soc_percent=42, connected=True),
        charger=ChargerState(
            connected=True,
            charging=False,
            power_w=0,
            availability=Availability.OFFLINE,
        ),
    )

    assert twin.usable_for_autopilot is False
