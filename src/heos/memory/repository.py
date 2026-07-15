from __future__ import annotations

import os
from pathlib import Path
from threading import RLock
from typing import Protocol

from .models import HouseMemoryRecord
from .serialization import dumps_record, loads_record


class MemoryConflictError(ValueError):
    pass


class MemoryNotFoundError(KeyError):
    pass


class HouseMemoryRepository(Protocol):
    def append(self, record: HouseMemoryRecord) -> None: ...

    def get(self, record_id: str) -> HouseMemoryRecord: ...

    def get_by_source(self, source_experience_id: str) -> HouseMemoryRecord | None: ...

    def list_all(self) -> tuple[HouseMemoryRecord, ...]: ...


class InMemoryHouseMemoryRepository:
    def __init__(self) -> None:
        self._records: dict[str, HouseMemoryRecord] = {}
        self._source_index: dict[str, str] = {}
        self._order: list[str] = []
        self._lock = RLock()

    def append(self, record: HouseMemoryRecord) -> None:
        with self._lock:
            existing = self._records.get(record.record_id)
            if existing is not None:
                if existing == record:
                    return
                raise MemoryConflictError(f"record_id already exists: {record.record_id}")
            source_record_id = self._source_index.get(record.source_experience_id)
            if source_record_id is not None:
                source_record = self._records[source_record_id]
                if source_record == record:
                    return
                raise MemoryConflictError(
                    "source_experience_id already exists: "
                    f"{record.source_experience_id}"
                )
            self._records[record.record_id] = record
            self._source_index[record.source_experience_id] = record.record_id
            self._order.append(record.record_id)

    def get(self, record_id: str) -> HouseMemoryRecord:
        try:
            return self._records[record_id]
        except KeyError as exc:
            raise MemoryNotFoundError(record_id) from exc

    def get_by_source(self, source_experience_id: str) -> HouseMemoryRecord | None:
        record_id = self._source_index.get(source_experience_id)
        return None if record_id is None else self._records[record_id]

    def list_all(self) -> tuple[HouseMemoryRecord, ...]:
        return tuple(self._records[record_id] for record_id in self._order)


class JsonlHouseMemoryRepository(InMemoryHouseMemoryRepository):
    def __init__(self, path: str | Path) -> None:
        super().__init__()
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            self._load()

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> None:
        for line_number, line in enumerate(
            self._path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            try:
                super().append(loads_record(line))
            except Exception as exc:
                raise ValueError(
                    f"invalid house-memory record at line {line_number}"
                ) from exc

    def append(self, record: HouseMemoryRecord) -> None:
        with self._lock:
            existing = self.get_by_source(record.source_experience_id)
            if existing is not None:
                if existing == record:
                    return
                raise MemoryConflictError(
                    "source_experience_id already exists: "
                    f"{record.source_experience_id}"
                )
            if record.record_id in self._records:
                if self._records[record.record_id] == record:
                    return
                raise MemoryConflictError(f"record_id already exists: {record.record_id}")

            encoded = dumps_record(record)
            with self._path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(encoded)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            super().append(record)
