# opskarta Specification v1 (Draft)

This specification describes the *minimal* compatible field set of the opskarta format.

- Serialization format: **YAML** (recommended) or JSON.
- Versioning: `version` field at document root.
- Node identifiers: string keys in the `nodes:` map.

> Status: **Draft**. The spec is intentionally starting small and extensible.

## Core vs Non-core

The specification distinguishes between **core** (normative) and **non-core** (informative/extensions) parts:

| Category | Description | Tool Implementation Requirement |
|----------|-------------|--------------------------------|
| **Core** | Basic format semantics, scheduling algorithms, validation rules | MUST implement |
| **Non-core** | Extensions (`x:` namespace), renderer profiles, additional view fields | MAY implement |

### Core Components

- Structure of `*.plan.yaml` and `*.views.yaml` files
- Node fields: `title`, `kind`, `status`, `parent`, `after`, `start`, `finish`, `duration`, `milestone`
- Date computation: `finish`, `start from after`
- Calendar exclusions: `"weekends"` and `YYYY-MM-DD` dates in `excludes`
- Default value: `duration = 1d` for scheduled nodes
- Validation rules and referential integrity

### Non-core Components

- Extensions via `x:` namespace (e.g., `x.scheduling.anchor_to_parent_start`)
- Renderer profiles (Mermaid Gantt, others)
- View fields for specific renderers (`date_format`, `axis_format`, `tick_interval`)
- Other values in `excludes` (not `"weekends"` and not `YYYY-MM-DD` dates)
- Default status colors
