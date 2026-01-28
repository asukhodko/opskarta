# Requirements Document

## Introduction

Реорганизация репозитория opskarta для поддержки версионирования спецификации. Цель — создать структуру, где каждая версия спецификации (v1, v2, ...) является самодостаточной единицей с текстовой спецификацией, примерами, JSON Schema и референсными инструментами. Текстовая спецификация первична, код — приложение к ней.

## Glossary

- **Spec_Version**: Самодостаточный каталог с полной версией спецификации формата opskarta (например, `specs/v1/`)
- **Plan_File**: YAML/JSON файл с моделью работ (`*.plan.yaml`)
- **Views_File**: YAML/JSON файл с представлениями плана (`*.views.yaml`)
- **Spec_Builder**: Скрипт для сборки частей спецификации в единый SPEC.md
- **Reference_Tools**: Минимальные инструменты для валидации и рендеринга, поставляемые вместе со спецификацией
- **Landing_README**: Корневой README.md, служащий разводящей страницей к версиям спецификации

## Requirements

### Requirement 1: Версионированная структура спецификаций

**User Story:** As a спецификатор формата, I want иметь отдельные каталоги для каждой версии спецификации, so that я могу развивать формат без нарушения обратной совместимости.

#### Acceptance Criteria

1. THE Repository SHALL содержать каталог `specs/` с подкаталогами для каждой версии
2. WHEN создаётся новая версия спецификации, THE Repository SHALL содержать отдельный каталог `specs/vN/` для этой версии
3. THE Repository SHALL содержать каталог `specs/drafts/` для черновиков будущих версий
4. THE Spec_Version SHALL быть самодостаточной и не зависеть от файлов других версий

### Requirement 2: Структура версии спецификации

**User Story:** As a разработчик инструментов, I want иметь предсказуемую структуру каждой версии спецификации, so that я могу легко находить нужные артефакты.

#### Acceptance Criteria

1. THE Spec_Version SHALL содержать каталог `spec/` с частями текстовой спецификации
2. THE Spec_Version SHALL содержать каталог `examples/` с примерами разной сложности (minimal, hello, advanced)
3. THE Spec_Version SHALL содержать каталог `schemas/` с JSON Schema для валидации
4. THE Spec_Version SHALL содержать каталог `tools/` с референсными инструментами
5. THE Spec_Version SHALL содержать файл `README.md` с обзором версии
6. WHEN Spec_Builder запускается, THE Spec_Version SHALL содержать сгенерированный файл `SPEC.md`

### Requirement 3: Текстовая спецификация

**User Story:** As a автор спецификации, I want разбить спецификацию на логические части, so that её удобно редактировать и ревьюить.

#### Acceptance Criteria

1. THE Spec_Version SHALL содержать части спецификации с нумерованными префиксами (00-, 10-, 20-, ...)
2. THE Spec_Version SHALL содержать следующие части: introduction, plan-file, nodes, views-file, statuses, scheduling, validation, extensibility
3. WHEN части спецификации собираются, THE Spec_Builder SHALL создать единый SPEC.md с оглавлением
4. THE Spec_Builder SHALL сохранять порядок частей согласно числовым префиксам

### Requirement 4: Примеры

**User Story:** As a пользователь формата, I want иметь примеры разной сложности, so that я могу быстро понять формат и начать использовать.

#### Acceptance Criteria

1. THE Spec_Version SHALL содержать минимальный пример (`minimal/`) с базовым планом
2. THE Spec_Version SHALL содержать базовый пример (`hello/`) с планом и представлениями
3. THE Spec_Version SHALL содержать продвинутый пример (`advanced/`) с расширенными возможностями
4. WHEN пример создаётся, THE Example SHALL содержать README.md с описанием

### Requirement 5: Референсные инструменты

**User Story:** As a разработчик, I want иметь референсные инструменты в составе версии спецификации, so that я могу проверить своё понимание формата.

#### Acceptance Criteria

1. THE Spec_Version SHALL содержать валидатор (`tools/validate.py`)
2. THE Spec_Version SHALL содержать рендерер Mermaid Gantt (`tools/render/mermaid_gantt.py`)
3. THE Reference_Tools SHALL быть автономными и не требовать установки пакета
4. IF инструмент требует зависимости, THEN THE Reference_Tools SHALL документировать их в README

### Requirement 6: Корневой README как разводящая страница

**User Story:** As a посетитель репозитория, I want быстро понять проект и найти нужную версию спецификации, so that я могу начать работу без изучения всей структуры.

#### Acceptance Criteria

1. THE Landing_README SHALL содержать краткое описание проекта opskarta
2. THE Landing_README SHALL содержать ссылки на все стабильные версии спецификации
3. THE Landing_README SHALL указывать текущую рекомендуемую версию
4. THE Landing_README SHALL содержать ссылку на философию/метод (`docs/method.md`)
5. THE Landing_README SHALL НЕ дублировать содержимое спецификации

### Requirement 7: Миграция существующих файлов

**User Story:** As a мейнтейнер репозитория, I want перенести существующие файлы в новую структуру, so that не потерять текущую работу.

#### Acceptance Criteria

1. WHEN миграция выполняется, THE System SHALL перенести `docs/spec/*` в `specs/v1/spec/`
2. WHEN миграция выполняется, THE System SHALL перенести `examples/*` в `specs/v1/examples/hello/`
3. WHEN миграция выполняется, THE System SHALL перенести `schemas/*` в `specs/v1/schemas/`
4. WHEN миграция выполняется, THE System SHALL перенести `src/opskarta/*` в `specs/v1/tools/`
5. THE System SHALL удалить устаревшие каталоги после миграции

### Requirement 8: Решение судьбы CLI-пакета

**User Story:** As a мейнтейнер, I want определить судьбу текущего Python-пакета, so that структура репозитория была чистой.

#### Acceptance Criteria

1. THE Repository SHALL удалить `pyproject.toml` из корня репозитория
2. THE Repository SHALL удалить каталог `src/` после миграции инструментов
3. THE Repository SHALL удалить каталог `tests/` (тесты переедут в tools версии)
4. IF в будущем понадобится CLI-пакет, THEN THE Repository SHALL создать отдельный репозиторий или подкаталог `packages/`

### Requirement 9: Сохранение метадокументации

**User Story:** As a контрибьютор, I want сохранить метадокументацию проекта, so that процессы разработки остались понятными.

#### Acceptance Criteria

1. THE Repository SHALL сохранить `docs/method.md` на верхнем уровне
2. THE Repository SHALL сохранить `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
3. THE Repository SHALL сохранить `LICENSE`, `NOTICE`, `CHANGELOG.md`
