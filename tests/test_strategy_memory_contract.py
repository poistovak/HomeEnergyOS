from heos.result_verification import (
    StrategyMemoryEngine,
)


def test_strategy_memory_stores_success():

    engine = StrategyMemoryEngine()

    result = engine.remember(
        "maximize_self_consumption",
        0.95,
    )

    assert result.strategy == "maximize_self_consumption"
    assert result.success_rate == 0.95