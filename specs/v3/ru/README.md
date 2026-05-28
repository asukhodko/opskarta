# opskarta v3

**Статус:** Alpha

v3 оставляет рабочую основу v2: структура работ живёт в `nodes`, календарь в `schedule`, фактическое выполнение в `execution`. Новое в v3 — операционная обвязка для живых программ: управленческие карты, короткие Markdown-сводки, оконные Gantt-срезы и штатное обновление сгенерированных блоков в документах.

## Что добавилось

| Возможность | Зачем нужна |
|-------------|-------------|
| `x.exec` | Собрать верхнеуровневые блоки программы, ближайшие ворота, health, владельцев и ручные заметки для синков. |
| `render executive` | Получить Mermaid-карту для руководительского или координационного среза. |
| `render executive-report` | Получить Markdown-секции `status`, `tracks`, `signals` для постоянного документа. |
| `window_start` / `window_finish` | Показать только нужное календарное окно на Gantt, не обрезая исходный план. |
| `expand_descendants: leaves` | В lane указать крупный блок, а вывести его leaf-задачи. |
| `where.x_ops_attention_class` | Отбирать узлы по `node.x.ops.attention_class`, например `date_holder` или `tail`. |
| `update-markdown` | Перегенерировать блоки в `.md` по командам из комментариев `Перегенерить`. |

## Быстрый пример

```bash
python -m specs.v3.tools.cli validate specs/v3/ru/examples/executive/release.plan.yaml
python -m specs.v3.tools.cli render executive specs/v3/ru/examples/executive/release.plan.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report specs/v3/ru/examples/executive/release.plan.yaml --section status
python -m specs.v3.tools.cli render gantt specs/v3/ru/examples/executive/release.plan.yaml --view release-window --style status
```

## Файлы

- [SPEC.md](SPEC.md) — полная спецификация.
- [SPEC.min.md](SPEC.min.md) — короткая памятка.
- [MIGRATION.md](MIGRATION.md) — переход с v2 на v3.
- [examples/executive/](examples/executive/) — пример `x.exec` и оконного Gantt.
