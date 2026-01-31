# Validation System

<cite>
**Referenced Files in This Document**
- [validate.py](file://specs/v1/tools/validate.py)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json)
- [views.schema.json](file://specs/v1/schemas/views.schema.json)
- [60-validation.md](file://specs/v1/spec/60-validation.md)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md)
- [10-plan-file.md](file://specs/v1/spec/10-plan-file.md)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md)
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml)
- [README.md](file://README.md)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive duplicate key detection for YAML files
- Implemented recursive date normalization from YAML dates to strings
- Enhanced error reporting with sophisticated severity level classification
- Added new validation rules for unique node identifiers and color formats
- Updated architecture diagrams to reflect new validation components
- Enhanced CLI interface with improved error handling and reporting

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
This document describes the validation system for Opskarta's plan and views file validator. It explains the three-tier validation approach:
- Syntax validation (YAML parsing with duplicate key detection)
- Schema validation (JSON Schema compliance)
- Semantic validation (referential integrity, business rules, and format validation)

The system now includes sophisticated error reporting with severity levels, comprehensive duplicate key detection, and enhanced validation rules for unique identifiers and color formats. It covers validation levels, error reporting mechanisms, debugging capabilities, and integration patterns.

## Project Structure
The validation system lives under the v1 specification and includes:
- A Python CLI validator script with enhanced error reporting
- JSON Schema definitions for plan and views
- Specification documents detailing validation rules and severity levels
- Example plan and views files demonstrating validation scenarios

```mermaid
graph TB
subgraph "Spec v1"
V["specs/v1/tools/validate.py"]
P["specs/v1/schemas/plan.schema.json"]
W["specs/v1/schemas/views.schema.json"]
S60["specs/v1/spec/60-validation.md"]
S40["specs/v1/spec/40-statuses.md"]
S10["specs/v1/spec/10-plan-file.md"]
S30["specs/v1/spec/30-views-file.md"]
E_HELLO_P["specs/v1/examples/hello/hello.plan.yaml"]
E_HELLO_V["specs/v1/examples/hello/hello.views.yaml"]
E_ADV_P["specs/v1/examples/advanced/program.plan.yaml"]
E_ADV_V["specs/v1/examples/advanced/program.views.yaml"]
end
V --> P
V --> W
V --> S60
V --> S40
V --> S10
V --> S30
V --> E_HELLO_P
V --> E_HELLO_V
V --> E_ADV_P
V --> E_ADV_V
```

**Diagram sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L752)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L90)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L1-L299)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md#L49-L93)
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L326)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)

**Section sources**
- [README.md](file://README.md#L68-L83)

## Core Components
- CLI entrypoint and argument parsing with enhanced error reporting
- YAML loader with comprehensive duplicate key detection and date normalization
- JSON Schema loader and validator
- Plan semantic validator with unique identifier validation and color format checking
- Views semantic validator with project linkage validation
- Sophisticated error reporting system with severity levels (error, warn, info)
- Structured exception handling with detailed error messages

Key responsibilities:
- Load and parse YAML safely with duplicate key detection
- Normalize YAML dates to standardized string format
- Optionally validate against built-in or custom JSON Schemas
- Enforce semantic rules including unique identifiers and color formats
- Detect cycles and format violations
- Provide hierarchical error reporting with severity classification

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L752)
- [validate.py](file://specs/v1/tools/validate.py#L69-L192)
- [validate.py](file://specs/v1/tools/validate.py#L194-L329)
- [validate.py](file://specs/v1/tools/validate.py#L431-L579)
- [validate.py](file://specs/v1/tools/validate.py#L586-L618)

## Architecture Overview
The validator runs in enhanced stages with sophisticated error handling:
1. Parse YAML files with duplicate key detection and date normalization
2. Optional JSON Schema validation
3. Semantic validation with unique identifier and format validation
4. Report warnings and errors with severity classification, exit with appropriate code

```mermaid
sequenceDiagram
participant U as "User"
participant CLI as "CLI main()"
participant Y as "load_yaml() with duplicate key detection"
participant DN as "normalize_yaml_dates()"
participant JS as "load_json_schema()/validate_with_schema()"
participant VP as "validate_plan() with unique ID & color validation"
participant VV as "validate_views()"
U->>CLI : "python validate.py [PLAN] [VIEWS] [--schema] [--plan-schema PATH] [--views-schema PATH]"
CLI->>Y : "load PLAN with duplicate key detection"
Y->>DN : "normalize YAML dates to strings"
DN-->>Y : "normalized data"
alt "--schema"
CLI->>JS : "load_json_schema(plan.schema.json)"
JS-->>CLI : "schema"
CLI->>JS : "validate_with_schema(PARSE_PLAN, SCHEMA)"
JS-->>CLI : "warnings or ValidationError"
end
CLI->>VP : "validate_plan(parsed_plan with unique IDs & colors)"
VP-->>CLI : "warnings, infos, or ValidationError"
opt VIEWS provided
CLI->>Y : "load VIEWS with duplicate key detection"
Y->>DN : "normalize YAML dates to strings"
DN-->>Y : "normalized data"
alt "--schema"
CLI->>JS : "load_json_schema(views.schema.json)"
JS-->>CLI : "schema"
CLI->>JS : "validate_with_schema(PARSE_VIEWS, SCHEMA)"
JS-->>CLI : "warnings or ValidationError"
end
CLI->>VV : "validate_views(parsed_views, parsed_plan)"
VV-->>CLI : "warnings, infos, or ValidationError"
end
CLI-->>U : "Success with severity classification or error with exit code"
```

**Diagram sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L752)
- [validate.py](file://specs/v1/tools/validate.py#L69-L192)
- [validate.py](file://specs/v1/tools/validate.py#L114-L134)
- [validate.py](file://specs/v1/tools/validate.py#L586-L618)
- [validate.py](file://specs/v1/tools/validate.py#L135-L329)
- [validate.py](file://specs/v1/tools/validate.py#L431-L579)

## Detailed Component Analysis

### Enhanced CLI and Argument Parsing
- Supports validating a plan alone or both plan and views
- Optional JSON Schema validation mode
- Custom schema paths for plan and views
- Clear help and usage examples with enhanced error reporting
- Sophisticated exit codes with user interruption handling

Exit codes:
- 0 on success
- 1 on validation errors
- 130 on keyboard interrupt

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L752)

### Enhanced YAML Loading and Error Reporting
- Loads YAML safely with comprehensive duplicate key detection
- Normalizes YAML dates to standardized string format (YYYY-MM-DD)
- Reports missing files, YAML parse errors, and duplicate key errors
- Provides structured error messages with path, value, and expected type
- Uses custom DuplicateKeyLoader for robust duplicate detection

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L69-L192)

### Recursive Date Normalization
- Converts YAML datetime objects to standardized date strings
- Recursively processes nested dictionaries and lists
- Ensures consistent date format across all validation stages
- Maintains data integrity while standardizing formats

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L114-L134)

### Comprehensive Duplicate Key Detection
- Custom YAML loader that detects duplicate keys during parsing
- Raises DuplicateKeyError for any duplicate key found
- Provides precise error reporting with the problematic key
- Prevents silent data loss from YAML duplicate key overrides

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L75-L111)

### Sophisticated Error Reporting with Severity Levels
- Structured exceptions with severity classification
- Three-level severity system: error, warn, info
- Enhanced message formatting with path, value, and expected information
- Available alternatives for reference validation
- Hierarchical error reporting for complex validation failures

Severity levels:
- **error**: Critical validation failure, stops validation process
- **warn**: Potential issue requiring attention, validation continues
- **info**: Informational message, validation successful

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L36-L68)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L197-L221)

### JSON Schema Validation Mode
- Optional mode invoked with a flag
- Loads custom schema files if provided
- Uses a third-party validator to enforce strict JSON Schema compliance
- Produces detailed error messages with JSON Pointer-style paths
- Integrates seamlessly with enhanced error reporting system

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L586-L618)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L90)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)

### Enhanced Plan Semantic Validation
Checks:
- Root fields: version and nodes presence and types
- Unique node identifier validation: all node_id keys must be unique
- Nodes: title presence and non-empty string
- Referential integrity:
  - parent must reference an existing node ID
  - after must be a list of existing node IDs
  - status must reference an existing status key if present
- Color format validation: hex color format validation for status colors
- Format validation:
  - start must match YYYY-MM-DD
  - duration must match <number><unit> where unit is d or w
- Cycle detection:
  - parent chain acyclic
  - after graph acyclic (DFS with state tracking)

Warnings:
- Non-default version triggers a warning
- Start date conflicts with dependencies trigger warnings
- Missing duration for planned nodes triggers warnings

Infos:
- Default duration usage for planned nodes
- Specific dates in excludes (non-core renderer hints)

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L135-L329)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L5-L81)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md#L49-L93)
- [10-plan-file.md](file://specs/v1/spec/10-plan-file.md#L1-L30)

### Enhanced Views Semantic Validation
Checks:
- Root fields: version and project presence and types
- project must equal meta.id from the plan
- gantt_views structure:
  - lanes must be a non-empty object
  - each lane must have a nodes list
  - each node ID in lanes must exist in the plan
- Excludes validation: specific dates vs calendar exclusions

Warnings:
- Specific dates in excludes (non-core renderer hints)

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L431-L579)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L82-L115)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md#L1-L34)

### Enhanced Error Reporting and Debugging
- Structured exceptions with severity classification
- Enhanced message formatting with path, value, and expected type
- Available alternatives for reference validation
- Hierarchical error reporting for complex validation failures
- Clear separation of error, warning, and informational messages
- User-friendly error messages with actionable guidance

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L36-L68)
- [validate.py](file://specs/v1/tools/validate.py#L742-L748)

## Dependency Analysis
```mermaid
graph LR
CLI["CLI main()"] --> LOAD_YAML["load_yaml() with duplicate key detection"]
CLI --> LOAD_SCHEMA["load_json_schema()"]
CLI --> VALIDATE_SCHEMA["validate_with_schema()"]
CLI --> VALIDATE_PLAN["validate_plan() with unique ID & color validation"]
CLI --> VALIDATE_VIEWS["validate_views()"]
VALIDATE_PLAN --> CYCLE_PARENT["_check_cycles_parent()"]
VALIDATE_PLAN --> CYCLE_AFTER["_check_cycles_after()"]
VALIDATE_PLAN --> DUPLICATE_KEY_CHECKER["_make_duplicate_key_checker()"]
VALIDATE_PLAN --> DATE_NORMALIZATION["normalize_yaml_dates()"]
LOAD_SCHEMA --> PLAN_SCHEMA["plan.schema.json"]
LOAD_SCHEMA --> VIEWS_SCHEMA["views.schema.json"]
```

**Diagram sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L752)
- [validate.py](file://specs/v1/tools/validate.py#L75-L111)
- [validate.py](file://specs/v1/tools/validate.py#L114-L134)
- [validate.py](file://specs/v1/tools/validate.py#L135-L329)
- [validate.py](file://specs/v1/tools/validate.py#L431-L579)
- [validate.py](file://specs/v1/tools/validate.py#L586-L618)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L90)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L752)

## Performance Considerations
- Large operational maps:
  - YAML parsing with duplicate key detection adds minimal overhead
  - Date normalization is O(n) where n is total number of data elements
  - JSON Schema validation adds overhead proportional to schema complexity and data size
  - Semantic validation is O(N + E) for N nodes and E edges (dependencies)
  - Cycle detection uses DFS with O(N + E) time and O(N) space
- Recommendations:
  - Prefer streaming parsers for extremely large files if needed
  - Use JSON Schema only when required by CI policy
  - Cache loaded schemas when validating many files
  - Split large plans into smaller, cohesive units
  - Duplicate key detection adds O(k) overhead where k is number of keys processed

## Troubleshooting Guide
Common validation errors and remedies:
- Missing or invalid YAML with duplicate keys
  - Ensure the file exists and is valid YAML
  - Verify the root element is an object
  - Check for duplicate keys in YAML structure
- Duplicate key detection errors
  - Remove duplicate keys from YAML files
  - Use unique identifiers for all nodes and statuses
- Enhanced format validation failures
  - Install the required library for schema mode
  - Use built-in schemas or provide compatible custom schemas
  - Validate color formats using hex notation (#RRGGBB)
- Semantic errors with severity classification
  - Referential integrity: ensure parent, after, and status IDs exist
  - Format errors: confirm start and duration formats
  - Cycle detection: remove circular parent/after links
  - Unique identifier violations: ensure all node_id values are unique
- Views linkage mismatch
  - project must equal meta.id from the plan

Debugging tips:
- Run with verbose output to see stage-by-stage progress
- Use the schema mode to catch type mismatches early
- Validate plan and views separately to isolate issues
- Inspect the printed path and expected value to fix quickly
- Pay attention to severity level classification for prioritizing fixes

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L742-L748)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L124-L140)

## Conclusion
Opskarta's enhanced validation system provides a robust, layered approach to ensure plan and views correctness with sophisticated error reporting and comprehensive duplicate key detection. By combining syntax checks with duplicate key prevention, JSON Schema enforcement, and semantic validations with severity classification, teams can catch mistakes early, maintain reliable operational maps, and ensure data integrity through comprehensive validation rules.

## Appendices

### CLI Usage and Parameters
- Basic usage
  - Validate a plan: python tools/validate.py examples/hello/hello.plan.yaml
  - Validate plan and views: python tools/validate.py examples/hello/hello.plan.yaml examples/hello/hello.views.yaml
  - Enable JSON Schema mode: python tools/validate.py --schema examples/hello/hello.plan.yaml
- Parameters
  - plan_file: Path to the plan file
  - views_file: Path to the views file (optional)
  - --schema: Enable JSON Schema validation
  - --plan-schema PATH: Custom plan schema path (default: schemas/plan.schema.json)
  - --views-schema PATH: Custom views schema path (default: schemas/views.schema.json)
- Exit codes
  - 0: Success
  - 1: Validation error
  - 130: Interrupted by user

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L752)
- [README.md](file://README.md#L68-L83)

### Enhanced Validation Rules Summary
- Plan
  - Required fields: version (int), nodes (object)
  - Node required: title (string)
  - Unique identifier validation: all node_id keys must be unique
  - Color format validation: hex color format (#RRGGBB) for status colors
  - Referential integrity: parent, after, status must reference existing IDs
  - Format: start (YYYY-MM-DD), duration (<number>d|w)
  - No cycles in parent or after
- Views
  - Required fields: version (int), project (string)
  - project must equal meta.id from plan
  - gantt_views.lanes must reference existing node IDs
  - Excludes validation: specific dates vs calendar exclusions

**Section sources**
- [60-validation.md](file://specs/v1/spec/60-validation.md#L5-L115)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md#L49-L93)
- [10-plan-file.md](file://specs/v1/spec/10-plan-file.md#L1-L30)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md#L1-L34)

### Example Files
- Minimal plan and views
  - [project.plan.yaml](file://specs/v1/examples/minimal/project.plan.yaml#L1-L6)
- Hello example
  - [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44)
  - [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)
- Advanced example
  - [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L326)
  - [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)

**Section sources**
- [hello.plan.yaml](file://specs/v1/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/examples/hello/hello.views.yaml#L1-L13)
- [program.plan.yaml](file://specs/v1/examples/advanced/program.plan.yaml#L1-L326)
- [program.views.yaml](file://specs/v1/examples/advanced/program.views.yaml#L1-L93)