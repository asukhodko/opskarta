# Migrating from opskarta v2 to v3

v3 keeps the v2 data model. If your plan only uses `nodes`, `schedule`, `execution`, and `views`, migration is mostly mechanical.

## Minimal Migration

1. Change `version: 2` to `version: 3` in every fragment.
2. Validate with v3 tools:

```bash
python -m specs.v3.tools.cli validate *.plan.yaml
```

3. In Markdown docs, replace `python -m specs.v2.tools.cli ...` commands with `python -m specs.v3.tools.cli ...`.

All new v3 fields are opt-in. Existing v2 views continue to work when they were valid v2 views.

## What to Add Next

### Executive overlay: `x.exec`

If you already maintain manual sync summaries, move them into `x.exec`:

```yaml
x:
  exec:
    program:
      committed_date: "2026-06-04"
      nearest_goal: "Pass the window without rollback."
    blocks:
      cutover:
        title: "Cutover window"
        scope_nodes: [cutover]
        target_gate: gate-done
        mgmt:
          health: yellow
          sync_note: "The main risk is smoke testing."
    views:
      exec-top:
        blocks: [cutover]
```

Render it:

```bash
python -m specs.v3.tools.cli render executive plan.yaml exec.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section status
```

### Gantt Windows

If a Gantt chart is too wide, add boundaries:

```yaml
views:
  release-window:
    window_start: "2026-06-01"
    window_finish: "2026-06-10"
```

The renderer clips output only; source schedule dates remain unchanged.

### Lane Expansion

```yaml
views:
  release-window:
    lanes:
      main:
        title: "Main path"
        expand_descendants: leaves
        nodes: [cutover]
```

This keeps the view config short while rendering leaf tasks.

### Operational Attention Filter

```yaml
nodes:
  switch:
    title: "Switch traffic"
    x:
      ops:
        attention_class: date_holder

views:
  date-holders:
    where:
      x_ops_attention_class: [date_holder]
```

## Markdown Refresh

v3 includes a standard command for refreshing generated Markdown blocks:

```bash
python -m specs.v3.tools.cli update-markdown plan.md exec.md
```

It finds blocks like:

````markdown
<!--
Перегенерить:
python -m specs.v3.tools.cli validate plan.yaml exec.yaml
python -m specs.v3.tools.cli render executive plan.yaml exec.yaml --view exec-top
-->
```mermaid
old
```
````

and replaces the next Mermaid block or content between `<!-- GENERATED:START -->` and `<!-- GENERATED:END -->`.

## When Staying on v2 Is Fine

If your plan is only a source for simple Gantt/list/tree renders and you do not need executive maps or generated sync docs, v2 is still fine. v3 is useful once the plan becomes the working center for syncs, leadership views, and living Markdown documents.
