# Temporal Planning and Scheduling

<cite>
**Referenced Files in This Document**
- [SPEC.md](file://specs/v1/SPEC.md)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md)
- [60-validation.md](file://specs/v1/spec/60-validation.md)
- [validate.py](file://specs/v1/tools/validate.py)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json)
- [views.schema.json](file://specs/v1/schemas/views.schema.json)
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml)
- [README.md (Advanced Examples)](file://specs/v1/examples/advanced/README.md)
- [test_scheduling.py](file://specs/v1/tests/test_scheduling.py)
- [weeks_duration.plan.yaml](file://specs/v1/tests/fixtures/weeks_duration.plan.yaml)
- [weekends_exclusion.plan.yaml](file://specs/v1/tests/fixtures/weekends_exclusion.plan.yaml)
</cite>

## Update Summary
**Changes Made**
- Updated duration parsing to support weeks ('w') units with comprehensive testing
- Enhanced weekend exclusion handling with improved business day arithmetic
- Added comprehensive validation for new scheduling features
- Updated dependency computation algorithms with better error handling
- Expanded scheduling specification with new duration formats and weekend exclusion rules

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
This document explains temporal planning and scheduling for operational maps in opskarta v1. It covers:
- Two scheduling approaches: explicit scheduling via start dates and durations, and implicit scheduling via dependency resolution.
- Automatic date calculation engine, including business day arithmetic and weekend exclusion logic.
- How dependencies drive schedule computation and critical path determination.
- Examples of schedule computation, date propagation through hierarchies, and conflict resolution.
- Scheduling validation rules, constraint checking, and performance considerations for large operational maps.
- Edge cases such as circular dependencies, missing dates, and schedule updates.

**Updated** Enhanced with comprehensive weeks duration support and improved weekend exclusion handling.

## Project Structure
The scheduling and rendering logic is implemented in Python tools under specs/v1/tools. The specification and examples live under specs/v1.

```mermaid
graph TB
subgraph "Specification"
S1["specs/v1/spec/50-scheduling.md"]
S2["specs/v1/spec/60-validation.md"]
S3["specs/v1/SPEC.md"]
end
subgraph "Schemas"
J1["specs/v1/schemas/plan.schema.json"]
J2["specs/v1/schemas/views.schema.json"]
end
subgraph "Tools"
T1["specs/v1/tools/validate.py"]
T2["specs/v1/tools/render/mermaid_gantt.py"]
end
subgraph "Tests & Fixtures"
TE1["specs/v1/tests/test_scheduling.py"]
TE2["specs/v1/tests/fixtures/weeks_duration.plan.yaml"]
TE3["specs/v1/tests/fixtures/weekends_exclusion.plan.yaml"]
end
subgraph "Examples"
E1["specs/v1/examples/hello/hello.plan.yaml"]
E2["specs/v1/examples/hello/hello.views.yaml"]
E3["specs/v1/examples/advanced/program.plan.yaml"]
E4["specs/v1/examples/advanced/program.views.yaml"]
end
S1 --> T2
S2 --> T1
J1 --> T1
J2 --> T1
T1 --> E1
T2 --> E1
T2 --> E3
T2 --> E4
TE1 --> T2
TE2 --> T2
TE3 --> T2
```

**Diagram sources**
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L1-L247)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L1-L140)
- [validate.py](file://specs/v1/tools/validate.py#L135-L782)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L217-L576)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L66)
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L326)
- [test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L1-L305)
- [weeks_duration.plan.yaml](file://specs/v1/tests/fixtures/weeks_duration.plan.yaml#L1-L24)
- [weekends_exclusion.plan.yaml](file://specs/v1/tests/fixtures/weekends_exclusion.plan.yaml#L1-L21)

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L1-L407)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L1-L247)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L1-L140)

## Core Components
- Explicit scheduling: start date and duration define a task's timeline segment.
- Implicit scheduling: start is derived from dependencies (after) and/or parent inheritance.
- Business day arithmetic: weekend exclusion and workday addition for duration calculation.
- Dependency graph validation: cycles and dangling references are detected during semantic validation.
- Rendering: Mermaid Gantt generation from computed schedules and view exclusions.

**Updated** Enhanced duration parsing now supports both days ('d') and weeks ('w') units, where 1 week equals 5 working days.

Key implementation references:
- Scheduling engine and business day helpers: [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L92-L207)
- Schedule computation with dependency resolution and parent inheritance: [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L223-L321)
- Validation of plan semantics (cycles, dangling refs, formats): [validate.py](file://specs/v1/tools/validate.py#L135-L414)
- Scheduling spec and notes: [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L1-L247), [SPEC.md](file://specs/v1/SPEC.md#L159-L239)

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L92-L207)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L223-L321)
- [validate.py](file://specs/v1/tools/validate.py#L135-L414)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L1-L247)
- [SPEC.md](file://specs/v1/SPEC.md#L159-L239)

## Architecture Overview
The scheduling pipeline transforms plan nodes into scheduled segments using explicit dates, dependency resolution, and business-day arithmetic. Views configure calendar exclusions and lane selection for rendering.

```mermaid
sequenceDiagram
participant Plan as "Plan YAML"
participant View as "Views YAML"
participant Sched as "compute_schedule()"
participant BD as "Business Day Helpers"
participant Render as "render_mermaid_gantt()"
participant Out as "Mermaid Gantt"
Plan->>Sched : nodes, durations (d/w), starts, after, parent
View->>Render : gantt_view config (excludes : weekends, dates)
Sched->>BD : parse_date(), parse_duration(), finish_date(), add_workdays()
Sched-->>Render : {node_id : ScheduledNode}
Render->>Out : generate Gantt with dateFormat, excludes, lanes
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L223-L321)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L92-L207)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L376-L460)

## Detailed Component Analysis

### Scheduling Engine and Business Day Arithmetic
The scheduling engine computes per-node start/finish/duration considering:
- Explicit start and duration.
- Dependencies (after) resolved transitively; start becomes latest dependency finish + 1 day (or next workday if excluding weekends).
- Parent inheritance: if no start/after, child may inherit parent start.
- Duration parsing supports integer days, "Nd" format, and "Nw" format (1w = 5 working days).
- Weekend exclusion toggled by view excludes.

**Updated** Enhanced duration parsing now comprehensively handles weeks ('w') units with proper validation and conversion to working days.

```mermaid
flowchart TD
Start(["resolve(node_id)"]) --> CheckCache["cached?"]
CheckCache --> |Yes| ReturnCache["return ScheduledNode"]
CheckCache --> |No| CheckCycle["visiting?"]
CheckCycle --> |Yes| ErrorCycle["raise SchedulingError: cycle"]
CheckCycle --> |No| LoadNode["load node"]
LoadNode --> ParseDur["parse_duration()"]
ParseDur --> HasStart["has explicit start?"]
HasStart --> |Yes| FinishExplicit["finish_date(start, dur, exclude)"]
HasStart --> |No| AfterDeps["after deps exist?"]
AfterDeps --> |Yes| ResolveDeps["resolve(dep) for all deps"]
ResolveDeps --> Latest["latest(dep.finish)"]
Latest --> NextWD{"exclude weekends?"}
NextWD --> |Yes| StartNextWD["next_workday(latest)"]
NextWD --> |No| StartNextDay["latest + 1 day"]
StartNextWD --> FinishImplicit["finish_date(start, dur, exclude)"]
StartNextDay --> FinishImplicit
AfterDeps --> |No| TryParent["try parent.start"]
TryParent --> ParentOk{"parent cached?"}
ParentOk --> |Yes| FinishImplicitFromParent["finish_date(parent.start, dur, exclude)"]
ParentOk --> |No| Skip["return None (no schedule)"]
FinishExplicit --> Store["cache ScheduledNode"]
FinishImplicit --> Store
FinishImplicitFromParent --> Store
Store --> End(["return ScheduledNode"])
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L246-L321)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L112-L207)

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L223-L321)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L92-L207)

### Dependency Resolution and Critical Path Determination
- Dependencies are modeled as a directed acyclic graph (DAG) via after lists.
- Critical path is the longest path in the DAG; it determines earliest possible completion of dependent tasks.
- The scheduler resolves each node by computing the latest finish among dependencies and advancing to the next working day when applicable.
- Cycles are prevented by validation and runtime checks.

**Updated** Improved dependency computation with enhanced error handling and better parent inheritance logic.

```mermaid
flowchart TD
A["Node A"] --> B["Node B (after: [A])"]
A --> C["Node C (after: [A])"]
B --> D["Node D (after: [B])"]
C --> D
D --> E["Node E (after: [C,D])"]
E --> F["Node F (after: [E])"]
style F stroke-dasharray: 0
```

**Diagram sources**
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L47-L66)
- [validate.py](file://specs/v1/tools/validate.py#L370-L414)

**Section sources**
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L47-L66)
- [validate.py](file://specs/v1/tools/validate.py#L370-L414)

### Automatic Date Calculation Engine
- Date parsing enforces ISO 8601 date strings.
- Duration parsing supports integers, "Nd" format, and "Nw" format (1w = 5 working days).
- Workday arithmetic:
  - Weekend detection uses weekday mapping.
  - Add workdays iterates calendar days, skipping weekends.
  - Finish date uses either inclusive-day semantics for 1-day duration or adds workdays minus 1.

**Updated** Comprehensive duration parsing with weeks support and improved validation logic.

```mermaid
flowchart TD
P["parse_duration(value)"] --> IsNone{"value is None?"}
IsNone --> |Yes| D1["return 1"]
IsNone --> |No| IsInt{"is int?"}
IsInt --> |Yes| PosInt{"> 0?"}
PosInt --> |No| ErrDur["raise SchedulingError"]
PosInt --> |Yes| RetInt["return value"]
IsInt --> |No| IsStr{"is string?"}
IsStr --> |Yes| DigitOnly{"digits only?"}
DigitOnly --> |Yes| RetStrInt["return int(value)"]
DigitOnly --> |No| EndsD{"ends with 'd'?"}
EndsD --> |Yes| PosD{"> 0?"}
PosD --> |No| ErrDur
PosD --> |Yes| RetD["return digits before 'd'"]
EndsD --> |No| EndsW{"ends with 'w'?"}
EndsW --> |Yes| PosW{"> 0?"}
PosW --> |No| ErrDur
PosW --> |Yes| RetW["return digits before 'w' * 5"]
EndsW --> |No| ErrDur
IsStr --> |No| ErrDur
```

**Diagram sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L112-L158)

**Section sources**
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L92-L207)

### Schedule Computation Examples
- Example: Hello Upgrade program demonstrates explicit start and after dependencies with weekend exclusion.
- Example: Advanced Program shows cross-track dependencies and multiple lanes with holiday exclusions.

**Updated** Added comprehensive examples demonstrating weeks duration and weekend exclusion handling.

References:
- Hello plan and views: [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44), [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)
- Advanced plan and views: [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L326), [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)
- Weeks duration fixture: [weeks_duration.plan.yaml](file://specs/v1/tests/fixtures/weeks_duration.plan.yaml#L1-L24)
- Weekends exclusion fixture: [weekends_exclusion.plan.yaml](file://specs/v1/tests/fixtures/weekends_exclusion.plan.yaml#L1-L21)

**Section sources**
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L326)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)
- [weeks_duration.plan.yaml](file://specs/v1/tests/fixtures/weeks_duration.plan.yaml#L1-L24)
- [weekends_exclusion.plan.yaml](file://specs/v1/tests/fixtures/weekends_exclusion.plan.yaml#L1-L21)

### Conflict Resolution and Updates
- Conflicts arise when dependencies cannot be satisfied (e.g., cycles) or when required dates are missing.
- Resolution strategies:
  - Fix cycles in after dependencies.
  - Provide explicit start or resolve dependencies to establish a baseline.
  - Adjust durations or exclusions to meet constraints.
- Updates propagate forward: changing a dependency's finish advances downstream nodes accordingly.

**Updated** Enhanced conflict resolution with improved error reporting for weeks duration and weekend exclusion scenarios.

Validation ensures correctness before rendering.

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L335-L414)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L223-L321)

## Dependency Analysis
The scheduling and validation logic depends on:
- Plan schema for structural validation.
- Views schema for view-level constraints.
- Python YAML loader for parsing.
- Business day helpers for date arithmetic.

```mermaid
graph LR
Plan["plan.yaml"] --> V["validate.py"]
Views["views.yaml"] --> V
Plan --> R["render/mermaid_gantt.py"]
Views --> R
V --> PlanSchema["plan.schema.json"]
V --> ViewsSchema["views.schema.json"]
R --> BD["business day helpers"]
```

**Diagram sources**
- [validate.py](file://specs/v1/tools/validate.py#L135-L782)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L223-L576)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L66)

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L135-L782)
- [mermaid_gantt.py](file://specs/v1/tools/render/mermaid_gantt.py#L223-L576)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L66)

## Performance Considerations
- Topological resolution: The scheduler uses a recursive resolver with memoization and a visiting-state to detect cycles and avoid recomputation. Complexity is O(V + E) per node resolved, with caching reducing repeated work.
- Large maps: Prefer precomputing and caching schedules; avoid redundant passes over the graph.
- Exclusions: Weekend exclusion adds iteration per workday; keep exclusions minimal or precompute extended calendars for very large datasets.
- Rendering: Limit visible lanes and date ranges to reduce output size and improve readability.

**Updated** Performance considerations now account for weeks duration calculations and improved weekend exclusion handling.

## Troubleshooting Guide
Common issues and resolutions:
- Circular dependencies in after lists: Detected by DFS with state tracking; fix by removing or altering edges.
- Non-existent parent or dependency references: Detected during validation; ensure all IDs exist in nodes.
- Invalid date or duration formats: Detected by format validators; correct to ISO date and "Nd"/"Nw".
- Missing start and after: Node remains unscheduled; add explicit start or dependencies.
- Exclusions mismatch: Verify view excludes align with intended calendar behavior.
- Weeks duration errors: Ensure weeks format follows "Nw" pattern with positive integer values.

**Updated** Added troubleshooting guidance for weeks duration and weekend exclusion scenarios.

Validation messages include:
- Field path, value, expected format, and available options.

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L135-L782)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L1-L140)

## Conclusion
opskarta v1 provides a robust, extensible framework for temporal planning:
- Explicit scheduling for deterministic control.
- Implicit scheduling driven by dependencies and hierarchy.
- Business-day-aware calculations with weekend exclusion.
- Strong validation against cycles, dangling references, and format errors.
- Practical examples demonstrate cross-track dependencies, calendar exclusions, and critical path focus.

**Updated** Enhanced with comprehensive weeks duration support and improved weekend exclusion handling for more flexible scheduling scenarios.

## Appendices

### Scheduling Specification Highlights
- Fields: start (ISO date), duration ("Nd" or "Nw"), after (list of node IDs).
- Interaction with views: excludes (weekends and specific dates), lanes.
- Notes: If neither start nor after is present, a node is considered unscheduled.

**Updated** Enhanced duration format specification with weeks support.

**Section sources**
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L1-L247)
- [SPEC.md](file://specs/v1/SPEC.md#L159-L239)

### Example Workflows
- Hello Upgrade: Demonstrates phased work with after dependencies and weekend exclusion.
- Advanced Program: Cross-track dependencies, multiple views, and holiday exclusions.
- Weeks Duration Testing: Demonstrates 1w = 5 working days calculation.
- Weekend Exclusion Testing: Demonstrates proper weekend skipping in schedule computation.

**Updated** Added comprehensive examples for weeks duration and weekend exclusion scenarios.

**Section sources**
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L326)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)
- [README.md (Advanced Examples)](file://specs/v1/examples/advanced/README.md#L82-L113)
- [weeks_duration.plan.yaml](file://specs/v1/tests/fixtures/weeks_duration.plan.yaml#L1-L24)
- [weekends_exclusion.plan.yaml](file://specs/v1/tests/fixtures/weekends_exclusion.plan.yaml#L1-L21)