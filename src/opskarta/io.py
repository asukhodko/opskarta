from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from .errors import OpskartaError


def load_yaml(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise OpskartaError(f"File not found: {p}") from e
    except Exception as e:  # noqa: BLE001
        raise OpskartaError(f"Failed to parse YAML: {p}: {e}") from e

    if not isinstance(data, dict):
        raise OpskartaError(f"Top-level YAML must be a mapping/object: {p}")

    return data
