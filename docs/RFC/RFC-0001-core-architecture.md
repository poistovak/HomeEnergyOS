# RFC-0001 — HEOS Core Architecture

**Status:** Draft  
**Codename:** Genesis

HEOS is decision-oriented, not entity-oriented.

```text
Device adapters
      ↓
Normalized HouseState
      ↓
Brains
      ↓
Decision Engine
      ↓
Safety Layer
      ↓
Action Layer
```

Every decision must contain a reason code, explanation, confidence and validity period.
AI must never bypass the Safety Layer.
