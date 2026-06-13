from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlLevel:
    id: str
    name: str
    description: str


CONTROL_LADDER: tuple[ControlLevel, ...] = (
    ControlLevel("L0", "raw_evidence", "A one-off incident, fix, or observation."),
    ControlLevel("L1", "reusable_observation", "A recurring pattern with a named failure class."),
    ControlLevel("L2", "documentation", "Human-readable guidance without executable enforcement."),
    ControlLevel("L3", "skill_workflow", "Agent workflow guidance for repeatable review or remediation."),
    ControlLevel("L4", "scoped_agents_rule", "Repository or subtree instruction that constrains agent behavior."),
    ControlLevel("L5", "static_quality_guard", "Deterministic static check suitable for local and CI execution."),
    ControlLevel("L6", "runtime_qa_harness", "Runtime, UI, screenshot, E2E, or integration harness."),
    ControlLevel("L7", "type_schema_contract_prevention", "Type, schema, API, or contract design prevents recurrence."),
    ControlLevel("L8", "retired_guard", "A former heuristic control retired after a stronger prevention exists."),
)


def ladder_as_dict() -> dict[str, dict[str, str]]:
    return {
        level.id: {"name": level.name, "description": level.description}
        for level in CONTROL_LADDER
    }


def level_name(level_id: str) -> str:
    for level in CONTROL_LADDER:
        if level.id == level_id:
            return level.name
    raise ValueError(f"unknown control level: {level_id}")
