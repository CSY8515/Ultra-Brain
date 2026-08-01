"""Caller-driven monitoring evaluation with explicit thresholds."""

from __future__ import annotations

from dataclasses import asdict

from .common import canonical_timestamp, utc_now
from .errors import ValidationError
from .models import MonitorSignal, Observation
from .validation import validate_observation


class Monitor:
    """Evaluate one supplied observation; never poll or schedule work."""

    @staticmethod
    def evaluate(
        observation: Observation,
        evaluated_at: str | None = None,
    ) -> MonitorSignal:
        if type(observation) is not Observation:
            raise ValidationError("observation:observation-required")
        observation = validate_observation(asdict(observation))
        value = observation.value
        warning_at = observation.warning_at
        critical_at = observation.critical_at
        evaluated_at = canonical_timestamp(
            utc_now() if evaluated_at is None else evaluated_at,
            "monitor.evaluated_at",
        )

        if value >= critical_at:
            status = "critical"
            reason = "critical-threshold-reached"
        elif value >= warning_at:
            status = "warning"
            reason = "warning-threshold-reached"
        else:
            status = "healthy"
            reason = "below-warning-threshold"

        return MonitorSignal(
            observation_id=observation.id,
            status=status,
            reason=reason,
            evaluated_at=evaluated_at,
        )
