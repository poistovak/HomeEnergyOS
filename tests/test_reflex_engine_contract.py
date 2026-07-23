from heos.reflex import ReflexEngine, ReflexRule


def test_reflex_engine_reacts():

    engine = ReflexEngine()

    result = []

    def optimize(event):
        result.append("optimized")

    engine.register(
        ReflexRule(
            event="surplus_detected",
            action=optimize,
        )
    )

    class Event:
        event = "surplus_detected"

    engine.process(Event())

    assert result == ["optimized"]