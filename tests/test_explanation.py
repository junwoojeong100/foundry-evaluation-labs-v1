"""Read-only explanations use synthetic judgments, never live model calls."""

from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from lab.cli import main
from lab.config import LabError
from lab.evidence import load_gates, score_row, summarize, write_report
from lab.explanation import explain_run
from lab.files import ROOT, read_json, read_jsonl, sha256_file, write_jsonl
from lab.preflight import save_json


class ExplanationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        patched = patch("lab.files.ARTIFACTS", self.root)
        patched.start()
        self.addCleanup(patched.stop)
        self.dataset = ROOT / "data/splits/dev.jsonl"
        self.cases = read_jsonl(self.dataset)
        self.known = {document["id"] for document in read_json(ROOT / "data/knowledge/documents.json")}

    def make_run(self, identifier, *, count=3, stage="iq", score=4, no_retrieval=False, raw=None, frozen=False, language=None):
        directory = self.root / "runs" / identifier
        directory.mkdir(parents=True)
        cases = self.cases[:count]
        captures, judges = [], {}
        for index, case in enumerate(cases):
            captures.append({
                "id": case["id"], "raw_output": raw if index == 0 and raw is not None else case["ground_truth"],
                "retrieved_context": "" if no_retrieval else case["context"],
                "error": None, "latency_ms": 10, "usage": None,
            })
            judges[case["id"]] = {
                "policy_correctness": score, "groundedness": None if no_retrieval else score,
                "relevance": score, "critical_failure": False,
                "reasons": {"policy": "단위 테스트용 업무 판단 이유", **({} if no_retrieval else {"retrieval": "단위 테스트용 실제 문맥 근거"})},
                "metric_errors": {"groundedness": "retrieval_not_observed"} if no_retrieval else {},
            }
        write_jsonl(directory / "outputs.jsonl", captures)
        save_json(directory / "judge-scores.json", judges)
        metadata = {
            **({"language": language} if language is not None else {}),
            "run_id": identifier, "stage": stage, "status": "completed",
            "split": "dev" if count == len(self.cases) else "smoke", "source_split": "dev",
            "row_ids": [case["id"] for case in cases],
            "dataset_sha256": sha256_file(self.dataset),
            "outputs_sha256": sha256_file(directory / "outputs.jsonl"),
            "model_deployment": "unit-test-model",
            "prompt_sha256": hashlib.sha256(stage.encode()).hexdigest(),
            "knowledge_sha256": hashlib.sha256(b"unit-test-knowledge").hexdigest(),
            "evaluation_contract_version": "atlas-evaluation-v1",
            "judge": {
                "model_deployment": "unit-test-judge", "prompt_sha256": "a" * 64,
                "version": "unit-test-only", "scale": [1, 5], "settings": {"test": True},
                "provenance": {"kind": "synthetic-test-not-live"},
            },
        }
        if frozen:
            metadata.update(freeze_id="unit-freeze", freeze_sha256="f" * 64)
        rows = [
            score_row(case, capture["raw_output"], known_citations=self.known, latency_ms=10,
                      judge=judges[case["id"]], retrieved_context=capture["retrieved_context"])
            for case, capture in zip(cases, captures, strict=True)
        ]
        save_json(directory / "metadata.json", metadata)
        save_json(directory / "summary.json", summarize(rows, metadata=metadata))
        return directory

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}

    def test_real_fields_reasons_and_improvement_hints_are_visible_without_writes(self):
        self.make_run("example", score=3)
        before = self.snapshot()
        text = explain_run("example")
        self.assertEqual(before, self.snapshot())
        self.assertIn("추가 모델 호출 0", text)
        self.assertIn("업무 정확성", text)
        self.assertIn("점수 3/3", text)
        self.assertIn("≥85%", text)
        self.assertIn("단위 테스트용 업무 판단 이유", text)
        self.assertIn("단위 테스트용 실제 문맥 근거", text)
        self.assertIn(self.cases[0]["query"], text)
        self.assertIn(self.cases[0]["ground_truth"], text)
        self.assertIn("최신 정책의 적용 시점", text)
        self.assertIn("not_granted", text)

    def test_english_explanation_localizes_labels_without_rewriting_actual_evidence(self):
        self.dataset = ROOT / "data/en/splits/dev.jsonl"
        self.cases = read_jsonl(self.dataset)
        self.known = {document["id"] for document in read_json(ROOT / "data/en/knowledge/documents.json")}
        with patch.dict(os.environ, {"LAB_LANGUAGE": "en"}):
            directory = self.make_run("english", score=3, language="en")
            before = self.snapshot()
            result = explain_run("english")
            self.assertEqual(before, self.snapshot())
            self.assertIn("# Evaluation explained", result)
            self.assertIn("Policy correctness", result)
            self.assertIn("scored 3/3", result)
            self.assertIn("HOLD causes", result)
            self.assertNotIn("# 평가 결과 해설", result)
            self.assertIn(self.cases[0]["ground_truth"], result)
            self.assertIn("단위 테스트용 업무 판단 이유", result)
            report = directory / "english-report.md"
            write_report(read_json(directory / "summary.json"), report)
            rendered = report.read_text()
            self.assertIn("# Foundry workshop evaluation evidence", rendered)
            self.assertIn("Interpretation limits", rendered)
            self.assertNotIn("## 해석의 한계", rendered)

    def test_baseline_missing_grounding_is_not_zero_or_a_false_pass(self):
        self.make_run("baseline", stage="baseline", no_retrieval=True)
        text = explain_run("baseline")
        self.assertIn("검색 미측정", text)
        self.assertIn("미측정 | 평균 ≥4 | 점수 0/3", text)
        self.assertIn("미기록 — 이유를 추정하거나 생성하지 않습니다", text)
        self.assertIn("**HOLD**", text)

    def test_invalid_json_response_is_explained_not_crashed_or_repaired(self):
        self.make_run("bad-json", raw='["not an object"]')
        text = explain_run("bad-json")
        self.assertIn('["not an object"]', text)
        self.assertIn("실제 route: 형식 오류", text)
        self.assertIn("네 필드 JSON", text)

    def test_pair_uses_existing_regression_engine_and_shows_both_responses(self):
        self.make_run("before", count=12, score=5)
        self.make_run("after", count=12, stage="optimized", score=4)
        before = self.snapshot()
        text = explain_run("after", baseline_id="before")
        self.assertEqual(before, self.snapshot())
        self.assertIn("자동 회귀 진단", text)
        self.assertIn("| groundedness_mean | 5.00점 | 4.00점 | 1.00점 | 0.20점 | 미충족/미측정 |", text)
        self.assertIn("이전 최종 응답", text)
        self.assertIn("업무 정확성의 전후 변화", text)
        self.assertIn("사람이 확인", text)
        self.assertIn("**HOLD**", text)

    def test_different_sample_counts_are_not_silently_compared(self):
        self.make_run("small", count=3)
        self.make_run("large", count=12)
        with self.assertRaisesRegex(ValueError, "paired comparison requires identical"):
            explain_run("large", baseline_id="small")

    def test_case_selection_keeps_all_rows_and_gate_denominators(self):
        self.make_run("twelve", count=12)
        selected = self.cases[-1]["id"]
        text = explain_run("twelve", case_id=selected)
        self.assertEqual(text.count("### 사례 "), 1)
        self.assertIn("상세 해설은 1/12건", text)
        self.assertIn("점수 12/12", text)
        self.assertTrue(all(case["id"] in text for case in self.cases))
        with self.assertRaisesRegex(LabError, "사례 ID"):
            explain_run("twelve", case_id="not-in-this-run")

    def test_default_details_are_bounded_while_every_case_remains_in_the_table(self):
        self.make_run("twelve", count=12)
        text = explain_run("twelve")
        self.assertEqual(text.count("### 사례 "), 3)
        self.assertTrue(all(case["id"] in text for case in self.cases))

    def test_dialogue_keeps_initial_and_scripted_followup_turns_visible(self):
        directory = self.make_run("dialogue")
        captures = read_jsonl(directory / "outputs.jsonl")
        captures[0]["turns"] = [
            {"input": self.cases[0]["query"], "input_source": "dataset_query", "raw_output": "초기 응답도 확인해야 합니다."},
            {"input": "명시적으로 제공한 후속 정보", "input_source": "scripted_user", "raw_output": captures[0]["raw_output"]},
        ]
        write_jsonl(directory / "outputs.jsonl", captures)
        digest = sha256_file(directory / "outputs.jsonl")
        metadata = read_json(directory / "metadata.json")
        metadata["outputs_sha256"] = digest
        save_json(directory / "metadata.json", metadata)
        summary = read_json(directory / "summary.json")
        summary["metadata"]["outputs_sha256"] = digest
        save_json(directory / "summary.json", summary)
        text = explain_run("dialogue", case_id=self.cases[0]["id"])
        self.assertIn("초기 응답도 확인해야 합니다.", text)
        self.assertIn("명시적으로 제공한 후속 정보", text)
        self.assertIn("입력 출처: scripted_user", text)

    def test_explicit_empty_selectors_do_not_silently_fall_back(self):
        self.make_run("example")
        with self.assertRaises(LabError):
            explain_run("example", case_id="")
        with self.assertRaises(LabError):
            explain_run("example", baseline_id="")

    def test_modified_judge_reasons_are_rejected_instead_of_mixed_with_old_metrics(self):
        directory = self.make_run("tampered")
        scores = read_json(directory / "judge-scores.json")
        scores[self.cases[0]["id"]]["reasons"]["policy"] = "changed after scoring"
        save_json(directory / "judge-scores.json", scores)
        with self.assertRaisesRegex(LabError, "summary가 다릅니다"):
            explain_run("tampered")

    def test_modified_captures_are_rejected(self):
        directory = self.make_run("capture-change")
        captures = read_jsonl(directory / "outputs.jsonl")
        captures[0]["raw_output"] = "{}"
        write_jsonl(directory / "outputs.jsonl", captures)
        with self.assertRaisesRegex(LabError, "원본 응답 파일"):
            explain_run("capture-change")

    def test_summary_cannot_expand_the_real_citation_catalog(self):
        directory = self.make_run("citation-change")
        summary = read_json(directory / "summary.json")
        summary["rows"][0]["known_citations"] = sorted([*summary["rows"][0]["known_citations"], "MADE-UP-ID"])
        save_json(directory / "summary.json", summary)
        with self.assertRaisesRegex(LabError, "summary가 다릅니다"):
            explain_run("citation-change")

    def test_saved_frozen_gate_is_used_without_lowering_the_global_gate(self):
        self.make_run("frozen", count=12, frozen=True)
        original = load_gates()
        frozen = deepcopy(original)
        frozen["minimum_test_rows"] = 12
        with patch("lab.governance.governance_status", return_value={"quality_status": "NOT_EVALUATED"}), \
             patch("lab.governance.validate_frozen_run", return_value={"content_sha256": "f" * 64, "gates": frozen}) as load:
            text = explain_run("frozen")
        load.assert_called_once_with("unit-freeze", "frozen")
        self.assertIn("동결된 게이트; 최종 최소 표본 12건", text)
        self.assertEqual(load_gates()["minimum_test_rows"], 20)

    def test_finalized_result_is_read_without_reopening_its_evaluation_attempt(self):
        self.make_run("finished", count=12, frozen=True)
        with patch("lab.governance.governance_status", return_value={"run_id": "finished", "quality_status": "HOLD"}) as status, \
             patch("lab.governance.load_freeze", return_value={"content_sha256": "f" * 64, "gates": load_gates()}), \
             patch("lab.governance.validate_frozen_run", side_effect=AssertionError("final attempt must stay closed")):
            text = explain_run("finished")
        status.assert_called_once_with("unit-freeze")
        self.assertIn("저장된 최종 판정: **HOLD**", text)

    def test_untrusted_response_stays_inside_a_longer_code_fence(self):
        self.make_run("quoted", raw="```\n<script>alert('not executed')</script>\n```")
        text = explain_run("quoted")
        self.assertIn("````text\n```\n<script>", text)
        self.assertIn("\n```\n````", text)

    def test_cli_does_not_load_environment_or_create_cloud_clients(self):
        self.make_run("local")
        output = io.StringIO()
        with redirect_stdout(output), patch("lab.cli.load_config", side_effect=AssertionError("no credentials")), \
             patch("lab.batch.AIProjectClient", side_effect=AssertionError("no cloud client")):
            self.assertEqual(main(["--config", "does-not-exist.env", "explain", "--run-id", "local"]), 0)
        self.assertIn("평가 결과 해설", output.getvalue())

    def test_missing_summary_and_bad_ids_fail_explicitly(self):
        for identifier in ("missing", "../outside"):
            with self.subTest(identifier=identifier):
                error = io.StringIO()
                with redirect_stderr(error):
                    self.assertEqual(main(["explain", "--run-id", identifier]), 1)
                self.assertIn("ERROR:", error.getvalue())


if __name__ == "__main__":
    unittest.main()
