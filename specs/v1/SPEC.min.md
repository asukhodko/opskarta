opskarta v1 (draft) — ultra-compact spec (LLM-paste), core-complete + anti-ambiguity

0) Общие
- Формат: YAML (рекомендуется) или JSON; version в корне.
- Core vs non-core: Core MUST implement; Non-core MAY implement.
- Core включает: структура plan/views, поля узлов (title, kind, status, parent, after, start, finish, duration, milestone), алгоритмы дат, core excludes, duration=1d для планируемых, валидация/ссылочная целостность.
- Non-core: x: расширения, renderer profiles, поля views для рендерера, non-core excludes, дефолтные цвета.

1) *.plan.yaml (plan)
- Корень: version:int, meta: {id:string, title:string}, statuses:object, nodes:object.
- meta.id RECOMMENDED; REQUIRED если есть views (views.project должен совпасть).
- nodes: map {node_id: node}.

2) nodes.* (узлы)
- node_id: уникален, MUST быть строкой; рекоменд. regex ^[a-zA-Z][a-zA-Z0-9._-]*$ (совм. с Mermaid).
- Обязательное поле: title:string.
- Поля (core): kind, status, parent, after, start, finish, duration, milestone.
- Прочие поля (non-core): issue, notes и любые неизвестные (см. расширяемость).
- milestone:
  - MUST иметь start или вычислимый start через after.
  - Если duration не задана у milestone, используется 1d.
  - start из after без +1 дня (см. планирование).

3) statuses
- Section statuses опциональна, но если хоть один узел имеет status, statuses MUST exist.
- Ссылочная целостность: status в узле MUST быть ключом statuses.
- status fields: label (recommended), color (optional).
- color MUST match ^#[0-9a-fA-F]{6}$.
- Если label отсутствует, рендерер MAY использовать ключ статуса как label.
- Дефолтные цвета — non-core (см. Mermaid профиль).

4) *.views.yaml (views)
- Корень: version:int, project:string, gantt_views:object (optional).
- project MUST == plan.meta.id; если meta.id нет → error.
- gantt_views.* core: title:string, excludes:list[string], lanes:object.
- lanes.*: title:string, nodes:list[node_id] (каждый node_id MUST существовать в plan).
- Non-core поля для Mermaid: date_format, axis_format, tick_interval.

5) Планирование (core) — per-view
- Расчёт расписания выполняется для каждого view отдельно (calendar(view) зависит от excludes).
- workday: день не исключён calendar(view).
- Core excludes: "weekends" и даты YYYY-MM-DD; они MUST влиять на расчёт. Non-core excludes MUST ignore + WARN.
- duration:
  - формат: ^[1-9][0-9]*[dw]$; строка.
  - Nd = N workdays; Nw = 5*N workdays.
  - duration без start/after не позиционирует узел.
  - default duration=1d для планируемых (scheduled) узлов.
- finish inclusive:
  - finish_from_start: finish = add_workdays(start, duration_days-1).
  - duration_from_dates: duration = count_workdays(start..finish inclusive).
  - start_from_finish: start = sub_workdays(finish, duration_days-1).
- priorites start computation (anti-ambiguity):
  1) явный start (после нормализации) — приоритет над after.
  2) если start отсутствует и заданы finish+duration → start_from_finish, даже если есть after (after не сдвигает даты, только логика/WARN).
  3) иначе если after: start = next_workday(max_finish) для обычных; start = max_finish для milestone.
  4) иначе узел unscheduled.
- after semantics:
  - start из after: обычный узел = next_workday(max_finish deps); milestone = max_finish (без +1 дня).
  - WARN если явный start < finish(deps) (логическая зависимость нарушена).
- Нормализация start:
  - если start на исключённый день и не milestone: MUST normalize to next_workday + WARN; расчёты используют effective_start.
  - milestone: без нормализации.
- finish на исключённый день:
  - обычный узел: WARN, без нормализации.
  - milestone: без WARN.
- Unscheduled:
  - нет start, нет finish, и нет вычислимого start через after (или after-сцепка без якоря).
  - Core правило: unscheduled НЕ отображаются на Gantt.
- Зависимости:
  - при расчёте view after MUST учитывать ВСЕ узлы плана, даже если они не показаны в view.
- Термины: scheduled = узел с вычислимым start.

6) Миграция из end(exclusive)
- finish (inclusive) = prev_workday(end_exclusive, calendar(view)).
- Нельзя просто -1 календарный день: учитывать excludes.

7) YAML/JSON типы и нормализация (core)
- YAML 1.1 может авто-типизировать даты; инструменты MUST normalize.
- Канон. типы:
  - start/finish: "YYYY-MM-DD" строка (regex ^\d{4}-\d{2}-\d{2}$).
  - excludes[]: строка (даты нормализовать к "YYYY-MM-DD").
  - duration: строка Nd/Nw.
  - node_id keys: строка (MUST; нестроковые ключи SHOULD error или convert, рекоменд. error).
- Инструменты MUST normalize start/finish/excludes из YAML date/datetime → строка.

8) Валидация (core) + severity
- severity: error (invalid), warn, info.
- Обязательные поля (error): plan.version, plan.nodes, node.title; views.version, views.project.
- Ссылочная целостность (error): parent/after/status должны ссылаться на существующее; lanes.nodes must exist; циклы parent/after — error.
- Форматы (error): start/finish regex ^\d{4}-\d{2}-\d{2}$; duration regex ^[1-9][0-9]*[dw]$; status.color regex ^#[0-9a-fA-F]{6}$.
- Несогласованные start+finish+duration — error.
- Дубликаты node_id и дубликаты YAML ключей — error.
- Chain after без якоря (нет start/finish в цепочке) — warn; узлы становятся unscheduled.
- start раньше finish(deps) при наличии after — warn.
- start на исключённом дне (не milestone) — warn.
- finish на исключённом дне — warn.
- Non-core excludes — warn.
- Отсутствие duration у планируемого узла — info.
- Конкретные даты в excludes (core) — info.
- Unscheduled узлы — info.
- Связь views.project == plan.meta.id (если meta.id нет — error).

9) Расширяемость (core-совместимость)
- Unknown fields MUST ignore and MUST preserve on parse→emit.
- Рекомендуемый namespace x: для расширений; допустимы расширения без x: (не рекомендуется).
- Расширяемые места: корень plan/views, meta, statuses.*, nodes.*, gantt_views.*, lanes.*.
- Renderer-specific extensions MUST be documented and MUST NOT affect core semantics.
- x.scheduling.anchor_to_parent_start — non-core пример расширения (см. Mermaid профиль).

10) Renderer profile: Mermaid Gantt (non-core, reference)
- MUST precompute core schedule; output explicit dates; do not rely on Mermaid planner.
- Передавать только core excludes; non-core excludes ignore+WARN; не передавать в Mermaid.
- duration w → d (1w=5d).
- lanes → section; parent иерархия плоско (Mermaid не поддерживает вложенные секции).
- milestones: milestone tag + 1d если duration не задана; точка/ромб.
- status mapping: done→tag done (✅), in_progress→active (🔄), blocked→crit (⛔), not_started→no tag.
- Default colors (если statuses[].color нет): not_started #9ca3af, in_progress #0ea5e9, done #22c55e, blocked #fecaca (non-core).
- Extension: x.scheduling.anchor_to_parent_start:
  - no start & no after → effective_start(child)=effective_start(parent)
  - has after & no start → effective_start=max(start_from_after, effective_start(parent))
  - has start → start wins.
- views fields (non-core): date_format→dateFormat, axis_format→axisFormat, tick_interval→tickInterval.