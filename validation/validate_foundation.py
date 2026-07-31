"""Validate the Ultra Brain v0.1 declarative foundation.

This validator intentionally uses only the Python standard library. It checks
foundation structure and contracts; it is not an operational Meta OS runtime.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/CSY8515/Ultra-Brain.git"
REGISTRY_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0.0"
MILESTONE_VERSION = "0.1"

REQUIRED_DOCUMENTS = (
    "README.md",
    "VERSION",
    "CHANGELOG.md",
    "ROADMAP.md",
    "ARCHITECTURE.md",
    "MASTER_DESIGN.md",
    "CONSTITUTION.md",
    "GOVERNANCE.md",
    "RULES.md",
    "POLICIES.md",
    "STANDARDS.md",
    "RESPONSIBILITY.md",
    "BOUNDARY.md",
    "CORE_AXIS.md",
    "REGISTRY.md",
    "DECISION_FLOW.md",
    "GOVERNANCE_LOOP.md",
    "EVOLUTION.md",
    "DEVELOPMENT_STANDARD.md",
    "REPOSITORY_STRATEGY.md",
    "VALIDATION_FRAMEWORK.md",
    "RELEASE_FRAMEWORK.md",
    "WORKSPACE_PROTECTION.md",
    "COMPLETION_RULE.md",
    "TERMINOLOGY.md",
    "DECISION_LOG.md",
    "registry/README.md",
    "schemas/README.md",
    "interfaces/README.md",
    "contracts/README.md",
    "validation/README.md",
    "tests/README.md",
    "Safety-Core-Meta-OS/README.md",
    "Enhancement-Core-Meta-OS/README.md",
    "Automation-Core-Meta-OS/README.md",
    "Collaboration-Connectivity-Core-Meta-OS/README.md",
    "Personal-Secretary-Core-Meta-OS/README.md",
)

REGISTRY_FILES = (
    "meta_os_registry.json",
    "ecosystem_registry.json",
    "capability_registry.json",
    "project_registry.json",
    "repository_registry.json",
    "rule_registry.json",
    "policy_registry.json",
    "standard_registry.json",
    "decision_registry.json",
    "release_registry.json",
    "interface_registry.json",
    "contract_registry.json",
)

SCHEMA_FILES = (
    "registry.schema.json",
    "interface.schema.json",
    "contract.schema.json",
    "decision.schema.json",
    "release.schema.json",
)

CONTAINER_FIELDS = {
    "registry_version",
    "schema_version",
    "registry_id",
    "registry_type",
    "name",
    "scope",
    "status",
    "owner_layer",
    "repository",
    "created_date",
    "updated_date",
    "entities",
}

ENTITY_FIELDS = {
    "id",
    "entity_type",
    "name",
    "scope",
    "status",
    "owner_layer",
    "parent",
    "repository",
    "path",
    "interface",
    "contract",
    "current_version",
    "created_date",
    "updated_date",
}

META_OS_IDS = {
    "safety-core-meta-os",
    "enhancement-core-meta-os",
    "automation-core-meta-os",
    "collaboration-connectivity-core-meta-os",
    "personal-secretary-core-meta-os",
}

CORE_META_OS_DIRECTORIES = (
    "Safety-Core-Meta-OS",
    "Enhancement-Core-Meta-OS",
    "Automation-Core-Meta-OS",
    "Collaboration-Connectivity-Core-Meta-OS",
    "Personal-Secretary-Core-Meta-OS",
)

ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


class DuplicateKeyError(ValueError):
    """Raised when a JSON object contains the same key more than once."""


def reject_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)


def within_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def validate_date(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{label}: date must be a string")
        return
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label}: invalid ISO date {value!r}")


def validate_required_artifacts(errors: list[str]) -> None:
    for relative in REQUIRED_DOCUMENTS:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required document: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"document is not UTF-8: {relative}")
            continue
        if not content.strip():
            errors.append(f"document is empty: {relative}")

    version_path = ROOT / "VERSION"
    if version_path.is_file() and version_path.read_text(encoding="utf-8").strip() != MILESTONE_VERSION:
        errors.append(f"VERSION must contain exactly {MILESTONE_VERSION}")


def validate_registries(errors: list[str]) -> None:
    entity_ids: set[str] = set()
    registry_ids: set[str] = set()
    loaded: dict[str, dict[str, Any]] = {}

    for filename in REGISTRY_FILES:
        path = ROOT / "registry" / filename
        if not path.is_file():
            errors.append(f"missing registry: registry/{filename}")
            continue
        try:
            data = load_json(path)
        except (json.JSONDecodeError, DuplicateKeyError) as exc:
            errors.append(f"registry/{filename}: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"registry/{filename}: root must be an object")
            continue
        loaded[filename] = data

        missing = sorted(CONTAINER_FIELDS - data.keys())
        if missing:
            errors.append(f"registry/{filename}: missing fields {', '.join(missing)}")
            continue
        if data["registry_version"] != REGISTRY_VERSION:
            errors.append(f"registry/{filename}: registry_version must be {REGISTRY_VERSION}")
        if data["schema_version"] != SCHEMA_VERSION:
            errors.append(f"registry/{filename}: schema_version must be {SCHEMA_VERSION}")
        if data["repository"] != REPOSITORY:
            errors.append(f"registry/{filename}: incorrect repository URL")
        registry_id = data["registry_id"]
        if not isinstance(registry_id, str) or not ID_PATTERN.fullmatch(registry_id):
            errors.append(f"registry/{filename}: invalid registry_id {registry_id!r}")
        elif registry_id in registry_ids:
            errors.append(f"registry/{filename}: duplicate registry_id {registry_id}")
        else:
            registry_ids.add(registry_id)
        validate_date(data["created_date"], f"registry/{filename}.created_date", errors)
        validate_date(data["updated_date"], f"registry/{filename}.updated_date", errors)

        entities = data["entities"]
        if not isinstance(entities, list):
            errors.append(f"registry/{filename}: entities must be an array")
            continue
        for index, entity in enumerate(entities):
            label = f"registry/{filename}.entities[{index}]"
            if not isinstance(entity, dict):
                errors.append(f"{label}: entity must be an object")
                continue
            missing_entity = sorted(ENTITY_FIELDS - entity.keys())
            if missing_entity:
                errors.append(f"{label}: missing fields {', '.join(missing_entity)}")
                continue
            entity_id = entity["id"]
            if not isinstance(entity_id, str) or not ID_PATTERN.fullmatch(entity_id):
                errors.append(f"{label}: invalid entity ID {entity_id!r}")
            elif entity_id in entity_ids:
                errors.append(f"{label}: duplicate global entity ID {entity_id}")
            else:
                entity_ids.add(entity_id)
            if entity["repository"] != REPOSITORY:
                errors.append(f"{label}: incorrect repository URL")
            if not isinstance(entity["current_version"], str) or not VERSION_PATTERN.fullmatch(entity["current_version"]):
                errors.append(f"{label}: invalid current_version {entity['current_version']!r}")
            if not isinstance(entity["interface"], list) or not isinstance(entity["contract"], list):
                errors.append(f"{label}: interface and contract must be arrays")
            validate_date(entity["created_date"], f"{label}.created_date", errors)
            validate_date(entity["updated_date"], f"{label}.updated_date", errors)

            relative_path = entity["path"]
            if not isinstance(relative_path, str) or not relative_path:
                errors.append(f"{label}: path must be a non-empty string")
            else:
                target = ROOT / relative_path
                if not within_root(target):
                    errors.append(f"{label}: path escapes repository root: {relative_path}")
                elif not target.exists():
                    errors.append(f"{label}: path does not exist: {relative_path}")

    meta = loaded.get("meta_os_registry.json")
    if meta:
        actual_meta_ids = {entity.get("id") for entity in meta.get("entities", []) if isinstance(entity, dict)}
        if actual_meta_ids != META_OS_IDS:
            errors.append("meta_os_registry.json must contain exactly the five Core Meta OS IDs")

    repository_registry = loaded.get("repository_registry.json")
    if repository_registry:
        repository_entities = repository_registry.get("entities", [])
        if len(repository_entities) != 1 or repository_entities[0].get("repository") != REPOSITORY:
            errors.append("repository_registry.json must contain exactly the canonical Ultra Brain repository")

    release_registry = loaded.get("release_registry.json")
    if release_registry:
        release_entities = release_registry.get("entities", [])
        if len(release_entities) != 1 or release_entities[0].get("current_version") != REGISTRY_VERSION:
            errors.append("release_registry.json must contain exactly the v0.1.0 Foundation release")


def validate_schemas(errors: list[str]) -> None:
    expected_draft = "https://json-schema.org/draft/2020-12/schema"
    for filename in SCHEMA_FILES:
        path = ROOT / "schemas" / filename
        if not path.is_file():
            errors.append(f"missing schema: schemas/{filename}")
            continue
        try:
            schema = load_json(path)
        except (json.JSONDecodeError, DuplicateKeyError) as exc:
            errors.append(f"schemas/{filename}: {exc}")
            continue
        if not isinstance(schema, dict):
            errors.append(f"schemas/{filename}: root must be an object")
            continue
        if schema.get("$schema") != expected_draft:
            errors.append(f"schemas/{filename}: must declare JSON Schema Draft 2020-12")
        if not isinstance(schema.get("$id"), str) or not schema["$id"].startswith("https://github.com/CSY8515/Ultra-Brain/"):
            errors.append(f"schemas/{filename}: invalid or missing $id")
        if schema.get("type") != "object":
            errors.append(f"schemas/{filename}: root type must be object")


def validate_markdown_links(errors: list[str]) -> None:
    excluded_roots = {ROOT / "OS Ecosystem", ROOT / ".git"}
    markdown_files = [
        path
        for path in ROOT.rglob("*.md")
        if not any(excluded == path or excluded in path.parents for excluded in excluded_roots)
    ]
    for path in markdown_files:
        content = path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_PATTERN.findall(content):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = unquote(target.split("#", 1)[0])
            resolved = path.parent / target
            if not within_root(resolved):
                errors.append(f"{path.relative_to(ROOT)}: link escapes repository: {raw_target}")
            elif not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link: {raw_target}")


def validate_scope_boundaries(errors: list[str]) -> None:
    forbidden_top_level = {"ui", "pages", "components", "styles", ".streamlit"}
    actual_top_level = {path.name.lower() for path in ROOT.iterdir() if path.name not in {".git", "OS Ecosystem"}}
    for forbidden in sorted(forbidden_top_level & actual_top_level):
        errors.append(f"forbidden v0.1 UI/runtime path exists: {forbidden}")

    for directory_name in CORE_META_OS_DIRECTORIES:
        directory = ROOT / directory_name
        if not directory.is_dir():
            errors.append(f"missing Core Meta OS directory: {directory_name}")
            continue
        files = sorted(path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file())
        if files != ["README.md"]:
            errors.append(f"{directory_name}: v0.1 permits only README.md, found {files}")
        if (directory / ".git").exists():
            errors.append(f"{directory_name}: nested Git repository is forbidden")


def main() -> int:
    errors: list[str] = []
    validate_required_artifacts(errors)
    validate_registries(errors)
    validate_schemas(errors)
    validate_markdown_links(errors)
    validate_scope_boundaries(errors)

    if errors:
        print("Ultra Brain v0.1 Foundation validation: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Ultra Brain v0.1 Foundation validation: PASSED")
    print(f"- Required documents: {len(REQUIRED_DOCUMENTS)}")
    print(f"- Registry files: {len(REGISTRY_FILES)}")
    print(f"- Schema files: {len(SCHEMA_FILES)}")
    print(f"- Core Meta OS scope directories: {len(CORE_META_OS_DIRECTORIES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
