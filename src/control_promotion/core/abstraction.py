from __future__ import annotations

import re
from typing import Any


def review_abstraction(candidate_text: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence = evidence or {}
    source_text = _combined_source_text(candidate_text, evidence)
    lower = source_text.lower()
    overfit_signals: list[str] = []
    missing_abstraction: list[str] = []

    has_contract = _has_contract(source_text, evidence)
    has_fixture_pair = _has_fixture_pair(evidence)
    has_surface_discovery = _has_surface_discovery(lower)
    has_exception_policy = _has_exception_policy(source_text, evidence)
    has_downstream_test = _has_downstream_test(source_text, evidence)

    if _has_literal_denylist(source_text):
        overfit_signals.append("literal_incident_phrase_denylist")
    if _has_fixed_file_allowlist(source_text) and not has_surface_discovery:
        overfit_signals.append("fixed_current_file_allowlist")
    if not has_fixture_pair:
        overfit_signals.append("missing_targeted_fixtures")
    if not has_contract:
        overfit_signals.append("missing_canonical_contract")
    if "contract" in lower and not has_downstream_test:
        overfit_signals.append("no_downstream_consumer_test")

    if not has_contract:
        missing_abstraction.append("canonical_contract")
    if _mentions_alias_or_table(lower) and "deprecated_alias" not in lower:
        missing_abstraction.append("deprecated_alias_set")
    if not has_surface_discovery:
        missing_abstraction.append("scoped_surface_discovery")
    if not has_exception_policy:
        missing_abstraction.append("exception_policy")
    if "contract" in lower and not has_downstream_test:
        missing_abstraction.append("downstream_consumer_test")

    specificity_risk = _risk_level(overfit_signals, missing_abstraction)
    return {
        "specificity_risk": specificity_risk,
        "overfit_signals": overfit_signals,
        "missing_abstraction": missing_abstraction,
        "recommendation": _recommendation(specificity_risk),
    }


def _combined_source_text(candidate_text: str, evidence: dict[str, Any]) -> str:
    parts: list[str] = [candidate_text]
    for key in ("source_text", "snippet"):
        value = evidence.get(key)
        if isinstance(value, str):
            parts.append(value)
    snippets = evidence.get("snippets")
    if isinstance(snippets, list):
        parts.extend(str(item) for item in snippets)
    files = evidence.get("files")
    if isinstance(files, dict):
        parts.extend(str(value) for value in files.values())
    for key in ("paths", "commands"):
        value = evidence.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
    contract = evidence.get("contract")
    if isinstance(contract, dict):
        parts.extend(f"{key}: {value}" for key, value in contract.items())
    return "\n".join(parts)


def _has_literal_denylist(source_text: str) -> bool:
    patterns = (
        r"\bFORBIDDEN_[A-Z0-9_]*(PHRASE|PHRASES|STRINGS|LITERALS)\b",
        r"\b(DENYLIST|BLACKLIST|BLOCKLIST)_[A-Z0-9_]*(PHRASE|PHRASES|STRINGS|LITERALS)?\b",
        r"\bforbidden_(phrase|phrases|strings|literals)\b",
    )
    return any(re.search(pattern, source_text) for pattern in patterns)


def _has_fixed_file_allowlist(source_text: str) -> bool:
    if re.search(r"\b(ALLOWED|ALLOWLIST|TARGET|SCANNED)_[A-Z0-9_]*(FILES|PATHS)\b", source_text):
        return True
    quoted_paths = re.findall(r"['\"][^'\"]+\.(?:md|py|json|yaml|yml|txt)['\"]", source_text)
    return len(set(quoted_paths)) >= 3


def _has_contract(source_text: str, evidence: dict[str, Any]) -> bool:
    contract = evidence.get("contract")
    if isinstance(contract, dict) and contract.get("canonical") and (contract.get("owner") or contract.get("env_key")):
        return True
    lower = source_text.lower()
    required_any = ("canonical", "canonical_contract", "table_name_contract")
    return any(token in lower for token in required_any) and ("owner" in lower or "env_key" in lower)


def _has_fixture_pair(evidence: dict[str, Any]) -> bool:
    fixtures = evidence.get("fixtures")
    if not isinstance(fixtures, dict):
        return False
    positive = fixtures.get("positive") or fixtures.get("passing")
    negative = fixtures.get("negative") or fixtures.get("failing")
    return bool(positive) and bool(negative)


def _has_surface_discovery(lower_source_text: str) -> bool:
    discovery_tokens = (
        "surface discovery",
        "surface_discovery",
        "discover_surfaces",
        "scoped surface",
        "scan roots",
        "scan_roots",
        "exclude_paths",
        "excludes",
        "glob",
        "rglob",
    )
    return any(token in lower_source_text for token in discovery_tokens)


def _has_exception_policy(source_text: str, evidence: dict[str, Any]) -> bool:
    policy = evidence.get("exception_policy")
    if isinstance(policy, dict):
        required = {"reason", "owner", "expires", "scope"}
        return required.issubset(set(policy.get("required_fields", [])) | set(policy.keys()))
    lower = source_text.lower()
    return all(token in lower for token in ("reason", "owner", "expires", "scope"))


def _has_downstream_test(source_text: str, evidence: dict[str, Any]) -> bool:
    tests = evidence.get("tests")
    if isinstance(tests, list) and any("consumer" in str(test).lower() for test in tests):
        return True
    lower = source_text.lower()
    return "downstream consumer" in lower or "consumer test" in lower


def _mentions_alias_or_table(lower_source_text: str) -> bool:
    return any(token in lower_source_text for token in ("alias", "table", "表", "canonical"))


def _risk_level(overfit_signals: list[str], missing_abstraction: list[str]) -> str:
    strong_overfit = {"literal_incident_phrase_denylist", "fixed_current_file_allowlist"}
    if strong_overfit.intersection(overfit_signals) and "canonical_contract" in missing_abstraction:
        return "high"
    if len(overfit_signals) >= 3 or len(missing_abstraction) >= 3:
        return "medium"
    return "low"


def _recommendation(specificity_risk: str) -> str:
    if specificity_risk == "high":
        return "refactor_before_promote"
    if specificity_risk == "medium":
        return "promote_with_follow_up"
    return "promote"
