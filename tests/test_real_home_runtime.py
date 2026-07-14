from datetime import UTC, datetime

from heos.applications.real_home.health import SnapshotHealthChecker
from heos.infrastructure.home_assistant.models import RawEnergySnapshot


def test_snapshot_health_accepts_valid_real_home_data() -> None:
    snapshot = RawEnergySnapshot(
        pv_power_w=5200,
        house_power_w=1400,
        grid_power_w=-3800,
        ev_soc_percent=42,
        ev_connected=True,
        charger_power_w=0,
        charger_current_a=0,
        charger_enabled=False,
        outdoor_temperature_c=24,
        electricity_price_eur_kwh=None,
        collected_at=datetime.now(UTC),
        source_entities={},
    )

    health = SnapshotHealthChecker().evaluate(snapshot)

    assert health.healthy is True


def test_snapshot_health_rejects_invalid_soc() -> None:
    snapshot = RawEnergySnapshot(
        pv_power_w=5200,
        house_power_w=1400,
        grid_power_w=-3800,
        ev_soc_percent=142,
        ev_connected=True,
        charger_power_w=0,
        charger_current_a=0,
        charger_enabled=False,
        outdoor_temperature_c=24,
        electricity_price_eur_kwh=None,
        collected_at=datetime.now(UTC),
        source_entities={},
    )

    health = SnapshotHealthChecker().evaluate(snapshot)

    assert health.healthy is False
    assert any("SOC" in reason for reason in health.reasons)
