# Examples

- `hello.plan.yaml` + `hello.views.yaml` — самый маленький пример.

Запуск:

```bash
pip install -e ".[dev]"
opskarta validate examples/hello.plan.yaml examples/hello.views.yaml
opskarta render gantt --plan examples/hello.plan.yaml --views examples/hello.views.yaml --view overview
```
