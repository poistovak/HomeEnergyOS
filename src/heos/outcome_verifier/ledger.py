from __future__ import annotations

from dataclasses import dataclass, field

from .models import OutcomeCertificate


@dataclass(slots=True)
class OutcomeLedger:
    _entries: list[OutcomeCertificate] = field(default_factory=list)

    def append(self, certificate: OutcomeCertificate) -> None:
        if not certificate.verify():
            raise ValueError("invalid outcome certificate")
        expected = self._entries[-1].digest if self._entries else None
        if certificate.previous_digest != expected:
            raise ValueError("outcome certificate chain mismatch")
        self._entries.append(certificate)

    def entries(self) -> tuple[OutcomeCertificate, ...]:
        return tuple(self._entries)

    def verify_chain(self) -> bool:
        previous = None
        for entry in self._entries:
            if not entry.verify() or entry.previous_digest != previous:
                return False
            previous = entry.digest
        return True
