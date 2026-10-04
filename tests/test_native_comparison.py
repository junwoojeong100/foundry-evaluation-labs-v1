from copy import deepcopy
import json
import unittest

from scripts.compare_foundry_eval import compare_pair


def fixture():
    row = {"query": "Synthetic unit question", "context": "Synthetic unit policy", "ground_truth": "Reference"}
    criteria = [{
        "type": "azure_ai_evaluator", "name": name, "evaluator_name": evaluator,
        "initialization_parameters": {"threshold": threshold, "deployment_name": "unit-judge"},
        "data_mapping": {"query": "{{item.query}}", "response": response},
    } for name, evaluator, threshold, response in (
        ("Relevance", "builtin.relevance", 4, "{{sample.output_text}}"),
        ("TaskAdherence", "builtin.task_adherence", 1, "{{sample.output_items}}"),
    )]
    result = {"dataset": [row]}
    for arm, version, relevance, prompt in (("baseline", "1", 4, "Original rules"), ("candidate", "2", 5, "Improved rules")):
        result[arm] = {
            "id": "run-" + arm, "eval_id": "eval-unit", "status": "completed",
            "data_source": {
                "target": {"name": "unit-agent", "version": version, "type": "azure_ai_agent"},
                "source": {"type": "file_id", "id": "unit-data"},
            },
            "result_counts": {"total": 1, "passed": 1, "failed": 0, "errored": 0, "skipped": 0},
            "latency": {"target": {"p50_ms": 100, "p95_ms": 120, "sample_count": 1}},
            "per_model_usage": [{"model_name": "unit-agent-model", "total_tokens": 200}],
        }
        result[arm + "_agent"] = {
            "definition": {"kind": "prompt", "model": "unit-agent-model", "instructions": prompt, "tools": []},
        }
        result[arm + "_evaluation"] = {"testing_criteria": deepcopy(criteria)}
        result[arm + "_items"] = [{
            "datasource_item": {
                **row, "agent_name": "unit-agent", "agent_version": version,
                "sample.output_items": [{"role": "system", "content": prompt}],
                "sample.output_text": json.dumps({
                    "answer": "Synthetic unit answer", "citations": ["ATLAS-DOC-001"],
                    "route": "answer", "needs_human": False,
                }),
                "internal_endpoint": "private.example.invalid",
            },
            "sample": {"latency_ms": 100},
            "results": [
                {"name": "Relevance", "score": relevance, "passed": True, "reason": "Addresses the unit question."},
                {"name": "TaskAdherence", "score": 1, "passed": True, "reason": "Follows the unit instructions."},
            ],
        }]
    return result


class NativeComparisonTests(unittest.TestCase):
    def test_improvement_requires_no_quality_regression_and_exposes_actual_reasons(self):
        report = compare_pair(**fixture())
        self.assertTrue(report["decision"]["measured_quality_improved_without_regression"])
        self.assertFalse(report["decision"]["guarantees_future_results"])
        self.assertEqual(report["cases"][0]["candidate"]["metrics"]["Relevance"]["reason"], "Addresses the unit question.")
        self.assertNotIn("private.example.invalid", json.dumps(report))
        self.assertNotIn("sample.output_items", json.dumps(report))
        self.assertEqual(report["arms"]["candidate"]["agent_tokens"], 200)
        self.assertEqual(report["language"], "en")

    def test_explicit_korean_comparison_is_not_mislabeled_as_english(self):
        report = compare_pair(**fixture(), language="ko")
        self.assertEqual(report["language"], "ko")
        self.assertEqual(report["cases"][0]["query"], "Synthetic unit question")
        self.assertTrue(report["decision"]["measured_quality_improved_without_regression"])

    def test_unknown_comparison_language_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "language"):
            compare_pair(**fixture(), language="unknown")

    def test_equal_results_are_not_an_improvement(self):
        data = fixture()
        data["candidate_items"][0]["results"][0]["score"] = 4
        report = compare_pair(**data)
        self.assertFalse(report["decision"]["measured_quality_improved_without_regression"])
        self.assertIn("no strict measured quality improvement", report["decision"]["failed_checks"])

    def test_higher_relevance_cannot_hide_task_adherence_failure(self):
        data = fixture()
        data["candidate_items"][0]["results"][1].update(score=0, passed=False)
        data["candidate"]["result_counts"].update(passed=0, failed=1)
        report = compare_pair(**data)
        self.assertFalse(report["decision"]["measured_quality_improved_without_regression"])
        self.assertIn("TaskAdherence pass count declined", report["decision"]["failed_checks"])

    def test_malformed_json_is_retained_as_a_failure_not_silently_repaired(self):
        data = fixture()
        data["candidate_items"][0]["datasource_item"]["sample.output_text"] = "Not JSON"
        report = compare_pair(**data)
        self.assertEqual(report["cases"][0]["candidate"]["response"], "Not JSON")
        self.assertTrue(report["cases"][0]["candidate"]["response_contract_errors"])
        self.assertFalse(report["decision"]["measured_quality_improved_without_regression"])

    def test_no_changed_model_data_criteria_or_version_evidence_is_accepted(self):
        variants = []
        data = fixture()
        data["candidate_agent"]["definition"]["model"] = "other"
        variants.append(data)
        data = fixture()
        data["candidate_items"][0]["datasource_item"]["ground_truth"] = "Changed"
        variants.append(data)
        data = fixture()
        data["candidate_evaluation"]["testing_criteria"][0]["initialization_parameters"]["threshold"] = 3
        variants.append(data)
        data = fixture()
        data["candidate_items"][0]["datasource_item"]["agent_version"] = "1"
        variants.append(data)
        data = fixture()
        data["candidate_items"] = []
        variants.append(data)
        for index, data in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(ValueError):
                compare_pair(**data)

    def test_unknown_token_usage_is_not_zero_cost(self):
        data = fixture()
        data["candidate"]["per_model_usage"] = []
        with self.assertRaisesRegex(ValueError, "unknown is not zero"):
            compare_pair(**data)

    def test_signed_urls_are_not_published_in_responses_or_reasons(self):
        data = fixture()
        data["candidate_items"][0]["results"][0]["reason"] = "Download https://example.invalid/file?sig=sensitive"
        with self.assertRaisesRegex(ValueError, "do not publish"):
            compare_pair(**data)

    def test_identical_prompt_resampling_does_not_pass_the_gate(self):
        data = fixture()
        data["candidate_agent"]["definition"]["instructions"] = data["baseline_agent"]["definition"]["instructions"]
        with self.assertRaisesRegex(ValueError, "resample"):
            compare_pair(**data)


if __name__ == "__main__":
    unittest.main()
