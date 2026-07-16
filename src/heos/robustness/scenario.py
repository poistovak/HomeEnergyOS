from __future__ import annotations

from dataclasses import replace

from heos.digital_twin import TwinDisturbance
from heos.strategy import StrategyRequest, TariffStep

from .grid import perturbation_id
from .models import Perturbation


def perturb_request(request: StrategyRequest, perturbation: Perturbation) -> StrategyRequest:
    disturbances = tuple(
        TwinDisturbance(
            outdoor_temp_c=item.outdoor_temp_c + perturbation.outdoor_temp_delta_c,
            pv_kw=item.pv_kw * perturbation.pv_multiplier,
            base_load_kw=item.base_load_kw * perturbation.load_multiplier,
            solar_gain_kw=item.solar_gain_kw,
            internal_gain_kw=item.internal_gain_kw,
        )
        for item in request.disturbances
    )
    tariffs = tuple(
        TariffStep(
            import_price_per_kwh=item.import_price_per_kwh
            * perturbation.tariff_multiplier,
            export_price_per_kwh=item.export_price_per_kwh
            * perturbation.tariff_multiplier,
        )
        for item in request.tariffs
    )
    metadata = (
        *request.metadata,
        ("robustness_variant", perturbation_id(perturbation)),
        ("robustness_pv_multiplier", f"{perturbation.pv_multiplier:.6f}"),
        ("robustness_load_multiplier", f"{perturbation.load_multiplier:.6f}"),
        ("robustness_outdoor_temp_delta_c", f"{perturbation.outdoor_temp_delta_c:.6f}"),
        ("robustness_tariff_multiplier", f"{perturbation.tariff_multiplier:.6f}"),
    )
    return replace(request, disturbances=disturbances, tariffs=tariffs, metadata=metadata)
