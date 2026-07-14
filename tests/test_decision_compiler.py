from heos.compiler.compiler import DecisionCompiler

def test_compile_charge_plan():
    plan=DecisionCompiler().compile("charge_ev_now")
    assert plan.scenario_id=="charge_ev_now"
    assert len(plan.steps)==5
    assert plan.steps[0].description=="Kernel READY"
