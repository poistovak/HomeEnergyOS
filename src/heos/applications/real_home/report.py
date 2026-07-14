from __future__ import annotations

from .runtime import RealHomeCycle


def render_cycle(cycle: RealHomeCycle) -> str:
    s = cycle.snapshot
    h = cycle.health

    lines = [
        "HEOS REAL HOME — READ ONLY",
        "==========================",
        f"PV power:        {s.pv_power_w:.0f} W",
        f"House load:      {s.house_power_w:.0f} W",
        f"Grid import:     {s.grid_import_w:.0f} W",
        f"Grid export:     {s.grid_export_w:.0f} W",
        f"Solar surplus:   {s.solar_surplus_w:.0f} W",
        f"EV SOC:          {s.ev_soc_percent if s.ev_soc_percent is not None else 'n/a'}",
        f"EV connected:    {s.ev_connected if s.ev_connected is not None else 'n/a'}",
        f"Charger power:   {s.charger_power_w if s.charger_power_w is not None else 'n/a'} W",
        f"Health:          {'OK' if h.healthy else 'FAILED'}",
        "Reasons:",
        *[f"- {reason}" for reason in h.reasons],
    ]
    return "\n".join(lines)
