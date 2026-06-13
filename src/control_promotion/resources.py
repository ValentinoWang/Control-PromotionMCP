from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

from control_promotion.core.ladder import ladder_as_dict
from control_promotion.io import dump_data, load_data


STATIC_RESOURCES = {
    "control://routing-matrix": "catalogs/base-routing-matrix.yaml",
    "control://smell-rubric": "catalogs/base-smell-catalog.yaml",
    "control://proof-obligations": "catalogs/base-control-maturity-ladder.yaml",
    "control://retirement-policy": "catalogs/base-control-maturity-ladder.yaml",
    "catalog://base": "catalogs/base-smell-catalog.yaml",
    "template://smell-gate-report": "templates/smell_gate_report.md.j2",
}


def list_resource_descriptors(project_root: str | Path = ".") -> list[dict[str, str]]:
    descriptors = [
        {"uri": "control://ladder", "name": "Control maturity ladder", "mimeType": "application/yaml"},
    ]
    descriptors.extend(
        {"uri": uri, "name": uri, "mimeType": "application/yaml" if not uri.startswith("template://") else "text/markdown"}
        for uri in STATIC_RESOURCES
    )
    if (Path(project_root) / ".control-promotion.yaml").exists():
        descriptors.append({"uri": "adapter://project", "name": "Project adapter", "mimeType": "application/yaml"})
    if (Path(project_root) / "references" / "smell-catalog.yaml").exists():
        descriptors.append({"uri": "catalog://project", "name": "Project smell catalog", "mimeType": "application/yaml"})
    return descriptors


def read_resource(uri: str, project_root: str | Path = ".") -> tuple[str, str]:
    root = Path(project_root)
    if uri == "control://ladder":
        return dump_data({"levels": ladder_as_dict()}), "application/yaml"
    if uri == "adapter://project":
        return (root / ".control-promotion.yaml").read_text(encoding="utf-8"), "application/yaml"
    if uri == "catalog://project":
        return (root / "references" / "smell-catalog.yaml").read_text(encoding="utf-8"), "application/yaml"
    if uri in STATIC_RESOURCES:
        package_root = resources.files("control_promotion")
        content = (package_root / STATIC_RESOURCES[uri]).read_text(encoding="utf-8")
        mime = "text/markdown" if uri.startswith("template://") else "application/yaml"
        return content, mime
    raise KeyError(f"unknown resource URI: {uri}")
