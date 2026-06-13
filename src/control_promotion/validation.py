from __future__ import annotations

from pathlib import Path
from typing import Any

from control_promotion.io import load_data


CATALOG_REQUIRED_FIELDS = (
    "id",
    "fingerprint",
    "protected_invariant",
    "control_state",
    "routing",
    "required_proof",
    "exception_policy",
    "retirement",
)

ADAPTER_REQUIRED_TOP_LEVEL = ("version", "project", "paths", "policies")


def validate_smell_catalog(path: str | Path) -> dict[str, Any]:
    catalog = load_data(path)
    smells = catalog.get("smells")
    errors: list[str] = []

    if not isinstance(smells, list) or not smells:
        errors.append("catalog must contain a non-empty 'smells' list")
        smells = []

    seen_ids: set[str] = set()
    for index, smell in enumerate(smells):
        if not isinstance(smell, dict):
            errors.append(f"smells[{index}] must be an object")
            continue
        smell_id = str(smell.get("id", f"index-{index}"))
        if smell_id in seen_ids:
            errors.append(f"duplicate smell id: {smell_id}")
        seen_ids.add(smell_id)
        for field in CATALOG_REQUIRED_FIELDS:
            if field not in smell:
                errors.append(f"{smell_id}: missing required field '{field}'")
        if "routing" in smell and not isinstance(smell["routing"], dict):
            errors.append(f"{smell_id}: routing must be an object")
        if "required_proof" in smell and not isinstance(smell["required_proof"], list):
            errors.append(f"{smell_id}: required_proof must be a list")

    return {
        "valid": not errors,
        "errors": errors,
        "smell_count": len(smells),
    }


def validate_project_adapter(path: str | Path) -> dict[str, Any]:
    adapter = load_data(path)
    errors: list[str] = []
    warnings: list[str] = []

    for field in ADAPTER_REQUIRED_TOP_LEVEL:
        if field not in adapter:
            errors.append(f"missing required top-level field '{field}'")

    project = adapter.get("project", {})
    if not isinstance(project, dict) or not project.get("name"):
        errors.append("project.name is required")

    paths = adapter.get("paths", {})
    if not isinstance(paths, dict):
        errors.append("paths must be an object")
    else:
        for field in ("quality", "qa", "skills", "docs"):
            if field not in paths:
                warnings.append(f"paths.{field} is not configured")

    policies = adapter.get("policies", {})
    if not isinstance(policies, dict):
        errors.append("policies must be an object")
    else:
        generated = policies.get("generated_artifact", {})
        if isinstance(generated, dict) and generated.get("manual_edit") != "forbidden":
            warnings.append("policies.generated_artifact.manual_edit should usually be 'forbidden'")
        mcp_write = policies.get("mcp_write_tools", {})
        if isinstance(mcp_write, dict) and mcp_write.get("enabled") is True:
            warnings.append("MCP write tools are enabled; keep path scopes narrow")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }
