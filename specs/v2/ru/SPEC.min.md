opskarta v2 (draft) — ультра-компактная спецификация (LLM-paste), core-complete + anti-ambiguity

0) Общее
- Сериализация: YAML (рекомендуется) или JSON; корень содержит version: 2.
- Идентификаторы узлов — строковые ключи в nodes.
- Ключевое отличие v2: overlay schedule — структура работ (nodes) отделена от календарного планирования (schedule).
- План без schedule полностью валиден.

1) Plan Set (Многофайловая структура)
- План можно разбить на несколько *.plan.yaml файлов (фрагментов).
- Фрагменты сливаются в единый Merged Plan детерминированно.
- Допустимые блоки верхнего уровня: version, meta, statuses, nodes, schedule, views, x.
- Любой другой блок верхнего уровня — ошибка.
- version: должен быть одинаковым во всех фрагментах; конфликт — ошибка.
- meta: поля объединяются; конфликтующие значения одного поля — ошибка.
- statuses/nodes/views: словари объединяются; дублирующийся ключ — ошибка с указанием файла.
- schedule.calendars/schedule.nodes: словари объединяются; дублирующийся ключ — ошибка.
- schedule.default_calendar: допускается только в ОДНОМ фрагменте; множественные определения — ошибка.
- x: словари объединяются; дублирующийся ключ — ошибка.

2) nodes (Структура работ)
- node_id: уникальный строковый ключ в nodes; рекомендуемый regex ^[a-zA-Z][a-zA-Z0-9._-]*$; избегать пробелов/скобок/двоеточий для Mermaid.
- Обязательно: title (string).
- Опционально: kind (string), status (string), parent (string), after (list[string]), milestone (bool), effort (number ≥0), issue (string), notes (string), x (object).
- ЗАПРЕЩЕНО в v2 nodes: start, finish, duration, excludes — перенесены в schedule.
- parent: существующий node_id; циклические ссылки запрещены.
- after: список node_id; циклические зависимости запрещены; зависимости определяются в nodes, НЕ в schedule.nodes.
- milestone: true = точечное событие; при вычислении start из after не добавляется +1 рабочий день.
- effort: неотрицательное число; единица измерения в meta.effort_unit (только для отображения).
- effort_rollup: сумма effort_effective прямых потомков.
- effort_effective: effort если задан, иначе effort_rollup.
- effort_gap: max(0, effort - effort_rollup).
- status: должен быть ключом в statuses; несуществующий статус — ошибка.

3) statuses
- Опционально, если ни один узел не имеет status; иначе statuses обязателен.
- Поля статуса: label (string, рекомендуется), color (string, опционально).
- Формат color: ^#[0-9a-fA-F]{6}$; невалидный цвет — ошибка.

4) schedule (Слой календарного планирования)
- Опциональный блок; план валиден без schedule.
- Структура: schedule.calendars, schedule.default_calendar, schedule.nodes.

4.1) schedule.calendars
- calendar_id: уникальный строковый ключ.
- excludes: список "weekends" и/или дат "YYYY-MM-DD".

4.2) schedule.default_calendar
- Ссылка на существующий calendar_id.
- Используется для узлов без явного calendar.

4.3) schedule.nodes
- node_id: должен существовать в nodes.
- Поля: start (YYYY-MM-DD), finish (YYYY-MM-DD), duration (Nd или Nw), calendar (calendar_id).
- after ЗАПРЕЩЁН в schedule.nodes — зависимости только в nodes.
- Состояния узла: unscheduled (нет в schedule.nodes), scheduled (есть в schedule.nodes), computed (scheduled + даты вычислены).

4.4) Вычисление дат
- Приоритет start: 1) явный start, 2) finish + duration (обратное), 3) зависимости after.
- Алгоритм after: получить deps из nodes.<id>.after; отфильтровать только scheduled deps; вычислить max(finish); обычный узел: start = next_workday(max_finish); milestone: start = max_finish.
- Unschedulable: нет явного start, нет finish+duration, все after deps unscheduled/unschedulable.
- Формат duration: ^[1-9][0-9]*[dw]$; d=рабочие дни; w=5 рабочих дней (1w=5d).
- finish = add_workdays(start, duration - 1, calendar); день start включён.
- Обратное планирование: start = sub_workdays(finish, duration - 1, calendar).
- Согласованность: если start+finish+duration все заданы, должны совпадать; несогласованность — ошибка.
- Нормализация start: если start на исключённом дне и не milestone, нормализуется к следующему рабочему дню + warning; milestones не нормализуются.

5) views (Представления)
- Views определяют визуализацию, НЕ влияют на вычисление schedule.
- ЗАПРЕЩЕНО в v2 views: excludes — календарь только в schedule.calendars.
- Поля view: title (string), where (object), order_by (string), group_by (string), lanes (object), date_format, axis_format, tick_interval.

5.1) where (Фильтр)
- kind: list[string] — узлы с указанным kind.
- status: list[string] — узлы с указанным status.
- has_schedule: bool — только scheduled (true) или unscheduled (false) узлы.
- parent: string — потомки указанного узла.
- Все условия объединяются через AND.

5.2) lanes (для Gantt)
- lane_id: { title: string, nodes: list[node_id] }.

6) Валидация
- Severity: error (невалидно), warn (валидно с предупреждением), info (валидно).
- Ошибки: отсутствуют обязательные поля; несуществующие ссылки (parent/after/status/calendar); циклические зависимости; дублирующиеся ключи; невалидные форматы; несогласованные даты; запрещённые поля в неправильных блоках.
- Предупреждения: unschedulable узлы; start на исключённом дне; все deps unscheduled.
- Info: unscheduled узлы; вычисленные даты.

7) Расширяемость
- Неизвестные поля ДОЛЖНЫ игнорироваться и сохраняться при parse→emit.
- Namespace x: для расширений; допускается в plan root, meta, statuses.*, nodes.*, schedule, views.*, lanes.*.
- Расширения НЕ ДОЛЖНЫ влиять на core-семантику.

8) Миграция с v1
- nodes: удалить start/finish/duration/excludes; перенести в schedule.nodes.
- views: удалить excludes; перенести в schedule.calendars.
- after: оставить в nodes (без изменений).
- finish (v1 inclusive) → finish (v2 inclusive): без изменений.

9) Anti-ambiguity
- Зависимости (after) определяются ТОЛЬКО в nodes, никогда в schedule.nodes.
- Календарь (excludes) определяется ТОЛЬКО в schedule.calendars, никогда в views.
- План без schedule валиден — структура существует независимо от календаря.
- Unscheduled узлы не показываются на Gantt, но существуют в tree/list/deps.
- Множественные зависимости: start вычисляется из max(finish) только scheduled deps.
