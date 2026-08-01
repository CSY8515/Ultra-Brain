from __future__ import annotations

import math
import unittest

from enhancement_core import EnhancementCore, ValidationError


def request(**changes):
    value = {
        "id": "analysis-001", "version": "0.3.0",
        "objective": "Choose the strongest governed option", "metric": "quality",
        "records": [
            {"id": f"evidence-{index}", "observed_at": f"2026-08-0{index}T00:00:00Z", "source": "approved-study", "metrics": {"quality": float(value)}, "quality": 0.9, "consent": True, "dimensions": {"cohort": "alpha"}}
            for index, value in enumerate((10, 12, 14, 16, 18), 1)
        ],
        "prediction_horizon": 2,
        "options": [
            {"id": "option-a", "scores": {"benefit": 8, "cost": 3}, "constraints_met": True},
            {"id": "option-b", "scores": {"benefit": 6, "cost": 8}, "constraints_met": True},
            {"id": "option-c", "scores": {"benefit": 99, "cost": 99}, "constraints_met": False}
        ],
        "criteria_weights": {"benefit": 0.75, "cost": 0.25},
    }
    value.update(changes)
    return value


class EnhancementCoreTests(unittest.TestCase):
    def setUp(self):
        self.core = EnhancementCore()

    def test_composed_result_covers_mission(self):
        result = self.core.analyze(request())
        self.assertEqual(result.analytics.mean, 14)
        self.assertEqual(result.analytics.slope, 2)
        self.assertEqual(result.learning.method, "bounded-linear-baseline")
        self.assertTrue(result.patterns)
        self.assertTrue(result.knowledge)
        self.assertEqual(result.prediction.value, 22)
        self.assertTrue(result.rules)
        self.assertTrue(result.insights)
        self.assertIsNotNone(result.decision_support)

    def test_provenance_is_preserved_end_to_end(self):
        result = self.core.analyze(request())
        ids = tuple(item["id"] for item in request()["records"])
        self.assertEqual(result.analytics.evidence_ids, ids)
        self.assertEqual(result.learning.trained_from, ids)
        self.assertEqual(result.prediction.evidence_ids, ids)
        self.assertTrue(all(item.provenance == ids for item in result.knowledge))

    def test_rules_are_draft_and_advisory_only(self):
        result = self.core.analyze(request())
        self.assertTrue(all(item.status == "draft" for item in result.rules))
        self.assertTrue(all(item.advisory_action == "request-human-review" for item in result.rules))

    def test_decision_support_is_advisory_and_feasibility_wins(self):
        decision = self.core.analyze(request()).decision_support
        self.assertEqual(decision.status, "advisory")
        self.assertTrue(decision.requires_human_decision)
        self.assertEqual(decision.recommended_option_id, "option-a")
        self.assertFalse(next(item for item in decision.ranked_options if item.option_id == "option-c").feasible)

    def test_no_feasible_option_returns_no_recommendation(self):
        value = request()
        value["options"] = [{**item, "constraints_met": False} for item in value["options"]]
        self.assertIsNone(self.core.analyze(value).decision_support.recommended_option_id)

    def test_result_is_json_compatible(self):
        result = self.core.analyze(request()).to_dict()
        self.assertEqual(result["version"], "0.3.0")
        self.assertEqual(result["rules"][0]["status"], "draft")

    def test_equal_input_is_deterministic(self):
        self.assertEqual(self.core.analyze(request()).to_dict(), self.core.analyze(request()).to_dict())

    def test_unconsented_evidence_fails_closed(self):
        value = request()
        value["records"][0]["consent"] = False
        with self.assertRaisesRegex(ValidationError, "consent"):
            self.core.analyze(value)

    def test_non_finite_metrics_fail_closed(self):
        for bad in (math.nan, math.inf, -math.inf):
            value = request()
            value["records"][0]["metrics"]["quality"] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(ValidationError, "finite"):
                self.core.analyze(value)

    def test_excessive_numeric_magnitude_fails_closed(self):
        value = request()
        value["records"][0]["metrics"]["quality"] = 1e13
        with self.assertRaisesRegex(ValidationError, "magnitude"):
            self.core.analyze(value)

    def test_duplicate_evidence_fails_closed(self):
        value = request()
        value["records"][1]["id"] = value["records"][0]["id"]
        with self.assertRaisesRegex(ValidationError, "duplicate"):
            self.core.analyze(value)

    def test_chronology_is_mandatory(self):
        value = request()
        value["records"] = list(reversed(value["records"]))
        with self.assertRaisesRegex(ValidationError, "chronological"):
            self.core.analyze(value)

    def test_chronology_uses_normalized_utc_time(self):
        value = request(records=request()["records"][:2], options=[], criteria_weights={})
        value["records"][0]["observed_at"] = "2026-08-01T01:30:00+02:00"
        value["records"][1]["observed_at"] = "2026-08-01T00:00:00Z"
        result = self.core.analyze(value)
        self.assertEqual(result.analytics.count, 2)

    def test_sensitive_dimension_names_are_rejected(self):
        value = request()
        value["records"][0]["dimensions"] = {"token": "not-allowed"}
        with self.assertRaisesRegex(ValidationError, "dimension-name"):
            self.core.analyze(value)

    def test_non_string_dimension_name_is_typed_failure(self):
        value = request()
        value["records"][0]["dimensions"] = {1: "invalid"}
        with self.assertRaisesRegex(ValidationError, "dimension-name"):
            self.core.analyze(value)

    def test_unsupported_contract_is_rejected(self):
        with self.assertRaisesRegex(ValidationError, "unsupported-version"):
            self.core.analyze(request(version="0.2.0"))

    def test_horizon_is_bounded(self):
        with self.assertRaisesRegex(ValidationError, "horizon"):
            self.core.analyze(request(prediction_horizon=101))

    def test_options_require_matching_explicit_weights(self):
        with self.assertRaisesRegex(ValidationError, "mismatch"):
            self.core.analyze(request(criteria_weights={}))

    def test_two_samples_are_supported_without_pattern_overclaim(self):
        value = request(records=request()["records"][:2], options=[], criteria_weights={})
        result = self.core.analyze(value)
        self.assertEqual(result.patterns, ())
        self.assertIsNone(result.decision_support)


if __name__ == "__main__":
    unittest.main()
