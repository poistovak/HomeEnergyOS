from __future__ import annotations

from datetime import datetime

from .models import ComponentVersion, SystemManifest


def standard_manifest(
    built_at: datetime,
    *,
    forecast: str,
    feedback: str,
    memory: str,
    digital_twin: str,
    calibration: str,
    strategy: str,
    compiler: str,
    safety: str,
    execution: str,
    schema_version: str = "heos-release-manifest-1",
) -> SystemManifest:
    return SystemManifest(
        components=(
            ComponentVersion("forecast", forecast),
            ComponentVersion("feedback", feedback),
            ComponentVersion("memory", memory),
            ComponentVersion("digital_twin", digital_twin),
            ComponentVersion("calibration", calibration),
            ComponentVersion("strategy", strategy),
            ComponentVersion("compiler", compiler),
            ComponentVersion("safety", safety),
            ComponentVersion("execution", execution),
        ),
        built_at=built_at,
        schema_version=schema_version,
    )
