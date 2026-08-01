from __future__ import annotations

import os
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import safety_core.backup as backup_module
import safety_core.recovery as recovery_module
from safety_core.backup import BackupManager, normalize_member_path
from safety_core.common import canonical_json, sha256_bytes
from safety_core.errors import RecoveryError, UnsafePathError
from safety_core.recovery import RecoveryManager


class BackupRecoveryTests(unittest.TestCase):
    def make_source(self, root: Path) -> Path:
        source = root / "source"
        (source / "nested").mkdir(parents=True)
        (source / "alpha.txt").write_text("alpha", encoding="utf-8")
        (source / "nested" / "beta.bin").write_bytes(b"\x00\x01beta")
        return source

    def test_backup_verify_and_non_overwriting_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_source(root)
            archive = root / "backup.zip"
            manifest = BackupManager.create(source, archive)
            self.assertEqual(len(manifest["files"]), 2)
            self.assertEqual(BackupManager.verify(archive), manifest)

            destination = root / "recovered"
            result = RecoveryManager.recover(archive, destination)
            self.assertEqual(result["status"], "recovered")
            self.assertEqual((destination / "alpha.txt").read_text(encoding="utf-8"), "alpha")
            self.assertEqual(
                (destination / "nested" / "beta.bin").read_bytes(),
                b"\x00\x01beta",
            )

            before = (destination / "alpha.txt").read_bytes()
            with self.assertRaises(RecoveryError):
                RecoveryManager.recover(archive, destination)
            self.assertEqual((destination / "alpha.txt").read_bytes(), before)

    def test_existing_backup_destination_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_source(root)
            archive = root / "backup.zip"
            archive.write_bytes(b"existing")
            with self.assertRaises(RecoveryError):
                BackupManager.create(source, archive)
            self.assertEqual(archive.read_bytes(), b"existing")

    def test_publish_race_never_overwrites_competing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_source(root)
            archive = root / "backup.zip"

            def competing_link(_source, destination):
                Path(destination).write_bytes(b"competing-writer")
                raise FileExistsError

            with mock.patch("safety_core.backup.os.link", side_effect=competing_link):
                with self.assertRaises(RecoveryError):
                    BackupManager.create(source, archive)
            self.assertEqual(archive.read_bytes(), b"competing-writer")

    def test_backup_inside_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_source(Path(directory))
            with self.assertRaises(UnsafePathError):
                BackupManager.create(source, source / "backup.zip")

    def test_tampered_payload_fails_before_recovery_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_source(root)
            archive = root / "backup.zip"
            BackupManager.create(source, archive)
            tampered = root / "tampered.zip"
            with zipfile.ZipFile(archive, "r") as original, zipfile.ZipFile(
                tampered, "w", compression=zipfile.ZIP_DEFLATED
            ) as changed:
                for info in original.infolist():
                    content = original.read(info.filename)
                    if info.filename == "data/alpha.txt":
                        content = b"tampered"
                    changed.writestr(info.filename, content)
            destination = root / "should-not-exist"
            with self.assertRaises(RecoveryError):
                RecoveryManager.recover(tampered, destination)
            self.assertFalse(destination.exists())

    def test_traversal_and_extra_members_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "malicious.zip"
            content = b"escape"
            manifest = {
                "version": "0.2.0",
                "created_at": "2026-08-01T00:00:00Z",
                "algorithm": "sha256",
                "files": [
                    {
                        "path": "../escape.txt",
                        "size": len(content),
                        "sha256": sha256_bytes(content),
                    }
                ],
            }
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("manifest.json", canonical_json(manifest))
                output.writestr("data/../escape.txt", content)
            with self.assertRaises(RecoveryError):
                RecoveryManager.recover(archive, root / "destination")
            self.assertFalse((root / "escape.txt").exists())

    def test_case_collision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "collision.zip"
            content = b"x"
            digest = sha256_bytes(content)
            manifest = {
                "version": "0.2.0",
                "created_at": "2026-08-01T00:00:00Z",
                "algorithm": "sha256",
                "files": [
                    {"path": "A.txt", "size": 1, "sha256": digest},
                    {"path": "a.txt", "size": 1, "sha256": digest},
                ],
            }
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("manifest.json", canonical_json(manifest))
                output.writestr("data/A.txt", content)
                output.writestr("data/a.txt", content)
            with self.assertRaises(RecoveryError):
                BackupManager.verify(archive)

    def test_noncanonical_manifest_file_order_is_rejected_before_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contents = {"a.txt": b"a", "b.txt": b"b"}
            cases = {
                "unsorted": ["b.txt", "a.txt"],
                "duplicate": ["a.txt", "a.txt"],
            }
            for label, paths in cases.items():
                with self.subTest(case=label):
                    archive = root / f"{label}.zip"
                    manifest = {
                        "version": "0.2.0",
                        "created_at": "2026-08-01T00:00:00Z",
                        "algorithm": "sha256",
                        "files": [
                            {
                                "path": path,
                                "size": len(contents[path]),
                                "sha256": sha256_bytes(contents[path]),
                            }
                            for path in paths
                        ],
                    }
                    with zipfile.ZipFile(
                        archive,
                        "w",
                        compression=zipfile.ZIP_DEFLATED,
                    ) as output:
                        output.writestr("manifest.json", canonical_json(manifest))
                        for path in sorted(set(paths)):
                            output.writestr(f"data/{path}", contents[path])

                    with self.assertRaisesRegex(
                        RecoveryError,
                        "backup-manifest-file-order-invalid",
                    ):
                        BackupManager.verify(archive)

                    destination = root / f"{label}-recovered"
                    with self.assertRaisesRegex(
                        RecoveryError,
                        "backup-manifest-file-order-invalid",
                    ):
                        RecoveryManager.recover(archive, destination)
                    self.assertFalse(destination.exists())

    def test_noncanonical_and_windows_ambiguous_members_are_rejected(self) -> None:
        for value in (
            "./file.txt",
            "a//file.txt",
            "file.txt/",
            "file.txt:stream",
            "file.txt.",
            "file.txt ",
            "NUL.txt",
            "nested/COM1.log",
            "bad?.txt",
            "bad*.txt",
            '<bad>.txt',
            'quote".txt',
            "pipe|.txt",
            "CONIN$.txt",
            "CONOUT$.txt",
        ):
            with self.subTest(value=value):
                with self.assertRaises(RecoveryError):
                    normalize_member_path(value)

    def test_unsupported_compression_is_a_typed_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "unsupported.zip"
            manifest = {
                "version": "0.2.0",
                "created_at": "2026-08-01T00:00:00Z",
                "algorithm": "sha256",
                "files": [],
            }
            with zipfile.ZipFile(
                archive,
                "w",
                compression=zipfile.ZIP_BZIP2,
            ) as output:
                output.writestr("manifest.json", canonical_json(manifest))
            with self.assertRaises(RecoveryError):
                BackupManager.verify(archive)

    def test_backup_creation_enforces_count_and_size_quotas(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_source(root)
            with mock.patch.object(backup_module, "MAX_FILES", 1):
                with self.assertRaises(RecoveryError):
                    BackupManager.create(source, root / "count.zip")
            with mock.patch.object(backup_module, "MAX_FILE_SIZE", 3):
                with self.assertRaises(RecoveryError):
                    BackupManager.create(source, root / "file-size.zip")
            with mock.patch.object(backup_module, "MAX_TOTAL_SIZE", 5):
                with self.assertRaises(RecoveryError):
                    BackupManager.create(source, root / "total-size.zip")

    def test_backup_verification_enforces_member_count_quota(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "backup.zip"
            BackupManager.create(self.make_source(root), archive)
            with mock.patch.object(backup_module, "MAX_FILES", 1):
                with self.assertRaises(RecoveryError):
                    BackupManager.verify(archive)

    def test_leaf_hardlink_race_never_modifies_victim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "backup.zip"
            BackupManager.create(self.make_source(root), archive)
            victim = root / "victim.bin"
            victim.write_bytes(b"outside-content")
            destination = root / "recovered"
            original = recovery_module._DirectoryGuard.create_file
            injected = False

            def inject_hardlink(guard, name, path):
                nonlocal injected
                if not injected:
                    injected = True
                    os.link(victim, path)
                return original(guard, name, path)

            with mock.patch.object(
                recovery_module._DirectoryGuard,
                "create_file",
                new=inject_hardlink,
            ):
                with self.assertRaises(RecoveryError):
                    RecoveryManager.recover(archive, destination)
            self.assertEqual(victim.read_bytes(), b"outside-content")

    def test_failed_recovery_never_runs_destructive_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "backup.zip"
            BackupManager.create(self.make_source(root), archive)
            destination = root / "recovered"
            with mock.patch.object(
                recovery_module,
                "_write_all",
                side_effect=RecoveryError("injected-write-failure"),
            ), mock.patch.object(Path, "unlink", side_effect=AssertionError), mock.patch.object(
                Path,
                "rmdir",
                side_effect=AssertionError,
            ):
                with self.assertRaises(RecoveryError):
                    RecoveryManager.recover(archive, destination)
            self.assertTrue(destination.exists())

    def test_final_rehash_detects_same_size_post_write_corruption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "backup.zip"
            BackupManager.create(self.make_source(root), archive)
            destination = root / "recovered"
            original_write = recovery_module._write_all
            corrupted = False

            def corrupt_after_write(descriptor, content):
                nonlocal corrupted
                digest = original_write(descriptor, content)
                if not corrupted and len(content) == 5:
                    corrupted = True
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    os.write(descriptor, b"EVIL!")
                    os.fsync(descriptor)
                return digest

            with mock.patch.object(
                recovery_module,
                "_write_all",
                new=corrupt_after_write,
            ):
                with self.assertRaises(RecoveryError):
                    RecoveryManager.recover(archive, destination)
            self.assertTrue(corrupted)
            self.assertEqual((destination / "alpha.txt").read_bytes(), b"EVIL!")

    def test_post_create_failure_closes_recovery_file_handle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "backup.zip"
            BackupManager.create(self.make_source(root), archive)
            destination = root / "recovered"
            original_check = recovery_module._is_link_like_metadata

            def fail_for_regular_file(metadata):
                if stat.S_ISREG(metadata.st_mode):
                    raise OSError("injected-post-create-failure")
                return original_check(metadata)

            with mock.patch.object(
                recovery_module,
                "_is_link_like_metadata",
                new=fail_for_regular_file,
            ):
                with self.assertRaises(RecoveryError):
                    RecoveryManager.recover(archive, destination)
            residual = destination / "alpha.txt"
            residual.unlink()
            self.assertFalse(residual.exists())

    def test_unexpected_final_tree_entry_blocks_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "safe.txt").write_text("safe", encoding="utf-8")
            archive = root / "backup.zip"
            BackupManager.create(source, archive)
            destination = root / "restore"
            original_manifest = recovery_module.IntegrityVerifier.tree_manifest
            injected = False

            def inject_extra(tree, **limits):
                nonlocal injected
                extra = Path(tree) / "unexpected-directory"
                extra.mkdir()
                injected = True
                return original_manifest(tree, **limits)

            with mock.patch.object(
                recovery_module.IntegrityVerifier,
                "tree_manifest",
                side_effect=inject_extra,
            ):
                with self.assertRaisesRegex(
                    RecoveryError,
                    "final-tree-mismatch",
                ):
                    RecoveryManager.recover(archive, destination)
            self.assertTrue(injected)
            self.assertTrue((destination / "unexpected-directory").is_dir())

    def test_source_symlink_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_source(root)
            try:
                os.symlink(source / "alpha.txt", source / "linked.txt")
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is not available")
            with self.assertRaises(UnsafePathError):
                BackupManager.create(source, root / "backup.zip")


if __name__ == "__main__":
    unittest.main()
