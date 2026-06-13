from __future__ import annotations

from typing import Any


def render_smell_gate_report(review: dict[str, Any]) -> str:
    failure = review.get("failure_class", {})
    routing = review.get("routing", {})
    lines = [
        "# Smell Gate Report",
        "",
        f"- Decision: `{review.get('decision', 'unknown')}`",
        f"- Control level: `{review.get('control_level', 'unknown')}`",
        f"- Confidence: `{review.get('confidence', 'unknown')}`",
        f"- Destination: `{routing.get('destination', 'unknown')}`",
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
