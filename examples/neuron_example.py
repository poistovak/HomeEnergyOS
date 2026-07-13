from heos.brains.ev_charging import EVChargingBrain
from heos.orchestrator import BrainOrchestrator, BrainRegistration
from heos.state import HouseState

orchestrator = BrainOrchestrator(
    registrations=(
        BrainRegistration(
            brain=EVChargingBrain(),
            priority=80,
            utility=0.5,
        ),
    )
)

state = HouseState(
    pv_power_w=6800,
    house_power_w=1500,
    grid_power_w=-5300,
    ev_soc_percent=42,
    ev_connected=True,
)

result = orchestrator.evaluate(state)

if result.decision:
    print(result.decision.action)
    print(result.decision.parameters)
    print(result.decision.explain())
