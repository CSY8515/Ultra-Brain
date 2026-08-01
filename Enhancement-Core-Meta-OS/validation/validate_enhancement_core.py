"""Dependency-free structural validator for Enhancement Core Meta OS."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md", "VERSION", "CHANGELOG.md", "ARCHITECTURE_REVIEW.md",
    "MASTER_DESIGN.md", "REQUIREMENTS.md", "enhancement_core/__init__.py",
    "enhancement_core/core.py", "enhancement_core/models.py",
    "enhancement_core/validation.py", "interfaces/enhancement_core.interface.json",
    "contracts/enhancement_core.contract.json", "schemas/analysis_request.schema.json",
    "schemas/enhancement_result.schema.json", "registry/enhancement_core_registry.json",
)
FORBIDDEN_IMPORTS = {"asyncio", "http", "requests", "socket", "subprocess", "threading", "streamlit", "tkinter"}


def load_json(path: Path):
    def reject(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject)


def validate() -> list[str]:
    errors = []
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"missing or empty: {relative}")
    if (ROOT / "VERSION").read_text(encoding="utf-8").strip() != "0.3":
        errors.append("VERSION must be 0.3")
    json_values = {}
    for path in ROOT.rglob("*.json"):
        try:
            json_values[path.relative_to(ROOT).as_posix()] = load_json(path)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    registry = json_values.get("registry/enhancement_core_registry.json", {})
    interface = json_values.get("interfaces/enhancement_core.interface.json", {})
    contract = json_values.get("contracts/enhancement_core.contract.json", {})
    if registry.get("version") != "0.3.0" or interface.get("version") != "0.3.0" or contract.get("version") != "0.3.0":
        errors.append("registry/interface/contract version mismatch")
    if interface.get("id") != registry.get("interface") or contract.get("id") != registry.get("contract"):
        errors.append("registry references do not resolve")
    if interface.get("execution_authority") is not False:
        errors.append("interface must deny execution authority")
    ids = []
    for entity in registry.get("entities", []):
        ids.append(entity.get("id"))
        relative = entity.get("path", "")
        if not relative or not (ROOT / relative).is_file():
            errors.append(f"registry path missing: {relative}")
    if len(ids) != len(set(ids)):
        errors.append("registry entity IDs must be unique")
    for path in (ROOT / "enhancement_core").glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        if imports & FORBIDDEN_IMPORTS:
            errors.append(f"{path.name}: forbidden imports {sorted(imports & FORBIDDEN_IMPORTS)}")
    forbidden_paths = {".streamlit", "automation", "connectors", "pages", "streamlit", "ui", "ux"}
    found = {path.name.lower() for path in ROOT.rglob("*") if path.is_dir()}
    if found & forbidden_paths:
        errors.append(f"forbidden product paths: {sorted(found & forbidden_paths)}")
    return errors


if __name__ == "__main__":
    findings = validate()
    if findings:
        print("Enhancement Core validation FAILED")
        for finding in findings:
            print(f"- {finding}")
        raise SystemExit(1)
    print("Enhancement Core validation PASSED")
