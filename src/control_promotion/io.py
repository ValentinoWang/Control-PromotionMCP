from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_data(path: str | Path) -> Any:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    if file_path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text) or {}


def dump_data(data: Any, fmt: str = "yaml") -> str:
    if fmt == "json":
        return json.dumps(data, indent=2, sort_keys=True) + "\n"
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def load_yaml_text(text: str) -> Any:
    return yaml.safe_load(text) or {}
