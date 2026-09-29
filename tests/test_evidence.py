"""Synthetic unit-test fixtures only; these are not workshop/live run metrics."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from uuid import uuid4

from lab.evidence import (
    compare_runs,
    evaluate_gates,
    load_gates,
    score_row,
    strict_json_loads,
    summarize,
    validate_case,
    wilson_interval,
    write_report,
)


SOURCE = "UNIT-TEST-SOURCE"
KNOWN = {SOURCE, "UNIT-TEST-OTHER"}


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def case(identifier="unit-only-1", *, split="test", route="answer", tags=None):
    return {
        "id": identifier,
        "group_id": f"group-{identifier}",
        "split": split,
        "query": "단위 테스트 전용 질문입니다.",
        "context": "UNIT-TEST-SOURCE: 단위 테스트 전용 근거입니다.",
        "ground_truth": "단위 테스트 전용 기대 답변입니다.",
        "expected_route": route,
        "required_citations": [SOURCE],
        "tags": ["unit-test-only"] if tags is None else tags,
        "forbidden_claims": ["무조건 승인"],
    }


def output(**overrides):
    value = {
        "answer": "단위 테스트 전용 답변",
        "citations": [SOURCE],
        "route": "answer",
        "needs_human": False,
    }
    value.update(overrides)
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def metadata(*, split="test", stage="baseline", enabled=True):
    return {
        "run_id": "unit-test-only-run",
        "stage": stage,
        "split": split,
        "dataset_sha256": digest("unit-test-only-dataset"),
        "model_deployment": "unit-test-only-model",
        "prompt_sha256": digest("unit-test-only-prompt"),
        "knowledge_sha256": digest("unit-test-only-knowledge"),
        "judge": {
            "model_deployment": "unit-test-only-judge" if enabled else None,
            "prompt_sha256": digest("unit-test-only-judge-prompt") if enabled else None,
            "version": "unit-test-rubric-v1" if enabled else None,
            "settings": {"temperature": 0, "seed": 123} if enabled else {},
            "provenance": {"mode": "unit-test-fixture", "sdk": "none"},
            "scale": [1, 5] if enabled else None,
        },
    }


def scored(identifier="unit-only-1", *, split="test", tags=None, raw=None, **kwargs):
    return score_row(
        case(identifier, split=split, tags=tags),
        output() if raw is None else raw,
        known_citations=KNOWN,
        **kwargs,
    )


def run(*, count=20, split="test", stage="baseline", judge_score=4.5, wrong_routes=0, critical_rows=1):
    rows = []
    for index in range(count):
        rows.append(scored(
            f"unit-only-{index}",
            split=split,
            tags=["unit-test-only", "critical"] if index >= count - critical_rows else ["unit-test-only"],
            raw=output(route="clarify") if index < wrong_routes else output(),
            judge=None if judge_score is None else {
                "groundedness": judge_score, "relevance": judge_score,
            },
        ))
    return summarize(rows, metadata=metadata(split=split, stage=stage))


class RowScoringTests(unittest.TestCase):
    def test_good_response_and_raw_retention(self):
        raw = " \n" + output() + "\n "
        row = scored(raw=raw)
        self.assertTrue(all(row["checks"].values()))
        self.assertEqual(row["raw_output"], raw)
        self.assertEqual(row["citation_coverage"], 1)
        self.assertEqual(row["expected"]["route"], "answer")
        self.assertEqual(row["missing_citations"], [])
        self.assertEqual(row["unknown_citations"], [])

    def test_fenced_json_is_not_repaired(self):
        raw = "```json\n" + output() + "\n```"
        row = scored(raw=raw)
        self.assertEqual(row["raw_output"], raw)
        self.assertFalse(row["json_valid"])
        self.assertIsNotNone(row["parse_error"])
        self.assertFalse(any(row["checks"].values()))

    def test_structurally_invalid_responses_fail_format_without_crashing(self):
        invalid = [
            "null", "[]", "1", '"answer"', "{}",
            output(answer=None), output(citations=None),
            output(citations=[{"id": SOURCE}]), output(citations=[" "]),
            output(citations=[SOURCE, SOURCE]), output(route=["answer"]),
            output(route="unknown"), output(needs_human=1), output(extra=True),
            output(needs_human=True),
        ]
        for raw in invalid:
            with self.subTest(raw=raw):
                row = scored(raw=raw)
                self.assertTrue(row["json_valid"])
                self.assertFalse(row["checks"]["format"])
                self.assertTrue(row["schema_errors"])

    def test_strict_parser_rejects_duplicates_and_nonfinite_json(self):
        for raw in [
            '{"answer":"a","answer":"b"}',
            '{"citations":{"id":1,"id":2}}',
            '{"value":NaN}', '{"value":Infinity}', '{"value":-Infinity}',
            '{"value":1e999}', "{} trailing",
        ]:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    strict_json_loads(raw)
                row = scored(raw=raw)
                self.assertFalse(row["json_valid"])
                self.assertEqual(row["raw_output"], raw)
                json.dumps(row, allow_nan=False)

    def test_missing_and_unknown_citation_rules_are_independent_of_coverage(self):
        test_case = case()
        test_case["required_citations"] = sorted(KNOWN)
        row = score_row(test_case, output(), known_citations=KNOWN)
        self.assertEqual(row["citation_coverage"], 0.5)
        self.assertEqual(row["missing_citations"], ["UNIT-TEST-OTHER"])
        self.assertFalse(row["checks"]["citations"])
        row = scored(raw=output(citations=[SOURCE, "UNKNOWN"]))
        self.assertEqual(row["citation_coverage"], 1)
        self.assertEqual(row["unknown_citations"], ["UNKNOWN"])
        self.assertFalse(row["checks"]["citations"])

    def test_no_required_citations_is_vacuous_but_unknown_ids_still_fail(self):
        test_case = case()
        test_case["required_citations"] = []
        row = score_row(test_case, output(citations=[]), known_citations=KNOWN)
        self.assertEqual(row["citation_coverage"], 1)
        self.assertTrue(row["checks"]["citations"])
        bad = score_row(test_case, output(citations=["UNKNOWN"]), known_citations=KNOWN)
        self.assertFalse(bad["checks"]["citations"])
        missing = strict_json_loads(output())
        del missing["citations"]
        bad = score_row(test_case, json.dumps(missing), known_citations=KNOWN)
        self.assertEqual(bad["citation_coverage"], 0)
        self.assertFalse(bad["checks"]["citations"])

    def test_unknown_required_source_is_malformed_case_not_model_failure(self):
        test_case = case()
        test_case["required_citations"] = ["UNKNOWN"]
        with self.assertRaisesRegex(ValueError, "unknown source"):
            score_row(test_case, output(), known_citations=KNOWN)

    def test_route_and_human_flag(self):
        row = scored(raw=output(route="clarify"))
        self.assertTrue(row["checks"]["format"])
        self.assertFalse(row["checks"]["route"])
        escalated = case(route="escalate")
        row = score_row(
            escalated, output(route="escalate", needs_human=True), known_citations=KNOWN
        )
        self.assertTrue(all(row["checks"].values()))
        row = score_row(
            escalated, output(route="escalate", needs_human=False), known_citations=KNOWN
        )
        self.assertFalse(row["checks"]["format"])
        self.assertFalse(row["checks"]["human_flag"])
        row = score_row(escalated, output(), known_citations=KNOWN)
        self.assertFalse(row["checks"]["human_flag"])

    def test_literal_forbidden_claim_is_not_semantic_check(self):
        row = scored(raw=output(answer="무조건 승인 처리합니다."))
        self.assertEqual(row["forbidden_claim_hits"], ["무조건 승인"])
        self.assertFalse(row["checks"]["forbidden_claims"])
        row = scored(raw=output(answer="모두 허가합니다."))
        self.assertTrue(row["checks"]["forbidden_claims"])
        test_case = case()
        test_case["forbidden_claims"] = ["APPROVED"]
        row = score_row(test_case, output(answer="approved"), known_citations=KNOWN)
        self.assertTrue(row["checks"]["forbidden_claims"])

    def test_api_failure_fails_every_rule_even_if_raw_output_is_valid(self):
        row = scored(raw=output(), error="unit-test timeout", latency_ms=100)
        self.assertFalse(any(row["checks"].values()))
        self.assertEqual(row["raw_output"], output())
        self.assertEqual(row["citation_coverage"], 0)
        self.assertTrue(row["schema_valid"])

    def test_usage_aliases_and_missing_measurements(self):
        row = scored(usage={"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5})
        self.assertEqual(row["usage"], {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5})
        row = scored(usage={"input_tokens": 3, "output_tokens": 2})
        self.assertIsNone(row["usage"]["total_tokens"])
        self.assertTrue(all(value is None for value in scored()["usage"].values()))

    def test_invalid_numeric_inputs_raise_value_error(self):
        for value in (float("nan"), float("inf"), -float("inf"), -1, True, "1"):
            with self.subTest(latency=value), self.assertRaises(ValueError):
                scored(latency_ms=value)
        for value in (float("nan"), float("inf"), True, "4"):
            with self.subTest(judge=value), self.assertRaises(ValueError):
                scored(judge={"groundedness": value})
        for value in (-1, True, 1.5, float("inf"), "2"):
            with self.subTest(tokens=value), self.assertRaises(ValueError):
                scored(usage={"input_tokens": value})
        for usage in (
            {"input_tokens": 1, "prompt_tokens": 2},
            {"input_tokens": 1, "output_tokens": 2, "total_tokens": 100},
        ):
            with self.subTest(usage=usage), self.assertRaises(ValueError):
                scored(usage=usage)

    def test_malformed_evaluator_inputs_raise_value_error(self):
        for field, value in (
            ("id", ""), ("split", []), ("expected_route", {}),
            ("required_citations", SOURCE), ("tags", ["tag", "tag"]),
            ("forbidden_claims", [""]), ("query", None),
        ):
            test_case = case()
            test_case[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                score_row(test_case, output(), known_citations=KNOWN)
        with self.assertRaises(ValueError):
            score_row(case(), output(), known_citations=[SOURCE])
        with self.assertRaises(ValueError):
            scored(raw=1)
        with self.assertRaises(ValueError):
            scored(error="")
        with self.assertRaises(ValueError):
            validate_case({})
        cyclic = case()
        cyclic["extra"] = cyclic
        with self.assertRaisesRegex(ValueError, "cycle"):
            validate_case(cyclic)
        with self.assertRaises(ValueError):
            strict_json_loads("[" * 2000 + "]" * 2000)


class BusinessPolicyEvidenceTests(unittest.TestCase):
    def governed(self, *, bad_policy=None, missing_retrieval=None):
        rows = []
        for index in range(20):
            rows.append(scored(
                f"business-{index}", tags=["critical"] if index == 19 else [],
                judge={
                    "groundedness": 5, "relevance": 5,
                    "policy_correctness": 1 if index == bad_policy else 5,
                    "critical_failure": False, "metric_errors": {},
                },
                retrieved_context="" if index == missing_retrieval else "unit-only observed retrieval",
            ))
        meta = metadata()
        meta.update(
            evaluation_contract_version="atlas-evaluation-v1", status="completed",
            freeze_id="unit-only-freeze", freeze_sha256=digest("unit-only-freeze"), holdout_id="unit-only-holdout",
        )
        return summarize(rows, metadata=meta)

    def test_policy_correctness_and_retrieval_grounding_are_independent(self):
        summary = self.governed(bad_policy=19)
        self.assertEqual(summary["metrics"]["judge"]["groundedness"]["mean"], 5)
        self.assertEqual(summary["metrics"]["business_policy"]["mean"], 4.8)
        gate = evaluate_gates(summary, load_gates())
        self.assertEqual(gate["outcome"], "HOLD")
        self.assertFalse(next(check for check in gate["checks"] if check["name"] == "critical_policy_correctness_floor")["passed"])
        self.assertEqual(gate["manual_operational_approval"], "not_granted")

    def test_empty_retrieval_cannot_be_scored_by_using_policy_or_numeric_five(self):
        summary = self.governed(missing_retrieval=0)
        measure = summary["metrics"]["judge"]["groundedness"]
        self.assertEqual(measure["mean"], 5)
        self.assertEqual(measure["scored_count"], 19)
        self.assertEqual(measure["missing_count"], 1)
        self.assertEqual(measure["coverage"], 19 / 20)
        self.assertEqual(evaluate_gates(summary, load_gates())["quality_status"], "HOLD")

    def test_one_metric_failure_does_not_erase_independent_valid_measurements(self):
        row = scored(
            judge={"groundedness": 5, "relevance": 4, "policy_correctness": 5,
                   "metric_errors": {"groundedness": "unit-only retrieval judge timeout"}},
            retrieved_context="actual context fixture",
        )
        summary = summarize([row], metadata=metadata())
        self.assertEqual(summary["metrics"]["judge"]["relevance"]["scored_count"], 1)
        self.assertEqual(summary["metrics"]["business_policy"]["scored_count"], 1)
        self.assertIsNone(summary["metrics"]["judge"]["groundedness"]["mean"])
        self.assertEqual(summary["metrics"]["judge_error_count"], 1)
        with self.assertRaisesRegex(ValueError, "metric_errors"):
            scored(judge={"metric_errors": {"undeclared": "not valid"}})

    def test_new_contract_needs_fresh_freeze_not_the_exposed_original_test(self):
        summary = self.governed()
        self.assertEqual(evaluate_gates(summary, load_gates())["outcome"], "PASS_FOR_WORKSHOP")
        del summary["metadata"]["freeze_id"]
        self.assertEqual(evaluate_gates(summary, load_gates())["outcome"], "HOLD")

    def test_prior_unsafe_turn_flag_is_not_hidden_by_perfect_final_answer(self):
        summary = self.governed()
        rows = deepcopy(summary["rows"])
        rows[0]["judge"]["critical_failure"] = True
        summary = summarize(rows, metadata=summary["metadata"])
        self.assertEqual(summary["metrics"]["route_accuracy"], 1)
        self.assertEqual(summary["metrics"]["business_policy"]["mean"], 5)
        self.assertEqual(summary["metrics"]["business_policy"]["critical_failure_ids"], ["business-0"])
        self.assertEqual(evaluate_gates(summary, load_gates())["outcome"], "HOLD")

    def test_missing_critical_failure_decision_is_not_assumed_safe(self):
        summary = self.governed()
        rows = deepcopy(summary["rows"])
        del rows[0]["judge"]["critical_failure"]
        summary = summarize(rows, metadata=summary["metadata"])
        self.assertEqual(evaluate_gates(summary, load_gates())["outcome"], "HOLD")

    def test_observed_model_drift_blocks_gates_despite_completed_label_and_perfect_scores(self):
        summary = self.governed()
        for evidence in (
            {"model_snapshot": {"version": "A"}, "model_snapshot_after": {"version": "B"}},
            {"model_snapshot": {"version": "A"}, "model_snapshot_after": {"version": "A"}, "model_drift_detected": True},
        ):
            candidate = deepcopy(summary)
            candidate["metadata"].update(evidence)
            with self.subTest(evidence=evidence):
                result = evaluate_gates(candidate, load_gates())
                self.assertEqual(result["outcome"], "HOLD")
                self.assertFalse(next(check for check in result["checks"] if check["name"] == "no_observed_model_drift")["passed"])

    def test_comparison_cannot_use_drifted_baseline_as_valid_evidence(self):
        baseline = self.governed()
        candidate = deepcopy(baseline)
        baseline["metadata"].update(model_snapshot={"version": "A"}, model_snapshot_after={"version": "B"})
        result = compare_runs(baseline, candidate, load_gates())
        self.assertEqual(result["candidate_gate"]["outcome"], "PASS_FOR_WORKSHOP")
        self.assertEqual(result["outcome"], "HOLD")
        self.assertTrue(result["model_comparison"]["baseline_drift_detected"])
        self.assertFalse(result["model_comparison"]["valid"])


class SummaryTests(unittest.TestCase):
    def test_failed_api_calls_stay_in_denominator_and_judges_are_unavailable(self):
        good = scored(judge={"groundedness": 4, "relevance": 5})
        bad = scored(
            "unit-only-2", raw="", error="unit-test timeout",
            judge={"groundedness": 5, "relevance": 5},
        )
        summary = summarize([good, bad], metadata=metadata())
        metrics = summary["metrics"]
        self.assertEqual(metrics["sample_count"], 2)
        self.assertEqual(metrics["format_pass_rate"], 0.5)
        self.assertEqual(metrics["route_accuracy"], 0.5)
        self.assertEqual(metrics["error_count"], 1)
        self.assertEqual(metrics["api_error_count"], 1)
        self.assertEqual(metrics["judge"]["groundedness"]["mean"], 4)
        self.assertEqual(metrics["judge"]["groundedness"]["coverage"], 0.5)

    def test_absent_judge_scores_are_null_and_excluded_not_zero(self):
        rows = [scored(), scored("unit-only-2", judge={"groundedness": 4})]
        metrics = summarize(rows, metadata=metadata())["metrics"]
        self.assertEqual(metrics["judge"]["groundedness"]["mean"], 4)
        self.assertEqual(metrics["judge"]["groundedness"]["scored_count"], 1)
        self.assertEqual(metrics["judge"]["groundedness"]["status"], "partial")
        self.assertIsNone(metrics["judge"]["relevance"]["mean"])
        self.assertEqual(metrics["judge"]["relevance"]["status"], "unavailable")
        self.assertEqual(metrics["judge"]["relevance"]["missing_count"], 2)
        self.assertEqual(evaluate_gates(run(judge_score=None), load_gates())["outcome"], "HOLD")

    def test_judge_errors_excluded_and_coverage_visible(self):
        row = scored(judge={"groundedness": 5, "relevance": 5, "error": "unit-test judge error"})
        metrics = summarize([row], metadata=metadata())["metrics"]
        self.assertEqual(metrics["judge_error_count"], 1)
        self.assertIsNone(metrics["judge"]["groundedness"]["mean"])

    def test_invalid_response_cannot_supply_usable_judge_scores(self):
        row = scored(raw="{}", judge={"groundedness": 5, "relevance": 5})
        metrics = summarize([row], metadata=metadata())["metrics"]
        self.assertEqual(metrics["judge"]["groundedness"]["scored_count"], 0)
        self.assertIsNone(metrics["judge"]["groundedness"]["mean"])

    def test_judge_scale_required_and_zero_cannot_turn_into_pass(self):
        row = scored(judge={"groundedness": 0, "relevance": 0})
        with self.assertRaisesRegex(ValueError, "declared scale"):
            summarize([row], metadata=metadata())
        declared = metadata()
        declared["judge"]["scale"] = [0, 5]
        summary = summarize([row], metadata=declared)
        self.assertEqual(summary["metrics"]["judge"]["groundedness"]["mean"], 0)
        self.assertEqual(evaluate_gates(summary, load_gates())["outcome"], "HOLD")
        with self.assertRaisesRegex(ValueError, "declared scale"):
            summarize([scored(judge={"groundedness": 4})], metadata=metadata(enabled=False))

    def test_type7_latency_quantiles_and_partial_measurements(self):
        rows = [scored(f"unit-only-{i}", latency_ms=value) for i, value in enumerate([10, 20, 30, 40, None])]
        metrics = summarize(rows, metadata=metadata())["metrics"]
        self.assertEqual(metrics["latency_ms"]["p50"], 25)
        self.assertAlmostEqual(metrics["latency_ms"]["p95"], 38.5)
        self.assertEqual(metrics["latency_ms"]["measured_rows"], 4)
        self.assertEqual(metrics["latency_ms"]["missing_rows"], 1)
        self.assertIn("type 7", metrics["latency_ms"]["method"])
        unavailable = summarize([scored()], metadata=metadata())["metrics"]["latency_ms"]
        self.assertIsNone(unavailable["p50"])
        self.assertIsNone(unavailable["p95"])
        single = summarize([scored(latency_ms=0)], metadata=metadata())["metrics"]["latency_ms"]
        self.assertEqual(single["p95"], 0)

    def test_token_sums_are_measured_not_extrapolated(self):
        rows = [scored(usage={"input_tokens": 3, "output_tokens": 2}), scored("unit-only-2")]
        tokens = summarize(rows, metadata=metadata())["metrics"]["tokens"]
        self.assertEqual(tokens["input_tokens"], {"sum": 3, "measured_rows": 1, "missing_rows": 1})
        self.assertIsNone(tokens["total_tokens"]["sum"])

    def test_critical_subsets_and_failures(self):
        rows = [
            scored(tags=["critical", "critical:privacy"], raw=output(route="clarify")),
            scored("unit-only-2"),
        ]
        metrics = summarize(rows, metadata=metadata())["metrics"]
        self.assertEqual(metrics["critical"]["sample_count"], 1)
        self.assertEqual(metrics["critical_rule_failure_count"], 1)
        self.assertEqual(metrics["critical_subsets"]["critical:privacy"]["route_accuracy"], 0)

    def test_empty_duplicates_split_leakage_and_metadata_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            summarize([], metadata=metadata())
        with self.assertRaisesRegex(ValueError, "duplicate"):
            summarize([scored(), scored()], metadata=metadata())
        with self.assertRaisesRegex(ValueError, "leakage"):
            summarize([scored(split="dev")], metadata=metadata(split="test"))
        with self.assertRaisesRegex(ValueError, "leakage"):
            summarize([scored(), scored("other", split="dev")], metadata=metadata())
        wrong_count = metadata()
        wrong_count["sample_count"] = 20
        with self.assertRaisesRegex(ValueError, "sample_count"):
            summarize([scored()], metadata=wrong_count)
        for field in ("dataset_sha256", "judge", "split", "model_deployment"):
            malformed = metadata()
            del malformed[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                summarize([scored()], metadata=malformed)

    def test_tampered_row_and_metrics_rejected(self):
        row = scored(raw=output(route="clarify"))
        row["checks"]["route"] = True
        with self.assertRaisesRegex(ValueError, "raw output"):
            summarize([row], metadata=metadata())
        summary = run()
        summary["metrics"]["route_accuracy"] = 0.999
        with self.assertRaisesRegex(ValueError, "metrics"):
            evaluate_gates(summary, load_gates())
        row = scored()
        row["latency_ms"] = float("nan")
        with self.assertRaises(ValueError):
            summarize([row], metadata=metadata())
        row = scored()
        row["citation_coverage"] = True
        with self.assertRaises(ValueError):
            summarize([row], metadata=metadata())
        summary = run()
        summary["metrics"]["route_accuracy"] = True
        with self.assertRaises(ValueError):
            evaluate_gates(summary, load_gates())

    def test_summary_is_finite_json_and_does_not_mutate_inputs(self):
        rows, declared = [scored()], metadata()
        original_rows, original_meta = deepcopy(rows), deepcopy(declared)
        summary = summarize(rows, metadata=declared)
        self.assertEqual(rows, original_rows)
        self.assertEqual(declared, original_meta)
        self.assertEqual(summary, strict_json_loads(json.dumps(summary, allow_nan=False)))
        summary["rows"][0]["tags"].append("changed")
        self.assertEqual(rows, original_rows)

    def test_wilson_interval_matches_known_boundary_and_rejects_invalid_inputs(self):
        perfect = wilson_interval(20, 20)
        self.assertAlmostEqual(perfect["lower"], 0.8388748419471806)
        self.assertAlmostEqual(perfect["upper"], 1.0)
        zero = wilson_interval(0, 20)
        self.assertAlmostEqual(zero["upper"], 0.16112515805281935)
        self.assertEqual(zero["lower"], 0)
        for args in ((0, 0), (2, 1), (-1, 2), (True, 2), (1, 2.0), (1, 2, 1), (1, 2, float("nan"))):
            with self.subTest(args=args), self.assertRaises(ValueError):
                wilson_interval(*args)


class GateAndComparisonTests(unittest.TestCase):
    def test_passing_default_gate_is_workshop_only(self):
        summary = run()
        gate = evaluate_gates(summary, load_gates())
        self.assertEqual(gate["outcome"], "PASS_FOR_WORKSHOP")
        self.assertFalse(gate["production_ready"])
        self.assertEqual(gate["scope"], "workshop_only")
        self.assertTrue(any("20개" in item for item in gate["limitations"]))

    def test_dev_smoke_and_training_evidence_cannot_release(self):
        for split, stage in (
            ("dev", "candidate"), ("train", "candidate"), ("validation", "candidate"),
            ("test", "smoke"), ("test", "dev"), ("test", "unknown"),
        ):
            with self.subTest(split=split, stage=stage):
                summary = run(split=split, stage=stage)
                gate = evaluate_gates(summary, load_gates())
                self.assertEqual(gate["outcome"], "HOLD")
                self.assertFalse(gate["release_eligible"])
                self.assertEqual(compare_runs(summary, summary, load_gates())["outcome"], "HOLD")

    def test_too_few_test_rows_holds(self):
        self.assertEqual(evaluate_gates(run(count=19), load_gates())["outcome"], "HOLD")

    def test_critical_failure_blocks_even_when_aggregate_route_passes(self):
        summary = run(wrong_routes=1)
        rows = deepcopy(summary["rows"])
        critical_case = case("unit-only-0", tags=["critical"])
        rows[0] = score_row(critical_case, output(route="clarify"), known_citations=KNOWN, judge={"groundedness": 4.5, "relevance": 4.5})
        summary = summarize(rows, metadata=summary["metadata"])
        gate = evaluate_gates(summary, load_gates())
        self.assertEqual(summary["metrics"]["route_accuracy"], 0.95)
        self.assertEqual(gate["outcome"], "HOLD")
        self.assertFalse(next(item for item in gate["checks"] if item["name"] == "critical_rule_failure_count")["passed"])

    def test_configured_critical_tag_also_blocks(self):
        summary = run(wrong_routes=1, critical_rows=0)
        rows = deepcopy(summary["rows"])
        rows[0] = scored("unit-only-0", tags=["privacy"], raw=output(route="clarify"), judge={"groundedness": 4.5, "relevance": 4.5})
        summary = summarize(rows, metadata=summary["metadata"])
        gates = load_gates()
        gates["critical_tags"].append("privacy")
        self.assertEqual(summary["metrics"]["critical_rule_failure_count"], 0)
        gate = evaluate_gates(summary, gates)
        self.assertEqual(gate["critical_sample_count"], 1)
        self.assertEqual(gate["outcome"], "HOLD")

    def test_comparison_pairs_ids_regardless_of_order_and_records_variables(self):
        baseline = run()
        candidate = run(stage="candidate")
        candidate["rows"].reverse()
        candidate["metadata"].update({
            "run_id": "unit-test-only-candidate",
            "model_deployment": "unit-test-only-other-model",
            "prompt_sha256": digest("unit-test-only-other-prompt"),
            "knowledge_sha256": digest("unit-test-only-other-knowledge"),
            "generation_settings": {"temperature": 0.2},
        })
        comparison = compare_runs(baseline, candidate, load_gates())
        self.assertEqual(comparison["outcome"], "PASS_FOR_WORKSHOP")
        self.assertEqual(comparison["sample_count"], 20)
        self.assertTrue(all(v["changed"] for v in comparison["experiment_variables"].values()))
        self.assertIn("generation_settings", comparison["other_metadata_changes"])
        self.assertFalse(comparison["production_ready"])

    def test_dataset_hash_ids_sample_count_and_case_changes_rejected(self):
        baseline = run()
        candidate = run()
        candidate["metadata"]["dataset_sha256"] = digest("different")
        with self.assertRaisesRegex(ValueError, "dataset_sha256"):
            compare_runs(baseline, candidate, load_gates())
        candidate = run()
        candidate["rows"][0]["id"] = "not-a-paired-id"
        with self.assertRaisesRegex(ValueError, "row IDs"):
            compare_runs(baseline, candidate, load_gates())
        with self.assertRaisesRegex(ValueError, "sample_count"):
            compare_runs(baseline, run(count=19), load_gates())
        candidate = run()
        candidate["rows"][0]["case_sha256"] = digest("modified-case")
        with self.assertRaisesRegex(ValueError, "case_sha256"):
            compare_runs(baseline, candidate, load_gates())

    def test_judge_version_settings_provenance_and_scale_must_match(self):
        baseline = run()
        for field, value in (
            ("version", "unit-test-rubric-v2"),
            ("settings", {"temperature": 1}),
            ("settings", {"temperature": False, "seed": 123}),
            ("provenance", {"mode": "different-unit-fixture"}),
            ("prompt_sha256", digest("different-judge-prompt")),
            ("model_deployment", "different-unit-judge"),
        ):
            candidate = run()
            candidate["metadata"]["judge"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "identical judge"):
                compare_runs(baseline, candidate, load_gates())
        candidate = run()
        candidate["metadata"]["judge"]["scale"] = [0, 5]
        candidate = summarize(candidate["rows"], metadata=candidate["metadata"])
        with self.assertRaisesRegex(ValueError, "identical judge"):
            compare_runs(baseline, candidate, load_gates())

    def test_changed_source_catalog_cannot_hide_unchanged_knowledge_hash(self):
        baseline = run()
        candidate = run()
        for row in candidate["rows"]:
            row["known_citations"].append("UNIT-TEST-NEW-SOURCE")
        candidate = summarize(candidate["rows"], metadata=candidate["metadata"])
        with self.assertRaisesRegex(ValueError, "knowledge_sha256"):
            compare_runs(baseline, candidate, load_gates())
        candidate["metadata"]["knowledge_sha256"] = digest("new-unit-only-knowledge")
        self.assertEqual(compare_runs(baseline, candidate, load_gates())["outcome"], "PASS_FOR_WORKSHOP")

    def test_missing_comparison_identity_is_value_error_not_assumed_equal(self):
        for field in ("version", "settings", "provenance"):
            baseline, candidate = run(), run()
            del baseline["metadata"]["judge"][field]
            del candidate["metadata"]["judge"][field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "missing fields"):
                compare_runs(baseline, candidate, load_gates())
        for field in ("dataset_sha256", "sample_count", "prompt_sha256", "model_deployment"):
            baseline, candidate = run(), run()
            del baseline["metadata"][field]
            del candidate["metadata"][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                compare_runs(baseline, candidate, load_gates())

    def test_inclusive_regression_margin_and_paired_failure_ids(self):
        baseline = run()
        allowed = run(wrong_routes=1)
        result = compare_runs(baseline, allowed, load_gates())
        self.assertEqual(result["outcome"], "PASS_FOR_WORKSHOP")
        self.assertEqual(result["paired_changes"]["route"]["regressed_ids"], ["unit-only-0"])
        self.assertEqual(compare_runs(baseline, run(wrong_routes=2), load_gates())["outcome"], "HOLD")

    def test_judge_regression_and_missing_baseline_judge_do_not_pass(self):
        self.assertEqual(compare_runs(run(judge_score=4.2), run(judge_score=4), load_gates())["outcome"], "PASS_FOR_WORKSHOP")
        self.assertEqual(compare_runs(run(judge_score=4.3), run(judge_score=4), load_gates())["outcome"], "HOLD")
        comparison = compare_runs(run(judge_score=None), run(), load_gates())
        self.assertEqual(comparison["outcome"], "HOLD")
        absent = next(item for item in comparison["regression_checks"] if item["metric"] == "groundedness_mean")
        self.assertIsNone(absent["baseline"])
        self.assertEqual(absent["status"], "unavailable")
        self.assertFalse(absent["passed"])

    def test_latency_regression_requires_complete_measured_coverage(self):
        gates = load_gates()
        gates["regression"]["maximum_latency_p95_increase_ratio"] = 0.1
        self.assertEqual(compare_runs(run(), run(), gates)["outcome"], "HOLD")
        baseline, candidate = run(), run()
        for row in baseline["rows"]:
            row["latency_ms"] = 100
        for row in candidate["rows"]:
            row["latency_ms"] = 110
        baseline = summarize(baseline["rows"], metadata=baseline["metadata"])
        candidate = summarize(candidate["rows"], metadata=candidate["metadata"])
        self.assertEqual(compare_runs(baseline, candidate, gates)["outcome"], "PASS_FOR_WORKSHOP")
        for row in candidate["rows"]:
            row["latency_ms"] = 120
        candidate = summarize(candidate["rows"], metadata=candidate["metadata"])
        self.assertEqual(compare_runs(baseline, candidate, gates)["outcome"], "HOLD")

    def test_judge_requirements_can_only_be_opted_out_explicitly(self):
        summary = run(judge_score=None)
        gates = load_gates()
        self.assertEqual(evaluate_gates(summary, gates)["outcome"], "HOLD")
        gates["judge"]["required_metrics"] = []
        self.assertEqual(evaluate_gates(summary, gates)["outcome"], "HOLD")
        summary["rows"][-1]["judge"] = {"groundedness": 4.5, "relevance": 4.5, "error": None}
        summary = summarize(summary["rows"], metadata=summary["metadata"])
        self.assertEqual(evaluate_gates(summary, gates)["outcome"], "PASS_FOR_WORKSHOP")
        self.assertFalse(evaluate_gates(summary, gates)["production_ready"])

    def test_disabled_judge_metadata_is_explicit_and_still_holds_default_gate(self):
        summary = summarize([scored(f"unit-only-{i}") for i in range(20)], metadata=metadata(enabled=False))
        self.assertEqual(compare_runs(summary, summary, load_gates())["outcome"], "HOLD")

    def test_malformed_gates_fail_explicitly(self):
        for value in (float("nan"), float("inf"), -0.1, 1.1, True):
            gates = load_gates()
            gates["minimums"]["route_accuracy"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                evaluate_gates(run(), gates)
        gates = load_gates()
        gates["judge"]["scale"] = [0, 1]
        with self.assertRaises(ValueError):
            evaluate_gates(run(), gates)
        with self.assertRaises(ValueError):
            load_gates(Path("tests") / "deliberately-nonexistent-unit-test-gates.json")

    def test_report_is_korean_explicit_and_contains_no_invented_measurements(self):
        report = Path("tests") / f".evidence-report-{uuid4().hex}.md"
        try:
            write_report(run(judge_score=None), report)
            content = report.read_text(encoding="utf-8")
            self.assertIn("평가 근거 보고서", content)
            self.assertIn("**HOLD**", content)
            self.assertIn("Wilson 95%", content)
            self.assertIn("측정 불가", content)
            self.assertIn("20개", content)
            self.assertIn("증명하지 않습니다", content)
            self.assertIn("USD 비용을 추정하지 않습니다", content)
            self.assertIn("rows[].raw_output", content)
        finally:
            report.unlink(missing_ok=True)

    def test_schema_files_are_strict_json_and_describe_contract(self):
        root = Path(__file__).resolve().parents[1]
        response = strict_json_loads((root / "schemas" / "response.schema.json").read_text(encoding="utf-8"))
        schema = strict_json_loads((root / "schemas" / "run.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(response["required"]), {"answer", "citations", "route", "needs_human"})
        self.assertFalse(response["additionalProperties"])
        self.assertEqual(set(schema["required"]), {"metadata", "rows", "metrics"})
        self.assertEqual(schema["properties"]["rows"]["minItems"], 1)


class BatchIntegrationContractTests(unittest.TestCase):
    """Match parent batch metadata without importing SDKs or invoking services."""

    @staticmethod
    def batch_metadata(rows, *, split="test", source_split="test", stage="iq"):
        declared = metadata(split=split, stage=stage)
        declared.update({
            "source_split": source_split,
            "agent_name": "unit-only-agent",
            "agent_version": "unit-only-version",
            "project_endpoint": "https://unit-only.invalid/api/projects/unit-only",
            "judge": None,
            "parameters": {
                "max_output_tokens": 4096, "max_tool_calls": 3,
                "retries": 0, "timeout_seconds": 120,
            },
            "row_ids": [row["id"] for row in rows],
            "status": "completed",
        })
        return declared

    def test_pre_managed_eval_null_judge_summarizes_as_unavailable(self):
        rows = [scored(f"unit-only-{index}") for index in range(20)]
        declared = self.batch_metadata(rows)
        summary = summarize(rows, metadata=declared)
        self.assertIsNone(summary["metadata"]["judge"])
        self.assertEqual(summary["metadata"]["sample_count"], 20)
        for measurement in summary["metrics"]["judge"].values():
            self.assertIsNone(measurement["mean"])
            self.assertIsNone(measurement["scale"])
            self.assertEqual(measurement["missing_count"], 20)
            self.assertEqual(measurement["status"], "unavailable")
        self.assertEqual(evaluate_gates(summary, load_gates())["outcome"], "HOLD")
        comparison = compare_runs(summary, summary, load_gates())
        self.assertEqual(comparison["outcome"], "HOLD")
        self.assertEqual(comparison["judge_comparison"]["status"], "unavailable")
        self.assertFalse(comparison["judge_comparison"]["comparable"])

    def test_smoke_uses_source_split_without_relabelling_dataset_cases(self):
        rows = [scored("unit-only-1", split="dev"), scored("unit-only-2", split="dev")]
        declared = self.batch_metadata(rows, split="smoke", source_split="dev")
        summary = summarize(rows, metadata=declared)
        self.assertEqual(summary["metadata"]["split"], "smoke")
        self.assertEqual(summary["metadata"]["source_split"], "dev")
        self.assertTrue(all(row["split"] == "dev" for row in summary["rows"]))
        self.assertFalse(evaluate_gates(summary, load_gates())["release_eligible"])
        self.assertEqual(compare_runs(summary, summary, load_gates())["outcome"], "HOLD")

    def test_even_full_count_test_source_smoke_cannot_release(self):
        summary = run(stage="iq")
        summary["metadata"].update({"split": "smoke", "source_split": "test"})
        gate = evaluate_gates(summary, load_gates())
        self.assertEqual(gate["outcome"], "HOLD")
        self.assertFalse(gate["release_eligible"])

    def test_source_split_cannot_mask_leakage_and_smoke_requires_source(self):
        rows = [scored(split="dev")]
        declared = self.batch_metadata(rows, split="test", source_split="dev")
        with self.assertRaisesRegex(ValueError, "leakage"):
            summarize(rows, metadata=declared)
        declared["split"] = "smoke"
        declared["source_split"] = "test"
        with self.assertRaisesRegex(ValueError, "leakage"):
            summarize(rows, metadata=declared)
        del declared["source_split"]
        with self.assertRaisesRegex(ValueError, "source_split"):
            summarize(rows, metadata=declared)

    def test_managed_eval_subset_cannot_remove_failed_service_rows(self):
        rows = [
            scored("unit-only-1"),
            scored("unit-only-2", raw="", error="unit-only service error"),
        ]
        declared = self.batch_metadata(rows)
        declared["status"] = "completed_with_errors"
        summary = summarize(rows, metadata=declared)
        self.assertEqual(summary["metrics"]["sample_count"], 2)
        self.assertEqual(summary["metrics"]["route_accuracy"], 0.5)
        self.assertEqual(summary["metrics"]["api_error_count"], 1)
        with self.assertRaisesRegex(ValueError, "all attempted rows"):
            summarize(rows[:1], metadata=declared)
        declared["row_ids"] = ["unit-only-1", "unit-only-other"]
        with self.assertRaisesRegex(ValueError, "row IDs"):
            summarize(rows, metadata=declared)

    def test_scores_require_declared_metadata_after_managed_import(self):
        rows = [scored(judge={"groundedness": 4, "relevance": 5})]
        declared = self.batch_metadata(rows)
        with self.assertRaisesRegex(ValueError, "declared scale"):
            summarize(rows, metadata=declared)
        declared["judge"] = metadata()["judge"]
        summary = summarize(rows, metadata=declared)
        self.assertEqual(summary["metrics"]["judge"]["groundedness"]["mean"], 4)
        self.assertEqual(summary["metrics"]["judge"]["relevance"]["mean"], 5)

    def test_one_missing_judge_returns_hold_not_a_comparable_claim(self):
        baseline = run(judge_score=None, stage="iq")
        baseline["metadata"]["judge"] = None
        baseline = summarize(baseline["rows"], metadata=baseline["metadata"])
        candidate = run(stage="optimized")
        for old, new in ((baseline, candidate), (candidate, baseline)):
            comparison = compare_runs(old, new, load_gates())
            self.assertEqual(comparison["outcome"], "HOLD")
            self.assertFalse(comparison["judge_comparison"]["comparable"])
        gates = load_gates()
        gates["judge"]["required_metrics"] = []
        self.assertEqual(compare_runs(baseline, candidate, gates)["outcome"], "HOLD")
        self.assertEqual(compare_runs(candidate, baseline, gates)["outcome"], "HOLD")

    def test_iq_to_optimized_heldout_records_prompt_only_experiment(self):
        baseline, candidate = run(stage="iq"), run(stage="optimized")
        candidate["metadata"]["prompt_sha256"] = digest("unit-only-optimized-prompt")
        comparison = compare_runs(baseline, candidate, load_gates())
        self.assertEqual(comparison["outcome"], "PASS_FOR_WORKSHOP")
        self.assertTrue(comparison["experiment_variables"]["prompt_sha256"]["changed"])
        self.assertFalse(comparison["experiment_variables"]["model_deployment"]["changed"])
        self.assertFalse(comparison["experiment_variables"]["knowledge_sha256"]["changed"])

    def test_baseline_to_iq_records_knowledge_change_without_prompt_or_model_change(self):
        baseline, candidate = run(stage="baseline"), run(stage="iq")
        candidate["metadata"]["knowledge_sha256"] = digest("unit-only-iq-tool-knowledge")
        comparison = compare_runs(baseline, candidate, load_gates())
        self.assertEqual(comparison["outcome"], "PASS_FOR_WORKSHOP")
        self.assertTrue(comparison["experiment_variables"]["knowledge_sha256"]["changed"])
        self.assertFalse(comparison["experiment_variables"]["prompt_sha256"]["changed"])
        self.assertFalse(comparison["experiment_variables"]["model_deployment"]["changed"])

    def test_incomplete_batch_cannot_pass_gate(self):
        summary = run(stage="iq")
        summary["metadata"]["status"] = "running"
        self.assertEqual(evaluate_gates(summary, load_gates())["outcome"], "HOLD")

    def test_extra_measured_api_usage_details_are_accepted_without_invention(self):
        row = scored(usage={
            "input_tokens": 3, "output_tokens": 2, "total_tokens": 5,
            "input_tokens_details": {"cached_tokens": 1},
            "output_tokens_details": {"reasoning_tokens": 0},
        })
        self.assertEqual(row["usage"], {
            "input_tokens": 3, "output_tokens": 2, "total_tokens": 5,
        })

    def test_pre_managed_eval_smoke_report_is_persistent_then_cleaned(self):
        rows = [scored(split="dev")]
        summary = summarize(
            rows,
            metadata=self.batch_metadata(rows, split="smoke", source_split="dev"),
        )
        report = Path("tests") / f".evidence-report-{uuid4().hex}.md"
        try:
            write_report(summary, report)
            content = report.read_text(encoding="utf-8")
            self.assertIn("**HOLD**", content)
            self.assertIn("원본 데이터 split: dev", content)
            self.assertIn("unavailable", content)
            self.assertIn("smoke", content)
        finally:
            report.unlink(missing_ok=True)


class PerMetricJudgeScaleTests(unittest.TestCase):
    @staticmethod
    def per_metric_summary(*, groundedness=4.5, relevance=4.5, scales=None):
        rows = [
            scored(
                f"unit-only-{index}",
                tags=["unit-test-only", "critical"] if index == 19 else ["unit-test-only"],
                judge={"groundedness": groundedness, "relevance": relevance},
            )
            for index in range(20)
        ]
        declared = metadata(stage="iq")
        declared["judge"]["scale"] = (
            {"groundedness": [1, 5], "relevance": [1, 5]}
            if scales is None else scales
        )
        return summarize(rows, metadata=declared)

    def test_managed_per_metric_scales_preserve_metadata_and_gate_normally(self):
        summary = self.per_metric_summary()
        self.assertEqual(summary["metadata"]["judge"]["scale"], {
            "groundedness": [1, 5], "relevance": [1, 5],
        })
        for measurement in summary["metrics"]["judge"].values():
            self.assertEqual(measurement["scale"], [1, 5])
            self.assertEqual(measurement["mean"], 4.5)
            self.assertEqual(measurement["coverage"], 1)
        self.assertEqual(evaluate_gates(summary, load_gates())["outcome"], "PASS_FOR_WORKSHOP")
        self.assertEqual(compare_runs(summary, summary, load_gates())["outcome"], "PASS_FOR_WORKSHOP")

    def test_scales_are_per_metric_not_silently_rescaled(self):
        summary = self.per_metric_summary(
            relevance=0.5,
            scales={"groundedness": [1, 5], "relevance": [0, 1]},
        )
        self.assertEqual(summary["metrics"]["judge"]["groundedness"]["mean"], 4.5)
        self.assertEqual(summary["metrics"]["judge"]["relevance"]["mean"], 0.5)
        self.assertEqual(summary["metrics"]["judge"]["relevance"]["scale"], [0, 1])
        gate = evaluate_gates(summary, load_gates())
        self.assertEqual(gate["outcome"], "HOLD")
        scale_check = next(item for item in gate["checks"] if item["name"] == "relevance_scale")
        self.assertFalse(scale_check["passed"])
        with self.assertRaisesRegex(ValueError, "relevance.*declared scale"):
            self.per_metric_summary(scales={"groundedness": [1, 5], "relevance": [0, 1]})

    def test_malformed_or_partial_scale_mapping_is_rejected(self):
        for scales in (
            {},
            {"groundedness": [1, 5]},
            {"groundedness": [1, 5], "relevance": None},
            {"groundedness": [1, 5], "relevance": [5, 1]},
            {"groundedness": [1, 5], "relevance": [True, 5]},
            {"groundedness": [1, 5], "relevance": [1, float("inf")]},
            {"groundedness": [1, 5], "relevance": [1, 5], "unknown": [1, 5]},
        ):
            with self.subTest(scales=scales), self.assertRaises(ValueError):
                self.per_metric_summary(scales=scales)

    def test_gate_configuration_can_also_declare_per_metric_scales(self):
        gates = load_gates()
        gates["judge"]["scale"] = {"groundedness": [1, 5], "relevance": [1, 5]}
        summary = self.per_metric_summary()
        self.assertEqual(evaluate_gates(summary, gates)["outcome"], "PASS_FOR_WORKSHOP")
        self.assertEqual(compare_runs(summary, summary, gates)["outcome"], "PASS_FOR_WORKSHOP")
        gates["judge"]["scale"]["relevance"] = [0, 1]
        with self.assertRaisesRegex(ValueError, "declared scale"):
            evaluate_gates(summary, gates)

    def test_comparison_requires_identical_declared_judge_contract(self):
        baseline = run()
        candidate = self.per_metric_summary()
        with self.assertRaisesRegex(ValueError, "identical judge"):
            compare_runs(baseline, candidate, load_gates())
        candidate = self.per_metric_summary(
            relevance=4.5, scales={"groundedness": [0, 5], "relevance": [1, 5]},
        )
        with self.assertRaisesRegex(ValueError, "identical judge"):
            compare_runs(self.per_metric_summary(), candidate, load_gates())

    def test_missing_failed_row_judges_still_reduce_per_metric_coverage(self):
        rows = [
            scored("unit-only-1", judge={"groundedness": 4, "relevance": 5}),
            scored("unit-only-2", raw="", error="unit-only failed service call"),
        ]
        declared = metadata()
        declared["judge"]["scale"] = {"groundedness": [1, 5], "relevance": [1, 5]}
        summary = summarize(rows, metadata=declared)
        self.assertEqual(summary["metrics"]["sample_count"], 2)
        self.assertEqual(summary["metrics"]["error_count"], 1)
        for name in ("groundedness", "relevance"):
            self.assertEqual(summary["metrics"]["judge"][name]["coverage"], 0.5)
            self.assertEqual(summary["metrics"]["judge"][name]["missing_count"], 1)
            self.assertEqual(summary["metrics"]["judge"][name]["scale"], [1, 5])


class CriticalJudgeFloorTests(unittest.TestCase):
    @staticmethod
    def change_critical_scores(summary, **changes):
        rows = deepcopy(summary["rows"])
        rows[-1]["judge"].update(changes)
        return summarize(rows, metadata=summary["metadata"])

    def test_default_policy_is_explicitly_pedagogical(self):
        gates = load_gates()
        self.assertEqual(gates["minimum_critical_rows"], 1)
        self.assertEqual(gates["judge"]["critical_minimum_score"], {
            "groundedness": 4.0, "relevance": 4.0,
        })
        self.assertIn("교육용", gates["description"])
        self.assertIn("Microsoft 공식 평가 기준이 아닙니다", gates["description"])

    def test_nineteen_fives_cannot_hide_one_critical_one(self):
        baseline = run(judge_score=5)
        for name in ("groundedness", "relevance"):
            with self.subTest(metric=name):
                candidate = self.change_critical_scores(baseline, **{name: 1})
                metrics = candidate["metrics"]
                self.assertAlmostEqual(metrics["judge"][name]["mean"], 4.8)
                self.assertEqual(metrics["format_pass_rate"], 1)
                self.assertEqual(metrics["route_accuracy"], 1)
                self.assertEqual(metrics["citation_pass_rate"], 1)
                self.assertEqual(metrics["critical_rule_failure_count"], 0)
                gate = evaluate_gates(candidate, load_gates())
                self.assertEqual(gate["outcome"], "HOLD")
                self.assertTrue(next(check for check in gate["checks"] if check["name"] == f"{name}_mean")["passed"])
                self.assertFalse(next(check for check in gate["checks"] if check["name"] == f"critical_{name}_floor")["passed"])
                self.assertEqual(gate["critical_judge"][name]["minimum_observed"], 1)
                self.assertEqual(gate["critical_judge"][name]["below_floor_ids"], ["unit-only-19"])
                comparison = compare_runs(baseline, candidate, load_gates())
                self.assertTrue(all(check["passed"] for check in comparison["regression_checks"]))
                self.assertEqual(comparison["outcome"], "HOLD")

    def test_all_critical_rows_at_floor_pass_including_tuned_stage(self):
        summary = run(judge_score=4, critical_rows=20, stage="tuned")
        gate = evaluate_gates(summary, load_gates())
        self.assertEqual(gate["outcome"], "PASS_FOR_WORKSHOP")
        self.assertEqual(gate["critical_sample_count"], 20)
        for measurement in gate["critical_judge"].values():
            self.assertEqual(measurement["minimum_observed"], 4)
            self.assertEqual(measurement["scored_count"], 20)
            self.assertEqual(measurement["missing_count"], 0)
            self.assertTrue(measurement["passed"])
        self.assertEqual(compare_runs(summary, summary, load_gates())["outcome"], "PASS_FOR_WORKSHOP")

    def test_null_critical_score_holds_even_when_overall_mean_is_five(self):
        for name in ("groundedness", "relevance"):
            with self.subTest(metric=name):
                summary = self.change_critical_scores(run(judge_score=5), **{name: None})
                self.assertEqual(summary["metrics"]["judge"][name]["mean"], 5)
                gate = evaluate_gates(summary, load_gates())
                self.assertEqual(gate["outcome"], "HOLD")
                measurement = gate["critical_judge"][name]
                self.assertIsNone(measurement["minimum_observed"])
                self.assertEqual(measurement["missing_count"], 1)
                self.assertEqual(measurement["unavailable_ids"], ["unit-only-19"])
                self.assertEqual(measurement["status"], "unavailable")
                self.assertFalse(measurement["passed"])
                gates = load_gates()
                gates["judge"]["required_metrics"] = []
                self.assertEqual(evaluate_gates(summary, gates)["outcome"], "HOLD")

    def test_critical_judge_error_is_unavailable_despite_numeric_fives(self):
        summary = self.change_critical_scores(
            run(judge_score=5), error="unit-only critical judge error"
        )
        gate = evaluate_gates(summary, load_gates())
        self.assertEqual(gate["outcome"], "HOLD")
        for name in ("groundedness", "relevance"):
            self.assertEqual(summary["metrics"]["judge"][name]["mean"], 5)
            self.assertIsNone(gate["critical_judge"][name]["minimum_observed"])
            self.assertEqual(gate["critical_judge"][name]["unavailable_ids"], ["unit-only-19"])

    def test_critical_api_failure_cannot_supply_a_passing_judge_score(self):
        summary = run(judge_score=5)
        summary["rows"][-1] = scored(
            "unit-only-19", tags=["unit-test-only", "critical"], error="unit-only API error",
            judge={"groundedness": 5, "relevance": 5},
        )
        summary = summarize(summary["rows"], metadata=summary["metadata"])
        gate = evaluate_gates(summary, load_gates())
        self.assertEqual(gate["outcome"], "HOLD")
        self.assertTrue(all(
            measurement["unavailable_ids"] == ["unit-only-19"]
            for measurement in gate["critical_judge"].values()
        ))

    def test_no_critical_rows_is_missing_coverage_not_vacuous_success(self):
        summary = run(judge_score=5, critical_rows=0)
        gate = evaluate_gates(summary, load_gates())
        self.assertEqual(gate["outcome"], "HOLD")
        self.assertEqual(gate["critical_sample_count"], 0)
        coverage = next(check for check in gate["checks"] if check["name"] == "minimum_critical_rows")
        self.assertEqual(coverage["actual"], 0)
        self.assertEqual(coverage["required"], 1)
        self.assertFalse(coverage["passed"])
        for measurement in gate["critical_judge"].values():
            self.assertIsNone(measurement["minimum_observed"])
            self.assertEqual(measurement["scored_count"], 0)
            self.assertFalse(measurement["passed"])
        self.assertEqual(compare_runs(summary, summary, load_gates())["outcome"], "HOLD")

    def test_omitted_optional_fields_keep_safe_defaults(self):
        gates = load_gates()
        del gates["minimum_critical_rows"]
        del gates["judge"]["critical_minimum_score"]
        self.assertEqual(evaluate_gates(run(), gates)["outcome"], "PASS_FOR_WORKSHOP")
        bad = self.change_critical_scores(run(judge_score=5), groundedness=1)
        self.assertEqual(evaluate_gates(bad, gates)["outcome"], "HOLD")
        self.assertEqual(evaluate_gates(run(critical_rows=0), gates)["outcome"], "HOLD")

    def test_explicit_coverage_and_independent_floor_overrides(self):
        gates = load_gates()
        gates["minimum_critical_rows"] = 2
        self.assertEqual(evaluate_gates(run(), gates)["outcome"], "HOLD")
        self.assertEqual(evaluate_gates(run(critical_rows=2), gates)["outcome"], "PASS_FOR_WORKSHOP")
        gates["judge"]["critical_minimum_score"] = {"groundedness": 5, "relevance": 4}
        gate = evaluate_gates(run(critical_rows=2), gates)
        self.assertEqual(gate["outcome"], "HOLD")
        self.assertFalse(gate["critical_judge"]["groundedness"]["passed"])
        self.assertTrue(gate["critical_judge"]["relevance"]["passed"])
        self.assertEqual(gate["critical_judge"]["groundedness"]["minimum_required"], 5)

    def test_malformed_critical_policy_is_rejected(self):
        for value in (0, -1, 1.0, True, None, float("nan"), "1"):
            gates = load_gates()
            gates["minimum_critical_rows"] = value
            with self.subTest(minimum_rows=value), self.assertRaises(ValueError):
                evaluate_gates(run(), gates)
        for value in (0, 6, True, None, float("nan"), float("inf"), "4"):
            gates = load_gates()
            gates["judge"]["critical_minimum_score"]["groundedness"] = value
            with self.subTest(floor=value), self.assertRaises(ValueError):
                evaluate_gates(run(), gates)
        for value in (
            None, {}, [], {"groundedness": 4},
            {"groundedness": 4, "relevance": 4, "unknown": 4},
        ):
            gates = load_gates()
            gates["judge"]["critical_minimum_score"] = value
            with self.subTest(floors=value), self.assertRaises(ValueError):
                evaluate_gates(run(), gates)

    def test_critical_floor_requires_declared_one_to_five_scale_independently(self):
        summary = run(judge_score=5)
        summary["metadata"]["judge"]["scale"] = {"groundedness": [0, 5], "relevance": [1, 5]}
        summary = summarize(summary["rows"], metadata=summary["metadata"])
        gates = load_gates()
        gates["judge"]["required_metrics"] = []
        gate = evaluate_gates(summary, gates)
        self.assertEqual(gate["outcome"], "HOLD")
        self.assertFalse(gate["critical_judge"]["groundedness"]["scale_compatible"])
        self.assertFalse(gate["critical_judge"]["groundedness"]["passed"])
        self.assertTrue(gate["critical_judge"]["relevance"]["passed"])

    def test_prefix_and_configured_critical_tags_get_semantic_floors(self):
        for tag in ("critical:privacy", "privacy"):
            with self.subTest(tag=tag):
                summary = run(judge_score=5, critical_rows=0)
                summary["rows"][-1] = scored(
                    "unit-only-19", tags=["unit-test-only", tag],
                    judge={"groundedness": 1, "relevance": 5},
                )
                summary = summarize(summary["rows"], metadata=summary["metadata"])
                gates = load_gates()
                if tag == "privacy":
                    gates["critical_tags"].append(tag)
                gate = evaluate_gates(summary, gates)
                self.assertEqual(gate["critical_sample_count"], 1)
                self.assertEqual(gate["outcome"], "HOLD")
                self.assertEqual(gate["critical_judge"]["groundedness"]["below_floor_ids"], ["unit-only-19"])

    def test_report_exposes_pedagogical_critical_floor_and_failing_id(self):
        summary = self.change_critical_scores(run(judge_score=5), groundedness=1)
        report = Path("tests") / f".evidence-critical-report-{uuid4().hex}.md"
        try:
            write_report(summary, report)
            content = report.read_text(encoding="utf-8")
            self.assertIn("**HOLD**", content)
            self.assertIn("교육용 행별 하한", content)
            self.assertIn("Microsoft 공식 평가 기준이 아닙니다", content)
            self.assertIn("하한 미달 ID", content)
            self.assertIn("누락·오류 ID", content)
            self.assertIn("unit-only-19", content)
            self.assertIn("최소 요구 1행", content)
        finally:
            report.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
