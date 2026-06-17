from __future__ import annotations

from typing import Any


GUARD_SPEC_REQUIRED_FIELDS = (
    "id",
    "protected_invariant",
    "failure_class",
    "contract",
    "scan_scope",
    "fixtures",
    "exception_policy",
    "retirement",
)

EXCEPTION_REQUIRED_FIELDS = {"reason", "owner", "expires", "scope"}


def validate_guard_spec_data(spec: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(spec, dict):
        return {"valid": False, "errors": ["guard spec must be an object"], "warnings": []}

    for field in GUARD_SPEC_REQUIRED_FIELDS:
        if field not in spec:
            errors.append(f"missing required field '{field}'")

    _validate_contract(spec.get("contract"), errors)
    _validate_scan_scope(spec.get("scan_scope"), errors, warnings)
    _validate_fixtures(spec.get("fixtures"), errors)
    _validate_exception_policy(spec.get("exception_policy"), errors)
    _validate_retirement(spec.get("retirement"), errors)

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def review_guard_quality(
    guard_spec: Any,
    abstraction_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validation = validate_guard_spec_data(guard_spec)
    spec = guard_spec if isinstance(guard_spec, dict) else {}
    abstraction_review = abstraction_review or {}

    contract_review = _contract_review(spec.get("contract"))
    coverage_review = _coverage_review(spec.get("scan_scope"))
    fixture_review = _fixture_review(spec.get("fixtures"))
    exception_review = _exception_review(spec.get("exception_policy"))
    retirement_review = _retirement_review(spec.get("retirement"))
    promotion_gate = _promotion_gate(
        validation,
        abstraction_review,
        contract_review,
        coverage_review,
        fixture_review,
        exception_review,
        retirement_review,
    )

    return {
        "spec_validation": validation,
        "contract_review": contract_review,
        "coverage_review": coverage_review,
        "fixture_review": fixture_review,
        "exception_review": exception_review,
        "retirement_review": retirement_review,
        "promotion_gate": promotion_gate,
    }


def _validate_contract(contract: Any, errors: list[str]) -> None:
    if not isinstance(contract, dict):
        errors.append("contract must be an object")
        return
    for field in ("owner", "canonical", "source"):
        if not contract.get(field):
            errors.append(f"contract.{field} is required")


def _validate_scan_scope(scan_scope: Any, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(scan_scope, dict):
        errors.append("scan_scope must be an object")
        return
    include = scan_scope.get("include")
    exclude = scan_scope.get("exclude")
    if not isinstance(include, list) or not include:
        errors.append("scan_scope.include must be a non-empty list")
    if not isinstance(exclude, list) or not exclude:
        errors.append("scan_scope.exclude must be a non-empty list")
    if isinstance(include, list) and len(include) <= 1:
        warnings.append("scan_scope.include has only one root; confirm this is not current-incident scope")


def _validate_fixtures(fixtures: Any, errors: list[str]) -> None:
    if not isinstance(fixtures, dict):
        errors.append("fixtures must be an object")
        return
    for field in ("positive", "negative", "near_miss", "exception"):
        values = fixtures.get(field)
        if not isinstance(values, list) or not values:
            errors.append(f"fixtures.{field} must be a non-empty list")


def _validate_exception_policy(policy: Any, errors: list[str]) -> None:
    if not isinstance(policy, dict):
        errors.append("exception_policy must be an object")
        return
    required_fields = set(policy.get("required_fields", []))
    missing = sorted(EXCEPTION_REQUIRED_FIELDS - required_fields)
    if missing:
        errors.append(f"exception_policy.required_fields missing: {', '.join(missing)}")


def _validate_retirement(retirement: Any, errors: list[str]) -> None:
    if not isinstance(retirement, dict):
        errors.append("retirement must be an object")
        return
    for field in ("stronger_control", "condition", "action"):
        if not retirement.get(field):
            errors.append(f"retirement.{field} is required")


def _contract_review(contract: Any) -> dict[str, Any]:
    contract = contract if isinstance(contract, dict) else {}
    return {
        "has_named_contract": bool(contract.get("owner") and contract.get("canonical")),
        "owner": contract.get("owner"),
        "canonical": contract.get("canonical"),
        "source": contract.get("source"),
    }


def _coverage_review(scan_scope: Any) -> dict[str, Any]:
    scan_scope = scan_scope if isinstance(scan_scope, dict) else {}
    include = scan_scope.get("include") if isinstance(scan_scope.get("include"), list) else []
    exclude = scan_scope.get("exclude") if isinstance(scan_scope.get("exclude"), list) else []
    return {
        "has_scoped_surface_discovery": bool(include and exclude),
        "include_count": len(include),
        "exclude_count": len(exclude),
        "excludes_generated_or_tmp": any(
            token in str(item).lower()
            for item in exclude
            for token in ("generated", "tmp", "agents-results", "history")
        ),
    }


def _fixture_review(fixtures: Any) -> dict[str, bool]:
    fixtures = fixtures if isinstance(fixtures, dict) else {}
    return {
        "has_positive_case": bool(fixtures.get("positive")),
        "has_negative_case": bool(fixtures.get("negative")),
        "has_near_miss_case": bool(fixtures.get("near_miss")),
        "has_exception_case": bool(fixtures.get("exception")),
    }


def _exception_review(policy: Any) -> dict[str, Any]:
    policy = policy if isinstance(policy, dict) else {}
    required_fields = set(policy.get("required_fields", []))
    return {
        "has_required_fields": EXCEPTION_REQUIRED_FIELDS.issubset(required_fields),
        "required_fields": sorted(required_fields),
    }


def _retirement_review(retirement: Any) -> dict[str, Any]:
    retirement = retirement if isinstance(retirement, dict) else {}
    return {
        "has_retirement_path": bool(
            retirement.get("stronger_control") and retirement.get("condition") and retirement.get("action")
        ),
        "stronger_control": retirement.get("stronger_control"),
    }


def _promotion_gate(
    validation: dict[str, Any],
    abstraction_review: dict[str, Any],
    contract_review: dict[str, Any],
    coverage_review: dict[str, Any],
    fixture_review: dict[str, bool],
    exception_review: dict[str, Any],
    retirement_review: dict[str, Any],
) -> dict[str, Any]:
    blockers = list(validation.get("errors", []))

    if abstraction_review.get("specificity_risk") == "high":
        blockers.append("high_specificity_risk")
    if not contract_review["has_named_contract"]:
        blockers.append("missing_named_contract")
    if not coverage_review["has_scoped_surface_discovery"]:
        blockers.append("missing_scoped_surface_discovery")
    if not fixture_review["has_near_miss_case"]:
        blockers.append("missing_near_miss_fixture")
    if not exception_review["has_required_fields"]:
        blockers.append("missing_exception_policy_fields")
    if not retirement_review["has_retirement_path"]:
        blockers.append("missing_retirement_path")

    blockers = list(dict.fromkeys(blockers))
    return {
        "can_promote_to_L5": not blockers,
        "blockers": blockers,
        "decision": "promote" if not blockers else "refactor_before_promote",
    }
