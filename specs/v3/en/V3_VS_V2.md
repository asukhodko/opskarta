# opskarta v3 vs v2

This document explains the practical difference between opskarta v2 and v3. It focuses on why v3 exists, what changed, and when the upgrade is worth it. For mechanical migration steps, see [MIGRATION.md](MIGRATION.md).

## Short Version

v3 is **v2 plus an official operational/executive layer**.

The v2 breakthrough was the separation of work structure from calendar planning:

- `nodes` describe work and dependencies;
- `schedule` adds dates only where calendar planning is needed;
- `views` render different slices of the same source.

v3 keeps that foundation and adds the layer needed when the plan becomes a live program artifact: executive maps, status sections, Gantt windows, operational filters, and Markdown refresh tooling.

## What Stays the Same

| Area | v2 behavior kept in v3 |
|------|-------------------------|
| Work model | Work is still defined in `nodes`. |
| Schedule overlay | Dates still live in `schedule.nodes`, not in `nodes`. |
| Optional schedule | A plan without `schedule` is still valid. |
| Views | Views select and render work; they do not compute schedule. |
| Execution overlay | `execution.nodes` still records factual progress. |
| Multi-file plans | Plan fragments still merge into one Merged Plan. |

This is why most valid v2 plans can move to v3 by changing `version: 2` to `version: 3` and running v3 validation.

## What v3 Adds

| Area | v2 | v3 | Practical advantage |
|------|----|----|---------------------|
| Management layer | Use custom `x` data or external docs. | Built-in `x.exec` profile. | Program status becomes structured and renderable. |
| Executive map | Not standard. | `render executive` emits Mermaid flowcharts from `x.exec.views`. | One source can produce a leadership or sync map. |
| Status report | Not standard. | `render executive-report` emits `status`, `tracks`, and `signals`. | Reusable Markdown status sections replace manual summaries. |
| Gantt focus | Views can filter, but large timelines remain noisy. | `window_start` / `window_finish` clip Gantt output. | A long plan can show only the relevant calendar window. |
| Lane maintenance | Lanes list specific nodes. | `expand_descendants: leaves` can expand large lane nodes. | Views stay short while rendering concrete leaf work. |
| Operational filters | Core filters cover kind/status/schedule/parent. | `where.x_ops_attention_class` filters by `node.x.ops.attention_class`. | Date holders, tails, and other operational classes can be selected directly. |
| Markdown workflow | External scripts or manual copy/paste. | `update-markdown` is a standard command. | Living docs can refresh generated blocks from embedded commands. |
| Report language | Not applicable. | `executive-report --lang ru|en`. | Built-in report labels and date formats fit Russian or English documents. |

## Why This Matters

v2 is excellent for a clean plan-as-code model. It answers:

- What is the work?
- How does it depend on other work?
- Which parts are scheduled?
- How can I render this as tree/list/deps/Gantt?

v3 answers the next operational questions:

- Which blocks matter for the next sync?
- What is the committed date and current forecast?
- Which gate is closest?
- Which track is yellow or red, and why?
- Which tasks hold the date?
- Which slice of the Gantt should be shown to people right now?
- How do generated diagrams and status sections stay fresh inside Markdown documents?

The change is not just extra syntax. It turns the plan from a planning source into a repeatable status and coordination surface.

## When v3 Is a Real Upgrade

Use v3 when at least one of these is true:

- the plan is used in recurring syncs;
- there are leadership or stakeholder status updates;
- a full Gantt chart is too wide for day-to-day decisions;
- you already keep manual status summaries next to the plan;
- you need a short map of gates, owners, health, and blockers;
- generated diagrams or report sections live inside Markdown docs;
- operational labels such as `date_holder` or `tail` are useful for filtering.

In these cases, v3 reduces duplication: the same structured source can drive validation, Gantt windows, executive maps, and status text.

## When v2 Is Still Fine

Stay on v2 when the plan is only used for simple plan-as-code workflows:

- tree/list/deps renders;
- a normal Gantt view;
- backlog and schedule separation;
- no executive map;
- no generated status report;
- no living Markdown refresh workflow.

v3 should not be treated as a forced replacement for v2. It is heavier because it covers a broader operational surface.

## Migration Impact

For ordinary v2 plans, migration is intentionally small:

1. Change `version: 2` to `version: 3`.
2. Run:

```bash
python -m specs.v3.tools.cli validate *.plan.yaml
```

3. Keep existing v2-style `nodes`, `schedule`, `execution`, and `views` if they validate.
4. Add v3 features only where they provide value.

The new v3 fields are opt-in. A plan does not need `x.exec`, Gantt windows, lane expansion, or Markdown refresh to be valid v3.

## Conceptual Summary

| Version | Main value |
|---------|------------|
| v2 | Clean separation of work structure, schedule, views, and execution. |
| v3 | v2 foundation plus structured operational reporting and executive coordination. |

If v2 is the plan as code, v3 is the plan as a living operational map.
