"""Composed Safety Core façade."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from dataclasses import asdict, replace
from types import MappingProxyType
from typing import Any

from .audit import AuditLedger
from .backup import BackupManager
from .common import MAX_IDENTIFIER_LENGTH, sha256_bytes, validate_filesystem_path
from .errors import LedgerError, ValidationError
from .execution import ExecutionSafety
from .incident import IncidentManager
from .models import (
    ExecutionRequest,
    Incident,
    MonitorSignal,
    Observation,
    SafetyDecision,
    SafetyPolicy,
)
from .monitoring import Monitor
from .recovery import RecoveryManager
from .validation import (
    load_policy,
    validate_execution_request,
    validate_observation,
    validate_policy,
)


def _derived_event_id(identifier: str, suffix: str) -> str:
    candidate = f"{identifier}-{suffix}"
    if len(candidate) <= MAX_IDENTIFIER_LENGTH:
        return candidate
    digest = sha256_bytes(candidate.encode("utf-8"))
    prefix_length = MAX_IDENTIFIER_LENGTH - len(suffix) - len(digest) - 2
    prefix = identifier[:prefix_length].rstrip("-")
    return f"{prefix}-{suffix}-{digest}"


class SafetyCore:
    """Coordinate Safety controls without executing the governed action."""

    def __init__(
        self,
        policy: SafetyPolicy,
        ledger: AuditLedger | None = None,
    ) -> None:
        if ledger is not None and type(ledger) is not AuditLedger:
            raise ValidationError("ledger:audit-ledger-required")
        self.policy = validate_policy(
            policy.to_dict() if type(policy) is SafetyPolicy else policy
        )
        self.ledger = ledger
        self.execution = ExecutionSafety()
        self.monitor = Monitor()
        self.incidents = IncidentManager()

    @classmethod
    def open(
        cls,
        policy_path: Path,
        ledger_path: Path | None = None,
        *,
        expected_ledger_count: int | None = None,
        expected_ledger_head: str | None = None,
    ) -> "SafetyCore":
        policy = load_policy(policy_path)
        ledger_file = (
            validate_filesystem_path(ledger_path, "ledger", ValidationError)
            if ledger_path is not None
            else None
        )
        ledger_exists = ledger_file is not None and os.path.lexists(ledger_file)
        anchors_supplied = (
            expected_ledger_count is not None or expected_ledger_head is not None
        )
        if ledger_file is None and anchors_supplied:
            raise LedgerError("ledger:path-required-for-anchor")
        if ledger_file is not None and ledger_exists:
            if expected_ledger_count is None or expected_ledger_head is None:
                raise LedgerError("ledger:external-anchor-required")
        elif ledger_file is not None and anchors_supplied:
            raise LedgerError("ledger:anchored-ledger-missing")

        ledger = AuditLedger(ledger_file) if ledger_file is not None else None
        if ledger is not None and ledger_exists:
            ledger.verify(
                expected_count=expected_ledger_count,
                expected_head=expected_ledger_head,
            )
        return cls(policy, ledger)

    def assess_execution(
        self,
        request: ExecutionRequest | dict[str, Any],
        incidents: Iterable[Incident] = (),
    ) -> SafetyDecision:
        request_data = request.to_dict() if type(request) is ExecutionRequest else request
        validated = validate_execution_request(request_data)
        decision = self.execution.evaluate(validated, self.policy, incidents)
        if self.ledger is not None:
            receipt = self.ledger.append(
                event_id=_derived_event_id(validated.id, "decision"),
                event_type="safety-decision",
                data={
                    "request_id": validated.id,
                    "actor": validated.actor,
                    "operation": validated.operation,
                    "target": validated.target,
                    "status": decision.status,
                    "reasons": list(decision.reasons),
                    "risk_level": decision.risk.level,
                    "risk_score": decision.risk.score,
                    "policy_version": decision.policy_version,
                },
                timestamp=decision.evaluated_at,
            )
            decision = replace(
                decision,
                audit_receipt=MappingProxyType({
                    "sequence": receipt["sequence"],
                    "event_id": receipt["event_id"],
                    "record_hash": receipt["record_hash"],
                    "previous_hash": receipt["previous_hash"],
                }),
            )
        return decision

    def evaluate_observation(
        self, observation: Observation | dict[str, Any]
    ) -> MonitorSignal:
        observation_data = asdict(observation) if type(observation) is Observation else observation
        validated = validate_observation(observation_data)
        signal = self.monitor.evaluate(validated)
        if self.ledger is not None:
            self.ledger.append(
                event_id=_derived_event_id(validated.id, "signal"),
                event_type="monitor-signal",
                data=signal.to_dict(),
                timestamp=signal.evaluated_at,
            )
        return signal

    def create_backup(self, source_root: Path, archive_path: Path) -> dict[str, Any]:
        return BackupManager.create(source_root, archive_path)

    def verify_backup(self, archive_path: Path) -> dict[str, Any]:
        return BackupManager.verify(archive_path)

    def recover_backup(self, archive_path: Path, destination: Path) -> dict[str, Any]:
        return RecoveryManager.recover(archive_path, destination)
