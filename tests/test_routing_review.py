from __future__ import annotations

import unittest

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
        self.assertEqual(review["decision"], "promote")
        self.assertIn("retirement", review)
        self.assertIn("required_proof", review)


if __name__ == "__main__":
    unittest.main()
