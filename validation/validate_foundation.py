"""Validate Foundation, cumulative integrations, and the v0.91 UI release.

This validator intentionally uses only the Python standard library. It checks
Foundation structure, release integration, and delegated Core validators; it is
not an operational Meta OS runtime.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/CSY8515/Ultra-Brain.git"
OS_ECOSYSTEM_REPOSITORY = "https://github.com/CSY8515/OS-Ecosystem.git"
REGISTRY_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0.0"
MILESTONE_VERSION = "0.91"
SAFETY_VERSION = "0.2.0"
ENHANCEMENT_VERSION = "0.3.0"
AUTOMATION_VERSION = "0.4.0"
CONNECTIVITY_VERSION = "0.5.0"
SECRETARY_RUNTIME_VERSION = "0.6.0"
SECRETARY_VERSION = "0.61.0"
OS_ECOSYSTEM_VERSION = "0.73"
INTEGRATION_VERSION = "0.7.0"
UI_FOUNDATION_VERSION = "0.8.0"
UI_PREVIOUS_VERSION = "0.9.0"
UI_VERSION = "0.91.0"

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
    "Personal-Secretary-Core-Meta-OS/ARCHITECTURE_AUDIT_v0.61.md",
    "Personal-Secretary-Core-Meta-OS/OPERATIONAL_REPORTING.md",
    "OS_ECOSYSTEM_INTEGRATION.md",
    "RELEASE_NOTES_v0.7.md",
    "RELEASE_NOTES_v0.9.md",
    "RELEASE_NOTES_v0.91.md",
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
    "ecosystem_integration.schema.json",
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
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?$")
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
            if entity["repository"] not in {REPOSITORY, OS_ECOSYSTEM_REPOSITORY}:
                errors.append(f"{label}: incorrect repository URL")
            if "health" in entity and entity["health"] not in {"healthy", "degraded", "unhealthy", "unknown"}:
                errors.append(f"{label}: invalid health {entity['health']!r}")
            if not isinstance(entity["current_version"], str) or not VERSION_PATTERN.fullmatch(entity["current_version"]):
                errors.append(f"{label}: invalid current_version {entity['current_version']!r}")
            if not isinstance(entity["interface"], list) or not isinstance(entity["contract"], list):
                errors.append(f"{label}: interface and contract must be arrays")
            validate_date(entity["created_date"], f"{label}.created_date", errors)
            validate_date(entity["updated_date"], f"{label}.updated_date", errors)

            relative_path = entity["path"]
            if not isinstance(relative_path, str) or not relative_path:
                errors.append(f"{label}: path must be a non-empty string")
            elif entity["repository"] == REPOSITORY:
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
        safety_entities = [
            entity
            for entity in meta.get("entities", [])
            if isinstance(entity, dict) and entity.get("id") == "safety-core-meta-os"
        ]
        if len(safety_entities) != 1:
            errors.append("meta_os_registry.json must contain one Safety Core entity")
        else:
            safety = safety_entities[0]
            if safety.get("status") != "active" or safety.get("current_version") != SAFETY_VERSION:
                errors.append("Safety Core registry state must be active at 0.2.0")
            if safety.get("interface") != ["safety-core-control-interface"]:
                errors.append("Safety Core registry interface reference is incorrect")
            if safety.get("contract") != ["safety-core-control-contract"]:
                errors.append("Safety Core registry contract reference is incorrect")
        enhancement = next((entity for entity in meta.get("entities", []) if entity.get("id") == "enhancement-core-meta-os"), None)
        if not enhancement or enhancement.get("status") != "active" or enhancement.get("current_version") != ENHANCEMENT_VERSION:
            errors.append("Enhancement Core registry state must be active at 0.3.0")
        elif enhancement.get("interface") != ["enhancement-core-analysis-interface"] or enhancement.get("contract") != ["enhancement-core-analysis-contract"]:
            errors.append("Enhancement Core registry references are incorrect")
        automation = next((entity for entity in meta.get("entities", []) if entity.get("id") == "automation-core-meta-os"), None)
        if not automation or automation.get("status") != "active" or automation.get("current_version") != AUTOMATION_VERSION:
            errors.append("Automation Core registry state must be active at 0.4.0")
        elif automation.get("interface") != ["automation-core-execution-interface"] or automation.get("contract") != ["automation-core-execution-contract"]:
            errors.append("Automation Core registry references are incorrect")
        connectivity = next((entity for entity in meta.get("entities", []) if entity.get("id") == "collaboration-connectivity-core-meta-os"), None)
        if not connectivity or connectivity.get("status") != "active" or connectivity.get("current_version") != CONNECTIVITY_VERSION:
            errors.append("Collaboration & Connectivity Core registry state must be active at 0.5.0")
        elif connectivity.get("interface") != ["collaboration-connectivity-core-exchange-interface"] or connectivity.get("contract") != ["collaboration-connectivity-core-exchange-contract"]:
            errors.append("Collaboration & Connectivity Core registry references are incorrect")
        secretary = next((entity for entity in meta.get("entities", []) if entity.get("id") == "personal-secretary-core-meta-os"), None)
        if not secretary or secretary.get("status") != "active" or secretary.get("current_version") != SECRETARY_VERSION:
            errors.append("Personal Secretary Core registry state must be active at 0.61.0")
        elif secretary.get("interface") != ["personal-secretary-core-assistance-interface", "personal-secretary-operational-reporting-interface"] or secretary.get("contract") != ["personal-secretary-core-assistance-contract", "personal-secretary-operational-reporting-contract"]:
            errors.append("Personal Secretary Core registry references are incorrect")

    repository_registry = loaded.get("repository_registry.json")
    if repository_registry:
        repository_entities = repository_registry.get("entities", [])
        repositories = {entity.get("id"): entity.get("repository") for entity in repository_entities}
        if repositories != {"ultra-brain-repository": REPOSITORY, "os-ecosystem-repository": OS_ECOSYSTEM_REPOSITORY}:
            errors.append("repository_registry.json must contain the canonical Ultra Brain and independent OS Ecosystem repositories")

    ecosystem_registry = loaded.get("ecosystem_registry.json")
    if ecosystem_registry:
        ecosystems = ecosystem_registry.get("entities", [])
        if len(ecosystems) != 1:
            errors.append("ecosystem_registry.json must contain exactly OS Ecosystem")
        else:
            ecosystem = ecosystems[0]
            if (
                ecosystem.get("id") != "os-ecosystem"
                or ecosystem.get("current_version") != OS_ECOSYSTEM_VERSION
                or ecosystem.get("status") != "active"
                or ecosystem.get("health") != "healthy"
                or ecosystem.get("repository") != OS_ECOSYSTEM_REPOSITORY
                or ecosystem.get("interface") != ["ultra-brain-os-ecosystem-management-interface"]
                or ecosystem.get("contract") != ["ultra-brain-os-ecosystem-management-contract"]
            ):
                errors.append("OS Ecosystem registry identity, version, status, health, repository, or bindings are incorrect")

    release_registry = loaded.get("release_registry.json")
    if release_registry:
        release_entities = release_registry.get("entities", [])
        releases = {
            entity.get("id"): entity
            for entity in release_entities
            if isinstance(entity, dict)
        }
        if set(releases) != {
            "ultra-brain-v0-1-foundation",
            "ultra-brain-v0-2-safety",
            "ultra-brain-v0-3-enhancement",
            "ultra-brain-v0-4-automation",
            "ultra-brain-v0-5-collaboration-connectivity",
            "ultra-brain-v0-6-personal-secretary",
            "ultra-brain-v0-61-personal-secretary-architecture-hotfix",
            "ultra-brain-v0-7-os-ecosystem-integration",
            "ultra-brain-v0-8-official-ui-foundation",
            "ultra-brain-v0-9-official-ui-ux-final",
            "ultra-brain-v0-91-hierarchy-propagation-final",
        }:
            errors.append("release_registry.json must contain exactly v0.1 through v0.91 milestones")
        elif (
            releases["ultra-brain-v0-1-foundation"].get("current_version")
            != REGISTRY_VERSION
            or releases["ultra-brain-v0-2-safety"].get("current_version")
            != SAFETY_VERSION
            or releases["ultra-brain-v0-2-safety"].get("status") != "released"
            or releases["ultra-brain-v0-3-enhancement"].get("current_version") != ENHANCEMENT_VERSION
            or releases["ultra-brain-v0-3-enhancement"].get("status") != "released"
            or releases["ultra-brain-v0-4-automation"].get("current_version") != AUTOMATION_VERSION
            or releases["ultra-brain-v0-4-automation"].get("status") != "released"
            or releases["ultra-brain-v0-5-collaboration-connectivity"].get("current_version") != CONNECTIVITY_VERSION
            or releases["ultra-brain-v0-5-collaboration-connectivity"].get("status") != "released"
            or releases["ultra-brain-v0-6-personal-secretary"].get("current_version") != SECRETARY_RUNTIME_VERSION
            or releases["ultra-brain-v0-6-personal-secretary"].get("status") != "released"
            or releases["ultra-brain-v0-61-personal-secretary-architecture-hotfix"].get("current_version") != SECRETARY_VERSION
            or releases["ultra-brain-v0-61-personal-secretary-architecture-hotfix"].get("status") != "released"
            or releases["ultra-brain-v0-7-os-ecosystem-integration"].get("current_version") != INTEGRATION_VERSION
            or releases["ultra-brain-v0-7-os-ecosystem-integration"].get("status") != "released"
            or releases["ultra-brain-v0-8-official-ui-foundation"].get("current_version") != UI_FOUNDATION_VERSION
            or releases["ultra-brain-v0-8-official-ui-foundation"].get("status") != "released"
            or releases["ultra-brain-v0-9-official-ui-ux-final"].get("current_version") != UI_PREVIOUS_VERSION
            or releases["ultra-brain-v0-9-official-ui-ux-final"].get("status") != "released"
            or releases["ultra-brain-v0-91-hierarchy-propagation-final"].get("current_version") != UI_VERSION
            or releases["ultra-brain-v0-91-hierarchy-propagation-final"].get("status") != "released"
        ):
            errors.append("release registry versions or release states are incorrect")

    expected_entries = {
        "interface_registry.json": {
            "safety-core-control-interface": SAFETY_VERSION,
            "enhancement-core-analysis-interface": ENHANCEMENT_VERSION,
            "automation-core-execution-interface": AUTOMATION_VERSION,
            "collaboration-connectivity-core-exchange-interface": CONNECTIVITY_VERSION,
            "personal-secretary-core-assistance-interface": SECRETARY_RUNTIME_VERSION,
            "personal-secretary-operational-reporting-interface": SECRETARY_VERSION,
            "ultra-brain-os-ecosystem-management-interface": INTEGRATION_VERSION,
            "ultra-brain-ui-system-interface": UI_VERSION,
        },
        "contract_registry.json": {
            "safety-core-control-contract": SAFETY_VERSION,
            "enhancement-core-analysis-contract": ENHANCEMENT_VERSION,
            "automation-core-execution-contract": AUTOMATION_VERSION,
            "collaboration-connectivity-core-exchange-contract": CONNECTIVITY_VERSION,
            "personal-secretary-core-assistance-contract": SECRETARY_RUNTIME_VERSION,
            "personal-secretary-operational-reporting-contract": SECRETARY_VERSION,
            "ultra-brain-os-ecosystem-management-contract": INTEGRATION_VERSION,
            "ultra-brain-ui-system-contract": UI_VERSION,
        },
    }
    for filename, expected in expected_entries.items():
        registry = loaded.get(filename)
        if not registry:
            continue
        observed = {entity.get("id"): entity for entity in registry.get("entities", [])}
        if set(observed) != set(expected) or any(observed[key].get("current_version") != version or observed[key].get("status") != "active" for key, version in expected.items()):
            errors.append(f"{filename}: approved Safety/Enhancement/Automation entries are incorrect")

    decision_registry = loaded.get("decision_registry.json")
    if decision_registry:
        decision_ids = {
            entity.get("id")
            for entity in decision_registry.get("entities", [])
            if isinstance(entity, dict)
        }
        if decision_ids != {
            "decision-0001",
            "decision-0002",
            "decision-0003",
            "decision-0004",
            "decision-0005",
            "decision-0006",
            "decision-0007",
            "decision-0008",
            "decision-0009",
            "decision-0010",
        }:
            errors.append("decision_registry.json must contain decisions 0001 through 0010")

    interface_ids = {
        entity.get("id")
        for entity in loaded.get("interface_registry.json", {}).get("entities", [])
        if isinstance(entity, dict)
    }
    contract_ids = {
        entity.get("id")
        for entity in loaded.get("contract_registry.json", {}).get("entities", [])
        if isinstance(entity, dict)
    }
    for filename, registry in loaded.items():
        for index, entity in enumerate(registry.get("entities", [])):
            if not isinstance(entity, dict):
                continue
            for reference in entity.get("interface", []):
                if reference not in interface_ids:
                    errors.append(
                        f"registry/{filename}.entities[{index}]: unknown interface {reference}"
                    )
            for reference in entity.get("contract", []):
                if reference not in contract_ids:
                    errors.append(
                        f"registry/{filename}.entities[{index}]: unknown contract {reference}"
                    )


def validate_os_ecosystem_integration(errors: list[str]) -> None:
    files = {
        "integration": ROOT / "integrations" / "os_ecosystem.integration.json",
        "interface": ROOT / "interfaces" / "os_ecosystem.interface.json",
        "contract": ROOT / "contracts" / "os_ecosystem.contract.json",
        "navigation": ROOT / "navigation" / "os_ecosystem.navigation.json",
    }
    loaded: dict[str, dict[str, Any]] = {}
    for label, path in files.items():
        if not path.is_file():
            errors.append(f"missing OS Ecosystem {label}: {path.relative_to(ROOT)}")
            continue
        try:
            value = load_json(path)
        except (json.JSONDecodeError, DuplicateKeyError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path.relative_to(ROOT)}: root must be an object")
            continue
        loaded[label] = value

    if len(loaded) != len(files):
        return
    integration = loaded["integration"]
    interface = loaded["interface"]
    contract = loaded["contract"]
    navigation = loaded["navigation"]
    ecosystem = integration.get("ecosystem", {})
    management = integration.get("management", {})
    if integration.get("version") != INTEGRATION_VERSION or integration.get("status") != "active":
        errors.append("OS Ecosystem integration version or status is incorrect")
    if ecosystem != {
        "id": "os-ecosystem",
        "version": OS_ECOSYSTEM_VERSION,
        "release_tag": "v0.73",
        "repository": OS_ECOSYSTEM_REPOSITORY,
        "status": "active",
        "health": "healthy",
        "health_basis": "Reviewed v0.73 identity and required reporting contracts are coherent; this is release health, not live availability monitoring.",
    }:
        errors.append("OS Ecosystem integration identity or health evidence is incorrect")
    if any(management.get(key) is not False for key in ("source_ownership_transferred", "repository_merged", "runtime_embedded")):
        errors.append("OS Ecosystem independence flags must remain false")
    expected_dependencies = {
        ("os-ecosystem-operational-report-contract", "1.0"),
        ("personal-secretary-operational-reporting-interface", SECRETARY_VERSION),
        ("personal-secretary-operational-reporting-contract", SECRETARY_VERSION),
        ("living-os.database-management", "source-identity"),
        ("universal-learning-engine.operational-reporting", "source-identity"),
    }
    observed_dependencies = {
        (item.get("id"), item.get("version"))
        for item in integration.get("dependencies", [])
        if isinstance(item, dict) and item.get("required") is True
    }
    if observed_dependencies != expected_dependencies:
        errors.append("OS Ecosystem dependency set is incomplete or incompatible")
    if integration.get("operational_flow") != [
        "living-os-or-universal-learning-engine",
        "os-ecosystem-personal-secretary-capability",
        "ultra-brain-personal-secretary-operational-reporting",
        "ultra-brain-governed-advisory-report",
        "user",
    ]:
        errors.append("OS Ecosystem operational report flow is incorrect")
    if (
        interface.get("id") != integration.get("interface")
        or contract.get("id") != integration.get("contract")
        or interface.get("version") != INTEGRATION_VERSION
        or contract.get("version") != INTEGRATION_VERSION
        or interface.get("status") != "approved"
        or contract.get("status") != "approved"
    ):
        errors.append("OS Ecosystem Interface and Contract bindings are incoherent")
    if (
        integration.get("navigation") != "navigation/os_ecosystem.navigation.json"
        or navigation.get("managed_entity") != "os-ecosystem"
        or navigation.get("interface") != interface.get("id")
        or navigation.get("contract") != contract.get("id")
        or any(navigation.get(key) is not False for key in ("ui_implemented", "world_implemented", "theme_implemented"))
    ):
        errors.append("OS Ecosystem navigation structure violates the non-UI contract")


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
    excluded_roots = {
        ROOT / "OS Ecosystem",
        ROOT / ".git",
        ROOT / ".pnpm-store",
        ROOT / "__pycache__",
        ROOT / "ui" / "node_modules",
        ROOT / "ui" / "dist",
        ROOT / "ui" / ".next",
        ROOT / "ui" / "build",
    }
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
    forbidden_top_level = {"pages", "components", "styles", ".streamlit"}
    actual_top_level = {path.name.lower() for path in ROOT.iterdir() if path.name not in {".git", "OS Ecosystem"}}
    for forbidden in sorted(forbidden_top_level & actual_top_level):
        errors.append(f"forbidden UI/runtime path exists: {forbidden}")

    for directory_name in CORE_META_OS_DIRECTORIES:
        directory = ROOT / directory_name
        if not directory.is_dir():
            errors.append(f"missing Core Meta OS directory: {directory_name}")
            continue
        if (directory / ".git").exists():
            errors.append(f"{directory_name}: nested Git repository is forbidden")
    protected = ["Safety-Core-Meta-OS", "Enhancement-Core-Meta-OS", "Automation-Core-Meta-OS", "Collaboration-Connectivity-Core-Meta-OS", "OS Ecosystem"]
    result = subprocess.run(["git", "diff", "--exit-code", "v0.5", "--", *protected], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        errors.append("prior Core domains or OS Ecosystem differ from v0.5")


def validate_safety_core(errors: list[str]) -> None:
    validator = ROOT / "Safety-Core-Meta-OS" / "validation" / "validate_safety_core.py"
    if not validator.is_file():
        errors.append("missing Safety Core validator")
        return
    result = subprocess.run(
        [sys.executable, "-B", str(validator)],
        cwd=ROOT / "Safety-Core-Meta-OS",
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        summary = (result.stdout + result.stderr).strip()
        errors.append(f"Safety Core validation failed: {summary}")


def validate_enhancement_core(errors: list[str]) -> None:
    validator = ROOT / "Enhancement-Core-Meta-OS" / "validation" / "validate_enhancement_core.py"
    if not validator.is_file():
        errors.append("missing Enhancement Core validator")
        return
    result = subprocess.run([sys.executable, "-B", str(validator)], cwd=ROOT / "Enhancement-Core-Meta-OS", capture_output=True, text=True, check=False)
    if result.returncode != 0:
        errors.append(f"Enhancement Core validation failed: {(result.stdout + result.stderr).strip()}")


def validate_automation_core(errors: list[str]) -> None:
    test_file = ROOT / "Automation-Core-Meta-OS" / "tests" / "test_automation_core.py"
    if not test_file.is_file():
        errors.append("missing Automation Core functional tests")
        return
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_automation_core.py"],
        cwd=ROOT / "Automation-Core-Meta-OS", capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        errors.append(f"Automation Core functional regression failed: {(result.stdout + result.stderr).strip()}")
    scope = subprocess.run(
        ["git", "diff", "--exit-code", "v0.4", "--", "Automation-Core-Meta-OS"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if scope.returncode != 0:
        errors.append("Automation Core differs from the v0.4 baseline")


def validate_connectivity_core(errors: list[str]) -> None:
    test_file = ROOT / "Collaboration-Connectivity-Core-Meta-OS" / "tests" / "test_connectivity_core.py"
    if not test_file.is_file():
        errors.append("missing Collaboration & Connectivity Core functional tests")
        return
    result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_connectivity_core.py"], cwd=ROOT / "Collaboration-Connectivity-Core-Meta-OS", capture_output=True, text=True, check=False)
    if result.returncode != 0:
        errors.append(f"Collaboration & Connectivity Core functional regression failed: {(result.stdout + result.stderr).strip()}")
    scope = subprocess.run(["git", "diff", "--exit-code", "v0.5", "--", "Collaboration-Connectivity-Core-Meta-OS"], cwd=ROOT, capture_output=True, text=True, check=False)
    if scope.returncode != 0:
        errors.append("Collaboration & Connectivity Core differs from the v0.5 baseline")


def validate_personal_secretary_core(errors: list[str]) -> None:
    validator = ROOT / "Personal-Secretary-Core-Meta-OS" / "validation" / "validate_personal_secretary_core.py"
    if not validator.is_file():
        errors.append("missing Personal Secretary Core validator")
        return
    result = subprocess.run([sys.executable, "-B", str(validator)], cwd=ROOT / "Personal-Secretary-Core-Meta-OS", capture_output=True, text=True, check=False)
    if result.returncode != 0:
        errors.append(f"Personal Secretary Core validation failed: {(result.stdout + result.stderr).strip()}")


def main() -> int:
    errors: list[str] = []
    validate_required_artifacts(errors)
    validate_registries(errors)
    validate_os_ecosystem_integration(errors)
    validate_schemas(errors)
    validate_markdown_links(errors)
    validate_scope_boundaries(errors)
    validate_safety_core(errors)
    validate_enhancement_core(errors)
    validate_automation_core(errors)
    validate_connectivity_core(errors)
    validate_personal_secretary_core(errors)

    if errors:
        print("Ultra Brain v0.91 release validation: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Ultra Brain v0.91 release validation: PASSED")
    print(f"- Required documents: {len(REQUIRED_DOCUMENTS)}")
    print(f"- Registry files: {len(REGISTRY_FILES)}")
    print(f"- Schema files: {len(SCHEMA_FILES)}")
    print(f"- Core Meta OS scope directories: {len(CORE_META_OS_DIRECTORIES)}")
    print("- Active implementations: Safety Core 0.2.0, Enhancement Core 0.3.0, Automation Core 0.4.0, Collaboration & Connectivity Core 0.5.0, Personal Secretary Runtime 0.6.0")
    print("- Recovered architecture: Personal Secretary Operational Reporting 0.61.0")
    print("- Integrated ecosystem: OS Ecosystem 0.73 (active, healthy, independent)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
