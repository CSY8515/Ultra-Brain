"""Immutable public records for Collaboration & Connectivity Core."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from types import MappingProxyType
from typing import Any, Mapping


def frozen_map(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Copy a mapping into a read-only view."""
    return MappingProxyType(dict(value))


class Record:
    def to_dict(self) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, Mapping):
                return {key: convert(item) for key, item in value.items()}
            if isinstance(value, tuple):
                return [convert(item) for item in value]
            if is_dataclass(value):
                return {item.name: convert(getattr(value, item.name)) for item in fields(value)}
            return value
        return convert(self)


@dataclass(frozen=True, slots=True)
class CredentialReference(Record):
    id: str
    provider: str
    scopes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConnectorSpec(Record):
    id: str
    kind: str
    platform: str
    api_version: str
    operations: tuple[str, ...]
    credential: CredentialReference | None = None
    max_payload_bytes: int = 65_536


@dataclass(frozen=True, slots=True)
class ConnectionGrant(Record):
    id: str
    approved: bool
    safety_decision_id: str
    valid_from: str
    expires_at: str
    allowed_connectors: tuple[str, ...]
    allowed_operations: tuple[str, ...]
    max_requests: int
    max_records: int
    allow_external_ai: bool = False
    allow_repository_write: bool = False
    allow_communication: bool = False


@dataclass(frozen=True, slots=True)
class OperationRequest(Record):
    id: str
    connector_id: str
    operation: str
    payload: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    idempotency_key: str = ""


@dataclass(frozen=True, slots=True)
class ConnectionEvent(Record):
    sequence: int
    state: str
    detail: str


@dataclass(frozen=True, slots=True)
class OperationResult(Record):
    request_id: str
    connector_id: str
    operation: str
    status: str
    input_digest: str
    output: Any
    error: str | None
    started_at: str
    finished_at: str
    events: tuple[ConnectionEvent, ...]


@dataclass(frozen=True, slots=True)
class ExchangeRecord(Record):
    id: str
    revision: int
    modified_at: str
    data: Mapping[str, Any]
    deleted: bool = False
    source: str = "local"


@dataclass(frozen=True, slots=True)
class SyncConflict(Record):
    record_id: str
    resolution: str
    local_revision: int
    remote_revision: int


@dataclass(frozen=True, slots=True)
class SyncResult(Record):
    status: str
    records: tuple[ExchangeRecord, ...]
    conflicts: tuple[SyncConflict, ...]


@dataclass(frozen=True, slots=True)
class ImportResult(Record):
    format: str
    records: tuple[Mapping[str, Any], ...]
    rejected: int
