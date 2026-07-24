from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from heos.digital_twin import TwinParameters

from .metrics import evaluate_parameters
from .models import (
    CalibrationPolicy,
    CalibrationReport,
    CalibrationSample,
    ParameterBounds,
    ParameterEstimate,
    ensure_unique_samples,
)


class CalibrationConfigurationError(ValueError):
    pass


class DigitalTwinCalibrator:
    def __init__(self, policy: CalibrationPolicy | None = None) -> None:
        self._policy = policy or CalibrationPolicy()

    @property
    def policy(self) -> CalibrationPolicy:
        return self._policy

    def calibrate(
        self,
        base_parameters: TwinParameters,
        samples: Iterable[CalibrationSample],
        bounds: Iterable[ParameterBounds],
        *,
        generated_at: datetime,
        validation_samples: Iterable[CalibrationSample] = (),
    ) -> CalibrationReport:
        if generated_at.tzinfo is None or generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")

        training = ensure_unique_samples(samples, "samples")
        validation = tuple(validation_samples)
        if validation:
            validation = ensure_unique_samples(validation, "validation_samples")
        elif self._policy.require_validation:
            raise CalibrationConfigurationError("validation samples are required by policy")

        overlap = {item.sample_id for item in training} & {
            item.sample_id for item in validation
        }
        if overlap:
            raise CalibrationConfigurationError(
                "training and validation sample ids must not overlap"
            )

        normalized_bounds = self._normalize_bounds(base_parameters, bounds)
        baseline_training = self._evaluate(base_parameters, training)
        baseline_validation = self._evaluate(base_parameters, validation) if validation else None

        calibrated = base_parameters
        windows = {
            item.parameter: (item.minimum, item.maximum)
            for item in normalized_bounds
        }
        bound_by_parameter = {item.parameter: item for item in normalized_bounds}

        for _ in range(self._policy.rounds):
            changed = False
            for parameter in sorted(bound_by_parameter, key=lambda item: item.value):
                bound = bound_by_parameter[parameter]
                low, high = windows[parameter]
                values = self._candidate_values(
                    low,
                    high,
                    bound.candidates,
                    current=float(getattr(calibrated, parameter.value)),
                )
                best_value = float(getattr(calibrated, parameter.value))
                best_loss = self._evaluate(calibrated, training).weighted_loss

                scored: list[tuple[float, float]] = []
                for value in values:
                    candidate = replace(calibrated, **{parameter.value: value})
                    loss = self._evaluate(candidate, training).weighted_loss
                    scored.append((loss, value))

                scored.sort(
                    key=lambda item: (
                        round(item[0], 15),
                        abs(item[1] - float(getattr(base_parameters, parameter.value))),
                        item[1],
                    )
                )
                selected_loss, selected_value = scored[0]
                if selected_loss + 1e-15 < best_loss:
                    calibrated = replace(calibrated, **{parameter.value: selected_value})
                    best_value = selected_value
                    changed = True
                else:
                    best_value = float(getattr(calibrated, parameter.value))

                step = (high - low) / (bound.candidates - 1)
                windows[parameter] = (
                    max(bound.minimum, best_value - step),
                    min(bound.maximum, best_value + step),
                )

            if not changed:
                break

        calibrated = replace(
            calibrated,
            version=self._calibrated_version(base_parameters, calibrated),
        )
        training_after = self._evaluate(calibrated, training)
        validation_after = self._evaluate(calibrated, validation) if validation else None

        before_selection = baseline_validation or baseline_training
        after_selection = validation_after or training_after
        absolute_improvement = before_selection.weighted_loss - after_selection.weighted_loss
        relative_improvement = (
            absolute_improvement / before_selection.weighted_loss
            if before_selection.weighted_loss > 1e-15
            else 0.0
        )
        accepted = (
            absolute_improvement >= self._policy.minimum_absolute_improvement
            and relative_improvement >= self._policy.minimum_relative_improvement
        )

        estimates = tuple(
            ParameterEstimate(
                parameter=item.parameter,
                before=float(getattr(base_parameters, item.parameter.value)),
                after=float(getattr(calibrated, item.parameter.value)),
                minimum=item.minimum,
                maximum=item.maximum,
            )
            for item in normalized_bounds
        )

        explanation = self._explanation(
            accepted=accepted,
            used_validation=bool(validation),
            absolute_improvement=absolute_improvement,
            relative_improvement=relative_improvement,
        )
        report_id = self._report_id(
            base_parameters=base_parameters,
            calibrated_parameters=calibrated,
            bounds=normalized_bounds,
            training=training,
            validation=validation,
        )

        return CalibrationReport(
            report_id=report_id,
            generated_at=generated_at,
            base_parameters=base_parameters,
            calibrated_parameters=calibrated,
            estimates=estimates,
            training_before=baseline_training,
            training_after=training_after,
            validation_before=baseline_validation,
            validation_after=validation_after,
            accepted=accepted,
            policy_version=self._policy.version,
            sample_ids=tuple(item.sample_id for item in training),
            validation_sample_ids=tuple(item.sample_id for item in validation),
            explanation=explanation,
        )

    def _evaluate(
        self,
        parameters: TwinParameters,
        samples: tuple[CalibrationSample, ...],
    ):
        return evaluate_parameters(
            parameters,
            samples,
            weights=self._policy.weights,
            scales=self._policy.scales,
        )

    @staticmethod
    def _candidate_values(
        minimum: float,
        maximum: float,
        candidates: int,
        *,
        current: float,
    ) -> tuple[float, ...]:
        step = (maximum - minimum) / (candidates - 1)
        values = [minimum + index * step for index in range(candidates)]
        values.append(current)
        return tuple(sorted({round(value, 12) for value in values}))

    @staticmethod
    def _normalize_bounds(
        base_parameters: TwinParameters,
        bounds: Iterable[ParameterBounds],
    ) -> tuple[ParameterBounds, ...]:
        normalized = tuple(bounds)
        if not normalized:
            raise CalibrationConfigurationError("bounds must not be empty")
        parameters = [item.parameter for item in normalized]
        if len(parameters) != len(set(parameters)):
            raise CalibrationConfigurationError("each parameter may appear only once")
        for item in normalized:
            current = float(getattr(base_parameters, item.parameter.value))
            if not item.minimum <= current <= item.maximum:
                raise CalibrationConfigurationError(
                    f"base parameter {item.parameter.value} must be inside its bounds"
                )
        return tuple(sorted(normalized, key=lambda item: item.parameter.value))

    @staticmethod
    def _calibrated_version(
        base_parameters: TwinParameters,
        calibrated_parameters: TwinParameters,
    ) -> str:
        payload = {
            name: getattr(calibrated_parameters, name)
            for name in calibrated_parameters.__dataclass_fields__
            if name != "version"
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        return f"{base_parameters.version}+cal-{digest}"

    def _report_id(
        self,
        *,
        base_parameters: TwinParameters,
        calibrated_parameters: TwinParameters,
        bounds: tuple[ParameterBounds, ...],
        training: tuple[CalibrationSample, ...],
        validation: tuple[CalibrationSample, ...],
    ) -> str:
        payload = {
            "policy": self._policy.version,
            "base_version": base_parameters.version,
            "calibrated_version": calibrated_parameters.version,
            "bounds": [
                {
                    "parameter": item.parameter.value,
                    "minimum": item.minimum,
                    "maximum": item.maximum,
                    "candidates": item.candidates,
                }
                for item in bounds
            ],
            "training": [item.sample_id for item in training],
            "validation": [item.sample_id for item in validation],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return str(uuid5(NAMESPACE_URL, f"heos-calibration:{canonical}"))

    @staticmethod
    def _explanation(
        *,
        accepted: bool,
        used_validation: bool,
        absolute_improvement: float,
        relative_improvement: float,
    ) -> str:
        dataset = "validation" if used_validation else "training"
        verdict = "accepted" if accepted else "rejected"
        return (
            f"Calibration candidate {verdict} using deterministic bounded coordinate search "
            f"and {dataset} loss. Absolute improvement={absolute_improvement:.8f}; "
            f"relative improvement={relative_improvement:.4%}. The report is advisory and "
            "does not activate parameters or command devices."
        )
