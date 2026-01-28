# Примеры opskarta v1

Этот каталог содержит примеры файлов плана и представлений разной сложности.

## Примеры

| Пример | Описание | Файлы |
|--------|----------|-------|
| [minimal/](minimal/) | Минимальный валидный план | только `.plan.yaml` |
| [hello/](hello/) | Базовый пример с планом и представлениями | `.plan.yaml` + `.views.yaml` |
| [advanced/](advanced/) | Продвинутый пример с несколькими треками | `.plan.yaml` + `.views.yaml` |

## Как использовать

Все примеры можно валидировать и рендерить с помощью [референсных инструментов](../tools/):

```bash
cd specs/v1

# Валидация
python tools/validate.py examples/hello/hello.plan.yaml examples/hello/hello.views.yaml

# Генерация Gantt
python -m tools.render.mermaid_gantt \
    --plan examples/hello/hello.plan.yaml \
    --views examples/hello/hello.views.yaml \
    --view overview
```

## См. также

- [Полная спецификация](../SPEC.md)
- [JSON Schema](../schemas/)
