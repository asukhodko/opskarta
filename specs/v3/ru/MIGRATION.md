# Миграция с opskarta v2 на v3

v3 совместима с базовой моделью v2. Если у вас обычный v2-план с `nodes`, `schedule`, `execution` и `views`, минимальная миграция почти механическая.

## Минимальный переход

1. Замените `version: 2` на `version: 3` во всех фрагментах.
2. Запустите проверку:

```bash
python -m specs.v3.tools.cli validate *.plan.yaml
```

3. Если в Markdown-документах были команды `python -m specs.v2.tools.cli ...`, замените их на `python -m specs.v3.tools.cli ...`.

Остальные поля v3 опциональны. Старые v2-представления продолжат работать, если они валидны по v2.

## Что можно добавить после миграции

### Управленческий слой `x.exec`

Если вокруг плана уже есть ручные сводки для синков, перенесите их в `x.exec`:

```yaml
x:
  exec:
    program:
      committed_date: "2026-06-04"
      nearest_goal: "Пройти окно без отката."
    blocks:
      cutover:
        title: "Окно переключения"
        scope_nodes: [cutover]
        target_gate: gate-done
        mgmt:
          health: yellow
          sync_note: "Главный риск сейчас в smoke-проверках."
    views:
      exec-top:
        blocks: [cutover]
```

Рендер:

```bash
python -m specs.v3.tools.cli render executive plan.yaml exec.yaml --view exec-top
python -m specs.v3.tools.cli render executive-report plan.yaml exec.yaml --section status
```

### Оконные Gantt-срезы

Если старый Gantt стал слишком широким, добавьте границы:

```yaml
views:
  release-window:
    window_start: "2026-06-01"
    window_finish: "2026-06-10"
```

Рендерер покажет только задачи, попадающие в окно, и обрежет задачи на границе окна только в выводе.

### Крупные lane без ручного списка leaf-задач

```yaml
views:
  release-window:
    lanes:
      main:
        title: "Основной путь"
        expand_descendants: leaves
        nodes: [cutover]
```

Так можно держать view коротким, а выводить конкретные leaf-задачи.

### Фильтр операционного внимания

```yaml
nodes:
  switch:
    title: "Переключить трафик"
    x:
      ops:
        attention_class: date_holder

views:
  date-holders:
    where:
      x_ops_attention_class: [date_holder]
```

## Markdown-регенерация

В v3 скрипт обновления Markdown стал штатной командой:

```bash
python -m specs.v3.tools.cli update-markdown plan.md exec.md
```

Команда ищет блоки вида:

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

и заменяет следующий Mermaid-блок или содержимое между `<!-- GENERATED:START -->` / `<!-- GENERATED:END -->`.

## Когда не надо мигрировать

Если план используется только как v2-источник для простого Gantt/list/tree и не нужен управленческий слой, можно остаться на v2. v3 полезна там, где план уже стал рабочим центром для синков, руководительских срезов и живых Markdown-документов.
