"""합성 데이터 계약과 분할 격리를 검사한다. 네트워크와 외부 패키지는 사용하지 않는다."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import re
import subprocess
import sys
import unittest
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts/build_datasets.py"
SPEC = importlib.util.spec_from_file_location("atlas_dataset_builder", BUILDER_PATH)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)

EXPECTED_COUNTS = {"train": 56, "validation": 12, "dev": 12, "test": 20}
EXPECTED_OUTPUT_KEYS = {"answer", "citations", "route", "needs_human"}
EXPECTED_ROW_KEYS = {
    "id",
    "group_id",
    "split",
    "query",
    "context",
    "ground_truth",
    "expected_route",
    "required_citations",
    "tags",
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def change_target(row: dict, **updates: object) -> None:
    target = json.loads(row["ground_truth"])
    target.update(updates)
    row["ground_truth"] = json.dumps(target, ensure_ascii=False)


class DatasetContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_jsonl(ROOT / "data/cases.jsonl")
        cls.documents = builder.load_documents(ROOT / "data/knowledge/documents.json")
        cls.by_split = {
            split: sorted(
                (row for row in cls.rows if row["split"] == split),
                key=lambda row: row["id"],
            )
            for split in EXPECTED_COUNTS
        }
        cls.artifacts = builder.build_artifacts(ROOT)

    def test_exact_counts_and_minimum_sizes(self) -> None:
        self.assertEqual(Counter(row["split"] for row in self.rows), EXPECTED_COUNTS)
        self.assertEqual(len(self.rows), 100)
        self.assertGreaterEqual(EXPECTED_COUNTS["train"], 48)
        self.assertLessEqual(EXPECTED_COUNTS["train"], 64)
        self.assertEqual(
            {split: len({row["group_id"] for row in rows}) for split, rows in self.by_split.items()},
            {"train": 54, "validation": 12, "dev": 12, "test": 20},
        )

    def test_knowledge_schema_and_meaningful_korean_content(self) -> None:
        self.assertEqual(len(self.documents), 8)
        for doc_id, document in self.documents.items():
            with self.subTest(document=doc_id):
                self.assertEqual(set(document), {"id", "title", "content", "effective_date"})
                self.assertRegex(doc_id, r"^ATLAS-[A-Z]+-\d{3}$")
                self.assertRegex(document["effective_date"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertRegex(document["title"], r"[가-힣]")
                self.assertGreater(len(document["content"]), 400)
                self.assertGreaterEqual(len(document["content"].split("\n\n")), 4)

    def test_case_schema(self) -> None:
        for row in self.rows:
            with self.subTest(case=row["id"]):
                self.assertTrue(EXPECTED_ROW_KEYS <= set(row))
                self.assertTrue(set(row) <= EXPECTED_ROW_KEYS | {"forbidden_claims"})
                for key in EXPECTED_ROW_KEYS - {"tags", "required_citations"}:
                    self.assertIsInstance(row[key], str)
                    self.assertTrue(row[key].strip())
                for key in ("tags", "required_citations"):
                    self.assertIsInstance(row[key], list)
                    self.assertTrue(row[key])
                    self.assertTrue(all(isinstance(value, str) and value for value in row[key]))
                    self.assertEqual(len(row[key]), len(set(row[key])))
                if "forbidden_claims" in row:
                    self.assertIsInstance(row["forbidden_claims"], list)
                    self.assertTrue(all(isinstance(value, str) for value in row["forbidden_claims"]))

    def test_all_ids_unique_and_split_identifiers_match(self) -> None:
        self.assertEqual(len(self.rows), len({row["id"] for row in self.rows}))
        for row in self.rows:
            self.assertRegex(row["id"], rf"^atlas-{row['split']}-\d{{3}}$")
        for left, right in combinations(self.by_split, 2):
            self.assertFalse(
                {row["id"] for row in self.by_split[left]}
                & {row["id"] for row in self.by_split[right]}
            )

    def test_group_and_normalized_query_isolation(self) -> None:
        normalized = [builder.normalize_query(row["query"]) for row in self.rows]
        self.assertEqual(len(normalized), len(set(normalized)))
        for left, right in combinations(self.by_split, 2):
            with self.subTest(left=left, right=right):
                for field in ("group_id", "query"):
                    self.assertFalse(
                        {row[field] for row in self.by_split[left]}
                        & {row[field] for row in self.by_split[right]}
                    )

    def test_cross_split_near_copy_guard(self) -> None:
        for left, right in combinations(self.rows, 2):
            if left["split"] == right["split"]:
                continue
            similarity = SequenceMatcher(
                None,
                builder.normalize_query(left["query"]),
                builder.normalize_query(right["query"]),
                autojunk=False,
            ).ratio()
            self.assertLess(similarity, 0.85, f"문장 복제 의심: {left['id']} / {right['id']}")

    def test_contexts_are_only_verbatim_document_paragraphs(self) -> None:
        for row in self.rows:
            with self.subTest(case=row["id"]):
                chunks = re.split(r"^\[([A-Z0-9-]+)\]\n", row["context"], flags=re.MULTILINE)
                self.assertEqual(chunks[0], "")
                self.assertGreaterEqual(len(chunks), 3)
                context_ids = chunks[1::2]
                self.assertEqual(len(context_ids), len(set(context_ids)))
                for doc_id, excerpt in zip(context_ids, chunks[2::2]):
                    self.assertIn(doc_id, self.documents)
                    for paragraph in excerpt.rstrip("\n").split("\n\n"):
                        self.assertIn(paragraph, self.documents[doc_id]["content"].split("\n\n"))
                self.assertTrue(set(row["required_citations"]) <= set(context_ids))
                for private_label in ("ground_truth", "expected_route", "required_citations"):
                    self.assertNotIn(private_label, row["context"])
                    self.assertNotIn(private_label, row["query"])

    def test_ground_truth_json_output_contract_and_citations(self) -> None:
        for row in self.rows:
            with self.subTest(case=row["id"]):
                output = json.loads(row["ground_truth"])
                self.assertIsInstance(output, dict)
                self.assertEqual(set(output), EXPECTED_OUTPUT_KEYS)
                self.assertIsInstance(output["answer"], str)
                self.assertRegex(output["answer"], r"[가-힣]")
                self.assertNotRegex(output["answer"], r"[ぁ-ゖァ-ヺ]")
                self.assertIsInstance(output["citations"], list)
                self.assertTrue(all(isinstance(value, str) for value in output["citations"]))
                self.assertEqual(len(output["citations"]), len(set(output["citations"])))
                self.assertEqual(set(output["citations"]), set(row["required_citations"]))
                self.assertTrue(set(output["citations"]) <= set(self.documents))
                self.assertIn(output["route"], {"answer", "clarify", "escalate", "refuse"})
                self.assertEqual(output["route"], row["expected_route"])
                self.assertIs(type(output["needs_human"]), bool)
                self.assertIs(output["needs_human"], output["route"] == "escalate")
                for phrase in row.get("forbidden_claims", []):
                    self.assertNotIn(phrase, output["answer"])

    def test_coverage_includes_distinct_behaviors(self) -> None:
        all_tags = {tag for row in self.rows for tag in row["tags"]}
        self.assertTrue(
            {
                "다중문서",
                "기간경계",
                "포함경계",
                "미포함경계",
                "정보부족",
                "프롬프트주입",
                "한국어모호성",
                "영어질문",
                "한국어답변",
                "근거없는기능",
                "미실행증거",
                "제한요청",
                "정책최신성",
            }
            <= all_tags
        )
        self.assertGreaterEqual(sum(len(row["required_citations"]) >= 2 for row in self.rows), 2)
        for split, rows in self.by_split.items():
            with self.subTest(split=split):
                self.assertEqual(
                    {row["expected_route"] for row in rows},
                    {"answer", "clarify", "escalate", "refuse"},
                )

    def test_synthetic_contact_information_smoke_check(self) -> None:
        text = "\n".join(
            [document["content"] for document in self.documents.values()]
            + [row["query"] + row["ground_truth"] for row in self.rows]
        )
        self.assertNotRegex(text, r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        self.assertNotRegex(text, r"(?<!\d)01[016789][ -]?\d{3,4}[ -]?\d{4}(?!\d)")
        self.assertIn("실습용 합성 정책", self.documents["ATLAS-DOC-001"]["content"])

    def test_critical_subsets_are_explicit_and_have_literal_guards(self) -> None:
        critical_counts = Counter()
        for row in self.rows:
            expected_critical = row["expected_route"] in {"escalate", "refuse"} or bool(
                {"프롬프트주입", "미실행증거"} & set(row["tags"])
            )
            with self.subTest(case=row["id"]):
                self.assertEqual("critical" in row["tags"], expected_critical)
                if expected_critical:
                    critical_counts[row["split"]] += 1
                    self.assertTrue(row.get("forbidden_claims"))
                    self.assertTrue(all(isinstance(value, str) for value in row["forbidden_claims"]))
        self.assertEqual(critical_counts, {"train": 13, "validation": 3, "dev": 4, "test": 9})

    def test_split_exports_match_master_exactly(self) -> None:
        for split, expected in self.by_split.items():
            with self.subTest(split=split):
                actual = load_jsonl(ROOT / f"data/splits/{split}.jsonl")
                self.assertEqual(actual, expected)

    def test_tuning_exports_use_only_messages_with_correct_roles(self) -> None:
        expected_system = (ROOT / "prompts/tuning-system.txt").read_text(encoding="utf-8").strip()
        for split in ("train", "validation"):
            records = load_jsonl(ROOT / f"data/tuning/sft-{split}.jsonl")
            self.assertEqual(len(records), EXPECTED_COUNTS[split])
            for record, original in zip(records, self.by_split[split]):
                with self.subTest(split=split, case=original["id"]):
                    self.assertEqual(set(record), {"messages"})
                    messages = record["messages"]
                    self.assertEqual([message["role"] for message in messages], ["system", "user", "assistant"])
                    for message in messages:
                        self.assertEqual(set(message), {"role", "content"})
                        self.assertIsInstance(message["content"], str)
                        self.assertTrue(message["content"])
                    self.assertEqual(messages[0]["content"], expected_system)
                    user_input = json.loads(messages[1]["content"])
                    self.assertEqual(set(user_input), {"query", "context"})
                    self.assertEqual(
                        user_input,
                        {"query": original["query"], "context": original["context"]},
                    )
                    self.assertEqual(json.loads(messages[2]["content"]), json.loads(original["ground_truth"]))

    def test_optimizer_export_matches_prompt_agent_portal_columns(self) -> None:
        records = load_jsonl(ROOT / "data/optimizer/dev.jsonl")
        self.assertEqual(len(records), 12)
        self.assertEqual(len({record["query"] for record in records}), 12)
        for actual, original in zip(records, self.by_split["dev"]):
            with self.subTest(case=original["id"]):
                self.assertEqual(set(actual), {"query", "ground_truth", "context"})
                self.assertEqual(actual["query"], original["query"])
                self.assertEqual(actual["ground_truth"], original["ground_truth"])
                self.assertEqual(actual["context"], original["context"])
                self.assertIsInstance(actual["query"], str)
                self.assertIsInstance(actual["ground_truth"], str)
                self.assertIsInstance(actual["context"], str)
                for forbidden in ("name", "criteria", "expected_behavior", "response", "expected_route"):
                    self.assertNotIn(forbidden, actual)
        self.assertFalse(
            {row["query"] for row in records}
            & {row["query"] for row in self.by_split["validation"]}
        )

    def test_optimizer_query_excludes_reference_context_and_evaluator_labels(self) -> None:
        row = copy.deepcopy(self.by_split["dev"][0])
        row["context"] = "에이전트에_보내면_안되는_참고문맥_센티널"
        row["ground_truth"] = "평가자만_읽는_정답_센티널"
        record = builder.optimizer_record(row)
        self.assertEqual(record["query"], row["query"])
        self.assertEqual(set(record), {"query", "ground_truth", "context"})
        self.assertEqual(record["context"], row["context"])
        self.assertNotIn("expected_route", record)
        self.assertNotIn("required_citations", record)
        self.assertNotIn(row["context"], record["query"])
        self.assertNotIn("센티널", record["query"])
        self.assertEqual(record["ground_truth"], row["ground_truth"])

    def test_labels_never_reach_the_user_message(self) -> None:
        row = copy.deepcopy(self.rows[0])
        row["ground_truth"] = "평가자_전용_정답_센티널"
        row["expected_route"] = "평가자_전용_분류_센티널"
        row["forbidden_claims"] = ["평가자_전용_금지_센티널"]
        user_message = builder.render_user_message(row)
        self.assertEqual(
            json.loads(user_message),
            {"query": row["query"], "context": row["context"]},
        )
        self.assertNotIn("센티널", user_message)
        self.assertNotIn("ground_truth", user_message)
        self.assertNotIn("expected_route", user_message)

    def test_test_queries_and_ids_absent_from_train_dev_and_tuning(self) -> None:
        exported_paths = [
            "data/splits/train.jsonl",
            "data/splits/validation.jsonl",
            "data/splits/dev.jsonl",
            "data/tuning/sft-train.jsonl",
            "data/tuning/sft-validation.jsonl",
            "data/optimizer/dev.jsonl",
        ]
        prompt_paths = [
            "prompts/baseline.txt",
            "prompts/candidate.txt",
            "prompts/tuning-system.txt",
            "prompts/rubric.txt",
        ]
        for relative in exported_paths + prompt_paths:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for row in self.by_split["test"]:
                with self.subTest(path=relative, case=row["id"]):
                    self.assertNotIn(row["id"], text)
                    query_forms = [row["query"]]
                    for _ in range(2):
                        query_forms.append(json.dumps(query_forms[-1], ensure_ascii=False)[1:-1])
                    for query in query_forms:
                        self.assertNotIn(query, text)

    def test_prompt_provenance_and_behavior_only_tuning_system(self) -> None:
        candidate = (ROOT / "prompts/candidate.txt").read_text(encoding="utf-8")
        self.assertIn("강사가 수동으로 작성", candidate)
        self.assertIn("실행 결과나 성능 개선이 입증된 산출물이 아닙니다", candidate)
        system = (ROOT / "prompts/tuning-system.txt").read_text(encoding="utf-8")
        self.assertLess(len(system), 1500)
        self.assertNotRegex(system, r"\d{4}-\d{2}-\d{2}|\d{1,3},\d{3}원")
        for doc_id in self.documents:
            self.assertNotIn(doc_id, system)
        for name in ("baseline", "candidate", "tuning-system"):
            prompt = (ROOT / f"prompts/{name}.txt").read_text(encoding="utf-8")
            for key in EXPECTED_OUTPUT_KEYS:
                self.assertIn(key, prompt)
            for route in ("answer", "clarify", "escalate", "refuse"):
                self.assertIn(route, prompt)

    def test_manifest_counts_hashes_and_group_leakage(self) -> None:
        manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["counts"], EXPECTED_COUNTS)
        self.assertEqual(manifest["master_rows"], 100)
        self.assertEqual(manifest["documents"], 8)
        self.assertEqual(
            manifest["critical_counts"],
            {"train": 13, "validation": 3, "dev": 4, "test": 9},
        )
        self.assertIs(manifest["synthetic"], True)
        self.assertIs(manifest["split_disjointness"]["passed"], True)
        self.assertEqual(len(manifest["split_disjointness"]["pairs"]), 6)
        for pair in manifest["split_disjointness"]["pairs"]:
            self.assertEqual(pair["id_overlap"], [])
            self.assertEqual(pair["group_overlap"], [])
            self.assertEqual(pair["normalized_query_overlap_count"], 0)
        for path, digest in manifest["sources_sha256"].items():
            self.assertEqual(digest, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
        self.assertEqual(len(manifest["exports"]), 7)
        for path, metadata in manifest["exports"].items():
            self.assertEqual(metadata["sha256"], hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
            self.assertEqual(metadata["rows"], len(load_jsonl(ROOT / path)))
            if "/tuning/" in path or "/optimizer/" in path:
                self.assertNotIn("test", metadata["source_splits"])
        self.assertEqual(manifest["holdout_checks"]["test_ids_in_tuning_or_optimizer"], 0)
        self.assertEqual(manifest["holdout_checks"]["test_queries_in_tuning_or_optimizer"], 0)
        optimizer = manifest["provenance"]["optimizer_export"]
        self.assertEqual(optimizer["service"], "agent optimizer")
        self.assertEqual(optimizer["lane"], "prompt-agent-portal")
        self.assertEqual(
            optimizer["schema_reference"],
            "https://learn.microsoft.com/azure/foundry/agents/quickstarts/"
            "quickstart-optimize-prompt-agent#prerequisites",
        )
        self.assertEqual(optimizer["columns"], ["query", "ground_truth", "context"])
        self.assertEqual(optimizer["agent_input_columns"], ["query"])
        self.assertEqual(optimizer["evaluator_only_columns"], ["ground_truth", "context"])
        self.assertIs(optimizer["column_mapping_supported"], False)
        self.assertIs(optimizer["authored_locally"], True)
        self.assertIs(optimizer["query_includes_reference_context"], False)

    def test_generation_is_byte_deterministic_and_current(self) -> None:
        second = builder.build_artifacts(ROOT)
        self.assertEqual(self.artifacts, second)
        self.assertEqual(
            set(second),
            {
                "data/splits/train.jsonl",
                "data/splits/validation.jsonl",
                "data/splits/dev.jsonl",
                "data/splits/test.jsonl",
                "data/tuning/sft-train.jsonl",
                "data/tuning/sft-validation.jsonl",
                "data/optimizer/dev.jsonl",
                "data/manifest.json",
            },
        )
        for relative, expected_bytes in second.items():
            self.assertEqual((ROOT / relative).read_bytes(), expected_bytes)
            self.assertTrue(expected_bytes.endswith(b"\n"))

    def test_check_command_needs_no_network_or_dependencies(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(BUILDER_PATH), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("train=56", result.stdout)
        self.assertIn("test=20", result.stdout)

    def _run_check_without_writes(self) -> tuple[int, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(
            Path, "write_bytes", side_effect=AssertionError("--check에서 파일 쓰기 금지")
        ), mock.patch.object(
            Path, "mkdir", side_effect=AssertionError("--check에서 디렉터리 생성 금지")
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            return_code = builder.main(["--check"])
        return return_code, stdout.getvalue() + stderr.getvalue()

    def test_check_rejects_stale_exports_and_manifest_without_writing(self) -> None:
        original_read_bytes = Path.read_bytes
        for relative in self.artifacts:
            target = ROOT / relative

            def stale_bytes(path: Path) -> bytes:
                return b"outdated generated file\n" if path == target else original_read_bytes(path)

            with self.subTest(path=relative), mock.patch.object(Path, "read_bytes", new=stale_bytes):
                status, output = self._run_check_without_writes()
                self.assertEqual(status, 1)
                self.assertIn(relative, output)
                self.assertIn("오래되었습니다", output)

    def test_english_check_rejects_crlf_checkouts_with_an_english_message(self) -> None:
        target = ROOT / "data/en/optimizer/dev.jsonl"
        original_read_bytes = Path.read_bytes

        def crlf_bytes(path: Path) -> bytes:
            data = original_read_bytes(path)
            return data.replace(b"\n", b"\r\n") if path == target else data

        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(Path, "read_bytes", new=crlf_bytes), redirect_stdout(stdout), redirect_stderr(stderr):
            status = builder.main(["--check", "--language", "en"])
        output = stdout.getvalue() + stderr.getvalue()
        self.assertEqual(status, 1)
        self.assertIn("data/en/optimizer/dev.jsonl", output)
        self.assertIn("missing or stale", output)
        self.assertIn("--language en", output)
        self.assertIsNone(re.search("[가-힣]", output))

    def test_check_rejects_missing_exports_and_manifest_without_writing(self) -> None:
        original_is_file = Path.is_file
        for relative in self.artifacts:
            target = ROOT / relative

            def missing_file(path: Path) -> bool:
                return False if path == target else original_is_file(path)

            with self.subTest(path=relative), mock.patch.object(Path, "is_file", new=missing_file):
                status, output = self._run_check_without_writes()
                self.assertEqual(status, 1)
                self.assertIn(relative, output)

    def test_check_validates_source_before_accepting_existing_exports(self) -> None:
        original_read_text = Path.read_text

        def corrupt_source(path: Path, *args: object, **kwargs: object) -> str:
            if path == ROOT / "data/cases.jsonl":
                return '{"id":'
            return original_read_text(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", new=corrupt_source):
            status, output = self._run_check_without_writes()
        self.assertEqual(status, 1)
        self.assertIn("데이터 오류", output)
        self.assertIn("cases.jsonl", output)

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_numbers(self) -> None:
        for text in ('{"answer":"첫째","answer":"둘째"}', '{"score":NaN}', '{"score":Infinity}', "{} 뒤풀이"):
            with self.subTest(text=text), self.assertRaises(builder.DatasetError):
                builder.parse_json(text)

    def test_validator_rejects_corrupted_cases(self) -> None:
        first_dev_group = self.by_split["dev"][0]["group_id"]
        mutations = {
            "필드누락": lambda rows: rows[0].pop("tags"),
            "추가필드": lambda rows: rows[0].update(unapproved_metadata="추가값"),
            "중복식별자": lambda rows: rows[1].update(id=rows[0]["id"]),
            "중복문의": lambda rows: rows[1].update(query="  " + rows[0]["query"] + "  "),
            "그룹누수": lambda rows: rows[0].update(group_id=first_dev_group),
            "잘못된분할": lambda rows: rows[0].update(split="holdout"),
            "필수인용부재": lambda rows: rows[0].update(required_citations=["ATLAS-NONE-999"]),
            "평가라벨누수": lambda rows: rows[0].update(query="expected_route: answer"),
            "정답을문맥에추가": lambda rows: rows[0].update(
                context=rows[0]["context"] + "\n\n정답은 환불 완료입니다."
            ),
            "거짓문서": lambda rows: rows[0].update(context="[ATLAS-NONE-999]\n알 수 없는 문서"),
            "중복인용": lambda rows: change_target(rows[0], citations=["ATLAS-SUB-001"] * 2),
            "문맥외인용": lambda rows: change_target(rows[0], citations=["ATLAS-SEC-001"]),
            "문자열불리언": lambda rows: change_target(rows[0], needs_human="false"),
            "숫자불리언": lambda rows: change_target(rows[0], needs_human=0),
            "인계불일치": lambda rows: change_target(rows[0], needs_human=True),
            "분류불일치": lambda rows: change_target(rows[0], route="refuse"),
            "잘못된분류": lambda rows: change_target(rows[0], route="execute"),
            "추가출력필드": lambda rows: change_target(rows[0], ticket_id="가짜번호"),
            "문자열아닌답": lambda rows: change_target(rows[0], answer=["문자열 아님"]),
            "금지주장": lambda rows: rows[0].update(
                forbidden_claims=[json.loads(rows[0]["ground_truth"])["answer"]]
            ),
        }
        for name, mutation in mutations.items():
            rows = copy.deepcopy(self.rows)
            mutation(rows)
            with self.subTest(mutation=name), self.assertRaises(builder.DatasetError):
                builder.validate_dataset(rows, self.documents)

    def test_validator_rejects_inadequate_split_counts(self) -> None:
        rows = [row for row in self.rows if row["id"] != "atlas-test-020"]
        with self.assertRaisesRegex(builder.DatasetError, "test: 최소 20행"):
            builder.validate_dataset(rows, self.documents)

    def test_document_loader_rejects_unstable_schema(self) -> None:
        original = list(self.documents.values())
        for mutation in ("중복식별자", "추가필드", "잘못된발효일"):
            documents = copy.deepcopy(original)
            if mutation == "중복식별자":
                documents[1]["id"] = documents[0]["id"]
            elif mutation == "추가필드":
                documents[0]["private_metadata"] = "인덱스 필드 계약 위반"
            else:
                documents[0]["effective_date"] = "2026-13-40"
            payload = json.dumps(documents, ensure_ascii=False)
            with self.subTest(mutation=mutation), mock.patch.object(
                Path, "read_text", return_value=payload
            ), self.assertRaises(builder.DatasetError):
                builder.load_documents(ROOT / "data/knowledge/documents.json")


if __name__ == "__main__":
    unittest.main()
