# Profiles (Extension Namespaces)

Profiles declare extension namespaces used in `x` fields throughout the plan.

## Concept

The `x` field on nodes and at the top level holds arbitrary extension data. Profiles provide a way to document and validate which namespaces are in use.

## Profile Structure

```yaml
profiles:
  - id: "opskarta.ai-dev"
    version: 1
    namespace: "ai"
```

## Profile Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Profile identifier (e.g., `"opskarta.ai-dev"`) |
| `version` | integer | Profile schema version |
| `namespace` | string | Key under `x` where profile data lives |

## Namespace Convention

The `namespace` value determines the key used in `x` fields:

```yaml
profiles:
  - id: "opskarta.ai-dev"
    version: 1
    namespace: "ai"

nodes:
  task1:
    title: "Implement feature"
    x:
      ai:
        complexity: high
        suggested_approach: "Use pattern X"
```

## Rules

- `namespace` MUST match `^[a-zA-Z_][a-zA-Z0-9_]*$`.
- Two profiles with the same `namespace` — **error**.
- `id`, `version`, and `namespace` are all **required** fields.

## Example

```yaml
version: 3

profiles:
  - id: "opskarta.ai-dev"
    version: 1
    namespace: "ai"
  - id: "mycompany.pm"
    version: 3
    namespace: "pm"

nodes:
  task1:
    title: "Backend API"
    x:
      ai:
        complexity: medium
      pm:
        assignee: "john"
        sprint: 5
```
