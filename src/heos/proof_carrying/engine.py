from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from .builder import ProofBuilder
from .models import CertifiedDecision, DecisionCertificate, ProofPolicy, VerificationReport
from .repository import InMemoryProofRepository, ProofRepository
from .verifier import ProofVerifier


class ProofCarryingDecisionEngine:
    def __init__(
        self,
        *,
        policy: ProofPolicy | None = None,
        repository: ProofRepository | None = None,
    ) -> None:
        self._builder = ProofBuilder(policy)
        self._verifier = ProofVerifier()
        self._repository = repository or InMemoryProofRepository()

    @property
    def builder(self) -> ProofBuilder:
        return self._builder

    @property
    def verifier(self) -> ProofVerifier:
        return self._verifier

    @property
    def repository(self) -> ProofRepository:
        return self._repository

    def certify(
        self,
        release_decision: Any,
        *,
        state_snapshot: Any,
        manifest_versions: Iterable[tuple[str, str]] | dict[str, str],
        model_versions: Iterable[tuple[str, str]] | dict[str, str] | None = None,
        rejected_alternatives: Iterable[Any] = (),
        previous_certificate: DecisionCertificate | CertifiedDecision | None = None,
        link_to_repository_head: bool = False,
        issued_at: datetime | None = None,
        metadata: Iterable[tuple[str, str]] = (),
    ) -> CertifiedDecision:
        previous = previous_certificate
        if link_to_repository_head and previous is None and hasattr(self._repository, "last"):
            previous = self._repository.last()
        decision = self._builder.certify(
            release_decision,
            state_snapshot=state_snapshot,
            manifest_versions=manifest_versions,
            model_versions=model_versions,
            rejected_alternatives=rejected_alternatives,
            previous_certificate=previous,
            issued_at=issued_at,
            metadata=metadata,
        )
        report = self._verifier.verify(
            decision,
            verified_at=decision.certificate.issued_at,
            previous_certificate=previous,
        )
        if not report.valid:
            details = "; ".join(item.detail for item in report.issues)
            raise ValueError(f"new certificate failed self-verification: {details}")
        return self._repository.append(decision)

    def verify(
        self,
        decision: CertifiedDecision,
        *,
        verified_at: datetime | None = None,
        previous_certificate: DecisionCertificate | CertifiedDecision | None = None,
    ) -> VerificationReport:
        return self._verifier.verify(
            decision,
            verified_at=verified_at,
            previous_certificate=previous_certificate,
        )
