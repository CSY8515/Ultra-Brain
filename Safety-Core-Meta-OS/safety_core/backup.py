"""Verified, bounded backup archive creation."""

from __future__ import annotations

import json
import os
import stat
import struct
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, BinaryIO, Iterator
from uuid import uuid4

from .common import (
    CONTRACT_VERSION,
    HASH_PATTERN,
    canonical_timestamp,
    canonical_json,
    reject_duplicate_keys,
    sha256_bytes,
    utc_now,
    validate_filesystem_path,
)
from .errors import IntegrityError, RecoveryError, UnsafePathError, ValidationError
from .integrity import IntegrityVerifier


MANIFEST_NAME = "manifest.json"
DATA_PREFIX = "data/"
WINDOWS_RESERVED_NAMES = {
    "con",
    "conin$",
    "conout$",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}
WINDOWS_INVALID_CHARACTERS = frozenset('<>:"\\|?*')
MAX_FILES = 512
MAX_FILE_SIZE = 16 * 1024 * 1024
MAX_TOTAL_SIZE = 64 * 1024 * 1024
MAX_MANIFEST_SIZE = 4 * 1024 * 1024
MAX_ARCHIVE_SIZE = 80 * 1024 * 1024
MAX_PATH_DEPTH = 32
MAX_ENTRIES = MAX_FILES * (MAX_PATH_DEPTH + 1)
ALLOWED_COMPRESSION = frozenset({zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED})


def _metadata_is_link_like(metadata: os.stat_result) -> bool:
    if stat.S_ISLNK(metadata.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _is_link_or_junction(path: Path) -> bool:
    try:
        return _metadata_is_link_like(os.lstat(path))
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise UnsafePathError("path-inspection-failed") from exc


def reject_linked_path(path: Path, *, include_leaf: bool = True) -> None:
    absolute = path.absolute()
    candidates = list(absolute.parents)
    candidates.reverse()
    if include_leaf:
        candidates.append(absolute)
    for candidate in candidates:
        if _is_link_or_junction(candidate):
            raise UnsafePathError("linked-path-forbidden")


def normalize_member_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise RecoveryError("unsafe-archive-path")
    if "\\" in value:
        raise RecoveryError("archive-backslash-forbidden")
    windows = PureWindowsPath(value)
    posix = PurePosixPath(value)
    if windows.is_absolute() or windows.drive or posix.is_absolute():
        raise RecoveryError("archive-absolute-path")
    if any(part in {"", ".", ".."} for part in posix.parts):
        raise RecoveryError("archive-traversal")
    normalized = posix.as_posix()
    if normalized != value:
        raise RecoveryError("archive-path-not-canonical")
    for part in posix.parts:
        if any(ord(character) < 32 for character in part) or any(
            character in WINDOWS_INVALID_CHARACTERS for character in part
        ):
            raise RecoveryError("archive-windows-unsafe-path")
        if part.endswith((" ", ".")):
            raise RecoveryError("archive-windows-ambiguous-path")
        if part.split(".", 1)[0].casefold() in WINDOWS_RESERVED_NAMES:
            raise RecoveryError("archive-windows-reserved-path")
    return normalized


def _validate_zip_info(info: zipfile.ZipInfo) -> None:
    if info.flag_bits & 0x1:
        raise RecoveryError("encrypted-backup-member")
    if info.compress_type not in ALLOWED_COMPRESSION:
        raise RecoveryError("unsupported-backup-compression")
    if info.file_size < 0 or info.compress_size < 0:
        raise RecoveryError("invalid-backup-member-size")


def _read_member_bounded(
    source: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    limit: int,
) -> bytes:
    if info.file_size > limit:
        raise RecoveryError("backup-member-size-limit")
    chunks: list[bytes] = []
    total = 0
    with source.open(info, mode="r") as stream:
        while True:
            block = stream.read(min(1024 * 1024, limit + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
            if total > limit:
                raise RecoveryError("backup-member-size-limit")
    if total != info.file_size:
        raise RecoveryError("backup-member-size-mismatch")
    return b"".join(chunks)


@contextmanager
def _open_stable_archive(path: Path) -> Iterator[BinaryIO]:
    reject_linked_path(path)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    if os.name != "nt":
        flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor: int | None = None
    try:
        path_before = os.lstat(path)
        descriptor = os.open(path, flags)
        descriptor_before = os.fstat(descriptor)
        path_opened = os.lstat(path)
        if (
            not stat.S_ISREG(descriptor_before.st_mode)
            or not os.path.samestat(path_before, descriptor_before)
            or not os.path.samestat(path_opened, descriptor_before)
        ):
            raise RecoveryError("backup-archive-replaced")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            yield stream
        descriptor_after = os.fstat(descriptor)
        path_after = os.lstat(path)
        before_identity = (
            descriptor_before.st_dev,
            descriptor_before.st_ino,
            descriptor_before.st_size,
            getattr(descriptor_before, "st_mtime_ns", None),
        )
        after_identity = (
            descriptor_after.st_dev,
            descriptor_after.st_ino,
            descriptor_after.st_size,
            getattr(descriptor_after, "st_mtime_ns", None),
        )
        if (
            before_identity != after_identity
            or not os.path.samestat(path_after, descriptor_after)
        ):
            raise RecoveryError("backup-archive-changed-during-read")
        reject_linked_path(path)
    except (RecoveryError, UnsafePathError):
        raise
    except OSError as exc:
        raise RecoveryError("backup-archive-read-failed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_source_file(path: Path, *, expected_size: int, expected_hash: str) -> bytes:
    reject_linked_path(path)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    if os.name != "nt":
        flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor: int | None = None
    try:
        path_before = os.lstat(path)
        descriptor = os.open(path, flags)
        descriptor_before = os.fstat(descriptor)
        path_opened = os.lstat(path)
        if (
            not stat.S_ISREG(descriptor_before.st_mode)
            or not os.path.samestat(path_before, descriptor_before)
            or not os.path.samestat(path_opened, descriptor_before)
        ):
            raise RecoveryError("backup-source-changed")
        if (
            getattr(path_before, "st_nlink", 1) != 1
            or getattr(descriptor_before, "st_nlink", 1) != 1
            or getattr(path_opened, "st_nlink", 1) != 1
        ):
            raise UnsafePathError("backup-source-hardlink-forbidden")
        if descriptor_before.st_size != expected_size or expected_size > MAX_FILE_SIZE:
            raise RecoveryError("backup-source-size-limit")
        chunks: list[bytes] = []
        total = 0
        while True:
            block = os.read(descriptor, min(1024 * 1024, MAX_FILE_SIZE + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
            if total > MAX_FILE_SIZE:
                raise RecoveryError("backup-source-size-limit")
        descriptor_after = os.fstat(descriptor)
        path_after = os.lstat(path)
        before_identity = (
            descriptor_before.st_dev,
            descriptor_before.st_ino,
            descriptor_before.st_size,
            getattr(descriptor_before, "st_mtime_ns", None),
        )
        after_identity = (
            descriptor_after.st_dev,
            descriptor_after.st_ino,
            descriptor_after.st_size,
            getattr(descriptor_after, "st_mtime_ns", None),
        )
        content = b"".join(chunks)
        if (
            getattr(descriptor_after, "st_nlink", 1) != 1
            or getattr(path_after, "st_nlink", 1) != 1
        ):
            raise UnsafePathError("backup-source-hardlink-forbidden")
        if (
            before_identity != after_identity
            or not os.path.samestat(path_after, descriptor_after)
            or len(content) != expected_size
            or sha256_bytes(content) != expected_hash
        ):
            raise RecoveryError("backup-source-changed")
        reject_linked_path(path)
        return content
    except (RecoveryError, UnsafePathError):
        raise
    except OSError as exc:
        raise RecoveryError("backup-source-read-failed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _preflight_zip(stream: BinaryIO) -> None:
    try:
        stream.seek(0, os.SEEK_END)
        archive_size = stream.tell()
        if archive_size < 22 or archive_size > MAX_ARCHIVE_SIZE:
            raise RecoveryError("backup-archive-size-limit")
        tail_size = min(archive_size, 65_557)
        stream.seek(archive_size - tail_size)
        tail = stream.read(tail_size)
        marker = tail.rfind(b"PK\x05\x06")
        if marker < 0 or marker + 22 > len(tail):
            raise RecoveryError("backup-eocd-missing")
        (
            signature,
            disk_number,
            central_disk,
            entries_on_disk,
            total_entries,
            central_size,
            central_offset,
            comment_size,
        ) = struct.unpack_from("<4s4H2LH", tail, marker)
        if signature != b"PK\x05\x06":
            raise RecoveryError("backup-eocd-invalid")
        if (
            disk_number != 0
            or central_disk != 0
            or entries_on_disk != total_entries
            or total_entries == 0xFFFF
            or central_size == 0xFFFFFFFF
            or central_offset == 0xFFFFFFFF
        ):
            raise RecoveryError("unsupported-backup-zip-layout")
        if total_entries > MAX_FILES + 1:
            raise RecoveryError("backup-member-count-limit")
        eocd_offset = archive_size - tail_size + marker
        if (
            central_offset + central_size > eocd_offset
            or marker + 22 + comment_size != len(tail)
        ):
            raise RecoveryError("backup-eocd-inconsistent")
        stream.seek(0)
    except RecoveryError:
        raise
    except (OSError, ValueError, struct.error) as exc:
        raise RecoveryError("invalid-backup-eocd") from exc


def _read_verified_zip(
    source: zipfile.ZipFile,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    infos = source.infolist()
    if len(infos) > MAX_FILES + 1:
        raise RecoveryError("backup-member-count-limit")
    names: list[str] = []
    folded: set[str] = set()
    by_name: dict[str, zipfile.ZipInfo] = {}
    for info in infos:
        _validate_zip_info(info)
        if info.compress_size > MAX_ARCHIVE_SIZE:
            raise RecoveryError("backup-compressed-size-limit")
        name = normalize_member_path(info.filename)
        if len(PurePosixPath(name).parts) > MAX_PATH_DEPTH + 1:
            raise RecoveryError("backup-path-depth-limit")
        mode = (info.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(mode):
            raise RecoveryError("archive-symlink-forbidden")
        folded_name = name.casefold()
        if name in by_name or folded_name in folded:
            raise RecoveryError("duplicate-archive-path")
        by_name[name] = info
        names.append(name)
        folded.add(folded_name)
    if MANIFEST_NAME not in by_name:
        raise RecoveryError("backup-manifest-missing")
    manifest = BackupManager._load_manifest(
        _read_member_bounded(
            source,
            by_name[MANIFEST_NAME],
            MAX_MANIFEST_SIZE,
        )
    )
    if len(manifest["files"]) > MAX_FILES:
        raise RecoveryError("backup-file-count-limit")

    expected_names = {MANIFEST_NAME}
    validated_entries: list[tuple[str, dict[str, Any], zipfile.ZipInfo]] = []
    seen_paths: set[str] = set()
    seen_folded: set[str] = set()
    total_size = 0
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "size", "sha256"}:
            raise RecoveryError("invalid-backup-entry")
        relative = normalize_member_path(entry["path"])
        if len(PurePosixPath(relative).parts) > MAX_PATH_DEPTH:
            raise RecoveryError("backup-path-depth-limit")
        folded_relative = relative.casefold()
        if relative in seen_paths or folded_relative in seen_folded:
            raise RecoveryError("duplicate-backup-entry")
        if type(entry["size"]) is not int or entry["size"] < 0:
            raise RecoveryError("invalid-backup-size")
        if entry["size"] > MAX_FILE_SIZE:
            raise RecoveryError("backup-file-size-limit")
        total_size += entry["size"]
        if total_size > MAX_TOTAL_SIZE:
            raise RecoveryError("backup-total-size-limit")
        if not isinstance(entry["sha256"], str) or not HASH_PATTERN.fullmatch(
            entry["sha256"]
        ):
            raise RecoveryError("invalid-backup-hash")
        member_name = f"{DATA_PREFIX}{relative}"
        if member_name not in by_name:
            raise RecoveryError("backup-file-missing")
        member_info = by_name[member_name]
        if member_info.file_size != entry["size"]:
            raise RecoveryError("backup-file-size-mismatch")
        validated_entries.append((relative, entry, member_info))
        seen_paths.add(relative)
        seen_folded.add(folded_relative)
        expected_names.add(member_name)
    if set(names) != expected_names:
        raise RecoveryError("unexpected-backup-member")

    files: dict[str, bytes] = {}
    for relative, entry, member_info in validated_entries:
        content = _read_member_bounded(source, member_info, MAX_FILE_SIZE)
        if sha256_bytes(content) != entry["sha256"]:
            raise RecoveryError("backup-file-integrity-failed")
        files[relative] = content
    return manifest, files


def _verify_archive_descriptor(
    descriptor: int,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    duplicate = os.dup(descriptor)
    try:
        os.lseek(duplicate, 0, os.SEEK_SET)
        with os.fdopen(duplicate, "rb", closefd=False) as stream:
            _preflight_zip(stream)
            with zipfile.ZipFile(stream, mode="r") as source:
                return _read_verified_zip(source)
    except (RecoveryError, UnsafePathError):
        raise
    except (
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
        NotImplementedError,
        RuntimeError,
        OSError,
        EOFError,
        ValueError,
        OverflowError,
        RecursionError,
    ) as exc:
        raise RecoveryError("invalid-or-unsupported-backup-archive") from exc
    finally:
        os.close(duplicate)


def _publish_unnamed_posix(
    descriptor: int,
    parent_descriptor: int,
    destination_name: str,
) -> None:
    import ctypes
    import errno

    libc = ctypes.CDLL(None, use_errno=True)
    linkat = libc.linkat
    linkat.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
    ]
    linkat.restype = ctypes.c_int
    result = linkat(
        descriptor,
        ctypes.c_char_p(b""),
        parent_descriptor,
        ctypes.c_char_p(os.fsencode(destination_name)),
        0x1000,
    )
    if result != 0:
        error = ctypes.get_errno()
        if error == errno.EEXIST:
            raise RecoveryError("backup-destination-raced")
        raise RecoveryError(f"backup-publish-failed:{error}")
    os.fsync(parent_descriptor)


class BackupManager:
    """Create and verify self-describing ZIP backups.

    Archives are written to a sibling temporary file, fully verified, and only
    then atomically published to the requested new path.
    """

    @staticmethod
    def create(source_root: Path, archive_path: Path) -> dict[str, Any]:
        source = validate_filesystem_path(
            source_root,
            "backup-source",
            RecoveryError,
        )
        archive = validate_filesystem_path(
            archive_path,
            "backup-destination",
            RecoveryError,
        )
        if not source.exists() or not source.is_dir():
            raise RecoveryError("backup-source-directory-required")
        reject_linked_path(source)
        reject_linked_path(archive, include_leaf=False)
        if os.path.lexists(archive):
            raise RecoveryError("backup-destination-exists")
        if not archive.parent.exists() or not archive.parent.is_dir():
            raise RecoveryError("backup-parent-missing")
        try:
            archive.absolute().relative_to(source.absolute())
        except ValueError:
            pass
        else:
            raise UnsafePathError("backup-destination-inside-source")

        from .recovery import _close_resources, _open_directory_chain

        guards = []
        descriptor: int | None = None
        temporary: Path | None = None
        try:
            archive_guards = _open_directory_chain(archive.parent)
            guards.extend(archive_guards)
            archive_parent_guard = archive_guards[-1]
            source_guards = _open_directory_chain(source)
            guards.extend(source_guards)

            try:
                files = IntegrityVerifier.file_manifest(
                    source,
                    max_depth=MAX_PATH_DEPTH,
                    max_files=MAX_FILES,
                    max_entries=MAX_ENTRIES,
                    max_file_size=MAX_FILE_SIZE,
                    max_total_size=MAX_TOTAL_SIZE,
                    reject_hardlinks=True,
                )
            except IntegrityError as exc:
                limit_errors = {
                    "manifest:depth-limit": "backup-path-depth-limit",
                    "manifest:file-count-limit": "backup-file-count-limit",
                    "manifest:entry-count-limit": "backup-entry-count-limit",
                    "manifest:file-size-limit": "backup-file-size-limit",
                    "manifest:total-size-limit": "backup-total-size-limit",
                }
                translated = limit_errors.get(str(exc))
                if translated is None:
                    raise
                raise RecoveryError(translated) from exc
            if len(files) > MAX_FILES:
                raise RecoveryError("backup-file-count-limit")
            total_size = sum(entry["size"] for entry in files)
            if any(entry["size"] > MAX_FILE_SIZE for entry in files):
                raise RecoveryError("backup-file-size-limit")
            if total_size > MAX_TOTAL_SIZE:
                raise RecoveryError("backup-total-size-limit")
            manifest = {
                "version": CONTRACT_VERSION,
                "created_at": utc_now(),
                "algorithm": "sha256",
                "files": files,
            }
            manifest_bytes = canonical_json(manifest).encode("utf-8")
            if len(manifest_bytes) > MAX_MANIFEST_SIZE:
                raise RecoveryError("backup-manifest-size-limit")

            if os.name == "nt":
                temporary = archive.with_name(f".{archive.name}.{uuid4().hex}.tmp")
                descriptor, descriptor_identity = archive_parent_guard.create_file(
                    temporary.name,
                    temporary,
                    delete_access=True,
                )
            else:
                parent_descriptor = archive_parent_guard._descriptor
                if parent_descriptor is None or not getattr(os, "O_TMPFILE", 0):
                    raise RecoveryError("stable-backup-publish-unavailable")
                try:
                    descriptor = os.open(
                        ".",
                        os.O_RDWR | os.O_TMPFILE,
                        0o600,
                        dir_fd=parent_descriptor,
                    )
                except OSError as exc:
                    raise RecoveryError("stable-backup-publish-unavailable") from exc
                descriptor_metadata = os.fstat(descriptor)
                descriptor_identity = (
                    descriptor_metadata.st_dev,
                    descriptor_metadata.st_ino,
                )

            with os.fdopen(os.dup(descriptor), "w+b") as archive_stream:
                with zipfile.ZipFile(
                    archive_stream,
                    mode="w",
                    compression=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                ) as output:
                    output.writestr(MANIFEST_NAME, manifest_bytes)
                    for entry in files:
                        relative = entry["path"]
                        source_file = source.joinpath(*PurePosixPath(relative).parts)
                        content = _read_source_file(
                            source_file,
                            expected_size=entry["size"],
                            expected_hash=entry["sha256"],
                        )
                        output.writestr(f"{DATA_PREFIX}{relative}", content)
                archive_stream.flush()
                os.fsync(archive_stream.fileno())

            descriptor_metadata = os.fstat(descriptor)
            if (
                (descriptor_metadata.st_dev, descriptor_metadata.st_ino)
                != descriptor_identity
                or descriptor_metadata.st_size > MAX_ARCHIVE_SIZE
            ):
                raise RecoveryError("backup-temporary-changed")
            verified, _verified_files = _verify_archive_descriptor(descriptor)

            if os.name == "nt":
                assert temporary is not None
                archive_parent_guard.link_file(
                    temporary.name,
                    temporary,
                    archive.name,
                    archive,
                    descriptor,
                )
                archive_parent_guard.mark_delete_on_close(descriptor)
            else:
                assert archive_parent_guard._descriptor is not None
                _publish_unnamed_posix(
                    descriptor,
                    archive_parent_guard._descriptor,
                    archive.name,
                )
                published_metadata = os.lstat(archive)
                if (
                    (published_metadata.st_dev, published_metadata.st_ino)
                    != descriptor_identity
                    or getattr(published_metadata, "st_nlink", 0) != 1
                ):
                    raise RecoveryError("stable-publish-identity-mismatch")

            os.close(descriptor)
            descriptor = None
            if os.name == "nt":
                if temporary is None or os.path.lexists(temporary):
                    raise RecoveryError("backup-temporary-alias-remains")
                published_metadata = os.lstat(archive)
                if getattr(published_metadata, "st_nlink", 0) != 1:
                    raise RecoveryError("backup-published-alias-count-invalid")
            close_error = _close_resources([], guards)
            if close_error is not None:
                raise RecoveryError("backup-resource-close-failed") from close_error
            return verified
        except Exception as cause:
            if descriptor is not None:
                if os.name == "nt" and temporary is not None:
                    try:
                        archive_parent_guard.mark_delete_on_close(descriptor)
                    except Exception:
                        pass
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            _close_resources([], guards)
            if isinstance(cause, (RecoveryError, UnsafePathError)):
                raise
            if isinstance(cause, OSError):
                raise RecoveryError("backup-create-failed") from cause
            raise

    @staticmethod
    def _load_manifest(raw: bytes) -> dict[str, Any]:
        try:
            manifest = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=reject_duplicate_keys,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValidationError(f"invalid-number:{value}")
                ),
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValidationError,
            RecursionError,
            ValueError,
            OverflowError,
        ) as exc:
            raise RecoveryError("invalid-backup-manifest") from exc
        if not isinstance(manifest, dict) or set(manifest) != {
            "version",
            "created_at",
            "algorithm",
            "files",
        }:
            raise RecoveryError("invalid-backup-manifest")
        if manifest["version"] != CONTRACT_VERSION or manifest["algorithm"] != "sha256":
            raise RecoveryError("unsupported-backup-manifest")
        if not isinstance(manifest["created_at"], str) or not isinstance(manifest["files"], list):
            raise RecoveryError("invalid-backup-manifest")
        if len(manifest["files"]) > MAX_FILES:
            raise RecoveryError("backup-file-count-limit")
        previous_path: str | None = None
        for entry in manifest["files"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                raise RecoveryError("invalid-backup-manifest")
            current_path = entry["path"]
            if previous_path is not None and current_path <= previous_path:
                raise RecoveryError("backup-manifest-file-order-invalid")
            previous_path = current_path
        try:
            if (
                canonical_timestamp(manifest["created_at"], "backup-created-at")
                != manifest["created_at"]
            ):
                raise RecoveryError("backup-timestamp-not-canonical-utc")
        except ValidationError as exc:
            raise RecoveryError("invalid-backup-timestamp") from exc
        return manifest

    @staticmethod
    def read_verified(archive_path: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
        archive = validate_filesystem_path(
            archive_path,
            "backup-archive",
            RecoveryError,
        )
        if not archive.exists() or not archive.is_file():
            raise RecoveryError("backup-archive-required")
        try:
            with _open_stable_archive(archive) as archive_stream:
                _preflight_zip(archive_stream)
                with zipfile.ZipFile(archive_stream, mode="r") as source:
                    return _read_verified_zip(source)
        except (RecoveryError, UnsafePathError):
            raise
        except (
            zipfile.BadZipFile,
            zipfile.LargeZipFile,
            NotImplementedError,
            RuntimeError,
            OSError,
            EOFError,
            ValueError,
            OverflowError,
            RecursionError,
        ) as exc:
            raise RecoveryError("invalid-or-unsupported-backup-archive") from exc

    @staticmethod
    def verify(archive_path: Path) -> dict[str, Any]:
        manifest, _ = BackupManager.read_verified(archive_path)
        return manifest
