from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .models import CalibrationReport
from .serialization import dumps_report, loads_report


class CalibrationConflictError(RuntimeError):
    pass


class CalibrationNotFoundError(KeyError):
    pass


class CalibrationRepository(Protocol):
    def append(self, report: CalibrationReport) -> CalibrationReport: ...

    def get(self, report_id: str) -> CalibrationReport: ...

    def all(self) -> tuple[CalibrationReport, ...]: ...


class InMemoryCalibrationRepository:
    def __init__(self) -> None:
        self._reports: dict[str, CalibrationReport] = {}
        self._order: list[str] = []

    def append(self, report: CalibrationReport) -> CalibrationReport:
        existing = self._reports.get(report.report_id)
        if existing is not None:
            if existing != report:
                raise CalibrationConflictError(
                    f"report_id already exists with different content: {report.report_id}"
                )
            return existing
        self._reports[report.report_id] = report
        self._order.append(report.report_id)
        return report

    def get(self, report_id: str) -> CalibrationReport:
        try:
            return self._reports[report_id]
        except KeyError as exc:
            raise CalibrationNotFoundError(report_id) from exc

    def all(self) -> tuple[CalibrationReport, ...]:
        return tuple(self._reports[item] for item in self._order)


class JsonlCalibrationRepository:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._memory = InMemoryCalibrationRepository()
        if self._path.exists():
            for line_number, raw in enumerate(
                self._path.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                if not raw.strip():
                    continue
                try:
                    self._memory.append(loads_report(raw))
                except Exception as exc:
                    raise ValueError(
                        f"invalid calibration record at line {line_number}"
                    ) from exc

    @property
    def path(self) -> Path:
        return self._path

    def append(self, report: CalibrationReport) -> CalibrationReport:
        existing = None
        try:
            existing = self._memory.get(report.report_id)
        except CalibrationNotFoundError:
            pass
        if existing is not None:
            if existing != report:
                raise CalibrationConflictError(
                    f"report_id already exists with different content: {report.report_id}"
                )
            return existing

        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(dumps_report(report))
            handle.write("\n")
        return self._memory.append(report)

    def get(self, report_id: str) -> CalibrationReport:
        return self._memory.get(report_id)

    def all(self) -> tuple[CalibrationReport, ...]:
        return self._memory.all()
