# Development and Contributing

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [CONTRIBUTING.md](file://CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](file://CODE_OF_CONDUCT.md)
- [SECURITY.md](file://SECURITY.md)
- [specs/v1/README.md](file://specs/v1/README.md)
- [specs/v1/SPEC.md](file://specs/v1/SPEC.md)
- [specs/v1/examples/README.md](file://specs/v1/examples/README.md)
- [specs/v1/tools/README.md](file://specs/v1/tools/README.md)
- [specs/v1/tools/requirements.txt](file://specs/v1/tools/requirements.txt)
- [specs/v1/tools/build_spec.py](file://specs/v1/tools/build_spec.py)
- [specs/v1/tools/validate.py](file://specs/v1/tools/validate.py)
- [specs/v1/schemas/plan.schema.json](file://specs/v1/schemas/plan.schema.json)
- [specs/v1/schemas/views.schema.json](file://specs/v1/schemas/views.schema.json)
- [specs/v1/spec/00-introduction.md](file://specs/v1/spec/00-introduction.md)
- [specs/v1/spec/90-extensibility.md](file://specs/v1/spec/90-extensibility.md)
- [specs/v1/tests/test_scheduling.py](file://specs/v1/tests/test_scheduling.py)
- [specs/v1/tests/fixtures/extensions.plan.yaml](file://specs/v1/tests/fixtures/extensions.plan.yaml)
- [specs/v1/tests/fixtures/parent_inheritance.plan.yaml](file://specs/v1/tests/fixtures/parent_inheritance.plan.yaml)
- [specs/v1/tests/fixtures/start_after_conflict.plan.yaml](file://specs/v1/tests/fixtures/start_after_conflict.plan.yaml)
- [specs/v1/tests/fixtures/weekends_exclusion.plan.yaml](file://specs/v1/tests/fixtures/weekends_exclusion.plan.yaml)
- [specs/v1/tests/fixtures/weeks_duration.plan.yaml](file://specs/v1/tests/fixtures/weeks_duration.plan.yaml)
- [Makefile](file://Makefile)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive testing infrastructure documentation with pytest integration
- Documented new test suite covering scheduling functionality with 304 lines of tests
- Added fixture-based testing documentation for various scheduling scenarios
- Enhanced development workflow with automated testing, coverage reporting, and CI/CD integration
- Updated Makefile targets for testing and coverage reporting

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Contribution Workflow](#contribution-workflow)
10. [Specification Evolution and Versioning](#specification-evolution-and-versioning)
11. [Testing and Quality Assurance](#testing-and-quality-assurance)
12. [Extending the Specification](#extending-the-specification)
13. [Continuous Integration Guidance](#continuous-integration-guidance)
14. [Conclusion](#conclusion)

## Introduction
This document provides a complete guide for developers and contributors working on Opskarta. It covers development environment setup, testing frameworks, code standards, specification evolution, versioning, contribution workflow, and quality assurance processes. The goal is to enable both bug fixes and feature contributions with clear expectations around documentation, examples, and ecosystem compatibility.

**Updated** Added comprehensive testing infrastructure documentation covering pytest integration, fixture-based testing, and automated quality assurance processes.

## Project Structure
Opskarta is organized around a single specification version (v1) with supporting tools, examples, schemas, and a comprehensive test suite. The repository is designed so that the specification is the core, and tools are reference implementations that remain lightweight and optional.

```mermaid
graph TB
root["Repository Root"]
docs["docs/"]
specs["specs/v1/"]
readme_root["README.md"]
contributing["CONTRIBUTING.md"]
coc["CODE_OF_CONDUCT.md"]
security["SECURITY.md"]
subgraph "specs/v1/"
v1_readme["specs/v1/README.md"]
v1_spec["specs/v1/SPEC.md"]
v1_examples["specs/v1/examples/"]
v1_tools["specs/v1/tools/"]
v1_schemas["specs/v1/schemas/"]
v1_tests["specs/v1/tests/"]
v1_spec_parts["specs/v1/spec/*.md"]
end
root --> docs
root --> specs
root --> readme_root
root --> contributing
root --> coc
root --> security
specs --> v1_readme
specs --> v1_spec
specs --> v1_examples
specs --> v1_tools
specs --> v1_schemas
specs --> v1_tests
specs --> v1_spec_parts
```

**Diagram sources**
- [README.md](file://README.md#L1-L96)
- [specs/v1/README.md](file://specs/v1/README.md#L1-L27)
- [specs/v1/SPEC.md](file://specs/v1/SPEC.md#L1-L407)

**Section sources**
- [README.md](file://README.md#L1-L96)
- [specs/v1/README.md](file://specs/v1/README.md#L1-L27)

## Core Components
- Specification v1: Defines the YAML/JSON format for plans and views, validation rules, scheduling semantics, statuses, and extensibility.
- Tools: Reference implementations for validating files, building the specification, and rendering Mermaid Gantt charts.
- Examples: Minimal, hello, and advanced example sets demonstrating plan and view usage.
- Schemas: JSON Schema definitions for machine-readable validation.
- **Tests**: Comprehensive test suite with 304 lines of scheduling tests and fixture-based scenarios covering various scheduling edge cases.

Key responsibilities:
- Maintain the specification as the single source of truth.
- Keep tools small, deterministic, and compatible with the spec.
- Provide clear examples and validation to ensure interoperability.
- **Ensure comprehensive test coverage for all scheduling functionality and edge cases.**

**Section sources**
- [specs/v1/SPEC.md](file://specs/v1/SPEC.md#L1-L407)
- [specs/v1/tools/README.md](file://specs/v1/tools/README.md#L1-L126)
- [specs/v1/examples/README.md](file://specs/v1/examples/README.md#L1-L34)
- [specs/v1/schemas/plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- [specs/v1/schemas/views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L26)
- [specs/v1/tests/test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L1-L305)

## Architecture Overview
The development architecture centers on the specification and reference tools with integrated testing infrastructure:

```mermaid
graph TB
user["Developer / Contributor"]
cli["CLI Tools<br/>validate.py, build_spec.py"]
renderer["Renderer<br/>render.mermaid_gantt"]
spec["SPEC.md<br/>and spec/*.md"]
schemas["JSON Schemas<br/>plan.schema.json, views.schema.json"]
examples["Examples<br/>minimal/, hello/, advanced/"]
tests["Test Suite<br/>test_scheduling.py<br/>304 lines of tests"]
fixtures["Test Fixtures<br/>5 scenario files"]
coverage["Coverage Reporting<br/>pytest-cov"]
user --> cli
user --> renderer
user --> tests
cli --> schemas
cli --> spec
cli --> tests
renderer --> spec
renderer --> examples
renderer --> tests
tests --> fixtures
tests --> coverage
spec --> schemas
```

**Diagram sources**
- [specs/v1/tools/validate.py](file://specs/v1/tools/validate.py#L1-L752)
- [specs/v1/tools/build_spec.py](file://specs/v1/tools/build_spec.py#L1-L240)
- [specs/v1/tools/README.md](file://specs/v1/tools/README.md#L1-L126)
- [specs/v1/SPEC.md](file://specs/v1/SPEC.md#L1-L407)
- [specs/v1/schemas/plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L86)
- [specs/v1/schemas/views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L26)
- [specs/v1/examples/README.md](file://specs/v1/examples/README.md#L1-L34)
- [specs/v1/tests/test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L1-L305)

## Detailed Component Analysis

### Validation Tool (validate.py)
Responsibilities:
- Parse YAML safely.
- Validate semantic correctness against the specification (required fields, referential integrity, cycles, formats).
- Optional JSON Schema validation for stricter machine-checking.
- Provide actionable error messages with paths, values, and expected formats.

```mermaid
flowchart TD
Start(["Start"]) --> LoadPlan["Load Plan YAML"]
LoadPlan --> SchemaFlag{"--schema flag?"}
SchemaFlag --> |Yes| LoadSchemaPlan["Load JSON Schema for Plan"]
SchemaFlag --> |No| SemanticsPlan["Run Semantic Validation (Plan)"]
LoadSchemaPlan --> ValidateSchemaPlan["Validate via JSON Schema"]
ValidateSchemaPlan --> SemanticsPlan
SemanticsPlan --> ViewsProvided{"Views provided?"}
ViewsProvided --> |Yes| LoadViews["Load Views YAML"]
LoadViews --> LoadSchemaViews["Optional: Load JSON Schema for Views"]
LoadSchemaViews --> ValidateSchemaViews["Optional: Validate via JSON Schema"]
ValidateSchemaViews --> SemanticsViews["Run Semantic Validation (Views)"]
ViewsProvided --> |No| ReportOK["Report Success"]
SemanticsViews --> ReportOK
ReportOK --> End(["End"])
```

**Diagram sources**
- [specs/v1/tools/validate.py](file://specs/v1/tools/validate.py#L634-L751)

**Section sources**
- [specs/v1/tools/validate.py](file://specs/v1/tools/validate.py#L1-L752)

### Spec Builder (build_spec.py)
Responsibilities:
- Assemble spec/*.md files into a single SPEC.md with a generated table of contents.
- Enforce numeric prefix ordering and detect duplicate prefixes.
- Provide a check mode to ensure SPEC.md stays in sync with spec/*.md.

```mermaid
flowchart TD
BS_Start(["Start"]) --> FindFiles["Find spec/*.md with NN-*.md pattern"]
FindFiles --> SortPrefix["Sort by numeric prefix"]
SortPrefix --> ExtractHeadings["Extract first-level headings"]
ExtractHeadings --> BuildTOC["Generate Table of Contents"]
BuildTOC --> MergeSections["Merge all sections"]
MergeSections --> OutputMode{"--check mode?"}
OutputMode --> |Yes| Compare["Compare with existing SPEC.md"]
OutputMode --> |No| WriteFile["Write SPEC.md"]
Compare --> BS_End(["End"])
WriteFile --> BS_End
```

**Diagram sources**
- [specs/v1/tools/build_spec.py](file://specs/v1/tools/build_spec.py#L174-L239)

**Section sources**
- [specs/v1/tools/build_spec.py](file://specs/v1/tools/build_spec.py#L1-L240)

### Renderer (Mermaid Gantt)
Responsibilities:
- Render Gantt diagrams from plan and views.
- Compute dates from dependencies and durations.
- Support calendar exclusions and status-based coloring.

Usage highlights:
- Accepts plan and views files, a target view, and optional output file.
- Lists available views when requested.

**Section sources**
- [specs/v1/tools/README.md](file://specs/v1/tools/README.md#L69-L92)

### Test Infrastructure (test_scheduling.py)
**New** Comprehensive test suite covering scheduling functionality with 304 lines of tests:

Responsibilities:
- **Duration parsing tests**: Validate day and week duration formats ("5d", "1w" = 5 workdays).
- **Date calculation tests**: Verify workday vs calendar day calculations with weekend exclusions.
- **Schedule computation tests**: Test explicit start dates, after dependencies, and precedence rules.
- **Validation tests**: Ensure proper error handling for invalid formats and missing required fields.
- **Fixture-based tests**: Validate real-world scenarios using YAML fixture files.

Test categories:
- **TestDuration**: Duration parsing edge cases and format validation.
- **TestDateCalculation**: Workday arithmetic with weekend exclusions.
- **TestScheduleComputation**: Complex scheduling scenarios and dependency resolution.
- **TestValidation**: Semantic validation of plan and views files.
- **TestFixtures**: Real-world scenario validation using fixture files.

```mermaid
flowchart TD
TestSuite["Test Suite<br/>test_scheduling.py<br/>304 lines"]
Duration["Duration Tests<br/>parse_duration()"]
Dates["Date Tests<br/>finish_date()"]
Schedule["Schedule Tests<br/>compute_schedule()"]
Validation["Validation Tests<br/>validate_plan()"]
Fixtures["Fixture Tests<br/>5 scenario files"]
Coverage["Coverage Reports<br/>pytest-cov"]
TestSuite --> Duration
TestSuite --> Dates
TestSuite --> Schedule
TestSuite --> Validation
TestSuite --> Fixtures
TestSuite --> Coverage
```

**Diagram sources**
- [specs/v1/tests/test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L33-L305)

**Section sources**
- [specs/v1/tests/test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L1-L305)

### Test Fixtures
**New** Five comprehensive fixture files covering different scheduling scenarios:

- **extensions.plan.yaml**: Custom extension fields using x: namespace for team assignments and risk assessment.
- **parent_inheritance.plan.yaml**: Opt-in parent inheritance via x.scheduling.anchor_to_parent_start configuration.
- **start_after_conflict.plan.yaml**: Conflict resolution where explicit start takes precedence over after dependencies.
- **weekends_exclusion.plan.yaml**: Weekend exclusion scenarios with proper workday calculations.
- **weeks_duration.plan.yaml**: Week-based duration calculations (1w = 5 workdays) with chaining dependencies.

**Section sources**
- [specs/v1/tests/fixtures/extensions.plan.yaml](file://specs/v1/tests/fixtures/extensions.plan.yaml#L1-L22)
- [specs/v1/tests/fixtures/parent_inheritance.plan.yaml](file://specs/v1/tests/fixtures/parent_inheritance.plan.yaml#L1-L29)
- [specs/v1/tests/fixtures/start_after_conflict.plan.yaml](file://specs/v1/tests/fixtures/start_after_conflict.plan.yaml#L1-L20)
- [specs/v1/tests/fixtures/weekends_exclusion.plan.yaml](file://specs/v1/tests/fixtures/weekends_exclusion.plan.yaml#L1-L21)
- [specs/v1/tests/fixtures/weeks_duration.plan.yaml](file://specs/v1/tests/fixtures/weeks_duration.plan.yaml#L1-L24)

## Dependency Analysis
- Python runtime: The tools require Python 3.11+.
- Dependencies:
  - PyYAML for parsing YAML.
  - Optional: jsonschema for JSON Schema validation.
  - **pytest and pytest-cov for comprehensive testing and coverage reporting.**
- Internal dependencies:
  - validate.py depends on JSON Schemas for optional strict validation.
  - build_spec.py depends on spec/*.md files to generate SPEC.md.
  - **test_scheduling.py imports validation and rendering functions for comprehensive testing.**

```mermaid
graph LR
py["Python >= 3.11"]
yaml["PyYAML >= 6.0"]
js["jsonschema (optional)"]
pytest["pytest & pytest-cov"]
tools["Reference Tools"]
schemas["JSON Schemas"]
spec_src["spec/*.md"]
fixtures["Test Fixtures"]
test_suite["Test Suite<br/>304 lines"]
py --> tools
py --> test_suite
yaml --> tools
js --> tools
pytest --> test_suite
schemas --> tools
spec_src --> tools
fixtures --> test_suite
```

**Diagram sources**
- [specs/v1/tools/requirements.txt](file://specs/v1/tools/requirements.txt#L1-L10)
- [specs/v1/tools/validate.py](file://specs/v1/tools/validate.py#L1-L16)
- [specs/v1/tools/build_spec.py](file://specs/v1/tools/build_spec.py#L1-L24)
- [Makefile](file://Makefile#L158-L161)

**Section sources**
- [specs/v1/tools/requirements.txt](file://specs/v1/tools/requirements.txt#L1-L10)
- [Makefile](file://Makefile#L158-L161)

## Performance Considerations
- Validation complexity:
  - Semantic checks are linear in the number of nodes and edges.
  - Cycle detection uses DFS and is O(V + E) for parent and after relations.
- Rendering:
  - Date computation and Gantt generation are linear in the number of nodes and lanes.
- **Testing performance**:
  - Test suite runs efficiently with pytest parallelization support.
  - Fixture-based tests reduce code duplication and improve maintainability.
  - Coverage reporting helps identify untested code paths.
- Recommendations:
  - Keep PRs small to minimize validation overhead.
  - Prefer incremental spec updates and targeted examples.
  - **Use pytest markers and selective test execution for faster development cycles.**

## Troubleshooting Guide
Common issues and resolutions:
- YAML parse errors: Ensure files are valid YAML and use UTF-8 encoding.
- Missing required fields: Add version, nodes, and title per specification.
- Referential integrity errors: Fix parent, after, and status references to existing node IDs.
- Cyclic dependencies: Remove cycles in parent and after chains.
- JSON Schema validation failures: Align data types and formats with schemas.
- Tool installation: Install dependencies from requirements.txt.
- **Test failures**: Use pytest verbose mode (-v) and coverage reports (--cov) to identify failing test cases.
- **Coverage gaps**: Analyze missing branch coverage and add targeted test cases.

**Section sources**
- [specs/v1/tools/validate.py](file://specs/v1/tools/validate.py#L135-L329)
- [specs/v1/tools/validate.py](file://specs/v1/tools/validate.py#L431-L579)
- [specs/v1/tools/README.md](file://specs/v1/tools/README.md#L6-L11)
- [specs/v1/tests/test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L10-L12)

## Contribution Workflow
- Issue-first collaboration: Open an issue describing the problem, proposal, or question.
- Provide examples: Include before/after YAML samples for format changes; show input and expected output for tools.
- Keep PRs small and focused.
- New fields must be optional (unless introducing a new major version), semantically clear, and documented in the specification.
- **Code standards**:
  - Python >= 3.11.
  - Formatting/linting with ruff (where applicable).
  - **Add comprehensive tests with pytest for all new functionality.**
  - **Maintain or improve test coverage for existing functionality.**
  - **Use fixture files for complex test scenarios.**

**Section sources**
- [CONTRIBUTING.md](file://CONTRIBUTING.md#L14-L31)

## Specification Evolution and Versioning
- Current state: v1 is Alpha and Draft.
- Versioning strategy:
  - The version field in the root documents identifies the schema version.
  - Extensibility is encouraged; unknown fields should be preserved and ignored by base tools.
- Backward compatibility:
  - New fields should be optional until a new major version.
  - Base tools must ignore unknown fields and preserve formatting when applicable.
- Change management:
  - Update spec/*.md files in order (numeric prefix).
  - Regenerate SPEC.md using the spec builder.
  - Run the spec builder in check mode to prevent drift.
  - **Update test fixtures to reflect new specification changes.**

**Section sources**
- [README.md](file://README.md#L10-L15)
- [specs/v1/README.md](file://specs/v1/README.md#L3-L4)
- [specs/v1/spec/00-introduction.md](file://specs/v1/spec/00-introduction.md#L1-L10)
- [specs/v1/spec/90-extensibility.md](file://specs/v1/spec/90-extensibility.md#L1-L26)
- [specs/v1/tools/build_spec.py](file://specs/v1/tools/build_spec.py#L174-L239)

## Testing and Quality Assurance
**Updated** Comprehensive testing infrastructure with multiple layers of quality assurance:

### Local Testing
- **Unit tests**: Run with pytest for comprehensive coverage: `make test-unit`
- **Full test suite**: Execute all tests with automatic fallback: `make test`
- **Coverage reporting**: Generate detailed coverage reports: `make test-coverage`
- **Individual test groups**: Run specific test categories: `python -m pytest test_scheduling.py TestDuration -v`

### Test Categories
- **Duration parsing**: Validate "5d", "1w", integer, and invalid format handling.
- **Date calculations**: Test workday vs calendar day computations with weekend exclusions.
- **Schedule computation**: Complex scenarios including dependencies, precedence rules, and inheritance.
- **Validation**: Semantic validation of plans and views with proper error handling.
- **Fixtures**: Real-world scenarios using YAML fixture files for regression testing.

### Test Fixtures
- **Extension fields**: Custom x: namespace usage for team assignments and risk assessment.
- **Parent inheritance**: Opt-in inheritance via x.scheduling.anchor_to_parent_start.
- **Conflict resolution**: Start vs after dependency precedence.
- **Weekend exclusions**: Proper workday calculations across weekends.
- **Week-based durations**: 1w = 5 workdays with chaining dependencies.

### Quality Metrics
- **Test coverage**: Automatic coverage reporting via pytest-cov.
- **Regression prevention**: Fixture-based tests ensure scenarios remain valid.
- **Edge case handling**: Comprehensive validation of boundary conditions.

**Section sources**
- [specs/v1/tests/test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L1-L305)
- [specs/v1/tests/fixtures/extensions.plan.yaml](file://specs/v1/tests/fixtures/extensions.plan.yaml#L1-L22)
- [specs/v1/tests/fixtures/parent_inheritance.plan.yaml](file://specs/v1/tests/fixtures/parent_inheritance.plan.yaml#L1-L29)
- [specs/v1/tests/fixtures/start_after_conflict.plan.yaml](file://specs/v1/tests/fixtures/start_after_conflict.plan.yaml#L1-L20)
- [specs/v1/tests/fixtures/weekends_exclusion.plan.yaml](file://specs/v1/tests/fixtures/weekends_exclusion.plan.yaml#L1-L21)
- [specs/v1/tests/fixtures/weeks_duration.plan.yaml](file://specs/v1/tests/fixtures/weeks_duration.plan.yaml#L1-L24)
- [Makefile](file://Makefile#L111-L127)

## Extending the Specification
Guidelines for extending the specification and maintaining ecosystem compatibility:
- Extend with optional fields; avoid breaking changes.
- Group user-defined fields under a namespace (e.g., x:) to prevent conflicts.
- Document new fields in spec/*.md and regenerate SPEC.md.
- Ensure tools ignore unknown fields and preserve formatting when applicable.
- **Update test fixtures to include new extension scenarios.**
- **Add comprehensive test coverage for new functionality.**

**Section sources**
- [specs/v1/spec/90-extensibility.md](file://specs/v1/spec/90-extensibility.md#L1-L26)
- [specs/v1/tools/build_spec.py](file://specs/v1/tools/build_spec.py#L174-L239)

## Continuous Integration Guidance
**Updated** Enhanced CI/CD integration with comprehensive testing and coverage reporting:

### Recommended CI Steps
- **Install dependencies**: `make deps` (installs pyyaml, jsonschema, pytest, pytest-cov)
- **Validate examples**: `make validate-examples`
- **Validate fixtures**: `make validate-fixtures`
- **Build and check spec**: `make build-spec && make check-spec`
- **Run full test suite**: `make test` (runs pytest with fallback to unittest)
- **Generate coverage reports**: `make test-coverage`
- **Docker-based CI**: `make ci-docker` for containerized testing

### CI Pipeline Structure
```mermaid
sequenceDiagram
participant Dev as "Developer"
participant CI as "CI Runner"
participant Make as "Makefile"
participant PyTest as "pytest"
participant Coverage as "pytest-cov"
participant Docker as "Docker"
Dev->>CI : Push changes
CI->>Make : make ci
Make->>Make : make check-spec
Make->>Make : make validate
Make->>PyTest : make test
PyTest->>Coverage : make test-coverage
Coverage-->>PyTest : Coverage report
PyTest-->>Make : Test results
Make-->>CI : CI status
CI-->>Dev : Report status
```

**Diagram sources**
- [Makefile](file://Makefile#L210-L217)
- [Makefile](file://Makefile#L111-L127)
- [Makefile](file://Makefile#L158-L161)

### Docker Integration
- **Containerized testing**: `make docker-test` for isolated test environments.
- **Containerized validation**: `make docker-validate` for schema validation.
- **Containerized builds**: `make docker-build` for SPEC.md generation.
- **Interactive shells**: `make docker-shell` for debugging.

### Quality Gates
- **SPEC.md freshness**: Automated spec integrity checking.
- **YAML validation**: Comprehensive plan and views validation.
- **Test execution**: Full test suite with coverage reporting.
- **Schema validation**: JSON schema syntax verification.

**Section sources**
- [Makefile](file://Makefile#L210-L217)
- [Makefile](file://Makefile#L111-L127)
- [Makefile](file://Makefile#L158-L161)
- [Makefile](file://Makefile#L179-L204)

## Conclusion
Opskarta's development model emphasizes a clear specification, minimal reference tools, practical examples, and comprehensive testing infrastructure. The addition of the 304-line test suite with fixture-based scenarios ensures robust quality assurance and regression prevention. Contributors should focus on small, well-scoped changes, maintain backward compatibility, ensure spec and tooling integrity, and leverage the comprehensive testing framework. By following the contribution workflow, testing practices, extension guidelines, and CI/CD integration, you can confidently add features and improve the ecosystem while preserving interoperability and maintaining high code quality standards.