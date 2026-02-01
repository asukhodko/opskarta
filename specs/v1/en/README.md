# opskarta Specification v1

**Status**: Alpha
**Release**: Draft

## Overview

Version 1 of the opskarta specification — the first formal version of the format for describing work plans. The specification defines the structure of YAML files for plans (`.plan.yaml`) and views (`.views.yaml`), as well as rules for their validation and interpretation.

Main capabilities of v1:
- Hierarchical node structure (programs, projects, tasks)
- Flexible status system
- Scheduling with dependencies (`after`) and durations (`duration`)
- Multiple views of a single plan (Gantt, Kanban, lists)
- Extensibility through custom fields (`x:` section)

## Changes from Previous Version

This is the first version of the opskarta specification. No previous versions exist.

## Quick Links

- [Full Specification](SPEC.md)
- [Examples](examples/) — minimal, hello, advanced
- [JSON Schema](../schemas/)
- [Reference Tools](../tools/)
