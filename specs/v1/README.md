# opskarta Specification v1

This directory contains the opskarta specification in two languages.

## Languages

| Language | Directory | Description |
|----------|-----------|-------------|
| **English** | [en/](en/) | Primary specification (canonical) |
| **Russian** | [ru/](ru/) | Translation |

## Structure

```
specs/v1/
├── en/                     # English (primary)
│   ├── SPEC.md             # Full specification
│   ├── SPEC.min.md         # Compact version
│   ├── README.md
│   ├── spec/               # Source sections
│   └── examples/           # Example files
├── ru/                     # Russian (translation)
│   ├── SPEC.md
│   ├── SPEC.min.md
│   ├── README.md
│   ├── spec/
│   └── examples/
├── schemas/                # JSON Schemas (shared)
├── tests/                  # Test suite (shared)
└── tools/                  # Build and validation tools
```

## Quick Start

```bash
# Build specification (both languages)
make spec-all

# Build English only
make spec-en

# Build Russian only
make spec-ru

# Validate examples
make validate-examples-all
```

## Tools

See [tools/README.md](tools/README.md) for documentation on:
- `build_spec.py` — Assembles SPEC.md from sections
- `validate.py` — Validates plan and view files
- `render/` — Gantt diagram renderers
