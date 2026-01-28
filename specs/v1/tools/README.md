# Референсные инструменты opskarta v1

Этот каталог содержит референсные инструменты для работы с форматом opskarta v1.
Инструменты автономны и не требуют установки пакета.

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Инструменты

### validate.py — Валидатор

Валидирует файлы плана и представлений на соответствие спецификации.

**Использование:**

```bash
# Валидация плана
python validate.py plan.yaml

# Валидация плана и представлений
python validate.py plan.yaml views.yaml

# Валидация через JSON Schema (требует jsonschema)
python validate.py --schema plan.yaml

# Указание пользовательских схем
python validate.py --schema --plan-schema custom.schema.json plan.yaml
```

**Уровни валидации:**

1. **Синтаксис** — корректность YAML
2. **Схема** — соответствие JSON Schema (опционально, с флагом `--schema`)
3. **Семантика** — ссылочная целостность, бизнес-правила

**Проверяемые правила:**

- Обязательные поля (`version`, `nodes`, `title` для узлов)
- Ссылочная целостность (`parent`, `after`, `status`)
- Отсутствие циклических зависимостей
- Формат полей планирования (`start`, `duration`)
- Соответствие `project` и `meta.id` для views

### build_spec.py — Сборщик спецификации

Собирает части спецификации из `spec/` в единый файл `SPEC.md`.

**Использование:**

```bash
# Генерация SPEC.md
python build_spec.py

# Проверка актуальности SPEC.md (для CI/CD)
python build_spec.py --check
```

**Алгоритм работы:**

1. Находит все `*.md` файлы в `spec/` с форматом имени `NN-*.md`
2. Сортирует по числовому префиксу
3. Извлекает заголовки первого уровня для оглавления
4. Собирает в единый файл с автоматическим оглавлением

### render/mermaid_gantt.py — Рендерер Mermaid Gantt

Генерирует диаграммы Gantt в формате Mermaid на основе файла плана и представлений.

**Использование:**

```bash
# Рендеринг диаграммы в stdout
python -m render.mermaid_gantt --plan plan.yaml --views views.yaml --view overview

# Сохранение в файл
python -m render.mermaid_gantt --plan plan.yaml --views views.yaml --view overview --output gantt.md

# Список доступных представлений
python -m render.mermaid_gantt --plan plan.yaml --views views.yaml --list-views
```

**Возможности:**

- Автоматическое вычисление дат на основе зависимостей (`after`)
- Поддержка исключения выходных дней (`excludes: weekends`)
- Цветовая кодировка статусов задач
- Эмодзи для визуального различения статусов

## Зависимости

| Зависимость | Версия | Назначение | Обязательность |
|-------------|--------|------------|----------------|
| PyYAML | ≥6.0 | Парсинг YAML файлов | Обязательно |
| jsonschema | ≥4.0 | Валидация через JSON Schema | Опционально |

## Примеры

Примеры файлов плана и представлений находятся в каталоге [`../examples/`](../examples/):

- [`minimal/`](../examples/minimal/) — минимальный пример (только план)
- [`hello/`](../examples/hello/) — базовый пример с планом и представлениями
- [`advanced/`](../examples/advanced/) — продвинутый пример с несколькими треками

### Быстрый старт

```bash
# Перейти в каталог tools
cd specs/v1/tools

# Установить зависимости
pip install -r requirements.txt

# Валидировать пример
python validate.py ../examples/hello/hello.plan.yaml ../examples/hello/hello.views.yaml

# Сгенерировать Gantt диаграмму
python -m render.mermaid_gantt \
    --plan ../examples/hello/hello.plan.yaml \
    --views ../examples/hello/hello.views.yaml \
    --view overview
```
