from heos.house_state import HouseState, PredictionWindow
from heos.intelligence import IntelligenceLayer, TrendDirection
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
    pv_w: float = 5000,
    house_w: float = 1200,
    grid_w: float = -3800,
    cloud_risk: float | None = 20,
    age_seconds: float = 5,
) -> HouseState:
    return HouseState(
        twin=DigitalTwin(
            power=PowerFlow(
                pv_w=pv_w,
                house_w=house_w,
                grid_w=grid_w,
                quality=SourceQuality(
                    confidence=0.98,
                    age_seconds=age_seconds,
                    source="test",
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
                    "pv": Availability.ONLINE,
                    "ev": Availability.ONLINE,
                    "charger": Availability.ONLINE,
                }
            ),
        ),
        predictions=PredictionWindow(
            expected_cloud_risk_percent=cloud_risk,
        ),
    )


def test_intelligence_layer_builds_decision_ready_result() -> None:
    result = IntelligenceLayer().analyze(
        make_state(),
        pv_history_w=(4200, 4500, 4800, 5000),
        house_history_w=(1150, 1180, 1200, 1200),
    )

    assert result.ready_for_decision is True
    assert result.pv_trend.direction is TrendDirection.RISING
    assert result.forecast.surplus_15m_w > 0


def test_cloud_risk_reduces_projected_pv() -> None:
    layer = IntelligenceLayer()

    clear = layer.analyze(make_state(cloud_risk=0))
    cloudy = layer.analyze(make_state(cloud_risk=90))

    assert cloudy.forecast.pv_15m_w < clear.forecast.pv_15m_w


def test_stale_data_blocks_decision_readiness() -> None:
    result = IntelligenceLayer().analyze(
        make_state(age_seconds=120)
    )

    assert result.ready_for_decision is False
    assert result.confidence.score < 0.80


def test_falling_pv_and_rising_load_raise_grid_risk() -> None:
    result = IntelligenceLayer().analyze(
        make_state(pv_w=2500, house_w=2200, grid_w=-300),
        pv_history_w=(5000, 4200, 3300, 2500),
        house_history_w=(1200, 1500, 1900, 2200),
    )

    assert result.pv_trend.direction is TrendDirection.FALLING
    assert result.house_trend.direction is TrendDirection.RISING
    assert result.forecast.grid_risk > 0
