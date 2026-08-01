from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import safety_core.common as common_module
from safety_core.common import (
    MAX_COLLECTION_ITEMS,
    MAX_IDENTIFIER_LENGTH,
    MAX_JSON_DOCUMENT_BYTES,
    MAX_SENSITIVE_SCAN_NODES,
    load_json_strict,
    reject_sensitive_keys,
    validate_filesystem_path,
    validate_identifier,
)
from safety_core.errors import ValidationError
from safety_core.execution import ExecutionSafety
from safety_core.incident import IncidentManager
from safety_core.validation import (
    load_policy,
    validate_execution_request,
    validate_observation,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY = load_policy(ROOT / "policies" / "default_policy.json")


class RaisingIncidentIterable:
    def __init__(self, stage: str, error: BaseException) -> None:
        self.stage = stage
        self.error = error

    def __iter__(self):
        if self.stage == "iter":
            raise self.error
        return self

    def __next__(self):
        raise self.error


def request_data(**updates):
    value = {
        "id": "request-boundary",
        "version": "0.2.0",
        "actor": "tester",
        "operation": "read",
        "target": "workspace/file.txt",
        "permissions": ["read"],
        "likelihood": 1,
        "impact": 1,
        "integrity_verified": True,
        "reversible": True,
        "recovery_plan_verified": True,
        "approved": True,
        "requested_at": "2026-08-01T00:00:00Z",
    }
    value.update(updates)
    return value


class SensitiveKeyFingerprintTests(unittest.TestCase):
    def test_separator_and_camel_case_variants_are_rejected(self) -> None:
        for key in (
            "pass_word",
            "passWord",
            "privateKey",
            "apiKey",
            "sessionToken",
        ):
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValidationError, "sensitive-key"):
                    reject_sensitive_keys({key: "value"})

    def test_unicode_compatibility_sensitive_key_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "sensitive-key"):
            reject_sensitive_keys({"\uff50\uff41\uff53\uff53\uff57\uff4f\uff52\uff44": "value"})

    def test_sensitive_key_scan_has_a_node_limit(self) -> None:
        with self.assertRaisesRegex(ValidationError, "node-limit"):
            reject_sensitive_keys([None] * MAX_SENSITIVE_SCAN_NODES)


class IdentifierAndCollectionLimitTests(unittest.TestCase):
    def test_identifier_length_limit_has_an_inclusive_boundary(self) -> None:
        valid = "a" * MAX_IDENTIFIER_LENGTH
        self.assertEqual(validate_identifier(valid), valid)
        with self.assertRaisesRegex(ValidationError, "too-long"):
            validate_identifier(valid + "a")
        with self.assertRaisesRegex(ValidationError, "too-long"):
            validate_execution_request(request_data(id=valid + "a"))

    def test_execution_request_rejects_oversized_permission_list(self) -> None:
        permissions = [f"permission-{index}" for index in range(MAX_COLLECTION_ITEMS + 1)]
        with self.assertRaisesRegex(ValidationError, "too-many-items"):
            validate_execution_request(request_data(permissions=permissions))

    def test_collection_bound_precedes_sensitive_key_scan(self) -> None:
        permissions = ["read"] * (MAX_COLLECTION_ITEMS + 1)
        permissions[-1] = {"password": "must-not-be-scanned"}  # type: ignore[list-item]
        with self.assertRaisesRegex(ValidationError, "too-many-items"):
            validate_execution_request(request_data(permissions=permissions))

    def test_execution_request_field_count_is_bounded_before_sorting(self) -> None:
        request = request_data()
        request.update({f"extra-{index}": index for index in range(1000)})
        with self.assertRaisesRegex(ValidationError, "too-many-fields"):
            validate_execution_request(request)

    def test_duplicate_permissions_remain_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "duplicate-value"):
            validate_execution_request(request_data(permissions=["read", "read"]))

    def test_oversized_builtin_strings_are_rejected_before_scanning(self) -> None:
        with self.assertRaisesRegex(ValidationError, "too-long"):
            validate_execution_request(request_data(actor="a" * 201))
        with self.assertRaisesRegex(ValidationError, "too-long"):
            IncidentManager.create("incident-boundary", "low", "a" * 501)

    def test_string_subclasses_are_rejected_without_running_protocols(self) -> None:
        class TrapString(str):
            def __len__(self):
                raise AssertionError("string subclass length was used")

            def __iter__(self):
                raise AssertionError("string subclass was scanned")

            def strip(self, *args, **kwargs):
                raise AssertionError("string subclass was copied")

            def __eq__(self, other):
                raise AssertionError("string subclass equality was used")

            def __hash__(self):
                raise AssertionError("string subclass hash was used")

        with self.assertRaisesRegex(ValidationError, "invalid-identifier"):
            validate_identifier(TrapString("identifier"))
        with self.assertRaisesRegex(ValidationError, "nonempty-string-required"):
            validate_execution_request(request_data(actor=TrapString("actor")))
        with self.assertRaises(ValidationError):
            validate_execution_request(
                request_data(permissions=[TrapString("bogus")])
            )
        with self.assertRaisesRegex(ValidationError, "summary:invalid"):
            IncidentManager.create(
                "incident-boundary",
                "low",
                TrapString("summary"),
            )


class StrictJsonBoundaryTests(unittest.TestCase):
    def test_json_loader_rejects_non_regular_and_oversized_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValidationError, "regular-file-required"):
                load_json_strict(root)
            oversized = root / "oversized.json"
            oversized.write_bytes(b" " * (MAX_JSON_DOCUMENT_BYTES + 1))
            with self.assertRaisesRegex(ValidationError, "size-limit"):
                load_json_strict(oversized)

    def test_json_loader_rejects_nonfinite_finite_syntax(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "overflow.json"
            path.write_text('{"value":1e9999}', encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "number-not-finite"):
                load_json_strict(path)

    def test_json_loader_reports_descriptor_close_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text('{"status":"active"}', encoding="utf-8")
            real_close = os.close

            def close_then_fail(descriptor: int) -> None:
                real_close(descriptor)
                raise OSError("forced close failure")

            with mock.patch.object(
                common_module.os,
                "close",
                side_effect=close_then_fail,
            ), self.assertRaisesRegex(ValidationError, "close-failed"):
                load_json_strict(path)

    def test_json_loader_never_returns_transient_same_length_content(self) -> None:
        original = b'{"trusted":"A"}'
        attacker = b'{"trusted":"B"}'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_bytes(original)
            metadata = path.stat()
            real_read = os.read
            calls = 0
            write_blocked = False

            def racing_read(descriptor: int, size: int) -> bytes:
                nonlocal calls, write_blocked
                calls += 1
                if calls == 1:
                    try:
                        path.write_bytes(attacker)
                    except OSError:
                        write_blocked = True
                result = real_read(descriptor, size)
                if calls == 3 and not write_blocked:
                    path.write_bytes(original)
                    os.utime(
                        path,
                        ns=(metadata.st_atime_ns, metadata.st_mtime_ns),
                    )
                return result

            with mock.patch.object(common_module.os, "read", side_effect=racing_read):
                try:
                    loaded = load_json_strict(path)
                except ValidationError:
                    return
            self.assertEqual(loaded, {"trusted": "A"})

    @unittest.skipUnless(os.name == "posix", "FIFO semantics are POSIX-only")
    def test_json_loader_rejects_fifo_without_opening_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "policy.fifo"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(ValidationError, "regular-file-required"):
                load_json_strict(fifo)

    def test_pathlike_runtime_failure_is_normalized(self) -> None:
        class FailingPath:
            def __fspath__(self):
                raise RuntimeError("untrusted path failure")

        with self.assertRaisesRegex(ValidationError, "invalid-path"):
            validate_filesystem_path(FailingPath(), "input")


class UnicodeScalarBoundaryTests(unittest.TestCase):
    def test_public_free_text_fields_reject_lone_surrogates(self) -> None:
        surrogate = chr(0xD800)
        with self.assertRaisesRegex(ValidationError, "invalid-unicode-scalar"):
            validate_execution_request(request_data(actor=surrogate))
        with self.assertRaisesRegex(ValidationError, "invalid-unicode-scalar"):
            validate_execution_request(request_data(target=f"workspace/{surrogate}"))
        with self.assertRaisesRegex(ValidationError, "invalid-unicode-scalar"):
            validate_observation(
                {
                    "id": "observation-boundary",
                    "metric": surrogate,
                    "value": 0,
                    "warning_at": 1,
                    "critical_at": 2,
                    "observed_at": "2026-08-01T00:00:00Z",
                }
            )
        with self.assertRaisesRegex(ValidationError, "invalid-unicode-scalar"):
            IncidentManager.create("incident-boundary", "low", surrogate)


class IncidentCollectionBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ExecutionSafety()
        self.request = validate_execution_request(request_data())

    def test_non_iterable_and_raw_incident_values_are_typed_failures(self) -> None:
        for incidents in (None, 1, [object()]):
            with self.subTest(incidents=incidents):
                with self.assertRaises(ValidationError):
                    self.engine.evaluate(self.request, POLICY, incidents)  # type: ignore[arg-type]

    def test_general_incident_iteration_failures_are_normalized(self) -> None:
        for stage, message in (
            ("iter", "incidents:iterable-required"),
            ("next", "incidents:iteration-failed"),
        ):
            with self.subTest(stage=stage):
                failure = KeyError("untrusted iterator failure")
                with self.assertRaisesRegex(ValidationError, message) as raised:
                    self.engine.evaluate(
                        self.request,
                        POLICY,
                        RaisingIncidentIterable(stage, failure),
                    )
                self.assertIs(raised.exception.__cause__, failure)

    def test_incident_iteration_preserves_validation_errors(self) -> None:
        for stage in ("iter", "next"):
            with self.subTest(stage=stage):
                failure = ValidationError("existing-validation-error")
                with self.assertRaises(ValidationError) as raised:
                    self.engine.evaluate(
                        self.request,
                        POLICY,
                        RaisingIncidentIterable(stage, failure),
                    )
                self.assertIs(raised.exception, failure)

    def test_incident_iteration_does_not_catch_base_exceptions(self) -> None:
        class IterationAbort(BaseException):
            pass

        for stage in ("iter", "next"):
            with self.subTest(stage=stage):
                failure = IterationAbort("abort")
                with self.assertRaises(IterationAbort) as raised:
                    self.engine.evaluate(
                        self.request,
                        POLICY,
                        RaisingIncidentIterable(stage, failure),
                    )
                self.assertIs(raised.exception, failure)

    def test_incident_collection_limit_is_checked_before_gate_short_circuit(self) -> None:
        active = IncidentManager.create(
            "incident-boundary",
            "critical",
            "Active containment",
            "2026-08-01T00:00:00Z",
        )
        with self.assertRaisesRegex(ValidationError, "too-many-items"):
            self.engine.evaluate(
                self.request,
                POLICY,
                [active] * (MAX_COLLECTION_ITEMS + 1),
            )


if __name__ == "__main__":
    unittest.main()
