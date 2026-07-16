from __future__ import annotations

from itertools import product

from .canonical import stable_id
from .models import Perturbation, RobustnessPolicy


def generate_perturbations(policy: RobustnessPolicy) -> tuple[Perturbation, ...]:
    if policy.variant_count > policy.max_variants:
        raise ValueError(
            f"robustness grid contains {policy.variant_count} variants; "
            f"maximum is {policy.max_variants}"
        )
    variants = {
        Perturbation(pv, load, temperature, tariff)
        for pv, load, temperature, tariff in product(
            policy.pv_multipliers,
            policy.load_multipliers,
            policy.outdoor_temp_deltas_c,
            policy.tariff_multipliers,
        )
    }
    return tuple(
        sorted(
            variants,
            key=lambda item: (
                round(item.distance, 12),
                item.pv_multiplier,
                item.load_multiplier,
                item.outdoor_temp_delta_c,
                item.tariff_multiplier,
            ),
        )
    )


def perturbation_id(perturbation: Perturbation) -> str:
    return stable_id("heos-robustness-variant", perturbation.to_dict())
