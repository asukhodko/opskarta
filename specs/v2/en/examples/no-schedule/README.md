# Example: No-schedule (plan without schedule)

This example demonstrates that an opskarta v2 plan can be **valid and useful without a `schedule` block** — just structure, hierarchy, dependencies, and effort estimates.

## What It Demonstrates

### Key v2 Concept: Overlay Schedule

In v2, calendar planning is an **optional layer** applied on top of work structure. A plan without `schedule`:

- ✅ Is fully valid
- ✅ Can be rendered as tree, list, deps
- ✅ Effort metrics are computed (rollup, gap)
- ❌ Cannot render Gantt (no dates)

### When to Use a Plan Without Schedule

| Scenario | Description |
|----------|-------------|
| **Product Backlog** | Feature list with priorities and estimates, no dates |
| **Roadmap** | Strategic product vision |
| **Early Planning** | Decomposition and estimation before scheduling |
| **Scope Assessment** | Understanding work volume before planning |
| **Grooming** | Refining requirements and estimates |

## Files

| File | Description |
|------|-------------|
| `backlog.plan.yaml` | Complete mobile app backlog plan |

## Structure

```
backlog (Mobile App Backlog) [100 sp]
│
├── onboarding (User Onboarding) [21 sp]
│   ├── welcome-screens [5 sp]
│   ├── registration [8 sp]
│   ├── profile-setup [5 sp]
│   └── tutorial [3 sp]
│
├── core-features (Core Features) [34 sp]
│   ├── dashboard [8 sp]
│   ├── search [5 sp]
│   ├── notifications [8 sp]
│   ├── settings [5 sp]
│   └── offline-mode [8 sp]
│
├── social (Social Features) [21 sp]
│   ├── user-profiles [5 sp]
│   ├── friends [8 sp]
│   ├── sharing [5 sp]
│   └── comments [3 sp]
│
├── monetization (Monetization) [13 sp]
│   ├── premium-subscription [8 sp]
│   └── in-app-purchases [5 sp]
│
└── tech-debt (Technical Debt) [11 sp]
    ├── refactor-auth [3 sp]
    ├── improve-performance [5 sp]
    └── update-dependencies [3 sp]
```

## Usage

```bash
cd specs/v2

# Validate
python -m tools.cli validate en/examples/no-schedule/backlog.plan.yaml

# Render tree
python -m tools.cli render tree en/examples/no-schedule/backlog.plan.yaml

# Render list
python -m tools.cli render list en/examples/no-schedule/backlog.plan.yaml

# Render dependencies
python -m tools.cli render deps en/examples/no-schedule/backlog.plan.yaml
```

## See Also

- [Nodes Specification](../../spec/20-nodes.md)
- [Schedule Specification](../../spec/30-schedule.md)
- [multi-file example](../multi-file/) — plan with schedule
- [partial-schedule example](../partial-schedule/) — partial schedule
