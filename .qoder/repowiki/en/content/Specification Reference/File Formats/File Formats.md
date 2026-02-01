# File Formats

<cite>
**Referenced Files in This Document**
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json)
- [views.schema.json](file://specs/v1/schemas/views.schema.json)
- [10-plan-file.md](file://specs/v1/spec/10-plan-file.md)
- [20-nodes.md](file://specs/v1/spec/20-nodes.md)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md)
- [55-yaml-notes.md](file://specs/v1/spec/55-yaml-notes.md)
- [60-validation.md](file://specs/v1/spec/60-validation.md)
- [90-extensibility.md](file://specs/v1/spec/90-extensibility.md)
- [SPEC.md](file://specs/v1/SPEC.md)
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml)
- [project.plan.yaml](file://specs/v1/examples/minimal/project.plan.yaml)
- [finish_field.plan.yaml](file://specs/v1/tests/fixtures/finish_field.plan.yaml)
- [validate.py](file://specs/v1/tools/validate.py)
</cite>

## Update Summary
**Changes Made**
- Enhanced YAML processing guidelines with comprehensive date normalization requirements
- Added explicit finish field validation rules and improved encoding standards
- Updated validation system to include robust date type handling and normalization
- Expanded YAML encoding guidelines to address YAML 1.1 auto-typification issues
- Improved error messaging and validation levels for better developer experience

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Enhanced YAML Processing Guidelines](#enhanced-yaml-processing-guidelines)
7. [Finish Field Specification](#finish-field-specification)
8. [Improved Validation System](#improved-validation-system)
9. [Dependency Analysis](#dependency-analysis)
10. [Performance Considerations](#performance-considerations)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Conclusion](#conclusion)
13. [Appendices](#appendices)

## Introduction
This document describes the opskarta v1 file formats that define operational maps:
- Plan files (*.plan.yaml): describe the work items, hierarchy, scheduling, statuses, and metadata.
- Views files (*.views.yaml): define how to present the plan (e.g., Gantt views) and organize lanes for visualization.

It explains the complete structure of both file types, their interplay, JSON Schema definitions, validation rules, recommended practices, and examples from the repository's hello and advanced samples. The documentation now includes comprehensive YAML processing guidelines, enhanced validation system with date normalization, and detailed coverage of the finish field specification.

## Project Structure
The opskarta v1 specification organizes documentation and examples under specs/v1:
- schemas: JSON Schema definitions for plan and views files.
- spec: Markdown documents detailing each aspect of the format, including enhanced YAML processing guidelines and finish field documentation.
- examples: Minimal, hello, and advanced examples demonstrating usage.
- tests: Fixtures and test cases validating finish field functionality.
- tools: Validation utilities with comprehensive YAML date normalization support.

```mermaid
graph TB
subgraph "Specs v1"
S1["schemas/plan.schema.json"]
S2["schemas/views.schema.json"]
D1["spec/10-plan-file.md"]
D2["spec/20-nodes.md"]
D3["spec/30-views-file.md"]
D4["spec/40-statuses.md"]
D5["spec/50-scheduling.md"]
D6["spec/55-yaml-notes.md"]
D7["spec/60-validation.md"]
D9["spec/90-extensibility.md"]
E_hello_plan["examples/hello/hello.plan.yaml"]
E_hello_views["examples/hello/hello.views.yaml"]
E_adv_plan["examples/advanced/program.plan.yaml"]
E_adv_views["examples/advanced/program.views.yaml"]
E_min_plan["examples/minimal/project.plan.yaml"]
F_finish["tests/fixtures/finish_field.plan.yaml"]
T_validate["tools/validate.py"]
end
```

**Diagram sources**
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L95)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)
- [10-plan-file.md](file://specs/v1/spec/10-plan-file.md#L1-L30)
- [20-nodes.md](file://specs/v1/spec/20-nodes.md#L1-L37)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md#L1-L34)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md#L1-L23)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L1-L474)
- [55-yaml-notes.md](file://specs/v1/spec/55-yaml-notes.md#L1-L137)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L1-L377)
- [90-extensibility.md](file://specs/v1/spec/90-extensibility.md#L1-L26)
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L331)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)
- [project.plan.yaml](file://specs/v1/examples/minimal/project.plan.yaml#L1-L6)
- [finish_field.plan.yaml](file://specs/v1/tests/fixtures/finish_field.plan.yaml#L1-L30)
- [validate.py](file://specs/v1/tools/validate.py#L114-L133)

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L1-L407)

## Core Components
- Plan file (*.plan.yaml)
  - Root fields: version, meta, statuses, nodes.
  - Meta: id and title; id binds to views via project.
  - Statuses: arbitrary map of status keys to objects with label and color.
  - Nodes: map of node_id to node objects; each node requires title and supports kind, status, parent, after, start, finish, duration, issue, notes.
- Views file (*.views.yaml)
  - Root fields: version, project, gantt_views.
  - project must match plan.meta.id.
  - gantt_views: named views with title, calendar excludes, and lanes.
  - lanes: per-view grouping of node_ids for visualization.

**Section sources**
- [10-plan-file.md](file://specs/v1/spec/10-plan-file.md#L1-L30)
- [20-nodes.md](file://specs/v1/spec/20-nodes.md#L1-L37)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md#L1-L34)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md#L1-L23)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L1-L140)
- [SPEC.md](file://specs/v1/SPEC.md#L27-L56)

## Architecture Overview
Plan and views files work together to define an operational map:
- Plan defines the work model (metadata, statuses, hierarchical nodes, scheduling).
- Views define presentation layers (Gantt views, lanes) over the plan.
- Validation ensures referential integrity across files and within each file.
- Enhanced YAML processing handles date normalization and encoding standards.

```mermaid
graph TB
P["Plan (*.plan.yaml)"]
V["Views (*.views.yaml)"]
S_P["Schema: plan.schema.json"]
S_V["Schema: views.schema.json"]
VLD["Enhanced Validation"]
NORM["Date Normalization"]
P --> S_P
V --> S_V
P --> VLD
V --> VLD
V --> |"project must equal plan.meta.id"| P
P --> NORM
V --> NORM
```

**Diagram sources**
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L95)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L82-L100)
- [validate.py](file://specs/v1/tools/validate.py#L114-L133)

## Detailed Component Analysis

### Plan File (*.plan.yaml)
Structure and semantics:
- version: integer ≥ 1.
- meta: object with id and title; both required.
- statuses: object; recommended keys include not_started, in_progress, done, blocked; each status object has label and color.
- nodes: object of node_id → node; each node requires title; recommended fields include kind, status, parent, after, start (YYYY-MM-DD), finish (YYYY-MM-DD), duration (<digits>d or <digits>w), issue, notes.

**Updated** Enhanced node specification to include the new finish field alongside existing scheduling fields with comprehensive validation.

Optional and extension fields:
- additionalProperties allowed at top level and within meta, statuses, and nodes.
- Custom extensions can be added; see extensibility guidance.

Relationship to views:
- plan.meta.id is matched by views.project.

Practical examples:
- hello.plan.yaml demonstrates a small plan with statuses, nodes hierarchy, and scheduling.
- program.plan.yaml demonstrates a large, multi-track plan with extensive hierarchy and custom extensions under x.

Common pitfalls and fixes:
- Missing title in a node.
- Non-existing parent or after references.
- Non-existing status key.
- Incorrect date or duration formats.
- **Updated** Finish field format validation and consistency checking with enhanced YAML processing.

```mermaid
flowchart TD
Start(["Load *.plan.yaml"]) --> CheckVersion["Check 'version' type and value"]
CheckVersion --> CheckMeta["Check 'meta' has 'id' and 'title'"]
CheckMeta --> CheckNodes["For each node: require 'title'"]
CheckNodes --> NormalizeDates["Normalize YAML dates to YYYY-MM-DD"]
NormalizeDates --> ValidateFinish["Validate 'finish' format (YYYY-MM-DD)"]
ValidateFinish --> CheckConsistency["Check 'start'/'finish'/'duration' consistency"]
CheckConsistency --> OptionalFields["Allow additionalProperties"]
OptionalFields --> Done(["Ready for validation"])
```

**Diagram sources**
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L6-L15)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L16-L33)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L38-L95)
- [20-nodes.md](file://specs/v1/spec/20-nodes.md#L5-L37)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L7-L11)
- [validate.py](file://specs/v1/tools/validate.py#L114-L133)

**Section sources**
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L95)
- [10-plan-file.md](file://specs/v1/spec/10-plan-file.md#L3-L10)
- [20-nodes.md](file://specs/v1/spec/20-nodes.md#L5-L37)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md#L12-L16)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L5-L11)
- [SPEC.md](file://specs/v1/SPEC.md#L27-L56)

### Views File (*.views.yaml)
Structure and semantics:
- version: integer ≥ 1.
- project: string matching plan.meta.id.
- gantt_views: object of view_id → view; each view has title, excludes (list of calendar exclusions), and lanes.
- lanes: object of lane_id → lane; each lane has title and nodes (list of node_ids).

Multi-view support:
- Multiple named views can be defined (e.g., overview, backend-detail, frontend-detail, infrastructure-detail, critical-path).

Practical examples:
- hello.views.yaml shows a single overview view with lanes.
- program.views.yaml shows multiple views across tracks and a critical path view.

Validation rules:
- project must equal plan.meta.id.
- All node_ids in lanes must exist in the plan's nodes.
- **Updated** Enhanced validation includes date normalization for excludes arrays.

```mermaid
sequenceDiagram
participant Author as "Author"
participant Plan as "Plan (*.plan.yaml)"
participant Views as "Views (*.views.yaml)"
participant Validator as "Validator"
participant Normalizer as "Date Normalizer"
Author->>Plan : Write meta.id, statuses, nodes
Author->>Views : Set project = Plan.meta.id, define gantt_views and lanes
Validator->>Plan : Validate schema and semantic rules
Validator->>Views : Validate schema and cross-reference project
Views->>Normalizer : Normalize YAML dates in excludes[]
Normalizer-->>Views : Return normalized dates
Views-->>Author : Rendered views (e.g., Gantt)
```

**Diagram sources**
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L6-L24)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md#L11-L18)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L82-L100)
- [validate.py](file://specs/v1/tools/validate.py#L114-L133)

**Section sources**
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md#L5-L18)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L82-L100)
- [SPEC.md](file://specs/v1/SPEC.md#L98-L131)

### JSON Schema Definitions

#### Plan Schema
- Top-level required: version, meta, nodes.
- meta.required: id, title.
- nodes: additionalProperties allowed; each node requires title; supports kind, status, parent, after (array of strings), start (date), finish (date), duration (string or integer), issue, notes.
- Additional top-level properties allowed.

**Updated** Added finish field to the schema with the same format requirements as start (YYYY-MM-DD).

**Section sources**
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L95)

#### Views Schema
- Top-level required: version, project.
- gantt_views: object with additionalProperties allowed.
- Additional top-level properties allowed.

**Section sources**
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)

## Enhanced YAML Processing Guidelines

**Updated** Comprehensive YAML processing guidelines with date normalization requirements and improved encoding standards.

The opskarta format supports both YAML and JSON serialization. YAML is recommended for human readability, while JSON provides machine-friendly interchange. Proper YAML encoding is crucial for reliable parsing and validation, especially given YAML 1.1's auto-typification behavior.

### Date Normalization Requirements

YAML-1.1 parsers (particularly PyYAML) automatically convert strings resembling dates into special date/datetime objects. This can cause unexpected behavior in downstream processing. The opskarta specification mandates comprehensive date normalization to ensure consistent processing.

#### Canonical Date Format
All date fields must be normalized to the canonical string format `YYYY-MM-DD`:
- `start` field: `YYYY-MM-DD` string
- `finish` field: `YYYY-MM-DD` string  
- `excludes[]` elements: `YYYY-MM-DD` string for date entries
- `duration` field: `<digits>d` or `<digits>w` string format

#### Normalization Process
The normalization process converts YAML date objects to standardized string representations:

```python
def normalize_date_field(value):
    """Нормализует значение даты (start, finish) к строке YYYY-MM-DD."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value.strip()
    raise ValueError(f"Invalid date type: {type(value)}")

def normalize_start(value):
    """Нормализует значение start к строке YYYY-MM-DD."""
    return normalize_date_field(value)

def normalize_finish(value):
    """Нормализует значение finish к строке YYYY-MM-DD."""
    return normalize_date_field(value)

def normalize_excludes(excludes_list):
    """Нормализует список excludes, преобразуя YAML-даты в строки."""
    result = []
    for item in excludes_list:
        if isinstance(item, (date, datetime)):
            result.append(item.isoformat() if isinstance(item, date) else item.date().isoformat())
        else:
            result.append(str(item))
    return result
```

### Date Formatting Recommendations

#### Recommended Format
Always quote date values in YAML files to prevent auto-typification:

```yaml
nodes:
  task1:
    title: "Task"
    start: "2024-03-15"   # String in quotes (recommended)
    finish: "2024-03-20"  # String in quotes (recommended)
    duration: "5d"
```

#### Risky Format
Avoid unquoted dates that may be auto-converted:

```yaml
nodes:
  task1:
    title: "Task"
    start: 2024-03-15   # Without quotes - may be interpreted as date or number
    finish: 2024-03-20  # Without quotes - may cause parsing errors
    duration: 5d        # Without quotes - may cause parsing errors
```

### Duration Specifications
The `duration` value MUST be a string in `<number><unit>` format (e.g., `5d`, `2w`).

**Correct examples:**
```yaml
duration: "5d"   # 5 days
duration: "2w"   # 2 weeks (= 10 working days)
duration: "10d"  # 10 days
```

**Incorrect examples:**
```yaml
duration: 5d     # Without quotes - may cause YAML parsing errors
duration: 5      # Number without unit - does not match format
duration: "0d"   # Zero is invalid
duration: "-1d"  # Negative values are invalid
```

### Multi-line Strings (notes field)
For multi-line notes, use literal blocks (`|`) or folded blocks (`>`):

**Literal block (preserves line breaks):**
```yaml
nodes:
  task1:
    title: "Task with notes"
    notes: |
      First line of note.
      Second line of note.
      
      Paragraph after empty line.
```

**Folded block (combines lines):**
```yaml
nodes:
  task1:
    title: "Task with notes"
    notes: >
      This is a long note that
      will be combined into a single line
      with spaces between parts.
```

### Special Characters
When using special characters in strings, quote them appropriately:

```yaml
nodes:
  task1:
    title: "Task: important!"      # Colon requires quotes
    issue: "JIRA-123"             # No problems
    notes: "Note with # symbol"   # Hash requires quotes
```

### YAML vs JSON Equivalence
The formats are fully interchangeable. Below are equivalent examples:

**YAML:**
```yaml
version: 1
meta:
  id: "my-project"
  title: "My Project"
nodes:
  task1:
    title: "First Task"
    start: "2024-03-01"
    finish: "2024-03-05"
    duration: "5d"
  task2:
    title: "Second Task"
    after:
      - task1
    duration: "3d"
```

**JSON (equivalent):**
```json
{
  "version": 1,
  "meta": {
    "id": "my-project",
    "title": "My Project"
  },
  "nodes": {
    "task1": {
      "title": "First Task",
      "start": "2024-03-01",
      "finish": "2024-03-05",
      "duration": "5d"
    },
    "task2": {
      "title": "Second Task",
      "after": ["task1"],
      "duration": "3d"
    }
  }
}
```

**Section sources**
- [55-yaml-notes.md](file://specs/v1/spec/55-yaml-notes.md#L1-L137)
- [validate.py](file://specs/v1/tools/validate.py#L114-L133)

## Finish Field Specification

**New** The finish field provides target completion date or deadline functionality alongside the existing start and duration fields.

### Field Definition
- **Name**: finish
- **Type**: string
- **Format**: YYYY-MM-DD (ISO 8601 date)
- **Pattern**: `^\d{4}-\d{2}-\d{2}$`
- **Description**: Target completion date or deadline in YYYY-MM-DD format

### Behavior and Algorithms

#### Backward Scheduling (finish + duration → start)
When finish and duration are specified but start is omitted:
1. Calculate the number of working days from duration
2. Subtract working days from finish, moving backwards
3. Result is the calculated start date

**Algorithm**: `start = sub_workdays(finish, duration_days - 1)`

**Example**: `finish: "2024-03-15"`, `duration: "5d"` → `start: "2024-03-11"`

#### Forward Calculation (start + finish → duration)
When start and finish are specified but duration is omitted:
1. Calculate the number of working days between start and finish
2. Result is the calculated duration

**Algorithm**: `duration = working_days_between(start, finish)`

**Example**: `start: "2024-03-11"`, `finish: "2024-03-15"` → `duration: "5d"`

#### Consistency Validation (all three fields)
When start, finish, and duration are all specified:
- They must be mathematically consistent
- Calculated finish from start + duration must equal specified finish
- Inconsistency is considered an error

### Practical Examples

#### Backward Planning Scenario
```yaml
nodes:
  release_prep:
    title: "Release Preparation"
    finish: "2024-03-15"  # Deadline
    duration: "5d"
    # start calculated: 2024-03-11 (5 working days before finish)
```

#### Mixed Scheduling Scenario
```yaml
nodes:
  task_with_all_fields:
    title: "Task with All Fields"
    start: "2024-03-01"
    finish: "2024-03-05"
    duration: "5d"
    # All three fields consistent (5 working days)
```

#### Dependency with Finish Field
```yaml
nodes:
  dependent_task:
    title: "Dependent Task"
    after: [parent_task_with_finish]
    duration: "3d"
    # start = next working day after parent_task_with_finish.finish
```

**Section sources**
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L56-L83)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L198-L226)
- [finish_field.plan.yaml](file://specs/v1/tests/fixtures/finish_field.plan.yaml#L1-L30)

## Improved Validation System

**Updated** Enhanced validation system with comprehensive date normalization, finish field validation, and improved error messaging.

The validation system operates on multiple levels to ensure data integrity and consistency across opskarta files, with enhanced support for YAML date normalization.

### Validation Levels

1. **Syntax Level** - Validates correct YAML/JSON syntax
2. **Schema Level** - Ensures field types, required fields, and formats match JSON Schema
3. **Semantic Level** - Verifies referential integrity, business rules, and date correctness
4. **Normalization Level** - Converts YAML date objects to canonical string format

### Enhanced Error Message Standards

The validator must provide clear, actionable error messages containing:
- Path to the problematic field (e.g., `nodes.task2.parent`)
- Problem description
- Expected value or format

**Example error outputs:**
```
Error: Invalid reference in nodes.task2.parent
  Value: "nonexistent"
  Expected: existing node ID from nodes
  Available: root, task1
```

```
Error: Invalid duration format in nodes.task1.duration
  Value: "5"
  Expected: format <number><unit> where unit is 'd' or 'w'
  Pattern: ^[1-9][0-9]*[dw]$
```

### Schema Validation Details

Both plan and views files use comprehensive JSON Schema validation:

**Plan Schema Validation:**
- Required fields: version, nodes
- Meta validation: id and title must be non-empty strings
- Node validation: each node requires title; supports kind, status, parent, after, start (YYYY-MM-DD), finish (YYYY-MM-DD), duration (<digits>d or <digits>w), issue, notes
- Additional properties allowed throughout for extensibility

**Updated** Finish field validation now includes format checking and consistency validation with start/duration fields, plus comprehensive YAML date normalization.

**Views Schema Validation:**
- Required fields: version, project
- Project validation: must match plan.meta.id
- Gantt view validation: supports title, excludes, and lanes
- Lane validation: each lane requires title and nodes list

### Cross-File Validation

The system validates relationships between plan and views files:
- project field must equal plan.meta.id
- All node_ids in views must exist in plan.nodes
- Duration formats must follow `<number><unit>` pattern
- Start and finish dates must follow YYYY-MM-DD format
- **Updated** Finish field format validation and consistency checking with enhanced YAML processing

### Date Normalization Integration

The validation system includes comprehensive date normalization:

```python
def normalize_yaml_dates(data: Any) -> Any:
    """
    Рекурсивно нормализует YAML-даты к строкам формата YYYY-MM-DD.
    
    Args:
        data: Данные из YAML-парсера
        
    Returns:
        Нормализованные данные
    """
    if isinstance(data, datetime):
        return data.date().isoformat()
    elif isinstance(data, date):
        return data.isoformat()
    elif isinstance(data, dict):
        return {k: normalize_yaml_dates(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [normalize_yaml_dates(item) for item in data]
    else:
        return data
```

**Section sources**
- [60-validation.md](file://specs/v1/spec/60-validation.md#L1-L377)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L95)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)
- [validate.py](file://specs/v1/tools/validate.py#L114-L133)

## Dependency Analysis
- Referential integrity:
  - nodes.parent must reference an existing node_id.
  - nodes.after entries must reference existing node_ids.
  - nodes.status must reference a key in statuses.
  - views.project must equal plan.meta.id.
  - views.lanes[].nodes[] entries must reference existing node_ids.

**Updated** Added finish field validation to ensure proper date format and consistency, plus comprehensive YAML date normalization.

```mermaid
graph LR
N1["nodes.*.parent"] --> N2["nodes (existence)"]
N3["nodes.*.after[*]"] --> N2
N4["nodes.*.status"] --> S["statuses (keys)"]
V["views.project"] --> M["plan.meta.id"]
L["views.lanes[*].nodes[*]"] --> N2
F["nodes.*.finish"] --> D["YYYY-MM-DD format"]
S["nodes.*.start"] --> D
NORM["YAML Date Normalization"] --> F
NORM --> S
```

**Diagram sources**
- [60-validation.md](file://specs/v1/spec/60-validation.md#L13-L75)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L89-L100)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L102-L104)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L63-L72)
- [validate.py](file://specs/v1/tools/validate.py#L114-L133)

**Section sources**
- [60-validation.md](file://specs/v1/spec/60-validation.md#L13-L75)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L89-L104)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L63-L72)
- [validate.py](file://specs/v1/tools/validate.py#L114-L133)

## Performance Considerations
- Keep nodes flat or reasonably deep to simplify rendering and dependency resolution.
- Prefer explicit after dependencies for complex schedules to avoid ambiguous start calculations.
- Limit excessive custom extensions to reduce parsing overhead in downstream tools.
- Use quoted strings for dates and durations to prevent YAML parsing overhead.
- **Updated** Finish field processing adds minimal computational overhead compared to start/duration calculations.
- **Updated** Date normalization occurs once during YAML loading and is cached for subsequent validations.

## Troubleshooting Guide

**Updated** Enhanced troubleshooting guide with finish field validation, backward planning considerations, and comprehensive YAML date normalization.

### Common YAML Formatting Errors and Resolutions

**Missing Required Fields:**
- Ensure plan.version, plan.meta.id/title, plan.nodes, and plan.nodes.*.title are present.
- Ensure views.version, views.project, and views.gantt_views are present.

**Reference Errors:**
- parent must exist in nodes.
- after entries must exist in nodes.
- status must be a key in statuses.
- project must equal plan.meta.id.
- lanes nodes must exist in nodes.

**Format Errors:**
- start must be YYYY-MM-DD (quoted).
- finish must be YYYY-MM-DD (quoted).
- duration must be <digits>d or <digits>w (quoted).
- Use proper YAML quoting for strings containing special characters.

**Finish Field Specific Issues:**
- **Format validation**: Both start and finish must follow YYYY-MM-DD pattern
- **Consistency validation**: When all three fields are present, they must be mathematically consistent
- **Backward planning**: finish + duration combinations trigger automatic start calculation
- **Forward calculation**: start + finish combinations trigger automatic duration calculation

**YAML-Specific Issues:**
- Date parsing: Always quote dates in start and finish fields to prevent automatic conversion to date types.
- Duration parsing: Always quote duration values to prevent YAML parser confusion.
- Multi-line strings: Use literal blocks (|) for preserved line breaks, folded blocks (>) for combined lines.
- Special characters: Quote strings containing colons, hash symbols, or other special characters.

**Enhanced Validation Messages:**
- Use clear error paths (e.g., nodes.task2.parent) and expected values.
- Pay attention to validation level indicators (syntax, schema, semantic, normalization).
- Check both plan and views file validation results.
- **Updated** Finish field validation provides specific error messages for format and consistency issues.
- **Updated** Date normalization errors clearly indicate which fields failed conversion.

**Date Normalization Issues:**
- **YAML date objects**: Ensure all date fields are properly normalized to strings
- **Excludes normalization**: Calendar exclusion dates must be normalized consistently
- **Type conversion errors**: Handle cases where YAML parser returns unexpected types

**Section sources**
- [60-validation.md](file://specs/v1/spec/60-validation.md#L7-L11)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L13-L75)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L77-L81)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L82-L100)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L124-L139)
- [55-yaml-notes.md](file://specs/v1/spec/55-yaml-notes.md#L5-L137)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L56-L83)
- [validate.py](file://specs/v1/tools/validate.py#L114-L133)

## Conclusion
The opskarta v1 file formats provide a compact, extensible foundation for operational maps:
- Plan files capture metadata, statuses, hierarchical nodes, and scheduling.
- Views files enable multiple presentations (e.g., Gantt) over the same plan.
- Enhanced validation rules ensure consistency across files and within each file.
- Comprehensive YAML encoding guidelines prevent parsing issues and ensure reliable data interchange.
- **Updated** The new finish field specification enables flexible scheduling approaches including backward planning and deadline-driven project management.
- **Updated** Enhanced YAML processing guarantees consistent date handling across different YAML parsers.
- Extensibility allows teams to tailor the format to their needs while preserving compatibility.

## Appendices

### Best Practices

**YAML Encoding Best Practices:**
- Always quote date values (YYYY-MM-DD) in start and finish fields.
- Always quote duration values (<digits>d or <digits>w).
- Use literal blocks (|) for multi-line notes that preserve formatting.
- Use folded blocks (>) for multi-line notes that combine into single lines.
- Quote strings containing special characters (colons, hash symbols, etc.).

**Finish Field Best Practices:**
- Use finish field for deadline-driven scheduling when you know the target completion date.
- Combine finish + duration for backward planning scenarios.
- Use start + finish for milestone tracking and progress monitoring.
- Maintain consistency between all three scheduling fields when specifying all three.

**Date Normalization Best Practices:**
- **Updated** Always quote date values in YAML to prevent auto-typification.
- **Updated** Ensure all date fields (start, finish, excludes[]) are normalized to YYYY-MM-DD strings.
- **Updated** Test YAML files with different parsers to ensure consistent behavior.
- **Updated** Use validation tools to verify proper date normalization.

**File Organization and Naming Conventions:**
- Plan files: *.plan.yaml
- Views files: *.views.yaml
- Place both files alongside the work items they describe; group by project or program.

**Version Control Integration:**
- Treat plan and views files as configuration; commit alongside source and documentation.
- Use pull requests to review changes to scheduling, dependencies, and statuses.
- Consider separate branches for major re-baselines or multi-program plans.

**Enhanced Validation Workflow:**
- Run syntax validation first to catch YAML/JSON parsing errors.
- Execute schema validation to ensure field types and formats are correct.
- Perform semantic validation to verify referential integrity and business rules.
- **Updated** Include date normalization validation to ensure consistent date handling.
- Review validation messages carefully, focusing on error paths and expected formats.
- **Updated** Include finish field validation in the comprehensive validation process.

**Section sources**
- [90-extensibility.md](file://specs/v1/spec/90-extensibility.md#L12-L26)
- [SPEC.md](file://specs/v1/SPEC.md#L17-L23)
- [55-yaml-notes.md](file://specs/v1/spec/55-yaml-notes.md#L1-L137)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L197-L220)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md#L56-L83)
- [validate.py](file://specs/v1/tools/validate.py#L114-L133)