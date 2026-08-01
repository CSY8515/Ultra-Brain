from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import safety_core.backup as backup_module
import safety_core.integrity as integrity_module
import safety_core.recovery as recovery_module
from safety_core.backup import BackupManager
from safety_core.errors import (
    IntegrityError,
    RecoveryError,
    UnsafePathError,
    ValidationError,
)
from safety_core.integrity import IntegrityVerifier


class IntegrityResourceLimitTests(unittest.TestCase):
    def test_individual_size_limit_is_checked_before_hashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "large.bin").write_bytes(b"12345")
            with mock.patch.object(
                integrity_module,
                "_hash_descriptor",
                side_effect=AssertionError("oversized file was hashed"),
            ):
                with self.assertRaisesRegex(IntegrityError, "file-size-limit"):
                    IntegrityVerifier.file_manifest(root, max_file_size=4)

    def test_file_count_limit_stops_before_hashing_excess_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("a", encoding="utf-8")
            (root / "b.txt").write_text("b", encoding="utf-8")
            original = integrity_module._hash_descriptor
            with mock.patch.object(
                integrity_module,
                "_hash_descriptor",
                wraps=original,
            ) as hashing:
                with self.assertRaisesRegex(IntegrityError, "file-count-limit"):
                    IntegrityVerifier.file_manifest(root, max_files=1)
            self.assertEqual(hashing.call_count, 1)

    def test_total_size_limit_stops_before_hashing_excess_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_bytes(b"123")
            (root / "b.txt").write_bytes(b"456")
            original = integrity_module._hash_descriptor
            with mock.patch.object(
                integrity_module,
                "_hash_descriptor",
                wraps=original,
            ) as hashing:
                with self.assertRaisesRegex(IntegrityError, "total-size-limit"):
                    IntegrityVerifier.file_manifest(root, max_total_size=5)
            self.assertEqual(hashing.call_count, 1)

    def test_entry_count_limit_stops_directory_snapshot_streaming(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("one", "two", "three", "four"):
                (root / name).mkdir()

            original_scandir = os.scandir
            scan_requests = 0

            class GuardedScandir:
                def __init__(self, path) -> None:
                    self._iterator = original_scandir(path)

                def __enter__(self):
                    self._iterator.__enter__()
                    return self

                def __exit__(self, *args):
                    return self._iterator.__exit__(*args)

                def __iter__(self):
                    return self

                def __next__(self):
                    nonlocal scan_requests
                    scan_requests += 1
                    if scan_requests > 2:
                        raise AssertionError("directory snapshot was eagerly materialized")
                    return next(self._iterator)

            with mock.patch.object(
                integrity_module.os,
                "scandir",
                side_effect=GuardedScandir,
            ), mock.patch.object(
                integrity_module,
                "_hash_descriptor",
                side_effect=AssertionError("entry limit reached file hashing"),
            ):
                with self.assertRaisesRegex(IntegrityError, "entry-count-limit"):
                    IntegrityVerifier.file_manifest(root, max_entries=1)
            self.assertEqual(scan_requests, 2)

    def test_manifest_limits_are_checked_before_filesystem_scan(self) -> None:
        manifest = [
            {"path": "a.txt", "size": 0, "sha256": "0" * 64},
            {"path": "b.txt", "size": 0, "sha256": "0" * 64},
        ]
        with mock.patch.object(
            IntegrityVerifier,
            "file_manifest",
            side_effect=AssertionError("unbounded manifest reached filesystem scan"),
        ):
            with self.assertRaisesRegex(ValidationError, "file-count-limit"):
                IntegrityVerifier.verify_manifest("unused", manifest, max_files=1)

    def test_depth_limit_stops_before_nested_file_hashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "one" / "two"
            nested.mkdir(parents=True)
            (nested / "deep.txt").write_text("deep", encoding="utf-8")
            with mock.patch.object(
                integrity_module,
                "_hash_descriptor",
                side_effect=AssertionError("over-depth file was hashed"),
            ):
                with self.assertRaisesRegex(IntegrityError, "depth-limit"):
                    IntegrityVerifier.file_manifest(root, max_depth=2)

    def test_recursion_error_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(
                integrity_module,
                "_walk_regular_files",
                side_effect=RecursionError,
            ):
                with self.assertRaisesRegex(IntegrityError, "depth-limit"):
                    IntegrityVerifier.file_manifest(root)

    def test_backup_rejects_external_source_hardlink_before_hashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            secret = root / "secret.txt"
            secret.write_text("outside-secret", encoding="utf-8")
            try:
                os.link(secret, source / "alias.txt")
            except (OSError, NotImplementedError):
                self.skipTest("hardlink creation is not available")
            archive = root / "backup.zip"
            with mock.patch.object(
                integrity_module,
                "_hash_descriptor",
                side_effect=AssertionError("hardlink target was hashed"),
            ):
                with self.assertRaisesRegex(UnsafePathError, "hardlink-forbidden"):
                    BackupManager.create(source, archive)
            self.assertFalse(archive.exists())

    def test_backup_passes_size_quota_into_integrity_walk(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "large.bin").write_bytes(b"12345")
            archive = root / "backup.zip"
            with mock.patch.object(backup_module, "MAX_FILE_SIZE", 4), mock.patch.object(
                integrity_module,
                "_hash_descriptor",
                side_effect=AssertionError("backup hashed an oversized source"),
            ):
                with self.assertRaisesRegex(RecoveryError, "file-size-limit"):
                    BackupManager.create(source, archive)
            self.assertFalse(archive.exists())

    @unittest.skipUnless(os.name == "nt", "Windows handle semantics")
    def test_windows_file_identity_mismatch_is_rejected_before_hashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            target = source / "file.txt"
            target.write_bytes(b"safe")
            original_entry = integrity_module._windows_file_entry
            mismatch_injected = False

            def inject_identity_mismatch(path, relative, expected, state):
                nonlocal mismatch_injected
                mismatch_injected = True
                values = list(expected)
                values[1] += 1
                mismatched = os.stat_result(values)
                return original_entry(path, relative, mismatched, state)

            with mock.patch.object(
                integrity_module,
                "_windows_file_entry",
                new=inject_identity_mismatch,
            ), mock.patch.object(
                integrity_module,
                "_hash_descriptor",
                side_effect=AssertionError("replacement was hashed"),
            ):
                with self.assertRaisesRegex(IntegrityError, "replaced-before-open"):
                    IntegrityVerifier.file_manifest(source)
            self.assertTrue(mismatch_injected)

    @unittest.skipIf(os.name == "nt", "POSIX descriptor limits")
    def test_recovery_descriptor_budget_fails_before_extraction(self) -> None:
        files = {f"dir-{index}/file.txt": b"" for index in range(10)}
        with mock.patch("resource.getrlimit", return_value=(32, 32)), mock.patch.object(
            recovery_module.os,
            "listdir",
            return_value=[str(index) for index in range(8)],
        ):
            with self.assertRaisesRegex(
                RecoveryError,
                "file-descriptor-limit",
            ):
                recovery_module._preflight_descriptor_budget(files, 1)


if __name__ == "__main__":
    unittest.main()
