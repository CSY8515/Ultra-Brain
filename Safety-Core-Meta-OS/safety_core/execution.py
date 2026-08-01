"""Fail-closed execution-safety decision engine."""

from __future__ import annotations

from collections.abc import Iterable

from .common import MAX_COLLECTION_ITEMS, utc_now
from .errors import ValidationError
from .incident import IncidentManager
from .models import ExecutionRequest, Incident, SafetyDecision, SafetyPolicy
from .risk import RiskEngine
from .validation import validate_execution_request, validate_policy


class ExecutionSafety:
    """Evaluate safety gates without performing the governed operation."""

    def __init__(self) -> None:
        self._risk_engine = RiskEngine()

    def evaluate(
        self,
        request: ExecutionRequest,
        policy: SafetyPolicy,
        incidents: Iterable[Incident] = (),
    ) -> SafetyDecision:
        request = validate_execution_request(
            request.to_dict() if type(request) is ExecutionRequest else request
        )
        policy = validate_policy(
            policy.to_dict() if type(policy) is SafetyPolicy else policy
        )
        risk = self._risk_engine.assess(request.likelihood, request.impact)
        deny: list[str] = []
        review: list[str] = []

        try:
            incident_iterator = iter(incidents)
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError("incidents:iterable-required") from exc
        validated_incidents: list[Incident] = []
        index = 0
        while True:
            try:
                incident = next(incident_iterator)
            except StopIteration:
                break
            except ValidationError:
                raise
            except Exception as exc:
                raise ValidationError("incidents:iteration-failed") from exc
            if index >= MAX_COLLECTION_ITEMS:
                raise ValidationError("incidents:too-many-items")
            validated_incidents.append(IncidentManager.validate(incident))
            index += 1

        if request.operation not in policy.allowed_operations:
            deny.append("operation-not-allowed")
        else:
            required_permission = policy.required_permissions.get(request.operation)
            if required_permission is None or required_permission not in request.permissions:
                deny.append("permission-missing")

        if (
            request.operation in policy.integrity_required
            and not request.integrity_verified
        ):
            deny.append("integrity-required")

        risk_denied = risk.level in policy.deny_risk_levels
        if risk_denied:
            deny.append("risk-denied")

        for incident in validated_incidents:
            active = incident.status not in {"resolved", "closed"}
            severity_blocks = incident.severity in policy.incident_block_levels
            if active and (incident.containment_block or severity_blocks):
                deny.append("incident-containment-active")
                break

        if request.operation in policy.mutating_operations:
            if not request.reversible and not request.recovery_plan_verified:
                deny.append("unrecoverable-mutation")

        if (
            risk.level in policy.recovery_required_for
            and not request.recovery_plan_verified
        ):
            deny.append("recovery-required")

        if (
            not risk_denied
            and risk.level in policy.approval_required_for
            and not request.approved
        ):
            review.append("approval-required")

        if deny:
            status = "deny"
            reasons = tuple(dict.fromkeys(deny + review))
        elif review:
            status = "review"
            reasons = tuple(dict.fromkeys(review))
        else:
            status = "allow"
            reasons = ("all-controls-passed",)

        return SafetyDecision(
            request_id=request.id,
            status=status,
            reasons=reasons,
            risk=risk,
            policy_version=policy.version,
            evaluated_at=utc_now(),
            audit_receipt=None,
        )
