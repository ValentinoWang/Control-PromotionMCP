from __future__ import annotations


def classify_failure_class(text: str) -> dict[str, str | list[str]]:
    lowered = text.lower()
    subject = "governance control"
    boundary = "project repository"
    bad_pattern = "unclassified recurring failure"
    missing_proof: list[str] = ["named_failure_class", "protected_invariant"]

    if _is_model_provider_drift(lowered):
        subject = "model provider resolution"
        boundary = "business code, runtime entrypoints, and bot config policy"
        bad_pattern = (
            "business code or runtime bypasses config/openclaw_bots.json "
            "policy.default_provider and falls back to legacy provider/model"
        )
        missing_proof = [
            "config_policy_source",
            "resolver_entrypoint",
            "runtime_sink_discovery",
            "legacy_provider_alias_set",
            "positive_negative_runtime_or_static_fixtures",
        ]
    elif "metric" in lowered or "kpi" in lowered:
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
    elif any(token in lowered for token in ("guard", "denylist", "forbidden", "allowlist", "blacklist")):
        subject = "quality guard"
        boundary = "project invariant"
        bad_pattern = "exact incident literals or current file paths guarded without a named contract"
        missing_proof = [
            "canonical_contract",
            "targeted_positive_case",
            "targeted_negative_case",
            "scoped_surface_discovery",
            "exception_policy",
        ]

    return {
        "subject": subject,
        "boundary": boundary,
        "broken_invariant": f"{subject} must preserve its protected invariant at {boundary}",
        "bad_pattern": bad_pattern,
        "missing_proof": missing_proof,
    }


def _is_model_provider_drift(lowered_text: str) -> bool:
    provider_signal = any(token in lowered_text for token in ("provider", "model", "default_provider"))
    policy_signal = any(
        token in lowered_text
        for token in (
            "openclaw_bots",
            "policy.default_provider",
            "default provider",
            "legacy provider",
            "legacy model",
            "model-provider-drift",
            "model provider drift",
        )
    )
    bypass_signal = any(token in lowered_text for token in ("bypass", "fallback", "legacy", "drift"))
    return provider_signal and (policy_signal or bypass_signal)
