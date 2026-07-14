from heos.compiler.compiler import DecisionCompiler
from heos.kernel import EnergyBalance, KernelHealth, KernelSnapshot
from heos.safety import SafetyContext, SafetyEngine


plan = DecisionCompiler().compile("charge_ev_now")

snapshot = KernelSnapshot(
    health=KernelHealth.READY,
    balance=EnergyBalance(
        production_w=5000,
        consumption_w=1500,
        storage_charge_w=0,
        storage_discharge_w=0,
        grid_import_w=0,
        grid_export_w=0,
    ),
    resource_count=4,
    flow_count=3,
)

report = SafetyEngine().evaluate(
    SafetyContext(
        plan=plan,
        kernel=snapshot,
        projected_grid_import_w=2000,
        maximum_grid_import_w=8000,
    )
)

print("Verdict:", report.verdict.value)
for finding in report.findings:
    print(
        finding.rule_id,
        finding.verdict.value,
        finding.reason,
    )
