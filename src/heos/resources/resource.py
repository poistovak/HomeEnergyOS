from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping
from .models import ResourceKind, ResourceState

@dataclass(frozen=True, slots=True)
class ResourceIdentity:
    resource_id: str
    name: str
    kind: ResourceKind

    def __post_init__(self) -> None:
        if not self.resource_id.strip():
            raise ValueError("resource_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")

@dataclass(slots=True)
class EnergyResource:
    identity: ResourceIdentity
    capabilities: frozenset[str] = frozenset()
    metadata: Mapping[str, object] = field(default_factory=dict)
    _state: ResourceState | None = field(default=None, init=False, repr=False)

    @property
    def resource_id(self) -> str:
        return self.identity.resource_id

    @property
    def kind(self) -> ResourceKind:
        return self.identity.kind

    @property
    def state(self) -> ResourceState | None:
        return self._state

    def update_state(self, state: ResourceState) -> None:
        if state.resource_id != self.resource_id:
            raise ValueError("state resource_id does not match resource identity")
        self._state = state

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities
