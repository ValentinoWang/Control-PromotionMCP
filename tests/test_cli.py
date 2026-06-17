from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from control_promotion.cli import main


class CLITest(unittest.TestCase):
    def test_validate_adapter_command(self) -> None:
        with redirect_stdout(io.StringIO()) as stdout:
            code = main(["validate-adapter", ".control-promotion.yaml", "--format", "json"])
        self.assertEqual(code, 0)
        self.assertIn('"valid": true', stdout.getvalue())

    def test_route_command(self) -> None:
        with redirect_stdout(io.StringIO()) as stdout:
            code = main(
                [
                    "route",
                    "--failure-class",
                    "semantic metric literal",
                    "--detectability",
                    "static",
                    "--recurrence",
                    "repeated",
                    "--harm",
                    "high",
                ]
            )
        self.assertEqual(code, 0)
        self.assertIn("scripts/quality", stdout.getvalue())

    def test_validate_guard_spec_command(self) -> None:
        with redirect_stdout(io.StringIO()) as stdout:
            code = main(
                [
                    "validate-guard-spec",
                    "examples/guard-specs/good-creation-table-contract.yaml",
                    "--format",
                    "json",
                ]
            )
        self.assertEqual(code, 0)
        self.assertIn('"valid": true', stdout.getvalue())

    def test_review_guard_command_blocks_bad_spec(self) -> None:
        with redirect_stdout(io.StringIO()) as stdout:
            code = main(
                [
                    "review-guard",
                    "examples/guard-specs/bad-incident-string-guard.yaml",
                    "--format",
                    "json",
                ]
            )
        self.assertEqual(code, 1)
        self.assertIn('"can_promote_to_L5": false', stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
