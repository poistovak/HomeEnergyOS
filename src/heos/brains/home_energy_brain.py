"""First real whole-home decision brain for HEOS.

The brain is deterministic and side-effect free:
HouseState -> EnergyDecision

It never calls Home Assistant, MQTT, Fronius or Wattpilot.
"""

from __future__ import annotations

from dataclasses import dataclass

from heos.house_state import HouseState

from .energy_models import DecisionReason, EnergyAction, EnergyDecision


@dataclass(frozen=True, slots=True)
class EnergyBrainPolicy:
    """Decision thresholds for one-phase EV charging."""

    voltage_v: float = 230.0
    minimum_ev_current_a: int = 6
    maximum_ev_current_a: int = 16
    reserve_power_w: float = 250.0
    target_soc_percent: float = 80.0

    def __post_init__(self) -> None:
        if self.voltage_v <= 0:
            raise ValueError("voltage_v must be positive")
        if self.minimum_ev_current_a <= 0:
            raise ValueError("minimum_ev_current_a must be positive")
        if self.maximum_ev_current_a < self.minimum_ev_current_a:
            raise ValueError(
                "maximum_ev_current_a must be >= minimum_ev_current_a"
            )
        if self.reserve_power_w < 0:
            raise ValueError("reserve_power_w must not be negative")
        if not 0.0 < self.target_soc_percent <= 100.0:
            raise ValueError("target_soc_percent must be between 0 and 100")


class HomeEnergyBrain:
    """Select the best immediate energy decision for the whole home."""

    brain_id = "home_energy"
    version = "0.6.0"

    def __init__(self, policy: EnergyBrainPolicy | None = None) -> None:
        self._policy = policy or EnergyBrainPolicy()

    def decide(self, state: HouseState) -> EnergyDecision:
        """Return one deterministic and explainable decision."""
        if not state.decision_ready:
            return self._hold_for_untrusted_state(state)

        twin = state.twin
        ev = twin.ev
        charger = twin.charger
        policy = self._policy

        target_soc = state.intent.ev_target_soc_percent
        if target_soc <= 0:
            target_soc = policy.target_soc_percent

        if ev.soc_percent is None:
            return EnergyDecision(
                action=EnergyAction.HOLD,
                confidence=0.55,
                score=10.0,
                reasons=(
                    DecisionReason(
                        code="missing_ev_soc",
                        message="EV state of charge is unavailable.",
                        weight=-0.8,
                    ),
                ),
            )

        if ev.soc_percent >= target_soc:
            return EnergyDecision(
                action=EnergyAction.STOP_EV_CHARGING,
                confidence=0.99,
                score=100.0,
                reasons=(
                    DecisionReason(
                        code="target_soc_reached",
                        message=(
                            f"EV reached {ev.soc_percent:.0f}% SOC; "
                            f"target is {target_soc:.0f}%."
                        ),
                        weight=1.0,
                    ),
                ),
                parameters={"target_soc_percent": target_soc},
            )

        if ev.connected is False or charger.connected is False:
            return EnergyDecision(
                action=EnergyAction.HOLD,
                confidence=0.98,
                score=85.0,
                reasons=(
                    DecisionReason(
                        code="ev_not_connected",
                        message="The vehicle is not connected to the charger.",
                        weight=1.0,
                    ),
                ),
            )

        grid_import_w = twin.power.grid_import_w
        charging_power_w = max(charger.power_w, ev.charging_power_w, 0.0)

        if grid_import_w > state.policy.reserve_power_w:
            return EnergyDecision(
                action=EnergyAction.STOP_EV_CHARGING,
                confidence=0.96,
                score=95.0,
                reasons=(
                    DecisionReason(
                        code="grid_import_detected",
                        message=(
                            f"Home is importing {grid_import_w:.0f} W; "
                            "protect self-consumption and breaker headroom."
                        ),
                        weight=1.0,
                    ),
                ),
                parameters={"grid_import_w": grid_import_w},
            )

        available_w = (
            twin.power.grid_export_w
            + charging_power_w
            - state.policy.reserve_power_w
        )
        available_w = max(available_w, 0.0)

        minimum_current = max(
            policy.minimum_ev_current_a,
            int(state.constraints.minimum_ev_current_a),
        )
        maximum_current = min(
            policy.maximum_ev_current_a,
            int(state.constraints.maximum_ev_current_a),
        )
        required_w = minimum_current * policy.voltage_v
        proposed_current_a = int(available_w / policy.voltage_v)

        if proposed_current_a < minimum_current:
            return EnergyDecision(
                action=EnergyAction.HOLD,
                confidence=0.91,
                score=70.0,
                reasons=(
                    DecisionReason(
                        code="surplus_below_stable_threshold",
                        message=(
                            f"Available power is {available_w:.0f} W; "
                            f"stable charging needs at least {required_w:.0f} W."
                        ),
                        weight=0.9,
                    ),
                    DecisionReason(
                        code="protect_grid_reserve",
                        message=(
                            f"HEOS keeps {state.policy.reserve_power_w:.0f} W "
                            "as operating reserve."
                        ),
                        weight=0.6,
                    ),
                ),
                parameters={
                    "available_power_w": available_w,
                    "required_power_w": required_w,
                },
            )

        current_a = min(proposed_current_a, maximum_current)
        power_w = current_a * policy.voltage_v
        cloud_risk = state.predictions.expected_cloud_risk_percent

        reasons = [
            DecisionReason(
                code="solar_surplus_available",
                message=(
                    f"Solar surplus supports {current_a} A "
                    f"({power_w:.0f} W) EV charging."
                ),
                weight=1.0,
            ),
            DecisionReason(
                code="ev_below_target",
                message=(
                    f"EV SOC is {ev.soc_percent:.0f}%; "
                    f"target is {target_soc:.0f}%."
                ),
                weight=0.9,
            ),
            DecisionReason(
                code="breaker_limits_respected",
                message=(
                    f"Charging remains within the configured "
                    f"{state.constraints.main_breaker_a:.0f} A main breaker."
                ),
                weight=0.7,
            ),
        ]

        confidence = 0.95
        score = 90.0

        if cloud_risk is not None and cloud_risk >= 70.0:
            reasons.append(
                DecisionReason(
                    code="high_cloud_risk",
                    message=(
                        f"Cloud risk is {cloud_risk:.0f}%; "
                        "use available solar energy now."
                    ),
                    weight=0.8,
                )
            )
            score += 5.0
            confidence = 0.97

        return EnergyDecision(
            action=EnergyAction.CHARGE_EV,
            confidence=confidence,
            score=score,
            reasons=tuple(reasons),
            parameters={
                "current_a": current_a,
                "power_w": power_w,
                "available_power_w": available_w,
                "target_soc_percent": target_soc,
            },
        )

    @staticmethod
    def _hold_for_untrusted_state(state: HouseState) -> EnergyDecision:
        return EnergyDecision(
            action=EnergyAction.HOLD,
            confidence=0.99,
            score=100.0,
            reasons=(
                DecisionReason(
                    code="state_not_ready",
                    message=(
                        "HouseState is stale or below the configured "
                        "confidence threshold."
                    ),
                    weight=1.0,
                ),
            ),
            parameters={
                "decision_ready": state.decision_ready,
                "control_mode": state.intent.control_mode.value,
            },
        )
