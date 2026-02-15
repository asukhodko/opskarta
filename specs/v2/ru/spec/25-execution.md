# Execution (Отслеживание выполнения)

Execution — **опциональный** оверлей для отслеживания факта выполнения: прогресс, фактические даты, уверенность.

## Концепция

Блок execution повторяет паттерн overlay schedule:

- **Nodes** описывают структуру работ
- **Schedule** добавляет календарное планирование
- **Execution** добавляет отслеживание прогресса

План может существовать без данных execution. Данные execution можно вести в отдельном файле-фрагменте.

## Структура блока Execution

```yaml
execution:
  nodes:
    <node_id>:
      progress: 0.75
      actual_start: "2024-03-01"
      actual_finish: "2024-03-15"
      updated_at: "2024-03-15T10:30:00Z"
      confidence: 0.9
      note: "По плану"
```

## Поля execution.nodes

| Поле | Тип | Описание |
|------|-----|----------|
| `progress` | number | Завершённость от 0.0 до 1.0 |
| `actual_start` | string | Фактическая дата начала (YYYY-MM-DD) |
| `actual_finish` | string | Фактическая дата завершения (YYYY-MM-DD) |
| `updated_at` | string | Время последнего обновления (ISO 8601) |
| `confidence` | number | Уровень уверенности от 0.0 до 1.0 |
| `note` | string | Необязательная аннотация |

## Агрегация прогресса (Rollup)

Для родительских узлов прогресс вычисляется автоматически через взвешенную агрегацию:

```
progress_rollup = sum(effort_effective_i * progress_i) / sum(effort_effective_i)
```

Только дочерние узлы с данными execution участвуют в агрегации.

### Покрытие прогресса (Coverage)

`progress_coverage` показывает, какая доля трудозатрат покрыта данными прогресса:

```
progress_coverage = sum(effort_effective с данными) / sum(всего effort_effective)
```

## Правила

- `node_id` в `execution.nodes` ДОЛЖЕН существовать в `nodes`.
- `progress` ДОЛЖЕН быть в диапазоне [0.0, 1.0].
- `confidence` ДОЛЖЕН быть в диапазоне [0.0, 1.0].
- `actual_start` и `actual_finish` ДОЛЖНЫ быть валидными датами `YYYY-MM-DD`.

## Пример

```yaml
version: 2

nodes:
  epic:
    title: "Аутентификация"
    effort: 13
  login:
    title: "Email логин"
    parent: epic
    effort: 5
  oauth:
    title: "OAuth логин"
    parent: epic
    effort: 8

execution:
  nodes:
    login:
      progress: 1.0
      actual_start: "2024-03-01"
      actual_finish: "2024-03-05"
      confidence: 1.0
    oauth:
      progress: 0.3
      actual_start: "2024-03-06"
      confidence: 0.7
      note: "Задержка с API провайдера"
```

В этом примере:
- `login`: 100% завершён, трудозатраты 5
- `oauth`: 30% завершён, трудозатраты 8
- `epic` rollup: (5 * 1.0 + 8 * 0.3) / (5 + 8) = 7.4 / 13 ≈ 0.57 (57%)
- `epic` coverage: (5 + 8) / 13 = 1.0 (100%)
