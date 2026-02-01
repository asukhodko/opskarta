# Example: Advanced (advanced program plan)

This example demonstrates full capabilities of the opskarta format using a platform modernization program with multiple work tracks.

## What It Demonstrates

### Plan File (`program.plan.yaml`)

- **Full meta section** — program identifier and title
- **Extended statuses** — 7 custom statuses with colors (not_started, planning, in_progress, review, done, blocked, on_hold)
- **Multiple tracks** — three parallel work directions (backend, frontend, infrastructure)
- **Deep hierarchy** — 4 nesting levels (summary → phase → epic → task)
- **Cross-track dependencies** — tasks depending on nodes from different tracks
- **All scheduling fields** — `start`, `duration`, `after`
- **Notes** — explanations for critical tasks
- **Extensions (x:)** — custom data (teams, risks, milestones)

### Views File (`program.views.yaml`)

- **Multiple views** — 5 different Gantt views
- **Different detail levels** — from program overview to detailed track plans
- **Calendar exclusions** — weekends and holidays
- **Critical path view** — focus on key dependencies

## Files

| File | Description |
|------|-------------|
| `program.plan.yaml` | Modernization program plan with three tracks and 30+ nodes |
| `program.views.yaml` | Five Gantt views for different audiences |

## Plan Structure

```
program (Platform Modernization Q1-Q2 2026)
│
├── backend (Backend)
│   ├── api-gateway (API Gateway)
│   │   ├── gateway-design
│   │   ├── gateway-impl
│   │   └── gateway-testing
│   └── microservices (Microservices Decomposition)
│       ├── user-service
│       ├── order-service
│       └── notification-service
│
├── frontend (Frontend)
│   ├── design-system (Design System)
│   │   ├── ds-tokens
│   │   ├── ds-components
│   │   └── ds-docs
│   └── ui-migration (UI Migration)
│       ├── migrate-auth
│       ├── migrate-dashboard
│       ├── migrate-settings
│       └── ui-e2e-tests
│
├── infrastructure (Infrastructure)
│   ├── k8s (Kubernetes Migration)
│   │   ├── k8s-cluster
│   │   ├── k8s-helm
│   │   └── k8s-ci-cd
│   └── monitoring (Monitoring System)
│       ├── prometheus
│       ├── logging
│       └── alerting
│
├── integration-testing (Integration Testing)
└── release (Release v2.0)
```

## Views

| View | Purpose |
|------|---------|
| `overview` | Full program overview for leadership |
| `backend-detail` | Detailed backend team plan |
| `frontend-detail` | Detailed frontend team plan |
| `infrastructure-detail` | Detailed infrastructure team plan |
| `critical-path` | Critical path to release |

## Usage

### Validation

```bash
cd specs/v1
python tools/validate.py en/examples/advanced/program.plan.yaml en/examples/advanced/program.views.yaml
```

### Generate Mermaid Gantt

```bash
cd specs/v1

# Overview view
python -m tools.render.plan2gantt \
  --plan en/examples/advanced/program.plan.yaml \
  --views en/examples/advanced/program.views.yaml \
  --view overview

# Detailed backend plan
python -m tools.render.plan2gantt \
  --plan en/examples/advanced/program.plan.yaml \
  --views en/examples/advanced/program.views.yaml \
  --view backend-detail

# Critical path
python -m tools.render.plan2gantt \
  --plan en/examples/advanced/program.plan.yaml \
  --views en/examples/advanced/program.views.yaml \
  --view critical-path
```

## Example Features

### Extensions (x:)

The example demonstrates using the `x:` section for storing custom data:

```yaml
x:
  team_assignments:
    backend: ["alice", "bob", "charlie"]
    frontend: ["diana", "eve"]
    infrastructure: ["frank", "grace"]
  
  risk_register:
    - id: R001
      description: "API Gateway delivery delay"
      probability: medium
      impact: high
      mitigation: "Parallel mock service development"
  
  milestones:
    - date: 2026-02-15
      name: "API Gateway Ready"
      nodes: [gateway-testing]
```

This data is ignored by standard tools but can be used by custom renderers and integrations.

### Cross-track Dependencies

Node `integration-testing` depends on completion of work in all three tracks:

```yaml
integration-testing:
  after: [gateway-testing, ui-e2e-tests, k8s-ci-cd]
```

This allows modeling complex dependencies between teams.

### Calendar Exclusions

Views file includes exclusions for holidays:

```yaml
excludes: ["weekends", "2026-02-23", "2026-03-08", "2026-05-01", "2026-05-09"]
```

## When to Use

This example is useful as a reference for:

- Planning large programs with multiple teams
- Modeling complex dependencies between tracks
- Creating views for different audiences
- Using extensions for custom data

For simpler projects see [minimal](../minimal/) and [hello](../hello/) examples.
