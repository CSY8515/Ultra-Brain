"""Deterministic likelihood-impact risk classification."""

from __future__ import annotations

from .errors import ValidationError
from .models import RiskAssessment


class RiskEngine:
    """Classify declared integer likelihood and impact without inference."""

    @staticmethod
    def assess(likelihood: int, impact: int) -> RiskAssessment:
        """Return the fixed v0.2 risk classification for two values in ``1..5``.

        ``bool`` is rejected explicitly because it is a subclass of ``int`` in
        Python but is not a valid declared risk value.
        """

        likelihood = _validate_factor(likelihood, "likelihood")
        impact = _validate_factor(impact, "impact")
        score = likelihood * impact

        if score <= 4:
            level = "low"
        elif score <= 9:
            level = "moderate"
        elif score <= 16:
            level = "high"
        else:
            level = "critical"

        return RiskAssessment(
            score=score,
            level=level,
            likelihood=likelihood,
            impact=impact,
        )


def _validate_factor(value: int, label: str) -> int:
    if type(value) is not int:
        raise ValidationError(f"{label}:integer-required")
    if not 1 <= value <= 5:
        raise ValidationError(f"{label}:out-of-range")
    return value
