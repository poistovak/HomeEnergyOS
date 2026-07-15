from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, TypeVar

from .models import (
    ComparisonRecord,
    DecisionRecord,
    ExperienceCandidate,
    OutcomeClassification,
    OutcomeRecord,
)

RecordT = TypeVar(
    "RecordT",
    DecisionRecord,
    OutcomeRecord,
    ComparisonRecord,
    ExperienceCandidate,
)


class FeedbackRepository(Protocol):
    def append_decision(self, record: DecisionRecord) -> None: ...

    def append_outcome(self, record: OutcomeRecord) -> None: ...

    def append_comparison(self, record: ComparisonRecord) -> None: ...

    def append_experience(self, record: ExperienceCandidate) -> None: ...

    def get_decision(self, record_id: str) -> DecisionRecord: ...

    def get_outcome(self, record_id: str) -> OutcomeRecord: ...

    def get_comparison(self, record_id: str) -> ComparisonRecord: ...


@dataclass(frozen=True, slots=True)
class FeedbackQuery:
    scenario_id: str | None = None
    classification: OutcomeClassification | None = None
    since: datetime | None = None
    until: datetime | None = None

    def __post_init__(self) -> None:
        for name in ("since", "until"):
            value = getattr(self, name)
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError(f"{name} must be timezone-aware")
        if self.since is not None and self.until is not None and self.until < self.since:
            raise ValueError("until must not be before since")


class InMemoryFeedbackRepository:
    def __init__(self) -> None:
        self._decisions: dict[str, DecisionRecord] = {}
        self._outcomes: dict[str, OutcomeRecord] = {}
        self._comparisons: dict[str, ComparisonRecord] = {}
        self._experiences: dict[str, ExperienceCandidate] = {}

    @staticmethod
    def _append(store: dict[str, RecordT], record: RecordT) -> None:
        if record.record_id in store:
            raise ValueError(f"record {record.record_id} already exists")
        store[record.record_id] = record

    def append_decision(self, record: DecisionRecord) -> None:
        self._append(self._decisions, record)

    def append_outcome(self, record: OutcomeRecord) -> None:
        if record.decision_record_id not in self._decisions:
            raise KeyError(record.decision_record_id)
        self._append(self._outcomes, record)

    def append_comparison(self, record: ComparisonRecord) -> None:
        if record.decision_record_id not in self._decisions:
            raise KeyError(record.decision_record_id)
        if record.outcome_record_id not in self._outcomes:
            raise KeyError(record.outcome_record_id)
        self._append(self._comparisons, record)

    def append_experience(self, record: ExperienceCandidate) -> None:
        if record.comparison_record_id not in self._comparisons:
            raise KeyError(record.comparison_record_id)
        self._append(self._experiences, record)

    def get_decision(self, record_id: str) -> DecisionRecord:
        return self._decisions[record_id]

    def get_outcome(self, record_id: str) -> OutcomeRecord:
        return self._outcomes[record_id]

    def get_comparison(self, record_id: str) -> ComparisonRecord:
        return self._comparisons[record_id]

    def get_experience(self, record_id: str) -> ExperienceCandidate:
        return self._experiences[record_id]

    def decisions(self) -> tuple[DecisionRecord, ...]:
        return tuple(self._decisions.values())

    def outcomes(self) -> tuple[OutcomeRecord, ...]:
        return tuple(self._outcomes.values())

    def comparisons(self, query: FeedbackQuery | None = None) -> tuple[ComparisonRecord, ...]:
        records = list(self._comparisons.values())
        if query is None:
            return tuple(records)
        if query.classification is not None:
            records = [item for item in records if item.classification is query.classification]
        if query.scenario_id is not None:
            matching_decisions = {
                item.record_id
                for item in self._decisions.values()
                if item.scenario_id == query.scenario_id
            }
            records = [item for item in records if item.decision_record_id in matching_decisions]
        if query.since is not None:
            records = [item for item in records if item.compared_at >= query.since]
        if query.until is not None:
            records = [item for item in records if item.compared_at <= query.until]
        return tuple(records)

    def experiences(self) -> tuple[ExperienceCandidate, ...]:
        return tuple(self._experiences.values())
