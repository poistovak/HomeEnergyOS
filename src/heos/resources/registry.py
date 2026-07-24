from __future__ import annotations

from .models import ResourceKind
from .resource import EnergyResource


class ResourceRegistry:
    def __init__(self) -> None:
        self._resources: dict[str, EnergyResource] = {}

    def register(self, resource: EnergyResource) -> None:
        if resource.resource_id in self._resources:
            raise ValueError(f"resource already registered: {resource.resource_id}")
        self._resources[resource.resource_id] = resource

    def get(self, resource_id: str) -> EnergyResource:
        return self._resources[resource_id]

    def find_by_kind(self, kind: ResourceKind) -> tuple[EnergyResource, ...]:
        return tuple(r for r in self._resources.values() if r.kind is kind)

    def find_by_capability(self, capability: str) -> tuple[EnergyResource, ...]:
        return tuple(r for r in self._resources.values() if r.supports(capability))

    @property
    def all(self) -> tuple[EnergyResource, ...]:
        return tuple(self._resources.values())
