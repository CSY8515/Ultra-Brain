from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any

from safety_core.execution import ExecutionSafety
from safety_core.incident import IncidentManager
from safety_core.validation import load_policy, validate_execution_request
from validation.validate_safety_core import validate_schemas


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def request_data() -> dict[str, object]:
    return {
        "id": "request-gate-order",
        "version": "0.2.0",
        "actor": "User",
        "operation": "write",
        "target": "Safety-Core-Meta-OS/README.md",
        "permissions": [],
        "likelihood": 4,
        "impact": 4,
        "integrity_verified": False,
        "reversible": False,
        "recovery_plan_verified": False,
        "approved": False,
        "requested_at": "2026-08-01T00:00:00Z",
    }


class ContractSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loaded = {
            f"schemas/{path.name}": load_json(f"schemas/{path.name}")
            for path in sorted((ROOT / "schemas").glob("*.json"))
        }

    def test_nested_contract_schemas_match_runtime_shapes(self) -> None:
        errors: list[str] = []
        validate_schemas(self.loaded, errors)
        self.assertEqual(errors, [])

        incident = IncidentManager.create(
            "incident-schema-shape",
            "low",
            "Verify incident history schema shape",
            "2026-08-01T00:00:00Z",
        )
        history_items = self.loaded["schemas/incident.schema.json"]["properties"][
            "history"
        ]["items"]
        self.assertEqual(
            set(history_items["properties"]),
            set(incident.to_dict()["history"][0]),
        )

    def test_validator_rejects_loose_incident_history_items(self) -> None:
        loaded = copy.deepcopy(self.loaded)
        loaded["schemas/incident.schema.json"]["properties"]["history"][
            "items"
        ] = {"type": "object"}
        errors: list[str] = []
        validate_schemas(loaded, errors)
        self.assertTrue(
            any("history items must define the exact runtime record" in error for error in errors)
        )

    def test_validator_rejects_loose_audit_receipt(self) -> None:
        loaded = copy.deepcopy(self.loaded)
        loaded["schemas/safety_decision.schema.json"]["properties"][
            "audit_receipt"
        ] = {"type": ["object", "null"]}
        errors: list[str] = []
        validate_schemas(loaded, errors)
        self.assertTrue(
            any("audit_receipt must be null or an exact receipt" in error for error in errors)
        )

    def test_validator_rejects_missing_identifier_length_limit(self) -> None:
        loaded = copy.deepcopy(self.loaded)
        del loaded["schemas/incident.schema.json"]["properties"]["id"][
            "maxLength"
        ]
        errors: list[str] = []
        validate_schemas(loaded, errors)
        self.assertTrue(
            any("identifier maxLength must be 100" in error for error in errors)
        )

    def test_validator_rejects_missing_permission_count_limit(self) -> None:
        loaded = copy.deepcopy(self.loaded)
        del loaded["schemas/execution_request.schema.json"]["properties"][
            "permissions"
        ]["maxItems"]
        errors: list[str] = []
        validate_schemas(loaded, errors)
        self.assertTrue(
            any("permissions maxItems must be 64" in error for error in errors)
        )

    def test_validator_rejects_missing_incident_history_count_limit(self) -> None:
        loaded = copy.deepcopy(self.loaded)
        del loaded["schemas/incident.schema.json"]["properties"]["history"][
            "maxItems"
        ]
        errors: list[str] = []
        validate_schemas(loaded, errors)
        self.assertTrue(
            any("history maxItems must be 64" in error for error in errors)
        )


class ExecutionGateOrderTests(unittest.TestCase):
    def test_multiple_failures_follow_master_design_gate_order(self) -> None:
        policy = load_policy(ROOT / "policies" / "default_policy.json")
        request = validate_execution_request(request_data())
        incident = IncidentManager.create(
            "incident-gate-order",
            "critical",
            "Verify execution gate ordering",
            "2026-08-01T00:00:00Z",
        )

        decision = ExecutionSafety().evaluate(request, policy, [incident])

        self.assertEqual(decision.status, "deny")
        self.assertEqual(
            decision.reasons,
            (
                "permission-missing",
                "integrity-required",
                "incident-containment-active",
                "unrecoverable-mutation",
                "recovery-required",
                "approval-required",
            ),
        )


if __name__ == "__main__":
    unittest.main()
