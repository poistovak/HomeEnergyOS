# RFC-0003 — Future Scenario Planning 1.0

**Status:** Proposed  
**Milestone:** 9

## Principle

HEOS does not select an action directly.

HEOS first generates possible futures.

Each `FutureScenario` contains:

- planned actions,
- expected metrics,
- score,
- confidence,
- reasons,
- planning horizon.

## First implementation

The initial planner generates up to three futures:

1. charge EV from available surplus,
2. export available surplus,
3. keep the current state.

A blocked Energy Kernel produces only a blocked scenario.

## Separation of responsibilities

The Planner generates futures.

The Optimizer will later compare them using the user's goals.

The Executor will later realize only an approved future.
