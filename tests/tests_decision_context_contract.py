from heos.result_verification import (
    DecisionContext,
    DecisionContextMemory,
)


def test_context_memory_stores_context():

    memory = DecisionContextMemory()

    memory.add(
        DecisionContext(
            decision="charge",
            context={
                "pv_power": 5000,
                "battery": 80,
            },
        )
    )

    result = memory.all()

    assert len(result) == 1
    assert result[0].decision == "charge"
    assert result[0].context["pv_power"] == 5000