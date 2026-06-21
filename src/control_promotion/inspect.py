from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from control_promotion.io import load_data


CONTROL_MARKERS = {
    "root_agents": "AGENTS.md",
    "skills": ".agents/skills",
    "docs": "docs",
    "quality_guard": "scripts/quality",
    "qa_harness": "scripts/qa",
    "makefile": "Makefile",
    "harness_overlays": ".harness/overlays",
}


def inspect_project(project_root: str | Path = ".") -> dict[str, Any]:
    root = Path(project_root).resolve()
    detected_controls: list[str] = []
    detected_layers: set[str] = set()

    for control, marker in CONTROL_MARKERS.items():
        if (root / marker).exists():
            detected_controls.append(control)

    if (root / "src").exists():
        detected_layers.add("package")
    if (root / "frontend").exists() or (root / "lib").exists():
        detected_layers.add("frontend")
    if (root / "backend").exists() or (root / "api").exists():
        detected_layers.add("backend")
    if (root / "openapi").exists() or (root / "schema").exists():
        detected_layers.add("api_contract")
    if (root / "scripts" / "quality").exists():
        detected_layers.add("quality")
    if (root / "scripts" / "qa").exists():
        detected_layers.add("qa")
    if (root / ".harness").exists() or (root / "harness-engineering").exists():
        detected_layers.add("harness")

    scoped_agents = [
        str(path.relative_to(root))
        for path in root.rglob("AGENTS.md")
        if ".git" not in path.parts and path != root / "AGENTS.md"
    ]

    adapter_path = root / ".control-promotion.yaml"
    adapter: dict[str, Any] | None = None
    if adapter_path.exists():
        loaded = load_data(adapter_path)
        adapter = loaded if isinstance(loaded, dict) else None

    project_type = "generic"
    if adapter:
        types = adapter.get("project", {}).get("type", [])
        if isinstance(types, list) and types:
            project_type = "_".join(str(item) for item in types)

    return {
        "project_root": str(root),
        "project_type": project_type,
        "detected_layers": sorted(detected_layers),
        "detected_controls": detected_controls,
        "scoped_agents": scoped_agents,
        "has_adapter": adapter_path.exists(),
    }


def check_ssot_links(paths: list[str], project_root: str | Path = ".", adapter_path: str | Path | None = None) -> dict[str, Any]:
    root = Path(project_root).resolve()
    adapter: dict[str, Any] = {}
    if adapter_path:
        loaded = load_data(adapter_path)
        if isinstance(loaded, dict):
            adapter = loaded

    classifications = {
        entry.get("path"): entry.get("classification")
        for entry in adapter.get("ssot_links", [])
        if isinstance(entry, dict)
    }

    results = []
    for raw_path in paths:
        raw = Path(raw_path)
        path = raw if raw.is_absolute() else root / raw
        rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        is_link = path.is_symlink()
        target = os.readlink(path) if is_link else None
        classification = classifications.get(rel, "unclassified")
        recommendation = "repo-local overlay is preferred for project-specific rules"
        if is_link:
            recommendation = "report SSOT ownership before editing; prefer adapter or overlay for project-specific rules"
        results.append(
            {
                "path": rel,
                "exists": path.exists(),
                "is_symlink": is_link,
                "target": target,
                "classification": classification,
                "recommendation": recommendation,
            }
        )

    return {"symlinks": results}
