# opskarta

> OpsKarta — Operational map format for complex programs (plan‑as‑code).  
> OpsCarto — Operational cartography for programs: model once, render many views. *(synonym)*

**opskarta** — открытый формат данных (YAML/JSON) для *оперативной карты программы/проекта*: единого артефакта, в котором менеджер фиксирует свою актуальную интерпретацию структуры работ и зависимостей, а затем генерирует из неё сколько угодно представлений (Gantt, граф зависимостей, чек‑листы, отчёты и т.д.).

Ключевая идея: **«источник истины» — не Jira, не Confluence и не "в голове", а твой версионируемый файл‑план**.

## Specification Versions

| Версия | Статус | Описание |
|--------|--------|----------|
| [v1](specs/v1/) | Alpha | Начальная версия спецификации |

## Как это выглядит

Файл плана (`hello.plan.yaml`):

```yaml
version: 1

meta:
  id: hello-upgrade
  title: "Пример: обновление Git-сервиса"

statuses:
  not_started: { label: "Не начато",     color: "#9ca3af" }
  in_progress: { label: "В работе",      color: "#0ea5e9" }
  done:        { label: "Готово",        color: "#22c55e" }
  blocked:     { label: "Заблокировано", color: "#fecaca" }

nodes:
  root:
    title: "Обновление Git-сервиса"
    kind: summary
    status: in_progress

  prep:
    title: "Подготовка"
    kind: phase
    parent: root
    start: 2026-02-01
    duration: 10d
    status: in_progress

  rollout:
    title: "Раскатка"
    kind: phase
    parent: root
    after: [prep]
    duration: 5d
    status: not_started

  switch:
    title: "Переключение трафика"
    kind: task
    parent: rollout
    after: [rollout]
    duration: 1d
    status: not_started
    notes: |
      Критичный шаг. Нужен план отката.
```

Из этого плана можно генерировать Gantt-диаграммы, графы зависимостей, отчёты — см. [полную спецификацию v1](specs/v1/).

## Quick Start

Текущая рекомендуемая версия — **[v1](specs/v1/)**.

```bash
cd specs/v1

# Валидация примера
python tools/validate.py examples/hello/hello.plan.yaml examples/hello/hello.views.yaml

# Генерация Mermaid Gantt
python -m tools.render.mermaid_gantt \
    --plan examples/hello/hello.plan.yaml \
    --views examples/hello/hello.views.yaml \
    --view overview
```

## Documentation

- [Философия и метод](docs/method.md) — зачем нужна opskarta и как её использовать
- [Contributing](CONTRIBUTING.md) — как внести вклад в проект
- [Code of Conduct](CODE_OF_CONDUCT.md) — правила поведения
- [Security](SECURITY.md) — политика безопасности
- [Changelog](CHANGELOG.md) — история изменений

## License

Apache License 2.0 — см. файл [LICENSE](LICENSE).
