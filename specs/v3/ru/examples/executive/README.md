# Executive example

Этот пример показывает новые практические возможности v3:

- управленческий слой `x.exec` с блоками, рёбрами и отдельными представлениями;
- Gantt-окно через `window_start` / `window_finish`;
- разворачивание lane до leaf-узлов через `expand_descendants: leaves`;
- фильтр по `node.x.ops.attention_class`.

Проверить и отрендерить:

```bash
python -m specs.v3.tools.cli validate specs/v3/ru/examples/executive/release.plan.yaml
python -m specs.v3.tools.cli render executive specs/v3/ru/examples/executive/release.plan.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report specs/v3/ru/examples/executive/release.plan.yaml --section status
python -m specs.v3.tools.cli render gantt specs/v3/ru/examples/executive/release.plan.yaml --view release-window --style status
```
