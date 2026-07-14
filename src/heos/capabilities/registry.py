from __future__ import annotations

from typing import Any


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[type, Any] = {}

    def register(self, capability_type: type, implementation: Any) -> None:
        self._capabilities[capability_type] = implementation

    def get(self, capability_type: type) -> Any:
        return self._capabilities[capability_type]

    def has(self, capability_type: type) -> bool:
        return capability_type in self._capabilities