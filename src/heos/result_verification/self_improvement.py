from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImprovementProposal:
    area: str
    expected_gain: float


class SelfImprovementEngine:

    def propose(
        self,
        area: str,
        expected_gain: float,
    ) -> ImprovementProposal:

        if not area.strip():
            raise ValueError(
                "area must not be empty"
            )

        if not 0 <= expected_gain <= 1:
            raise ValueError(
                "expected_gain must be between 0 and 1"
            )

        return ImprovementProposal(
            area=area,
            expected_gain=expected_gain,
        )