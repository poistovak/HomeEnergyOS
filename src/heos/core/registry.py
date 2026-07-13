from dataclasses import dataclass, field
from typing import Any, Mapping

@dataclass(frozen=True, slots=True)
class DeviceRecord:
    device_id: str
    device_type: str
    adapter: str
    capabilities: frozenset[str] = frozenset()
    metadata: Mapping[str, Any] = field(default_factory=dict)

class DeviceRegistry:
    def __init__(self) -> None:
        self._devices: dict[str, DeviceRecord] = {}

    def register(self, device: DeviceRecord) -> None:
        if device.device_id in self._devices:
            raise ValueError(f"device already registered: {device.device_id}")
        self._devices[device.device_id] = device

    def get(self, device_id: str) -> DeviceRecord | None:
        return self._devices.get(device_id)

    def with_capability(self, capability: str) -> tuple[DeviceRecord, ...]:
        return tuple(d for d in self._devices.values() if capability in d.capabilities)
