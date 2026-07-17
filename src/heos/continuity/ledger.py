from __future__ import annotations

from dataclasses import dataclass, field

from .models import ContinuityCertificate


@dataclass(slots=True)
class ContinuityLedger:
    _entries: list[ContinuityCertificate] = field(default_factory=list)

    def append(self, certificate: ContinuityCertificate) -> None:
        previous = self._entries[-1].digest if self._entries else None
        if certificate.previous_digest != previous:
            raise ValueError("certificate chain mismatch")
        if not certificate.verify():
            raise ValueError("invalid continuity certificate")
        self._entries.append(certificate)

    def entries(self) -> tuple[ContinuityCertificate, ...]:
        return tuple(self._entries)

    def verify_chain(self) -> bool:
        previous: str | None = None
        for certificate in self._entries:
            if certificate.previous_digest != previous:
                return False
            if not certificate.verify():
                return False
            previous = certificate.digest
        return True
