"""Immutable public records for Personal Secretary Core Meta OS."""
from __future__ import annotations
from dataclasses import dataclass, field, fields, is_dataclass
from types import MappingProxyType
from typing import Any, Mapping

def freeze(value: Any) -> Any:
    if isinstance(value, Mapping): return MappingProxyType({str(k): freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)): return tuple(freeze(v) for v in value)
    return value

class Record:
    def to_dict(self):
        def convert(value):
            if isinstance(value, Mapping): return {k: convert(v) for k, v in value.items()}
            if isinstance(value, tuple): return [convert(v) for v in value]
            if is_dataclass(value): return {f.name: convert(getattr(value, f.name)) for f in fields(value)}
            return value
        return convert(self)

@dataclass(frozen=True, slots=True)
class SecretaryGrant(Record):
    id: str; user_id: str; approved: bool; safety_decision_id: str; valid_from: str; expires_at: str
    allowed_operations: tuple[str, ...]; allowed_context_categories: tuple[str, ...]; max_items: int; max_horizon_days: int
    allow_sensitive_context: bool = False
    def __post_init__(self):
        object.__setattr__(self, "allowed_operations", tuple(self.allowed_operations))
        object.__setattr__(self, "allowed_context_categories", tuple(self.allowed_context_categories))
@dataclass(frozen=True, slots=True)
class Task(Record):
    id: str; title: str; status: str; due_at: str | None; importance: int; effort_minutes: int; created_at: str
    category: str = "general"; sensitive: bool = False
@dataclass(frozen=True, slots=True)
class ScheduleItem(Record):
    id: str; title: str; start_at: str; end_at: str; category: str = "general"; confirmed: bool = True; sensitive: bool = False
@dataclass(frozen=True, slots=True)
class Reminder(Record):
    id: str; title: str; remind_at: str; source_id: str = ""; acknowledged: bool = False; sensitive: bool = False
@dataclass(frozen=True, slots=True)
class Goal(Record):
    id: str; title: str; period: str; status: str; progress: float
@dataclass(frozen=True, slots=True)
class ContextItem(Record):
    id: str; category: str; content: str; observed_at: str; source: str; sensitive: bool = False
@dataclass(frozen=True, slots=True)
class DecisionOption(Record):
    id: str; label: str; scores: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    def __post_init__(self): object.__setattr__(self, "scores", freeze(self.scores))
@dataclass(frozen=True, slots=True)
class Briefing(Record):
    kind: str; period_start: str; period_end: str; generated_at: str; sections: Mapping[str, tuple[str, ...]]
@dataclass(frozen=True, slots=True)
class Review(Record):
    kind: str; period_start: str; period_end: str; generated_at: str; metrics: Mapping[str, float | int]; highlights: tuple[str, ...]; attention: tuple[str, ...]
@dataclass(frozen=True, slots=True)
class PriorityItem(Record):
    task_id: str; rank: int; score: int; reasons: tuple[str, ...]
@dataclass(frozen=True, slots=True)
class PriorityPlan(Record):
    generated_at: str; items: tuple[PriorityItem, ...]
@dataclass(frozen=True, slots=True)
class Recommendation(Record):
    id: str; summary: str; rationale: str; evidence_ids: tuple[str, ...]; confidence: float; requires_confirmation: bool = True
@dataclass(frozen=True, slots=True)
class RecommendationSet(Record):
    generated_at: str; recommendations: tuple[Recommendation, ...]
@dataclass(frozen=True, slots=True)
class DecisionAnalysis(Record):
    generated_at: str; ranking: tuple[str, ...]; weighted_scores: Mapping[str, float]; tradeoffs: Mapping[str, tuple[str, ...]]; decision_owner: str = "user"
@dataclass(frozen=True, slots=True)
class AssistanceStep(Record):
    sequence: int; task_id: str; action: str; requires_confirmation: bool
@dataclass(frozen=True, slots=True)
class AssistancePlan(Record):
    generated_at: str; objective: str; steps: tuple[AssistanceStep, ...]; status: str = "proposal"
@dataclass(frozen=True, slots=True)
class ContextResult(Record):
    query: str; matched_ids: tuple[str, ...]; matches: tuple[ContextItem, ...]
@dataclass(frozen=True, slots=True)
class SchedulePlan(Record):
    generated_at: str; duration_minutes: int; proposed_slots: tuple[tuple[str, str], ...]; conflict_ids: tuple[str, ...]; status: str = "proposal"
