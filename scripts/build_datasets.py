#!/usr/bin/env python3
"""합성 원본을 검증하고 평가·학습·최적화용 JSONL을 결정적으로 내보냅니다."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from datetime import date
from itertools import combinations
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPLITS = ("train", "validation", "dev", "test")
ROUTES = frozenset(("answer", "clarify", "escalate", "refuse"))
MINIMUM_COUNTS = {"train": 48, "validation": 12, "dev": 12, "test": 20}
ROW_FIELDS = frozenset(
    (
        "id",
        "group_id",
        "split",
        "query",
        "context",
        "ground_truth",
        "expected_route",
        "required_citations",
        "tags",
    )
)
OUTPUT_FIELDS = frozenset(("answer", "citations", "route", "needs_human"))
DOCUMENT_FIELDS = frozenset(("id", "title", "content", "effective_date"))
CONTEXT_HEADER = re.compile(r"^\[([A-Z][A-Z0-9-]+)\]\n", re.MULTILINE)
AGENT_OPTIMIZER_PORTAL_DOC_URL = (
    "https://learn.microsoft.com/azure/foundry/agents/quickstarts/"
    "quickstart-optimize-prompt-agent#prerequisites"
)
SOURCE_PATHS = (
    "data/cases.jsonl",
    "data/knowledge/documents.json",
    "prompts/baseline.txt",
    "prompts/candidate.txt",
    "prompts/tuning-system.txt",
    "prompts/rubric.txt",
)
LANGUAGES = ("ko", "en")


class DatasetError(ValueError):
    """원본 또는 내보내기 계약 위반."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DatasetError(message)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"중복 JSON 키: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise DatasetError(f"JSON에서 허용되지 않는 상수: {value}")


def parse_json(text: str, location: str = "JSON") -> Any:
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (ValueError, TypeError) as exc:
        raise DatasetError(f"{location}: {exc}") from exc


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        require(bool(line.strip()), f"{path}:{number}: 빈 행은 허용하지 않습니다")
        row = parse_json(line, f"{path}:{number}")
        require(isinstance(row, dict), f"{path}:{number}: JSON 객체가 필요합니다")
        rows.append(row)
    return rows


def require_text(value: Any, label: str) -> None:
    require(
        isinstance(value, str) and bool(value.strip()),
        f"{label}: 비어 있지 않은 문자열이 필요합니다",
    )


def require_string_list(value: Any, label: str, *, nonempty: bool = True) -> None:
    require(isinstance(value, list), f"{label}: 문자열 배열이 필요합니다")
    require(not nonempty or bool(value), f"{label}: 빈 배열은 허용하지 않습니다")
    for item in value:
        require_text(item, label)
    require(len(value) == len(set(value)), f"{label}: 중복 항목이 있습니다")


def require_language_text(value: str, label: str, language: str) -> None:
    require(language in LANGUAGES, f"Unsupported content language: {language}")
    if language == "en":
        require(
            re.search(r"[A-Za-z]", value) is not None and re.search(r"[가-힣]", value) is None,
            f"{label}: English content is required; do not mix the Korean corpus into this dataset",
        )
    else:
        require(re.search(r"[가-힣]", value) is not None, f"{label}: 한국어가 필요합니다")


def load_documents(path: Path, *, language: str = "ko") -> dict[str, dict[str, str]]:
    source = parse_json(path.read_text(encoding="utf-8"), str(path))
    require(isinstance(source, list), "정책 파일의 최상위 값은 배열이어야 합니다")
    require(len(source) >= 4, "서로 다른 정책 문서가 최소 4개 필요합니다")
    documents = {}
    for document in source:
        require(isinstance(document, dict), "정책 문서는 객체여야 합니다")
        require(set(document) == DOCUMENT_FIELDS, "정책 문서의 필드가 계약과 다릅니다")
        for field in DOCUMENT_FIELDS:
            require_text(document[field], f"문서 {field}")
        doc_id = document["id"]
        require(
            re.fullmatch(r"ATLAS-[A-Z]+-\d{3}", doc_id) is not None,
            f"안정된 문서 식별자 형식이 아닙니다: {doc_id}",
        )
        require(doc_id not in documents, f"중복 문서 식별자: {doc_id}")
        try:
            effective = date.fromisoformat(document["effective_date"])
        except ValueError as exc:
            raise DatasetError(f"{doc_id}: 잘못된 발효일") from exc
        require(
            effective.isoformat() == document["effective_date"],
            f"{doc_id}: 발효일은 YYYY-MM-DD 형식이어야 합니다",
        )
        require_language_text(document["content"], doc_id, language)
        if language == "en":
            require_language_text(document["title"], f"{doc_id} title", language)
        documents[doc_id] = document
    return documents


def context_document_ids(
    context: str, documents: dict[str, dict[str, str]]
) -> list[str]:
    require_text(context, "context")
    headers = list(CONTEXT_HEADER.finditer(context))
    require(bool(headers) and headers[0].start() == 0, "문맥은 [문서 식별자]로 시작해야 합니다")
    doc_ids = []
    for index, header in enumerate(headers):
        doc_id = header.group(1)
        require(doc_id in documents, f"문맥의 문서가 존재하지 않습니다: {doc_id}")
        require(doc_id not in doc_ids, f"문맥의 문서 블록이 중복됩니다: {doc_id}")
        end = headers[index + 1].start() if index + 1 < len(headers) else len(context)
        excerpt = context[header.end() : end].rstrip("\n")
        require(bool(excerpt), f"{doc_id}: 발췌가 비어 있습니다")
        paragraphs = excerpt.split("\n\n")
        original = documents[doc_id]["content"].split("\n\n")
        positions = []
        for paragraph in paragraphs:
            require(
                paragraph in original,
                f"{doc_id}: 문맥은 정책 원문 문단을 그대로 발췌해야 합니다",
            )
            positions.append(original.index(paragraph))
        require(
            positions == sorted(set(positions)),
            f"{doc_id}: 문단 순서를 유지하고 같은 문단을 반복하지 않아야 합니다",
        )
        doc_ids.append(doc_id)
    return doc_ids


def validate_output(output: Any, allowed_citations: set[str], *, language: str = "ko") -> None:
    require(isinstance(output, dict), "모범 응답은 JSON 객체여야 합니다")
    require(set(output) == OUTPUT_FIELDS, "모범 응답의 필드가 출력 계약과 다릅니다")
    require_text(output["answer"], "answer")
    require_language_text(output["answer"], "answer", language)
    require_string_list(output["citations"], "citations", nonempty=False)
    require(
        set(output["citations"]) <= allowed_citations,
        "제공한 문맥에 없는 문서를 응답에서 인용했습니다",
    )
    require(isinstance(output["route"], str) and output["route"] in ROUTES, "잘못된 route")
    require(type(output["needs_human"]) is bool, "needs_human은 JSON 불리언이어야 합니다")
    require(
        output["needs_human"] is (output["route"] == "escalate"),
        "needs_human은 escalate일 때만 true여야 합니다",
    )


def normalize_query(query: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", query).casefold().split())


def validate_dataset(
    rows: list[dict[str, Any]], documents: dict[str, dict[str, str]], *, language: str = "ko",
) -> dict[str, Any]:
    require(language in LANGUAGES, f"Unsupported content language: {language}")
    require(isinstance(rows, list) and bool(rows), "사례 배열이 비어 있습니다")
    seen_ids: set[str] = set()
    seen_queries: set[str] = set()
    group_splits: dict[str, str] = {}
    counts: Counter[str] = Counter()
    by_split = {split: [] for split in SPLITS}
    for row in rows:
        require(isinstance(row, dict), "사례는 JSON 객체여야 합니다")
        keys = set(row)
        require(
            ROW_FIELDS <= keys <= ROW_FIELDS | {"forbidden_claims"},
            "사례 필드가 계약과 다릅니다",
        )
        for field in ROW_FIELDS - {"required_citations", "tags"}:
            require_text(row[field], field)
        if language == "en":
            for field in ("query", "context"):
                require_language_text(row[field], field, language)
        case_id = row["id"]
        split = row["split"]
        require(split in SPLITS, f"{case_id}: 잘못된 split")
        require(
            re.fullmatch(rf"atlas-{split}-\d{{3}}", case_id) is not None,
            f"{case_id}: 사례 식별자와 split이 맞지 않습니다",
        )
        require(case_id not in seen_ids, f"중복 사례 식별자: {case_id}")
        seen_ids.add(case_id)
        query = normalize_query(row["query"])
        require(query not in seen_queries, f"{case_id}: 중복 문의")
        seen_queries.add(query)
        group = row["group_id"]
        require(
            re.fullmatch(r"[a-z][a-z0-9-]+", group) is not None,
            f"{case_id}: group_id는 읽을 수 있는 영문 슬러그여야 합니다",
        )
        require(
            group not in group_splits or group_splits[group] == split,
            f"{case_id}: group_id가 분할 사이에 유출되었습니다",
        )
        group_splits[group] = split
        context_ids = context_document_ids(row["context"], documents)
        require_string_list(row["required_citations"], f"{case_id} required_citations")
        require_string_list(row["tags"], f"{case_id} tags")
        require(
            set(row["required_citations"]) <= set(context_ids),
            f"{case_id}: 필수 인용 문서가 문맥에 없습니다",
        )
        output = parse_json(row["ground_truth"], f"{case_id} ground_truth")
        validate_output(output, set(context_ids), language=language)
        require(output["route"] == row["expected_route"], f"{case_id}: 분류가 정답과 다릅니다")
        require(
            set(output["citations"]) == set(row["required_citations"]),
            f"{case_id}: 모범 답변 인용과 필수 인용이 다릅니다",
        )
        if "forbidden_claims" in row:
            require_string_list(row["forbidden_claims"], f"{case_id} forbidden_claims")
            for claim in row["forbidden_claims"]:
                require(
                    claim not in output["answer"],
                    f"{case_id}: 모범 답변에 금지된 주장이 들어 있습니다",
                )
        for label in ("ground_truth", "expected_route", "required_citations", "forbidden_claims"):
            require(
                label not in row["query"] and label not in row["context"],
                f"{case_id}: 평가자 전용 필드가 모델 입력에 들어 있습니다",
            )
        counts[split] += 1
        by_split[split].append(row)
    for split in SPLITS:
        require(
            counts[split] >= MINIMUM_COUNTS[split],
            f"{split}: 최소 {MINIMUM_COUNTS[split]}행이 필요합니다",
        )
    require(counts["train"] <= 64, "이 실습의 train 목표는 48~64행입니다")
    pairs = []
    for left, right in combinations(SPLITS, 2):
        left_rows, right_rows = by_split[left], by_split[right]
        pairs.append(
            {
                "left": left,
                "right": right,
                "id_overlap": sorted({r["id"] for r in left_rows} & {r["id"] for r in right_rows}),
                "group_overlap": sorted(
                    {r["group_id"] for r in left_rows} & {r["group_id"] for r in right_rows}
                ),
                "normalized_query_overlap_count": len(
                    {normalize_query(r["query"]) for r in left_rows}
                    & {normalize_query(r["query"]) for r in right_rows}
                ),
            }
        )
    return {
        "counts": dict(counts),
        "group_counts": {
            split: len({row["group_id"] for row in by_split[split]}) for split in SPLITS
        },
        "route_counts": {
            split: dict(sorted(Counter(row["expected_route"] for row in by_split[split]).items()))
            for split in SPLITS
        },
        "critical_counts": {
            split: sum("critical" in row["tags"] for row in by_split[split]) for split in SPLITS
        },
        "split_disjointness": {"passed": True, "pairs": pairs},
    }


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8")


def render_user_message(row: dict[str, Any]) -> str:
    """평가용 라벨이 아닌 query와 정책 발췌만 모델에 보냅니다."""
    return canonical_json({"query": row["query"], "context": row["context"]})


def sft_record(row: dict[str, Any], system_prompt: str) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": render_user_message(row)},
            {"role": "assistant", "content": row["ground_truth"]},
        ]
    }


def optimizer_record(row: dict[str, Any]) -> dict[str, Any]:
    """포털 평가 열로 내보냅니다. query만 에이전트 입력이고 나머지는 평가자용입니다."""
    return {
        "query": row["query"],
        "ground_truth": row["ground_truth"],
        "context": row["context"],
    }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_artifacts(root: Path = ROOT, *, language: str = "ko") -> dict[str, bytes]:
    """검증된 생성물의 상대 경로와 바이트를 반환하며 파일을 쓰지 않습니다."""
    require(language in LANGUAGES, f"Unsupported content language: {language}")
    data_prefix = "data/en" if language == "en" else "data"
    prompt_prefix = "prompts/en" if language == "en" else "prompts"
    source_paths = tuple(
        path.replace("data/", data_prefix + "/", 1).replace("prompts/", prompt_prefix + "/", 1)
        for path in SOURCE_PATHS
    )
    documents = load_documents(root / data_prefix / "knowledge/documents.json", language=language)
    rows = read_jsonl(root / data_prefix / "cases.jsonl")
    audit = validate_dataset(rows, documents, language=language)
    system_prompt = (root / prompt_prefix / "tuning-system.txt").read_text(encoding="utf-8").strip()
    require_text(system_prompt, "학습 system 프롬프트")
    split_rows = {
        split: sorted((row for row in rows if row["split"] == split), key=lambda row: row["id"])
        for split in SPLITS
    }
    artifacts: dict[str, bytes] = {}
    export_info: dict[str, dict[str, Any]] = {}

    def add(path: str, records: list[dict[str, Any]], source_split: str, purpose: str) -> None:
        artifacts[path] = jsonl_bytes(records)
        export_info[path] = {
            "rows": len(records),
            "sha256": sha256(artifacts[path]),
            "source_splits": [source_split],
            "purpose": purpose,
        }

    for split in SPLITS:
        add(
            f"{data_prefix}/splits/{split}.jsonl", split_rows[split], split,
            "Local evaluation cases" if language == "en" else "로컬 평가 사례",
        )
    for split in ("train", "validation"):
        add(
            f"{data_prefix}/tuning/sft-{split}.jsonl",
            [sft_record(row, system_prompt) for row in split_rows[split]],
            split,
            "Supervised fine-tuning messages" if language == "en" else "지도 미세조정용 messages",
        )
    add(
        f"{data_prefix}/optimizer/dev.jsonl",
        [optimizer_record(row) for row in split_rows["dev"]],
        "dev",
        "Prompt-agent Agent Optimizer portal evaluation JSONL"
        if language == "en" else "프롬프트 에이전트 Agent Optimizer 포털 평가 JSONL",
    )

    restricted = [path for path in artifacts if "/tuning/" in path or "/optimizer/" in path]
    for row in split_rows["test"]:
        for path in restricted:
            payload = artifacts[path].decode("utf-8")
            require(row["id"] not in payload, f"{path}: 동결 test 식별자가 유출되었습니다")
            escaped_query = json.dumps(row["query"], ensure_ascii=False)[1:-1]
            require(
                row["query"] not in payload and escaped_query not in payload,
                f"{path}: 동결 test 문의가 유출되었습니다",
            )

    manifest = {
        "schema_version": 1,
        "dataset": f"contoso-atlas-cloud-{language}-v1",
        "synthetic": True,
        "master_rows": len(rows),
        "documents": len(documents),
        **audit,
        "sources_sha256": {path: sha256((root / path).read_bytes()) for path in source_paths},
        "exports": export_info,
        "holdout_checks": {
            "test_ids_in_tuning_or_optimizer": 0,
            "test_queries_in_tuning_or_optimizer": 0,
            "optimizer_source_splits": ["dev"],
            "sft_source_splits": ["train", "validation"],
        },
        "provenance": {
            "authoring": "강사가 수동 작성한 완전 합성 정책·문의·모범 응답입니다.",
            "candidate_prompt": "강사 작성 비교 후보이며 공식 최적화 실행 결과가 아닙니다.",
            "optimizer_export": {
                "service": "Agent Optimizer",
                "lane": "prompt-agent-portal",
                "schema_reference": AGENT_OPTIMIZER_PORTAL_DOC_URL,
                "columns": ["query", "ground_truth", "context"],
                "agent_input_columns": ["query"],
                "evaluator_only_columns": ["ground_truth", "context"],
                "column_mapping_supported": False,
                "authored_locally": True,
                "query_includes_reference_context": False,
            },
            "network_or_model_calls": False,
            "performance_metrics": "포함하지 않습니다. 실제 평가를 별도로 실행해야 합니다.",
            "paraphrase_review": "상황·판단 과제별로 수동 분리합니다. 식별자 검사만으로 의미 중복이 없음을 보증하지 않습니다.",
        },
    }
    if language == "en":
        manifest.update(language="en", localization_of="contoso-atlas-cloud-ko-v1")
        manifest["provenance"].update(
            authoring="AI-authored English localization of synthetic policies, questions and reference answers; not human-reviewed.",
            candidate_prompt="Authored comparison candidate, not an official optimization result.",
            performance_metrics="Not included; actual evaluation must be executed separately.",
            paraphrase_review="Scenario groups are preserved; identifier and lexical checks do not prove semantic independence.",
        )
    artifacts[f"{data_prefix}/manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    return artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="쓰지 않고 현재 생성물과 원본의 일치 여부 검사")
    parser.add_argument("--language", choices=LANGUAGES, default=os.environ.get("LAB_LANGUAGE", "ko"))
    args = parser.parse_args(argv)
    try:
        artifacts = build_artifacts(language=args.language)
        mismatches = []
        for relative, data in artifacts.items():
            path = ROOT / relative
            if args.check:
                if not path.is_file() or path.read_bytes() != data:
                    mismatches.append(relative)
            elif not path.is_file() or path.read_bytes() != data:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        if mismatches:
            if args.language == "en":
                print("Generated files are missing or stale:\n" + "\n".join(mismatches), file=sys.stderr)
                print(f"Regenerate them with: python scripts/build_datasets.py --language {args.language}", file=sys.stderr)
            else:
                print("생성물이 없거나 오래되었습니다:\n" + "\n".join(mismatches), file=sys.stderr)
                print(f"python scripts/build_datasets.py --language {args.language} 명령으로 다시 생성해야 합니다.", file=sys.stderr)
            return 1
        manifest_path = "data/en/manifest.json" if args.language == "en" else "data/manifest.json"
        manifest = parse_json(artifacts[manifest_path].decode("utf-8"))
        counts = ", ".join(f"{split}={manifest['counts'][split]}" for split in SPLITS)
        if args.language == "en":
            action = "Consistency check" if args.check else "Generation"
            print(f"{action} complete: {counts}; policies={manifest['documents']}; artifacts={len(artifacts)}")
        else:
            action = "일치 검사" if args.check else "생성"
            print(f"{action} 완료: {counts}; 정책 {manifest['documents']}개; 생성물 {len(artifacts)}개")
        return 0
    except (DatasetError, OSError) as exc:
        print(f"데이터 오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
