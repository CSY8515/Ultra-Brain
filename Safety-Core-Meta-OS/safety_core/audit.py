"""Append-only, canonical JSONL safety audit ledger."""

from __future__ import annotations

import copy
import json
import math
import os
import re
import stat
import threading
import unicodedata
from contextlib import contextmanager
from datetime import timezone
from pathlib import Path
from typing import Any

from .common import (
    HASH_PATTERN,
    ZERO_HASH,
    canonical_json,
    parse_timestamp,
    reject_duplicate_keys,
    reject_sensitive_keys,
    require_exact_fields,
    sha256_bytes,
    utc_now,
    validate_filesystem_path,
    validate_identifier,
)
from .errors import LedgerError, ValidationError


AUDIT_FIELDS = {
    "sequence",
    "event_id",
    "event_type",
    "timestamp",
    "data",
    "previous_hash",
    "record_hash",
}

# Public, stable resource ceilings for caller data and persisted ledgers.  The
# byte limits refer to canonical UTF-8 data, a complete JSONL record including
# its trailing newline, and the complete ledger respectively.
MAX_AUDIT_DATA_BYTES = 256 * 1024
MAX_AUDIT_RECORD_BYTES = 512 * 1024
MAX_AUDIT_LEDGER_BYTES = 64 * 1024 * 1024
MAX_AUDIT_RECORDS = 100_000
MAX_AUDIT_DATA_DEPTH = 32
MAX_AUDIT_DATA_NODES = 10_000

_PATH_LOCKS: dict[str, threading.RLock] = {}
_PATH_LOCKS_GUARD = threading.Lock()

try:  # pragma: no cover - platform-specific branch
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

try:  # pragma: no cover - platform-specific branch
    import msvcrt
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None


def _path_lock(path: Path) -> threading.RLock:
    key = os.path.normcase(os.path.abspath(os.fspath(path)))
    with _PATH_LOCKS_GUARD:
        return _PATH_LOCKS.setdefault(key, threading.RLock())


def _posix_nonblocking_flag() -> int:
    return 0 if os.name == "nt" else getattr(os, "O_NONBLOCK", 0)


def _cleanup_failure(code: str, failures: list[Exception]) -> LedgerError | None:
    if not failures:
        return None
    error = LedgerError(code)
    error.__cause__ = failures[0]
    if len(failures) > 1:
        error.add_note(f"{len(failures)} cleanup operations failed")
    return error


def _finish_after_cleanup(
    primary: BaseException | None,
    cleanup: LedgerError | None,
) -> None:
    if primary is not None:
        if cleanup is not None:
            primary.add_note(str(cleanup))
        raise primary.with_traceback(primary.__traceback__)
    if cleanup is not None:
        raise cleanup


def _cleanup_descriptor(descriptor: int | None, code: str) -> LedgerError | None:
    if descriptor is None:
        return None
    failures: list[Exception] = []
    try:
        os.close(descriptor)
    except Exception as exc:  # close failures must cross the public boundary typed
        failures.append(exc)
    return _cleanup_failure(code, failures)


def _cleanup_read_resources(stream: Any, descriptor: int | None) -> LedgerError | None:
    failures: list[Exception] = []
    if stream is not None:
        try:
            stream.close()
        except Exception as exc:
            failures.append(exc)
    if descriptor is not None:
        try:
            os.close(descriptor)
        except Exception as exc:
            failures.append(exc)
    return _cleanup_failure("ledger:read-cleanup-failed", failures)


def _cleanup_process_lock(descriptor: int | None, locked: bool) -> LedgerError | None:
    failures: list[Exception] = []
    if descriptor is not None and locked:
        try:
            if msvcrt is not None:
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            elif fcntl is not None:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        except Exception as exc:
            failures.append(exc)
    if descriptor is not None:
        try:
            os.close(descriptor)
        except Exception as exc:
            failures.append(exc)
    return _cleanup_failure("ledger:process-lock-cleanup-failed", failures)


def _preflight_lock_path(lock_path: Path) -> None:
    for component in reversed([lock_path.parent, *lock_path.parent.parents]):
        try:
            metadata = os.lstat(component)
        except OSError as exc:
            raise LedgerError("ledger:lock-parent-unavailable") from exc
        if _metadata_is_link_like(metadata):
            raise LedgerError("ledger:lock-parent-link-forbidden")
    try:
        parent_metadata = os.lstat(lock_path.parent)
    except OSError as exc:
        raise LedgerError("ledger:lock-parent-unavailable") from exc
    if not stat.S_ISDIR(parent_metadata.st_mode):
        raise LedgerError("ledger:lock-parent-directory-required")
    try:
        lock_metadata = os.lstat(lock_path)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LedgerError("ledger:lock-inspection-failed") from exc
    if _metadata_is_link_like(lock_metadata):
        raise LedgerError("ledger:lock-link-forbidden")
    if not stat.S_ISREG(lock_metadata.st_mode):
        raise LedgerError("ledger:lock-not-regular")


@contextmanager
def _process_lock(ledger_path: Path):
    lock_path = ledger_path.with_name(f".{ledger_path.name}.lock")
    _preflight_lock_path(lock_path)
    flags = os.O_RDWR | getattr(os, "O_BINARY", 0) | _posix_nonblocking_flag()
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    locked = False
    created = False
    primary: BaseException | None = None
    try:
        try:
            descriptor = os.open(lock_path, flags | os.O_CREAT | os.O_EXCL, 0o600)
            created = True
        except FileExistsError:
            _preflight_lock_path(lock_path)
            descriptor = os.open(lock_path, flags)

        _validate_lock_identity(
            lock_path,
            descriptor,
            require_initialized=not created,
        )
        _preflight_lock_path(lock_path)
        if created:
            if os.write(descriptor, b"\0") != 1:
                raise LedgerError("ledger:lock-initialization-failed")
            os.fsync(descriptor)
            _validate_lock_identity(lock_path, descriptor, require_initialized=True)
        if msvcrt is not None:
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)
        elif fcntl is not None:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
        else:  # pragma: no cover - unsupported Python platform
            raise LedgerError("ledger:process-lock-unavailable")
        locked = True
        _validate_lock_identity(lock_path, descriptor, require_initialized=True)
        yield
        _validate_lock_identity(lock_path, descriptor, require_initialized=True)
    except LedgerError as exc:
        primary = exc
    except OSError as exc:
        primary = LedgerError("ledger:process-lock-failed")
        primary.__cause__ = exc
    except BaseException as exc:
        primary = exc
    cleanup = _cleanup_process_lock(descriptor, locked)
    _finish_after_cleanup(primary, cleanup)


def _metadata_is_link_like(metadata: os.stat_result) -> bool:
    if stat.S_ISLNK(metadata.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _ledger_signature(metadata: os.stat_result) -> tuple[Any, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        getattr(metadata, "st_mtime_ns", None),
        getattr(metadata, "st_nlink", None),
    )


def _validate_lock_identity(
    lock_path: Path,
    descriptor: int,
    *,
    require_initialized: bool,
) -> os.stat_result:
    try:
        path_metadata = os.lstat(lock_path)
        descriptor_metadata = os.fstat(descriptor)
    except OSError as exc:
        raise LedgerError("ledger:lock-inspection-failed") from exc
    if (
        _metadata_is_link_like(path_metadata)
        or _metadata_is_link_like(descriptor_metadata)
    ):
        raise LedgerError("ledger:lock-link-forbidden")
    if (
        not stat.S_ISREG(path_metadata.st_mode)
        or not stat.S_ISREG(descriptor_metadata.st_mode)
    ):
        raise LedgerError("ledger:lock-not-regular")
    if (
        getattr(path_metadata, "st_nlink", 1) != 1
        or getattr(descriptor_metadata, "st_nlink", 1) != 1
    ):
        raise LedgerError("ledger:lock-hardlink-forbidden")
    if not os.path.samestat(path_metadata, descriptor_metadata):
        raise LedgerError("ledger:lock-replaced")
    if require_initialized and descriptor_metadata.st_size < 1:
        raise LedgerError("ledger:lock-uninitialized")
    return descriptor_metadata


def _is_link_like(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise LedgerError("ledger:path-inspection-failed") from exc
    return _metadata_is_link_like(metadata)


def _canonical_timestamp(value: Any, label: str) -> str:
    parsed = parse_timestamp(value, label).astimezone(timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def _record_hash(record: dict[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "record_hash"}
    return sha256_bytes(canonical_json(body).encode("utf-8"))


def _json_string_size(value: str, maximum: int) -> int:
    size = 2
    if size > maximum:
        raise ValidationError("audit-data:size-limit")
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ValidationError("audit-data:invalid-unicode-scalar")
        if character in {'"', "\\"} or character in "\b\f\n\r\t":
            size += 2
        elif codepoint < 0x20:
            size += 6
        elif codepoint < 0x80:
            size += 1
        elif codepoint < 0x800:
            size += 2
        elif codepoint < 0x10000:
            size += 3
        else:
            size += 4
        if size > maximum:
            raise ValidationError("audit-data:size-limit")
    return size


def _preflight_audit_data(value: dict[str, Any]) -> int:
    """Bound traversal and canonical UTF-8 size before JSON serialization."""

    nodes = 0
    estimated_size = 0
    active_containers: set[int] = set()

    def consume(size: int) -> None:
        nonlocal estimated_size
        estimated_size += size
        if estimated_size > MAX_AUDIT_DATA_BYTES:
            raise ValidationError("audit-data:size-limit")

    def visit(item: Any, depth: int) -> None:
        nonlocal nodes
        if depth > MAX_AUDIT_DATA_DEPTH:
            raise ValidationError("audit-data:depth-limit")
        nodes += 1
        if nodes > MAX_AUDIT_DATA_NODES:
            raise ValidationError("audit-data:node-limit")

        item_type = type(item)
        if item is None:
            consume(4)
            return
        if item_type is bool:
            consume(4 if item else 5)
            return
        if item_type is int:
            bits = item.bit_length()
            upper_digits = max(1, (bits * 30103 + 99_999) // 100_000)
            upper_size = upper_digits + (1 if item < 0 else 0)
            if upper_size > MAX_AUDIT_DATA_BYTES:
                raise ValidationError("audit-data:size-limit")
            try:
                consume(len(str(item)))
            except (ValueError, OverflowError) as exc:
                raise ValidationError("audit-data:invalid-number") from exc
            return
        if item_type is float:
            if not math.isfinite(item):
                raise ValidationError("audit-data:invalid-number")
            encoded_number = json.dumps(
                item,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")
            consume(len(encoded_number))
            return
        if item_type is str:
            consume(_json_string_size(item, MAX_AUDIT_DATA_BYTES - estimated_size))
            return
        if item_type is dict:
            identity = id(item)
            if identity in active_containers:
                raise ValidationError("audit-data:cyclic-value")
            active_containers.add(identity)
            try:
                consume(2)
                for index, (key, child) in enumerate(item.items()):
                    if type(key) is not str:
                        raise ValidationError("audit-data:object-key-not-string")
                    nodes += 1
                    if nodes > MAX_AUDIT_DATA_NODES:
                        raise ValidationError("audit-data:node-limit")
                    if index:
                        consume(1)
                    key_size = _json_string_size(
                        key, MAX_AUDIT_DATA_BYTES - estimated_size - 1
                    )
                    consume(key_size + 1)
                    visit(child, depth + 1)
            finally:
                active_containers.remove(identity)
            return
        if item_type is list:
            identity = id(item)
            if identity in active_containers:
                raise ValidationError("audit-data:cyclic-value")
            active_containers.add(identity)
            try:
                consume(2)
                for index, child in enumerate(item):
                    if index:
                        consume(1)
                    visit(child, depth + 1)
            finally:
                active_containers.remove(identity)
            return
        raise ValidationError("audit-data:unsupported-json-type")

    visit(value, 0)
    return estimated_size


def _reject_raw_payload_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            compatibility_key = unicodedata.normalize("NFKC", str(key))
            camel_separated = re.sub(
                r"(?<=[a-z0-9])(?=[A-Z])", "-", compatibility_key
            )
            normalized = re.sub(
                r"[^a-z0-9]+", "-", camel_separated.casefold()
            ).strip("-")
            compact = normalized.replace("-", "")
            if "payload" in normalized.split("-") or "payload" in compact:
                raise ValidationError("audit-data:raw-payload-forbidden")
            _reject_raw_payload_keys(item)
    elif isinstance(value, list):
        for item in value:
            _reject_raw_payload_keys(item)


class AuditLedger:
    """A process-synchronized JSONL hash chain.

    Verification establishes internal continuity. Detecting replacement of the
    entire ledger or removal from its tail requires both ``expected_head`` and
    ``expected_count`` obtained from an independent, revision-addressed source.
    """

    def __init__(self, path: str | os.PathLike[str]) -> None:
        try:
            raw = os.fspath(
                validate_filesystem_path(path, "ledger", ValidationError)
            )
            self.path = Path(os.path.abspath(raw))
        except (OSError, TypeError, ValueError) as exc:
            if isinstance(exc, ValidationError):
                raise
            raise ValidationError("ledger:invalid-path") from exc
        self._lock = _path_lock(self.path)
        try:
            metadata = os.lstat(self.path)
        except FileNotFoundError:
            self._trusted_count: int | None = 0
            self._trusted_head: str | None = ZERO_HASH
        except OSError as exc:
            raise LedgerError("ledger:path-inspection-failed") from exc
        else:
            self._trusted_count = None
            self._trusted_head = None

    def _check_path(self, *, require_exists: bool) -> None:
        for component in reversed([self.path, *self.path.parents]):
            if _is_link_like(component):
                raise LedgerError("ledger:symlink-forbidden")
        parent = self.path.parent
        try:
            parent_metadata = os.lstat(parent)
        except OSError as exc:
            raise LedgerError("ledger:parent-unavailable") from exc
        if not stat.S_ISDIR(parent_metadata.st_mode):
            raise LedgerError("ledger:parent-directory-required")
        try:
            metadata = os.lstat(self.path)
        except FileNotFoundError:
            if require_exists:
                raise LedgerError("ledger:missing")
            return
        except OSError as exc:
            raise LedgerError("ledger:path-inspection-failed") from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise LedgerError("ledger:regular-file-required")
        if getattr(metadata, "st_nlink", 1) != 1:
            raise LedgerError("ledger:hardlink-forbidden")

    @contextmanager
    def _open_readonly(self):
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | _posix_nonblocking_flag()
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor: int | None = None
        stream = None
        primary: BaseException | None = None
        try:
            path_before = os.lstat(self.path)
            descriptor = os.open(self.path, flags)
            metadata = os.fstat(descriptor)
            path_after = os.lstat(self.path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or getattr(metadata, "st_nlink", 1) != 1
                or getattr(path_after, "st_nlink", 1) != 1
                or not os.path.samestat(path_before, metadata)
                or not os.path.samestat(path_after, metadata)
            ):
                raise LedgerError("ledger:file-replaced")
            if metadata.st_size > MAX_AUDIT_LEDGER_BYTES:
                raise LedgerError("ledger:size-limit")
            stream = os.fdopen(descriptor, "rb", closefd=False)
            yield stream, metadata
            descriptor_after = os.fstat(descriptor)
            path_final = os.lstat(self.path)
            if (
                _ledger_signature(descriptor_after) != _ledger_signature(metadata)
                or not os.path.samestat(path_final, descriptor_after)
                or getattr(path_final, "st_nlink", 1) != 1
            ):
                raise LedgerError("ledger:file-changed-during-read")
        except LedgerError as exc:
            primary = exc
        except OSError as exc:
            primary = LedgerError("ledger:read-failed")
            primary.__cause__ = exc
        except BaseException as exc:
            primary = exc
        cleanup = _cleanup_read_resources(stream, descriptor)
        _finish_after_cleanup(primary, cleanup)

    def _load_verified(
        self,
        *,
        require_exists: bool,
    ) -> tuple[list[dict[str, Any]], os.stat_result | None]:
        self._check_path(require_exists=require_exists)
        if not os.path.lexists(self.path):
            if require_exists:
                raise LedgerError("ledger:missing")
            return [], None

        records: list[dict[str, Any]] = []
        previous_hash = ZERO_HASH
        previous_timestamp = None
        event_ids: set[str] = set()
        try:
            with self._open_readonly() as (stream, verified_metadata):
                expected_sequence = 1
                total_bytes = 0
                while True:
                    raw_line = stream.readline(MAX_AUDIT_RECORD_BYTES + 1)
                    if not raw_line:
                        break
                    total_bytes += len(raw_line)
                    if total_bytes > MAX_AUDIT_LEDGER_BYTES:
                        raise LedgerError("ledger:size-limit")
                    if len(raw_line) > MAX_AUDIT_RECORD_BYTES:
                        raise LedgerError("ledger:record-size-limit")
                    if expected_sequence > MAX_AUDIT_RECORDS:
                        raise LedgerError("ledger:record-count-limit")
                    if not raw_line.endswith(b"\n") or raw_line == b"\n":
                        raise LedgerError("ledger:malformed-record")
                    try:
                        line = raw_line[:-1].decode("utf-8")
                        record = json.loads(
                            line,
                            object_pairs_hook=reject_duplicate_keys,
                            parse_constant=lambda _value: (_ for _ in ()).throw(
                                ValidationError("audit-record:invalid-number")
                            ),
                        )
                    except (
                        UnicodeDecodeError,
                        json.JSONDecodeError,
                        ValidationError,
                        ValueError,
                        OverflowError,
                        RecursionError,
                    ) as exc:
                        raise LedgerError("ledger:malformed-record") from exc

                    try:
                        record = require_exact_fields(
                            record,
                            AUDIT_FIELDS,
                            label="audit-record",
                        )
                        sequence = record["sequence"]
                        if type(sequence) is not int or sequence != expected_sequence:
                            raise ValidationError("audit-record:invalid-sequence")
                        event_id = validate_identifier(record["event_id"], "event-id")
                        validate_identifier(record["event_type"], "event-type")
                        if event_id in event_ids:
                            raise ValidationError("audit-record:duplicate-event-id")
                        event_ids.add(event_id)
                        if not isinstance(record["data"], dict):
                            raise ValidationError("audit-record:data-object-required")
                        _preflight_audit_data(record["data"])
                        serialized_data = canonical_json(record["data"])
                        if len(serialized_data.encode("utf-8")) > MAX_AUDIT_DATA_BYTES:
                            raise ValidationError("audit-data:size-limit")
                        reject_sensitive_keys(record["data"], "audit-data")
                        _reject_raw_payload_keys(record["data"])
                        timestamp = _canonical_timestamp(record["timestamp"], "audit-record")
                        if timestamp != record["timestamp"]:
                            raise ValidationError("audit-record:timestamp-not-canonical-utc")
                        parsed_timestamp = parse_timestamp(timestamp, "audit-record")
                        if previous_timestamp is not None and parsed_timestamp < previous_timestamp:
                            raise ValidationError("audit-record:timestamp-out-of-order")
                        previous_timestamp = parsed_timestamp
                        if record["previous_hash"] != previous_hash:
                            raise ValidationError("audit-record:previous-hash-mismatch")
                        record_digest = record["record_hash"]
                        if (
                            not isinstance(record_digest, str)
                            or not HASH_PATTERN.fullmatch(record_digest)
                            or record_digest != _record_hash(record)
                        ):
                            raise ValidationError("audit-record:hash-mismatch")
                        if canonical_json(record) != line:
                            raise ValidationError("audit-record:noncanonical-json")
                    except ValidationError as exc:
                        raise LedgerError("ledger:verification-failed") from exc

                    previous_hash = record["record_hash"]
                    records.append(record)
                    expected_sequence += 1
        except LedgerError:
            raise
        except OSError as exc:
            raise LedgerError("ledger:read-failed") from exc
        return records, verified_metadata

    def append(
        self,
        event_id: Any,
        event_type: Any,
        data: Any,
        timestamp: Any = None,
    ) -> dict[str, Any]:
        event_id = validate_identifier(event_id, "event-id")
        event_type = validate_identifier(event_type, "event-type")
        if type(data) is not dict:
            raise ValidationError("audit-data:object-required")
        _preflight_audit_data(data)
        serialized_data = canonical_json(data)
        if len(serialized_data.encode("utf-8")) > MAX_AUDIT_DATA_BYTES:
            raise ValidationError("audit-data:size-limit")
        safe_data = json.loads(
            serialized_data,
            object_pairs_hook=reject_duplicate_keys,
        )
        reject_sensitive_keys(safe_data, "audit-data")
        _reject_raw_payload_keys(safe_data)
        supplied_timestamp = (
            None if timestamp is None else _canonical_timestamp(timestamp, "audit-event")
        )

        self._check_path(require_exists=False)
        with self._lock, _process_lock(self.path):
            records, verified_metadata = self._load_verified(require_exists=False)
            normalized_timestamp = (
                utc_now() if supplied_timestamp is None else supplied_timestamp
            )
            actual_count = len(records)
            actual_head = records[-1]["record_hash"] if records else ZERO_HASH
            if self._trusted_count is None or self._trusted_head is None:
                raise LedgerError("ledger:external-anchor-required")
            if (
                actual_count != self._trusted_count
                or actual_head != self._trusted_head
            ):
                raise LedgerError("ledger:trusted-anchor-mismatch")
            if actual_count >= MAX_AUDIT_RECORDS:
                raise LedgerError("ledger:record-count-limit")
            if any(record["event_id"] == event_id for record in records):
                raise LedgerError("ledger:duplicate-event-id")
            if records:
                last_timestamp = parse_timestamp(records[-1]["timestamp"], "audit-record")
                if parse_timestamp(normalized_timestamp, "audit-event") < last_timestamp:
                    raise ValidationError("audit-event:timestamp-out-of-order")
            record: dict[str, Any] = {
                "sequence": len(records) + 1,
                "event_id": event_id,
                "event_type": event_type,
                "timestamp": normalized_timestamp,
                "data": safe_data,
                "previous_hash": records[-1]["record_hash"] if records else ZERO_HASH,
            }
            record["record_hash"] = _record_hash(record)
            encoded = (canonical_json(record) + "\n").encode("utf-8")
            if len(encoded) > MAX_AUDIT_RECORD_BYTES:
                raise ValidationError("audit-record:size-limit")
            current_size = 0 if verified_metadata is None else verified_metadata.st_size
            if current_size + len(encoded) > MAX_AUDIT_LEDGER_BYTES:
                raise LedgerError("ledger:size-limit")

            self._check_path(require_exists=False)
            try:
                path_before = os.lstat(self.path)
            except FileNotFoundError:
                path_before = None
            except OSError as exc:
                raise LedgerError("ledger:path-inspection-failed") from exc

            if verified_metadata is None:
                if path_before is not None:
                    raise LedgerError("ledger:file-appeared-after-verification")
            elif path_before is None:
                raise LedgerError("ledger:file-disappeared-after-verification")
            elif _ledger_signature(path_before) != _ledger_signature(
                verified_metadata
            ):
                raise LedgerError("ledger:file-changed-after-verification")

            flags = (
                os.O_WRONLY
                | os.O_APPEND
                | getattr(os, "O_BINARY", 0)
                | _posix_nonblocking_flag()
            )
            if path_before is None:
                flags |= os.O_CREAT | os.O_EXCL
            flags |= getattr(os, "O_NOFOLLOW", 0)
            descriptor: int | None = None
            append_primary: BaseException | None = None
            try:
                descriptor = os.open(self.path, flags, 0o600)
                metadata = os.fstat(descriptor)
                path_after = os.lstat(self.path)
                if (
                    not stat.S_ISREG(metadata.st_mode)
                    or getattr(metadata, "st_nlink", 1) != 1
                    or getattr(path_after, "st_nlink", 1) != 1
                    or not os.path.samestat(path_after, metadata)
                    or (
                        path_before is not None
                        and _ledger_signature(path_before)
                        != _ledger_signature(metadata)
                    )
                ):
                    raise LedgerError("ledger:regular-file-required")
                if metadata.st_size != current_size:
                    raise LedgerError("ledger:file-changed-after-verification")
                if metadata.st_size + len(encoded) > MAX_AUDIT_LEDGER_BYTES:
                    raise LedgerError("ledger:size-limit")
                offset = 0
                while offset < len(encoded):
                    written = os.write(descriptor, encoded[offset:])
                    if written <= 0:
                        raise LedgerError("ledger:short-write")
                    offset += written
                os.fsync(descriptor)
                path_final = os.lstat(self.path)
                metadata_final = os.fstat(descriptor)
                if (
                    getattr(metadata_final, "st_nlink", 1) != 1
                    or not os.path.samestat(path_final, metadata_final)
                    or not os.path.samestat(metadata, metadata_final)
                ):
                    raise LedgerError("ledger:file-replaced-during-append")
            except LedgerError as exc:
                append_primary = exc
            except OSError as exc:
                append_primary = LedgerError("ledger:append-failed")
                append_primary.__cause__ = exc
            except BaseException as exc:
                append_primary = exc
            append_cleanup = _cleanup_descriptor(
                descriptor, "ledger:append-cleanup-failed"
            )
            _finish_after_cleanup(append_primary, append_cleanup)

            persisted_records, _persisted_metadata = self._load_verified(
                require_exists=True
            )
            if (
                len(persisted_records) != record["sequence"]
                or not persisted_records
                or persisted_records[-1]["record_hash"] != record["record_hash"]
            ):
                raise LedgerError("ledger:append-not-durable")
        self._trusted_count = record["sequence"]
        self._trusted_head = record["record_hash"]
        return copy.deepcopy(record)

    def verify(
        self,
        expected_count: Any = None,
        expected_head: Any = None,
    ) -> bool:
        if (expected_count is None) != (expected_head is None):
            raise ValidationError("ledger:complete-anchor-required")
        if expected_count is not None and (
            type(expected_count) is not int or expected_count < 0
        ):
            raise ValidationError("ledger:invalid-expected-count")
        if expected_head is not None and (
            not isinstance(expected_head, str)
            or not HASH_PATTERN.fullmatch(expected_head)
        ):
            raise ValidationError("ledger:invalid-expected-head")

        self._check_path(require_exists=True)
        with self._lock, _process_lock(self.path):
            records, _verified_metadata = self._load_verified(require_exists=True)
            actual_head = records[-1]["record_hash"] if records else ZERO_HASH
            if expected_count is not None:
                if len(records) != expected_count:
                    raise LedgerError("ledger:count-mismatch")
                if actual_head != expected_head:
                    raise LedgerError("ledger:head-mismatch")
                self._trusted_count = expected_count
                self._trusted_head = expected_head
            else:
                if self._trusted_count is None or self._trusted_head is None:
                    raise LedgerError("ledger:external-anchor-required")
                if (
                    len(records) != self._trusted_count
                    or actual_head != self._trusted_head
                ):
                    raise LedgerError("ledger:trusted-anchor-mismatch")
            return True

    def query(self, event_type: Any = None) -> list[dict[str, Any]]:
        if event_type is not None:
            event_type = validate_identifier(event_type, "event-type")
        self._check_path(require_exists=True)
        with self._lock, _process_lock(self.path):
            records, _verified_metadata = self._load_verified(require_exists=True)
            actual_head = records[-1]["record_hash"] if records else ZERO_HASH
            if self._trusted_count is None or self._trusted_head is None:
                raise LedgerError("ledger:external-anchor-required")
            if (
                len(records) != self._trusted_count
                or actual_head != self._trusted_head
            ):
                raise LedgerError("ledger:trusted-anchor-mismatch")
            selected = (
                records
                if event_type is None
                else [record for record in records if record["event_type"] == event_type]
            )
            return copy.deepcopy(selected)
