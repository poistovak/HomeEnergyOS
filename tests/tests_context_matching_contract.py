from heos.result_verification import (
    ContextMatcher,
)


def test_context_match_finds_history():

    matcher = ContextMatcher()

    result = matcher.match(
        "charge",
        [
            {
                "pv": 5000,
                "battery": 80,
            }
        ],
        {
            "pv": 5000,
            "battery": 80,
        },
    )

    assert result.decision == "charge"
    assert result.matches == 1