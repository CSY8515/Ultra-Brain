"""Immutable public records for the Enhancement Core."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from types import MappingProxyType
from typing import Any, Mapping


def frozen_map(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


class Record:
    def to_dict(self) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, Mapping):
                return {key: convert(item) for key, item in value.items()}
            if isinstance(value, tuple):
                return [convert(item) for item in value]
            if is_dataclass(value):
                return {item.name: convert(getattr(value, item.name)) for item in fields(value)}
            return value
        return convert(self)


@dataclass(frozen=True, slots=True)
class EvidenceRecord(Record):
    id: str
    observed_at: str
    source: str
    metrics: Mapping[str, float]
    quality: float
    consent: bool
    dimensions: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class DecisionOption(Record):
    id: str
    scores: Mapping[str, float]
    constraints_met: bool = True


@dataclass(frozen=True, slots=True)
class AnalysisRequest(Record):
    id: str
    version: str
    objective: str
    metric: str
    records: tuple[EvidenceRecord, ...]
    prediction_horizon: int = 1
    options: tuple[DecisionOption, ...] = ()
    criteria_weights: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class AnalyticsReport(Record):
    metric: str
    count: int
    minimum: float
    maximum: float
    mean: float
    median: float
    standard_deviation: float
    slope: float
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LearningModel(Record):
    id: str
    version: str
    metric: str
    sample_count: int
    baseline: float
    slope: float
    confidence: float
    trained_from: tuple[str, ...]
    method: str = "bounded-linear-baseline"


@dataclass(frozen=True, slots=True)
class PatternFinding(Record):
    id: str
    kind: str
    direction: str
    strength: float
    support: int
    evidence_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True, slots=True)
class KnowledgeCandidate(Record):
    id: str
    statement: str
    status: str
    confidence: float
    provenance: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Prediction(Record):
    metric: str
    horizon: int
    value: float
    lower_bound: float
    upper_bound: float
    confidence: float
    method: str
    evidence_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuleCandidate(Record):
    id: str
    status: str
    metric: str
    operator: str
    threshold: float
    advisory_action: str
    confidence: float
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Insight(Record):
    id: str
    statement: str
    significance: str
    confidence: float
    evidence_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RankedOption(Record):
    option_id: str
    score: float
    feasible: bool
    contributions: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class DecisionSupport(Record):
    status: str
    objective: str
    recommended_option_id: str | None
    ranked_options: tuple[RankedOption, ...]
    rationale: tuple[str, ...]
    confidence: float
    requires_human_decision: bool = True


@dataclass(frozen=True, slots=True)
class EnhancementResult(Record):
    request_id: str
    version: str
    analytics: AnalyticsReport
    learning: LearningModel
    patterns: tuple[PatternFinding, ...]
    knowledge: tuple[KnowledgeCandidate, ...]
    prediction: Prediction
    rules: tuple[RuleCandidate, ...]
    insights: tuple[Insight, ...]
    decision_support: DecisionSupport | None
    limitations: tuple[str, ...]
