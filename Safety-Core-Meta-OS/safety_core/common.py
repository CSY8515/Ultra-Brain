"""Shared canonicalization and strict input helpers."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import unicodedata
from datetime import datetime, timezone
from os import PathLike
from pathlib import Path
from typing import Any, Iterable

from .errors import ValidationError


CONTRACT_VERSION = "0.2.0"
ZERO_HASH = "0" * 64
MAX_IDENTIFIER_LENGTH = 100
MAX_COLLECTION_ITEMS = 64
MAX_JSON_DOCUMENT_BYTES = 1024 * 1024
MAX_SENSITIVE_SCAN_NODES = 10_000
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")
SENSITIVE_KEY_PARTS = {
    "api-key",
    "apikey",
    "authorization",
    "credential",
    "password",
    "private-key",
    "secret",
    "session",
    "token",
}


def _security_key_fingerprint(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^a-z0-9]+", "", normalized)


SENSITIVE_KEY_FINGERPRINTS = frozenset(
    _security_key_fingerprint(value) for value in SENSITIVE_KEY_PARTS
)
WINDOWS_INVALID_PATH_CHARACTERS = frozenset('<>:"|?*')
WINDOWS_RESERVED_PATH_NAMES = {
    "con",
    "conin$",
    "conout$",
    "prn",
    "aux",
    "nul",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}


class DuplicateKeyError(ValidationError):
    """Raised when strict JSON contains a duplicate object key."""


def reject_duplicate_keys(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate-key:{key}")
        result[key] = value
    return result


def _open_json_readonly(path: Path, flags: int) -> int:
    """Open JSON while denying concurrent writers where Windows supports it."""

    if os.name != "nt":
        return os.open(path, flags)

    import ctypes
    import msvcrt

    generic_read = 0x80000000
    file_share_read = 0x00000001
    open_existing = 3
    file_attribute_normal = 0x00000080
    file_flag_sequential_scan = 0x08000000
    file_flag_open_reparse_point = 0x00200000
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    create_file.restype = ctypes.c_void_p
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_int
    handle = create_file(
        str(path),
        generic_read,
        file_share_read,
        None,
        open_existing,
        file_attribute_normal
        | file_flag_sequential_scan
        | file_flag_open_reparse_point,
        None,
    )
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return msvcrt.open_osfhandle(
            handle,
            os.O_RDONLY | getattr(os, "O_BINARY", 0),
        )
    except BaseException:
        close_handle(handle)
        raise


def load_json_strict(path: Path) -> Any:
    """Load one bounded, stable, regular UTF-8 JSON document."""

    descriptor: int | None = None
    document_bytes: bytes | None = None
    primary: BaseException | None = None
    try:
        validated_path = validate_filesystem_path(path, "json", ValidationError)
        json_path = Path(os.path.abspath(os.fspath(validated_path)))
        before = os.lstat(json_path)
        if not stat.S_ISREG(before.st_mode):
            raise ValidationError("json:regular-file-required")
        if getattr(before, "st_nlink", 1) != 1:
            raise ValidationError("json:hardlink-forbidden")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        if os.name == "posix":
            flags |= getattr(os, "O_NONBLOCK", 0)
        descriptor = _open_json_readonly(json_path, flags)
        opened = os.fstat(descriptor)
        after_open = os.lstat(json_path)
        if (
            not stat.S_ISREG(opened.st_mode)
            or getattr(opened, "st_nlink", 1) != 1
            or getattr(after_open, "st_nlink", 1) != 1
            or not os.path.samestat(before, opened)
            or not os.path.samestat(after_open, opened)
        ):
            raise ValidationError("json:file-replaced")
        if opened.st_size > MAX_JSON_DOCUMENT_BYTES:
            raise ValidationError("json:size-limit")

        def read_once() -> bytes:
            blocks: list[bytes] = []
            total = 0
            while total <= MAX_JSON_DOCUMENT_BYTES:
                block = os.read(
                    descriptor,
                    min(64 * 1024, MAX_JSON_DOCUMENT_BYTES + 1 - total),
                )
                if not block:
                    break
                blocks.append(block)
                total += len(block)
            if total > MAX_JSON_DOCUMENT_BYTES:
                raise ValidationError("json:size-limit")
            return b"".join(blocks)

        first_read = read_once()
        os.lseek(descriptor, 0, os.SEEK_SET)
        second_read = read_once()
        if first_read != second_read:
            raise ValidationError("json:file-changed-during-read")

        final_descriptor = os.fstat(descriptor)
        final_path = os.lstat(json_path)
        if (
            not os.path.samestat(opened, final_descriptor)
            or not os.path.samestat(final_path, final_descriptor)
            or getattr(final_descriptor, "st_nlink", 1) != 1
            or final_descriptor.st_size != opened.st_size
            or getattr(final_descriptor, "st_mtime_ns", None)
            != getattr(opened, "st_mtime_ns", None)
            or (
                os.name == "posix"
                and getattr(final_descriptor, "st_ctime_ns", None)
                != getattr(opened, "st_ctime_ns", None)
            )
        ):
            raise ValidationError("json:file-changed-during-read")
        document_bytes = first_read
    except ValidationError as exc:
        primary = exc
    except (OSError, ValueError, OverflowError, RecursionError, TypeError) as exc:
        primary = ValidationError("invalid-json-value")
        primary.__cause__ = exc
    except BaseException as exc:
        primary = exc

    close_error: OSError | None = None
    if descriptor is not None:
        try:
            os.close(descriptor)
        except OSError as exc:
            close_error = exc
    if primary is not None:
        if close_error is not None:
            if isinstance(primary, Exception):
                combined = ValidationError("json:operation-and-close-failed")
                combined.__cause__ = ExceptionGroup(
                    "JSON operation and descriptor cleanup both failed",
                    [primary, close_error],
                )
                raise combined
            primary.add_note("JSON descriptor cleanup also failed")
        raise primary
    if close_error is not None:
        raise ValidationError("json:close-failed") from close_error
    if document_bytes is None:
        raise ValidationError("invalid-json-value")

    try:
        document = document_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError("json-not-utf8") from exc
    try:
        loaded = json.loads(
            document,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValidationError(f"invalid-number:{value}")
            ),
        )
        _validate_json_value(loaded)
        return loaded
    except ValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid-json:{exc.msg}") from exc
    except (ValueError, OverflowError, RecursionError, TypeError) as exc:
        raise ValidationError("invalid-json-value") from exc


def canonical_json(value: Any) -> str:
    try:
        _validate_json_value(value)
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except ValidationError:
        raise
    except (ValueError, OverflowError, RecursionError, TypeError) as exc:
        raise ValidationError("value-not-canonical-json") from exc


def _validate_json_value(value: Any, depth: int = 0) -> None:
    if depth > 32:
        raise ValidationError("value-too-deep")
    if value is None or type(value) in (bool, int):
        return
    if type(value) is str:
        validate_unicode_string(value)
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValidationError("number-not-finite")
        return
    if type(value) is list:
        for item in value:
            _validate_json_value(item, depth + 1)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValidationError("object-key-not-string")
            validate_unicode_string(key)
            _validate_json_value(item, depth + 1)
        return
    raise ValidationError(f"unsupported-json-type:{type(value).__name__}")


def validate_unicode_string(value: Any, label: str | None = None) -> str:
    if type(value) is not str:
        prefix = "value" if label is None else label
        raise ValidationError(f"{prefix}:string-required")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        if label is None:
            raise ValidationError("invalid-unicode-scalar")
        raise ValidationError(f"{label}:invalid-unicode-scalar")
    return value


def validate_filesystem_path(
    value: Any,
    label: str,
    error_type: type[ValidationError] = ValidationError,
) -> Path:
    """Return a lexical path after cross-platform unsafe-name rejection."""

    if not isinstance(value, (str, PathLike)):
        raise error_type(f"{label}:path-required")
    try:
        raw = os.fspath(value)
    except Exception as exc:
        raise error_type(f"{label}:invalid-path") from exc
    if type(raw) is not str or not raw or "\x00" in raw:
        raise error_type(f"{label}:invalid-path")
    try:
        validate_unicode_string(raw)
        path = Path(raw)
    except ValidationError as exc:
        raise error_type(f"{label}:invalid-path") from exc
    except (TypeError, ValueError, OSError) as exc:
        raise error_type(f"{label}:invalid-path") from exc
    if path.drive and not path.root:
        raise error_type(f"{label}:drive-relative-path")
    anchor = path.anchor
    for part in path.parts:
        if part == anchor:
            continue
        if part in {"", ".", ".."}:
            raise error_type(f"{label}:unsafe-component")
        if any(ord(character) < 32 for character in part):
            raise error_type(f"{label}:control-character")
        if any(character in WINDOWS_INVALID_PATH_CHARACTERS for character in part):
            raise error_type(f"{label}:windows-invalid-character")
        if part.endswith((" ", ".")):
            raise error_type(f"{label}:windows-ambiguous-component")
        if part.split(".", 1)[0].casefold() in WINDOWS_RESERVED_PATH_NAMES:
            raise error_type(f"{label}:windows-reserved-component")
    return path


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any, label: str) -> datetime:
    if type(value) is not str or not value:
        raise ValidationError(f"{label}:timestamp-required")
    if len(value) > 64:
        raise ValidationError(f"{label}:invalid-timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError(f"{label}:invalid-timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValidationError(f"{label}:timezone-required")
    return parsed


def canonical_timestamp(value: Any, label: str) -> str:
    return (
        parse_timestamp(value, label)
        .astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def validate_identifier(value: Any, label: str = "id") -> str:
    if type(value) is not str:
        raise ValidationError(f"{label}:invalid-identifier")
    if len(value) > MAX_IDENTIFIER_LENGTH:
        raise ValidationError(f"{label}:too-long")
    validate_unicode_string(value, label)
    if not ID_PATTERN.fullmatch(value):
        raise ValidationError(f"{label}:invalid-identifier")
    return value


def reject_sensitive_keys(value: Any, path: str = "data") -> None:
    _reject_sensitive_keys(
        value,
        path,
        depth=0,
        active_containers=set(),
        nodes=[0],
    )


def _reject_sensitive_keys(
    value: Any,
    path: str,
    *,
    depth: int,
    active_containers: set[int],
    nodes: list[int],
) -> None:
    if depth > 32:
        raise ValidationError(f"{path}:value-too-deep")
    nodes[0] += 1
    if nodes[0] > MAX_SENSITIVE_SCAN_NODES:
        raise ValidationError(f"{path}:node-limit")
    if isinstance(value, (dict, list)) and type(value) not in (dict, list):
        raise ValidationError(f"{path}:unsupported-container")
    if type(value) is dict:
        identity = id(value)
        if identity in active_containers:
            raise ValidationError(f"{path}:cyclic-value")
        active_containers.add(identity)
        try:
            for key, item in value.items():
                if type(key) is not str:
                    raise ValidationError(f"{path}:object-key-not-string")
                validate_unicode_string(key, f"{path}:key")
                fingerprint = _security_key_fingerprint(key)
                if any(
                    sensitive in fingerprint
                    for sensitive in SENSITIVE_KEY_FINGERPRINTS
                ):
                    raise ValidationError(f"{path}:sensitive-key")
                _reject_sensitive_keys(
                    item,
                    f"{path}.{key}",
                    depth=depth + 1,
                    active_containers=active_containers,
                    nodes=nodes,
                )
        finally:
            active_containers.remove(identity)
    elif type(value) is list:
        identity = id(value)
        if identity in active_containers:
            raise ValidationError(f"{path}:cyclic-value")
        active_containers.add(identity)
        try:
            for index, item in enumerate(value):
                _reject_sensitive_keys(
                    item,
                    f"{path}[{index}]",
                    depth=depth + 1,
                    active_containers=active_containers,
                    nodes=nodes,
                )
        finally:
            active_containers.remove(identity)


def require_exact_fields(
    data: Any,
    required: set[str],
    optional: set[str] | None = None,
    label: str = "record",
) -> dict[str, Any]:
    if type(data) is not dict:
        raise ValidationError(f"{label}:object-required")
    allowed_count = len(required) + len(optional or set())
    if len(data) > allowed_count:
        raise ValidationError(f"{label}:too-many-fields")
    if any(type(key) is not str for key in data):
        raise ValidationError(f"{label}:field-name-string-required")
    optional = optional or set()
    missing = sorted(required - data.keys())
    extra = sorted(data.keys() - required - optional)
    if missing:
        raise ValidationError(f"{label}:missing-fields:{','.join(missing)}")
    if extra:
        raise ValidationError(f"{label}:unknown-fields:{','.join(extra)}")
    return data
