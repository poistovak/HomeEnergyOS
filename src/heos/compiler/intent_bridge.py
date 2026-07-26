from __future__ import annotations

from dataclasses import dataclass

from heos.release_gate import ExecutionIntent


@dataclass(frozen=True, slots=True)
class IntentCompilerBridge:
    def scenario_id(
        self,
        intent: ExecutionIntent,
    ) -> str:
        payload = dict(intent.control_payload)

        if payload.get("ev_charge_kw", 0.0) > 0.0:
            return "charge_ev_now"

        return "observe_only"