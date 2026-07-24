"""Safe Home Assistant command translation.

Milestone 4 defaults to dry-run. No service is called unless a future
explicit live executor is introduced and approved by the Safety Layer.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .client import HomeAssistantClient


@dataclass(frozen=True, slots=True)
class HomeAssistantServiceCommand:
    domain: str
    service: str
    data: Mapping[str, object] = field(default_factory=dict)
    reason: str = ""


class DryRunHomeAssistantExecutor:
    """Record commands without changing the real home."""

    def __init__(self) -> None:
        self._commands: list[HomeAssistantServiceCommand] = []

    def execute(
        self,
        command: HomeAssistantServiceCommand,
    ) -> None:
        self._commands.append(command)

    @property
    def commands(self) -> tuple[HomeAssistantServiceCommand, ...]:
        return tuple(self._commands)


class LiveHomeAssistantExecutor:
    """Explicit live executor kept separate from the default dry-run path."""

    def __init__(
        self,
        client: HomeAssistantClient,
        *,
        enabled: bool = False,
    ) -> None:
        self._client = client
        self._enabled = enabled

    def execute(
        self,
        command: HomeAssistantServiceCommand,
    ) -> None:
        if not self._enabled:
            raise RuntimeError(
                "Live Home Assistant execution is disabled"
            )
        self._client.call_service(
            command.domain,
            command.service,
            dict(command.data),
        )
