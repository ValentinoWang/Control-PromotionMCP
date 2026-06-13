from __future__ import annotations


def classify_failure_class(text: str) -> dict[str, str | list[str]]:
    lowered = text.lower()
    subject = "governance control"
    boundary = "project repository"
    bad_pattern = "unclassified recurring failure"
    missing_proof: list[str] = ["named_failure_class", "protected_invariant"]

    if "metric" in lowered or "kpi" in lowered:
        subject = "user-facing semantic metric"
        boundary = "production UI and localization"
        bad_pattern = "semantic metric presented without provenance"
        missing_proof = ["api_source", "provider_source", "formula", "unavailable_state"]
    elif "generated" in lowered:
        subject = "generated artifact"
        boundary = "generated code or generated documentation"
        bad_pattern = "manual edit applied to generated output"
        missing_proof = ["generator_source", "regeneration_command", "drift_check"]
    elif "ssot" in lowered or "symlink" in lowered or "readlink" in lowered:
        subject = "single source of truth link"
        boundary = "shared harness or governance document"
        bad_pattern = "repo-local edit made through an SSOT symlink"
        missing_proof = ["link_target", "ownership_classification", "overlay_decision"]
    elif "screenshot" in lowered or "overflow" in lowered or "visual" in lowered:
        subject = "runtime visual contract"
        boundary = "rendered UI surface"
        bad_pattern = "visual regression not captured by static checks"
        missing_proof = ["viewport", "route", "artifact", "acceptance_rule"]

    return {
        "subject": subject,
        "boundary": boundary,
        "broken_invariant": f"{subject} must preserve its protected invariant at {boundary}",
        "bad_pattern": bad_pattern,
        "missing_proof": missing_proof,
    }
