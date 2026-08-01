from __future__ import annotations

import unittest
from datetime import datetime, timezone

from connectivity_core import (
    AuthorizationError, ConflictError, ConnectionGrant, ConnectivityCore,
    ConnectorError, ConnectorSpec, CredentialReference, ExchangeRecord,
    OperationRequest, ValidationError, frozen_map,
)


NOW = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)


def grant(**changes):
    values = dict(
        id="grant-1", approved=True, safety_decision_id="decision-safety-1",
        valid_from="2026-08-01T00:00:00Z", expires_at="2026-08-02T00:00:00Z",
        allowed_connectors=("api-1",), allowed_operations=("read",),
        max_requests=3, max_records=10, allow_external_ai=False,
        allow_repository_write=False, allow_communication=False,
    )
    values.update(changes)
    return ConnectionGrant(**values)


def request(connector="api-1", operation="read", payload=None, key="key-1"):
    return OperationRequest("request-1", connector, operation, frozen_map(payload or {"value": 1}), key)


class ConnectorTests(unittest.TestCase):
    def setUp(self):
        self.core = ConnectivityCore(clock=lambda: NOW)

    def test_registered_connector_invocation_and_api_budget(self):
        self.core.register_connector(ConnectorSpec("api-1", "api", "neutral", "1.0", ("read",)), lambda req, secret: {"echo": req.payload["value"]})
        result = self.core.invoke(request(), grant())
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output["echo"], 1)
        self.assertEqual(self.core.api.usage("grant-1"), 1)

    def test_credential_is_resolved_but_not_exposed(self):
        seen = []
        spec = ConnectorSpec("api-1", "api", "neutral", "1.0", ("read",), CredentialReference("secret-ref", "vault", ("read",)))
        self.core.register_connector(spec, lambda req, secret: seen.append(secret) or {"ok": True})
        result = self.core.invoke(request(), grant(), credential_resolver=lambda ref: "actual-secret")
        self.assertEqual(seen, ["actual-secret"])
        self.assertNotIn("actual-secret", str(result.to_dict()))
        self.assertNotIn("actual-secret", str(spec.to_dict()))

    def test_credential_disclosure_and_resolver_failure_are_contained(self):
        spec = ConnectorSpec("api-1", "api", "neutral", "1.0", ("read",), CredentialReference("secret-ref", "vault"))
        self.core.register_connector(spec, lambda req, secret: {"leak": f"value:{secret}"})
        with self.assertRaisesRegex(ConnectorError, "disclosure"):
            self.core.invoke(request(), grant(), credential_resolver=lambda ref: "actual-secret")
        other = ConnectivityCore(clock=lambda: NOW)
        other.register_connector(spec, lambda req, secret: {})
        with self.assertRaisesRegex(AuthorizationError, "resolution-failed"):
            other.invoke(request(), grant(), credential_resolver=lambda ref: (_ for _ in ()).throw(RuntimeError("private")))

    def test_registration_is_not_authorization(self):
        self.core.register_connector(ConnectorSpec("api-1", "api", "neutral", "1.0", ("read",)), lambda req, secret: {})
        with self.assertRaises(AuthorizationError):
            self.core.invoke(request(), grant(allowed_connectors=("other",)))

    def test_budget_fails_closed_before_transport(self):
        calls = []
        self.core.register_connector(ConnectorSpec("api-1", "api", "neutral", "1.0", ("read",)), lambda req, secret: calls.append(1) or {})
        limited = grant(max_requests=1)
        self.core.invoke(request(key="first"), limited)
        with self.assertRaises(AuthorizationError):
            self.core.invoke(request(key="second"), limited)
        self.assertEqual(len(calls), 1)

    def test_record_budget_fails_closed(self):
        self.core.register_connector(ConnectorSpec("api-1", "api", "neutral", "1.0", ("read",)), lambda req, secret: {})
        with self.assertRaisesRegex(AuthorizationError, "record-budget"):
            self.core.invoke(request(payload={"records": [{}, {}]}), grant(max_records=1))

    def test_idempotency_returns_prior_and_rejects_conflict(self):
        calls = []
        self.core.register_connector(ConnectorSpec("api-1", "api", "neutral", "1.0", ("read",)), lambda req, secret: calls.append(1) or {"ok": True})
        first = self.core.invoke(request(), grant())
        self.assertIs(self.core.invoke(request(), grant()), first)
        self.assertEqual(len(calls), 1)
        with self.assertRaises(ConflictError):
            self.core.invoke(request(payload={"value": 2}), grant())

    def test_transport_failure_is_sanitized(self):
        def fail(req, secret):
            raise RuntimeError("private token and endpoint")
        self.core.register_connector(ConnectorSpec("api-1", "api", "neutral", "1.0", ("read",)), fail)
        result = self.core.invoke(request(), grant())
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error, "connector:transport-failed")
        self.assertNotIn("private", str(result.to_dict()))

    def test_unregistered_and_oversized_fail(self):
        with self.assertRaises(ConnectorError):
            self.core.invoke(request(), grant())
        self.core.register_connector(ConnectorSpec("api-1", "api", "neutral", "1.0", ("read",), max_payload_bytes=10), lambda req, secret: {})
        with self.assertRaises(ValidationError):
            self.core.invoke(request(payload={"value": "too long"}), grant())


class SensitiveDomainTests(unittest.TestCase):
    def make_core(self, connector, kind, operation):
        core = ConnectivityCore(clock=lambda: NOW)
        core.register_connector(ConnectorSpec(connector, kind, "neutral", "1.0", (operation,)), lambda req, secret: {"ok": True})
        return core

    def test_external_ai_requires_kind_and_permission(self):
        core = self.make_core("ai-1", "external_ai", "infer")
        req = request("ai-1", "infer")
        denied = grant(allowed_connectors=("ai-1",), allowed_operations=("infer",))
        with self.assertRaises(AuthorizationError):
            core.call_external_ai(req, denied)
        allowed = grant(allowed_connectors=("ai-1",), allowed_operations=("infer",), allow_external_ai=True)
        self.assertEqual(core.call_external_ai(req, allowed).status, "completed")

    def test_repository_write_requires_separate_permission(self):
        core = self.make_core("repo-1", "repository", "push")
        req = request("repo-1", "push")
        denied = grant(allowed_connectors=("repo-1",), allowed_operations=("push",))
        with self.assertRaises(AuthorizationError):
            core.access_repository(req, denied)
        allowed = grant(allowed_connectors=("repo-1",), allowed_operations=("push",), allow_repository_write=True)
        self.assertEqual(core.access_repository(req, allowed).status, "completed")

    def test_communication_requires_separate_permission(self):
        core = self.make_core("chat-1", "communication", "send")
        req = request("chat-1", "send")
        denied = grant(allowed_connectors=("chat-1",), allowed_operations=("send",))
        with self.assertRaises(AuthorizationError):
            core.communicate(req, denied)
        allowed = grant(allowed_connectors=("chat-1",), allowed_operations=("send",), allow_communication=True)
        self.assertEqual(core.communicate(req, allowed).status, "completed")

    def test_ecosystem_kind_is_enforced(self):
        core = self.make_core("platform-1", "platform", "exchange")
        req = request("platform-1", "exchange")
        allowed = grant(allowed_connectors=("platform-1",), allowed_operations=("exchange",))
        with self.assertRaises(ConnectorError):
            core.connect_ecosystem(req, allowed)


class DataExchangeTests(unittest.TestCase):
    def setUp(self):
        self.core = ConnectivityCore(clock=lambda: NOW)

    def test_json_jsonl_and_csv_round_trip(self):
        records = [{"id": "a", "value": 1}, {"id": "b", "value": 2}]
        for format in ("json", "jsonl", "csv"):
            with self.subTest(format=format):
                content = self.core.exchange.export_records(records, format)
                result = self.core.exchange.import_records(content, format)
                self.assertEqual(len(result.records), 2)
                self.assertEqual(result.rejected, 0)

    def test_csv_rejects_nested_values_and_import_is_bounded(self):
        with self.assertRaises(ValidationError):
            self.core.exchange.export_records([{"nested": {"x": 1}}], "csv")
        with self.assertRaises(ValidationError):
            self.core.exchange.import_records('[{},{}]', "json", max_records=1)

    def test_sync_uses_revision_then_explicit_policy(self):
        local = ExchangeRecord("a", 2, "2026-08-01T11:00:00Z", frozen_map({"value": "local"}), source="local")
        remote = ExchangeRecord("a", 1, "2026-08-01T12:00:00Z", frozen_map({"value": "remote"}), source="remote")
        result = self.core.sync.reconcile([local], [remote], policy="remote_wins")
        self.assertEqual(result.records[0].data["value"], "local")
        self.assertEqual(result.conflicts[0].resolution, "local-newer")

    def test_equal_revision_conflict_policies(self):
        local = ExchangeRecord("a", 1, "2026-08-01T11:00:00Z", frozen_map({"value": "local"}), source="local")
        remote = ExchangeRecord("a", 1, "2026-08-01T12:00:00Z", frozen_map({"value": "remote"}), source="remote")
        self.assertEqual(self.core.sync.reconcile([local], [remote], policy="latest").records[0].source, "remote")
        with self.assertRaises(ConflictError):
            self.core.sync.reconcile([local], [remote], policy="reject")


if __name__ == "__main__":
    unittest.main()
