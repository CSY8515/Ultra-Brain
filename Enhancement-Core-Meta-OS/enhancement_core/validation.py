"""Strict, bounded validation for Enhancement inputs."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .models import AnalysisRequest, DecisionOption, EvidenceRecord


CONTRACT_VERSION = "0.3.0"
MAX_RECORDS = 1000
MAX_OPTIONS = 100
MAX_HORIZON = 100
MAX_ABSOLUTE_NUMBER = 1_000_000_000_000.0
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
METRIC = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


class ValidationError(ValueError):
    """Raised before analysis when a public contract is invalid."""


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValidationError(f"{label}:invalid-identifier")
    return value


def _text(value: Any, label: str, maximum: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValidationError(f"{label}:invalid-text")
    return value.strip()


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{label}:number-required")
    result = float(value)
    if not math.isfinite(result):
        raise ValidationError(f"{label}:finite-required")
    if abs(result) > MAX_ABSOLUTE_NUMBER:
        raise ValidationError(f"{label}:magnitude-exceeded")
    return result


def _timestamp(value: Any, label: str) -> str:
    value = _text(value, label, 64)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label}:invalid-timestamp") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"{label}:timezone-required")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_record(value: EvidenceRecord | Mapping[str, Any]) -> EvidenceRecord:
    data = value.to_dict() if type(value) is EvidenceRecord else value
    if not isinstance(data, Mapping):
        raise ValidationError("record:object-required")
    required = {"id", "observed_at", "source", "metrics", "quality", "consent", "dimensions"}
    if set(data) != required:
        raise ValidationError("record:fields-invalid")
    if data["consent"] is not True:
        raise ValidationError("record:explicit-consent-required")
    metrics = data["metrics"]
    if not isinstance(metrics, Mapping) or not metrics or len(metrics) > 64:
        raise ValidationError("record:metrics-invalid")
    clean_metrics: dict[str, float] = {}
    for key, item in metrics.items():
        if not isinstance(key, str) or not METRIC.fullmatch(key):
            raise ValidationError("record:metric-name-invalid")
        clean_metrics[key] = _number(item, f"metric:{key}")
    quality = _number(data["quality"], "record:quality")
    if not 0 <= quality <= 1:
        raise ValidationError("record:quality-out-of-range")
    dimensions = data["dimensions"]
    if not isinstance(dimensions, Mapping) or len(dimensions) > 16:
        raise ValidationError("record:dimensions-invalid")
    clean_dimensions: dict[str, str] = {}
    sensitive = {"password", "secret", "token", "credential", "api_key"}
    for key, item in dimensions.items():
        if not isinstance(key, str) or key.lower() in sensitive or not METRIC.fullmatch(key):
            raise ValidationError("record:dimension-name-invalid")
        clean_dimensions[key] = _text(item, f"dimension:{key}", 128)
    return EvidenceRecord(
        _identifier(data["id"], "record:id"),
        _timestamp(data["observed_at"], "record:observed_at"),
        _text(data["source"], "record:source", 256),
        MappingProxyType(clean_metrics), quality, True,
        MappingProxyType(clean_dimensions),
    )


def validate_option(value: DecisionOption | Mapping[str, Any]) -> DecisionOption:
    data = value.to_dict() if type(value) is DecisionOption else value
    if not isinstance(data, Mapping) or set(data) != {"id", "scores", "constraints_met"}:
        raise ValidationError("option:fields-invalid")
    if type(data["constraints_met"]) is not bool:
        raise ValidationError("option:constraints-met-boolean-required")
    scores = data["scores"]
    if not isinstance(scores, Mapping) or not scores or len(scores) > 32:
        raise ValidationError("option:scores-invalid")
    clean = {}
    for key, item in scores.items():
        if not isinstance(key, str) or not METRIC.fullmatch(key):
            raise ValidationError("option:criterion-invalid")
        clean[key] = _number(item, f"option:{key}")
    return DecisionOption(_identifier(data["id"], "option:id"), MappingProxyType(clean), data["constraints_met"])


def validate_request(value: AnalysisRequest | Mapping[str, Any]) -> AnalysisRequest:
    data = value.to_dict() if type(value) is AnalysisRequest else value
    required = {"id", "version", "objective", "metric", "records", "prediction_horizon", "options", "criteria_weights"}
    if not isinstance(data, Mapping) or set(data) != required:
        raise ValidationError("request:fields-invalid")
    if data["version"] != CONTRACT_VERSION:
        raise ValidationError("request:unsupported-version")
    metric = data["metric"]
    if not isinstance(metric, str) or not METRIC.fullmatch(metric):
        raise ValidationError("request:metric-invalid")
    records_raw = data["records"]
    if not isinstance(records_raw, (list, tuple)) or not 2 <= len(records_raw) <= MAX_RECORDS:
        raise ValidationError("request:record-count-invalid")
    records = tuple(validate_record(item) for item in records_raw)
    ids = [item.id for item in records]
    if len(ids) != len(set(ids)):
        raise ValidationError("request:duplicate-record-id")
    if any(metric not in item.metrics for item in records):
        raise ValidationError("request:metric-missing")
    if tuple(item.observed_at for item in records) != tuple(sorted(item.observed_at for item in records)):
        raise ValidationError("request:records-not-chronological")
    horizon = data["prediction_horizon"]
    if isinstance(horizon, bool) or not isinstance(horizon, int) or not 1 <= horizon <= MAX_HORIZON:
        raise ValidationError("request:horizon-invalid")
    options_raw = data["options"]
    if not isinstance(options_raw, (list, tuple)) or len(options_raw) > MAX_OPTIONS:
        raise ValidationError("request:options-invalid")
    options = tuple(validate_option(item) for item in options_raw)
    option_ids = [item.id for item in options]
    if len(option_ids) != len(set(option_ids)):
        raise ValidationError("request:duplicate-option-id")
    weights = data["criteria_weights"]
    if not isinstance(weights, Mapping) or len(weights) > 32:
        raise ValidationError("request:weights-invalid")
    clean_weights = {}
    for key, item in weights.items():
        if not isinstance(key, str) or not METRIC.fullmatch(key):
            raise ValidationError("request:criterion-invalid")
        number = _number(item, f"weight:{key}")
        if number < 0:
            raise ValidationError("request:negative-weight")
        clean_weights[key] = number
    if bool(options) != bool(clean_weights) or (clean_weights and sum(clean_weights.values()) <= 0):
        raise ValidationError("request:options-weights-mismatch")
    if options and any(set(item.scores) != set(clean_weights) for item in options):
        raise ValidationError("request:option-criteria-mismatch")
    return AnalysisRequest(
        _identifier(data["id"], "request:id"), CONTRACT_VERSION,
        _text(data["objective"], "request:objective", 512), metric, records,
        horizon, options, MappingProxyType(clean_weights),
    )
