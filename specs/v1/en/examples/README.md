# opskarta v1 Examples

This directory contains example plan and view files of varying complexity.

## Examples

| Example | Description | Files |
|---------|-------------|-------|
| [minimal/](minimal/) | Minimal valid plan | only `.plan.yaml` |
| [hello/](hello/) | Basic example with plan and views | `.plan.yaml` + `.views.yaml` |
| [advanced/](advanced/) | Advanced example with multiple tracks | `.plan.yaml` + `.views.yaml` |

## How to Use

All examples can be validated and rendered using [reference tools](../../tools/):

```bash
cd specs/v1

# Validation
python tools/validate.py en/examples/hello/hello.plan.yaml en/examples/hello/hello.views.yaml

# Generate Gantt
python -m tools.render.plan2gantt \
    --plan en/examples/hello/hello.plan.yaml \
    --views en/examples/hello/hello.views.yaml \
    --view overview
```

## See Also

- [Full Specification](../SPEC.md)
- [JSON Schema](../../schemas/)
