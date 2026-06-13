from __future__ import annotations


BASE_PROOF = (
    "named_failure_class",
    "protected_invariant",
    "targeted_positive_case",
    "targeted_negative_case",
    "actionable_failure_message",
)


def proof_for_level(control_level: str) -> list[str]:
    if control_level.startswith("L5"):
        return [
            *BASE_PROOF,
            "wrapper_command",
            "ci_mode",
            "documented_exception_policy",
        ]
    if control_level.startswith("L6"):
        return [
            *BASE_PROOF,
            "runtime_fixture_or_route",
            "artifact_capture_path",
            "non_flaky_execution_boundary",
        ]
    if control_level.startswith("L7"):
        return [
            *BASE_PROOF,
            "contract_owner",
            "migration_plan",
            "downstream_consumer_test",
        ]
    if control_level.startswith("L3"):
        return [
            *BASE_PROOF,
            "trigger_conditions",
            "expected_agent_outputs",
        ]
    return list(BASE_PROOF)
