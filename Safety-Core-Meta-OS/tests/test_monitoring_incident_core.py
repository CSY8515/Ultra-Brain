from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from safety_core.audit import AuditLedger
from safety_core.core import SafetyCore
from safety_core.errors import LedgerError, StateTransitionError, ValidationError
from safety_core.incident import ALLOWED_TRANSITIONS, IncidentManager, STATUSES
from safety_core.models import Incident, Observation
from safety_core.monitoring import Monitor
from safety_core.validation import (
    load_policy,
    validate_execution_request,
    validate_observation,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policies" / "default_policy.json"


def observation(value: float):
    return validate_observation(
        {
            "id": "observation-0001",
            "metric": "validation-failures",
            "value": value,
            "warning_at": 5,
            "critical_at": 10,
            "observed_at": "2026-08-01T00:00:00Z",
        }
    )


def request():
    return validate_execution_request(
        {
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
    )


class MonitoringTests(unittest.TestCase):
    def test_threshold_boundaries(self) -> None:
        self.assertEqual(Monitor.evaluate(observation(4.9)).status, "healthy")
        self.assertEqual(Monitor.evaluate(observation(5)).status, "warning")
        self.assertEqual(Monitor.evaluate(observation(9.9)).status, "warning")
        self.assertEqual(Monitor.evaluate(observation(10)).status, "critical")

    def test_invalid_numbers_and_threshold_order_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            validate_observation(
                {
                    "id": "observation-0001",
                    "metric": "metric",
                    "value": float("nan"),
                    "warning_at": 5,
                    "critical_at": 10,
                    "observed_at": "2026-08-01T00:00:00Z",
                }
            )
        with self.assertRaises(ValidationError):
            validate_observation(
                {
                    "id": "observation-0001",
                    "metric": "metric",
                    "value": 1,
                    "warning_at": 10,
                    "critical_at": 10,
                    "observed_at": "2026-08-01T00:00:00Z",
                }
            )

    def test_huge_integer_is_rejected_as_typed_validation_failure(self) -> None:
        data = {
            "id": "observation-0001",
            "metric": "metric",
            "value": 10**10000,
            "warning_at": 5,
            "critical_at": 10,
            "observed_at": "2026-08-01T00:00:00Z",
        }
        with self.assertRaises(ValidationError):
            validate_observation(data)
        forged = Observation(
            id="observation-0001",
            metric="metric",
            value=10**10000,
            warning_at=5,
            critical_at=10,
            observed_at="2026-08-01T00:00:00Z",
        )
        with self.assertRaises(ValidationError):
            Monitor.evaluate(forged)


class IncidentTests(unittest.TestCase):
    def test_allowed_transition_path_preserves_history(self) -> None:
        manager = IncidentManager()
        incident = manager.create(
            "incident-0001",
            "high",
            "Integrity validation failed",
            "2026-08-01T00:00:00Z",
        )
        incident = manager.transition(
            incident,
            "contained",
            1,
            "2026-08-01T00:00:01Z",
        )
        incident = manager.transition(
            incident,
            "recovering",
            2,
            "2026-08-01T00:00:02Z",
        )
        incident = manager.transition(
            incident,
            "resolved",
            3,
            "2026-08-01T00:00:03Z",
        )
        incident = manager.transition(
            incident,
            "closed",
            4,
            "2026-08-01T00:00:04Z",
        )
        self.assertEqual(incident.status, "closed")
        self.assertFalse(incident.containment_block)
        self.assertEqual(incident.revision, 5)
        self.assertEqual(len(incident.history), 5)

    def test_all_disallowed_edges_and_stale_revision_fail(self) -> None:
        base = IncidentManager.create(
            "incident-0001", "low", "Bounded test incident"
        )
        for target in STATUSES - ALLOWED_TRANSITIONS["open"]:
            with self.subTest(target=target):
                with self.assertRaises(StateTransitionError):
                    IncidentManager.transition(base, target, base.revision)
        with self.assertRaises(StateTransitionError):
            IncidentManager.transition(base, "contained", 99)

    def test_critical_resolution_requires_recovery_evidence(self) -> None:
        incident = IncidentManager.create(
            "incident-0001", "critical", "Critical integrity failure"
        )
        incident = IncidentManager.transition(incident, "contained", 1)
        with self.assertRaises(StateTransitionError):
            IncidentManager.transition(incident, "resolved", 2)
        resolved = IncidentManager.transition(
            incident, "resolved", 2, recovery_verified=True
        )
        self.assertEqual(resolved.status, "resolved")

    def test_incident_history_is_immutable_and_validated(self) -> None:
        incident = IncidentManager.create(
            "incident-0001",
            "low",
            "Bounded test incident",
            "2026-08-01T00:00:00Z",
        )
        with self.assertRaises(TypeError):
            incident.history[0]["to_status"] = "closed"  # type: ignore[index]
        forged = Incident(
            id=incident.id,
            severity=incident.severity,
            status="open",
            summary=incident.summary,
            containment_block=True,
            revision=99,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            history=incident.history,
        )
        with self.assertRaises(ValidationError):
            IncidentManager.transition(forged, "contained", 99)

    def test_external_incident_history_is_copied_before_transition(self) -> None:
        history = {
            "revision": 1,
            "from_status": None,
            "to_status": "open",
            "at": "2026-08-01T00:00:00Z",
            "recovery_verified": False,
        }
        external = Incident(
            id="incident-0001",
            severity="low",
            status="open",
            summary="Caller supplied incident",
            containment_block=True,
            revision=1,
            created_at="2026-08-01T00:00:00Z",
            updated_at="2026-08-01T00:00:00Z",
            history=(history,),
        )
        transitioned = IncidentManager.transition(
            external,
            "contained",
            1,
            "2026-08-01T00:00:01Z",
        )
        history["to_status"] = "closed"
        self.assertEqual(transitioned.history[0]["to_status"], "open")
        with self.assertRaises(TypeError):
            transitioned.history[0]["to_status"] = "closed"  # type: ignore[index]

    def test_transition_timestamp_cannot_move_backward(self) -> None:
        incident = IncidentManager.create(
            "incident-0001",
            "low",
            "Bounded test incident",
            "2026-08-01T00:00:01Z",
        )
        with self.assertRaises(StateTransitionError):
            IncidentManager.transition(
                incident,
                "contained",
                1,
                "2026-08-01T00:00:00Z",
            )


class CoreTests(unittest.TestCase):
    def test_decision_and_monitoring_are_durably_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "audit.jsonl"
            core = SafetyCore(load_policy(POLICY), AuditLedger(ledger_path))
            decision = core.assess_execution(request())
            signal = core.evaluate_observation(observation(6))
            self.assertEqual(decision.status, "allow")
            self.assertIsNotNone(decision.audit_receipt)
            self.assertEqual(signal.status, "warning")
            records = core.ledger.query() if core.ledger else []
            self.assertEqual([item["event_type"] for item in records], [
                "safety-decision",
                "monitor-signal",
            ])

    def test_opening_existing_ledger_requires_external_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "audit.jsonl"
            ledger = AuditLedger(ledger_path)
            receipt = ledger.append("event-0001", "event", {})
            with self.assertRaises(LedgerError):
                SafetyCore.open(POLICY, ledger_path)
            reopened = SafetyCore.open(
                POLICY,
                ledger_path,
                expected_ledger_count=1,
                expected_ledger_head=receipt["record_hash"],
            )
            self.assertIsNotNone(reopened.ledger)

    def test_open_rejects_anchor_for_missing_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "missing.jsonl"
            with self.assertRaises(LedgerError):
                SafetyCore.open(
                    POLICY,
                    ledger_path,
                    expected_ledger_count=1,
                    expected_ledger_head="0" * 64,
                )
            self.assertFalse(ledger_path.exists())

    def test_corrupt_ledger_blocks_recorded_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "audit.jsonl"
            ledger = AuditLedger(ledger_path)
            ledger.append("event-0001", "event", {"status": "ok"})
            ledger_path.write_text("{}\n", encoding="utf-8")
            core = SafetyCore(load_policy(POLICY), ledger)
            with self.assertRaises(LedgerError):
                core.assess_execution(request())

    def test_maximum_length_source_ids_produce_bounded_audit_event_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = AuditLedger(Path(directory) / "audit.jsonl")
            core = SafetyCore(load_policy(POLICY), ledger)
            request_data = request().to_dict()
            request_data["id"] = "a" * 25 + "-" + "b" * 74
            long_request = validate_execution_request(request_data)
            long_observation = validate_observation(
                {
                    "id": "a" * 27 + "-" + "b" * 72,
                    "metric": "validation-failures",
                    "value": 1,
                    "warning_at": 5,
                    "critical_at": 10,
                    "observed_at": "2026-08-01T00:00:00Z",
                }
            )

            core.assess_execution(long_request)
            core.evaluate_observation(long_observation)

            event_ids = [record["event_id"] for record in ledger.query()]
            self.assertEqual(len(event_ids), 2)
            self.assertEqual(len(set(event_ids)), 2)
            self.assertTrue(all(len(event_id) <= 100 for event_id in event_ids))
            self.assertTrue(all("--" not in event_id for event_id in event_ids))


if __name__ == "__main__":
    unittest.main()
