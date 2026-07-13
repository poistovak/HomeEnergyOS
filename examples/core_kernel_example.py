from heos.core import HEOSKernel

kernel = HEOSKernel(
    state_provider=lambda: {"pv_w": 6800, "house_w": 1500, "grid_w": -5300},
    decision_processor=lambda state: {
        "action": "charge_ev",
        "current_a": 16,
        "reason": f"PV surplus: {-state['grid_w']} W",
    },
)

result = kernel.tick()
print(result.decision)
print(f"tick duration: {result.duration_ms:.2f} ms")
