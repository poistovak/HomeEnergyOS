from heos.state import HouseState


def test_legacy_house_state_converts_to_digital_twin() -> None:
    state = HouseState(
        pv_power_w=5000,
        house_power_w=1200,
        grid_power_w=-3800,
        ev_soc_percent=42,
        ev_connected=True,
        ev_charging_power_w=0,
    )

    twin = state.to_digital_twin()

    assert twin.power.grid_export_w == 3800
    assert twin.ev.soc_percent == 42
    assert twin.charger.connected is True
