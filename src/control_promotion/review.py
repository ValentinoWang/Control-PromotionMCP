from __future__ import annotations

from typing import Any

from control_promotion.core.abstraction import review_abstraction
from control_promotion.core.fingerprint import classify_failure_class
from control_promotion.core.guard_spec import review_guard_quality
from control_promotion.core.proof_obligation import proof_for_level
from control_promotion.core.retirement import retirement_condition
from control_promotion.core.routing import route_control_destination


def evaluate_control_candidate(
    candidate_text: str,
    evidence: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence = evidence or {}
    context = context or {}
    fingerprint = classify_failure_class(candidate_text)
    route = route_control_destination(
        failure_class=str(fingerprint["bad_pattern"]),
        detectability=_infer_detectability(candidate_text, evidence),
        recurrence=str(context.get("recurrence", "repeated")),
        harm=str(context.get("harm", "high")),
        scope=str(context.get("scope", "project")),
    )
    required_proof = proof_for_level(route.control_level)
    provided_paths = evidence.get("paths", []) if isinstance(evidence, dict) else []
    provided_commands = evidence.get("commands", []) if isinstance(evidence, dict) else []
    confidence = "guarded" if provided_paths or provided_commands else "tentative"
    abstraction_review = review_abstraction(candidate_text, evidence)
    guard_quality_review = review_guard_quality(evidence.get("guard_spec"), abstraction_review)
    decision = _decision_for(route.control_level, abstraction_review, guard_quality_review)

    return {
        "decision": decision,
        "control_level": route.control_level,
        "recommended_future_level": _future_level(route.control_level),
        "confidence": confidence,
        "protected_invariant": fingerprint["broken_invariant"],
        "failure_class": fingerprint,
        "routing": route.to_dict(),
        "required_proof": required_proof,
        "provided_evidence": {
            "paths": provided_paths,
            "commands": provided_commands,
        },
        "abstraction_review": abstraction_review,
        "guard_quality_review": guard_quality_review,
        "retirement": retirement_condition(route.control_level, str(fingerprint["bad_pattern"])),
    }


def _infer_detectability(candidate_text: str, evidence: dict[str, Any]) -> str:
    text = candidate_text.lower()
    paths = " ".join(str(path).lower() for path in evidence.get("paths", []))
    joined = f"{text} {paths}"
    if "model-provider-drift" in joined or "policy.default_provider" in joined:
        return "static"
    if any(token in joined for token in ("screenshot", "playwright", "appium", "e2e", "runtime", "browser")):
        return "runtime"
    if any(token in joined for token in ("schema", "openapi", "type_schema", "sdk")):
        return "contract"
    if any(token in joined for token in ("guard", "lint", "static", "grep", "ast", "scripts/quality")):
        return "static"
    return "review"


def _future_level(control_level: str) -> str:
    if control_level.startswith("L5"):
        return "L7_type_schema_contract_prevention"
    if control_level.startswith("L6"):
        return "L7_type_schema_contract_prevention"
    if control_level.startswith("L3"):
        return "L5_static_quality_guard"
    return control_level


def _decision_for(
    control_level: str,
    abstraction_review: dict[str, Any],
    guard_quality_review: dict[str, Any],
) -> str:
    if not control_level.startswith(("L5", "L6", "L7")):
        return "hold"
    gate = guard_quality_review["promotion_gate"]
    if control_level.startswith("L5") and not gate["can_promote_to_L5"]:
        return gate["decision"]
    specificity_risk = abstraction_review["specificity_risk"]
    if specificity_risk == "high":
        return "refactor_before_promote"
    if specificity_risk == "medium":
        return "promote_with_follow_up"
    if specificity_risk == "low":
        return "promote"
    raise ValueError(f"unknown specificity risk: {specificity_risk}")
