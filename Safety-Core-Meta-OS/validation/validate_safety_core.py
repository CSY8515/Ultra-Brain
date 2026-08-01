"""Validate the Ultra Brain v0.2 Safety Core Meta OS artifacts."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from safety_core.common import (  # noqa: E402
    CONTRACT_VERSION,
    DuplicateKeyError,
    ID_PATTERN,
    reject_duplicate_keys,
)
from safety_core.validation import load_policy  # noqa: E402


REPOSITORY = "https://github.com/CSY8515/Ultra-Brain.git"
REQUIRED_FILES = (
    "README.md",
    "VERSION",
    "CHANGELOG.md",
    "ARCHITECTURE_REVIEW.md",
    "MASTER_DESIGN.md",
    "ARCHITECTURE.md",
    "REQUIREMENTS.md",
    "THREAT_MODEL.md",
    "registry/safety_core_registry.json",
    "interfaces/safety_core.interface.json",
    "contracts/safety_core.contract.json",
    "policies/default_policy.json",
    "schemas/execution_request.schema.json",
    "schemas/safety_decision.schema.json",
    "schemas/audit_record.schema.json",
    "schemas/incident.schema.json",
    "schemas/backup_manifest.schema.json",
    "schemas/observation.schema.json",
    "safety_core/__init__.py",
    "safety_core/__main__.py",
    "safety_core/errors.py",
    "safety_core/common.py",
    "safety_core/models.py",
    "safety_core/validation.py",
    "safety_core/integrity.py",
    "safety_core/risk.py",
    "safety_core/monitoring.py",
    "safety_core/audit.py",
    "safety_core/backup.py",
    "safety_core/recovery.py",
    "safety_core/execution.py",
    "safety_core/incident.py",
    "safety_core/core.py",
    "safety_core/cli.py",
    "validation/README.md",
    "validation/validate_safety_core.py",
    "tests/README.md",
    "tests/test_validation_risk_execution.py",
    "tests/test_integrity_audit.py",
    "tests/test_backup_recovery.py",
    "tests/test_monitoring_incident_core.py",
    "tests/test_artifacts_scope.py",
    "tests/test_contract_schema_hardening.py",
    "tests/test_public_boundaries.py",
    "tests/test_audit_adversarial.py",
    "tests/test_integrity_resource_limits.py",
    "tests/test_audit_resource_boundaries.py",
    "tests/test_input_resource_boundaries.py",
)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(rb"sk-[A-Za-z0-9]{20,}"),
)
FORBIDDEN_IMPORTS = {
    "django",
    "fastapi",
    "flask",
    "http.client",
    "requests",
    "selenium",
    "socket",
    "streamlit",
    "subprocess",
    "tkinter",
    "urllib.request",
}
INCIDENT_STATUSES = {
    "open",
    "contained",
    "recovering",
    "resolved",
    "closed",
}
INCIDENT_HISTORY_FIELDS = {
    "revision",
    "from_status",
    "to_status",
    "at",
    "recovery_verified",
}
AUDIT_RECEIPT_FIELDS = {
    "sequence",
    "event_id",
    "record_hash",
    "previous_hash",
}
SCHEMA_ID_PATTERN = "^[a-z0-9]+(?:-[a-z0-9]+)*$"
SCHEMA_HASH_PATTERN = "^[a-f0-9]{64}$"
SCHEMA_IDENTIFIER_MAX_LENGTH = 100
SCHEMA_PERMISSION_MAX_ITEMS = 64
SCHEMA_INCIDENT_HISTORY_MAX_ITEMS = 64


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"invalid numeric constant {value}")
        ),
    )


def within_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def validate_required_files(errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
        elif not path.read_bytes().strip():
            errors.append(f"empty required file: {relative}")
    version = ROOT / "VERSION"
    if version.is_file() and version.read_text(encoding="utf-8").strip() != "0.2":
        errors.append("VERSION must contain exactly 0.2")


def validate_json_artifacts(errors: list[str]) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for path in sorted(ROOT.rglob("*.json")):
        relative = path.relative_to(ROOT).as_posix()
        try:
            loaded[relative] = load_json(path)
        except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
            errors.append(f"{relative}: {exc}")
    return loaded


def validate_registry(loaded: dict[str, Any], errors: list[str]) -> None:
    relative = "registry/safety_core_registry.json"
    registry = loaded.get(relative)
    if not isinstance(registry, dict):
        errors.append(f"{relative}: object required")
        return
    required = {
        "registry_version",
        "schema_version",
        "registry_id",
        "registry_type",
        "name",
        "scope",
        "status",
        "owner_layer",
        "parent",
        "repository",
        "interface",
        "contract",
        "created_date",
        "updated_date",
        "entities",
    }
    if set(registry) != required:
        errors.append(f"{relative}: fields do not match contract")
        return
    if registry["registry_version"] != CONTRACT_VERSION or registry["schema_version"] != CONTRACT_VERSION:
        errors.append(f"{relative}: version mismatch")
    if registry["repository"] != REPOSITORY:
        errors.append(f"{relative}: repository mismatch")
    if registry["interface"] != "safety-core-control-interface":
        errors.append(f"{relative}: interface mismatch")
    if registry["contract"] != "safety-core-control-contract":
        errors.append(f"{relative}: contract mismatch")
    entities = registry["entities"]
    if not isinstance(entities, list) or len(entities) != 10:
        errors.append(f"{relative}: exactly ten controls required")
        return
    ids: set[str] = set()
    orders: set[int] = set()
    for index, entity in enumerate(entities):
        label = f"{relative}.entities[{index}]"
        if not isinstance(entity, dict) or set(entity) != {
            "id",
            "name",
            "responsibility",
            "status",
            "path",
            "required",
            "order",
        }:
            errors.append(f"{label}: fields do not match contract")
            continue
        entity_id = entity["id"]
        if not isinstance(entity_id, str) or not ID_PATTERN.fullmatch(entity_id):
            errors.append(f"{label}: invalid id")
        elif entity_id in ids:
            errors.append(f"{label}: duplicate id")
        ids.add(entity_id)
        if type(entity["order"]) is not int or entity["order"] in orders:
            errors.append(f"{label}: invalid or duplicate order")
        orders.add(entity["order"])
        if entity["status"] != "active" or type(entity["required"]) is not bool:
            errors.append(f"{label}: invalid lifecycle fields")
        path = ROOT / str(entity["path"])
        if not within_root(path) or not path.is_file():
            errors.append(f"{label}: unresolved path")


def validate_contracts(loaded: dict[str, Any], errors: list[str]) -> None:
    interface = loaded.get("interfaces/safety_core.interface.json")
    contract = loaded.get("contracts/safety_core.contract.json")
    if not isinstance(interface, dict) or interface.get("id") != "safety-core-control-interface":
        errors.append("interface identity mismatch")
    elif interface.get("version") != CONTRACT_VERSION or interface.get("status") != "approved":
        errors.append("interface version or status mismatch")
    if not isinstance(contract, dict) or contract.get("id") != "safety-core-control-contract":
        errors.append("contract identity mismatch")
    elif contract.get("version") != CONTRACT_VERSION or contract.get("status") != "approved":
        errors.append("contract version or status mismatch")
    try:
        load_policy(ROOT / "policies" / "default_policy.json")
    except Exception as exc:
        errors.append(f"default policy invalid: {exc}")


def _exact_object_schema(value: Any, fields: set[str]) -> bool:
    if not isinstance(value, dict):
        return False
    required = value.get("required")
    properties = value.get("properties")
    return (
        value.get("type") == "object"
        and value.get("additionalProperties") is False
        and isinstance(required, list)
        and all(isinstance(field, str) for field in required)
        and len(required) == len(fields)
        and set(required) == fields
        and isinstance(properties, dict)
        and set(properties) == fields
    )


def _enum_matches(value: Any, expected: set[Any]) -> bool:
    if not isinstance(value, list) or len(value) != len(expected):
        return False
    try:
        return set(value) == expected
    except TypeError:
        return False


def _validate_incident_history_schema(
    loaded: dict[str, Any], errors: list[str]
) -> None:
    relative = "schemas/incident.schema.json"
    schema = loaded.get(relative)
    if not isinstance(schema, dict):
        return
    properties = schema.get("properties")
    history = properties.get("history") if isinstance(properties, dict) else None
    items = history.get("items") if isinstance(history, dict) else None
    if not (
        isinstance(history, dict)
        and history.get("type") == "array"
        and history.get("minItems") == 1
        and _exact_object_schema(items, INCIDENT_HISTORY_FIELDS)
    ):
        errors.append(f"{relative}: history items must define the exact runtime record")
        return
    if history.get("maxItems") != SCHEMA_INCIDENT_HISTORY_MAX_ITEMS:
        errors.append(
            f"{relative}: history maxItems must be "
            f"{SCHEMA_INCIDENT_HISTORY_MAX_ITEMS}"
        )

    item_properties = items["properties"]
    revision = item_properties["revision"]
    from_status = item_properties["from_status"]
    to_status = item_properties["to_status"]
    at = item_properties["at"]
    recovery_verified = item_properties["recovery_verified"]
    valid = (
        isinstance(revision, dict)
        and revision.get("type") == "integer"
        and revision.get("minimum") == 1
        and isinstance(from_status, dict)
        and _enum_matches(from_status.get("type"), {"string", "null"})
        and _enum_matches(from_status.get("enum"), INCIDENT_STATUSES | {None})
        and isinstance(to_status, dict)
        and _enum_matches(to_status.get("enum"), INCIDENT_STATUSES)
        and isinstance(at, dict)
        and at.get("type") == "string"
        and at.get("format") == "date-time"
        and isinstance(recovery_verified, dict)
        and recovery_verified.get("type") == "boolean"
    )
    if not valid:
        errors.append(f"{relative}: history field constraints do not match runtime")


def _validate_audit_receipt_schema(
    loaded: dict[str, Any], errors: list[str]
) -> None:
    relative = "schemas/safety_decision.schema.json"
    schema = loaded.get(relative)
    if not isinstance(schema, dict):
        return
    properties = schema.get("properties")
    receipt = properties.get("audit_receipt") if isinstance(properties, dict) else None
    alternatives = receipt.get("oneOf") if isinstance(receipt, dict) else None
    if not isinstance(alternatives, list) or len(alternatives) != 2:
        errors.append(f"{relative}: audit_receipt must be null or an exact receipt")
        return
    null_schemas = [
        item for item in alternatives if isinstance(item, dict) and item.get("type") == "null"
    ]
    object_schemas = [
        item
        for item in alternatives
        if _exact_object_schema(item, AUDIT_RECEIPT_FIELDS)
    ]
    if len(null_schemas) != 1 or len(object_schemas) != 1:
        errors.append(f"{relative}: audit_receipt must be null or an exact receipt")
        return

    receipt_properties = object_schemas[0]["properties"]
    sequence = receipt_properties["sequence"]
    event_id = receipt_properties["event_id"]
    record_hash = receipt_properties["record_hash"]
    previous_hash = receipt_properties["previous_hash"]
    valid = (
        isinstance(sequence, dict)
        and sequence.get("type") == "integer"
        and sequence.get("minimum") == 1
        and isinstance(event_id, dict)
        and event_id.get("type") == "string"
        and event_id.get("pattern") == SCHEMA_ID_PATTERN
        and isinstance(record_hash, dict)
        and record_hash.get("type") == "string"
        and record_hash.get("pattern") == SCHEMA_HASH_PATTERN
        and isinstance(previous_hash, dict)
        and previous_hash.get("type") == "string"
        and previous_hash.get("pattern") == SCHEMA_HASH_PATTERN
    )
    if not valid:
        errors.append(f"{relative}: audit receipt field constraints do not match runtime")


def _schema_nodes(
    value: Any,
    location: str = "$",
) -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        yield location, value
        for key, item in value.items():
            yield from _schema_nodes(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _schema_nodes(item, f"{location}[{index}]")


def _validate_schema_resource_limits(
    loaded: dict[str, Any], errors: list[str]
) -> None:
    for relative, schema in loaded.items():
        if not relative.startswith("schemas/") or not isinstance(schema, dict):
            continue
        for location, node in _schema_nodes(schema):
            if (
                node.get("pattern") == SCHEMA_ID_PATTERN
                and node.get("maxLength") != SCHEMA_IDENTIFIER_MAX_LENGTH
            ):
                errors.append(
                    f"{relative}:{location}: identifier maxLength must be "
                    f"{SCHEMA_IDENTIFIER_MAX_LENGTH}"
                )

    relative = "schemas/execution_request.schema.json"
    request_schema = loaded.get(relative)
    properties = (
        request_schema.get("properties")
        if isinstance(request_schema, dict)
        else None
    )
    permissions = (
        properties.get("permissions") if isinstance(properties, dict) else None
    )
    if isinstance(request_schema, dict) and not (
        isinstance(permissions, dict)
        and permissions.get("type") == "array"
        and permissions.get("maxItems") == SCHEMA_PERMISSION_MAX_ITEMS
    ):
        errors.append(
            f"{relative}: permissions maxItems must be {SCHEMA_PERMISSION_MAX_ITEMS}"
        )


def validate_schemas(loaded: dict[str, Any], errors: list[str]) -> None:
    for relative, value in loaded.items():
        if not relative.startswith("schemas/"):
            continue
        if not isinstance(value, dict):
            errors.append(f"{relative}: schema object required")
            continue
        if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{relative}: wrong JSON Schema draft")
        if not str(value.get("$id", "")).startswith(
            "https://github.com/CSY8515/Ultra-Brain/Safety-Core-Meta-OS/"
        ):
            errors.append(f"{relative}: wrong schema id")
        if value.get("type") != "object":
            errors.append(f"{relative}: object root required")
    _validate_incident_history_schema(loaded, errors)
    _validate_audit_receipt_schema(loaded, errors)
    _validate_schema_resource_limits(loaded, errors)


def validate_markdown_links(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_PATTERN.findall(content):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = unquote(target.split("#", 1)[0])
            resolved = path.parent / target
            if not within_root(resolved):
                errors.append(f"{path.relative_to(ROOT)}: link escapes Safety root")
            elif not resolved.exists():
                errors.append(
                    f"{path.relative_to(ROOT)}: broken local link: {raw_target}"
                )


def _import_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Import):
        return node.names[0].name
    if isinstance(node, ast.ImportFrom):
        return node.module
    return None


def validate_python(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=relative)
            compile(tree, relative, "exec")
        except (UnicodeDecodeError, SyntaxError) as exc:
            errors.append(f"{relative}: {exc}")
            continue
        for node in ast.walk(tree):
            name = _import_name(node)
            if name and any(name == item or name.startswith(item + ".") for item in FORBIDDEN_IMPORTS):
                errors.append(f"{relative}: prohibited import {name}")


def validate_protection(errors: list[str]) -> None:
    for path in ROOT.rglob("*"):
        if path.name == ".git":
            errors.append("nested Git repository is forbidden")
        if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}:
            errors.append(f"generated Python cache present: {path.relative_to(ROOT)}")
        if path.is_symlink():
            errors.append(f"symlink present in release artifacts: {path.relative_to(ROOT)}")
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        content = path.read_bytes()
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                errors.append(f"possible secret signature: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    validate_required_files(errors)
    loaded = validate_json_artifacts(errors)
    validate_registry(loaded, errors)
    validate_contracts(loaded, errors)
    validate_schemas(loaded, errors)
    validate_markdown_links(errors)
    validate_python(errors)
    validate_protection(errors)
    if errors:
        print("Ultra Brain v0.2 Safety Core validation: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Ultra Brain v0.2 Safety Core validation: PASSED")
    print(f"- Required files: {len(REQUIRED_FILES)}")
    print(f"- JSON artifacts: {len(loaded)}")
    print("- Registered controls: 10")
    print("- Contract version: 0.2.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
