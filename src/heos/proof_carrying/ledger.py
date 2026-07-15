from __future__ import annotations

from collections.abc import Iterable

from .integrity import certificate_fingerprint, certificate_id_for
from .models import ChainAuditIssue, ChainAuditReport, CertifiedDecision


def audit_chain(records: Iterable[CertifiedDecision]) -> ChainAuditReport:
    decisions = tuple(records)
    issues: list[ChainAuditIssue] = []
    previous = None
    for index, decision in enumerate(decisions):
        certificate = decision.certificate
        if certificate_id_for(certificate) != certificate.certificate_id:
            issues.append(ChainAuditIssue(index, "certificate id is invalid"))
        expected = certificate_fingerprint(previous.certificate) if previous is not None else None
        if certificate.previous_certificate_hash != expected:
            issues.append(ChainAuditIssue(index, "previous certificate hash is invalid"))
        previous = decision
    head_hash = certificate_fingerprint(decisions[-1].certificate) if decisions else None
    return ChainAuditReport(
        valid=not issues,
        length=len(decisions),
        head_hash=head_hash,
        issues=tuple(issues),
    )
