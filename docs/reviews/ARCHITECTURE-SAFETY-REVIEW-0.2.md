# HEOS Architecture & Safety Review 0.2

## Verification result

Audit performed against the uploaded repository snapshot.

- Python package installation: passed
- Ruff: passed
- Pytest: 30 passed, 1 failed before the included fix
- Failure: `HomeAssistantSnapshotAdapter.collect()` used `vars()` on a
  `slots=True` dataclass, which has no `__dict__`

The included adapter fix uses `dataclasses.fields()` and `getattr()`.

## Critical

1. **Home Assistant adapter runtime failure** — fixed in this patch.
2. **Invalid `*.py.py` files remain in `src/heos/core/`**. They are not normal
   importable Python modules and should be removed after confirming they are
   obsolete.
3. **Generated cache files are present**. They must not be committed.

## Important

1. There are two Event Bus implementations:
   - `heos.core.events` — functional and tested
   - `heos.eventbus` — placeholder implementation with `pass`

   Keep `heos.core.events` as the canonical implementation for now. Remove or
   formally deprecate the placeholder package in a separate refactor.

2. There are parallel decision modules:
   - canonical early API in `heos.decision_engine`
   - a largely skeletal `heos.decision` package

   Do not expand both. Choose one canonical application layer before Milestone 5.

3. Two different HouseState models remain:
   - legacy `heos.state.HouseState`
   - canonical `heos.domain.house_state.HouseState`, exported through
     `heos.house_state`

   Keep the legacy model only as a documented compatibility adapter and plan
   its removal before version 1.0.

4. `src/heos/optimizer/objektive.py` contains a spelling inconsistency.
   Rename only in a dedicated refactor with import updates and tests.

## Safety review

- Live Home Assistant execution defaults to disabled: passed.
- Dry-run executor is the default: passed.
- Decision translation is separate from execution: passed.
- Required numeric HA states fail closed: passed.
- Core does not directly import Home Assistant infrastructure: passed.

## Recommended next commit

`🧹 Architecture & Safety Review 0.2`

Scope:

- apply the HA adapter fix,
- add `.gitignore`,
- remove caches and backup archives,
- remove obsolete `*.py.py` files,
- do not yet merge or rename decision/event packages.

After applying:

```powershell
py -m pip install -e ".[dev]"
py -m pytest -q
py -m ruff check .
```
