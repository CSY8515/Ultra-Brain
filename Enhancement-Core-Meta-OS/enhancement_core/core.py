"""Deterministic, non-executing Enhancement components and facade."""

from __future__ import annotations

import math
import statistics
from types import MappingProxyType

from .models import (
    AnalysisRequest, AnalyticsReport, DecisionSupport, EnhancementResult, Insight,
    KnowledgeCandidate, LearningModel, PatternFinding, Prediction, RankedOption,
    RuleCandidate,
)
from .validation import CONTRACT_VERSION, ValidationError, validate_request


def _rounded(value: float) -> float:
    return round(value, 10)


class Analytics:
    def analyze(self, request: AnalysisRequest) -> AnalyticsReport:
        values = [record.metrics[request.metric] for record in request.records]
        count = len(values)
        x_mean = (count - 1) / 2
        denominator = sum((index - x_mean) ** 2 for index in range(count))
        slope = sum((index - x_mean) * (value - statistics.fmean(values)) for index, value in enumerate(values)) / denominator
        return AnalyticsReport(
            request.metric, count, min(values), max(values),
            _rounded(statistics.fmean(values)), _rounded(statistics.median(values)),
            _rounded(statistics.pstdev(values)), _rounded(slope),
            tuple(record.id for record in request.records),
        )


class Learning:
    def fit(self, request: AnalysisRequest, report: AnalyticsReport) -> LearningModel:
        quality = statistics.fmean(record.quality for record in request.records)
        support = min(1.0, report.count / 20)
        confidence = _rounded(quality * (0.5 + 0.5 * support))
        return LearningModel(
            f"{request.id}-model", CONTRACT_VERSION, request.metric, report.count,
            report.mean, report.slope, confidence, report.evidence_ids,
        )


class PatternAnalysis:
    def detect(self, report: AnalyticsReport) -> tuple[PatternFinding, ...]:
        findings: list[PatternFinding] = []
        scale = max(abs(report.mean), report.standard_deviation, 1e-12)
        strength = min(1.0, abs(report.slope) / scale)
        if report.count >= 3 and strength >= 0.01:
            direction = "increasing" if report.slope > 0 else "decreasing"
            findings.append(PatternFinding(
                f"{report.metric}-trend", "trend", direction, _rounded(strength),
                report.count, report.evidence_ids,
                f"Observed values have a {direction} linear trend; this is descriptive, not causal.",
            ))
        if report.count >= 4 and report.standard_deviation > 0:
            z_limit = 2.0
            outliers = sum(
                abs(value - report.mean) / report.standard_deviation >= z_limit
                for value in (report.minimum, report.maximum)
            )
            if outliers:
                findings.append(PatternFinding(
                    f"{report.metric}-outlier", "outlier", "mixed", _rounded(min(1.0, outliers / 2)),
                    outliers, report.evidence_ids,
                    "At least one observed extreme is two standard deviations from the mean.",
                ))
        return tuple(findings)


class Knowledge:
    def build(self, report: AnalyticsReport, patterns: tuple[PatternFinding, ...], confidence: float) -> tuple[KnowledgeCandidate, ...]:
        statement = f"For {report.metric}, {report.count} supplied observations have mean {report.mean}."
        candidates = [KnowledgeCandidate(
            f"{report.metric}-summary", statement, "candidate", confidence,
            report.evidence_ids, ("Caller-supplied evidence only.", "No causal conclusion.")
        )]
        candidates.extend(KnowledgeCandidate(
            f"knowledge-{pattern.id}", pattern.explanation, "candidate",
            _rounded(confidence * pattern.strength), pattern.evidence_ids,
            ("Pattern requires governed review before promotion.",)
        ) for pattern in patterns)
        return tuple(candidates)


class PredictionEngine:
    def predict(self, request: AnalysisRequest, report: AnalyticsReport, model: LearningModel) -> Prediction:
        last = request.records[-1].metrics[request.metric]
        value = last + report.slope * request.prediction_horizon
        uncertainty = report.standard_deviation * math.sqrt(1 + request.prediction_horizon / report.count)
        confidence = _rounded(model.confidence / (1 + 0.05 * request.prediction_horizon))
        return Prediction(
            request.metric, request.prediction_horizon, _rounded(value),
            _rounded(value - uncertainty), _rounded(value + uncertainty), confidence,
            "bounded-linear-extrapolation", report.evidence_ids,
            ("Assumes the observed linear trend continues.", "Bounds are descriptive, not calibrated probability intervals."),
        )


class RuleGeneration:
    def generate(self, report: AnalyticsReport, patterns: tuple[PatternFinding, ...], confidence: float) -> tuple[RuleCandidate, ...]:
        rules = []
        for pattern in patterns:
            if pattern.kind == "trend":
                operator = ">" if pattern.direction == "increasing" else "<"
                rules.append(RuleCandidate(
                    f"rule-{pattern.id}", "draft", report.metric, operator, report.mean,
                    "request-human-review", _rounded(confidence * pattern.strength), pattern.evidence_ids,
                ))
        return tuple(rules)


class InsightEngine:
    def explain(self, report: AnalyticsReport, patterns: tuple[PatternFinding, ...], confidence: float) -> tuple[Insight, ...]:
        spread = report.maximum - report.minimum
        insights = [Insight(
            f"insight-{report.metric}-range",
            f"{report.metric} spans {spread} across {report.count} supplied observations.",
            "material" if spread > abs(report.mean) * 0.25 else "informational",
            confidence, report.evidence_ids,
            ("Descriptive result; source quality controls confidence.",),
        )]
        insights.extend(Insight(
            f"insight-{pattern.id}", pattern.explanation,
            "material" if pattern.strength >= 0.25 else "informational",
            _rounded(confidence * pattern.strength), pattern.evidence_ids,
            ("Association does not establish causation.",),
        ) for pattern in patterns)
        return tuple(insights)


class Optimization:
    def rank(self, request: AnalysisRequest) -> tuple[RankedOption, ...]:
        total_weight = sum(request.criteria_weights.values())
        ranked = []
        for option in request.options:
            contributions = {criterion: _rounded(option.scores[criterion] * weight / total_weight) for criterion, weight in request.criteria_weights.items()}
            score = _rounded(sum(contributions.values())) if option.constraints_met else float("-inf")
            ranked.append(RankedOption(option.id, score, option.constraints_met, MappingProxyType(contributions)))
        return tuple(sorted(ranked, key=lambda item: (not item.feasible, -item.score if math.isfinite(item.score) else math.inf, item.option_id)))


class DecisionSupportEngine:
    def advise(self, request: AnalysisRequest, ranked: tuple[RankedOption, ...], evidence_confidence: float) -> DecisionSupport:
        feasible = [item for item in ranked if item.feasible]
        recommended = feasible[0].option_id if feasible else None
        rationale = (
            (f"{recommended} has the highest explicit weighted score among feasible options.",)
            if recommended else ("No supplied option satisfies all declared constraints.",)
        )
        return DecisionSupport("advisory", request.objective, recommended, ranked, rationale, evidence_confidence, True)


class EnhancementCore:
    """Compose Enhancement outputs without collecting data or executing actions."""

    def __init__(self) -> None:
        self.analytics = Analytics()
        self.learning = Learning()
        self.patterns = PatternAnalysis()
        self.knowledge = Knowledge()
        self.predictions = PredictionEngine()
        self.rules = RuleGeneration()
        self.insights = InsightEngine()
        self.optimization = Optimization()
        self.decisions = DecisionSupportEngine()

    def analyze(self, value: AnalysisRequest | dict) -> EnhancementResult:
        request = validate_request(value)
        report = self.analytics.analyze(request)
        model = self.learning.fit(request, report)
        patterns = self.patterns.detect(report)
        knowledge = self.knowledge.build(report, patterns, model.confidence)
        prediction = self.predictions.predict(request, report, model)
        rules = self.rules.generate(report, patterns, model.confidence)
        insights = self.insights.explain(report, patterns, model.confidence)
        decision = None
        if request.options:
            decision = self.decisions.advise(request, self.optimization.rank(request), model.confidence)
        return EnhancementResult(
            request.id, CONTRACT_VERSION, report, model, patterns, knowledge,
            prediction, rules, insights, decision,
            ("Outputs are advisory and grant no execution authority.", "Safety evaluation remains independently mandatory for governed actions."),
        )
