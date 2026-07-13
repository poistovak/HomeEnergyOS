"""Built-in EV charging brain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from ..brain import BaseBrain, BrainMetadata
from ..decision import Action, Decision, DecisionReason
from ..state import HouseState


@dataclass(frozen=True, slots=True)
class EVChargingPolicy:
    """User policy for one-phase solar EV charging."""

    target_soc_percent: float = 80.0
    voltage_v: float = 230.0
    minimum_current_a: int = 6
    maximum_current_a: int = 16
    grid_reserve_w: float = 250.0

    def __post_init__(self) -> None:
        if not 0 < self.target_soc_percent <= 100:
            raise ValueError("target_soc_percent must be between 0 and 100")
        if self.minimum_current_a < 1:
            raise ValueError("minimum_current_a must be positive")
        if self.maximum_current_a < self.minimum_current_a:
            raise ValueError("maximum_current_a must be >= minimum_current_a")
        if self.voltage_v <= 0:
            raise ValueError("voltage_v must be positive")
        if self.grid_reserve_w < 0:
            raise ValueError("grid_reserve_w must not be negative")


class EVChargingBrain(BaseBrain):
    """Propose explainable EV charging decisions."""

    metadata = BrainMetadata(
        brain_id="ev_charging",
        name="EV Charging Brain",
        version="0.2.0",
        description="Optimizes one-phase EV charging from available solar surplus.",
    )

    def __init__(self, policy: EVChargingPolicy | None = None) -> None:
        self._policy = policy or EVChargingPolicy()

    def propose(self, state: HouseState) -> tuple[Decision, ...]:
        policy = self._policy

        if state.ev_soc_percent is None:
            return (
                Decision(
                    action=Action.WAIT,
                    confidence=0.45,
                    reasons=(
                        DecisionReason(
                            code="missing_ev_soc",
                            message="EV state of charge is unavailable.",
                        ),
                    ),
                ),
            )

        if state.ev_soc_percent >= policy.target_soc_percent:
            return (
                Decision(
                    action=Action.STOP,
                    confidence=0.99,
                    reasons=(
                        DecisionReason(
                            code="target_soc_reached",
                            message=(
                                f"EV state of charge reached "
                                f"{state.ev_soc_percent:.0f} percent."
                            ),
                        ),
                    ),
                ),
            )

        if state.ev_connected is False:
            return (
                Decision(
                    action=Action.WAIT,
                    confidence=0.98,
                    reasons=(
                        DecisionReason(
                            code="ev_disconnected",
                            message="The EV is not connected.",
                        ),
                    ),
                ),
            )

        available_w = (
            state.grid_export_w
            + (state.ev_charging_power_w or 0.0)
            - policy.grid_reserve_w
        )
        raw_current_a = int(max(available_w, 0.0) / policy.voltage_v)

        if raw_current_a < policy.minimum_current_a:
            threshold_w = (
                policy.minimum_current_a * policy.voltage_v
                + policy.grid_reserve_w
            )
            return (
                Decision(
                    action=Action.WAIT,
                    confidence=0.88,
                    reasons=(
                        DecisionReason(
                            code="insufficient_surplus",
                            message=(
                                f"Available surplus is {max(available_w, 0.0):.0f} W; "
                                f"stable charging needs about {threshold_w:.0f} W."
                            ),
                        ),
                    ),
                    parameters={
                        "available_power_w": max(available_w, 0.0),
                        "required_power_w": threshold_w,
                    },
                    valid_for=timedelta(seconds=30),
                ),
            )

        current_a = min(raw_current_a, policy.maximum_current_a)
        return (
            Decision(
                action=Action.CHARGE,
                confidence=0.95,
                reasons=(
                    DecisionReason(
                        code="pv_surplus_available",
                        message=f"Solar surplus supports {current_a} A charging.",
                    ),
                    DecisionReason(
                        code="ev_soc_below_target",
                        message=(
                            f"EV state of charge is below the "
                            f"{policy.target_soc_percent:.0f} percent target."
                        ),
                    ),
                ),
                parameters={
                    "current_a": current_a,
                    "available_power_w": max(available_w, 0.0),
                },
                valid_for=timedelta(seconds=45),
            ),
        )
