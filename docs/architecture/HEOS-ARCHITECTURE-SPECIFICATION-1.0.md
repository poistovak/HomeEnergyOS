# HEOS Architecture Specification 1.0

**Project:** HEOS — Home Energy Operating System  
**Status:** Proposed Standard  
**Version:** 1.0  
**Codename:** Seven Layers  
**Principle:** *Automation executes rules. HEOS makes decisions.*

---

## 1. Purpose

HEOS is an open-source operating system for residential energy intelligence.

Its purpose is not to automate isolated devices. Its purpose is to understand the energy state of the whole home, predict likely future conditions, simulate possible strategies, choose the best safe decision, explain that decision, and execute it through replaceable adapters.

HEOS must remain:

- vendor independent,
- local first,
- explainable,
- deterministic where safety matters,
- modular,
- testable without hardware,
- replaceable at every infrastructure boundary.

---

## 2. Architectural Law

HEOS is divided into seven layers.

```text
┌──────────────────────────────────────────────┐
│ 7. Applications                             │
├──────────────────────────────────────────────┤
│ 6. Brains                                   │
├──────────────────────────────────────────────┤
│ 5. Intelligence                             │
├──────────────────────────────────────────────┤
│ 4. Simulation                               │
├──────────────────────────────────────────────┤
│ 3. Decision                                 │
├──────────────────────────────────────────────┤
│ 2. Domain                                   │
├──────────────────────────────────────────────┤
│ 1. Infrastructure                           │
└──────────────────────────────────────────────┘
```

### Dependency rule

A layer may depend only on:

1. its own public interfaces,
2. the public interfaces of lower layers.

A lower layer must never import a higher layer.

Forbidden examples:

```text
Domain → Home Assistant
Decision → MQTT
Simulation → Fronius
Infrastructure → Brain
```

Allowed direction:

```text
Applications
    ↓
Brains
    ↓
Intelligence
    ↓
Simulation
    ↓
Decision
    ↓
Domain
    ↓
Infrastructure ports
```

Infrastructure implementations plug into ports defined by the inner layers. Concrete adapters are replaceable.

---

# 3. Layer 1 — Infrastructure

## Responsibility

Infrastructure communicates with the external world.

It reads and writes data, but it never makes business decisions.

Examples:

- Home Assistant
- MQTT
- Modbus
- REST APIs
- Fronius
- Wattpilot
- Daikin
- Omoda
- weather providers
- electricity price providers
- databases
- files
- clocks
- notification services

## Rules

Infrastructure may:

- read entity states,
- call external services,
- translate vendor payloads,
- persist events,
- publish telemetry,
- provide clocks and storage.

Infrastructure must not:

- optimize,
- decide priorities,
- calculate strategy,
- bypass validation,
- contain user policy,
- call Brains directly.

## Public contracts

```python
class StateSource:
    def read(self) -> RawSnapshot:
        ...

class CommandSink:
    def execute(self, command: Command) -> ExecutionResult:
        ...

class HistoryRepository:
    def append(self, event: DomainEvent) -> None:
        ...

class Clock:
    def now(self) -> datetime:
        ...
```

## Adapter principle

Vendor names belong only here.

```text
FroniusAdapter
WattpilotAdapter
DaikinAdapter
OmodaAdapter
HomeAssistantAdapter
```

The rest of HEOS must never depend on those names.

---

# 4. Layer 2 — Domain

## Responsibility

The Domain layer models the home as energy reality.

It contains no network code, no Home Assistant code, no vendor-specific code, and no side effects.

## Core models

```text
HouseState
DigitalTwin
PowerFlow
EnergyStore
VehicleState
ClimateState
PriceState
ForecastState
UserIntent
SafetyConstraints
OperatingPolicy
Capability
Decision
ActionPlan
DomainEvent
```

## HouseState

`HouseState` is the single immutable decision context.

```text
HouseState
├── DigitalTwin
├── UserIntent
├── SafetyConstraints
├── Forecasts
├── OperatingPolicy
├── Confidence
└── Timestamp
```

## Digital Twin

The Digital Twin represents what is true now.

It must be:

- immutable,
- vendor neutral,
- timestamped,
- confidence aware,
- replayable in tests,
- serializable.

## Capability model

HEOS optimizes capabilities, not devices.

A device is only one possible provider of a capability.

Examples:

```text
measure_power
produce_energy
store_electricity
store_heat
charge_vehicle
control_current
control_temperature
shift_load
export_energy
import_energy
```

Example:

```text
Wattpilot
└── capabilities:
    ├── charge_vehicle
    ├── control_current
    └── stop_charging
```

```text
Daikin
└── capabilities:
    ├── consume_energy
    ├── store_heat
    └── control_temperature
```

## Domain purity

Domain objects must be testable using plain Python without:

- internet,
- Home Assistant,
- MQTT,
- hardware,
- cloud credentials,
- operating-system services.

---

# 5. Layer 3 — Decision

## Responsibility

The Decision layer turns a valid `HouseState` into candidate decisions and selects the best safe action plan.

## Components

```text
Planner
Rule Engine
Policy Validator
Optimizer
Priority Resolver
Decision Engine
Explanation Engine
Action Plan Builder
```

## Pipeline

```text
HouseState
    ↓
Planner
    ↓
Objectives
    ↓
Rule Engine
    ↓
Candidate Plans
    ↓
Policy Validator
    ↓
Optimizer
    ↓
Selected Decision
    ↓
Explanation
```

## Decision object

Every decision must include:

```text
id
action
parameters
score
confidence
reasons
constraints_checked
valid_from
valid_until
source_brain
expected_effect
fallback
```

Example:

```json
{
  "action": "charge_vehicle",
  "parameters": {
    "current_a": 12
  },
  "confidence": 0.94,
  "score": 91.0,
  "reasons": [
    "Solar surplus is 2.9 kW",
    "EV SOC is below target",
    "Grid reserve remains protected"
  ],
  "valid_until": "2026-07-14T12:35:30Z"
}
```

## Mandatory rule

No Decision may be executed without:

1. a reason,
2. a confidence value,
3. a validity period,
4. successful policy validation.

---

# 6. Layer 4 — Simulation

## Responsibility

The Simulation layer evaluates possible futures before execution.

HEOS must not choose only the first valid action. It must compare scenarios.

## Scenario model

```text
Scenario
├── initial_state
├── proposed_actions
├── projected_states
├── cost
├── comfort
├── battery_wear
├── grid_impact
├── emissions
├── risk
└── confidence
```

## Example scenarios

```text
Scenario A
Charge EV now at 12 A

Scenario B
Wait 30 minutes

Scenario C
Heat water first, then charge EV

Scenario D
Export surplus
```

## Simulation horizon

Supported horizons:

- 15 minutes,
- 1 hour,
- 6 hours,
- 24 hours,
- user-defined horizon.

## Simulation output

```text
best_cost
best_comfort
lowest_grid_import
highest_self_consumption
lowest_battery_degradation
highest_confidence
```

## Safety

Simulation may suggest unsafe scenarios, but such scenarios must be rejected before selection.

Simulation never executes.

---

# 7. Layer 5 — Intelligence

## Responsibility

The Intelligence layer creates trusted predictions and learned models.

It answers:

- what is likely to happen,
- how reliable that forecast is,
- what patterns exist,
- how the current home differs from generic assumptions.

## Components

```text
Feature Extractor
Trend Estimator
Forecast Engine
Confidence Engine
House Memory
House DNA
Learning Engine
Anomaly Detector
Outcome Evaluator
```

## House Memory

House Memory stores observations and outcomes.

It contains:

- past states,
- past decisions,
- actual outcomes,
- forecast errors,
- recurring patterns,
- confidence changes.

## House DNA

House DNA is the learned model of one specific home.

```text
HouseDNA
├── Building Model
├── PV Model
├── Load Model
├── Climate Model
├── Vehicle Model
├── Occupancy Model
├── Price Response Model
├── Habit Model
└── Confidence Model
```

## Learning rule

HEOS learns only from measured outcomes.

It must record:

```text
prediction
decision
expected effect
actual effect
error
updated confidence
```

## Deterministic fallback

Machine learning is optional.

Every intelligence capability must have a deterministic fallback.

HEOS must continue operating safely if:

- internet fails,
- cloud AI is unavailable,
- a model cannot load,
- historical data is insufficient.

---

# 8. Layer 6 — Brains

## Responsibility

Brains are modular experts.

A Brain proposes decisions for one area, but does not execute actions.

Examples:

```text
SolarBrain
EVBrain
BatteryBrain
HeatPumpBrain
PriceBrain
WeatherBrain
ComfortBrain
GridBrain
WaterHeatingBrain
```

## Brain contract

```python
class Brain:
    brain_id: str
    version: str

    def evaluate(
        self,
        state: HouseState,
        intelligence: IntelligenceResult,
        scenarios: tuple[Scenario, ...],
    ) -> tuple[CandidateDecision, ...]:
        ...
```

## Brain rules

A Brain must:

- be deterministic for identical inputs,
- return immutable candidate decisions,
- explain every proposal,
- declare required capabilities,
- declare required data,
- expose confidence,
- remain side-effect free.

A Brain must not:

- call Home Assistant,
- call MQTT,
- call vendor APIs,
- execute actions,
- write directly to storage,
- bypass the Decision layer.

## Brain discovery

Brains are plugins discovered through metadata.

```text
brain_id
version
required_capabilities
required_features
supported_objectives
minimum_data_quality
```

---

# 9. Layer 7 — Applications

## Responsibility

Applications expose HEOS to users and external systems.

Examples:

- Home Assistant integration
- dashboard
- CLI
- REST API
- mobile app
- web UI
- voice assistant
- notifications
- diagnostic tools

Applications may:

- display state,
- display recommendations,
- accept user intent,
- request evaluation,
- approve decisions,
- show history,
- expose controls.

Applications must not contain decision logic.

## Example flow

```text
User selects:
"Charge as cheaply as possible before 07:00"

Application
    ↓
UserIntent
    ↓
HouseState
    ↓
Brains + Simulation + Decision
    ↓
Recommendation
    ↓
Application displays explanation
```

---

# 10. End-to-End Lifecycle

```text
1. Observe
2. Normalize
3. Build Digital Twin
4. Build HouseState
5. Analyze history
6. Predict
7. Generate scenarios
8. Ask Brains for candidates
9. Validate policies
10. Optimize
11. Select one decision
12. Explain
13. Request approval or execute
14. Observe actual result
15. Learn
16. Repeat
```

Compact form:

```text
Observe
  ↓
Remember
  ↓
Predict
  ↓
Simulate
  ↓
Decide
  ↓
Validate
  ↓
Execute
  ↓
Learn
  ↓
Repeat
```

---

# 11. Safety Architecture

## Safety hierarchy

```text
Human override
    ↓
Hard electrical constraints
    ↓
Device constraints
    ↓
Comfort constraints
    ↓
Economic optimization
```

Savings may never override safety.

## Mandatory safety controls

- main breaker limit,
- phase current limit,
- device current limit,
- battery SOC limits,
- temperature limits,
- stale-data blocking,
- unavailable-device blocking,
- command expiry,
- idempotency,
- rollback or safe fallback,
- manual override,
- dry-run mode.

## Execution modes

```text
Recommendation
Semi-automatic
Autopilot
```

Default mode:

```text
Recommendation
```

Autopilot requires:

- explicit user enablement,
- healthy Digital Twin,
- trusted data,
- validated decision,
- safe executor,
- audit logging.

---

# 12. Explainability Standard

Every action must answer:

```text
What did HEOS decide?
Why?
Based on which inputs?
With what confidence?
What alternatives were considered?
What constraints were checked?
What is the expected effect?
When will the decision expire?
```

Example:

```text
Decision:
Charge EV at 10 A

Why:
- 2.6 kW stable solar surplus
- EV SOC is 42%, target 80%
- house load is stable
- cloud risk is rising

Confidence:
93%

Alternatives:
- wait 30 minutes
- export surplus

Expected effect:
+2.3 kWh EV energy
0 W expected grid import

Valid for:
45 seconds
```

---

# 13. Data Ownership and Privacy

HEOS is local first.

The home owns:

- history,
- learned models,
- preferences,
- decisions,
- forecasts,
- device mappings.

Cloud services are optional.

No cloud dependency may be required for core safety or basic operation.

Sensitive household patterns must remain local unless the user explicitly enables export.

---

# 14. Repository Structure

Recommended structure:

```text
src/heos/
├── domain/
│   ├── house_state.py
│   ├── digital_twin.py
│   ├── decision.py
│   ├── capability.py
│   └── events.py
│
├── decision/
│   ├── planner.py
│   ├── rules.py
│   ├── optimizer.py
│   ├── validator.py
│   └── explanation.py
│
├── simulation/
│   ├── scenario.py
│   ├── engine.py
│   └── scoring.py
│
├── intelligence/
│   ├── features.py
│   ├── forecast.py
│   ├── confidence.py
│   ├── memory.py
│   └── house_dna.py
│
├── brains/
│   ├── base.py
│   ├── solar.py
│   ├── ev.py
│   ├── battery.py
│   └── climate.py
│
├── infrastructure/
│   ├── home_assistant/
│   ├── mqtt/
│   ├── storage/
│   └── providers/
│
└── applications/
    ├── cli/
    ├── api/
    └── home_assistant/
```

---

# 15. Testing Standard

Every layer must be independently testable.

Required test categories:

```text
unit
integration
contract
simulation
safety
regression
replay
```

## Minimum requirements

- identical input produces identical decision,
- stale data blocks execution,
- unsafe scenarios are rejected,
- adapters pass contract tests,
- Brains work without hardware,
- simulation results are reproducible,
- public APIs remain backward compatible or versioned.

---

# 16. Versioning

HEOS uses semantic versioning.

```text
MAJOR.MINOR.PATCH
```

Example:

```text
1.0.0
```

Architectural contracts are versioned separately where needed.

Breaking changes require:

- RFC,
- migration path,
- deprecation period,
- tests,
- changelog entry.

---

# 17. Non-Negotiable Principles

1. **Architecture first.**
2. **Safety before savings.**
3. **Every decision must have a reason.**
4. **Local first.**
5. **Vendor neutral.**
6. **Small core, powerful extensions.**
7. **Capabilities over devices.**
8. **Simulation before execution.**
9. **Humans retain final control.**
10. **Learning must never remove deterministic safety.**

---

# 18. Definition of HEOS

> HEOS is a local-first, explainable, modular operating system for residential energy intelligence.

It observes the home, builds a Digital Twin, learns the House DNA, predicts future conditions, simulates possible strategies, selects the best safe decision, explains it, executes it through replaceable capability adapters, and learns from the outcome.

---

# 19. Final Architecture Statement

```text
HEOS does not automate devices.

HEOS governs energy.
```
