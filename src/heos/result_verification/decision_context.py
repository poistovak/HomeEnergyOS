from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionContext:
    decision: str
    context: dict[str, object]


class DecisionContextMemory:

    def __init__(self):
        self._items: list[DecisionContext] = []

    def add(
        self,
        item: DecisionContext,
    ) -> None:
        self._items.append(item)

    def all(self) -> list[DecisionContext]:
        return list(self._items)