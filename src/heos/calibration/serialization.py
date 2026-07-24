from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from heos.digital_twin import TwinParameters

from .models import (
    CalibratableParameter,
    CalibrationMetrics,
    CalibrationReport,
    ParameterEstimate,
)


def _parameters_to_dict(parameters: TwinParameters) -> dict[str, Any]:
    return {
        name: getattr(parameters, name)
        for name in parameters.__dataclass_fields__
    }


def _metrics_to_dict(metrics: CalibrationMetrics) -> dict[str, Any]:
    return {
        name: getattr(metrics, name)
        for name in metrics.__dataclass_fields__
    }


def _metrics_from_dict(data: Mapping[str, Any]) -> CalibrationMetrics:
    return CalibrationMetrics(
        indoor_temp_mae_c=float(data["indoor_temp_mae_c"]),
        battery_soc_mae=float(data["battery_soc_mae"]),
        ev_soc_mae=float(data["ev_soc_mae"]),
        grid_import_mae_kwh=float(data["grid_import_mae_kwh"]),
        grid_export_mae_kwh=float(data["grid_export_mae_kwh"]),
        battery_throughput_mae_kwh=float(data["battery_throughput_mae_kwh"]),
        weighted_loss=float(data["weighted_loss"]),
        sample_count=int(data["sample_count"]),
        total_weight=float(data["total_weight"]),
    )


def report_to_dict(report: CalibrationReport) -> dict[str, Any]:
    return {
        "report_id": report.report_id,
        "generated_at": report.generated_at.isoformat(),
        "base_parameters": _parameters_to_dict(report.base_parameters),
        "calibrated_parameters": _parameters_to_dict(report.calibrated_parameters),
        "estimates": [
            {
                "parameter": item.parameter.value,
                "before": item.before,
                "after": item.after,
                "minimum": item.minimum,
                "maximum": item.maximum,
            }
            for item in report.estimates
        ],
        "training_before": _metrics_to_dict(report.training_before),
        "training_after": _metrics_to_dict(report.training_after),
        "validation_before": (
            _metrics_to_dict(report.validation_before)
            if report.validation_before is not None
            else None
        ),
        "validation_after": (
            _metrics_to_dict(report.validation_after)
            if report.validation_after is not None
            else None
        ),
        "accepted": report.accepted,
        "policy_version": report.policy_version,
        "sample_ids": list(report.sample_ids),
        "validation_sample_ids": list(report.validation_sample_ids),
        "explanation": report.explanation,
    }


def report_from_dict(data: Mapping[str, Any]) -> CalibrationReport:
    raw_estimates = data["estimates"]
    if not isinstance(raw_estimates, list):
        raise ValueError("estimates must be a list")
    estimates = tuple(
        ParameterEstimate(
            parameter=CalibratableParameter(str(item["parameter"])),
            before=float(item["before"]),
            after=float(item["after"]),
            minimum=float(item["minimum"]),
            maximum=float(item["maximum"]),
        )
        for item in raw_estimates
    )
    validation_before_data = data.get("validation_before")
    validation_after_data = data.get("validation_after")
    return CalibrationReport(
        report_id=str(data["report_id"]),
        generated_at=datetime.fromisoformat(str(data["generated_at"])),
        base_parameters=TwinParameters(**dict(data["base_parameters"])),
        calibrated_parameters=TwinParameters(**dict(data["calibrated_parameters"])),
        estimates=estimates,
        training_before=_metrics_from_dict(data["training_before"]),
        training_after=_metrics_from_dict(data["training_after"]),
        validation_before=(
            _metrics_from_dict(validation_before_data)
            if isinstance(validation_before_data, Mapping)
            else None
        ),
        validation_after=(
            _metrics_from_dict(validation_after_data)
            if isinstance(validation_after_data, Mapping)
            else None
        ),
        accepted=bool(data["accepted"]),
        policy_version=str(data["policy_version"]),
        sample_ids=tuple(str(item) for item in data["sample_ids"]),
        validation_sample_ids=tuple(
            str(item) for item in data.get("validation_sample_ids", [])
        ),
        explanation=str(data["explanation"]),
    )


def dumps_report(report: CalibrationReport) -> str:
    return json.dumps(report_to_dict(report), sort_keys=True, separators=(",", ":"))


def loads_report(payload: str) -> CalibrationReport:
    data = json.loads(payload)
    if not isinstance(data, Mapping):
        raise ValueError("calibration JSON must contain an object")
    return report_from_dict(data)
