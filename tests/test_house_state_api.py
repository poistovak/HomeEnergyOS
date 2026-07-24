from heos import house_state

EXPECTED_EXPORTS = {
    "ControlMode",
    "HouseState",
    "Objective",
    "OperatingPolicy",
    "PredictionWindow",
    "SafetyConstraints",
    "UserIntent",
}


def test_public_api_exports():
    assert set(house_state.__all__) == EXPECTED_EXPORTS


def test_public_api_contains_all_exports():
    for name in house_state.__all__:
        assert hasattr(house_state, name)


def test_all_exports_are_unique():
    assert len(house_state.__all__) == len(set(house_state.__all__))


def test_export_count():
    assert len(house_state.__all__) == 7


def test_expected_names_are_strings():
    assert all(isinstance(name, str) for name in house_state.__all__)