"""Fail-closed validation for Collaboration & Connectivity Core."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .models import (
    ConnectionGrant, ConnectorSpec, CredentialReference, ExchangeRecord,
    OperationRequest,
)


IDENTIFIER = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?$")
KINDS = {"api", "platform", "external_ai", "repository", "communication", "ecosystem"}
MAX_JSON_DEPTH = 12
MAX_COLLECTION_ITEMS = 1_000
MAX_TEXT_LENGTH = 65_536


class ConnectivityError(Exception):
    """Base error with safe, stable messages."""


class ValidationError(ConnectivityError):
    pass


class AuthorizationError(ConnectivityError):
    pass


class ConnectorError(ConnectivityError):
    pass


class ConflictError(ConnectivityError):
    pass


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValidationError(f"{label}:invalid")
    return value


def parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValidationError("timestamp:utc-required")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValidationError("timestamp:invalid") from exc
    return parsed.astimezone(timezone.utc)


def _json(value: Any, *, depth: int = 0) -> Any:
    if depth > MAX_JSON_DEPTH:
        raise ValidationError("json:depth-exceeded")
    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            raise ValidationError("json:number-invalid")
        return value
    if isinstance(value, str):
        if len(value) > MAX_TEXT_LENGTH:
            raise ValidationError("json:text-too-long")
        return value
    if isinstance(value, Mapping):
        if len(value) > MAX_COLLECTION_ITEMS:
            raise ValidationError("json:object-too-large")
        clean: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 128:
                raise ValidationError("json:key-invalid")
            clean[key] = _json(item, depth=depth + 1)
        return MappingProxyType(clean)
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_COLLECTION_ITEMS:
            raise ValidationError("json:array-too-large")
        return tuple(_json(item, depth=depth + 1) for item in value)
    raise ValidationError("json:type-invalid")


def thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(item) for item in value]
    return value


def validate_payload(value: Any, max_bytes: int) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError("payload:object-required")
    clean = _json(value)
    size = len(json.dumps(thaw_json(clean), ensure_ascii=False, sort_keys=True).encode("utf-8"))
    if size > max_bytes:
        raise ValidationError("payload:size-exceeded")
    return clean


def validate_output(value: Any, max_bytes: int) -> Any:
    clean = _json(value)
    size = len(json.dumps(thaw_json(clean), ensure_ascii=False, sort_keys=True).encode("utf-8"))
    if size > max_bytes:
        raise ConnectorError("connector:output-size-exceeded")
    return clean


def validate_credential(value: CredentialReference | Mapping[str, Any]) -> CredentialReference:
    if isinstance(value, CredentialReference):
        source = value.to_dict()
    elif isinstance(value, Mapping):
        source = dict(value)
    else:
        raise ValidationError("credential:object-required")
    allowed = {"id", "provider", "scopes"}
    if set(source) != allowed:
        raise ValidationError("credential:fields-invalid")
    scopes = tuple(_identifier(item, "credential:scope") for item in source["scopes"])
    if len(set(scopes)) != len(scopes):
        raise ValidationError("credential:scope-duplicate")
    return CredentialReference(_identifier(source["id"], "credential:id"), _identifier(source["provider"], "credential:provider"), scopes)


def validate_connector(value: ConnectorSpec | Mapping[str, Any]) -> ConnectorSpec:
    source = value.to_dict() if isinstance(value, ConnectorSpec) else dict(value) if isinstance(value, Mapping) else None
    if source is None:
        raise ValidationError("connector:object-required")
    allowed = {"id", "kind", "platform", "api_version", "operations", "credential", "max_payload_bytes"}
    if set(source) != allowed:
        raise ValidationError("connector:fields-invalid")
    kind = source["kind"]
    if kind not in KINDS:
        raise ValidationError("connector:kind-invalid")
    if not isinstance(source["api_version"], str) or not VERSION.fullmatch(source["api_version"]):
        raise ValidationError("connector:version-invalid")
    operations = tuple(_identifier(item, "connector:operation") for item in source["operations"])
    if not operations or len(operations) > 64 or len(set(operations)) != len(operations):
        raise ValidationError("connector:operations-invalid")
    limit = source["max_payload_bytes"]
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1_048_576:
        raise ValidationError("connector:payload-limit-invalid")
    credential = None if source["credential"] is None else validate_credential(source["credential"])
    return ConnectorSpec(
        _identifier(source["id"], "connector:id"), kind,
        _identifier(source["platform"], "connector:platform"), source["api_version"],
        operations, credential, limit,
    )


def validate_grant(value: ConnectionGrant | Mapping[str, Any], now: datetime) -> ConnectionGrant:
    source = value.to_dict() if isinstance(value, ConnectionGrant) else dict(value) if isinstance(value, Mapping) else None
    if source is None:
        raise ValidationError("grant:object-required")
    expected = {
        "id", "approved", "safety_decision_id", "valid_from", "expires_at",
        "allowed_connectors", "allowed_operations", "max_requests", "max_records",
        "allow_external_ai", "allow_repository_write", "allow_communication",
    }
    if set(source) != expected:
        raise ValidationError("grant:fields-invalid")
    if source["approved"] is not True:
        raise AuthorizationError("grant:not-approved")
    if not isinstance(source["safety_decision_id"], str) or not source["safety_decision_id"].startswith("decision-"):
        raise AuthorizationError("grant:safety-reference-invalid")
    start, end = parse_timestamp(source["valid_from"]), parse_timestamp(source["expires_at"])
    current = now.astimezone(timezone.utc) if now.tzinfo else None
    if current is None:
        raise ValidationError("grant:now-timezone-required")
    if end <= start or current < start or current >= end:
        raise AuthorizationError("grant:not-current")
    connectors = tuple(_identifier(item, "grant:connector") for item in source["allowed_connectors"])
    operations = tuple(_identifier(item, "grant:operation") for item in source["allowed_operations"])
    if not connectors or not operations or len(set(connectors)) != len(connectors) or len(set(operations)) != len(operations):
        raise ValidationError("grant:allowlist-invalid")
    for name in ("max_requests", "max_records"):
        if not isinstance(source[name], int) or isinstance(source[name], bool) or not 1 <= source[name] <= 10_000:
            raise ValidationError(f"grant:{name}-invalid")
    for name in ("allow_external_ai", "allow_repository_write", "allow_communication"):
        if not isinstance(source[name], bool):
            raise ValidationError(f"grant:{name}-invalid")
    return ConnectionGrant(
        _identifier(source["id"], "grant:id"), True, source["safety_decision_id"],
        source["valid_from"], source["expires_at"], connectors, operations,
        source["max_requests"], source["max_records"], source["allow_external_ai"],
        source["allow_repository_write"], source["allow_communication"],
    )


def validate_request(value: OperationRequest | Mapping[str, Any], max_bytes: int) -> OperationRequest:
    source = value.to_dict() if isinstance(value, OperationRequest) else dict(value) if isinstance(value, Mapping) else None
    if source is None or set(source) != {"id", "connector_id", "operation", "payload", "idempotency_key"}:
        raise ValidationError("request:fields-invalid")
    key = source["idempotency_key"]
    if not isinstance(key, str) or len(key) > 128 or (key and not IDENTIFIER.fullmatch(key)):
        raise ValidationError("request:idempotency-key-invalid")
    return OperationRequest(
        _identifier(source["id"], "request:id"),
        _identifier(source["connector_id"], "request:connector"),
        _identifier(source["operation"], "request:operation"),
        validate_payload(source["payload"], max_bytes), key,
    )


def validate_records(values: Sequence[ExchangeRecord | Mapping[str, Any]], max_records: int) -> tuple[ExchangeRecord, ...]:
    if isinstance(values, (str, bytes)) or len(values) > max_records:
        raise ValidationError("records:count-exceeded")
    result: list[ExchangeRecord] = []
    seen: set[str] = set()
    for value in values:
        source = value.to_dict() if isinstance(value, ExchangeRecord) else dict(value) if isinstance(value, Mapping) else None
        if source is None or set(source) != {"id", "revision", "modified_at", "data", "deleted", "source"}:
            raise ValidationError("record:fields-invalid")
        record_id = _identifier(source["id"], "record:id")
        if record_id in seen:
            raise ValidationError("record:id-duplicate")
        seen.add(record_id)
        revision = source["revision"]
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
            raise ValidationError("record:revision-invalid")
        parse_timestamp(source["modified_at"])
        if not isinstance(source["deleted"], bool):
            raise ValidationError("record:deleted-invalid")
        result.append(ExchangeRecord(record_id, revision, source["modified_at"], validate_payload(source["data"], 1_048_576), source["deleted"], _identifier(source["source"], "record:source")))
    return tuple(result)
