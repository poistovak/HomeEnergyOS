from __future__ import annotations

from dataclasses import dataclass, field

from .models import ExecutionCertificate


@dataclass(slots=True)
class ExecutionLedger:
    _entries: list[ExecutionCertificate] = field(default_factory=list)

    def append(self, certificate: ExecutionCertificate) -> None:
        if not certificate.verify():
            raise ValueError("invalid execution certificate")
        expected = self._entries[-1].digest if self._entries else None
        if certificate.previous_digest != expected:
            raise ValueError("execution certificate chain mismatch")
        self._entries.append(certificate)

    def entries(self) -> tuple[ExecutionCertificate, ...]:
        return tuple(self._entries)

    def verify_chain(self) -> bool:
        previous = None
        for entry in self._entries:
            if not entry.verify() or entry.previous_digest != previous:
                return False
            previous = entry.digest
        return True
