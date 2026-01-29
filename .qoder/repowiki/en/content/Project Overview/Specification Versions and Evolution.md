# Specification Versions and Evolution

<cite>
**Referenced Files in This Document**
- [SPEC.md](file://specs/v1/SPEC.md)
- [README.md](file://specs/v1/README.md)
- [00-introduction.md](file://specs/v1/spec/00-introduction.md)
- [10-plan-file.md](file://specs/v1/spec/10-plan-file.md)
- [20-nodes.md](file://specs/v1/spec/20-nodes.md)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md)
- [50-scheduling.md](file://specs/v1/spec/50-scheduling.md)
- [60-validation.md](file://specs/v1/spec/60-validation.md)
- [90-extensibility.md](file://specs/v1/spec/90-extensibility.md)
- [build_spec.py](file://specs/v1/tools/build_spec.py)
- [validate.py](file://specs/v1/tools/validate.py)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json)
- [views.schema.json](file://specs/v1/schemas/views.schema.json)
- [minimal.project.plan.yaml](file://specs/v1/examples/minimal/project.plan.yaml)
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml)
</cite>

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

## Introduction
This document explains the evolution and current state of the Opskarta specification, focusing on the v1 specification. It covers the versioning strategy, current alpha status, roadmap considerations, backward compatibility, building process, feature introduction, migration guidance, and practical advice for selecting the right version for different use cases.

## Project Structure
The Opskarta specification v1 is organized as a modular, documentation-driven specification with supporting tools and schemas:
- Specification chapters are authored in separate Markdown files under specs/v1/spec/.
- A build script aggregates these chapters into a single specification document.
- JSON Schemas define formal validation rules for plan and views files.
- A validator enforces both schema-level and semantic rules.
- Examples demonstrate minimal and advanced usage patterns.

```mermaid
graph TB
subgraph "Specification v1"
A["specs/v1/spec/*.md<br/>Chapters"]
B["specs/v1/SPEC.md<br/>Aggregated Spec"]
C["specs/v1/tools/build_spec.py<br/>Build Script"]
D["specs/v1/tools/validate.py<br/>Validator"]
E["specs/v1/schemas/*.json<br/>JSON Schemas"]
F["specs/v1/examples/*/*.yaml<br/>Usage Examples"]
end
A --> C --> B
B -. references .-> E
D -. validates .-> E
D -. reads .-> F
```

**Diagram sources**
- [build_spec.py](file://specs/v1/tools/build_spec.py#L1-L240)
- [SPEC.md](file://specs/v1/SPEC.md#L1-L407)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L26)
- [validate.py](file://specs/v1/tools/validate.py#L1-L752)

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L1-L407)
- [README.md](file://specs/v1/README.md#L1-L27)
- [build_spec.py](file://specs/v1/tools/build_spec.py#L1-L240)
- [validate.py](file://specs/v1/tools/validate.py#L1-L752)

## Core Components
- Versioning strategy: Both plan and views files include a version integer at the root. The validator currently supports version 1 and will warn for other values.
- Current status: The v1 specification is marked as Alpha and Draft, indicating early adoption and potential changes.
- Building process: The build_spec.py script compiles chapter files into a unified specification document and can check whether the generated SPEC.md matches the latest chapter content.
- Validation pipeline: The validate.py script performs YAML parsing, optional JSON Schema validation, and semantic checks (referential integrity, business rules).
- Schemas: JSON Schemas define required fields and types for plan and views files, enabling automated validation.

Key artifacts:
- Aggregated specification: [SPEC.md](file://specs/v1/SPEC.md#L1-L407)
- Build tool: [build_spec.py](file://specs/v1/tools/build_spec.py#L1-L240)
- Validator: [validate.py](file://specs/v1/tools/validate.py#L1-L752)
- Plan schema: [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- Views schema: [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L26)
- Examples: [minimal.project.plan.yaml](file://specs/v1/examples/minimal/project.plan.yaml#L1-L6), [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44), [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L15-L25)
- [README.md](file://specs/v1/README.md#L3-L4)
- [build_spec.py](file://specs/v1/tools/build_spec.py#L1-L240)
- [validate.py](file://specs/v1/tools/validate.py#L1-L752)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L26)

## Architecture Overview
The specification lifecycle integrates authoring, assembly, validation, and usage:
- Authoring: Chapters in specs/v1/spec/ describe plan, nodes, views, statuses, scheduling, validation rules, and extensibility.
- Assembly: build_spec.py scans chapter files, extracts headings, generates a table of contents, and produces SPEC.md.
- Validation: validate.py loads YAML, optionally validates via JSON Schema, and enforces semantic rules (referential integrity, date/time formats).
- Usage: Examples show minimal and advanced configurations for plans and views.

```mermaid
sequenceDiagram
participant Author as "Author"
participant Builder as "build_spec.py"
participant Spec as "SPEC.md"
participant Validator as "validate.py"
participant Schema as "JSON Schemas"
Author->>Builder : Edit spec/*.md
Builder->>Spec : Generate/Update SPEC.md
Author->>Validator : Run validate.py plan.yaml [views.yaml]
Validator->>Schema : Optional JSON Schema validation
Validator-->>Author : Validation report (syntax, schema, semantics)
```

**Diagram sources**
- [build_spec.py](file://specs/v1/tools/build_spec.py#L1-L240)
- [SPEC.md](file://specs/v1/SPEC.md#L1-L407)
- [validate.py](file://specs/v1/tools/validate.py#L1-L752)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L26)

## Detailed Component Analysis

### Versioning Strategy
- Root version field: Both plan and views files include a version integer at the root.
- Validator behavior: The validator checks the version field and warns if it differs from the supported version (v1).
- Backward compatibility: The specification emphasizes extensibility and ignores unknown fields during basic processing, facilitating forward-compatible evolution.

```mermaid
flowchart TD
Start(["Load YAML"]) --> CheckVersion["Check 'version' field"]
CheckVersion --> IsV1{"Is version == 1?"}
IsV1 --> |Yes| Proceed["Proceed with validation"]
IsV1 --> |No| Warn["Emit warning about unsupported version"]
Proceed --> End(["Validation Complete"])
Warn --> End
```

**Diagram sources**
- [validate.py](file://specs/v1/tools/validate.py#L153-L172)
- [SPEC.md](file://specs/v1/SPEC.md#L31-L32)

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L19-L21)
- [SPEC.md](file://specs/v1/SPEC.md#L245-L251)
- [SPEC.md](file://specs/v1/SPEC.md#L322-L328)
- [validate.py](file://specs/v1/tools/validate.py#L153-L172)

### Current Alpha Status of v1
- Status indicators: The v1 README marks the release as Alpha and Draft.
- Scope: v1 defines the minimal compatible set of fields and core capabilities (hierarchical nodes, statuses, scheduling, multiple views, and extensibility).

**Section sources**
- [README.md](file://specs/v1/README.md#L3-L4)
- [SPEC.md](file://specs/v1/SPEC.md#L17-L23)

### Roadmap Considerations
- Extensibility-first design: The specification encourages adding custom fields and namespaces, enabling incremental feature additions without breaking base compatibility.
- Version field presence: The version field allows future major versions to introduce breaking changes while maintaining a clear upgrade path.

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L385-L407)
- [SPEC.md](file://specs/v1/SPEC.md#L19-L21)

### Relationship Between Versions and Backward Compatibility
- Unknown fields: Base tools must ignore unknown fields and preserve them through parse-emit cycles when formatting requires it.
- Recommended namespace grouping: Users can group custom fields under a dedicated namespace to avoid conflicts when multiple parties extend the format.

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L389-L393)
- [SPEC.md](file://specs/v1/SPEC.md#L396-L405)

### Specification Building Process
- Chapter organization: Each chapter file starts with a numeric prefix and a descriptive name; build_spec.py sorts them numerically and extracts first-level headings for the table of contents.
- Output generation: The script writes a unified SPEC.md with automatic header comments and a generated table of contents.
- Integrity checks: The script detects duplicate prefixes and missing spec directories, and can check whether SPEC.md is up-to-date without rewriting.

```mermaid
flowchart TD
A["Find spec/*.md files"] --> B["Sort by numeric prefix"]
B --> C["Extract first-level headings"]
C --> D["Generate TOC anchors"]
D --> E["Concatenate sections"]
E --> F["Write SPEC.md"]
```

**Diagram sources**
- [build_spec.py](file://specs/v1/tools/build_spec.py#L46-L86)
- [build_spec.py](file://specs/v1/tools/build_spec.py#L123-L144)
- [build_spec.py](file://specs/v1/tools/build_spec.py#L147-L171)

**Section sources**
- [build_spec.py](file://specs/v1/tools/build_spec.py#L1-L240)

### How New Features Are Introduced
- Extensibility rule: Nodes may include additional fields; base tools must ignore unknown fields and preserve them when formatting.
- Namespace recommendation: Grouping custom fields under a dedicated namespace reduces collision risks.

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L389-L393)
- [SPEC.md](file://specs/v1/SPEC.md#L396-L405)

### Migration Guidance
- From v1 to future versions: Since v1 is the first version, there is no prior version to migrate from. Future major versions may introduce breaking changes signaled by a higher version number.
- Version alignment: Ensure both plan and views files declare version 1; mismatches will trigger validation errors.
- Semantic integrity: Fix referential errors (parent, after, status) and format violations (date, duration) before upgrading expectations.

**Section sources**
- [README.md](file://specs/v1/README.md#L17-L19)
- [SPEC.md](file://specs/v1/SPEC.md#L245-L251)
- [SPEC.md](file://specs/v1/SPEC.md#L322-L328)
- [validate.py](file://specs/v1/tools/validate.py#L153-L172)

### Choosing the Right Specification Version
- Use v1 for:
  - Early experimentation and prototyping.
  - Environments requiring a small, stable baseline with clear extensibility.
  - Projects needing hierarchical work breakdown, scheduling, and multiple views.
- Considerations:
  - v1 is Alpha/Draft; expect changes as the ecosystem evolves.
  - Adopt custom fields cautiously and consider namespace grouping to ease future updates.

**Section sources**
- [README.md](file://specs/v1/README.md#L6-L16)
- [SPEC.md](file://specs/v1/SPEC.md#L17-L23)

## Dependency Analysis
The validator depends on JSON Schemas for structural validation and on the plan/views content for semantic checks. The build tool depends on chapter files and generates the aggregated specification.

```mermaid
graph TB
V["validate.py"]
P["plan.schema.json"]
VY["views.schema.json"]
PL["Plan YAML"]
VS["Views YAML"]
V --> P
V --> VY
V --> PL
V --> VS
```

**Diagram sources**
- [validate.py](file://specs/v1/tools/validate.py#L586-L618)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L26)

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L1-L752)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L26)

## Performance Considerations
- Validation levels: The validator runs multiple passes (syntax, schema, semantics). For large documents, prefer schema validation only when necessary, and rely on semantic checks for critical integrity.
- Cyclic dependency detection: The validator performs depth-first searches for parent and after relationships; keep node graphs acyclic to avoid expensive cycles.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common validation issues and remedies:
- Missing version field: Add version: 1 to plan and views files.
- Incorrect types: Ensure version is an integer and required fields are present.
- Referential errors:
  - parent must reference an existing node ID.
  - after must reference existing node IDs.
  - status must reference an existing status key.
- Date and duration formats:
  - start must follow YYYY-MM-DD.
  - duration must follow <number>d or <number>w.
- Project mismatch: project in views must equal meta.id in plan.
- Cyclic dependencies: Remove cycles in parent or after relationships.

Diagnostic output includes:
- Field path, value, expected format, and available alternatives for quick fixes.

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L245-L251)
- [SPEC.md](file://specs/v1/SPEC.md#L276-L295)
- [SPEC.md](file://specs/v1/SPEC.md#L317-L321)
- [SPEC.md](file://specs/v1/SPEC.md#L329-L340)
- [SPEC.md](file://specs/v1/SPEC.md#L342-L354)
- [SPEC.md](file://specs/v1/SPEC.md#L356-L380)
- [validate.py](file://specs/v1/tools/validate.py#L153-L172)
- [validate.py](file://specs/v1/tools/validate.py#L230-L324)
- [validate.py](file://specs/v1/tools/validate.py#L448-L492)
- [validate.py](file://specs/v1/tools/validate.py#L561-L577)

## Conclusion
Opskarta v1 establishes a compact, extensible foundation for work planning and visualization. Its Alpha/Draft status signals readiness for early adopters while preserving flexibility for future evolution. The version field, JSON Schemas, and robust validator support reliable authoring and validation. For most current use cases, v1 provides sufficient capability with clear pathways for extension and eventual upgrades.