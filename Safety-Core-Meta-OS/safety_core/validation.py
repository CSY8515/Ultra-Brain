"""Strict validation for Safety Core requests, policy, and observations."""

from __future__ import annotations

import math
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Any

from .common import (
    CONTRACT_VERSION,
    MAX_COLLECTION_ITEMS,
    canonical_timestamp,
    load_json_strict,
    reject_sensitive_keys,
    require_exact_fields,
    validate_filesystem_path,
    validate_identifier,
    validate_unicode_string,
)
from .errors import PolicyError, ValidationError
from .models import ExecutionRequest, Observation, SafetyPolicy


REQUEST_FIELDS = {
    "id",
    "version",
    "actor",
    "operation",
    "target",
    "permissions",
    "likelihood",
    "impact",
    "integrity_verified",
    "reversible",
    "recovery_plan_verified",
    "approved",
    "requested_at",
}

POLICY_FIELDS = {
    "id",
    "version",
    "status",
    "allowed_operations",
    "mutating_operations",
    "required_permissions",
    "integrity_required",
    "recovery_required_for",
    "approval_required_for",
    "deny_risk_levels",
    "incident_block_levels",
}

OBSERVATION_FIELDS = {
    "id",
    "metric",
    "value",
    "warning_at",
    "critical_at",
    "observed_at",
}

RISK_LEVELS = {"low", "moderate", "high", "critical"}
REQUIRED_OPERATIONS = {
    "read",
    "validate",
    "write",
    "update",
    "backup",
    "recover",
    "release",
}
REQUIRED_MUTATING_OPERATIONS = {"write", "update", "recover", "release"}
WINDOWS_RESERVED_NAMES = {
    "con",
    "conin$",
    "conout$",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}
WINDOWS_INVALID_CHARACTERS = frozenset('<>:"\\\\|?*')


def _strict_bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ValidationError(f"{label}:boolean-required")
    return value


def _bounded_int(value: Any, label: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise ValidationError(f"{label}:integer-required")
    if not minimum <= value <= maximum:
        raise ValidationError(f"{label}:out-of-range")
    return value


def _string(value: Any, label: str, maximum: int) -> str:
    if type(value) is not str:
        raise ValidationError(f"{label}:nonempty-string-required")
    if len(value) > maximum:
        raise ValidationError(f"{label}:too-long")
    validate_unicode_string(value, label)
    if not value.strip():
        raise ValidationError(f"{label}:nonempty-string-required")
    if "\x00" in value or any(ord(char) < 32 for char in value):
        raise ValidationError(f"{label}:control-character")
    return value


def validate_relative_target(value: Any, label: str = "target") -> str:
    target = _string(value, label, 500)
    if "\\" in target:
        normalized = target.replace("\\", "/")
    else:
        normalized = target
    windows = PureWindowsPath(target)
    posix = PurePosixPath(normalized)
    if windows.is_absolute() or windows.drive or posix.is_absolute():
        raise ValidationError(f"{label}:absolute-path")
    if any(character in WINDOWS_INVALID_CHARACTERS for character in target):
        raise ValidationError(f"{label}:windows-invalid-character")
    parts = posix.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValidationError(f"{label}:unsafe-path")
    for part in parts:
        if part.endswith((" ", ".")):
            raise ValidationError(f"{label}:windows-ambiguous-path")
        stem = part.split(".", 1)[0].casefold()
        if stem in WINDOWS_RESERVED_NAMES:
            raise ValidationError(f"{label}:windows-reserved-path")
    return "/".join(parts)


def _string_tuple(
    value: Any,
    label: str,
    *,
    identifiers: bool = False,
    allowed: set[str] | None = None,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValidationError(f"{label}:array-required")
    if len(value) > MAX_COLLECTION_ITEMS:
        raise ValidationError(f"{label}:too-many-items")
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        text = validate_identifier(item, item_label) if identifiers else _string(item, item_label, 100)
        if allowed is not None and text not in allowed:
            raise ValidationError(f"{item_label}:unsupported-value")
        if text in seen:
            raise ValidationError(f"{label}:duplicate-value")
        seen.add(text)
        result.append(text)
    return tuple(result)


def validate_execution_request(data: Any) -> ExecutionRequest:
    record = require_exact_fields(data, REQUEST_FIELDS, label="execution-request")
    if type(record["version"]) is not str or record["version"] != CONTRACT_VERSION:
        raise ValidationError("execution-request:unsupported-version")
    permissions = _string_tuple(record["permissions"], "permissions", identifiers=True)
    operation = validate_identifier(record["operation"], "operation")
    if operation not in REQUIRED_OPERATIONS:
        raise ValidationError("operation:unsupported-value")
    request = ExecutionRequest(
        id=validate_identifier(record["id"], "id"),
        version=CONTRACT_VERSION,
        actor=_string(record["actor"], "actor", 200),
        operation=operation,
        target=validate_relative_target(record["target"]),
        permissions=permissions,
        likelihood=_bounded_int(record["likelihood"], "likelihood", 1, 5),
        impact=_bounded_int(record["impact"], "impact", 1, 5),
        integrity_verified=_strict_bool(record["integrity_verified"], "integrity-verified"),
        reversible=_strict_bool(record["reversible"], "reversible"),
        recovery_plan_verified=_strict_bool(
            record["recovery_plan_verified"], "recovery-plan-verified"
        ),
        approved=_strict_bool(record["approved"], "approved"),
        requested_at=canonical_timestamp(record["requested_at"], "requested-at"),
    )
    reject_sensitive_keys(record, "execution-request")
    return request


def _policy_values(
    record: dict[str, Any], field: str, *, allowed: set[str] | None = None
) -> tuple[str, ...]:
    return _string_tuple(record[field], field, identifiers=True, allowed=allowed)


def validate_policy(data: Any) -> SafetyPolicy:
    try:
        record = require_exact_fields(data, POLICY_FIELDS, label="policy")
        if type(record["version"]) is not str or record["version"] != CONTRACT_VERSION:
            raise PolicyError("policy:unsupported-version")
        if type(record["status"]) is not str or record["status"] != "active":
            raise PolicyError("policy:not-active")
        policy_id = validate_identifier(record["id"], "policy-id")
        allowed_operations = _policy_values(record, "allowed_operations")
        if set(allowed_operations) != REQUIRED_OPERATIONS:
            raise PolicyError("policy:operation-set-mismatch")
        mutating = _policy_values(record, "mutating_operations")
        if set(mutating) != REQUIRED_MUTATING_OPERATIONS:
            raise PolicyError("policy:mutating-set-mismatch")
        permissions = record["required_permissions"]
        if type(permissions) is not dict:
            raise PolicyError("policy:permissions-object-required")
        if len(permissions) != len(allowed_operations):
            raise PolicyError("policy:permission-map-incomplete")
        if set(permissions) != set(allowed_operations):
            raise PolicyError("policy:permission-map-incomplete")
        permission_map: dict[str, str] = {}
        for operation, permission in permissions.items():
            validate_identifier(operation, "policy-operation")
            permission_map[operation] = validate_identifier(permission, "policy-permission")
        integrity_required = _policy_values(record, "integrity_required")
        if not REQUIRED_MUTATING_OPERATIONS <= set(integrity_required):
            raise PolicyError("policy:integrity-invariant-missing")
        recovery_required = _policy_values(
            record, "recovery_required_for", allowed=RISK_LEVELS
        )
        approval_required = _policy_values(
            record, "approval_required_for", allowed=RISK_LEVELS
        )
        denied = _policy_values(record, "deny_risk_levels", allowed=RISK_LEVELS)
        incident_block = _policy_values(
            record, "incident_block_levels", allowed=RISK_LEVELS
        )
        if not {"high", "critical"} <= set(recovery_required):
            raise PolicyError("policy:recovery-invariant-missing")
        if not {"high", "critical"} <= set(approval_required):
            raise PolicyError("policy:approval-invariant-missing")
        if "critical" not in denied:
            raise PolicyError("policy:critical-deny-invariant-missing")
        if "critical" not in incident_block:
            raise PolicyError("policy:critical-incident-invariant-missing")
    except ValidationError as exc:
        if isinstance(exc, PolicyError):
            raise
        raise PolicyError(str(exc)) from exc
    return SafetyPolicy(
        id=policy_id,
        version=CONTRACT_VERSION,
        status="active",
        allowed_operations=allowed_operations,
        mutating_operations=mutating,
        required_permissions=MappingProxyType(dict(permission_map)),
        integrity_required=integrity_required,
        recovery_required_for=recovery_required,
        approval_required_for=approval_required,
        deny_risk_levels=denied,
        incident_block_levels=incident_block,
    )


def load_policy(path: Path) -> SafetyPolicy:
    policy_path = validate_filesystem_path(path, "policy", PolicyError)
    try:
        return validate_policy(load_json_strict(policy_path))
    except PolicyError:
        raise
    except (ValidationError, OSError, ValueError, TypeError) as exc:
        raise PolicyError("policy:load-failed") from exc


def validate_observation(data: Any) -> Observation:
    record = require_exact_fields(data, OBSERVATION_FIELDS, label="observation")
    identifier = validate_identifier(record["id"], "observation-id")
    metric = _string(record["metric"], "metric", 200)
    numbers: dict[str, float] = {}
    for field in ("value", "warning_at", "critical_at"):
        value = record[field]
        if type(value) not in (int, float):
            raise ValidationError(f"{field}:number-required")
        try:
            number = float(value)
        except (OverflowError, ValueError) as exc:
            raise ValidationError(f"{field}:number-out-of-range") from exc
        if not math.isfinite(number):
            raise ValidationError(f"{field}:number-not-finite")
        numbers[field] = number
    if numbers["warning_at"] >= numbers["critical_at"]:
        raise ValidationError("observation:threshold-order")
    return Observation(
        id=identifier,
        metric=metric,
        value=numbers["value"],
        warning_at=numbers["warning_at"],
        critical_at=numbers["critical_at"],
        observed_at=canonical_timestamp(record["observed_at"], "observed-at"),
    )
