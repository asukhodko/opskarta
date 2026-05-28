# Profiles (Пространства расширений)

Profiles объявляют пространства имён расширений, используемые в полях `x` плана.

## Концепция

Поле `x` в узлах и на верхнем уровне хранит произвольные данные расширений. Profiles позволяют документировать и валидировать используемые пространства имён.

## Структура Profile

```yaml
profiles:
  - id: "opskarta.ai-dev"
    version: 1
    namespace: "ai"
```

## Поля Profile

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | string | Идентификатор профиля (напр. `"opskarta.ai-dev"`) |
| `version` | integer | Версия схемы профиля |
| `namespace` | string | Ключ в `x`, где размещаются данные профиля |

## Соглашение о пространствах имён

Значение `namespace` определяет ключ в полях `x`:

```yaml
profiles:
  - id: "opskarta.ai-dev"
    version: 1
    namespace: "ai"

nodes:
  task1:
    title: "Реализовать фичу"
    x:
      ai:
        complexity: high
        suggested_approach: "Использовать паттерн X"
```

## Правила

- `namespace` ДОЛЖЕН соответствовать `^[a-zA-Z_][a-zA-Z0-9_]*$`.
- Два профиля с одинаковым `namespace` — **ошибка**.
- `id`, `version` и `namespace` — все **обязательные** поля.

## Пример

```yaml
version: 3

profiles:
  - id: "opskarta.ai-dev"
    version: 1
    namespace: "ai"
  - id: "mycompany.pm"
    version: 3
    namespace: "pm"

nodes:
  task1:
    title: "Backend API"
    x:
      ai:
        complexity: medium
      pm:
        assignee: "john"
        sprint: 5
```
