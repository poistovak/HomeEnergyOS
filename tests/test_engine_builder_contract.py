from heos.devtools import EngineBuilder


def test_engine_builder_creates_paths():

    builder = EngineBuilder()

    result = builder.create_engine(
        "adaptive_test"
    )

    assert len(result) == 2
    assert "adaptive_test.py" in str(result[0])
    assert "test_adaptive_test_contract.py" in str(result[1])