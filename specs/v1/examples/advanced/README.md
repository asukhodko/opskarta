# Пример: Advanced (продвинутый план программы)

Этот пример демонстрирует полные возможности формата opskarta на примере программы модернизации платформы с несколькими треками работ.

## Что демонстрирует

### Файл плана (`program.plan.yaml`)

- **Полная секция meta** — идентификатор и название программы
- **Расширенные статусы** — 7 кастомных статусов с цветами (not_started, planning, in_progress, review, done, blocked, on_hold)
- **Множественные треки** — три параллельных направления работ (бэкенд, фронтенд, инфраструктура)
- **Глубокая иерархия** — 4 уровня вложенности (summary → phase → epic → task)
- **Кросс-трековые зависимости** — задачи, зависящие от узлов из разных треков
- **Все поля планирования** — `start`, `duration`, `after`
- **Заметки** — пояснения к критичным задачам
- **Расширения (x:)** — пользовательские данные (команды, риски, вехи)

### Файл представлений (`program.views.yaml`)

- **Множественные представления** — 5 различных Gantt-представлений
- **Разные уровни детализации** — от обзора программы до детальных планов треков
- **Исключения календаря** — выходные и праздничные дни
- **Представление критического пути** — фокус на ключевых зависимостях

## Файлы

| Файл | Описание |
|------|----------|
| `program.plan.yaml` | План программы модернизации с тремя треками и 30+ узлами |
| `program.views.yaml` | Пять Gantt-представлений для разных аудиторий |

## Структура плана

```
program (Модернизация платформы Q1-Q2 2026)
│
├── backend (Бэкенд)
│   ├── api-gateway (API Gateway)
│   │   ├── gateway-design
│   │   ├── gateway-impl
│   │   └── gateway-testing
│   └── microservices (Декомпозиция на микросервисы)
│       ├── user-service
│       ├── order-service
│       └── notification-service
│
├── frontend (Фронтенд)
│   ├── design-system (Дизайн-система)
│   │   ├── ds-tokens
│   │   ├── ds-components
│   │   └── ds-docs
│   └── ui-migration (Миграция на новый UI)
│       ├── migrate-auth
│       ├── migrate-dashboard
│       ├── migrate-settings
│       └── ui-e2e-tests
│
├── infrastructure (Инфраструктура)
│   ├── k8s (Миграция на Kubernetes)
│   │   ├── k8s-cluster
│   │   ├── k8s-helm
│   │   └── k8s-ci-cd
│   └── monitoring (Система мониторинга)
│       ├── prometheus
│       ├── logging
│       └── alerting
│
├── integration-testing (Интеграционное тестирование)
└── release (Релиз v2.0)
```

## Представления

| Представление | Назначение |
|---------------|------------|
| `overview` | Обзор всей программы для руководства |
| `backend-detail` | Детальный план бэкенд-команды |
| `frontend-detail` | Детальный план фронтенд-команды |
| `infrastructure-detail` | Детальный план инфраструктурной команды |
| `critical-path` | Критический путь к релизу |

## Использование

### Валидация

```bash
cd specs/v1
python tools/validate.py examples/advanced/program.plan.yaml examples/advanced/program.views.yaml
```

### Генерация Mermaid Gantt

```bash
cd specs/v1

# Обзорное представление
python -m tools.render.mermaid_gantt \
  --plan examples/advanced/program.plan.yaml \
  --views examples/advanced/program.views.yaml \
  --view overview

# Детальный план бэкенда
python -m tools.render.mermaid_gantt \
  --plan examples/advanced/program.plan.yaml \
  --views examples/advanced/program.views.yaml \
  --view backend-detail

# Критический путь
python -m tools.render.mermaid_gantt \
  --plan examples/advanced/program.plan.yaml \
  --views examples/advanced/program.views.yaml \
  --view critical-path
```

## Особенности примера

### Расширения (x:)

Пример демонстрирует использование секции `x:` для хранения пользовательских данных:

```yaml
x:
  team_assignments:
    backend: ["alice", "bob", "charlie"]
    frontend: ["diana", "eve"]
    infrastructure: ["frank", "grace"]
  
  risk_register:
    - id: R001
      description: "Задержка поставки API Gateway"
      probability: medium
      impact: high
      mitigation: "Параллельная разработка mock-сервиса"
  
  milestones:
    - date: 2026-02-15
      name: "API Gateway Ready"
      nodes: [gateway-testing]
```

Эти данные игнорируются стандартными инструментами, но могут использоваться кастомными рендерерами и интеграциями.

### Кросс-трековые зависимости

Узел `integration-testing` зависит от завершения работ во всех трёх треках:

```yaml
integration-testing:
  after: [gateway-testing, ui-e2e-tests, k8s-ci-cd]
```

Это позволяет моделировать сложные зависимости между командами.

### Исключения календаря

Файл представлений включает исключения для праздничных дней:

```yaml
excludes: ["weekends", "2026-02-23", "2026-03-08", "2026-05-01", "2026-05-09"]
```

## Когда использовать

Этот пример полезен как референс для:

- Планирования крупных программ с несколькими командами
- Моделирования сложных зависимостей между треками
- Создания представлений для разных аудиторий
- Использования расширений для кастомных данных

Для более простых проектов см. примеры [minimal](../minimal/) и [hello](../hello/).
