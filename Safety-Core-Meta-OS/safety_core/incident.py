"""Immutable incident lifecycle and containment controls."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from .common import (
    MAX_COLLECTION_ITEMS,
    canonical_timestamp,
    parse_timestamp,
    utc_now,
    validate_identifier,
    validate_unicode_string,
)
from .errors import StateTransitionError, ValidationError
from .models import Incident


SEVERITIES = frozenset({"low", "moderate", "high", "critical"})
STATUSES = frozenset({"open", "contained", "recovering", "resolved", "closed"})
ALLOWED_TRANSITIONS = {
    "open": frozenset({"contained"}),
    "contained": frozenset({"recovering", "resolved"}),
    "recovering": frozenset({"resolved"}),
    "resolved": frozenset({"closed"}),
    "closed": frozenset(),
}
HISTORY_FIELDS = {
    "revision",
    "from_status",
    "to_status",
    "at",
    "recovery_verified",
}
_PLAIN_DICT_TYPE = dict


class IncidentManager:
    """Create incidents and return new values for permitted transitions."""

    @staticmethod
    def create(
        incident_id: str,
        severity: str,
        summary: str,
        created_at: str | None = None,
    ) -> Incident:
        validate_identifier(incident_id, "incident.id")
        _validate_severity(severity)
        _validate_summary(summary)

        created_at = canonical_timestamp(
            utc_now() if created_at is None else created_at,
            "incident.created_at",
        )
        history = (
            MappingProxyType({
                "revision": 1,
                "from_status": None,
                "to_status": "open",
                "at": created_at,
                "recovery_verified": False,
            }),
        )
        return Incident(
            id=incident_id,
            severity=severity,
            status="open",
            summary=summary,
            containment_block=True,
            revision=1,
            created_at=created_at,
            updated_at=created_at,
            history=history,
        )

    @staticmethod
    def transition(
        incident: Incident,
        target_status: str,
        expected_revision: int,
        transitioned_at: str | None = None,
        recovery_verified: bool = False,
    ) -> Incident:
        incident = IncidentManager.validate(incident)
        if type(target_status) is not str or target_status not in STATUSES:
            raise StateTransitionError("incident:invalid-target-status")
        if type(expected_revision) is not int:
            raise ValidationError("incident.expected_revision:integer-required")
        if expected_revision != incident.revision:
            raise StateTransitionError("incident:stale-revision")
        if not isinstance(recovery_verified, bool):
            raise ValidationError("incident.recovery_verified:boolean-required")

        if target_status == incident.status:
            raise StateTransitionError("incident:same-state-transition")
        if target_status not in ALLOWED_TRANSITIONS[incident.status]:
            raise StateTransitionError("incident:transition-not-allowed")
        if (
            incident.severity == "critical"
            and target_status == "resolved"
            and not recovery_verified
        ):
            raise StateTransitionError("incident:critical-recovery-not-verified")

        transitioned_at = canonical_timestamp(
            utc_now() if transitioned_at is None else transitioned_at,
            "incident.transitioned_at",
        )
        if parse_timestamp(transitioned_at, "incident.transitioned_at") < parse_timestamp(
            incident.updated_at, "incident.updated_at"
        ):
            raise StateTransitionError("incident:timestamp-out-of-order")
        revision = incident.revision + 1
        history_entry = MappingProxyType({
            "revision": revision,
            "from_status": incident.status,
            "to_status": target_status,
            "at": transitioned_at,
            "recovery_verified": recovery_verified,
        })

        return Incident(
            id=incident.id,
            severity=incident.severity,
            status=target_status,
            summary=incident.summary,
            containment_block=target_status not in {"resolved", "closed"},
            revision=revision,
            created_at=incident.created_at,
            updated_at=transitioned_at,
            history=incident.history + (history_entry,),
        )

    @staticmethod
    def validate(incident: Incident) -> Incident:
        _validate_incident_fields(incident)
        history = _snapshot_history(incident.history)
        _validate_incident_history(incident, history)
        frozen_history = tuple(
            MappingProxyType(entry) for entry in history
        )
        return Incident(
            id=incident.id,
            severity=incident.severity,
            status=incident.status,
            summary=incident.summary,
            containment_block=incident.containment_block,
            revision=incident.revision,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            history=frozen_history,
        )


def _validate_severity(severity: str) -> None:
    if type(severity) is not str or severity not in SEVERITIES:
        raise ValidationError("incident.severity:invalid")


def _validate_summary(summary: str) -> None:
    if type(summary) is not str:
        raise ValidationError("incident.summary:invalid")
    if len(summary) > 500:
        raise ValidationError("incident.summary:too-long")
    validate_unicode_string(summary, "incident.summary")
    if not summary.strip():
        raise ValidationError("incident.summary:invalid")


def _snapshot_history(history: object) -> tuple[dict[str, object], ...]:
    if type(history) is not tuple or not history:
        raise ValidationError("incident.history:non-empty-tuple-required")
    if len(history) > MAX_COLLECTION_ITEMS:
        raise ValidationError("incident.history:too-many-items")

    snapshots: list[dict[str, object]] = []
    for entry in history:
        if not isinstance(entry, Mapping):
            raise ValidationError("incident.history:invalid-entry")
        snapshots.append(_snapshot_history_entry(entry))
    return tuple(snapshots)


def _snapshot_history_entry(entry: Mapping[object, object]) -> dict[str, object]:
    if type(entry) is _PLAIN_DICT_TYPE and len(entry) > len(HISTORY_FIELDS):
        raise ValidationError("incident.history:invalid-entry")

    try:
        iterator = iter(entry)
    except Exception as exc:
        raise ValidationError("incident.history:invalid-entry") from exc

    snapshot: dict[str, object] = {}
    for _index in range(len(HISTORY_FIELDS) + 1):
        try:
            key = next(iterator)
        except StopIteration:
            break
        except Exception as exc:
            raise ValidationError("incident.history:invalid-entry") from exc
        if type(key) is not str or key not in HISTORY_FIELDS or key in snapshot:
            raise ValidationError("incident.history:invalid-entry")
        try:
            snapshot[key] = entry[key]
        except Exception as exc:
            raise ValidationError("incident.history:invalid-entry") from exc

    if set(snapshot) != HISTORY_FIELDS:
        raise ValidationError("incident.history:invalid-entry")
    return snapshot


def _validate_incident_fields(incident: Incident) -> None:
    if type(incident) is not Incident:
        raise ValidationError("incident:incident-required")
    validate_identifier(incident.id, "incident.id")
    _validate_severity(incident.severity)
    _validate_summary(incident.summary)
    if type(incident.status) is not str or incident.status not in STATUSES:
        raise ValidationError("incident.status:invalid")
    if type(incident.revision) is not int:
        raise ValidationError("incident.revision:integer-required")
    if incident.revision < 1:
        raise ValidationError("incident.revision:out-of-range")
    if not isinstance(incident.containment_block, bool):
        raise ValidationError("incident.containment_block:boolean-required")
    expected_block = incident.status not in {"resolved", "closed"}
    if incident.containment_block is not expected_block:
        raise ValidationError("incident:containment-state-inconsistent")
    if canonical_timestamp(incident.created_at, "incident.created_at") != incident.created_at:
        raise ValidationError("incident.created_at:not-canonical-utc")
    if canonical_timestamp(incident.updated_at, "incident.updated_at") != incident.updated_at:
        raise ValidationError("incident.updated_at:not-canonical-utc")


def _validate_incident_history(
    incident: Incident,
    history: tuple[dict[str, object], ...],
) -> None:
    if len(history) != incident.revision:
        raise ValidationError("incident.history:revision-mismatch")

    prior_status: str | None = None
    prior_timestamp = None
    for expected_revision, entry in enumerate(history, 1):
        if not isinstance(entry, Mapping) or set(entry) != HISTORY_FIELDS:
            raise ValidationError("incident.history:invalid-entry")
        if type(entry["revision"]) is not int or entry["revision"] != expected_revision:
            raise ValidationError("incident.history:invalid-revision")
        if type(entry["recovery_verified"]) is not bool:
            raise ValidationError("incident.history:invalid-recovery-evidence")
        if type(entry["to_status"]) is not str or entry["to_status"] not in STATUSES:
            raise ValidationError("incident.history:invalid-to-status")
        if entry["from_status"] is not None and (
            type(entry["from_status"]) is not str
            or entry["from_status"] not in STATUSES
        ):
            raise ValidationError("incident.history:invalid-from-status")
        timestamp = parse_timestamp(entry["at"], "incident.history.at")
        if canonical_timestamp(entry["at"], "incident.history.at") != entry["at"]:
            raise ValidationError("incident.history:timestamp-not-canonical-utc")
        if prior_timestamp is not None and timestamp < prior_timestamp:
            raise ValidationError("incident.history:timestamp-out-of-order")
        if expected_revision == 1:
            if (
                entry["from_status"] is not None
                or entry["to_status"] != "open"
                or entry["recovery_verified"]
            ):
                raise ValidationError("incident.history:invalid-opening")
        else:
            if entry["from_status"] != prior_status:
                raise ValidationError("incident.history:broken-state-chain")
            if entry["to_status"] not in ALLOWED_TRANSITIONS.get(prior_status, set()):
                raise ValidationError("incident.history:invalid-transition")
            if (
                incident.severity == "critical"
                and entry["to_status"] == "resolved"
                and not entry["recovery_verified"]
            ):
                raise ValidationError("incident.history:critical-recovery-unverified")
        prior_status = entry["to_status"]
        prior_timestamp = timestamp

    if history[0]["at"] != incident.created_at:
        raise ValidationError("incident.history:created-at-mismatch")
    if history[-1]["at"] != incident.updated_at:
        raise ValidationError("incident.history:updated-at-mismatch")
    if prior_status != incident.status:
        raise ValidationError("incident.history:status-mismatch")
