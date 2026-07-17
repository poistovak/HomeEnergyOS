from __future__ import annotations

from dataclasses import dataclass, field

from .models import RecoveryCertificate


@dataclass(slots=True)
class IncidentLedger:
    _entries: list[RecoveryCertificate] = field(default_factory=list)

    def append(self, certificate: RecoveryCertificate) -> None:
        expected_previous = self._entries[-1].digest if self._entries else None
        if certificate.previous_digest != expected_previous:
            raise ValueError("certificate chain mismatch")
        if not certificate.verify():
            raise ValueError("invalid recovery certificate")
        self._entries.append(certificate)

    def entries(self) -> tuple[RecoveryCertificate, ...]:
        return tuple(self._entries)

    def verify_chain(self) -> bool:
        previous: str | None = None
        for certificate in self._entries:
            if certificate.previous_digest != previous or not certificate.verify():
                return False
            previous = certificate.digest
        return True
