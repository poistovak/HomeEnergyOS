from __future__ import annotations
from collections import defaultdict, deque
from .flow import EnergyCarrier, EnergyFlow
from .registry import ResourceRegistry
from .resource import EnergyResource

class ResourceGraph:
    def __init__(self) -> None:
        self.registry = ResourceRegistry()
        self._edges: dict[tuple[str, str, EnergyCarrier], EnergyFlow] = {}
        self._outgoing: dict[str, set[str]] = defaultdict(set)

    def add_resource(self, resource: EnergyResource) -> None:
        self.registry.register(resource)

    def connect(self, flow: EnergyFlow) -> None:
        self.registry.get(flow.source_id)
        self.registry.get(flow.destination_id)
        self._edges[(flow.source_id, flow.destination_id, flow.carrier)] = flow
        self._outgoing[flow.source_id].add(flow.destination_id)

    def outgoing(self, resource_id: str) -> tuple[EnergyResource, ...]:
        self.registry.get(resource_id)
        return tuple(self.registry.get(i) for i in sorted(self._outgoing.get(resource_id, set())))

    def has_path(self, source_id: str, destination_id: str) -> bool:
        self.registry.get(source_id)
        self.registry.get(destination_id)
        queue: deque[str] = deque([source_id])
        visited: set[str] = set()
        while queue:
            current = queue.popleft()
            if current == destination_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self._outgoing.get(current, set()) - visited)
        return False

    @property
    def flows(self) -> tuple[EnergyFlow, ...]:
        return tuple(self._edges.values())
