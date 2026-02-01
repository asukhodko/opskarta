# Validation System

<cite>
**Referenced Files in This Document**
- [validate.py](file://specs/v1/tools/validate.py)
- [Makefile](file://Makefile)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json)
- [views.schema.json](file://specs/v1/schemas/views.schema.json)
- [60-validation.md](file://specs/v1/spec/60-validation.md)
- [SPEC.md](file://specs/v1/SPEC.md)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md)
- [10-plan-file.md](file://specs/v1/spec/10-plan-file.md)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md)
- [hello.plan.yaml](file://specs/v1/en/examples/hello/hello.plan.yaml)
- [hello.views.yaml](file://specs/v1/en/examples/hello/hello.views.yaml)
- [program.plan.yaml](file://specs/v1/en/examples/advanced/program.plan.yaml)
- [program.views.yaml](file://specs/v1/en/examples/advanced/program.views.yaml)
- [hello.plan.ru.yaml](file://specs/v1/ru/examples/hello/hello.plan.yaml)
- [hello.views.ru.yaml](file://specs/v1/ru/examples/hello/hello.views.yaml)
- [README.md](file://README.md)
- [finish_field.plan.yaml](file://specs/v1/tests/fixtures/finish_field.plan.yaml)
- [start_after_conflict.plan.yaml](file://specs/v1/tests/fixtures/start_after_conflict.plan.yaml)
- [after_no_anchor.plan.yaml](file://specs/v1/tests/fixtures/after_no_anchor.plan.yaml)
- [test_scheduling.py](file://specs/v1/tests/test_scheduling.py)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive bilingual example validation system with new Makefile targets
- Enhanced validate.py with 247+ lines of new validation logic for improved error reporting
- Introduced validate-examples-en, validate-examples-ru, and validate-examples-all targets
- Added support for Russian language examples alongside English examples
- Enhanced CLI interface with improved error reporting and debugging capabilities
- Expanded validation rules with stricter format validation and enhanced temporal field consistency checks

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Bilingual Example Validation System](#bilingual-example-validation-system)
7. [Enhanced CLI and Error Reporting](#enhanced-cli-and-error-reporting)
8. [Dependency Analysis](#dependency-analysis)
9. [Performance Considerations](#performance-considerations)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Conclusion](#conclusion)
12. [Appendices](#appendices)

## Introduction
This document describes the validation system for Opskarta's plan and views file validator. It explains the three-tier validation approach:
- Syntax validation (YAML parsing with comprehensive duplicate key detection)
- Schema validation (JSON Schema compliance)
- Semantic validation (referential integrity, business rules, and enhanced format validation)

The system now includes sophisticated error reporting with severity levels, comprehensive duplicate key detection, and enhanced validation rules for unique identifiers, color formats, and temporal field consistency. It covers validation levels, error reporting mechanisms, debugging capabilities, and integration patterns.

**Updated** The validation system now supports bilingual example validation with dedicated targets for English and Russian examples, providing comprehensive validation coverage across both language variants. The enhanced validate.py script includes 247+ lines of new validation logic with improved error reporting and debugging capabilities.

## Project Structure
The validation system lives under the v1 specification and includes:
- A Python CLI validator script with enhanced error reporting and bilingual support
- Makefile targets for automated validation of English and Russian examples
- JSON Schema definitions for plan and views
- Specification documents detailing validation rules and severity levels
- Bilingual example plan and views files demonstrating validation scenarios
- Test fixtures covering new finish field requirements and consistency checks

```mermaid
graph TB
subgraph "Spec v1"
V["specs/v1/tools/validate.py"]
M["Makefile"]
P["specs/v1/schemas/plan.schema.json"]
W["specs/v1/schemas/views.schema.json"]
SE["specs/v1/en/examples/"]
SR["specs/v1/ru/examples/"]
S60["specs/v1/spec/60-validation.md"]
SPEC["specs/v1/SPEC.md"]
S40["specs/v1/spec/40-statuses.md"]
S10["specs/v1/spec/10-plan-file.md"]
S30["specs/v1/spec/30-views-file.md"]
E_HELLO_P["specs/v1/en/examples/hello/hello.plan.yaml"]
E_HELLO_V["specs/v1/en/examples/hello/hello.views.yaml"]
E_ADV_P["specs/v1/en/examples/advanced/program.plan.yaml"]
E_ADV_V["specs/v1/en/examples/advanced/program.views.yaml"]
R_HELLO_P["specs/v1/ru/examples/hello/hello.plan.yaml"]
R_HELLO_V["specs/v1/ru/examples/hello/hello.views.yaml"]
TF["specs/v1/tests/fixtures/finish_field.plan.yaml"]
TSA["specs/v1/tests/fixtures/start_after_conflict.plan.yaml"]
TAN["specs/v1/tests/fixtures/after_no_anchor.plan.yaml"]
TS["specs/v1/tests/test_scheduling.py"]
end
V --> P
V --> W
V --> S60
V --> SPEC
V --> S40
V --> S10
V --> S30
V --> E_HELLO_P
V --> E_HELLO_V
V --> E_ADV_P
V --> E_ADV_V
V --> R_HELLO_P
V --> R_HELLO_V
V --> TF
V --> TSA
V --> TAN
V --> TS
M --> SE
M --> SR
M --> V
```

**Diagram sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L1081)
- [Makefile](file://Makefile#L149-L187)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L95)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L1-L377)
- [SPEC.md](file://specs/v1/SPEC.md#L1434-L1511)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md#L49-L93)
- [hello.plan.yaml](file://specs/v1/en/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/en/examples/hello/hello.views.yaml#L1-L13)
- [program.plan.yaml](file://specs/v1/en/examples/advanced/program.plan.yaml#L1-L331)
- [program.views.yaml](file://specs/v1/en/examples/advanced/program.views.yaml#L1-L93)
- [hello.plan.ru.yaml](file://specs/v1/ru/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.ru.yaml](file://specs/v1/ru/examples/hello/hello.views.yaml#L1-L13)
- [finish_field.plan.yaml](file://specs/v1/tests/fixtures/finish_field.plan.yaml#L1-L30)
- [start_after_conflict.plan.yaml](file://specs/v1/tests/fixtures/start_after_conflict.plan.yaml#L1-L20)
- [after_no_anchor.plan.yaml](file://specs/v1/tests/fixtures/after_no_anchor.plan.yaml#L1-L27)
- [test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L1-L403)

**Section sources**
- [README.md](file://README.md#L68-L83)

## Core Components
- CLI entrypoint and argument parsing with enhanced error reporting
- YAML loader with comprehensive duplicate key detection and date normalization
- JSON Schema loader and validator
- Plan semantic validator with unique identifier validation, color format checking, and enhanced temporal field validation
- Views semantic validator with project linkage validation
- Sophisticated error reporting system with severity levels (error, warn, info)
- Structured exception handling with detailed error messages
- **New**: Bilingual example validation system with automated validation targets
- **New**: Enhanced CLI interface with improved debugging and error reporting

Key responsibilities:
- Load and parse YAML safely with comprehensive duplicate key detection
- Normalize YAML dates to standardized string format
- Optionally validate against built-in or custom JSON Schemas
- Enforce semantic rules including unique identifiers, color formats, and temporal field consistency
- Detect cycles and format violations
- Provide hierarchical error reporting with severity classification
- **New**: Validate English and Russian example sets automatically
- **New**: Enhanced error reporting with detailed path information and available alternatives

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L1081)
- [validate.py](file://specs/v1/tools/validate.py#L69-L192)
- [validate.py](file://specs/v1/tools/validate.py#L194-L329)
- [validate.py](file://specs/v1/tools/validate.py#L431-L579)
- [validate.py](file://specs/v1/tools/validate.py#L586-L618)
- [Makefile](file://Makefile#L149-L187)

## Architecture Overview
The validator runs in enhanced stages with sophisticated error handling:
1. Parse YAML files with comprehensive duplicate key detection and date normalization
2. Optional JSON Schema validation
3. Semantic validation with unique identifier and enhanced temporal field validation
4. Report warnings and errors with severity classification, exit with appropriate code

```mermaid
sequenceDiagram
participant U as "User"
participant CLI as "CLI main()"
participant Y as "load_yaml() with comprehensive duplicate key detection"
participant DN as "normalize_yaml_dates()"
participant JS as "load_json_schema()/validate_with_schema()"
participant VP as "validate_plan() with enhanced temporal field validation"
participant VV as "validate_views()"
U->>CLI : "python validate.py [PLAN] [VIEWS] [--schema] [--plan-schema PATH] [--views-schema PATH]"
CLI->>Y : "load PLAN with comprehensive duplicate key detection"
Y->>DN : "normalize YAML dates to strings"
DN-->>Y : "normalized data"
alt "--schema"
CLI->>JS : "load_json_schema(plan.schema.json)"
JS-->>CLI : "schema"
CLI->>JS : "validate_with_schema(PARSE_PLAN, SCHEMA)"
JS-->>CLI : "warnings or ValidationError"
end
CLI->>VP : "validate_plan(parsed_plan with enhanced temporal field validation)"
VP-->>CLI : "warnings, infos, or ValidationError"
opt VIEWS provided
CLI->>Y : "load VIEWS with comprehensive duplicate key detection"
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
- [validate.py](file://specs/v1/tools/validate.py#L634-L1081)
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
- [validate.py](file://specs/v1/tools/validate.py#L955-L1081)

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
- [SPEC.md](file://specs/v1/SPEC.md#L1434-L1511)

### JSON Schema Validation Mode
- Optional mode invoked with a flag
- Loads custom schema files if provided
- Uses a third-party validator to enforce strict JSON Schema compliance
- Produces detailed error messages with JSON Pointer-style paths
- Integrates seamlessly with enhanced error reporting system

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L907-L939)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L95)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)

### Enhanced Plan Semantic Validation
Enhanced temporal field validation includes:

**Finish Field Requirements**:
- Finish field validation with strict YYYY-MM-DD regex format (`^\d{4}-\d{2}-\d{2}$`)
- Consistency checks between start, finish, and duration fields
- Backward scheduling support: finish + duration calculates start date
- Mutual exclusivity validation: ensure proper field combinations

**Enhanced Format Validation**:
- Start field: strict YYYY-MM-DD regex validation with date existence checking
- Finish field: identical validation to start field for consistency
- Duration field: enhanced pattern validation `^[1-9][0-9]*[dw]$` with improved error messages
- Cross-field consistency: validate that start + duration equals computed finish

**Temporal Field Consistency Checks**:
- All three fields (start, finish, duration) validation when present
- Computed finish verification against provided finish date
- Error reporting with expected vs actual values for debugging
- Graceful handling of edge cases and invalid combinations

**Cycle Detection and Referential Integrity**:
- Parent chain acyclic validation
- After graph acyclic validation using DFS with state tracking
- Enhanced duplicate key detection for node identifiers
- Improved error reporting for complex validation failures

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L262-L558)
- [SPEC.md](file://specs/v1/SPEC.md#L1499-L1511)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L99-L152)
- [finish_field.plan.yaml](file://specs/v1/tests/fixtures/finish_field.plan.yaml#L1-L30)
- [test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L325-L349)

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
- [validate.py](file://specs/v1/tools/validate.py#L719-L900)
- [SPEC.md](file://specs/v1/SPEC.md#L1499-L1511)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L154-L203)
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
- [validate.py](file://specs/v1/tools/validate.py#L1056-L1076)

## Bilingual Example Validation System

### New Makefile Targets for Bilingual Validation
The validation system now includes comprehensive support for validating both English and Russian example sets:

**Individual Language Targets**:
- `validate-examples-en`: Validates all English example files
- `validate-examples-ru`: Validates all Russian example files
- `validate-examples-all`: Validates both English and Russian example files

**Automated Validation Process**:
- Iterates through all example directories in both language variants
- Automatically discovers plan and views files in each directory
- Validates files sequentially with immediate error reporting
- Provides clear progress indication during validation

**Language Directory Structure**:
- English examples: `specs/v1/en/examples/`
- Russian examples: `specs/v1/ru/examples/`
- Both directories follow identical structure with corresponding files

**Section sources**
- [Makefile](file://Makefile#L149-L187)

### Enhanced Example Files with Bilingual Support
The example files now include comprehensive bilingual support:

**English Examples**:
- Hello example: Git service upgrade with English titles and descriptions
- Advanced example: Complex program scheduling with English terminology
- Minimal example: Simple project structure demonstration

**Russian Examples**:
- Identical structure to English examples with Russian translations
- Titles and descriptions translated to Russian
- Status labels and terminology localized for Russian users
- Meta information including Russian project titles

**Cross-Language Consistency**:
- Both language variants maintain identical structural relationships
- Node hierarchies and dependencies remain consistent across languages
- Validation rules apply uniformly to both language variants
- Error messages and validation behavior are identical regardless of language

**Section sources**
- [hello.plan.yaml](file://specs/v1/en/examples/hello/hello.plan.yaml#L1-L44)
- [hello.plan.ru.yaml](file://specs/v1/ru/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/en/examples/hello/hello.views.yaml#L1-L13)
- [hello.views.ru.yaml](file://specs/v1/ru/examples/hello/hello.views.yaml#L1-L13)

### Integration with CI Pipeline
The bilingual validation system integrates seamlessly with the CI pipeline:

**CI Target**:
- `validate-examples-all`: Validates both language variants during continuous integration
- Ensures quality across all supported languages
- Prevents regression in either language variant

**Automated Testing Benefits**:
- Immediate detection of language-specific issues
- Consistent validation behavior across all example sets
- Streamlined development workflow with automated validation
- Comprehensive coverage of both language variants

**Section sources**
- [Makefile](file://Makefile#L285-L287)

## Enhanced CLI and Error Reporting

### Improved CLI Interface
The enhanced CLI provides comprehensive error reporting and debugging capabilities:

**Enhanced Error Messages**:
- Structured ValidationError exceptions with detailed path information
- Clear separation between error, warning, and informational messages
- Available alternatives for reference validation failures
- Contextual information for complex validation failures

**Debugging Features**:
- Hierarchical error reporting with nested path information
- Available reference suggestions for missing identifiers
- Expected vs actual value comparisons for format validation
- Detailed error messages with actionable guidance

**User Experience Improvements**:
- Clear exit codes with specific meanings
- Graceful handling of keyboard interrupts
- Progress indication during validation stages
- Structured output with severity classification

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L36-L68)
- [validate.py](file://specs/v1/tools/validate.py#L1056-L1076)

### Enhanced Validation Logic
The validate.py script includes 247+ lines of new validation logic:

**Improved Exception Handling**:
- Enhanced ValidationError class with comprehensive formatting
- Structured error messages with path, value, and expected information
- Available alternatives for reference validation failures
- Detailed contextual information for debugging

**Advanced Error Reporting**:
- Hierarchical path construction for complex nested structures
- Available reference suggestions for missing identifiers
- Expected vs actual value comparisons for format validation
- Clear separation of different severity levels

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L36-L68)
- [validate.py](file://specs/v1/tools/validate.py#L1056-L1076)

## Dependency Analysis
```mermaid
graph LR
CLI["CLI main()"] --> LOAD_YAML["load_yaml() with comprehensive duplicate key detection"]
CLI --> LOAD_SCHEMA["load_json_schema()"]
CLI --> VALIDATE_SCHEMA["validate_with_schema()"]
CLI --> VALIDATE_PLAN["validate_plan() with enhanced temporal field validation"]
CLI --> VALIDATE_VIEWS["validate_views()"]
VALIDATE_PLAN --> CYCLE_PARENT["_check_cycles_parent()"]
VALIDATE_PLAN --> CYCLE_AFTER["_check_cycles_after()"]
VALIDATE_PLAN --> DUPLICATE_KEY_CHECKER["_make_duplicate_key_checker()"]
VALIDATE_PLAN --> DATE_NORMALIZATION["normalize_yaml_dates()"]
VALIDATE_PLAN --> FINISH_FIELD_VALIDATION["enhanced finish field validation"]
VALIDATE_PLAN --> AFTER_CHAIN_CHECK["_check_after_chains_have_anchor()"]
LOAD_SCHEMA --> PLAN_SCHEMA["plan.schema.json"]
LOAD_SCHEMA --> VIEWS_SCHEMA["views.schema.json"]
MAKE["Makefile Targets"] --> VALIDATE_EXAMPLES_EN["validate-examples-en"]
MAKE --> VALIDATE_EXAMPLES_RU["validate-examples-ru"]
MAKE --> VALIDATE_EXAMPLES_ALL["validate-examples-all"]
VALIDATE_EXAMPLES_EN --> EN_EXAMPLES["English Examples"]
VALIDATE_EXAMPLES_RU --> RU_EXAMPLES["Russian Examples"]
```

**Diagram sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L1081)
- [validate.py](file://specs/v1/tools/validate.py#L75-L111)
- [validate.py](file://specs/v1/tools/validate.py#L114-L134)
- [validate.py](file://specs/v1/tools/validate.py#L135-L329)
- [validate.py](file://specs/v1/tools/validate.py#L431-L579)
- [validate.py](file://specs/v1/tools/validate.py#L586-L618)
- [Makefile](file://Makefile#L149-L187)
- [plan.schema.json](file://specs/v1/schemas/plan.schema.json#L1-L95)
- [views.schema.json](file://specs/v1/schemas/views.schema.json#L1-L78)

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L634-L1081)
- [Makefile](file://Makefile#L149-L187)

## Performance Considerations
- Large operational maps:
  - YAML parsing with comprehensive duplicate key detection adds minimal overhead
  - Date normalization is O(n) where n is total number of data elements
  - JSON Schema validation adds overhead proportional to schema complexity and data size
  - Semantic validation is O(N + E) for N nodes and E edges (dependencies)
  - Enhanced temporal field validation adds O(N) complexity for date computations
  - Cycle detection uses DFS with O(N + E) time and O(N) space
- **New**: Bilingual validation system adds minimal overhead for example validation
- **New**: Automated validation targets process examples sequentially without significant performance impact
- Recommendations:
  - Prefer streaming parsers for extremely large files if needed
  - Use JSON Schema only when required by CI policy
  - Cache loaded schemas when validating many files
  - Split large plans into smaller, cohesive units
  - Comprehensive duplicate key detection adds O(k) overhead where k is number of keys processed
  - Enhanced finish field validation performs additional date calculations but maintains linear complexity
  - **New**: Bilingual validation system processes examples efficiently with automatic discovery

## Troubleshooting Guide
Common validation errors and remedies:

**Enhanced Temporal Field Errors**:
- Finish field format validation failures
  - Ensure finish field matches YYYY-MM-DD regex pattern
  - Verify date existence in calendar (not February 30th, etc.)
  - Check consistency with start and duration fields
- Inconsistent temporal field combinations
  - When all three fields (start, finish, duration) are present, they must be mutually consistent
  - Use either forward scheduling (start + duration) or backward scheduling (finish + duration)
  - Avoid mixing explicit start with implied finish constraints

**Duplicate Key Detection Errors**:
- Missing or invalid YAML with duplicate keys
  - Ensure the file exists and is valid YAML
  - Verify the root element is an object
  - Check for duplicate keys in YAML structure, including finish field declarations
- Comprehensive duplicate detection prevents silent data loss

**Enhanced Format Validation Failures**:
- Install the required library for schema mode
- Use built-in schemas or provide compatible custom schemas
- Validate color formats using hex notation (#RRGGBB)
- Ensure proper field combinations for temporal scheduling

**Semantic Errors with Severity Classification**:
- Referential integrity: ensure parent, after, and status IDs exist
- Format errors: confirm start, finish, and duration formats
- Cycle detection: remove circular parent/after links
- Unique identifier violations: ensure all node_id values are unique
- Views linkage mismatch: project must equal meta.id from the plan

**Bilingual Validation Issues**:
- **New**: Ensure both English and Russian example files are properly structured
- **New**: Verify that Russian examples maintain the same logical relationships as English examples
- **New**: Check that validation targets can discover both language variants correctly
- **New**: Confirm that cross-language consistency is maintained across all example sets

**Views Linkage Mismatch**:
- project must equal meta.id from the plan

Debugging tips:
- Run with verbose output to see stage-by-stage progress
- Use the schema mode to catch type mismatches early
- Validate plan and views separately to isolate issues
- Inspect the printed path and expected value to fix quickly
- Pay attention to severity level classification for prioritizing fixes
- Test temporal field combinations incrementally when debugging scheduling issues
- **New**: Use specific validation targets (validate-examples-en, validate-examples-ru) for focused debugging
- **New**: Compare English and Russian examples side-by-side to identify language-specific issues

**Section sources**
- [validate.py](file://specs/v1/tools/validate.py#L1056-L1076)
- [SPEC.md](file://specs/v1/SPEC.md#L1434-L1511)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L215-L244)
- [finish_field.plan.yaml](file://specs/v1/tests/fixtures/finish_field.plan.yaml#L1-L30)
- [start_after_conflict.plan.yaml](file://specs/v1/tests/fixtures/start_after_conflict.plan.yaml#L1-L20)
- [after_no_anchor.plan.yaml](file://specs/v1/tests/fixtures/after_no_anchor.plan.yaml#L1-L27)
- [Makefile](file://Makefile#L149-L187)

## Conclusion
Opskarta's enhanced validation system provides a robust, layered approach to ensure plan and views correctness with sophisticated error reporting and comprehensive duplicate key detection. The expanded validation rules now include strict finish field requirements, enhanced temporal field consistency checks, and improved error reporting for edge cases.

**Updated** The validation system now includes comprehensive bilingual example validation with dedicated Makefile targets for English and Russian examples, providing automated validation coverage across both language variants. The enhanced validate.py script includes 247+ lines of new validation logic with improved error reporting, debugging capabilities, and structured exception handling. By combining syntax checks with duplicate key prevention, JSON Schema enforcement, and semantic validations with severity classification, teams can catch mistakes early, maintain reliable operational maps, and ensure data integrity through comprehensive validation rules across all supported languages.

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
- [validate.py](file://specs/v1/tools/validate.py#L955-L1081)
- [README.md](file://README.md#L68-L83)

### Enhanced Validation Rules Summary

**Plan Validation Enhancements**:
- Required fields: version (int), nodes (object)
- Node required: title (string)
- Unique identifier validation: all node_id keys must be unique
- Color format validation: hex color format (#RRGGBB) for status colors
- Enhanced temporal validation:
  - start: strict YYYY-MM-DD regex format with date existence validation
  - finish: identical validation to start for consistency
  - duration: enhanced pattern validation with improved error messages
  - Cross-field consistency: validate relationships between start, finish, and duration
  - Backward scheduling: finish + duration calculates start date
- Referential integrity: parent, after, status must reference existing IDs
- No cycles in parent or after
- Enhanced duplicate key detection for all field types

**Views Validation**:
- Required fields: version (int), project (string)
- project must equal meta.id from plan
- gantt_views.lanes must reference existing node IDs
- Excludes validation: specific dates vs calendar exclusions

**Section sources**
- [SPEC.md](file://specs/v1/SPEC.md#L1434-L1511)
- [60-validation.md](file://specs/v1/spec/60-validation.md#L5-L203)
- [40-statuses.md](file://specs/v1/spec/40-statuses.md#L49-L93)
- [10-plan-file.md](file://specs/v1/spec/10-plan-file.md#L1-L30)
- [30-views-file.md](file://specs/v1/spec/30-views-file.md#L1-L34)
- [finish_field.plan.yaml](file://specs/v1/tests/fixtures/finish_field.plan.yaml#L1-L30)
- [test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L325-L349)

### Bilingual Example Validation Targets

**Makefile Targets**:
- `validate-examples-en`: Validates all English example files with automatic discovery
- `validate-examples-ru`: Validates all Russian example files with automatic discovery
- `validate-examples-all`: Validates both English and Russian example files sequentially

**Validation Process**:
- Iterates through all example directories in both language variants
- Automatically discovers plan and views files using wildcard patterns
- Validates files sequentially with immediate error reporting
- Provides clear progress indication during validation

**Language Support**:
- English examples: `specs/v1/en/examples/`
- Russian examples: `specs/v1/ru/examples/`
- Both directories maintain identical structure and relationships

**Section sources**
- [Makefile](file://Makefile#L149-L187)

### Example Files
- Minimal plan and views
  - [project.plan.yaml](file://specs/v1/en/examples/minimal/project.plan.yaml#L1-L6)
- Hello example with enhanced temporal validation
  - [hello.plan.yaml](file://specs/v1/en/examples/hello/hello.plan.yaml#L1-L44)
  - [hello.views.yaml](file://specs/v1/en/examples/hello/hello.views.yaml#L1-L13)
- Advanced example with complex scheduling
  - [program.plan.yaml](file://specs/v1/en/examples/advanced/program.plan.yaml#L1-L331)
  - [program.views.yaml](file://specs/v1/en/examples/advanced/program.views.yaml#L1-L93)
- **New**: Russian language examples with bilingual support
  - [hello.plan.ru.yaml](file://specs/v1/ru/examples/hello/hello.plan.yaml#L1-L44)
  - [hello.views.ru.yaml](file://specs/v1/ru/examples/hello/hello.views.yaml#L1-L13)

**Section sources**
- [hello.plan.yaml](file://specs/v1/en/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.yaml](file://specs/v1/en/examples/hello/hello.views.yaml#L1-L13)
- [program.plan.yaml](file://specs/v1/en/examples/advanced/program.plan.yaml#L1-L331)
- [program.views.yaml](file://specs/v1/en/examples/advanced/program.views.yaml#L1-L93)
- [hello.plan.ru.yaml](file://specs/v1/ru/examples/hello/hello.plan.yaml#L1-L44)
- [hello.views.ru.yaml](file://specs/v1/ru/examples/hello/hello.views.yaml#L1-L13)

### Test Fixtures Demonstrating New Validation Rules
- Finish field validation and backward scheduling
  - [finish_field.plan.yaml](file://specs/v1/tests/fixtures/finish_field.plan.yaml#L1-L30)
- Start and after conflict resolution
  - [start_after_conflict.plan.yaml](file://specs/v1/tests/fixtures/start_after_conflict.plan.yaml#L1-L20)
- After chain without anchor validation
  - [after_no_anchor.plan.yaml](file://specs/v1/tests/fixtures/after_no_anchor.plan.yaml#L1-L27)

**Section sources**
- [finish_field.plan.yaml](file://specs/v1/tests/fixtures/finish_field.plan.yaml#L1-L30)
- [start_after_conflict.plan.yaml](file://specs/v1/tests/fixtures/start_after_conflict.plan.yaml#L1-L20)
- [after_no_anchor.plan.yaml](file://specs/v1/tests/fixtures/after_no_anchor.plan.yaml#L1-L27)
- [test_scheduling.py](file://specs/v1/tests/test_scheduling.py#L325-L349)