from __future__ import annotations

import os
import multiprocessing
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import safety_core.integrity as integrity_module
from safety_core.audit import AuditLedger
from safety_core.common import ZERO_HASH
from safety_core.errors import (
    IntegrityError,
    LedgerError,
    UnsafePathError,
    ValidationError,
)
from safety_core.integrity import IntegrityVerifier


def _process_append(
    path: str,
    event_id: str,
    ready,
    start,
    results,
) -> None:
    ledger = AuditLedger(path)
    ready.put("ready")
    start.wait(10)
    try:
        receipt = ledger.append(event_id, "event", {})
        results.put(("ok", receipt["record_hash"]))
    except LedgerError:
        results.put(("blocked", None))


class IntegrityTests(unittest.TestCase):
    def test_manifest_is_sorted_and_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "z.txt").write_text("z", encoding="utf-8")
            (root / "nested" / "a.txt").write_text("alpha", encoding="utf-8")
            manifest = IntegrityVerifier.file_manifest(root)
            self.assertEqual(
                [item["path"] for item in manifest],
                ["nested/a.txt", "z.txt"],
            )
            self.assertTrue(IntegrityVerifier.verify_manifest(root, manifest))
            (root / "z.txt").write_text("changed", encoding="utf-8")
            self.assertFalse(IntegrityVerifier.verify_manifest(root, manifest))

    def test_malformed_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a").write_text("a", encoding="utf-8")
            with self.assertRaises(ValidationError):
                IntegrityVerifier.verify_manifest(
                    root,
                    [{"path": "../escape", "size": 1, "sha256": "0" * 64}],
                )

    def test_symlink_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.txt"
            target.write_text("content", encoding="utf-8")
            link = root / "link.txt"
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is not available")
            with self.assertRaises(UnsafePathError):
                IntegrityVerifier.file_manifest(root)

    @unittest.skipUnless(os.name == "nt", "Windows handle semantics")
    def test_windows_root_handle_blocks_namespace_swap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            (root / "file.txt").write_text("safe", encoding="utf-8")
            replacement = root.with_name("replacement")
            original_snapshot = integrity_module._windows_snapshot
            attempted = False

            def attempt_swap(path, maximum_entries):
                nonlocal attempted
                if path == root and not attempted:
                    attempted = True
                    with self.assertRaises(OSError):
                        root.rename(replacement)
                return original_snapshot(path, maximum_entries)

            with mock.patch.object(
                integrity_module,
                "_windows_snapshot",
                new=attempt_swap,
            ):
                manifest = IntegrityVerifier.file_manifest(root)
            self.assertTrue(attempted)
            self.assertEqual(manifest[0]["sha256"], IntegrityVerifier.file_manifest(root)[0]["sha256"])
            self.assertFalse(replacement.exists())

    @unittest.skipUnless(os.name == "nt", "Windows handle semantics")
    def test_directory_addition_during_scan_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "file.txt").write_text("safe", encoding="utf-8")
            original_entry = integrity_module._windows_file_entry
            injected = False

            def inject_file(path, relative, expected, state):
                nonlocal injected
                result = original_entry(path, relative, expected, state)
                if not injected:
                    injected = True
                    (source / "late.txt").write_text("late", encoding="utf-8")
                return result

            with mock.patch.object(
                integrity_module,
                "_windows_file_entry",
                new=inject_file,
            ):
                with self.assertRaises(IntegrityError):
                    IntegrityVerifier.file_manifest(source)


class AuditTests(unittest.TestCase):
    def test_append_verify_query_and_copy_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = AuditLedger(Path(directory) / "audit.jsonl")
            first = ledger.append(
                "event-0001",
                "safety-decision",
                {"status": "allow", "request_id": "request-0001"},
                "2026-08-01T00:00:00Z",
            )
            second = ledger.append(
                "event-0002",
                "monitor-signal",
                {"status": "warning"},
                "2026-08-01T00:00:01Z",
            )
            self.assertTrue(
                ledger.verify(expected_count=2, expected_head=second["record_hash"])
            )
            self.assertEqual(first["sequence"], 1)
            queried = ledger.query()
            queried[0]["data"]["status"] = "mutated-copy"
            self.assertEqual(ledger.query()[0]["data"]["status"], "allow")
            self.assertEqual(len(ledger.query("monitor-signal")), 1)

    def test_sensitive_or_raw_payload_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = AuditLedger(Path(directory) / "audit.jsonl")
            for data in (
                {"token": "value"},
                {"nested": {"private_key": "value"}},
                {"request_payload": {"content": "value"}},
                {"api.key": "value"},
                {"nested": {"private.key": "value"}},
                {"request.payload": {"content": "value"}},
            ):
                with self.subTest(data=data):
                    with self.assertRaises(ValidationError):
                        ledger.append("event-0001", "safety-decision", data)

    def test_duplicate_event_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = AuditLedger(Path(directory) / "audit.jsonl")
            ledger.append("event-0001", "event", {})
            with self.assertRaises(LedgerError):
                ledger.append("event-0001", "event", {})

    def test_mutation_deletion_and_anchor_mismatch_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            ledger = AuditLedger(path)
            ledger.append(
                "event-0001",
                "event",
                {"status": "allow"},
                "2026-08-01T00:00:00Z",
            )
            head = ledger.append(
                "event-0002",
                "event",
                {"status": "deny"},
                "2026-08-01T00:00:01Z",
            )["record_hash"]
            original = path.read_bytes()
            path.write_bytes(original.replace(b'"deny"', b'"allow"', 1))
            with self.assertRaises(LedgerError):
                ledger.verify()
            path.write_bytes(original.splitlines(keepends=True)[0])
            with self.assertRaises(LedgerError):
                ledger.verify()
            with self.assertRaises(LedgerError):
                ledger.verify(expected_count=2, expected_head=head)

    def test_preexisting_empty_ledger_requires_zero_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            path.touch()
            ledger = AuditLedger(path)
            with self.assertRaises(LedgerError):
                ledger.verify()
            with self.assertRaises(LedgerError):
                ledger.query()
            with self.assertRaises(LedgerError):
                ledger.append("event-0001", "event", {})
            self.assertTrue(ledger.verify(expected_count=0, expected_head=ZERO_HASH))
            receipt = ledger.append("event-0001", "event", {})
            self.assertEqual(receipt["sequence"], 1)

    def test_partial_external_anchor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = AuditLedger(Path(directory) / "audit.jsonl")
            ledger.append("event-0001", "event", {})
            with self.assertRaises(ValidationError):
                ledger.verify(expected_count=1)
            with self.assertRaises(ValidationError):
                ledger.verify(expected_head="0" * 64)

    def test_lock_hardlink_never_modifies_victim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "audit.jsonl"
            victim = root / "victim.bin"
            victim.write_bytes(b"")
            os.link(victim, root / ".audit.jsonl.lock")
            ledger = AuditLedger(path)
            with self.assertRaises(LedgerError):
                ledger.append("event-0001", "event", {})
            self.assertEqual(victim.read_bytes(), b"")
            self.assertFalse(path.exists())

    def test_preexisting_empty_lock_is_never_initialized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "audit.jsonl"
            lock_path = root / ".audit.jsonl.lock"
            lock_path.touch()
            ledger = AuditLedger(path)
            with self.assertRaises(LedgerError):
                ledger.append("event-0001", "event", {})
            self.assertEqual(lock_path.read_bytes(), b"")
            self.assertFalse(path.exists())

    def test_reopened_ledger_requires_external_anchor_before_append(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            initial = AuditLedger(path)
            head = initial.append("event-0001", "event", {})["record_hash"]
            reopened = AuditLedger(path)
            with self.assertRaises(LedgerError):
                reopened.append("event-0002", "event", {})
            reopened.verify(expected_count=1, expected_head=head)
            second = reopened.append("event-0002", "event", {})
            self.assertEqual(second["sequence"], 2)

    def test_concurrent_appends_form_one_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = AuditLedger(Path(directory) / "audit.jsonl")
            failures: list[Exception] = []

            def append(index: int) -> None:
                try:
                    ledger.append(f"event-{index:04d}", "event", {"index": index})
                except Exception as exc:  # pragma: no cover - failure is asserted below
                    failures.append(exc)

            workers = [threading.Thread(target=append, args=(index,)) for index in range(1, 9)]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join()
            self.assertEqual(failures, [])
            records = ledger.query()
            self.assertTrue(
                ledger.verify(
                    expected_count=8,
                    expected_head=records[-1]["record_hash"],
                )
            )
            self.assertEqual(
                [record["sequence"] for record in records],
                list(range(1, 9)),
            )

    def test_competing_processes_do_not_fork_the_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            context = multiprocessing.get_context("spawn")
            ready = context.Queue()
            start = context.Event()
            results = context.Queue()
            workers = [
                context.Process(
                    target=_process_append,
                    args=(str(path), f"event-{index:04d}", ready, start, results),
                )
                for index in (1, 2)
            ]
            for worker in workers:
                worker.start()
            self.assertEqual(ready.get(timeout=10), "ready")
            self.assertEqual(ready.get(timeout=10), "ready")
            start.set()
            outcomes = [results.get(timeout=10) for _ in workers]
            for worker in workers:
                worker.join(timeout=10)
                self.assertEqual(worker.exitcode, 0)
            self.assertEqual(sorted(status for status, _head in outcomes), ["blocked", "ok"])
            successful_head = next(
                head for status, head in outcomes if status == "ok"
            )
            ledger = AuditLedger(path)
            self.assertTrue(
                ledger.verify(expected_count=1, expected_head=successful_head)
            )
            records = ledger.query()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["record_hash"], successful_head)


if __name__ == "__main__":
    unittest.main()
