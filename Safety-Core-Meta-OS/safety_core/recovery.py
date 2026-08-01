"""Verified, bounded, non-overwriting recovery."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any

from .backup import (
    MAX_ENTRIES,
    MAX_FILES,
    MAX_FILE_SIZE,
    MAX_PATH_DEPTH,
    MAX_TOTAL_SIZE,
    BackupManager,
    reject_linked_path,
)
from .common import utc_now, validate_filesystem_path
from .errors import IntegrityError, RecoveryError, UnsafePathError, ValidationError
from .integrity import IntegrityVerifier


if os.name == "nt":  # pragma: no cover - declarations are platform-specific
    import ctypes
    import msvcrt
    from ctypes import wintypes

    _GENERIC_READ = 0x80000000
    _GENERIC_WRITE = 0x40000000
    _DELETE_ACCESS = 0x00010000
    _FILE_SHARE_READ = 0x00000001
    _FILE_SHARE_WRITE = 0x00000002
    _CREATE_NEW = 1
    _OPEN_EXISTING = 3
    _FILE_ATTRIBUTE_NORMAL = 0x00000080
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
    _kernel32.GetFinalPathNameByHandleW.argtypes = [
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    _kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    _kernel32.SetFileInformationByHandle.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    _kernel32.SetFileInformationByHandle.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL

    class _WindowsFileDisposition(ctypes.Structure):
        _fields_ = [("DeleteFile", wintypes.BOOL)]


def _is_link_like_metadata(metadata: os.stat_result) -> bool:
    if stat.S_ISLNK(metadata.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _path_identity(metadata: os.stat_result) -> tuple[int, int]:
    return (metadata.st_dev, metadata.st_ino)


def _inspect_directory(path: Path) -> os.stat_result:
    try:
        metadata = os.lstat(path)
    except OSError as exc:
        raise RecoveryError("recovery-directory-inspection-failed") from exc
    if _is_link_like_metadata(metadata):
        raise UnsafePathError("recovery-linked-directory-forbidden")
    if not stat.S_ISDIR(metadata.st_mode):
        raise RecoveryError("recovery-directory-required")
    return metadata


def _windows_directory_information(handle: int):
    information = _WindowsFileInformation()
    if not _kernel32.GetFileInformationByHandle(handle, ctypes.byref(information)):
        raise RecoveryError("recovery-directory-handle-inspection-failed")
    if not information.dwFileAttributes & _FILE_ATTRIBUTE_DIRECTORY:
        raise RecoveryError("recovery-directory-required")
    if information.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
        raise UnsafePathError("recovery-linked-directory-forbidden")
    identity = (
        information.dwVolumeSerialNumber,
        (information.nFileIndexHigh << 32) | information.nFileIndexLow,
    )
    return information, identity


def _windows_final_path(handle: int) -> Path:
    required = _kernel32.GetFinalPathNameByHandleW(handle, None, 0, 0)
    if required == 0:
        raise RecoveryError("recovery-directory-final-path-failed")
    buffer = ctypes.create_unicode_buffer(required + 1)
    written = _kernel32.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
    if written == 0 or written >= len(buffer):
        raise RecoveryError("recovery-directory-final-path-failed")
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return Path(os.path.abspath(value))


class _DirectoryGuard:
    """Hold one directory object stable while child paths are created."""

    def __init__(self, path: Path, *, descriptor: int | None = None) -> None:
        self.path = path
        self._descriptor: int | None = descriptor if os.name != "nt" else None
        self._handle: int | None = None
        try:
            before = _inspect_directory(path)
            self.path_identity = _path_identity(before)
            if os.name == "nt":
                handle = _kernel32.CreateFileW(
                    str(path),
                    _GENERIC_READ,
                    _FILE_SHARE_READ | _FILE_SHARE_WRITE,
                    None,
                    _OPEN_EXISTING,
                    _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
                    None,
                )
                if handle == _INVALID_HANDLE_VALUE:
                    raise RecoveryError("recovery-directory-open-failed")
                self._handle = handle
                _information, self._native_identity = _windows_directory_information(
                    handle
                )
                self._operation_path = _windows_final_path(handle)
                after = _inspect_directory(path)
                if (
                    _path_identity(after) != self.path_identity
                    or after.st_ino != self._native_identity[1]
                    or os.path.normcase(os.fspath(self._operation_path))
                    != os.path.normcase(os.path.abspath(os.fspath(path)))
                ):
                    raise RecoveryError("recovery-directory-replaced")
            else:
                flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                flags |= getattr(os, "O_NOFOLLOW", 0)
                if self._descriptor is None:
                    self._descriptor = os.open(path, flags)
                descriptor_metadata = os.fstat(self._descriptor)
                after = _inspect_directory(path)
                if (
                    not stat.S_ISDIR(descriptor_metadata.st_mode)
                    or not os.path.samestat(before, descriptor_metadata)
                    or not os.path.samestat(after, descriptor_metadata)
                ):
                    raise RecoveryError("recovery-directory-replaced")
                self._native_identity = _path_identity(descriptor_metadata)
        except Exception:
            self.close()
            raise

    def verify(self) -> None:
        current = _inspect_directory(self.path)
        if _path_identity(current) != self.path_identity:
            raise RecoveryError("recovery-directory-replaced")
        if os.name == "nt":
            if self._handle is None:
                raise RecoveryError("recovery-directory-guard-closed")
            _information, identity = _windows_directory_information(self._handle)
            final_path = _windows_final_path(self._handle)
            if (
                identity != self._native_identity
                or current.st_ino != identity[1]
                or os.path.normcase(os.fspath(final_path))
                != os.path.normcase(os.path.abspath(os.fspath(self.path)))
            ):
                raise RecoveryError("recovery-directory-replaced")
        else:
            if self._descriptor is None:
                raise RecoveryError("recovery-directory-guard-closed")
            descriptor_metadata = os.fstat(self._descriptor)
            if (
                _path_identity(descriptor_metadata) != self._native_identity
                or not os.path.samestat(current, descriptor_metadata)
            ):
                raise RecoveryError("recovery-directory-replaced")

    def create_directory(self, name: str, path: Path) -> "_DirectoryGuard":
        self.verify()
        try:
            if os.name == "nt":
                operation_path = self._operation_path / name
                os.mkdir(operation_path, 0o700)
                child = _DirectoryGuard(operation_path)
                child.path = path
            else:
                if self._descriptor is None:
                    raise RecoveryError("recovery-directory-guard-closed")
                os.mkdir(name, 0o700, dir_fd=self._descriptor)
                flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                flags |= getattr(os, "O_NOFOLLOW", 0)
                child_descriptor = os.open(name, flags, dir_fd=self._descriptor)
                child = _DirectoryGuard(path, descriptor=child_descriptor)
        except FileExistsError as exc:
            raise RecoveryError("recovery-target-collision") from exc
        except (RecoveryError, UnsafePathError):
            raise
        except OSError as exc:
            raise RecoveryError("recovery-directory-create-failed") from exc
        self.verify()
        return child

    def open_directory(self, name: str, path: Path) -> "_DirectoryGuard":
        self.verify()
        try:
            if os.name == "nt":
                operation_path = self._operation_path / name
                child = _DirectoryGuard(operation_path)
                child.path = path
                child._operation_path = operation_path
            else:
                if self._descriptor is None:
                    raise RecoveryError("recovery-directory-guard-closed")
                flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                flags |= getattr(os, "O_NOFOLLOW", 0)
                child_descriptor = os.open(name, flags, dir_fd=self._descriptor)
                child = _DirectoryGuard(path, descriptor=child_descriptor)
        except (RecoveryError, UnsafePathError):
            raise
        except OSError as exc:
            raise RecoveryError("recovery-directory-open-failed") from exc
        self.verify()
        return child

    def create_file(
        self,
        name: str,
        path: Path,
        *,
        delete_access: bool = False,
    ) -> tuple[int, tuple[int, int]]:
        self.verify()
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor: int | None = None
        native_handle: int | None = None
        try:
            if os.name == "nt":
                operation_path = self._operation_path / name
                native_handle = _kernel32.CreateFileW(
                    str(operation_path),
                    _GENERIC_READ
                    | _GENERIC_WRITE
                    | (_DELETE_ACCESS if delete_access else 0),
                    _FILE_SHARE_READ,
                    None,
                    _CREATE_NEW,
                    _FILE_ATTRIBUTE_NORMAL | _FILE_FLAG_OPEN_REPARSE_POINT,
                    None,
                )
                if native_handle == _INVALID_HANDLE_VALUE:
                    error = ctypes.get_last_error()
                    if error in {80, 183}:
                        raise RecoveryError("recovery-target-collision")
                    raise OSError(error, "CreateFileW failed")
                descriptor = msvcrt.open_osfhandle(
                    native_handle,
                    os.O_RDWR | getattr(os, "O_BINARY", 0),
                )
                native_handle = None
            else:
                if self._descriptor is None:
                    raise RecoveryError("recovery-directory-guard-closed")
                descriptor = os.open(name, flags, 0o600, dir_fd=self._descriptor)
            descriptor_metadata = os.fstat(descriptor)
            path_metadata = os.lstat(
                self._operation_path / name if os.name == "nt" else path
            )
            if (
                not stat.S_ISREG(descriptor_metadata.st_mode)
                or _is_link_like_metadata(path_metadata)
                or getattr(descriptor_metadata, "st_nlink", 1) != 1
                or getattr(path_metadata, "st_nlink", 1) != 1
                or not os.path.samestat(path_metadata, descriptor_metadata)
            ):
                raise RecoveryError("recovery-created-file-invalid")
            self.verify()
            result = descriptor, _path_identity(descriptor_metadata)
            descriptor = None
            return result
        except FileExistsError as exc:
            raise RecoveryError("recovery-target-collision") from exc
        except (RecoveryError, UnsafePathError):
            raise
        except OSError as exc:
            raise RecoveryError("recovery-file-create-failed") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if native_handle is not None and native_handle != _INVALID_HANDLE_VALUE:
                _kernel32.CloseHandle(native_handle)

    def link_file(
        self,
        source_name: str,
        source_path: Path,
        destination_name: str,
        destination_path: Path,
        descriptor: int,
    ) -> None:
        self.verify()
        try:
            descriptor_metadata = os.fstat(descriptor)
            if os.name == "nt":
                operation_source = self._operation_path / source_name
                operation_destination = self._operation_path / destination_name
                source_metadata = os.lstat(operation_source)
                os.link(operation_source, operation_destination)
            else:
                if self._descriptor is None:
                    raise RecoveryError("recovery-directory-guard-closed")
                source_metadata = os.stat(
                    source_name,
                    dir_fd=self._descriptor,
                    follow_symlinks=False,
                )
                os.link(
                    source_name,
                    destination_name,
                    src_dir_fd=self._descriptor,
                    dst_dir_fd=self._descriptor,
                    follow_symlinks=False,
                )
            destination_metadata = os.lstat(
                self._operation_path / destination_name
                if os.name == "nt"
                else destination_path
            )
            source_after = os.lstat(
                self._operation_path / source_name if os.name == "nt" else source_path
            )
            if (
                not os.path.samestat(source_metadata, descriptor_metadata)
                or not os.path.samestat(source_after, descriptor_metadata)
                or not os.path.samestat(destination_metadata, descriptor_metadata)
                or getattr(destination_metadata, "st_nlink", 0) != 2
            ):
                raise RecoveryError("stable-publish-identity-mismatch")
            self.verify()
        except FileExistsError as exc:
            raise RecoveryError("backup-destination-raced") from exc
        except (RecoveryError, UnsafePathError):
            raise
        except OSError as exc:
            raise RecoveryError("backup-publish-failed") from exc

    @staticmethod
    def mark_delete_on_close(descriptor: int) -> None:
        if os.name != "nt":
            raise RecoveryError("delete-on-close-unavailable")
        native_handle = msvcrt.get_osfhandle(descriptor)
        disposition = _WindowsFileDisposition(True)
        if not _kernel32.SetFileInformationByHandle(
            native_handle,
            4,
            ctypes.byref(disposition),
            ctypes.sizeof(disposition),
        ):
            raise RecoveryError("backup-temporary-delete-mark-failed")

    def close(self) -> None:
        if self._descriptor is not None:
            os.close(self._descriptor)
            self._descriptor = None
        if self._handle is not None:
            _kernel32.CloseHandle(self._handle)
            self._handle = None


def _write_all(descriptor: int, content: bytes) -> str:
    digest = hashlib.sha256()
    offset = 0
    view = memoryview(content)
    while offset < len(view):
        written = os.write(descriptor, view[offset : offset + 1024 * 1024])
        if written <= 0:
            raise RecoveryError("recovery-short-write")
        digest.update(view[offset : offset + written])
        offset += written
    os.fsync(descriptor)
    return digest.hexdigest()


def _matches_owned_path(
    path: Path,
    identity: tuple[int, int],
    *,
    directory: bool,
) -> bool:
    try:
        metadata = os.lstat(path)
    except OSError:
        return False
    if _is_link_like_metadata(metadata) or _path_identity(metadata) != identity:
        return False
    return stat.S_ISDIR(metadata.st_mode) if directory else stat.S_ISREG(metadata.st_mode)


def _hash_open_file(descriptor: int) -> tuple[str, os.stat_result]:
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        before = os.fstat(descriptor)
        digest = hashlib.sha256()
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            digest.update(block)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise RecoveryError("recovery-final-read-failed") from exc
    if (
        not stat.S_ISREG(before.st_mode)
        or _path_identity(before) != _path_identity(after)
        or before.st_size != after.st_size
        or getattr(before, "st_mtime_ns", None)
        != getattr(after, "st_mtime_ns", None)
        or getattr(after, "st_nlink", 1) != 1
    ):
        raise RecoveryError("recovery-file-changed-during-verification")
    return digest.hexdigest(), after


def _open_directory_chain(path: Path) -> list[_DirectoryGuard]:
    absolute = Path(os.path.abspath(os.fspath(path)))
    if os.name == "nt":
        reject_linked_path(absolute)
        return [_DirectoryGuard(absolute)]
    if os.name != "nt" and (
        not getattr(os, "O_DIRECTORY", 0)
        or not getattr(os, "O_NOFOLLOW", 0)
        or os.open not in os.supports_dir_fd
        or os.mkdir not in os.supports_dir_fd
    ):
        raise RecoveryError("stable-recovery-unavailable")
    anchor = Path(absolute.anchor)
    if not absolute.anchor or not anchor.is_dir():
        raise RecoveryError("recovery-path-anchor-required")
    guards: list[_DirectoryGuard] = []
    try:
        current_path = anchor
        current = _DirectoryGuard(anchor)
        guards.append(current)
        for component in absolute.relative_to(anchor).parts:
            current_path = current_path / component
            current = current.open_directory(component, current_path)
            guards.append(current)
        return guards
    except Exception:
        for guard in reversed(guards):
            try:
                guard.close()
            except OSError:
                pass
        raise


def _close_resources(
    descriptors: list[int],
    guards: list[_DirectoryGuard],
) -> OSError | None:
    first_error: OSError | None = None
    for descriptor in reversed(descriptors):
        try:
            os.close(descriptor)
        except OSError as exc:
            first_error = first_error or exc
    descriptors.clear()
    for guard in reversed(guards):
        try:
            guard.close()
        except OSError as exc:
            first_error = first_error or exc
    guards.clear()
    return first_error


def _preflight_descriptor_budget(
    files: dict[str, bytes],
    open_guard_count: int,
) -> None:
    """Fail before extraction when stable handles cannot fit the POSIX fd limit."""

    if os.name == "nt":
        return
    try:
        import resource

        soft_limit, _hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    except (ImportError, OSError, ValueError) as exc:
        raise RecoveryError("recovery-file-descriptor-limit-unavailable") from exc
    if soft_limit == resource.RLIM_INFINITY or soft_limit < 0:
        return

    directory_prefixes: set[tuple[str, ...]] = set()
    for relative in files:
        parts = PurePosixPath(relative).parts
        directory_prefixes.update(
            tuple(parts[:depth]) for depth in range(1, len(parts))
        )
    additional_descriptors = len(files) + len(directory_prefixes) + 1

    try:
        current_open = len(os.listdir("/proc/self/fd"))
    except OSError:
        current_open = open_guard_count + 32
    safety_reserve = 16
    if current_open + additional_descriptors + safety_reserve > soft_limit:
        raise RecoveryError("recovery-file-descriptor-limit")


class RecoveryManager:
    """Recover a verified archive into a newly and exclusively created tree."""

    @staticmethod
    def recover(archive_path: Path, destination: Path) -> dict[str, Any]:
        destination_path = validate_filesystem_path(
            destination,
            "recovery-destination",
            RecoveryError,
        )
        target = Path(os.path.abspath(os.fspath(destination_path)))
        if os.path.lexists(target):
            raise RecoveryError("recovery-destination-exists")
        if not target.parent.exists() or not target.parent.is_dir():
            raise RecoveryError("recovery-parent-missing")
        reject_linked_path(target, include_leaf=False)

        written: list[str] = []
        guards: list[_DirectoryGuard] = []
        open_files: list[int] = []
        file_records: list[tuple[int, Path, tuple[int, int], str, int]] = []

        try:
            guards.extend(_open_directory_chain(target.parent))
            parent_guard = guards[-1]
            manifest, files = BackupManager.read_verified(archive_path)
            _preflight_descriptor_budget(files, len(guards))
            expected_hashes = {
                entry["path"]: entry["sha256"] for entry in manifest["files"]
            }
            target_guard = parent_guard.create_directory(target.name, target)
            guards.append(target_guard)
            directory_guards: dict[tuple[str, ...], _DirectoryGuard] = {
                (): target_guard
            }

            for relative, content in sorted(files.items()):
                parts = PurePosixPath(relative).parts
                if len(parts) > 32:
                    raise RecoveryError("recovery-path-depth-limit")
                parent_parts: tuple[str, ...] = ()
                parent = target_guard
                parent_path = target
                for component in parts[:-1]:
                    child_parts = parent_parts + (component,)
                    child_path = parent_path / component
                    child = directory_guards.get(child_parts)
                    if child is None:
                        child = parent.create_directory(component, child_path)
                        guards.append(child)
                        directory_guards[child_parts] = child
                    else:
                        child.verify()
                    parent_parts = child_parts
                    parent = child
                    parent_path = child_path

                output = parent_path / parts[-1]
                descriptor, identity = parent.create_file(parts[-1], output)
                open_files.append(descriptor)
                file_records.append(
                    (
                        descriptor,
                        output,
                        identity,
                        expected_hashes[relative],
                        len(content),
                    )
                )
                observed_hash = _write_all(descriptor, content)
                descriptor_metadata = os.fstat(descriptor)
                path_metadata = os.lstat(output)
                if (
                    observed_hash != expected_hashes[relative]
                    or descriptor_metadata.st_size != len(content)
                    or _path_identity(descriptor_metadata) != identity
                    or getattr(descriptor_metadata, "st_nlink", 1) != 1
                    or not os.path.samestat(path_metadata, descriptor_metadata)
                ):
                    raise RecoveryError("recovery-write-verification-failed")
                parent.verify()
                written.append(relative)

            for guard in guards:
                guard.verify()
            for descriptor, path, identity, expected_hash, expected_size in file_records:
                final_hash, final_metadata = _hash_open_file(descriptor)
                if (
                    final_hash != expected_hash
                    or final_metadata.st_size != expected_size
                    or _path_identity(final_metadata) != identity
                    or not _matches_owned_path(path, identity, directory=False)
                ):
                    raise RecoveryError("recovery-created-file-replaced")

            close_error = _close_resources(open_files, [])
            if close_error is not None:
                raise RecoveryError("recovery-resource-close-failed") from close_error
            try:
                final_manifest, final_directories = IntegrityVerifier.tree_manifest(
                    target,
                    max_depth=MAX_PATH_DEPTH,
                    max_files=MAX_FILES,
                    max_entries=MAX_ENTRIES,
                    max_file_size=MAX_FILE_SIZE,
                    max_total_size=MAX_TOTAL_SIZE,
                    reject_hardlinks=True,
                )
            except (IntegrityError, ValidationError) as exc:
                raise RecoveryError("recovery-final-tree-verification-failed") from exc
            expected_directories = sorted(
                {
                    PurePosixPath(*PurePosixPath(relative).parts[:depth]).as_posix()
                    for relative in files
                    for depth in range(1, len(PurePosixPath(relative).parts))
                }
            )
            if (
                final_manifest != manifest["files"]
                or final_directories != expected_directories
            ):
                raise RecoveryError("recovery-final-tree-mismatch")
            for guard in guards:
                guard.verify()
        except Exception as cause:
            _close_resources(open_files, guards)
            if isinstance(cause, (RecoveryError, UnsafePathError)):
                raise
            if isinstance(cause, OSError):
                raise RecoveryError("recovery-filesystem-operation-failed") from cause
            raise

        close_error = _close_resources(open_files, guards)
        if close_error is not None:
            raise RecoveryError("recovery-resource-close-failed") from close_error
        return {
            "status": "recovered",
            "destination": str(target),
            "files": written,
            "file_count": len(written),
            "recovered_at": utc_now(),
        }
