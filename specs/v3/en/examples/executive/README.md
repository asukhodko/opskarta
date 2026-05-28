# Executive example

This example shows the practical v3 additions:

- the `x.exec` management layer with blocks, edges, and executive views;
- Gantt clipping via `window_start` / `window_finish`;
- lane expansion to leaf nodes with `expand_descendants: leaves`;
- filtering by `node.x.ops.attention_class`.

Validate and render:

```bash
python -m specs.v3.tools.cli validate specs/v3/en/examples/executive/release.plan.yaml
python -m specs.v3.tools.cli render executive specs/v3/en/examples/executive/release.plan.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report specs/v3/en/examples/executive/release.plan.yaml --section status --lang en
python -m specs.v3.tools.cli render gantt specs/v3/en/examples/executive/release.plan.yaml --view release-window --style status
```
