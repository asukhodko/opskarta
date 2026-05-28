# opskarta Specification v3

v3 keeps the v2 base model: nodes describe work, `schedule` describes dates, `execution` describes factual progress. The new part is the operational layer around real rollouts: short executive maps, Markdown sections for sync documents, clipped Gantt windows, and reusable Markdown refresh tooling.

## Key Additions

| Area | What changed |
|------|--------------|
| Executive overlay | `x.exec` is now a documented built-in profile for management blocks, gates, health, owners, and executive views. |
| Executive renderers | `render executive` produces Mermaid flowcharts; `render executive-report` produces status/tracks/signals Markdown sections. |
| Gantt windows | Views may define `window_start` / `window_finish`; tasks are clipped to the visible window. |
| Lane expansion | Gantt lanes may use `expand_descendants: leaves` to keep views compact while rendering leaf work. |
| Ops filter | `where.x_ops_attention_class` filters by `node.x.ops.attention_class`. |
| Markdown refresh | `update-markdown` refreshes generated Mermaid or Markdown blocks from commands embedded in docs. |

## Structure

```
specs/v3/
├── ru/                     # Russian docs, primary
├── en/                     # English docs
├── schemas/                # JSON Schemas
├── tests/                  # Test suite
└── tools/                  # Reference implementation
```

## Quick Start

```bash
python -m specs.v3.tools.cli validate specs/v3/ru/examples/executive/release.plan.yaml
python -m specs.v3.tools.cli render executive specs/v3/ru/examples/executive/release.plan.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report specs/v3/ru/examples/executive/release.plan.yaml --section status
python -m specs.v3.tools.cli render gantt specs/v3/ru/examples/executive/release.plan.yaml --view release-window --style status
```

## Migration

See [ru/MIGRATION.md](ru/MIGRATION.md) or [en/MIGRATION.md](en/MIGRATION.md). For most v2 users the minimum migration is changing `version: 2` to `version: 3`; the new fields are opt-in.
