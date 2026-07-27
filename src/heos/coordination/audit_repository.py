from __future__ import annotations

import os
from pathlib import Path

from .audit import CoordinationAuditRecord, CoordinationAuditTrail
from .audit_serialization import (
    dumps_audit_record,
    loads_audit_record,
)


class JsonlCoordinationAuditTrail(CoordinationAuditTrail):
    """Persistent tamper-evident coordination audit trail."""

    def __init__(
        self,
        path: str | Path,
    ) -> None:
        super().__init__()
        self._path = Path(path)
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if self._path.exists():
            self._load()

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> None:
        for line_number, line in enumerate(
            self._path.read_text(
                encoding="utf-8",
            ).splitlines(),
            start=1,
        ):
            if not line.strip():
                continue

            try:
                super().append(
                    loads_audit_record(line)
                )
            except Exception as exc:
                raise ValueError(
                    "invalid coordination audit record "
                    f"at line {line_number}"
                ) from exc

    def append(
        self,
        record: CoordinationAuditRecord,
    ) -> CoordinationAuditRecord:
        if not record.verify():
            raise ValueError(
                "invalid coordination audit record"
            )

        records = self.records()
        expected = (
            records[-1].digest
            if records
            else None
        )

        if record.previous_digest != expected:
            raise ValueError(
                "coordination audit chain mismatch"
            )

        encoded = dumps_audit_record(record)

        with self._path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(encoded)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        return super().append(record)