import pytest

from datetime import UTC, datetime, timedelta

from heos.digital_twin import (
    TwinControl,
    TwinDisturbance,
    TwinState,
)

from heos.strategy.models import (
    ComfortBand,
    StrategyCandidate,
    StrategyEvaluation,
    StrategyMetrics,
    StrategyPolicy,
    StrategyRequest,
    TariffStep,
)


# ==============================
# TariffStep
# ==============================


def test_tariff_step_accepts_valid_values():
    tariff = TariffStep(
        import_price_per_kwh=0.20,
        export_price_per_kwh=0.05,
    )

    assert tariff.import_price_per_kwh == 0.20


@pytest.mark.parametrize(
    "value",
    [-1.0, float("inf"), float("-inf"), float("nan")],
)
def test_tariff_step_rejects_invalid_prices(value):
    with pytest.raises(ValueError):
        TariffStep(import_price_per_kwh=value)


# ==============================
# ComfortBand
# ==============================


def test_comfort_band_midpoint():
    band = ComfortBand(
        minimum_c=20.0,
        maximum_c=24.0,
    )

    assert band.midpoint_c == 22.0


def test_comfort_band_requires_valid_range():
    with pytest.raises(ValueError):
        ComfortBand(
            minimum_c=24.0,
            maximum_c=20.0,
        )


# ==============================
# StrategyCandidate
# ==============================


def make_candidate():
    return StrategyCandidate(
        candidate_id="cand-001",
        name="Solar First",
        controls=(TwinControl(),),
    )


def test_strategy_candidate_accepts_valid_values():
    candidate = make_candidate()

    assert candidate.candidate_id == "cand-001"


def test_strategy_candidate_rejects_empty_id():
    with pytest.raises(ValueError):
        StrategyCandidate(
            candidate_id="",
            name="Solar",
            controls=(TwinControl(),),
        )


def test_strategy_candidate_normalizes_tags():
    candidate = StrategyCandidate(
        candidate_id="001",
        name="Solar",
        controls=(TwinControl(),),
        tags=("solar", "battery", "solar"),
    )

    assert candidate.tags == ("battery", "solar")


# ==============================
# StrategyRequest
# ==============================


def make_request():
    state = TwinState(
        observed_at=datetime.now(UTC),
        indoor_temp_c=22.0,
        battery_soc=0.5,
    )

    return StrategyRequest(
        initial_state=state,
        disturbances=(
            TwinDisturbance(
                outdoor_temp_c=20.0,
                pv_kw=5.0,
                base_load_kw=1.0,
            ),
        ),
        tariffs=(
            TariffStep(
                import_price_per_kwh=0.20,
            ),
        ),
        comfort_bands=(
            ComfortBand(
                minimum_c=20.0,
                maximum_c=24.0,
            ),
        ),
        step_duration=timedelta(hours=1),
        generated_at=datetime.now(UTC),
    )


def test_strategy_request_horizon():
    assert make_request().horizon == 1


def test_strategy_request_expands_tariff():
    assert len(make_request().expanded_tariffs) == 1


# ==============================
# StrategyPolicy
# ==============================


def test_strategy_policy_defaults():
    policy = StrategyPolicy()

    assert policy.energy_cost_weight == 1.0


def test_strategy_policy_rejects_negative_weight():
    with pytest.raises(ValueError):
        StrategyPolicy(
            energy_cost_weight=-1.0,
        )


def test_strategy_policy_rejects_invalid_soc():
    with pytest.raises(ValueError):
        StrategyPolicy(
            target_ev_soc=2.0,
        )


# ==============================
# StrategyMetrics
# ==============================


def make_metrics():
    return StrategyMetrics(
        total_grid_import_kwh=10.0,
        total_grid_export_kwh=2.0,
        net_energy_cost=1.5,
        peak_grid_import_kw=3.0,
        battery_throughput_kwh=5.0,
        comfort_deviation_degree_hours=0.0,
        ev_shortfall=0.0,
        battery_reserve_shortfall=0.0,
        violation_count=0,
        violation_magnitude=0.0,
        objective_score=0.95,
    )


def test_strategy_metrics_accepts_values():
    metrics = make_metrics()

    assert metrics.objective_score == 0.95


def test_strategy_metrics_rejects_negative_energy():
    with pytest.raises(ValueError):
        StrategyMetrics(
            total_grid_import_kwh=-1.0,
            total_grid_export_kwh=0.0,
            net_energy_cost=0.0,
            peak_grid_import_kw=0.0,
            battery_throughput_kwh=0.0,
            comfort_deviation_degree_hours=0.0,
            ev_shortfall=0.0,
            battery_reserve_shortfall=0.0,
            violation_count=0,
            violation_magnitude=0.0,
            objective_score=1.0,
        )


def test_strategy_metrics_rejects_invalid_score():
    with pytest.raises(ValueError):
        StrategyMetrics(
            total_grid_import_kwh=0.0,
            total_grid_export_kwh=0.0,
            net_energy_cost=0.0,
            peak_grid_import_kw=0.0,
            battery_throughput_kwh=0.0,
            comfort_deviation_degree_hours=0.0,
            ev_shortfall=0.0,
            battery_reserve_shortfall=0.0,
            violation_count=0,
            violation_magnitude=0.0,
            objective_score=float("nan"),
        )


# ==============================
# StrategyEvaluation
# ==============================
def make_trace():
    return None

def test_strategy_evaluation_accepts_valid_values():
    evaluation = StrategyEvaluation(
        candidate=make_candidate(),
        trace=make_trace(),
        metrics=make_metrics(),
        feasible=True,
        rank=1,
        explanation="best strategy",
    )

    assert evaluation.rank == 1
    assert evaluation.feasible is True


def test_strategy_evaluation_rejects_invalid_rank():
    with pytest.raises(ValueError):
        StrategyEvaluation(
            candidate=make_candidate(),
            trace=make_trace(),
            metrics=make_metrics(),
            feasible=True,
            rank=0,
            explanation="bad",
        )


def test_strategy_evaluation_rejects_empty_explanation():
    with pytest.raises(ValueError):
        StrategyEvaluation(
            candidate=make_candidate(),
            trace=make_trace(),
            metrics=make_metrics(),
            feasible=True,
            rank=1,
            explanation="",
        )