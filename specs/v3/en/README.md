# opskarta v3

**Status:** Alpha

v3 keeps the v2 foundation: work structure in `nodes`, calendar planning in `schedule`, and factual progress in `execution`. The new layer is operational: executive maps, Markdown report sections, clipped Gantt windows, and a built-in Markdown refresh command.

## What's New

| Feature | Why it exists |
|---------|---------------|
| `x.exec` | Describe program blocks, gates, health, owners, and sync notes. |
| `render executive` | Produce a Mermaid executive flowchart. |
| `render executive-report` | Produce Markdown sections: `status`, `tracks`, `signals`. |
| `window_start` / `window_finish` | Show only a useful Gantt time window without changing source dates. |
| `expand_descendants: leaves` | Put a large node into a lane and render its leaf tasks. |
| `where.x_ops_attention_class` | Filter by `node.x.ops.attention_class`, such as `date_holder` or `tail`. |
| `update-markdown` | Refresh generated blocks in `.md` files from embedded commands. |

## Quick Example

```bash
python -m specs.v3.tools.cli validate specs/v3/en/examples/executive/release.plan.yaml
python -m specs.v3.tools.cli render executive specs/v3/en/examples/executive/release.plan.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report specs/v3/en/examples/executive/release.plan.yaml --section status --lang en
python -m specs.v3.tools.cli render gantt specs/v3/en/examples/executive/release.plan.yaml --view release-window --style status
```

## Files

- [SPEC.md](SPEC.md) — full specification.
- [SPEC.min.md](SPEC.min.md) — compact full-spec summary designed to fit into an LLM context.
- [V3_VS_V2.md](V3_VS_V2.md) — practical benefits and changes compared with v2.
- [MIGRATION.md](MIGRATION.md) — v2 to v3 migration guide.
- [examples/executive/](examples/executive/) — `x.exec` and Gantt window example.
