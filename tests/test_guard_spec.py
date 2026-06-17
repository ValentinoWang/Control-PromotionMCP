from __future__ import annotations

import unittest

from control_promotion.core.guard_spec import review_guard_quality, validate_guard_spec_data
from control_promotion.io import load_data
from control_promotion.review import evaluate_control_candidate


class GuardSpecTest(unittest.TestCase):
    def test_good_guard_spec_is_valid_and_promotable(self) -> None:
        spec = load_data("examples/guard-specs/good-creation-table-contract.yaml")
        validation = validate_guard_spec_data(spec)
        review = review_guard_quality(spec)

        self.assertTrue(validation["valid"], validation)
        self.assertTrue(review["promotion_gate"]["can_promote_to_L5"], review)

    def test_bad_guard_spec_blocks_promotion(self) -> None:
        spec = load_data("examples/guard-specs/bad-incident-string-guard.yaml")
        validation = validate_guard_spec_data(spec)
        review = review_guard_quality(spec)

        self.assertFalse(validation["valid"])
        self.assertFalse(review["promotion_gate"]["can_promote_to_L5"])
        self.assertIn("missing_named_contract", review["promotion_gate"]["blockers"])
        self.assertIn("missing_near_miss_fixture", review["promotion_gate"]["blockers"])

    def test_candidate_file_with_good_guard_spec_promotes(self) -> None:
        candidate = load_data("examples/candidates/good-creation-table-contract.yaml")
        evidence = candidate["evidence"]
        evidence = {**evidence, "guard_spec": load_data(evidence["guard_spec_path"])}
        review = evaluate_control_candidate(
            candidate["candidate_text"],
            evidence=evidence,
            context=candidate["context"],
        )

        self.assertEqual(review["decision"], "promote")
        self.assertTrue(review["guard_quality_review"]["promotion_gate"]["can_promote_to_L5"])

    def test_candidate_file_with_bad_guard_spec_blocks_promotion(self) -> None:
        candidate = load_data("examples/candidates/bad-incident-string-guard.yaml")
        evidence = candidate["evidence"]
        evidence = {**evidence, "guard_spec": load_data(evidence["guard_spec_path"])}
        review = evaluate_control_candidate(
            candidate["candidate_text"],
            evidence=evidence,
            context=candidate["context"],
        )

        self.assertEqual(review["decision"], "refactor_before_promote")
        self.assertEqual(review["abstraction_review"]["specificity_risk"], "high")
        self.assertFalse(review["guard_quality_review"]["promotion_gate"]["can_promote_to_L5"])
        self.assertIn("high_specificity_risk", review["guard_quality_review"]["promotion_gate"]["blockers"])

    def test_model_provider_drift_sample_promotes_with_correct_taxonomy(self) -> None:
        candidate = load_data("examples/candidates/good-model-provider-drift.yaml")
        evidence = candidate["evidence"]
        evidence = {**evidence, "guard_spec": load_data(evidence["guard_spec_path"])}
        review = evaluate_control_candidate(
            candidate["candidate_text"],
            evidence=evidence,
            context=candidate["context"],
        )

        self.assertEqual(review["decision"], "promote")
        self.assertEqual(review["failure_class"]["subject"], "model provider resolution")
        self.assertTrue(review["guard_quality_review"]["promotion_gate"]["can_promote_to_L5"])


if __name__ == "__main__":
    unittest.main()
