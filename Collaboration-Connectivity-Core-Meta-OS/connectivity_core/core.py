"""Governed, caller-driven Collaboration & Connectivity Core runtime."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from .models import (
    ConnectionEvent, ConnectionGrant, ConnectorSpec, ExchangeRecord, ImportResult,
    OperationRequest, OperationResult, SyncConflict, SyncResult,
)
from .validation import (
    AuthorizationError, ConflictError, ConnectorError, ValidationError,
    parse_timestamp, thaw_json, validate_connector, validate_grant,
    validate_output, validate_payload, validate_records, validate_request,
)


Transport = Callable[[OperationRequest, str | None], Any]
CredentialResolver = Callable[[str], str]
Clock = Callable[[], datetime]


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValidationError("time:timezone-required")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _contains_secret(value: Any, secret: str) -> bool:
    if isinstance(value, str):
        return secret in value
    if isinstance(value, Mapping):
        return any(_contains_secret(key, secret) or _contains_secret(item, secret) for key, item in value.items())
    if isinstance(value, (tuple, list)):
        return any(_contains_secret(item, secret) for item in value)
    return False


class ApiManager:
    """Tracks explicit per-grant request budgets; it performs no I/O."""

    def __init__(self) -> None:
        self._usage: dict[str, int] = {}

    def authorize(self, spec: ConnectorSpec, request: OperationRequest, grant: ConnectionGrant) -> None:
        if request.connector_id != spec.id or spec.id not in grant.allowed_connectors:
            raise AuthorizationError("connector:not-allowed")
        if request.operation not in spec.operations or request.operation not in grant.allowed_operations:
            raise AuthorizationError("operation:not-allowed")
        used = self._usage.get(grant.id, 0)
        if used >= grant.max_requests:
            raise AuthorizationError("grant:request-budget-exhausted")
        if spec.kind == "external_ai" and not grant.allow_external_ai:
            raise AuthorizationError("external-ai:not-allowed")
        if spec.kind == "communication" and not grant.allow_communication:
            raise AuthorizationError("communication:not-allowed")
        if spec.kind == "repository" and request.operation in {"create", "update", "delete", "push", "merge"} and not grant.allow_repository_write:
            raise AuthorizationError("repository-write:not-allowed")
        records = request.payload.get("records")
        if isinstance(records, tuple) and len(records) > grant.max_records:
            raise AuthorizationError("grant:record-budget-exceeded")

    def consume(self, grant_id: str) -> None:
        self._usage[grant_id] = self._usage.get(grant_id, 0) + 1

    def usage(self, grant_id: str) -> int:
        return self._usage.get(grant_id, 0)


class DataExchange:
    """Bounded import and export without filesystem or network access."""

    def export_records(self, records: Sequence[Mapping[str, Any]], format: str, max_records: int = 1_000) -> str:
        if isinstance(records, (str, bytes)) or len(records) > max_records:
            raise ValidationError("export:record-count-exceeded")
        clean = [thaw_json(validate_payload(item, 1_048_576)) for item in records]
        if format == "json":
            return json.dumps(clean, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if format == "jsonl":
            return "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for item in clean)
        if format == "csv":
            if not clean:
                return ""
            fields = sorted({key for item in clean for key in item})
            if any(any(isinstance(value, (dict, list)) for value in item.values()) for item in clean):
                raise ValidationError("export:csv-scalar-values-required")
            buffer = io.StringIO(newline="")
            writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(clean)
            return buffer.getvalue()
        raise ValidationError("export:format-invalid")

    def import_records(self, content: str, format: str, max_records: int = 1_000, max_bytes: int = 1_048_576) -> ImportResult:
        if not isinstance(content, str) or len(content.encode("utf-8")) > max_bytes:
            raise ValidationError("import:size-exceeded")
        try:
            if format == "json":
                raw = json.loads(content)
                if not isinstance(raw, list):
                    raise ValidationError("import:array-required")
            elif format == "jsonl":
                raw = [json.loads(line) for line in content.splitlines() if line.strip()]
            elif format == "csv":
                raw = list(csv.DictReader(io.StringIO(content)))
            else:
                raise ValidationError("import:format-invalid")
        except (json.JSONDecodeError, csv.Error) as exc:
            raise ValidationError("import:malformed") from exc
        if len(raw) > max_records:
            raise ValidationError("import:record-count-exceeded")
        accepted: list[Mapping[str, Any]] = []
        rejected = 0
        for item in raw:
            try:
                accepted.append(validate_payload(item, max_bytes))
            except ValidationError:
                rejected += 1
        return ImportResult(format, tuple(accepted), rejected)


class Synchronizer:
    """Deterministically reconciles caller-supplied record snapshots."""

    POLICIES = {"local_wins", "remote_wins", "latest", "reject"}

    def reconcile(self, local: Sequence[ExchangeRecord | Mapping[str, Any]], remote: Sequence[ExchangeRecord | Mapping[str, Any]], *, policy: str, max_records: int = 1_000) -> SyncResult:
        if policy not in self.POLICIES:
            raise ValidationError("sync:policy-invalid")
        local_records = validate_records(local, max_records)
        remote_records = validate_records(remote, max_records)
        if len(local_records) + len(remote_records) > max_records * 2:
            raise ValidationError("sync:record-count-exceeded")
        left = {item.id: item for item in local_records}
        right = {item.id: item for item in remote_records}
        merged: list[ExchangeRecord] = []
        conflicts: list[SyncConflict] = []
        for record_id in sorted(set(left) | set(right)):
            local_item, remote_item = left.get(record_id), right.get(record_id)
            if local_item is None or remote_item is None:
                merged.append(local_item or remote_item)  # type: ignore[arg-type]
                continue
            if local_item.to_dict() == remote_item.to_dict():
                merged.append(local_item)
                continue
            if local_item.revision > remote_item.revision:
                chosen, resolution = local_item, "local-newer"
            elif remote_item.revision > local_item.revision:
                chosen, resolution = remote_item, "remote-newer"
            elif policy == "local_wins":
                chosen, resolution = local_item, "local-wins"
            elif policy == "remote_wins":
                chosen, resolution = remote_item, "remote-wins"
            elif policy == "latest":
                if parse_timestamp(local_item.modified_at) == parse_timestamp(remote_item.modified_at):
                    raise ConflictError("sync:ambiguous-conflict")
                chosen = local_item if parse_timestamp(local_item.modified_at) > parse_timestamp(remote_item.modified_at) else remote_item
                resolution = "latest"
            else:
                raise ConflictError("sync:conflict")
            merged.append(chosen)
            conflicts.append(SyncConflict(record_id, resolution, local_item.revision, remote_item.revision))
        status = "conflicts-resolved" if conflicts else "synchronized"
        return SyncResult(status, tuple(merged), tuple(conflicts))


class ConnectivityCore:
    """Facade for connectors, APIs, exchange, sync, AI, repositories, and messages."""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._connectors: dict[str, tuple[ConnectorSpec, Transport]] = {}
        self._ledger: dict[tuple[str, str], tuple[str, OperationResult]] = {}
        self.api = ApiManager()
        self.exchange = DataExchange()
        self.sync = Synchronizer()

    def register_connector(self, spec: ConnectorSpec | Mapping[str, Any], transport: Transport) -> ConnectorSpec:
        clean = validate_connector(spec)
        if not callable(transport):
            raise ValidationError("connector:transport-not-callable")
        if clean.id in self._connectors:
            raise ValidationError("connector:duplicate")
        self._connectors[clean.id] = (clean, transport)
        return clean

    def invoke(self, request: OperationRequest | Mapping[str, Any], grant: ConnectionGrant | Mapping[str, Any], *, credential_resolver: CredentialResolver | None = None) -> OperationResult:
        now = self._clock()
        preliminary = request.to_dict() if isinstance(request, OperationRequest) else dict(request) if isinstance(request, Mapping) else {}
        connector_id = preliminary.get("connector_id")
        if connector_id not in self._connectors:
            raise ConnectorError("connector:not-registered")
        spec, transport = self._connectors[connector_id]
        clean_request = validate_request(request, spec.max_payload_bytes)
        clean_grant = validate_grant(grant, now)
        self.api.authorize(spec, clean_request, clean_grant)
        digest = _digest(clean_request.to_dict())
        ledger_key = (clean_grant.id, clean_request.idempotency_key)
        if clean_request.idempotency_key and ledger_key in self._ledger:
            prior_digest, prior_result = self._ledger[ledger_key]
            if prior_digest != digest:
                raise ConflictError("idempotency:key-reused")
            return prior_result

        secret: str | None = None
        if spec.credential is not None:
            if credential_resolver is None:
                raise AuthorizationError("credential:resolver-required")
            try:
                secret = credential_resolver(spec.credential.id)
            except Exception:
                raise AuthorizationError("credential:resolution-failed") from None
            if not isinstance(secret, str) or not secret:
                raise AuthorizationError("credential:unavailable")

        started = _utc_text(now)
        events = [ConnectionEvent(1, "authorized", "connector and operation allowed")]
        self.api.consume(clean_grant.id)
        try:
            raw_output = transport(clean_request, secret)
            output = validate_output(raw_output, spec.max_payload_bytes)
            if secret is not None and _contains_secret(output, secret):
                raise ConnectorError("credential:disclosure-detected")
        except ConnectorError:
            raise
        except Exception:
            finished = _utc_text(self._clock())
            events.append(ConnectionEvent(2, "failed", "connector transport failed"))
            return OperationResult(clean_request.id, spec.id, clean_request.operation, "failed", digest, None, "connector:transport-failed", started, finished, tuple(events))
        finally:
            secret = None
        finished = _utc_text(self._clock())
        events.append(ConnectionEvent(2, "completed", "connector response validated"))
        result = OperationResult(clean_request.id, spec.id, clean_request.operation, "completed", digest, output, None, started, finished, tuple(events))
        if clean_request.idempotency_key:
            self._ledger[ledger_key] = (digest, result)
        return result

    def call_external_ai(self, request: OperationRequest | Mapping[str, Any], grant: ConnectionGrant | Mapping[str, Any], **kwargs: Any) -> OperationResult:
        return self._invoke_kind("external_ai", request, grant, **kwargs)

    def access_repository(self, request: OperationRequest | Mapping[str, Any], grant: ConnectionGrant | Mapping[str, Any], **kwargs: Any) -> OperationResult:
        return self._invoke_kind("repository", request, grant, **kwargs)

    def communicate(self, request: OperationRequest | Mapping[str, Any], grant: ConnectionGrant | Mapping[str, Any], **kwargs: Any) -> OperationResult:
        return self._invoke_kind("communication", request, grant, **kwargs)

    def connect_ecosystem(self, request: OperationRequest | Mapping[str, Any], grant: ConnectionGrant | Mapping[str, Any], **kwargs: Any) -> OperationResult:
        return self._invoke_kind("ecosystem", request, grant, **kwargs)

    def _invoke_kind(self, expected: str, request: OperationRequest | Mapping[str, Any], grant: ConnectionGrant | Mapping[str, Any], **kwargs: Any) -> OperationResult:
        source = request.to_dict() if isinstance(request, OperationRequest) else request
        connector_id = source.get("connector_id") if isinstance(source, Mapping) else None
        registered = self._connectors.get(connector_id) if isinstance(connector_id, str) else None
        if registered is None or registered[0].kind != expected:
            raise ConnectorError(f"connector:kind-must-be-{expected.replace('_', '-')}")
        return self.invoke(request, grant, **kwargs)
