# Rendering Engine

<cite>
**Referenced Files in This Document**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py)
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md)
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml)
- [README.md](file://README.md)
- [SPEC.md](file://specs/v1/SPEC.md)
- [date_excludes.plan.yaml](file://specs/v1/tests/fixtures/date_excludes.plan.yaml)
- [date_excludes.views.yaml](file://specs/v1/tests/fixtures/date_excludes.views.yaml)
- [non_core_excludes.views.yaml](file://specs/v1/tests/fixtures/non_core_excludes.views.yaml)
- [weekends_exclusion.plan.yaml](file://specs/v1/tests/fixtures/weekends_exclusion.plan.yaml)
- [test_scheduling.py](file://specs/v1/tests/test_scheduling.py)
</cite>

## Update Summary
**Changes Made**
- Updated to reflect the new core/non-core exclusion model implementation in the Mermaid renderer
- Enhanced weekend exclusion handling documentation with core vs non-core distinction
- Documented the `get_core_excludes()` function and its role in separating core from non-core exclusions
- Added comprehensive coverage of non-core exclusion warnings and Mermaid compatibility considerations
- Updated renderer profile to include the new exclusion model behavior
- Enhanced troubleshooting guidance for exclusion-related issues

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document describes the rendering engine that generates Mermaid Gantt diagrams from opskarta plan and view definitions. It explains the scheduling computation algorithm, automatic date calculation from dependencies, weekend exclusion logic, and business day arithmetic. It documents the rendering pipeline from validated plan data to Mermaid output, view configuration options, lane organization, status theming with color coding and emoji support, CLI usage, output formatting, integration with visualization tools, the Python API for programmatic rendering, data structures for scheduled nodes, performance optimization for large datasets, customization options, export formats, and troubleshooting rendering issues.

**Updated** Enhanced coverage of the Mermaid Gantt renderer profile, including the new core/non-core exclusion model that separates "weekends" and specific date exclusions (core) from other exclusion types (non-core). The renderer now implements strict separation between core scheduling calculations and Mermaid visual representation to prevent visual discrepancies.

## Project Structure
The rendering engine lives under specs/v1/tools/render/mermaid_gantt.py and integrates with the opskarta specification and example files. The CLI entry point is exposed via python -m tools.render.mermaid_gantt. The engine supports two primary example targets: hello (basic usage) and program (advanced multi-track scenarios).

```mermaid
graph TB
subgraph "Tools"
RG["render.mermaid_gantt<br/>CLI + renderer"]
SPEC["95-renderer-mermaid.md<br/>Renderer Profile"]
SCHED["50-scheduling.md<br/>Scheduling Spec"]
END
subgraph "Examples"
HP["hello.plan.yaml<br/>Basic usage"]
HV["hello.views.yaml<br/>Simple view"]
PP["program.plan.yaml<br/>Advanced multi-track"]
PV["program.views.yaml<br/>Multi-lane views"]
END
RG --> HP
RG --> HV
RG --> PP
RG --> PV
SPEC --> RG
SCHED --> RG
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L466-L576)
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L1-L255)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L1-L262)
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L326)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)

**Section sources**
- [README.md](file://README.md#L68-L84)
- [SPEC.md](file://specs/v1/SPEC.md#L1-L407)

## Core Components
- Date parsing and duration parsing utilities with support for "d" (days) and "w" (weeks) units
- Business day arithmetic helpers (weekend detection, next workday, add workdays)
- Schedule computation engine with dependency resolution, cycle detection, and parent inheritance support
- **Core/Non-Core exclusion separation** with `get_core_excludes()` function
- Mermaid Gantt renderer with theme generation and lane emission
- CLI entrypoint with argument parsing and output handling
- Status-to-Mermaid tag mapping and emoji mapping for visual cues

Key responsibilities:
- Parse and validate temporal fields (start, duration) and dependencies (after).
- Compute earliest feasible dates respecting dependencies, exclusions, and optional parent inheritance.
- **Separate core exclusions ("weekends" and specific dates) from non-core exclusions** for accurate scheduling vs visualization.
- Emit Mermaid Gantt blocks with lanes, statuses, and optional emoji markers.

**Updated** Enhanced schedule computation to include core/non-core exclusion separation, where only core exclusions influence scheduling calculations while all exclusions are passed to Mermaid for visual representation.

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L92-L294)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L286-L314)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L376-L460)

## Architecture Overview
The rendering pipeline consists of:
1. Load and validate plan and views.
2. **Separate core from non-core exclusions** before computing schedule.
3. Compute schedule per node considering explicit start, dependencies, core exclusions, and optional parent inheritance.
4. Render Mermaid Gantt output with theme variables and lane sections, passing only core exclusions to Mermaid.

```mermaid
sequenceDiagram
participant CLI as "CLI"
participant Loader as "load_yaml()"
participant Renderer as "render_mermaid_gantt()"
participant Excludes as "get_core_excludes()"
participant Scheduler as "compute_schedule()"
participant Theme as "_theme_vars_from_statuses()"
participant Out as "stdout/file"
CLI->>Loader : plan.yaml
CLI->>Loader : views.yaml
CLI->>Renderer : plan, selected view
Renderer->>Excludes : split core/non-core excludes
Excludes-->>Renderer : core_excludes, non_core_excludes
Renderer->>Scheduler : nodes, core_excludes, parent inheritance
Scheduler-->>Renderer : {node_id : ScheduledNode}
Renderer->>Theme : statuses
Theme-->>Renderer : themeVariables
Renderer-->>Out : "
```mermaid ... ```"
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L466-L576)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L376-L460)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L286-L314)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L223-L321)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L344-L374)

## Detailed Component Analysis

### Core/Non-Core Exclusion Model
The renderer implements a strict separation between core and non-core exclusions to prevent visual discrepancies:

**Core Exclusions** (used in scheduling calculations):
- `"weekends"`: Excludes Saturday and Sunday from working days
- Specific dates: Individual dates like `"2024-03-08"` for business day calculations

**Non-Core Exclusions** (ignored in scheduling, only for warnings):
- `"monday"`, `"tuesday"`, etc.: Specific weekdays
- `"custom-holiday"`: Custom holiday names
- Other arbitrary strings

**Behavior**:
- Core exclusions are used for all scheduling computations
- Non-core exclusions trigger warnings but are ignored for scheduling
- Only core exclusions are passed to Mermaid for visual representation

```mermaid
flowchart TD
Start(["get_core_excludes(excludes)"]) --> Split["Split items by type"]
Split --> CheckCore{"Is 'weekends' or YYYY-MM-DD?"}
CheckCore --> |Yes| Core["Add to core_excludes"]
CheckCore --> |No| NonCore["Add to non_core_excludes"]
Core --> Warn["Issue warnings for non-core items"]
Warn --> Merge["Return (core_excludes, non_core_excludes)"]
NonCore --> Warn
Merge --> End(["Use core_excludes for scheduling"])
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L286-L314)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L346-L354)

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L286-L354)
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L101-L137)

### Scheduling Computation Algorithm
The scheduler resolves node start dates by:
- Using explicit start when present.
- Otherwise computing the start as the next working day after the latest completion of dependencies (after).
- **Optionally inheriting start from parent** when `x.scheduling.anchor_to_parent_start: true` and no explicit start or dependencies exist.
- **Applying core exclusions only** during scheduling calculations.

```mermaid
flowchart TD
Start(["resolve(node_id)"]) --> CheckCache["cached?"]
CheckCache --> |Yes| ReturnCache["return cached ScheduledNode"]
CheckCache --> |No| CheckVisiting["visiting?"]
CheckVisiting --> |Yes| CycleErr["raise SchedulingError: cycle"]
CheckVisiting --> |No| CheckExists["node exists?"]
CheckExists --> |No| RefErr["raise SchedulingError: missing node"]
CheckExists --> ParseDuration["parse_duration()"]
ParseDuration --> HasStart["has explicit start?"]
HasStart --> |Yes| ParseDate["parse_date() or use date"]
HasStart --> |No| AfterDeps["after dependencies?"]
AfterDeps --> |Yes| ResolveDeps["resolve(dep) for all deps"]
ResolveDeps --> LatestFinish["max(dep.finish)"]
LatestFinish --> CoreExcludes["get_core_excludes(excludes)"]
CoreExcludes --> WeekendAdj{"exclude weekends?"}
WeekendAdj --> |Yes| NextWD["next_workday(latest, core_excludes)"]
WeekendAdj --> |No| NextDay["latest + 1 day"]
NextWD --> MakeStart["start = next_working_day"]
NextDay --> MakeStart
AfterDeps --> |No| ParentAnchor["check parent inheritance"]
ParentAnchor --> CheckAnchor{"anchor_to_parent_start?"}
CheckAnchor --> |Yes| ParentStart["parent exists?"]
ParentStart --> |Yes| UseParent["start = parent.start"]
ParentStart --> |No| NoStart["no start found"]
CheckAnchor --> |No| NoStart
UseParent --> MakeStart
NoStart --> NoSchedule["return None (container-like)"]
MakeStart --> FinishCalc["finish_date(start, duration, core_excludes)"]
FinishCalc --> Cache["cache[node_id] = ScheduledNode"]
Cache --> ReturnRes["return ScheduledNode"]
```

**Updated** Added core exclusion separation and parent inheritance logic with the `x.scheduling.anchor_to_parent_start` extension check.

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L246-L311)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L281-L299)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L112-L158)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L165-L192)

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L223-L321)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L82-L149)

### Renderer Profile: Mermaid Gantt
The Mermaid Gantt renderer provides reference implementation behavior with specific defaults and non-core extensions.

#### Default Behaviors
- **Duration Default**: If node lacks `duration`, renderer uses **1 day** (`1d`) instead of core specification's undefined behavior.
- **Unscheduled Nodes**: Nodes without calculable start dates are **skipped** without error, with optional informational warnings.

#### Core/Non-Core Exclusion Model
**Core Exclusions** (affect scheduling):
- `"weekends"`: Excludes Saturday and Sunday from working days
- Specific dates: Individual dates like `"2024-03-08"` for business day calculations

**Non-Core Exclusions** (ignored in scheduling):
- `"monday"`, `"tuesday"`, etc.: Specific weekdays
- `"custom-holiday"`: Custom holiday names
- Other arbitrary strings

**Behavior**:
- Core exclusions are used for all scheduling computations
- Non-core exclusions trigger warnings but are ignored for scheduling
- Only core exclusions are passed to Mermaid for visual representation

#### Parent-Child Inheritance Extension
The renderer supports optional `x.scheduling.anchor_to_parent_start` for inheritance:

**Semantics**:
1. **If node has no `start` and no `after`**: `effective_start(child) = effective_start(parent)`
2. **If node has `after` (but no `start`)**: `effective_start = max(start_from_after, effective_start(parent))`
3. **If node has explicit `start`**: Uses explicit `start` (extension has no effect)

**Important**: This extension is **non-core** and renderer-specific. Other tools are not required to support it.

**Section sources**
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L7-L74)
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L101-L137)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L281-L299)

### Weekend Exclusion Logic and Business Day Arithmetic
- Weekend detection uses standard weekday semantics (Saturday and Sunday).
- Next workday advances a date until a non-weekend day is found.
- Adding workdays iterates day-by-day, skipping weekends when excluded.
- Finish date calculation respects duration and weekend exclusion.

```mermaid
flowchart TD
D0["start date"] --> WDCheck{"is weekend?"}
WDCheck --> |Yes| Inc1["add 1 day"] --> WDCheck
WDCheck --> |No| DoneNext["return start or next workday"]
DoneNext --> AddWD["add_workdays(start, workdays, excludes)"]
AddWD --> Step["while remaining > 0:<br/>advance by step sign"]
Step --> IsWD{"is workday?"}
IsWD --> |Yes| Dec["remaining -= 1"]
IsWD --> |No| Skip["skip (remaining unchanged)"]
Skip --> Step
Dec --> Step
Step --> DoneWD["return final date"]
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L165-L192)

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L160-L192)

### Enhanced Weekend Exclusion Handling
The renderer supports both "weekends" exclusion and specific date exclusions:

**Supported Exclusions**:
- `"weekends"`: Excludes Saturday and Sunday from working days
- Specific dates: Individual dates like `"2024-03-08"` for visual marking
- Multiple exclusions: Arrays combining weekends with specific dates

**Core vs Non-Core Behavior**:
- **Core exclusions** (`"weekends"` and `"YYYY-MM-DD"`) affect scheduling calculations
- **Non-core exclusions** (like `"monday"`, `"custom-holiday"`) are ignored in scheduling but trigger warnings
- **All exclusions** are passed to Mermaid for visual representation

**Section sources**
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L101-L121)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L10)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L286-L314)

### View Configuration Options and Lane Organization
- Views define gantt_views with title, excludes, and lanes.
- Lanes group node IDs into sections for the Gantt.
- Excludes supports calendar exclusions; weekends and specific dates are supported.

```mermaid
classDiagram
class View {
+string title
+string[] excludes
+map~string, Lane~ lanes
}
class Lane {
+string title
+string[] nodes
}
View --> Lane : "contains"
```

**Diagram sources**
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L189-L216)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L12-L28)

**Section sources**
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L189-L216)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)

### Status Theming, Color Coding, and Emoji Support
- Status-to-Mermaid tag mapping enables Mermaid-specific styling keywords.
- Status-to-color mapping drives theme variables for Mermaid.
- Status-to-emoji mapping adds visual cues directly in task labels.

```mermaid
classDiagram
class StatusMapping {
+map~string,string~ STATUS_TO_MERMAID_TAG
+map~string,string~ STATUS_TO_EMOJI
}
class ThemeVars {
+map~string,string~ themeVariables
}
StatusMapping --> ThemeVars : "drives"
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L327-L342)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L344-L374)

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L327-L374)
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L75-L99)

### Rendering Pipeline to Mermaid Output
- The renderer builds a Mermaid block with init theme variables, title, date format, optional axis format, and optional weekend exclusion.
- It emits sections per lane and tasks with optional Mermaid tags and emoji prefixes.
- **Only core exclusions are passed to Mermaid** to maintain consistency between calculated schedules and visual representation.

```mermaid
sequenceDiagram
participant R as "render_mermaid_gantt"
participant E as "get_core_excludes()"
participant T as "theme vars"
participant L as "lanes"
participant O as "Mermaid output"
R->>E : split excludes into core/non-core
E-->>R : core_excludes, non_core_excludes
R->>T : statuses
T-->>R : themeVariables
R->>L : iterate lanes
loop for each node in lane
R->>R : fetch ScheduledNode
alt has ScheduledNode
R->>O : append task line with optional tag and emoji
else
R->>R : skip (container-like)
end
end
R-->>O : finalize block with core excludes only
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L376-L460)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L551-L583)

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L376-L460)

### CLI Usage Examples and Output Formatting
- CLI supports loading plan and views, selecting a view, listing available views, and writing output to a file or stdout.
- Output is a fenced Mermaid block suitable for Markdown consumption.

Example invocations:
- List views: python -m tools.render.mermaid_gantt --plan examples/hello/hello.plan.yaml --views examples/hello/hello.views.yaml --list-views
- Render a view: python -m tools.render.mermaid_gantt --plan examples/hello/hello.plan.yaml --views examples/hello/hello.views.yaml --view overview
- Save to file: python -m tools.render.mermaid_gantt --plan examples/hello/hello.plan.yaml --views examples/hello/hello.views.yaml --view overview --output gantt.md

Output formatting options:
- title from view or plan meta.
- date_format and axis_format from view.
- excludes controls weekend exclusion and can include specific dates.

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L466-L576)
- [README.md](file://README.md#L78-L84)
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L189-L216)

### Python API for Programmatic Rendering
- render_mermaid_gantt(plan: Dict[str, Any], view: Dict[str, Any]) -> str
- Intended for embedding in larger toolchains or notebooks.

Integration with visualization tools:
- The output is a Mermaid Gantt block; render it with any Mermaid-compatible Markdown viewer or static site generator.

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L376-L460)

### Data Structures Used for Scheduled Nodes
- ScheduledNode: immutable record containing start date, finish date, and integer duration in days.

```mermaid
classDiagram
class ScheduledNode {
+date start
+date finish
+int duration_days
}
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L215-L221)

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L215-L221)

### Performance Considerations
- Topological resolution with memoization and a visiting-set prevents recomputation and detects cycles efficiently.
- Duration parsing and date arithmetic are linear-time per node.
- **Core exclusion separation** adds minimal overhead with regex pattern matching.
- For very large plans, consider:
  - Pre-validating with the validator to catch errors early.
  - Limiting view scope to relevant lanes.
  - Avoiding excessive nested parents that inflate dependency depth.
  - Ensuring durations are reasonable to reduce date arithmetic overhead.

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L242-L321)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L286-L314)

### Customization Options
- View-level:
  - title, date_format, axis_format, excludes (supports weekends and specific dates).
  - lanes organize nodes into sections.
- Status-level:
  - statuses define color hex values used for theming.
- Node-level:
  - status influences both Mermaid tags and emoji.
  - **Parent inheritance**: `x.scheduling.anchor_to_parent_start: true` enables inheritance from parent when no explicit start is given.
  - **Core/non-core exclusions**: `excludes` supports both core exclusions (weekends, specific dates) and non-core exclusions (with warnings).

**Updated** Added core/non-core exclusion customization option.

**Section sources**
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L189-L216)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L141-L150)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L281-L299)

### Export Formats and Integration
- The renderer produces a Mermaid Gantt fenced block intended for Markdown consumption.
- Integration examples:
  - Obsidian, LogSeq, Typora, or any Markdown preview supporting Mermaid.
  - Static site generators (e.g., MkDocs, Docusaurus) with Mermaid plugins.
  - CI/CD pipelines to generate and commit Gantt diagrams.

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L376-L460)

## Dependency Analysis
The rendering engine depends on:
- Plan and view schemas and validation rules.
- Mermaid-specific rendering semantics (tags, theme variables).
- Business rules for scheduling and exclusions.

```mermaid
graph TB
PLAN["hello.plan.yaml / program.plan.yaml"]
VIEWS["hello.views.yaml / program.views.yaml"]
RENDER["render.mermaid_gantt.py"]
SPEC["95-renderer-mermaid.md"]
SCHED["50-scheduling.md"]
PLAN --> RENDER
VIEWS --> RENDER
SPEC --> RENDER
SCHED --> RENDER
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L466-L576)
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L326)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L1-L255)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L1-L262)

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L241-L356)

## Performance Considerations
- Complexity:
  - compute_schedule performs DFS with memoization; worst-case O(V + E) per node resolved.
  - Date arithmetic is O(n) for adding workdays where n is the number of days.
  - **Core exclusion separation** adds O(n) regex pattern matching per exclusion item.
- Recommendations:
  - Keep views scoped to relevant lanes to reduce emission overhead.
  - Validate with the validator to detect cycles and invalid references before rendering.
  - Prefer compact dependency graphs; avoid deep chains of after dependencies when not necessary.
  - **Limit non-core exclusions** to reduce warning messages and processing overhead.

## Troubleshooting Guide
Common issues and resolutions:
- Missing or invalid YAML:
  - Ensure files are valid YAML and readable; the loader raises file-related errors.
- Unsupported duration format:
  - Use integer or "<number>d" or "<number>w"; otherwise a scheduling error is raised.
- Invalid date format:
  - Use "YYYY-MM-DD" for start fields.
- Cyclic dependencies:
  - The scheduler detects cycles via visiting sets; fix the graph so after and parent references form a DAG.
- Reference errors:
  - The validator checks parent, after, and status references; ensure all IDs exist and match statuses.
- Non-existent view:
  - Use --list-views to discover available view IDs; select one present in gantt_views.
- Output not rendering:
  - Verify the emitted fenced block is placed in a Markdown-compatible environment with Mermaid support.
- **Parent inheritance not working**:
  - Ensure `x.scheduling.anchor_to_parent_start: true` is set in the child node.
  - Verify the parent node has a calculable start date.
  - Note that this is a renderer-specific extension, not part of core specification.
- **Non-core exclusion warnings**:
  - Non-core exclusions (like `"monday"`, `"custom-holiday"`) are intentionally ignored in scheduling calculations.
  - These exclusions still appear in the rendered diagram but don't affect computed schedules.
  - Remove non-core exclusions if they cause confusion or use only core exclusions for clarity.

**Updated** Added troubleshooting guidance for core/non-core exclusion model and parent inheritance feature.

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L49-L86)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L112-L158)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L249-L252)
- [README.md](file://README.md#L78-L84)

## Conclusion
The opskarta Mermaid Gantt rendering engine computes accurate schedules from explicit starts and dependencies, enforces weekend exclusion when configured, and renders a ready-to-use Mermaid block with theming and emoji. Its modular design integrates cleanly with validation and supports flexible view configuration, making it suitable for automated documentation pipelines and interactive dashboards. The renderer profile provides additional capabilities including parent-child inheritance, enhanced weekend exclusion handling with support for both "weekends" and specific date exclusions, and the new core/non-core exclusion model that ensures consistency between calculated schedules and visual representation.

## Appendices

### Example Inputs and Outputs
- Minimal plan and view examples demonstrate basic usage and weekend exclusion.
- Advanced example shows multi-lane, multi-track Gantt with critical path emphasis.

**Section sources**
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L326)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)

### Renderer Profile Details
The Mermaid Gantt renderer implements specific behaviors beyond core specification:

- **Duration Default**: 1 day for nodes without duration
- **Unscheduled Node Handling**: Skips nodes without calculable start dates
- **Core/Non-Core Exclusion Model**: Separates scheduling exclusions from visual exclusions
- **Parent Inheritance**: Optional `x.scheduling.anchor_to_parent_start` extension
- **Enhanced Weekend Exclusion**: Supports `excludes: ["weekends"]` with visual holiday markers
- **Multiple Exclusion Types**: Supports both "weekends" and specific date exclusions
- **Output Format**: Standard Mermaid Gantt fenced block with theme variables

**Section sources**
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L7-L121)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L376-L460)

### Core/Non-Core Exclusion Examples
**Core Exclusions** (affect scheduling):
- `"weekends"`: Excludes Saturday and Sunday
- `"2024-03-08"`: Specific holiday date

**Non-Core Exclusions** (ignored in scheduling):
- `"monday"`: Specific weekday exclusion
- `"custom-holiday"`: Custom holiday name

**Section sources**
- [95-renderer-mermaid.md](file://specs/v1/spec/95-renderer-mermaid.md#L101-L137)
- [non_core_excludes.views.yaml](file://specs/v1/tests/fixtures/non_core_excludes.views.yaml#L8-L12)
- [date_excludes.views.yaml](file://specs/v1/tests/fixtures/date_excludes.views.yaml#L8-L10)