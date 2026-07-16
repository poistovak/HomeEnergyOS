from heos.demo.scenarios import sunny_surplus_scenario
from heos.robustness import RobustnessEngine, RobustnessPolicy, render_report

scenario = sunny_surplus_scenario()
engine = RobustnessEngine(
    scenario.parameters,
    strategy_policy=scenario.policy,
    robustness_policy=RobustnessPolicy(),
)
run = engine.evaluate(scenario.scenario_id, scenario.candidates, scenario.request)
print(render_report(run), end="")
