"""Bounded SHA-256 file manifests and exact integrity verification."""

from __future__ import annotations

import hashlib
import os
import stat
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .common import HASH_PATTERN, require_exact_fields, validate_filesystem_path
from .errors import IntegrityError, UnsafePathError, ValidationError


MANIFEST_FIELDS = {"path", "size", "sha256"}
DEFAULT_MAX_DEPTH = 64
DEFAULT_MAX_FILES = 10_000
DEFAULT_MAX_ENTRIES = 100_000
DEFAULT_MAX_FILE_SIZE = 256 * 1024 * 1024
DEFAULT_MAX_TOTAL_SIZE = 1024 * 1024 * 1024
MAX_MANIFEST_PATH_LENGTH = 4096


@dataclass(frozen=True)
class _TraversalLimits:
    max_depth: int
    max_files: int
    max_entries: int
    max_file_size: int
    max_total_size: int
    reject_hardlinks: bool


@dataclass
class _TraversalState:
    file_count: int = 0
    entry_count: int = 0
    total_size: int = 0


_ACTIVE_LIMITS: ContextVar[_TraversalLimits | None] = ContextVar(
    "integrity-active-limits",
    default=None,
)


def _validated_limit(value: Any, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValidationError(f"manifest:{label}:nonnegative-integer-required")
    return value


def _traversal_limits(
    *,
    max_depth: int,
    max_files: int,
    max_entries: int,
    max_file_size: int,
    max_total_size: int,
    reject_hardlinks: bool,
) -> _TraversalLimits:
    if type(reject_hardlinks) is not bool:
        raise ValidationError("manifest:reject-hardlinks:boolean-required")
    return _TraversalLimits(
        max_depth=_validated_limit(max_depth, "max-depth"),
        max_files=_validated_limit(max_files, "max-files"),
        max_entries=_validated_limit(max_entries, "max-entries"),
        max_file_size=_validated_limit(max_file_size, "max-file-size"),
        max_total_size=_validated_limit(max_total_size, "max-total-size"),
        reject_hardlinks=reject_hardlinks,
    )


def _register_file(
    metadata: os.stat_result,
    state: _TraversalState,
    limits: _TraversalLimits,
) -> None:
    if limits.reject_hardlinks and getattr(metadata, "st_nlink", 1) != 1:
        raise UnsafePathError("manifest:hardlink-forbidden")
    if metadata.st_size > limits.max_file_size:
        raise IntegrityError("manifest:file-size-limit")
    if state.file_count >= limits.max_files:
        raise IntegrityError("manifest:file-count-limit")
    if state.total_size + metadata.st_size > limits.max_total_size:
        raise IntegrityError("manifest:total-size-limit")
    state.file_count += 1
    state.total_size += metadata.st_size


if os.name == "nt":  # pragma: no cover - declarations are platform-specific
    import ctypes
    import msvcrt
    from ctypes import wintypes

    _GENERIC_READ = 0x80000000
    _FILE_SHARE_READ = 0x00000001
    _OPEN_EXISTING = 3
    _FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    _FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    _FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    class _WindowsFileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _kernel32.CreateFileW.restype = wintypes.HANDLE
    _kernel32.GetFileInformationByHandle.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_WindowsFileInformation),
    ]
    _kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL


def _absolute_path(value: str | os.PathLike[str], label: str) -> Path:
    try:
        raw = os.fspath(validate_filesystem_path(value, label, ValidationError))
        return Path(os.path.abspath(raw))
    except (OSError, TypeError, ValueError) as exc:
        if isinstance(exc, ValidationError):
            raise
        raise ValidationError(f"{label}:invalid-path") from exc


def _is_link_like(path: Path) -> bool:
    """Return whether *path* is a symlink or Windows reparse point."""

    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise IntegrityError("manifest:path-inspection-failed") from exc

    if stat.S_ISLNK(metadata.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _reject_link_components(path: Path) -> None:
    """Reject a link in the existing lexical path, including ancestors."""

    components = [path, *path.parents]
    for component in reversed(components):
        if _is_link_like(component):
            raise UnsafePathError("manifest:symlink-forbidden")


def _relative_manifest_path(relative: Path) -> str:
    value = relative.as_posix()
    if not value or value == "." or "\\" in value:
        raise UnsafePathError("manifest:unsafe-relative-path")
    if any(ord(character) < 32 for character in value):
        raise UnsafePathError("manifest:unsafe-relative-path")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise UnsafePathError("manifest:unsafe-relative-path")
    if parsed.as_posix() != value:
        raise UnsafePathError("manifest:noncanonical-relative-path")
    return value


def _metadata_signature(metadata: os.stat_result) -> tuple[Any, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        getattr(metadata, "st_mtime_ns", None),
        getattr(metadata, "st_ctime_ns", None),
        getattr(metadata, "st_nlink", None),
        getattr(metadata, "st_file_attributes", None),
    )


def _hash_descriptor(
    descriptor: int,
    maximum_size: int | None = None,
) -> tuple[str, os.stat_result, os.stat_result]:
    before = os.fstat(descriptor)
    effective_maximum = before.st_size if maximum_size is None else maximum_size
    if before.st_size > effective_maximum:
        raise IntegrityError("manifest:file-size-limit")
    digest = hashlib.sha256()
    total = 0
    while True:
        block = os.read(
            descriptor,
            min(1024 * 1024, effective_maximum + 1 - total),
        )
        if not block:
            break
        digest.update(block)
        total += len(block)
        if total > effective_maximum:
            raise IntegrityError("manifest:file-size-limit")
    after = os.fstat(descriptor)
    if (
        not stat.S_ISREG(before.st_mode)
        or not stat.S_ISREG(after.st_mode)
        or _metadata_signature(before) != _metadata_signature(after)
    ):
        raise IntegrityError("manifest:file-changed-during-read")
    return digest.hexdigest(), before, after


def _posix_snapshot(
    descriptor: int,
    maximum_entries: int,
) -> dict[str, tuple[Any, ...]]:
    try:
        snapshot: dict[str, tuple[Any, ...]] = {}
        with os.scandir(descriptor) as iterator:
            for item in iterator:
                if len(snapshot) >= maximum_entries:
                    raise IntegrityError("manifest:entry-count-limit")
                name = item.name
                if not isinstance(name, str) or not name or name in {".", ".."}:
                    raise IntegrityError("manifest:invalid-directory-entry")
                metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                if stat.S_ISLNK(metadata.st_mode):
                    raise UnsafePathError("manifest:symlink-forbidden")
                snapshot[name] = _metadata_signature(metadata)
        return snapshot
    except (IntegrityError, UnsafePathError):
        raise
    except OSError as exc:
        raise IntegrityError("manifest:directory-read-failed") from exc


def _walk_posix(
    root: Path,
    limits: _TraversalLimits,
) -> tuple[list[dict[str, Any]], list[str]]:
    required = {os.open, os.stat}
    if (
        not required <= os.supports_dir_fd
        or not getattr(os, "O_DIRECTORY", 0)
        or not getattr(os, "O_NOFOLLOW", 0)
    ):
        raise IntegrityError("manifest:stable-traversal-unavailable")

    entries: list[dict[str, Any]] = []
    directories: list[str] = []
    state = _TraversalState()
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | os.O_NOFOLLOW
    file_flags |= getattr(os, "O_NONBLOCK", 0)

    def visit(descriptor: int, directory: Path, relative: Path) -> None:
        descriptor_before = os.fstat(descriptor)
        path_before = os.lstat(directory)
        if (
            not stat.S_ISDIR(descriptor_before.st_mode)
            or not os.path.samestat(path_before, descriptor_before)
        ):
            raise IntegrityError("manifest:directory-replaced")
        remaining_entries = limits.max_entries - state.entry_count
        snapshot_before = _posix_snapshot(descriptor, remaining_entries)
        state.entry_count += len(snapshot_before)

        for name in sorted(snapshot_before):
            child_path = directory / name
            child_relative = relative / name
            if len(child_relative.parts) > limits.max_depth:
                raise IntegrityError("manifest:depth-limit")
            child_before = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if _metadata_signature(child_before) != snapshot_before[name]:
                raise IntegrityError("manifest:directory-changed-during-read")
            if stat.S_ISDIR(child_before.st_mode):
                directories.append(_relative_manifest_path(child_relative))
                child_descriptor: int | None = None
                try:
                    child_descriptor = os.open(
                        name,
                        directory_flags,
                        dir_fd=descriptor,
                    )
                    child_opened = os.fstat(child_descriptor)
                    if not os.path.samestat(child_before, child_opened):
                        raise IntegrityError("manifest:directory-replaced")
                    visit(child_descriptor, child_path, child_relative)
                finally:
                    if child_descriptor is not None:
                        os.close(child_descriptor)
            elif stat.S_ISREG(child_before.st_mode):
                file_descriptor: int | None = None
                try:
                    file_descriptor = os.open(name, file_flags, dir_fd=descriptor)
                    file_opened = os.fstat(file_descriptor)
                    if not os.path.samestat(child_before, file_opened):
                        raise IntegrityError("manifest:file-replaced-before-open")
                    _register_file(file_opened, state, limits)
                    digest, file_before, file_after = _hash_descriptor(
                        file_descriptor,
                        file_opened.st_size,
                    )
                    child_after = os.stat(
                        name,
                        dir_fd=descriptor,
                        follow_symlinks=False,
                    )
                    if not os.path.samestat(child_after, file_before):
                        raise IntegrityError("manifest:file-replaced-during-read")
                    if limits.reject_hardlinks and (
                        getattr(file_after, "st_nlink", 1) != 1
                        or getattr(child_after, "st_nlink", 1) != 1
                    ):
                        raise UnsafePathError("manifest:hardlink-forbidden")
                    entries.append(
                        {
                            "path": _relative_manifest_path(child_relative),
                            "size": file_before.st_size,
                            "sha256": digest,
                        }
                    )
                finally:
                    if file_descriptor is not None:
                        os.close(file_descriptor)
            else:
                raise IntegrityError("manifest:non-regular-entry")

            child_final = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if _metadata_signature(child_final) != snapshot_before[name]:
                raise IntegrityError("manifest:entry-changed-during-read")

        snapshot_after = _posix_snapshot(descriptor, len(snapshot_before))
        descriptor_after = os.fstat(descriptor)
        path_after = os.lstat(directory)
        if (
            snapshot_after != snapshot_before
            or _metadata_signature(descriptor_after)
            != _metadata_signature(descriptor_before)
            or not os.path.samestat(path_after, descriptor_after)
        ):
            raise IntegrityError("manifest:directory-changed-during-read")
        _reject_link_components(directory)

    root_descriptor: int | None = None
    try:
        _reject_link_components(root)
        root_descriptor = os.open(root, directory_flags)
        visit(root_descriptor, root, Path())
    except (IntegrityError, UnsafePathError):
        raise
    except OSError as exc:
        raise IntegrityError("manifest:stable-traversal-failed") from exc
    finally:
        if root_descriptor is not None:
            os.close(root_descriptor)
    entries.sort(key=lambda entry: entry["path"])
    directories.sort()
    return entries, directories


def _windows_information(handle: int):
    information = _WindowsFileInformation()
    if not _kernel32.GetFileInformationByHandle(handle, ctypes.byref(information)):
        raise IntegrityError("manifest:handle-inspection-failed")
    identity = (
        information.dwVolumeSerialNumber,
        (information.nFileIndexHigh << 32) | information.nFileIndexLow,
    )
    signature = (
        *identity,
        information.dwFileAttributes,
        information.nFileSizeHigh,
        information.nFileSizeLow,
        information.nNumberOfLinks,
        information.ftLastWriteTime.dwHighDateTime,
        information.ftLastWriteTime.dwLowDateTime,
    )
    return information, identity, signature


def _windows_open(path: Path, *, directory: bool) -> int:
    flags = _FILE_FLAG_OPEN_REPARSE_POINT
    if directory:
        flags |= _FILE_FLAG_BACKUP_SEMANTICS
    handle = _kernel32.CreateFileW(
        str(path),
        _GENERIC_READ,
        _FILE_SHARE_READ,
        None,
        _OPEN_EXISTING,
        flags,
        None,
    )
    if handle == _INVALID_HANDLE_VALUE:
        raise IntegrityError("manifest:stable-handle-open-failed")
    try:
        information, _identity, _signature = _windows_information(handle)
        is_directory = bool(information.dwFileAttributes & _FILE_ATTRIBUTE_DIRECTORY)
        if information.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise UnsafePathError("manifest:symlink-forbidden")
        if is_directory != directory:
            raise IntegrityError("manifest:entry-type-changed")
        return handle
    except Exception:
        _kernel32.CloseHandle(handle)
        raise


def _windows_snapshot(
    directory: Path,
    maximum_entries: int,
) -> dict[str, tuple[Any, ...]]:
    try:
        with os.scandir(directory) as iterator:
            snapshot: dict[str, tuple[Any, ...]] = {}
            for item in iterator:
                if len(snapshot) >= maximum_entries:
                    raise IntegrityError("manifest:entry-count-limit")
                name = item.name
                metadata = os.lstat(directory / name)
                if _is_link_like(directory / name):
                    raise UnsafePathError("manifest:symlink-forbidden")
                snapshot[name] = _metadata_signature(metadata)
        return snapshot
    except (IntegrityError, UnsafePathError):
        raise
    except OSError as exc:
        raise IntegrityError("manifest:directory-read-failed") from exc


def _windows_file_entry(
    path: Path,
    relative: Path,
    expected: os.stat_result,
    state: _TraversalState,
) -> dict[str, Any]:
    limits = _ACTIVE_LIMITS.get()
    if limits is None:
        raise IntegrityError("manifest:traversal-limits-missing")
    _reject_link_components(path)
    path_before = os.lstat(path)
    if _metadata_signature(path_before) != _metadata_signature(expected):
        raise IntegrityError("manifest:file-replaced-before-open")
    if not stat.S_ISREG(path_before.st_mode):
        raise IntegrityError("manifest:non-regular-entry")
    if limits.reject_hardlinks and getattr(path_before, "st_nlink", 1) != 1:
        raise UnsafePathError("manifest:hardlink-forbidden")
    handle = _windows_open(path, directory=False)
    descriptor: int | None = None
    try:
        information, identity, native_before = _windows_information(handle)
        path_opened = os.lstat(path)
        if (
            _metadata_signature(path_opened) != _metadata_signature(path_before)
            or path_opened.st_ino != identity[1]
        ):
            raise IntegrityError("manifest:file-replaced-before-open")
        if limits.reject_hardlinks and (
            information.nNumberOfLinks != 1
            or getattr(path_opened, "st_nlink", 1) != 1
        ):
            raise UnsafePathError("manifest:hardlink-forbidden")
        _register_file(path_opened, state, limits)
        descriptor = msvcrt.open_osfhandle(
            handle,
            os.O_RDONLY | getattr(os, "O_BINARY", 0),
        )
        handle = None
        digest, descriptor_before, descriptor_after = _hash_descriptor(
            descriptor,
            path_opened.st_size,
        )
        native_handle = msvcrt.get_osfhandle(descriptor)
        _information, identity_after, native_after = _windows_information(native_handle)
        path_after = os.lstat(path)
        if (
            native_before != native_after
            or identity_after != identity
            or _metadata_signature(path_after) != _metadata_signature(path_before)
            or path_after.st_ino != identity[1]
        ):
            raise IntegrityError("manifest:file-changed-during-read")
        if limits.reject_hardlinks and (
            getattr(descriptor_after, "st_nlink", 1) != 1
            or getattr(path_after, "st_nlink", 1) != 1
        ):
            raise UnsafePathError("manifest:hardlink-forbidden")
        _reject_link_components(path)
        return {
            "path": _relative_manifest_path(relative),
            "size": descriptor_before.st_size,
            "sha256": digest,
        }
    except (IntegrityError, UnsafePathError):
        raise
    except OSError as exc:
        raise IntegrityError("manifest:file-read-failed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        elif handle is not None:
            _kernel32.CloseHandle(handle)


def _walk_windows(
    root: Path,
    limits: _TraversalLimits,
) -> tuple[list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    directories: list[str] = []
    state = _TraversalState()

    def visit(directory: Path, relative: Path) -> None:
        _reject_link_components(directory)
        path_before = os.lstat(directory)
        if not stat.S_ISDIR(path_before.st_mode):
            raise IntegrityError("manifest:directory-required")
        handle = _windows_open(directory, directory=True)
        try:
            _information, identity, native_before = _windows_information(handle)
            path_opened = os.lstat(directory)
            if (
                _metadata_signature(path_opened) != _metadata_signature(path_before)
                or path_opened.st_ino != identity[1]
            ):
                raise IntegrityError("manifest:directory-replaced")
            remaining_entries = limits.max_entries - state.entry_count
            snapshot_before = _windows_snapshot(directory, remaining_entries)
            state.entry_count += len(snapshot_before)
            for name in sorted(snapshot_before):
                child_path = directory / name
                child_relative = relative / name
                if len(child_relative.parts) > limits.max_depth:
                    raise IntegrityError("manifest:depth-limit")
                child_before = os.lstat(child_path)
                if _metadata_signature(child_before) != snapshot_before[name]:
                    raise IntegrityError("manifest:entry-changed-during-read")
                if stat.S_ISDIR(child_before.st_mode):
                    directories.append(_relative_manifest_path(child_relative))
                    visit(child_path, child_relative)
                elif stat.S_ISREG(child_before.st_mode):
                    entries.append(
                        _windows_file_entry(
                            child_path,
                            child_relative,
                            child_before,
                            state,
                        )
                    )
                else:
                    raise IntegrityError("manifest:non-regular-entry")
                child_after = os.lstat(child_path)
                if _metadata_signature(child_after) != snapshot_before[name]:
                    raise IntegrityError("manifest:entry-changed-during-read")

            snapshot_after = _windows_snapshot(directory, len(snapshot_before))
            _information, identity_after, native_after = _windows_information(handle)
            path_after = os.lstat(directory)
            if (
                snapshot_after != snapshot_before
                or native_after != native_before
                or identity_after != identity
                or _metadata_signature(path_after) != _metadata_signature(path_before)
                or path_after.st_ino != identity[1]
            ):
                raise IntegrityError("manifest:directory-changed-during-read")
            _reject_link_components(directory)
        finally:
            _kernel32.CloseHandle(handle)

    token = _ACTIVE_LIMITS.set(limits)
    try:
        visit(root, Path())
    except (IntegrityError, UnsafePathError):
        raise
    except OSError as exc:
        raise IntegrityError("manifest:stable-traversal-failed") from exc
    finally:
        _ACTIVE_LIMITS.reset(token)
    entries.sort(key=lambda entry: entry["path"])
    directories.sort()
    return entries, directories


def _walk_tree(
    root: Path,
    limits: _TraversalLimits,
) -> tuple[list[dict[str, Any]], list[str]]:
    return _walk_windows(root, limits) if os.name == "nt" else _walk_posix(
        root,
        limits,
    )


def _walk_regular_files(
    root: Path,
    limits: _TraversalLimits,
) -> list[dict[str, Any]]:
    return _walk_tree(root, limits)[0]


def _validated_manifest_root(root: str | os.PathLike[str]) -> Path:
    root_path = _absolute_path(root, "manifest-root")
    _reject_link_components(root_path)
    try:
        metadata = os.lstat(root_path)
    except FileNotFoundError as exc:
        raise IntegrityError("manifest:root-missing") from exc
    except OSError as exc:
        raise IntegrityError("manifest:root-inspection-failed") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise IntegrityError("manifest:root-directory-required")
    return root_path


def _validate_manifest(
    manifest: Any,
    limits: _TraversalLimits,
) -> list[dict[str, Any]]:
    if not isinstance(manifest, list):
        raise ValidationError("manifest:array-required")
    if len(manifest) > limits.max_files:
        raise ValidationError("manifest:file-count-limit")

    validated: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    total_size = 0
    for index, value in enumerate(manifest):
        record = require_exact_fields(
            value,
            MANIFEST_FIELDS,
            label=f"manifest[{index}]",
        )
        path = record["path"]
        if (
            not isinstance(path, str)
            or not path
            or len(path) > MAX_MANIFEST_PATH_LENGTH
            or "\\" in path
            or "\x00" in path
        ):
            raise ValidationError(f"manifest[{index}].path:invalid")
        parsed = PurePosixPath(path)
        if (
            path == "."
            or
            parsed.is_absolute()
            or parsed.as_posix() != path
            or any(part in {"", ".", ".."} for part in parsed.parts)
            or len(parsed.parts) > limits.max_depth
        ):
            raise ValidationError(f"manifest[{index}].path:unsafe")
        if path in seen_paths:
            raise ValidationError("manifest:duplicate-path")
        seen_paths.add(path)

        size = record["size"]
        if type(size) is not int or size < 0:
            raise ValidationError(f"manifest[{index}].size:invalid")
        if size > limits.max_file_size:
            raise ValidationError("manifest:file-size-limit")
        total_size += size
        if total_size > limits.max_total_size:
            raise ValidationError("manifest:total-size-limit")
        digest = record["sha256"]
        if not isinstance(digest, str) or not HASH_PATTERN.fullmatch(digest):
            raise ValidationError(f"manifest[{index}].sha256:invalid")
        validated.append({"path": path, "size": size, "sha256": digest})
    return validated


class IntegrityVerifier:
    """Create and verify deterministic manifests beneath one explicit root."""

    @staticmethod
    def file_manifest(
        root: str | os.PathLike[str],
        *,
        max_depth: int = DEFAULT_MAX_DEPTH,
        max_files: int = DEFAULT_MAX_FILES,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
        max_total_size: int = DEFAULT_MAX_TOTAL_SIZE,
        reject_hardlinks: bool = False,
    ) -> list[dict[str, Any]]:
        limits = _traversal_limits(
            max_depth=max_depth,
            max_files=max_files,
            max_entries=max_entries,
            max_file_size=max_file_size,
            max_total_size=max_total_size,
            reject_hardlinks=reject_hardlinks,
        )
        root_path = _validated_manifest_root(root)
        try:
            return _walk_regular_files(root_path, limits)
        except RecursionError as exc:
            raise IntegrityError("manifest:depth-limit") from exc

    @staticmethod
    def tree_manifest(
        root: str | os.PathLike[str],
        *,
        max_depth: int = DEFAULT_MAX_DEPTH,
        max_files: int = DEFAULT_MAX_FILES,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
        max_total_size: int = DEFAULT_MAX_TOTAL_SIZE,
        reject_hardlinks: bool = False,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Return files and directories from one bounded stable traversal."""

        limits = _traversal_limits(
            max_depth=max_depth,
            max_files=max_files,
            max_entries=max_entries,
            max_file_size=max_file_size,
            max_total_size=max_total_size,
            reject_hardlinks=reject_hardlinks,
        )
        root_path = _validated_manifest_root(root)
        try:
            return _walk_tree(root_path, limits)
        except RecursionError as exc:
            raise IntegrityError("manifest:depth-limit") from exc

    @classmethod
    def verify_manifest(
        cls,
        root: str | os.PathLike[str],
        manifest: Any,
        *,
        max_depth: int = DEFAULT_MAX_DEPTH,
        max_files: int = DEFAULT_MAX_FILES,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
        max_total_size: int = DEFAULT_MAX_TOTAL_SIZE,
        reject_hardlinks: bool = False,
    ) -> bool:
        limits = _traversal_limits(
            max_depth=max_depth,
            max_files=max_files,
            max_entries=max_entries,
            max_file_size=max_file_size,
            max_total_size=max_total_size,
            reject_hardlinks=reject_hardlinks,
        )
        expected = _validate_manifest(manifest, limits)
        observed = cls.file_manifest(
            root,
            max_depth=max_depth,
            max_files=max_files,
            max_entries=max_entries,
            max_file_size=max_file_size,
            max_total_size=max_total_size,
            reject_hardlinks=reject_hardlinks,
        )
        return observed == expected
