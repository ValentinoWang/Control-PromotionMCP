from __future__ import annotations


def retirement_condition(control_level: str, failure_class: str) -> dict[str, str]:
    if control_level.startswith("L5"):
        return {
            "condition": (
                "A stronger type, schema, API, or contract control makes the "
                f"{failure_class or 'failure class'} impossible in production paths."
            ),
            "action": "downgrade_or_delete_heuristic_guard_after_ci_overlap_period",
        }
    if control_level.startswith("L6"):
        return {
            "condition": "The runtime invariant is guaranteed by lower-level contracts and covered by consumer tests.",
            "action": "keep_one_smoke_or_retire_redundant_runtime_harness",
        }
    if control_level.startswith("L7"):
        return {
            "condition": "Contract remains the source of truth and downstream compatibility tests pass.",
            "action": "retire_weaker_overlapping_guidance_or_guards",
        }
    return {
        "condition": "A stable executable control exists and covers the documented scenario.",
        "action": "replace_human_guidance_with_machine_check_where_possible",
    }
