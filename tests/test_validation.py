from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from control_promotion.validation import validate_project_adapter, validate_smell_catalog


class ValidationTest(unittest.TestCase):
    def test_project_adapter_is_valid(self) -> None:
        result = validate_project_adapter(".control-promotion.yaml")
        self.assertTrue(result["valid"], result)

    def test_smell_catalog_is_valid(self) -> None:
        result = validate_smell_catalog("references/smell-catalog.yaml")
        self.assertTrue(result["valid"], result)

    def test_catalog_reports_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.yaml"
            path.write_text("version: 1\nsmells:\n  - id: missing-fields\n", encoding="utf-8")
            result = validate_smell_catalog(path)
        self.assertFalse(result["valid"])
        self.assertTrue(any("missing required field" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
