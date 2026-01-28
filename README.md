# opskarta

> OpsKarta — Operational map format for complex programs (plan‑as‑code).  
> OpsCarto — Operational cartography for programs: model once, render many views. *(synonym)*

**opskarta** — открытый формат данных (YAML/JSON) для *оперативной карты программы/проекта*: единого артефакта, в котором менеджер фиксирует свою актуальную интерпретацию структуры работ и зависимостей, а затем генерирует из неё сколько угодно представлений (Gantt, граф зависимостей, чек‑листы, отчёты и т.д.).

Ключевая идея: **«источник истины» — не Jira, не Confluence и не "в голове", а твой версионируемый файл‑план**.

## Specification Versions

| Версия | Статус | Описание |
|--------|--------|----------|
| [v1](specs/v1/) | Alpha | Начальная версия спецификации |

## Quick Start

Текущая рекомендуемая версия — **[v1](specs/v1/)**.

```bash
cd specs/v1

# Валидация примера
python tools/validate.py examples/hello/hello.plan.yaml examples/hello/hello.views.yaml

# Генерация Mermaid Gantt
python -m tools.render.mermaid_gantt --plan examples/hello/hello.plan.yaml --views examples/hello/hello.views.yaml --view overview
```

## Documentation

- [Философия и метод](docs/method.md) — зачем нужна opskarta и как её использовать
- [Contributing](CONTRIBUTING.md) — как внести вклад в проект

## License

Apache License 2.0 — см. файл [LICENSE](LICENSE).
