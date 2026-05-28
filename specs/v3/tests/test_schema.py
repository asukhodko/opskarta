"""Tests for v3 JSON Schema artifacts."""

import json
import unittest
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - optional dependency guard
    jsonschema = None


@unittest.skipIf(jsonschema is None, "jsonschema is not installed")
class FragmentSchemaTests(unittest.TestCase):
    """Validate schema behavior that plain JSON parsing cannot catch."""

    @classmethod
    def setUpClass(cls):
        schema_path = Path(__file__).parents[1] / "schemas" / "fragment.schema.json"
        cls.schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(cls.schema)
        cls.validator = jsonschema.Draft202012Validator(cls.schema)

    def assert_schema_valid(self, document: dict) -> None:
        errors = sorted(self.validator.iter_errors(document), key=lambda error: list(error.path))
        self.assertEqual([], [error.message for error in errors])

    def assert_schema_invalid(self, document: dict, expected: str) -> None:
        messages = [error.message for error in self.validator.iter_errors(document)]
        self.assertTrue(
            any(expected in message for message in messages),
            f"Expected {expected!r} in schema errors: {messages}",
        )

    def test_node_deps_accept_string_and_dep_edge(self):
        """deps items may be shorthand strings or full dep_edge objects."""
        self.assert_schema_valid(
            {
                "version": 3,
                "nodes": {
                    "root": {"title": "Root"},
                    "task": {
                        "title": "Task",
                        "deps": [
                            "root",
                            {
                                "id": "root",
                                "type": "ss",
                                "lag": "1d",
                                "hard": False,
                                "note": "Start together",
                            },
                        ],
                    },
                },
            }
        )

    def test_node_deps_reject_invalid_items(self):
        """deps schema must reject values that are neither strings nor dep_edge objects."""
        self.assert_schema_invalid(
            {
                "version": 3,
                "nodes": {
                    "root": {"title": "Root"},
                    "task": {"title": "Task", "deps": [123]},
                },
            },
            "123 is not valid under any of the given schemas",
        )

    def test_lane_nodes_are_required(self):
        """Gantt lanes need an explicit node list before renderers can use them."""
        self.assert_schema_invalid(
            {
                "version": 3,
                "nodes": {"root": {"title": "Root"}},
                "views": {
                    "gantt": {
                        "lanes": {
                            "main": {"title": "Main path"},
                        },
                    },
                },
            },
            "'nodes' is a required property",
        )


if __name__ == "__main__":
    unittest.main()
