# Implementation Plan: Repository Reorganization

## Overview

Реорганизация репозитория opskarta для поддержки версионирования спецификации. Задачи выполняются последовательно: сначала создаётся структура, затем мигрируются файлы, дописываются недостающие части, создаются инструменты.

## Tasks

- [x] 1. Создать базовую структуру каталогов
  - [x] 1.1 Создать каталог `specs/v1/` со всеми подкаталогами
    - Создать `specs/v1/spec/`, `specs/v1/examples/`, `specs/v1/schemas/`, `specs/v1/tools/`
    - Создать `specs/v1/examples/minimal/`, `specs/v1/examples/hello/`, `specs/v1/examples/advanced/`
    - Создать `specs/v1/tools/render/`
    - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4_
  - [x] 1.2 Создать каталог `specs/drafts/`
    - Создать пустой каталог с .gitkeep
    - _Requirements: 1.3_

- [x] 2. Мигрировать спецификацию
  - [x] 2.1 Перенести и переименовать файлы спецификации
    - `docs/spec/000-overview.md` → `specs/v1/spec/00-introduction.md`
    - `docs/spec/010-plan-file.md` → `specs/v1/spec/10-plan-file.md`
    - `docs/spec/020-nodes.md` → `specs/v1/spec/20-nodes.md`
    - `docs/spec/030-views.md` → `specs/v1/spec/30-views-file.md`
    - `docs/spec/040-statuses.md` → `specs/v1/spec/40-statuses.md`
    - `docs/spec/050-extensibility.md` → `specs/v1/spec/90-extensibility.md`
    - _Requirements: 3.1, 7.1_
  - [x] 2.2 Создать недостающие части спецификации
    - Создать `specs/v1/spec/50-scheduling.md` — описание планирования (start, duration, after)
    - Создать `specs/v1/spec/60-validation.md` — правила валидации
    - _Requirements: 3.2_

- [x] 3. Мигрировать примеры
  - [x] 3.1 Перенести текущий пример в hello/
    - `examples/hello.plan.yaml` → `specs/v1/examples/hello/hello.plan.yaml`
    - `examples/hello.views.yaml` → `specs/v1/examples/hello/hello.views.yaml`
    - Создать `specs/v1/examples/hello/README.md`
    - _Requirements: 4.2, 7.2_
  - [x] 3.2 Создать минимальный пример
    - Создать `specs/v1/examples/minimal/project.plan.yaml` — план без views
    - Создать `specs/v1/examples/minimal/README.md`
    - _Requirements: 4.1, 4.4_
  - [x] 3.3 Создать продвинутый пример
    - Создать `specs/v1/examples/advanced/program.plan.yaml` — сложный план с несколькими треками
    - Создать `specs/v1/examples/advanced/program.views.yaml` — несколько представлений
    - Создать `specs/v1/examples/advanced/README.md`
    - _Requirements: 4.3, 4.4_

- [x] 4. Мигрировать схемы
  - [x] 4.1 Перенести и переименовать JSON Schema
    - `schemas/opskarta.plan.schema.json` → `specs/v1/schemas/plan.schema.json`
    - `schemas/opskarta.views.schema.json` → `specs/v1/schemas/views.schema.json`
    - _Requirements: 2.3, 7.3_

- [x] 5. Checkpoint — проверить структуру
  - Убедиться, что все файлы на месте, структура соответствует дизайну

- [x] 6. Создать референсные инструменты
  - [x] 6.1 Создать Spec Builder
    - Создать `specs/v1/tools/build_spec.py`
    - Реализовать сборку SPEC.md из частей spec/
    - Реализовать генерацию оглавления
    - _Requirements: 2.6, 3.3, 3.4_
  - [ ]* 6.2 Написать property test для Spec Builder
    - **Property 2: Spec_Builder Output Correctness**
    - **Validates: Requirements 3.3, 3.4**
  - [x] 6.3 Перенести и адаптировать валидатор
    - Создать `specs/v1/tools/validate.py` на основе `src/opskarta/validation.py`
    - Сделать автономным (без зависимости от пакета)
    - Добавить CLI интерфейс
    - _Requirements: 5.1, 5.3, 7.4_
  - [x] 6.4 Перенести и адаптировать рендерер
    - Создать `specs/v1/tools/render/mermaid_gantt.py` на основе `src/opskarta/render/mermaid_gantt.py`
    - Перенести вспомогательные модули (io.py, errors.py, scheduling.py)
    - Сделать автономным
    - _Requirements: 5.2, 5.3, 7.4_
  - [x] 6.5 Создать документацию инструментов
    - Создать `specs/v1/tools/README.md` с описанием использования
    - Создать `specs/v1/tools/requirements.txt` с зависимостями
    - _Requirements: 5.4_

- [x] 7. Создать README файлы версии
  - [x] 7.1 Создать README версии v1
    - Создать `specs/v1/README.md` с обзором версии, статусом, ссылками
    - _Requirements: 2.5_
  - [x] 7.2 Сгенерировать SPEC.md
    - Запустить build_spec.py для генерации `specs/v1/SPEC.md`
    - _Requirements: 2.6_

- [x] 8. Checkpoint — проверить инструменты
  - Убедиться, что validate.py работает с примерами
  - Убедиться, что build_spec.py генерирует корректный SPEC.md

- [x] 9. Обновить корневые файлы
  - [x] 9.1 Переписать корневой README
    - Создать новый `README.md` как разводящую страницу
    - Добавить таблицу версий спецификации
    - Добавить ссылки на docs/method.md
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 10. Удалить устаревшие файлы и каталоги
  - [x] 10.1 Удалить старую структуру
    - Удалить `docs/spec/` (перенесено в specs/v1/spec/)
    - Удалить `examples/` (перенесено в specs/v1/examples/)
    - Удалить `schemas/` (перенесено в specs/v1/schemas/)
    - _Requirements: 7.1, 7.2, 7.3_
  - [x] 10.2 Удалить Python-пакет
    - Удалить `src/` (инструменты перенесены в specs/v1/tools/)
    - Удалить `tests/`
    - Удалить `pyproject.toml`
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 11. Final checkpoint — финальная проверка
  - Убедиться, что все ссылки в README работают
  - Убедиться, что примеры валидируются
  - Убедиться, что SPEC.md актуален

## Notes

- Задачи с `*` являются опциональными (property tests)
- Каждый checkpoint — точка для ручной проверки перед продолжением
- Миграция выполняется копированием, удаление — в конце
- docs/method.md остаётся на месте (не мигрируется)
