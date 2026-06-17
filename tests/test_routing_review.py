from __future__ import annotations

import unittest

from control_promotion.io import load_data
from control_promotion.review import evaluate_control_candidate
from control_promotion.core.routing import route_control_destination


class RoutingReviewTest(unittest.TestCase):
    def test_static_guard_routes_to_quality(self) -> None:
        route = route_control_destination(
            failure_class="semantic metric literal",
            detectability="static",
            recurrence="repeated",
            harm="high",
            scope="frontend",
        )
        self.assertEqual(route.destination, "scripts/quality")
        self.assertTrue(route.control_level.startswith("L5"))

    def test_runtime_routes_to_qa(self) -> None:
        route = route_control_destination(
            failure_class="mobile screenshot overflow",
            detectability="runtime",
            recurrence="repeated",
            harm="high",
            scope="mobile",
        )
        self.assertEqual(route.destination, "scripts/qa")
        self.assertTrue(route.control_level.startswith("L6"))

    def test_candidate_review_has_retirement_plan(self) -> None:
        review = evaluate_control_candidate(
            "frontend-metric-source-guard prevents semantic KPI literals",
            evidence={"paths": ["scripts/quality/check_frontend_metric_source_guard.py"]},
            context={"recurrence": "repeated", "harm": "high"},
        )
        self.assertEqual(review["decision"], "refactor_before_promote")
        self.assertIn("retirement", review)
        self.assertIn("required_proof", review)
        self.assertIn("abstraction_review", review)
        self.assertIn("guard_quality_review", review)

    def test_incident_string_guard_is_flagged_as_overfit(self) -> None:
        review = evaluate_control_candidate(
            "creation table name guard prevents user-facing deprecated table aliases",
            evidence={
                "paths": ["scripts/quality/check_creation_table_name_guard.py"],
                "snippets": [
                    """
                    FORBIDDEN_USER_FACING_CREATION_TABLE_PHRASES = (
                        "创作灵感表",
                        "灵感表：",
                        "写入创作灵感表",
                    )
                    ALLOWED_FILES = (
                        "openclaw-agents/media/AGENTS.md",
                        "openclaw-agents/media/USER.md",
                        "openclaw-agents/media/TOOLS.md",
                    )
                    """
                ],
            },
            context={"recurrence": "repeated", "harm": "high"},
        )

        abstraction = review["abstraction_review"]
        self.assertEqual(review["decision"], "refactor_before_promote")
        self.assertEqual(review["control_level"], "L5_static_quality_guard")
        self.assertEqual(review["failure_class"]["subject"], "quality guard")
        self.assertEqual(abstraction["specificity_risk"], "high")
        self.assertIn("literal_incident_phrase_denylist", abstraction["overfit_signals"])
        self.assertIn("fixed_current_file_allowlist", abstraction["overfit_signals"])
        self.assertIn("canonical_contract", abstraction["missing_abstraction"])

    def test_contract_guard_has_low_specificity_risk(self) -> None:
        review = evaluate_control_candidate(
            "creation table name guard enforces canonical table-name contract with scoped surface discovery",
            evidence={
                "paths": ["scripts/quality/check_creation_table_name_guard.py"],
                "snippets": [
                    """
                    CREATION_TABLE_NAME_CONTRACT = {
                        "owner": "CREATION_OUTPUT_TABLE_CONTRACT",
                        "canonical": "03_创作任务总表",
                        "env_key": "MEDIA_OS_CREATION_TASKS_URL",
                        "deprecated_aliases": {"创作灵感表", "灵感表"},
                    }
                    SCAN_ROOTS = ("docs/说明书", "openclaw-agents/media")
                    EXCLUDE_PATHS = ("tmp/**", "agents-results/**")
                    """
                ],
                "fixtures": {
                    "negative": ["产出位置：写入创作灵感表"],
                    "positive": ["产出位置：写入 03_创作任务总表"],
                },
                "exception_policy": {
                    "required_fields": ["reason", "owner", "expires", "scope"],
                },
                "contract": {
                    "owner": "CREATION_OUTPUT_TABLE_CONTRACT",
                    "canonical": "03_创作任务总表",
                    "source": "MEDIA_OS_CREATION_TASKS_URL",
                },
                "guard_spec": load_data("examples/guard-specs/good-creation-table-contract.yaml"),
            },
            context={"recurrence": "repeated", "harm": "high"},
        )

        abstraction = review["abstraction_review"]
        gate = review["guard_quality_review"]["promotion_gate"]
        self.assertEqual(review["decision"], "promote")
        self.assertEqual(review["control_level"], "L5_static_quality_guard")
        self.assertEqual(abstraction["specificity_risk"], "low")
        self.assertEqual(abstraction["recommendation"], "promote")
        self.assertTrue(gate["can_promote_to_L5"])


if __name__ == "__main__":
    unittest.main()
