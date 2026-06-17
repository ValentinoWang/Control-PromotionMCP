from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RouteDecision:
    destination: str
    control_level: str
    why: tuple[str, ...]
    why_not: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "destination": self.destination,
            "control_level": self.control_level,
            "why": list(self.why),
            "why_not": self.why_not,
        }


def route_control_destination(
    failure_class: str = "",
    detectability: str = "",
    recurrence: str = "",
    harm: str = "",
    scope: str = "",
) -> RouteDecision:
    text = " ".join([failure_class, detectability, recurrence, harm, scope]).lower()
    reasons: list[str] = []

    if detectability in {"contract", "schema"} or any(token in text for token in ("type/schema", "type_schema", "openapi", "sdk")):
        return RouteDecision(
            destination="type_schema_contract",
            control_level="L7_type_schema_contract_prevention",
            why=("prevention_possible_at_interface_boundary", "machine_enforceable_contract"),
            why_not={
                "docs": "documentation cannot make illegal states unrepresentable",
                "static_quality_guard": "a stronger contract can prevent the failure class",
                "runtime_qa_harness": "runtime proof is useful but should not be the primary control",
            },
        )

    if detectability == "runtime" or (
        detectability != "static"
        and any(token in text for token in ("runtime", "screenshot", "visual", "e2e", "browser", "navigation"))
    ):
        return RouteDecision(
            destination="scripts/qa",
            control_level="L6_runtime_qa_harness",
            why=("runtime_observation_required", "static_signal_insufficient"),
            why_not={
                "docs": "documentation does not prove runtime behavior",
                "scripts/quality": "static inspection cannot observe the required state",
                "root_AGENTS": "the failure class needs executable verification",
            },
        )

    if any(token in text for token in ("static", "literal", "grep", "ast", "lint", "generated", "symlink", "ssot")):
        reasons.append("static_detectable")
    if recurrence in {"repeated", "high", "recurring"} or "repeated" in text:
        reasons.append("stable_failure_class")
    if harm in {"high", "critical"} or "high" in text or "critical" in text:
        reasons.append("actionable_failure_message_required")

    if reasons:
        return RouteDecision(
            destination="scripts/quality",
            control_level="L5_static_quality_guard",
            why=tuple(dict.fromkeys(reasons)),
            why_not={
                "docs": "documentation does not prevent recurrence",
                "scripts_qa": "runtime execution is not required for the primary signal",
                "root_AGENTS": "the rule is specific enough to enforce mechanically",
            },
        )

    if any(token in text for token in ("workflow", "agent", "review", "migration")):
        return RouteDecision(
            destination=".agents/skills",
            control_level="L3_skill_workflow",
            why=("repeatable_agent_workflow", "judgment_still_required"),
            why_not={
                "scripts/quality": "deterministic detection is not yet clear",
                "scripts/qa": "runtime proof is not the key evidence",
                "type_schema_contract": "prevention boundary has not been identified",
            },
        )

    return RouteDecision(
        destination="docs",
        control_level="L2_documentation",
        why=("insufficient_recurrence_or_detectability",),
        why_not={
            "scripts/quality": "needs a stable machine-detectable fingerprint",
            "scripts/qa": "needs a runtime-observable invariant",
            "root_AGENTS": "too immature for a global agent rule",
        },
    )
