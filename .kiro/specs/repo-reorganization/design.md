# Design Document: Repository Reorganization

## Overview

Реорганизация репозитория opskarta для поддержки версионирования спецификации. Основная идея: каждая версия спецификации — самодостаточный каталог с текстовой спецификацией, примерами, схемами и инструментами. Текстовая спецификация первична, код — приложение к ней.

### Ключевые принципы

1. **Spec-first**: Текстовая спецификация — источник истины, инструменты — её приложение
2. **Self-contained versions**: Каждая версия полностью автономна
3. **Predictable structure**: Единообразная структура для всех версий
4. **Minimal tooling**: Инструменты минимальны и не требуют сложной установки

## Architecture

```
opskarta/
├── specs/                          # Все версии спецификации
│   ├── v1/                         # Версия 1 (текущая)
│   │   ├── README.md               # Обзор версии
│   │   ├── SPEC.md                 # Собранная спецификация
│   │   ├── spec/                   # Части спецификации
│   │   ├── examples/               # Примеры
│   │   ├── schemas/                # JSON Schema
│   │   └── tools/                  # Референсные инструменты
│   └── drafts/                     # Черновики будущих версий
├── docs/
│   └── method.md                   # Философия проекта
├── README.md                       # Разводящая страница
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── LICENSE
├── NOTICE
└── CHANGELOG.md
```

## Components and Interfaces

### Component 1: Spec Version Directory (`specs/vN/`)

Каждая версия спецификации имеет фиксированную структуру:

```
specs/v1/
├── README.md                       # Обзор версии, статус, изменения
├── SPEC.md                         # Генерируется из spec/
├── spec/
│   ├── 00-introduction.md          # Введение, цели, non-goals
│   ├── 10-plan-file.md             # Структура файла плана
│   ├── 20-nodes.md                 # Узлы и их атрибуты
│   ├── 30-views-file.md            # Структура файла представлений
│   ├── 40-statuses.md              # Статусы
│   ├── 50-scheduling.md            # Планирование (start, duration, after)
│   ├── 60-validation.md            # Правила валидации
│   └── 90-extensibility.md         # Расширяемость формата
├── examples/
│   ├── minimal/                    # Минимальный пример
│   │   ├── README.md
│   │   └── project.plan.yaml
│   ├── hello/                      # Базовый пример (текущий)
│   │   ├── README.md
│   │   ├── hello.plan.yaml
│   │   └── hello.views.yaml
│   └── advanced/                   # Продвинутый пример
│       ├── README.md
│       ├── program.plan.yaml
│       └── program.views.yaml
├── schemas/
│   ├── plan.schema.json            # JSON Schema для plan файлов
│   └── views.schema.json           # JSON Schema для views файлов
└── tools/
    ├── README.md                   # Документация инструментов
    ├── requirements.txt            # Зависимости (PyYAML)
    ├── validate.py                 # Валидатор
    └── render/
        ├── __init__.py
        └── mermaid_gantt.py        # Рендерер Mermaid Gantt
```

### Component 2: Spec Builder Script

Скрипт для сборки частей спецификации в единый SPEC.md.

**Расположение**: `specs/v1/tools/build_spec.py`

**Интерфейс**:
```bash
python tools/build_spec.py          # Генерирует SPEC.md
python tools/build_spec.py --check  # Проверяет актуальность SPEC.md
```

**Алгоритм**:
1. Найти все `*.md` файлы в `spec/`
2. Отсортировать по числовому префиксу
3. Извлечь заголовки первого уровня для оглавления
4. Собрать в единый файл с оглавлением

### Component 3: Reference Validator

Автономный валидатор для проверки plan и views файлов.

**Расположение**: `specs/v1/tools/validate.py`

**Интерфейс**:
```bash
python tools/validate.py plan.yaml                    # Валидация плана
python tools/validate.py plan.yaml views.yaml         # Валидация плана и views
python tools/validate.py --schema plan.yaml           # Валидация через JSON Schema
```

**Зависимости**: PyYAML (указаны в requirements.txt)

### Component 4: Reference Renderers

Рендереры для генерации представлений из плана.

**Расположение**: `specs/v1/tools/render/`

**Интерфейс**:
```bash
python -m render.mermaid_gantt --plan plan.yaml --views views.yaml --view overview
```

### Component 5: Landing README

Корневой README.md как разводящая страница.

**Структура**:
1. Краткое описание opskarta (2-3 абзаца)
2. Таблица версий спецификации со статусами
3. Быстрый старт (ссылка на текущую версию)
4. Ссылки на философию и контрибьюцию

## Data Models

### Spec Part File Format

Каждая часть спецификации — Markdown файл с:
- Заголовком первого уровня (используется в оглавлении)
- Содержимым в формате Markdown

```markdown
# Название части

Содержимое...
```

### Version README Format

```markdown
# opskarta Specification v1

**Status**: Alpha / Stable / Deprecated
**Released**: YYYY-MM-DD (или "Draft")

## Overview

Краткое описание версии...

## Changes from Previous Version

- Изменение 1
- Изменение 2

## Quick Links

- [Full Specification](SPEC.md)
- [Examples](examples/)
- [JSON Schema](schemas/)
- [Reference Tools](tools/)
```

### Landing README Format

```markdown
# opskarta

Краткое описание...

## Specification Versions

| Version | Status | Description |
|---------|--------|-------------|
| [v1](specs/v1/) | Alpha | Initial version |

## Quick Start

See [v1 specification](specs/v1/) for the current version.

## Documentation

- [Philosophy & Method](docs/method.md)
- [Contributing](CONTRIBUTING.md)

## License

Apache License 2.0
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Spec File Naming Convention

*For any* file in the `spec/` directory of a Spec_Version, the filename SHALL match the pattern `NN-*.md` where NN is a two-digit number.

**Validates: Requirements 3.1**

### Property 2: Spec_Builder Output Correctness

*For any* set of spec part files in `spec/`, when Spec_Builder runs:
- The generated SPEC.md SHALL contain a Table of Contents section
- The SPEC.md SHALL contain content from ALL spec part files
- The order of sections in SPEC.md SHALL match the numeric prefix order of source files

**Validates: Requirements 3.3, 3.4**

### Property 3: Example Directory Completeness

*For any* example directory in `examples/` (minimal, hello, advanced), the directory SHALL contain a README.md file.

**Validates: Requirements 4.4**

## Error Handling

### Spec_Builder Errors

| Error Condition | Handling |
|-----------------|----------|
| No spec files found | Exit with error message, non-zero exit code |
| Invalid filename format | Warning, skip file, continue processing |
| Duplicate numeric prefix | Error, list conflicting files |
| Missing write permissions | Exit with error message |

### Validator Errors

| Error Condition | Handling |
|-----------------|----------|
| File not found | Exit with error message |
| Invalid YAML syntax | Exit with parse error details |
| Schema validation failure | Exit with list of violations |
| Missing required fields | Exit with field path and expected type |

## Testing Strategy

### Dual Testing Approach

Для этого проекта реорганизации тестирование фокусируется на:

1. **Unit tests**: Проверка конкретных примеров и edge cases
   - Spec_Builder корректно обрабатывает пустой каталог
   - Spec_Builder корректно обрабатывает файлы без числового префикса
   - Validator корректно отклоняет невалидные файлы

2. **Property tests**: Проверка универсальных свойств
   - Property 1: Все файлы в spec/ соответствуют naming convention
   - Property 2: SPEC.md содержит все части в правильном порядке
   - Property 3: Все примеры содержат README.md

### Property-Based Testing Configuration

- **Library**: pytest с hypothesis (для Python)
- **Iterations**: Минимум 100 итераций на property test
- **Tag format**: `Feature: repo-reorganization, Property N: {property_text}`

### Test Locations

Тесты располагаются в `specs/v1/tools/tests/`:
- `test_build_spec.py` — тесты Spec_Builder
- `test_validate.py` — тесты валидатора
- `test_structure.py` — тесты структуры репозитория

### Manual Verification Checklist

После реорганизации необходимо вручную проверить:
- [ ] Все ссылки в README файлах работают
- [ ] Примеры валидируются без ошибок
- [ ] Инструменты запускаются без установки пакета
- [ ] SPEC.md генерируется корректно
