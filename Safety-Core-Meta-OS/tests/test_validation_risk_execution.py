from __future__ import annotations

import copy
import unittest

from safety_core.errors import PolicyError, ValidationError
from safety_core.execution import ExecutionSafety
from safety_core.incident import IncidentManager
from safety_core.models import ExecutionRequest, SafetyPolicy
from safety_core.risk import RiskEngine
from safety_core.core import SafetyCore
from safety_core.validation import validate_execution_request, validate_policy


def request_data(**updates: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": "request-0001",
        "version": "0.2.0",
        "actor": "User",
        "operation": "read",
        "target": "Safety-Core-Meta-OS/README.md",
        "permissions": ["read"],
        "likelihood": 1,
        "impact": 1,
        "integrity_verified": True,
        "reversible": True,
        "recovery_plan_verified": False,
        "approved": False,
        "requested_at": "2026-08-01T00:00:00Z",
    }
    value.update(updates)
    return value


def policy_data() -> dict[str, object]:
    return {
        "id": "safety-core-default-policy",
        "version": "0.2.0",
        "status": "active",
        "allowed_operations": [
            "read",
            "validate",
            "write",
            "update",
            "backup",
            "recover",
            "release",
        ],
        "mutating_operations": ["write", "update", "recover", "release"],
        "required_permissions": {
            "read": "read",
            "validate": "validate",
            "write": "write",
            "update": "write",
            "backup": "backup",
            "recover": "recover",
            "release": "release",
        },
        "integrity_required": ["write", "update", "recover", "release"],
        "recovery_required_for": ["high", "critical"],
        "approval_required_for": ["high", "critical"],
        "deny_risk_levels": ["critical"],
        "incident_block_levels": ["critical"],
    }


class ValidationTests(unittest.TestCase):
    def test_valid_request_is_normalized(self) -> None:
        request = validate_execution_request(request_data())
        self.assertEqual(request.id, "request-0001")
        self.assertEqual(request.permissions, ("read",))

    def test_missing_and_unknown_fields_are_rejected(self) -> None:
        missing = request_data()
        del missing["actor"]
        with self.assertRaises(ValidationError):
            validate_execution_request(missing)
        extra = request_data(unexpected=True)
        with self.assertRaises(ValidationError):
            validate_execution_request(extra)

    def test_bool_is_not_risk_integer(self) -> None:
        with self.assertRaises(ValidationError):
            validate_execution_request(request_data(likelihood=True))

    def test_unsafe_targets_are_rejected(self) -> None:
        for target in (
            "../outside",
            "..\\outside",
            "/absolute/path",
            "C:\\outside",
            "safe/../../outside",
            "name:stream",
            "bad?.txt",
            "bad*.txt",
            'bad"name.txt',
            "bad|name.txt",
            "CONIN$.txt",
            "CONOUT$.txt",
        ):
            with self.subTest(target=target):
                with self.assertRaises(ValidationError):
                    validate_execution_request(request_data(target=target))

    def test_naive_timestamp_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            validate_execution_request(
                request_data(requested_at="2026-08-01T00:00:00")
            )

    def test_offset_timestamp_is_normalized_to_utc(self) -> None:
        request = validate_execution_request(
            request_data(requested_at="2026-08-01T09:00:00+09:00")
        )
        self.assertEqual(request.requested_at, "2026-08-01T00:00:00Z")

    def test_unknown_operation_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            validate_execution_request(request_data(operation="unknown"))

    def test_policy_requires_exact_permission_map(self) -> None:
        value = policy_data()
        permissions = copy.deepcopy(value["required_permissions"])
        assert isinstance(permissions, dict)
        del permissions["read"]
        value["required_permissions"] = permissions
        with self.assertRaises(Exception):
            validate_policy(value)

    def test_policy_cannot_remove_critical_invariants(self) -> None:
        for field in (
            "recovery_required_for",
            "approval_required_for",
            "deny_risk_levels",
            "incident_block_levels",
        ):
            with self.subTest(field=field):
                value = policy_data()
                value[field] = []
                with self.assertRaises(Exception):
                    validate_policy(value)

    def test_typed_request_is_revalidated_at_facade(self) -> None:
        core = SafetyCore(validate_policy(policy_data()))
        forged = ExecutionRequest(
            id="request-0001",
            version="9.9.9",
            actor="User",
            operation="read",
            target="C:\\outside",
            permissions=("read",),
            likelihood=1,
            impact=1,
            integrity_verified=True,
            reversible=True,
            recovery_plan_verified=False,
            approved=False,
            requested_at="2026-08-01T00:00:00Z",
        )
        with self.assertRaises(ValidationError):
            core.assess_execution(forged)


class RiskTests(unittest.TestCase):
    def test_all_matrix_values_and_thresholds(self) -> None:
        for likelihood in range(1, 6):
            previous = 0
            for impact in range(1, 6):
                result = RiskEngine.assess(likelihood, impact)
                self.assertEqual(result.score, likelihood * impact)
                self.assertGreaterEqual(result.score, previous)
                previous = result.score
                expected = (
                    "low"
                    if result.score <= 4
                    else "moderate"
                    if result.score <= 9
                    else "high"
                    if result.score <= 16
                    else "critical"
                )
                self.assertEqual(result.level, expected)

    def test_invalid_factors_are_rejected(self) -> None:
        for value in (True, 0, 6, 1.0, "1", None):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    RiskEngine.assess(value, 1)  # type: ignore[arg-type]


class ExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = validate_policy(policy_data())
        self.engine = ExecutionSafety()

    def test_validated_policy_permission_map_is_immutable(self) -> None:
        with self.assertRaises(TypeError):
            self.policy.required_permissions["read"] = "none"  # type: ignore[index]

    def test_public_engine_revalidates_forged_typed_request(self) -> None:
        forged = ExecutionRequest(
            id="request-0001",
            version="9.9.9",
            actor="User",
            operation="read",
            target="C:\\outside",
            permissions=("read",),
            likelihood=1,
            impact=1,
            integrity_verified="true",  # type: ignore[arg-type]
            reversible=True,
            recovery_plan_verified=False,
            approved=False,
            requested_at="2026-08-01T00:00:00Z",
        )
        with self.assertRaises(ValidationError):
            self.engine.evaluate(forged, self.policy)

    def test_weak_typed_policy_is_rejected_by_all_public_boundaries(self) -> None:
        weak = SafetyPolicy(
            id=self.policy.id,
            version=self.policy.version,
            status=self.policy.status,
            allowed_operations=self.policy.allowed_operations,
            mutating_operations=self.policy.mutating_operations,
            required_permissions=self.policy.required_permissions,
            integrity_required=(),
            recovery_required_for=(),
            approval_required_for=(),
            deny_risk_levels=(),
            incident_block_levels=(),
        )
        critical = validate_execution_request(
            request_data(likelihood=5, impact=5, approved=True)
        )
        with self.assertRaises(PolicyError):
            self.engine.evaluate(critical, weak)
        with self.assertRaises(PolicyError):
            SafetyCore(weak)

    def evaluate(self, **updates: object):
        return self.engine.evaluate(
            validate_execution_request(request_data(**updates)), self.policy
        )

    def test_low_risk_valid_request_is_allowed(self) -> None:
        decision = self.evaluate()
        self.assertEqual(decision.status, "allow")
        self.assertEqual(decision.reasons, ("all-controls-passed",))

    def test_missing_permission_and_integrity_deny(self) -> None:
        decision = self.evaluate(
            operation="write",
            permissions=[],
            integrity_verified=False,
            reversible=False,
        )
        self.assertEqual(decision.status, "deny")
        self.assertIn("permission-missing", decision.reasons)
        self.assertIn("integrity-required", decision.reasons)
        self.assertIn("unrecoverable-mutation", decision.reasons)

    def test_high_risk_requires_recovery_and_approval(self) -> None:
        denied = self.evaluate(likelihood=4, impact=4)
        self.assertEqual(denied.status, "deny")
        self.assertIn("recovery-required", denied.reasons)
        reviewed = self.evaluate(
            likelihood=4,
            impact=4,
            recovery_plan_verified=True,
        )
        self.assertEqual(reviewed.status, "review")
        self.assertIn("approval-required", reviewed.reasons)
        allowed = self.evaluate(
            likelihood=4,
            impact=4,
            recovery_plan_verified=True,
            approved=True,
        )
        self.assertEqual(allowed.status, "allow")

    def test_critical_risk_is_denied_even_with_approval(self) -> None:
        decision = self.evaluate(
            likelihood=5,
            impact=5,
            recovery_plan_verified=True,
            approved=True,
        )
        self.assertEqual(decision.status, "deny")
        self.assertIn("risk-denied", decision.reasons)

    def test_active_critical_incident_blocks_execution(self) -> None:
        incident = IncidentManager.create(
            "incident-0001", "critical", "Release integrity failure"
        )
        request = validate_execution_request(request_data())
        decision = self.engine.evaluate(request, self.policy, [incident])
        self.assertEqual(decision.status, "deny")
        self.assertIn("incident-containment-active", decision.reasons)


if __name__ == "__main__":
    unittest.main()
