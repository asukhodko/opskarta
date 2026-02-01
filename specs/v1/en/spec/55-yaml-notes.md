# YAML Encoding Recommendations

opskarta format uses YAML (recommended) or JSON for serialization. This section describes recommendations for correct data encoding in YAML.

## Dates (fields `start`, `finish`, `excludes`)

YAML parsers (especially YAML 1.1, including PyYAML by default) may automatically convert strings that look like dates into special data types (date/datetime). This can lead to unexpected behavior.

### Strongly Recommended Format

```yaml
nodes:
  task1:
    title: "Task"
    start: "2024-03-15"  # Quoted string — STRONGLY RECOMMENDED
    duration: "5d"
```

### Allowed but Risky Format

```yaml
nodes:
  task1:
    title: "Task"
    start: 2024-03-15  # Unquoted — PyYAML 1.1 converts to date type!
    duration: 5d       # Unquoted — valid plain scalar, but better quoted
```

> **Warning:** `start: 2024-03-15` without quotes in PyYAML will be converted to Python `datetime.date(2024, 3, 15)`, not string `"2024-03-15"`. opskarta tools MUST normalize such values (see "Type Normalization" section).

## Duration (field `duration`)

`duration` value MUST be a string in format `<number><unit>` (e.g., `5d`, `2w`).

### Correct Examples

```yaml
duration: "5d"   # 5 days (recommended format)
duration: "2w"   # 2 weeks (= 10 workdays)
duration: "10d"  # 10 days
duration: 5d     # Valid YAML plain scalar, parsed as string "5d"
```

> **Note:** `5d` without quotes is a valid YAML plain scalar and correctly parses as string. Quotes are recommended for consistency with the `start` field, but not required.

### Incorrect Examples

```yaml
duration: 5      # Number without unit — doesn't match format
duration: "0d"   # Zero is not allowed
duration: "-1d"  # Negative values are not allowed
```

## YAML and JSON Equivalence

opskarta data format is JSON-compatible. YAML is recommended as more convenient syntax for manual editing, but tools MUST convert YAML values to canonical opskarta types (see "Type Normalization" section).

> **Important:** YAML is a superset of JSON, but YAML 1.1 parsers (e.g., PyYAML) have auto-typing features that can lead to unexpected results. opskarta tools MUST correctly handle such cases.

### YAML

```yaml
version: 1
meta:
  id: "my-project"
  title: "My Project"
nodes:
  task1:
    title: "First Task"
    start: "2024-03-01"
    duration: "5d"
  task2:
    title: "Second Task"
    after:
      - task1
    duration: "3d"
```

### JSON (equivalent)

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

## Multiline Strings (field `notes`)

For multiline notes, use literal block (`|`) or folded block (`>`):

### Literal Block (preserves line breaks)

```yaml
nodes:
  task1:
    title: "Task with Notes"
    notes: |
      First line of note.
      Second line of note.
      
      Paragraph after empty line.
```

### Folded Block (joins lines)

```yaml
nodes:
  task1:
    title: "Task with Notes"
    notes: >
      This is a long note that
      will be joined into one line
      with spaces between parts.
```

## Special Characters

When using special characters in strings, enclose them in quotes:

```yaml
nodes:
  task1:
    title: "Task: important!"      # Colon requires quotes
    issue: "JIRA-123"              # No problem
    notes: "Note with # symbol"    # Hash requires quotes
```

## Type Normalization

opskarta tools (validators, renderers) MUST normalize YAML values to canonical opskarta types:

### Canonical Field Types

| Field | Canonical Type | Allowed YAML Input | Normalization |
|-------|----------------|-------------------|---------------|
| `start` | string `YYYY-MM-DD` | string or YAML date | `date(2024, 3, 15)` → `"2024-03-15"` |
| `finish` | string `YYYY-MM-DD` | string or YAML date | `date(2024, 3, 15)` → `"2024-03-15"` |
| `excludes[]` | string | string or YAML date | `date(2024, 3, 8)` → `"2024-03-08"` |
| `duration` | string `Nd` or `Nw` | string | — |
| `node_id` (keys in `nodes`) | string | string | — |

### Normalization Rules

1. **Field `start`:**
   - If YAML parser returned a `date` or `datetime` object, tool MUST convert it to string in `YYYY-MM-DD` format.
   - Example: Python `datetime.date(2024, 3, 15)` → string `"2024-03-15"`.

2. **Field `finish`:**
   - Similar to `start`: if YAML parser returned a `date` or `datetime` object, tool MUST convert it to string in `YYYY-MM-DD` format.

3. **Elements `excludes[]`:**
   - Each element of `excludes` array in view (`gantt_views`) may be a YAML date.
   - Tool MUST normalize such elements to string `YYYY-MM-DD`.
   - Example: `excludes: [weekends, 2024-03-08]` — if `2024-03-08` parsed as `date`, normalize to string `"2024-03-08"`.

4. **Node identifiers (`node_id`):**
   - Keys in `nodes` dictionary MUST be strings.
   - If YAML parser returned a non-string key (e.g., number), tool MAY convert it to string or reject with error.
   - Recommendation: reject non-string keys for explicitness.

5. **General principle:**
   - Tools MUST NOT crash on correct YAML files just because of YAML typing quirks.
   - Tools MUST convert values to canonical types before further processing.

### Python Normalization Example

```python
from datetime import date, datetime

def normalize_date_field(value):
    """Normalizes date value (start, finish) to string YYYY-MM-DD."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value.strip()
    raise ValueError(f"Invalid date type: {type(value)}")


def normalize_start(value):
    """Normalizes start value to string YYYY-MM-DD."""
    return normalize_date_field(value)


def normalize_finish(value):
    """Normalizes finish value to string YYYY-MM-DD."""
    return normalize_date_field(value)


def normalize_excludes(excludes_list):
    """Normalizes excludes list, converting YAML dates to strings."""
    result = []
    for item in excludes_list:
        if isinstance(item, (date, datetime)):
            result.append(item.isoformat() if isinstance(item, date) else item.date().isoformat())
        else:
            result.append(str(item))
    return result
```
