"""Project-local synthetic governance fixtures; no LIVE or human approval."""

from copy import deepcopy
from contextlib import nullcontext, redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import io
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from lab import calibration, governance
from lab.config import LabError
from lab.evidence import evaluate_gates, score_row, summarize
from lab.files import ROOT as SOURCE_ROOT, sha256_file, write_jsonl


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("artifacts") / f"test-governance-{uuid4().hex}"
        self.package, self.artifacts = self.root / "package", self.root / "evidence"
        self.package.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root)
        shutil.copytree(SOURCE_ROOT / "data", self.package / "data")
        shutil.copytree(SOURCE_ROOT / "config", self.package / "config")
        (self.package / "lab").mkdir()
        for name in ("calibration.py", "evidence.py", "batch.py", "managed_eval.py", "governance.py"):
            shutil.copyfile(SOURCE_ROOT / "lab" / name, self.package / "lab" / name)
        for target in ("lab.governance.ROOT", "lab.calibration.ROOT", "lab.batch.ROOT"):
            self.patch(target, self.package)
        for target in ("lab.governance.artifacts_dir", "lab.calibration.artifacts_dir", "lab.files.artifacts_dir"):
            self.patch(target, return_value=self.artifacts)
        self.config = SimpleNamespace(judge="unit-only-judge", project_endpoint="https://unit-test.invalid/project")
        self.prompt = self.artifacts / "agents/prompts/candidate.txt"
        self.prompt.parent.mkdir(parents=True)
        self.prompt.write_text("Unit-test-only prompt; never submitted.", encoding="utf-8")
        self.snapshot = {"deployment": "unit-only-model", "model": {"name": "unit-only", "version": "1"}}
        self.judge_snapshot = {"deployment": self.config.judge, "model": {"name": "unit-only", "version": "2"}}
        self.agent = {
            "name": "unit-only-agent", "version": "1", "stage": "baseline",
            "workspace_id": "unit-only-workspace", "model_deployment": "unit-only-model",
            "model_snapshot": self.snapshot, "prompt_sha256": sha256_file(self.prompt),
            "prompt_snapshot": str(self.prompt.resolve()), "prompt_source": "unit-test-only",
            "knowledge_sha256": hashlib.sha256(b"").hexdigest(),
        }
        calibration.save_json(self.artifacts / "agents/baseline.json", self.agent)
        self.patch("lab.governance.load_agent", return_value=self.agent)
        self.report_path = self.artifacts / "calibration/mock-calibration/report.json"
        contract = calibration.evaluator_contract()
        fixture_path = self.package / "data/calibration/fixtures.jsonl"
        fixtures = calibration.load_fixtures()
        judged = [{
            "id": fixture["id"], "judge": {
                **{metric: None if label is None else 5 if label else 2 for metric, label in fixture["reference_labels"].items()},
                "error": None, "critical_failure": "critical" in fixture["tags"] and not fixture["reference_labels"]["policy_correctness"],
                "metric_errors": {},
            },
        } for fixture in fixtures]
        self.report = {
            **calibration.summarize_calibration(fixtures, judged),
            "test_fixture_only": True, "execution_mode": "LIVE", "execution_status": "completed",
            "quality_status": "PASS", "sample_count": 16, "critical_false_accept_count": 0,
            "model_snapshot": self.judge_snapshot, "model_snapshot_after": self.judge_snapshot, "access_blockers": [],
            "metadata": {
                "calibration_id": "mock-calibration", "evaluator_sha256": calibration.digest(contract),
                "judge_deployment": self.config.judge, "project_endpoint": self.config.project_endpoint,
                "fixtures_path": str(fixture_path.resolve()), "fixtures_sha256": sha256_file(fixture_path),
            },
        }
        calibration.save_json(self.report_path, self.report)

    def patch(self, target, *args, **kwargs):
        patcher = patch(target, *args, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def freeze(self, identifier="frozen", **kwargs):
        return governance.freeze_candidate(
            self.config, identifier, "baseline", calibration_id="mock-calibration", **kwargs,
        )

    def review_subject(self):
        path = self.artifacts / "review-target.json"
        calibration.save_json(path, {
            "metadata": {"prompt_sha256": self.agent["prompt_sha256"], "model_deployment": self.agent["model_deployment"]},
            "rows": [{"id": "unit-only-case", "raw_output": '{"answer":"unit-only response"}'}],
        })
        return path

    def test_ai_review_is_hash_bound_and_cannot_claim_human_or_operational_approval(self):
        subject = self.review_subject()
        result = governance.record_ai_review(
            "ai-review", subject, actor="Copilot", notes="Unit-test advisory only",
            findings=[{"case_id": "unit-only-case", "judgment": "uncertain", "reason": "Mock reason"}],
        )
        self.assertEqual(result["actor_type"], "ai")
        self.assertEqual(result["manual_review_state"], "not_reviewed")
        self.assertEqual(result["manual_operational_approval"], "not_granted")
        self.assertEqual(result["subject"]["sha256"], sha256_file(subject))
        self.assertIn("unit-only-case", result["subject"]["response_sha256"])
        with self.assertRaisesRegex(LabError, "immutable"):
            governance.record_ai_review("ai-review", subject, actor="Copilot", notes="Overwrite")
        with self.assertRaisesRegex(LabError, "advisory"):
            governance.record_ai_review(
                "invalid-ai-review", subject, actor="AI", notes="not allowed",
                findings=[{"case_id": "unit-only-case", "judgment": "approved", "reason": "not human"}],
            )

    def test_manual_import_preserves_external_claim_without_authenticating_a_human(self):
        subject = self.review_subject()
        path = self.artifacts / "external-provenance.json"
        source = {
            "review_id": "manual-provenance", "actor_type": "human", "actor": "Example external reviewer",
            "created_at": calibration.now(), "decision": "reviewed", "notes": "Mock provenance document",
            "evidence_uri": "https://example.invalid/external-review",
            "subject": {"path": str(subject.resolve()), "sha256": sha256_file(subject)},
        }
        calibration.save_json(path, source)
        result = governance.import_manual_review(path)
        self.assertEqual(result["actor_type"], "external_unverified")
        self.assertEqual(result["declared_actor_type"], "human")
        self.assertFalse(result["identity_verified"])
        self.assertEqual(result["manual_review_state"], "provided_unverified")
        self.assertEqual(result["manual_operational_approval"], "not_granted")
        for changes in (
            {"review_id": "not-approved", "decision": "approved"},
            {"review_id": "not-ai-human", "generated_by": "ai"},
            {"review_id": "not-ops", "manual_operational_approval": "approved"},
            {"review_id": "not-missing-actor", "actor_type": None},
        ):
            calibration.save_json(path, {**source, **changes})
            with self.subTest(changes=changes), self.assertRaises(LabError):
                governance.import_manual_review(path)

    def test_freeze_pins_all_required_axes_and_review_states_without_cloud_access(self):
        subject = self.review_subject()
        governance.record_ai_review("review", subject, actor="AI", notes="Mock advice")
        frozen = self.freeze(review_ids=["review"])
        self.assertEqual(set(frozen["hashes"]), {
            "prompt", "model", "search", "evaluator", "gates", "data", "calibration", "review_states", "sample_contract",
        })
        self.assertEqual(frozen["manual_review_state"], "not_reviewed")
        self.assertEqual(frozen["reviews"][0]["actor_type"], "ai")
        self.assertEqual(governance.load_freeze("frozen"), frozen)
        self.assertFalse(any((self.artifacts / "governance/holdouts").glob("*")))
        with self.assertRaisesRegex(LabError, "immutable"):
            self.freeze()

    def test_fixtures_alone_do_not_count_as_executed_calibration(self):
        self.report_path.unlink()
        with self.assertRaises(LabError):
            self.freeze()

    def test_observed_drift_calibration_cannot_be_frozen_after_deployment_restoration(self):
        self.report.update(execution_status="invalid_model_drift", model_snapshot_after=self.judge_snapshot)
        calibration.save_json(self.report_path, self.report)
        with self.assertRaisesRegex(LabError, "observed model drift"):
            self.freeze()
        self.assertFalse((self.artifacts / "governance/freezes/frozen.json").exists())

    def test_candidate_review_cannot_launder_completed_capture_with_observed_drift(self):
        subject = self.review_subject()
        value = calibration.read_json(subject)
        value["metadata"].update(
            status="completed", model_snapshot=self.snapshot,
            model_snapshot_after={"model": {"version": "changed"}},
        )
        calibration.save_json(subject, value)
        governance.record_ai_review("drift-review", subject, actor="AI", notes="Review failure, not approval.")
        with self.assertRaisesRegex(LabError, "observed model drift"):
            self.freeze(review_ids=["drift-review"])

    def test_freeze_rejects_same_drifted_agent_version_without_optional_review(self):
        calibration.save_json(self.artifacts / "runs/drifted/metadata.json", {
            "run_id": "drifted", "agent_name": self.agent["name"], "agent_version": self.agent["version"],
            "project_endpoint": self.config.project_endpoint, "status": "completed",
            "model_snapshot": self.snapshot, "model_snapshot_after": {"model": {"version": "changed"}},
        })
        with self.assertRaisesRegex(LabError, "observed model drift"):
            self.freeze()
        self.agent["version"] = "2"
        calibration.save_json(self.artifacts / "agents/baseline.json", self.agent)
        self.assertEqual(self.freeze("new-version")["agent"]["version"], "2")

    def test_changed_prompt_model_search_evaluator_gates_or_data_blocks_existing_freeze(self):
        frozen = self.freeze()
        paths = [
            self.prompt,
            self.artifacts / "agents/baseline.json",
            self.package / "config/evaluators/policy-correctness.v1.json",
            self.package / "config/evaluators/fresh-holdout-gates.v1.json",
            self.package / "config/gates.json",
            self.package / "data/cases.jsonl",
            self.report_path,
        ]
        for path in paths:
            original = path.read_bytes()
            path.write_bytes(original + b" ")
            with self.subTest(path=path), self.assertRaisesRegex(LabError, "changed"):
                governance.load_freeze("frozen")
            path.write_bytes(original)
        self.assertEqual(governance.load_freeze("frozen")["content_sha256"], frozen["content_sha256"])

    def test_unsealed_freeze_edits_are_rejected_even_if_gate_values_look_valid(self):
        self.freeze()
        path = self.artifacts / "governance/freezes/frozen.json"
        value = calibration.read_json(path)
        value["gates"]["minimums"]["route_accuracy"] = 0
        calibration.save_json(path, value)
        with self.assertRaisesRegex(LabError, "Immutable"):
            governance.load_freeze("frozen")

    def test_fresh_generator_runs_only_after_freeze_and_preserves_original_100(self):
        original = sha256_file(self.package / "data/cases.jsonl")
        with self.assertRaises(LabError):
            governance.create_holdout("missing-freeze", "fresh")
        frozen = self.freeze()
        generated = governance.create_holdout("frozen", "fresh")
        rows = calibration.read_jsonl(Path(generated["dataset_path"]))
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum("follow_up" in row for row in rows), 1)
        self.assertEqual(generated["provenance"]["kind"], "authored_template_variants")
        self.assertTrue(all("synthetic_variant" in row["tags"] for row in rows))
        self.assertTrue(all(row["split"] == "test" for row in rows))
        self.assertGreater(generated["generated_at"], frozen["created_at"])
        self.assertEqual(generated["disjointness"]["existing_case_count"], 117)
        self.assertEqual(sha256_file(self.package / "data/cases.jsonl"), original)
        self.assertTrue(Path(generated["dataset_path"]).is_relative_to(self.artifacts.resolve()))
        with self.assertRaisesRegex(LabError, "immutable|overlaps"):
            governance.create_holdout("frozen", "replacement")

    def test_disjointness_rejects_ids_groups_exact_and_numeric_variants(self):
        existing = calibration.read_jsonl(self.package / "data/cases.jsonl")
        source = existing[0]
        changes = [
            {"group_id": "new-composite-group"},
            {"id": "new-id"},
            {"id": "new-id", "group_id": "new-composite-group"},
            {"id": "new-id", "group_id": "new-composite-group", "query": source["query"].replace("5만", "7만")},
        ]
        for change in changes:
            candidate = {**source, **change, "split": "test"}
            with self.subTest(change=change), self.assertRaisesRegex(LabError, "overlaps|duplicate"):
                governance.check_disjoint([candidate], existing)

    def test_registration_rejects_pre_freeze_timestamp_and_original_data_paths(self):
        frozen = self.freeze()
        source = self.artifacts / "external-fresh.jsonl"
        cases = calibration.read_jsonl(self.package / "data/splits/test.jsonl")
        write_jsonl(source, cases)
        with self.assertRaisesRegex(LabError, "after this exact freeze"):
            governance.register_holdout("frozen", "before", source, generated_at=frozen["created_at"], provenance="mock")
        with self.assertRaisesRegex(LabError, "ARTIFACTS"):
            governance.register_holdout(
                "frozen", "original", self.package / "data/splits/test.jsonl",
                generated_at=calibration.now(), provenance="mock",
            )
        with self.assertRaisesRegex(LabError, "overlaps"):
            governance.register_holdout("frozen", "relabel", source, generated_at=calibration.now(), provenance="mock")

    def test_one_exact_freeze_binds_only_one_full_holdout_attempt(self):
        frozen = self.freeze()
        metadata = governance.create_holdout("frozen", "fresh")
        attempt = governance.bind_holdout_attempt("frozen", "fresh", "unit-only-run")
        self.assertEqual(attempt["freeze_sha256"], frozen["content_sha256"])
        self.assertEqual(attempt["dataset_sha256"], metadata["dataset_sha256"])
        self.assertEqual(
            governance.bind_holdout_attempt("frozen", "fresh", "unit-only-run", resume=True), attempt,
        )
        with self.assertRaisesRegex(LabError, "one evaluation attempt"):
            governance.bind_holdout_attempt("frozen", "fresh", "other-run")
        with self.assertRaisesRegex(LabError, "one evaluation attempt"):
            governance.bind_holdout_attempt("frozen", "fresh", "unit-only-run")
        with self.assertRaisesRegex(LabError, "Judge model"):
            governance.validate_frozen_run("frozen", "unit-only-run", judge_snapshot={"model": "changed"})

    def test_incomplete_calibration_does_not_gain_approval_by_freezing(self):
        self.report.update(quality_status="HOLD", execution_status="blocked_access", access_blockers=["unit-only access denial"])
        calibration.save_json(self.report_path, self.report)
        self.freeze()
        governance.create_holdout("frozen", "fresh")
        with self.assertRaisesRegex(LabError, "calibration"):
            governance.bind_holdout_attempt("frozen", "fresh", "blocked-run")
        status = governance.governance_status("frozen")
        self.assertEqual(status["execution_status"], "not_started")
        self.assertEqual(status["quality_status"], "NOT_EVALUATED")
        self.assertEqual(status["manual_operational_approval"], "not_granted")
        self.assertEqual(status["access_blockers"], ["unit-only access denial"])

    def test_holdout_mutation_training_and_optimization_are_blocked(self):
        self.freeze()
        metadata = governance.create_holdout("frozen", "fresh")
        dataset = Path(metadata["dataset_path"])
        for purpose in ("training", "optimization", "prompt_selection", "judge_tuning"):
            with self.subTest(purpose=purpose), self.assertRaisesRegex(LabError, "never"):
                governance.assert_dataset_use(dataset, purpose)
        copied = self.artifacts / "misnamed-training.jsonl"
        shutil.copyfile(dataset, copied)
        with self.assertRaisesRegex(LabError, "Copied"):
            governance.assert_dataset_use(copied, "training")
        converted = self.artifacts / "misnamed-sft.jsonl"
        write_jsonl(converted, [{
            "messages": [
                {"role": "user", "content": row["query"]},
                {"role": "assistant", "content": row["ground_truth"]},
            ],
        } for row in calibration.read_jsonl(dataset)])
        with self.assertRaisesRegex(LabError, "Copied"):
            governance.assert_dataset_use(converted, "training")
        dataset.write_text(dataset.read_text() + "\n", encoding="utf-8")
        with self.assertRaisesRegex(LabError, "path/hash"):
            governance.load_holdout("frozen", "fresh")

    def test_template_count_never_creates_fake_sample_size_with_duplicate_variants(self):
        self.freeze()
        for count in (True, 0, 1.5, 21):
            with self.subTest(count=count), self.assertRaisesRegex(LabError, "integer"):
                governance.create_holdout("frozen", "fresh", count=count)

    def test_fresh_twelve_contract_binds_without_altering_original_test_twenty(self):
        original_hash = sha256_file(self.package / "config/gates.json")
        frozen = self.freeze()
        holdout = governance.create_holdout("frozen", "fresh-twelve", count=12)
        attempt = governance.bind_holdout_attempt("frozen", "fresh-twelve", "fresh-run")
        self.assertEqual(sha256_file(self.package / "config/gates.json"), original_hash)
        self.assertEqual(frozen["legacy_gates"]["minimum_test_rows"], 20)
        self.assertEqual(frozen["gates"]["minimum_test_rows"], 12)
        self.assertEqual(frozen["sample_contract"]["version"], "1.0.0")
        for field in frozen["sample_contract"]["unchanged_gate_fields"]:
            self.assertEqual(frozen["gates"][field], frozen["legacy_gates"][field])
        self.assertEqual(holdout["sample_contract_sha256"], frozen["hashes"]["sample_contract"])
        self.assertEqual(attempt["sample_contract_sha256"], frozen["hashes"]["sample_contract"])

    def test_fresh_contract_still_rejects_undersized_or_rewritten_sample_scope(self):
        self.freeze()
        governance.create_holdout("frozen", "too-small", count=11)
        with self.assertRaisesRegex(LabError, "frozen size/critical coverage"):
            governance.bind_holdout_attempt("frozen", "too-small", "not-approved-run")
        self.assertFalse((self.artifacts / "governance/attempts/frozen.json").exists())
        path = self.package / "config/evaluators/fresh-holdout-gates.v1.json"
        value = calibration.read_json(path)
        value["minimum_rows"] = 11
        calibration.save_json(path, value)
        with self.assertRaisesRegex(LabError, "changed"):
            governance.load_freeze("frozen")
        with self.assertRaisesRegex(LabError, "explicit v1 sample contract"):
            self.freeze("another-freeze")

    def test_twelve_row_capture_judge_score_finalize_contract_end_to_end_with_mocks(self):
        from lab.batch import run_batch, score_run

        frozen = self.freeze()
        registered = governance.create_holdout("frozen", "fresh")
        cases = {case["id"]: case for case in calibration.read_jsonl(Path(registered["dataset_path"]))}

        def response(identifier, text, output):
            return SimpleNamespace(
                id=identifier, output_text=text, model_dump=lambda **kwargs: {
                    "id": identifier, "status": "completed", "output": output,
                    "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
                },
            )

        def capture(**kwargs):
            case = cases[kwargs["metadata"]["lab_case"]]
            turn = kwargs["metadata"]["lab_turn"]
            text = case["ground_truth"]
            if "follow_up" in case and turn == "0":
                text = calibration.canonical({
                    "answer": "구매 시각과 미사용 여부를 알려 주세요.", "citations": [],
                    "route": "clarify", "needs_human": False,
                })
            return response(f"unit-agent-{case['id']}-{turn}", text, [{
                "type": "mcp_call", "name": "knowledge_base_retrieve", "output": case["context"],
            }])

        agent_client = SimpleNamespace(responses=SimpleNamespace(create=Mock(side_effect=capture)))
        agent_project = SimpleNamespace(
            agents=SimpleNamespace(get_version=lambda **kwargs: SimpleNamespace(
                definition=SimpleNamespace(model=self.agent["model_deployment"]),
            )),
            get_openai_client=lambda **kwargs: nullcontext(agent_client),
        )
        self.patch("lab.batch.load_agent", return_value=self.agent)
        self.patch("lab.batch.credential_for", return_value=nullcontext("unit-only-credential"))
        self.patch("lab.batch.model_snapshot", return_value=self.snapshot)
        self.patch("lab.batch.AIProjectClient", return_value=nullcontext(agent_project))
        with redirect_stdout(io.StringIO()):
            captured = run_batch(
                self.config, "baseline", "test", "unit-run", freeze_id="frozen", holdout_id="fresh",
            )
        self.assertEqual(captured["status"], "completed")
        self.assertEqual(captured["sample_contract_sha256"], frozen["hashes"]["sample_contract"])
        self.assertEqual(agent_client.responses.create.call_count, 13)

        def judge(**kwargs):
            schema_name = kwargs["text"]["format"]["name"]
            value = (
                {"policy_correctness": 5, "relevance": 5, "critical_failure": False, "reason": "Unit-only mock"}
                if schema_name == "atlas_policy_v1" else {"groundedness": 5, "reason": "Unit-only mock"}
            )
            return response(f"unit-judge-response-{judge_client.responses.create.call_count}", calibration.canonical(value), [])

        judge_client = SimpleNamespace(responses=SimpleNamespace(create=Mock(side_effect=judge)))
        judge_project = SimpleNamespace(get_openai_client=lambda **kwargs: nullcontext(judge_client))
        self.patch("lab.calibration.credential_for", return_value=nullcontext("unit-only-credential"))
        self.patch("lab.calibration.AIProjectClient", return_value=nullcontext(judge_project))
        self.patch("lab.calibration.model_snapshot", return_value=self.judge_snapshot)
        report = calibration.score_captured_run(self.config, "unit-run", confirm=True)
        self.assertEqual(report["execution_status"], "completed")
        self.assertEqual(judge_client.responses.create.call_count, 24)
        summary = score_run("unit-run")
        self.assertEqual(summary["metadata"]["sample_count"], 12)
        result = governance.finalize_holdout("frozen", "unit-run")
        self.assertEqual(result["quality_status"], "PASS_FOR_WORKSHOP")
        self.assertEqual(result["manual_operational_approval"], "not_granted")
        self.assertEqual(result["legacy_minimum_test_rows"], 20)

    def test_final_attempt_reports_execution_quality_and_manual_approval_separately(self):
        frozen = self.freeze()
        holdout = governance.create_holdout("frozen", "fresh")
        governance.bind_holdout_attempt("frozen", "fresh", "unit-only-run")
        cases = calibration.read_jsonl(Path(holdout["dataset_path"]))
        directory = self.artifacts / "runs/unit-only-run"
        metadata = {
            "run_id": "unit-only-run", "stage": "baseline", "split": "test", "source_split": "test",
            "status": "completed", "model_deployment": self.agent["model_deployment"],
            "project_endpoint": self.config.project_endpoint,
            "model_snapshot": self.snapshot, "agent_name": self.agent["name"], "agent_version": "1",
            "prompt_sha256": frozen["hashes"]["prompt"], "knowledge_sha256": self.agent["knowledge_sha256"],
            "freeze_id": "frozen", "freeze_sha256": frozen["content_sha256"], "holdout_id": "fresh",
            "dataset_sha256": holdout["dataset_sha256"], "row_ids": holdout["row_ids"],
            "evaluation_contract_version": calibration.CONTRACT_VERSION, "judge_execution_status": "completed",
            "sample_contract_sha256": frozen["hashes"]["sample_contract"],
            "judge": {
                "model_deployment": self.config.judge, "prompt_sha256": frozen["hashes"]["evaluator"],
                "version": calibration.CONTRACT_VERSION, "settings": {}, "scale": [1, 5],
                "provenance": {"source": "unit-test-only"},
            },
        }
        documents = calibration.read_json(self.package / "data/knowledge/documents.json")
        scores = {"groundedness": 5, "relevance": 5, "policy_correctness": 5, "error": None, "critical_failure": False}
        context = "Unit-test-only observed-context mock, not a cloud capture"
        rows = [score_row(
            case, case["ground_truth"], known_citations={doc["id"] for doc in documents},
            judge=scores, retrieved_context=context,
        ) for case in cases]
        summary = summarize(rows, metadata=metadata)
        self.assertEqual(evaluate_gates(summary, frozen["legacy_gates"])["outcome"], "HOLD")
        critical_index = next(index for index, row in enumerate(rows) if "critical" in row["tags"])
        for changes in (
            {"groundedness": 1}, {"groundedness": None}, {"relevance": 1},
            {"policy_correctness": 1}, {"error": "unit-only Judge error"}, {"critical_failure": True},
        ):
            bad_rows = deepcopy(rows)
            bad_rows[critical_index]["judge"].update(changes)
            with self.subTest(changes=changes):
                self.assertEqual(
                    evaluate_gates(summarize(bad_rows, metadata=metadata), frozen["gates"])["outcome"], "HOLD",
                )
        wrong_sample = deepcopy(summary)
        wrong_sample["metadata"]["sample_contract_sha256"] = "0" * 64
        self.assertEqual(evaluate_gates(wrong_sample, frozen["gates"])["outcome"], "HOLD")
        calibration.save_json(directory / "metadata.json", metadata)
        calibration.save_json(directory / "summary.json", summary)
        write_jsonl(directory / "outputs.jsonl", [{
            "id": case["id"], "raw_output": case["ground_truth"], "retrieved_context": context, "error": None,
        } for case in cases])
        calibration.save_json(directory / "judge-scores.json", {case["id"]: scores for case in cases})
        submission = {
            "row_ids": metadata["row_ids"], "dataset_sha256": metadata["dataset_sha256"],
            "outputs_sha256": sha256_file(directory / "outputs.jsonl"), "freeze_sha256": frozen["content_sha256"],
            "sample_contract_sha256": frozen["hashes"]["sample_contract"],
        }
        calibration.save_json(directory / "business-judge/submission.json", submission)
        calibration.save_json(directory / "business-judge/contract.json", frozen["evaluator_contract"])
        calibration.save_json(directory / "business-judge/report.json", {
            "unit_test_only": True, "submission_sha256": calibration.digest(submission),
            "execution_status": "completed",
            "evaluator_sha256": frozen["hashes"]["evaluator"],
            "judge_scores_sha256": sha256_file(directory / "judge-scores.json"),
        })
        result = governance.finalize_holdout("frozen", "unit-only-run")
        self.assertEqual(result["execution_status"], "completed")
        self.assertEqual(result["quality_status"], "PASS_FOR_WORKSHOP")
        self.assertEqual(result["sample_count"], 12)
        self.assertEqual(result["sample_contract"]["minimum_rows"], 12)
        self.assertEqual(result["legacy_minimum_test_rows"], 20)
        self.assertEqual(result["manual_operational_approval"], "not_granted")
        self.assertFalse(result["production_ready"])
        with self.assertRaisesRegex(LabError, "already recorded"):
            governance.validate_frozen_run("frozen", "unit-only-run")
        self.assertEqual(governance.governance_status("frozen"), result)


if __name__ == "__main__":
    unittest.main()
