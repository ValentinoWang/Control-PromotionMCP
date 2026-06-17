from __future__ import annotations

from typing import Any


def render_smell_gate_report(review: dict[str, Any]) -> str:
    failure = review.get("failure_class", {})
    routing = review.get("routing", {})
    abstraction = review.get("abstraction_review", {})
    guard_quality = review.get("guard_quality_review", {})
    promotion_gate = guard_quality.get("promotion_gate", {})
    lines = [
        "# Smell Gate Report",
        "",
        f"- Decision: `{review.get('decision', 'unknown')}`",
        f"- Control level: `{review.get('control_level', 'unknown')}`",
        f"- Confidence: `{review.get('confidence', 'unknown')}`",
        f"- Destination: `{routing.get('destination', 'unknown')}`",
        f"- Specificity risk: `{abstraction.get('specificity_risk', 'unknown')}`",
        f"- Can promote to L5: `{promotion_gate.get('can_promote_to_L5', 'unknown')}`",
        "",
        "## Protected Invariant",
        "",
        str(review.get("protected_invariant", "")),
        "",
        "## Failure Class",
        "",
        f"- Subject: {failure.get('subject', 'unknown')}",
        f"- Boundary: {failure.get('boundary', 'unknown')}",
        f"- Bad pattern: {failure.get('bad_pattern', 'unknown')}",
        "",
        "## Required Proof",
        "",
    ]
    lines.extend(f"- {item}" for item in review.get("required_proof", []))
    lines.extend(
        [
            "",
            "## Abstraction / Overfit Assessment",
            "",
            f"- Specificity risk: `{abstraction.get('specificity_risk', 'unknown')}`",
            f"- Recommendation: `{abstraction.get('recommendation', 'unknown')}`",
            "",
            "### Overfit Signals",
            "",
        ]
    )
    lines.extend(_bullet_or_none(abstraction.get("overfit_signals", [])))
    lines.extend(
        [
            "",
            "### Missing Abstraction",
            "",
        ]
    )
    lines.extend(_bullet_or_none(abstraction.get("missing_abstraction", [])))
    lines.extend(
        [
            "",
            "## Guard Quality / Promotion Gate",
            "",
            f"- Can promote to L5: `{promotion_gate.get('can_promote_to_L5', 'unknown')}`",
            f"- Gate decision: `{promotion_gate.get('decision', 'unknown')}`",
            "",
            "### Blockers",
            "",
        ]
    )
    lines.extend(_bullet_or_none(promotion_gate.get("blockers", [])))
    lines.extend(
        [
            "",
            "## Routing",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in routing.get("why", []))
    lines.extend(
        [
            "",
            "## Retirement",
            "",
            str(review.get("retirement", {}).get("condition", "")),
            "",
            f"Action: `{review.get('retirement', {}).get('action', '')}`",
            "",
        ]
    )
    return "\n".join(lines)


def _bullet_or_none(items: Any) -> list[str]:
    if isinstance(items, list) and items:
        return [f"- {item}" for item in items]
    return ["- none"]
