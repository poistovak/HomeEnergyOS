from heos.brains.energy_models import EnergyAction
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


def make_state(
    *,
    grid_w: float,
    soc: float | None = 42.0,
    connected: bool = True,
    charging_power_w: float = 0.0,
    cloud_risk: float | None = None,
) -> HouseState:
    twin = DigitalTwin(
        power=PowerFlow(
            pv_w=5000.0,
            house_w=1200.0,
            grid_w=grid_w,
            ev_w=charging_power_w,
            quality=SourceQuality(
                confidence=0.98,
                age_seconds=5.0,
                source="test",
            ),
        ),
        ev=EVState(
            soc_percent=soc,
            connected=connected,
            charging_power_w=charging_power_w,
            availability=Availability.ONLINE,
        ),
        charger=ChargerState(
            connected=connected,
            charging=charging_power_w > 0,
            power_w=charging_power_w,
            maximum_current_a=16,
            phases=1,
            availability=Availability.ONLINE,
        ),
        health=DeviceHealth(
            states={
                "pv": Availability.ONLINE,
                "charger": Availability.ONLINE,
                "vehicle": Availability.ONLINE,
            }
        ),
    )
    return HouseState(
        twin=twin,
        constraints=SafetyConstraints(
            main_breaker_a=25,
            phases=3,
            minimum_ev_current_a=6,
            maximum_ev_current_a=16,
        ),
        predictions=PredictionWindow(
            expected_cloud_risk_percent=cloud_risk
        ),
    )


def test_brain_charges_ev_from_solar_surplus() -> None:
    decision = HomeEnergyBrain().decide(
        make_state(grid_w=-3800.0)
    )

    assert decision.action is EnergyAction.CHARGE_EV
    assert decision.parameters["current_a"] == 15
    assert decision.confidence >= 0.95


def test_brain_holds_when_surplus_is_too_small() -> None:
    decision = HomeEnergyBrain().decide(
        make_state(grid_w=-1000.0)
    )

    assert decision.action is EnergyAction.HOLD
    assert decision.parameters["required_power_w"] == 1380.0


def test_brain_stops_charging_when_grid_import_is_detected() -> None:
    decision = HomeEnergyBrain().decide(
        make_state(
            grid_w=900.0,
            charging_power_w=2300.0,
        )
    )

    assert decision.action is EnergyAction.STOP_EV_CHARGING
    assert decision.parameters["grid_import_w"] == 900.0


def test_brain_stops_at_target_soc() -> None:
    decision = HomeEnergyBrain().decide(
        make_state(grid_w=-4000.0, soc=82.0)
    )

    assert decision.action is EnergyAction.STOP_EV_CHARGING


def test_high_cloud_risk_strengthens_charge_decision() -> None:
    decision = HomeEnergyBrain().decide(
        make_state(grid_w=-3800.0, cloud_risk=85.0)
    )

    assert decision.action is EnergyAction.CHARGE_EV
    assert decision.confidence == 0.97
    assert any(
        reason.code == "high_cloud_risk"
        for reason in decision.reasons
    )
