# opskarta v3, коротко

## Основа

Файл или набор файлов содержит:

- `version: 3`
- `meta`
- `statuses`
- `nodes`
- `schedule`
- `execution`
- `views`
- `profiles`
- `x`

`nodes` описывает структуру работ и зависимости. Даты находятся только в `schedule.nodes`. Фактическое выполнение и прогресс находятся в `execution.nodes`.

## Новое в v3

### `x.exec`

Стабилизированный профиль для управленческого слоя:

- `program` — обещанная дата, ближайшая цель, критерий успеха к следующему синку;
- `blocks` — крупные управленческие блоки;
- `edges` — связи между блоками (`required`, `risk_reduction`, `context`);
- `views` — executive-представления.

Блок задаёт ровно одно из:

- `scope_nodes` — область из обычных `nodes`;
- `source_blocks` — агрегация других executive-блоков.

Частые поля блока: `title`, `target_gate`, `kind`, `progress_override`, `mgmt.health`, `mgmt.sync_note`, `mgmt.next_sync_goal`, `mgmt.owner`.

### Views

Дополнения к обычным views:

- `window_start`, `window_finish` — календарное окно для Gantt-вывода;
- `lanes.*.expand_descendants: leaves` — вывести leaf-потомков указанных lane-узлов;
- `where.x_ops_attention_class` — фильтр по `nodes.*.x.ops.attention_class`.

## CLI

```bash
python -m specs.v3.tools.cli validate plan.yaml
python -m specs.v3.tools.cli render gantt plan.yaml --view release-window --style status
python -m specs.v3.tools.cli render executive plan.yaml exec.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section status
python -m specs.v3.tools.cli update-markdown plan.md exec.md
```
