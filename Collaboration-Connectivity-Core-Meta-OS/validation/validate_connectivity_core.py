"""Validate the isolated v0.5 Collaboration & Connectivity Core."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parent
VERSION = "0.5.0"
REQUIRED = (
    "README.md", "REQUIREMENTS.md", "ARCHITECTURE_REVIEW.md", "MASTER_DESIGN.md",
    "CHANGELOG.md", "VERSION", "connectivity_core/__init__.py",
    "connectivity_core/__main__.py", "connectivity_core/models.py",
    "connectivity_core/validation.py", "connectivity_core/core.py",
    "interfaces/connectivity_core.interface.json",
    "contracts/connectivity_core.contract.json",
    "registry/connectivity_core_registry.json",
    "schemas/connector_spec.schema.json", "schemas/connection_grant.schema.json",
    "schemas/operation_request.schema.json", "schemas/operation_result.schema.json",
    "schemas/exchange_record.schema.json", "tests/test_connectivity_core.py",
    "tests/test_artifacts_scope.py",
)
FORBIDDEN_IMPORTS = {
    "asyncio", "http", "importlib", "requests", "socket", "subprocess",
    "threading", "tkinter", "streamlit", "urllib",
}


def load_json(path: Path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def main() -> int:
    errors = []
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"missing or empty artifact: {relative}")
    if (ROOT / "VERSION").is_file() and (ROOT / "VERSION").read_text(encoding="utf-8").strip() != "0.5":
        errors.append("VERSION must be 0.5")

    json_values = {}
    for path in ROOT.rglob("*.json"):
        try:
            json_values[path.relative_to(ROOT).as_posix()] = load_json(path)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    interface = json_values.get("interfaces/connectivity_core.interface.json", {})
    contract = json_values.get("contracts/connectivity_core.contract.json", {})
    registry = json_values.get("registry/connectivity_core_registry.json", {})
    entities = registry.get("entities", [])
    if interface.get("version") != VERSION or contract.get("version") != VERSION or registry.get("version") != VERSION:
        errors.append("registry/interface/contract version mismatch")
    if registry.get("interface") != interface.get("id") or registry.get("contract") != contract.get("id"):
        errors.append("registry references do not resolve")
    entity_ids = [item.get("id") for item in entities]
    if len(entity_ids) != len(set(entity_ids)):
        errors.append("registry entity IDs must be unique")
    for entity in entities:
        if not (ROOT / entity.get("path", "")).is_file():
            errors.append(f"registry path missing: {entity.get('path')}")

    for path in (ROOT / "connectivity_core").glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        if imports & FORBIDDEN_IMPORTS:
            errors.append(f"{path.relative_to(ROOT)}: forbidden imports {sorted(imports & FORBIDDEN_IMPORTS)}")

    protected = [
        "Safety-Core-Meta-OS", "Enhancement-Core-Meta-OS",
        "Automation-Core-Meta-OS", "Personal-Secretary-Core-Meta-OS",
        "OS Ecosystem",
    ]
    result = subprocess.run(["git", "diff", "--exit-code", "v0.4", "--", *protected], cwd=REPOSITORY, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        errors.append("protected domains differ from v0.4")

    if errors:
        print("Collaboration & Connectivity Core Meta OS v0.5 validation: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Collaboration & Connectivity Core Meta OS v0.5 validation: PASSED")
    print(f"- Required artifacts: {len(REQUIRED)}")
    print(f"- JSON artifacts: {len(json_values)}")
    print("- Registered exchange boundary: coherent at 0.5.0")
    print("- Protected domains: unchanged from v0.4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
