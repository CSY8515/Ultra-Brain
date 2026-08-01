"""Immutable public records used by the Safety Core controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from collections.abc import Mapping
from typing import Any


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    score: int
    level: str
    likelihood: int
    impact: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    id: str
    version: str
    actor: str
    operation: str
    target: str
    permissions: tuple[str, ...]
    likelihood: int
    impact: int
    integrity_verified: bool
    reversible: bool
    recovery_plan_verified: bool
    approved: bool
    requested_at: str

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["permissions"] = list(self.permissions)
        return result


@dataclass(frozen=True, slots=True)
class SafetyPolicy:
    id: str
    version: str
    status: str
    allowed_operations: tuple[str, ...]
    mutating_operations: tuple[str, ...]
    required_permissions: Mapping[str, str]
    integrity_required: tuple[str, ...]
    recovery_required_for: tuple[str, ...]
    approval_required_for: tuple[str, ...]
    deny_risk_levels: tuple[str, ...]
    incident_block_levels: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "status": self.status,
            "allowed_operations": list(self.allowed_operations),
            "mutating_operations": list(self.mutating_operations),
            "required_permissions": dict(self.required_permissions),
            "integrity_required": list(self.integrity_required),
            "recovery_required_for": list(self.recovery_required_for),
            "approval_required_for": list(self.approval_required_for),
            "deny_risk_levels": list(self.deny_risk_levels),
            "incident_block_levels": list(self.incident_block_levels),
        }


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    request_id: str
    status: str
    reasons: tuple[str, ...]
    risk: RiskAssessment
    policy_version: str
    evaluated_at: str
    audit_receipt: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status,
            "reasons": list(self.reasons),
            "risk": self.risk.to_dict(),
            "policy_version": self.policy_version,
            "evaluated_at": self.evaluated_at,
            "audit_receipt": (
                dict(self.audit_receipt) if self.audit_receipt is not None else None
            ),
        }


@dataclass(frozen=True, slots=True)
class Observation:
    id: str
    metric: str
    value: float
    warning_at: float
    critical_at: float
    observed_at: str


@dataclass(frozen=True, slots=True)
class MonitorSignal:
    observation_id: str
    status: str
    reason: str
    evaluated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Incident:
    id: str
    severity: str
    status: str
    summary: str
    containment_block: bool
    revision: int
    created_at: str
    updated_at: str
    history: tuple[Mapping[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "status": self.status,
            "summary": self.summary,
            "containment_block": self.containment_block,
            "revision": self.revision,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "history": [dict(item) for item in self.history],
        }
