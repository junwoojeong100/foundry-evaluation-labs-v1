"""Capture actual agent outputs, preserving failures and provenance."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time

from azure.ai.projects import AIProjectClient
from openai import APIError

from lab.agents import load_agent
from lab.auth import credential_for
from lab.config import Config, LabError
from lab.files import ROOT, read_json, read_jsonl, safe_run_dir, sha256_file, write_jsonl
from lab.preflight import model_snapshot, save_json


def response_context(payload: dict) -> str:
    outputs = []
    for item in payload.get("output", []):
        if item.get("type") == "mcp_call" and isinstance(item.get("output"), str):
            outputs.append(item["output"])
    return "\n\n".join(outputs)


def retrieval_observation(records: list[dict]) -> dict:
    successful_rows = []
    calls = 0
    errors = 0
    for record in records:
        found = False
        for item in (record.get("response") or {}).get("output", []):
            if item.get("type") != "mcp_call" or item.get("name") != "knowledge_base_retrieve":
                continue
            calls += 1
            output = item.get("output")
            is_error = item.get("error") is not None
            if isinstance(output, str) and output.strip():
                try:
                    parsed = json.loads(output)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, dict):
                    is_error = is_error or parsed.get("isError") is True
                    nested = parsed.get("result")
                    if isinstance(nested, dict):
                        is_error = is_error or nested.get("isError") is True
                if not is_error:
                    found = True
            if is_error:
                errors += 1
        if found:
            successful_rows.append(record["id"])
    return {
        "knowledge_tool_calls": calls,
        "tool_error_calls": errors,
        "rows_with_tool_output": len(successful_rows),
        "row_ids_with_tool_output": successful_rows,
        "meaning": "Observed non-error tool outputs, not a semantic retrieval-quality score.",
    }


def capture_case(client, agent: dict, case: dict) -> dict:
    started = time.perf_counter()
    try:
        response = client.responses.create(
            input=case["query"],
            extra_body={
                "agent_reference": {
                    "type": "agent_reference",
                    "name": agent["name"],
                    "version": agent["version"],
                },
            },
            max_output_tokens=4096,
            max_tool_calls=3,
            store=True,
            metadata={
                "lab_workspace": agent["workspace_id"],
                "lab_case": case["id"],
                "lab_agent": agent["name"],
            },
        )
    except APIError as exc:
        return {
            "id": case["id"],
            "raw_output": "",
            "latency_ms": (time.perf_counter() - started) * 1000,
            "usage": None,
            "response_id": None,
            "retrieved_context": "",
            "error": f"{type(exc).__name__}: {exc}",
            "response": None,
        }
    payload = response.model_dump(mode="json")
    status = payload.get("status")
    error = None if status == "completed" else f"Response status={status}; details={payload.get('incomplete_details')}"
    return {
        "id": case["id"],
        "raw_output": response.output_text or "",
        "latency_ms": (time.perf_counter() - started) * 1000,
        "usage": payload.get("usage"),
        "response_id": response.id,
        "retrieved_context": response_context(payload),
        "error": error,
        "response": payload,
    }


def run_batch(config: Config, stage: str, split: str, run_id: str, *, limit: int | None = None) -> dict:
    from lab.evidence import validate_case

    if split not in {"dev", "test"}:
        raise LabError("평가 실행 데이터는 dev 또는 test만 허용합니다.")
    dataset_path = ROOT / "data/splits" / f"{split}.jsonl"
    cases = read_jsonl(dataset_path)
    for case in cases:
        validate_case(case)
        if case["split"] != split:
            raise LabError("선택한 파일과 사례의 split이 다릅니다. 호출 전에 데이터를 수정하세요.")
    ids = [case.get("id") for case in cases]
    if (
        any(not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value) for value in ids)
        or len(set(ids)) != len(ids)
    ):
        raise LabError("데이터셋 ID가 중복되거나 안전한 파일 이름 형식이 아닙니다.")
    if limit is not None:
        if limit < 1 or limit > len(cases):
            raise LabError(f"limit은 1~{len(cases)} 사이여야 합니다.")
        cases = cases[:limit]
    run_dir = safe_run_dir(run_id)
    if run_dir.exists():
        raise LabError(f"{run_dir}이 이미 존재합니다. 원본 근거를 덮어쓰지 말고 새 run-id를 지정하세요.")
    agent = load_agent(config, stage)
    if stage != "baseline" and sha256_file(ROOT / "data/knowledge/documents.json") != agent["knowledge_sha256"]:
        raise LabError("에이전트 생성 후 지식 원본이 바뀌었습니다. 새 지식·에이전트 버전을 기록하세요.")
    metadata = {
        "run_id": run_id,
        "stage": stage,
        "target_type": "agent",
        "split": "smoke" if limit is not None else split,
        "source_split": split,
        "dataset_sha256": sha256_file(dataset_path),
        "model_deployment": agent["model_deployment"],
        "prompt_sha256": agent["prompt_sha256"],
        "prompt_source": agent["prompt_source"],
        "knowledge_sha256": agent["knowledge_sha256"],
        "agent_name": agent["name"],
        "agent_version": agent["version"],
        "workspace_id": agent["workspace_id"],
        "prompt_snapshot": agent["prompt_snapshot"],
        "project_endpoint": config.project_endpoint,
        "judge": None,
        "parameters": {"max_output_tokens": 4096, "max_tool_calls": 3, "retries": 0, "timeout_seconds": 120},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "row_ids": [case["id"] for case in cases],
        "status": "running",
    }
    with credential_for(config) as credential:
        before_model = model_snapshot(config, agent["model_deployment"])
        if before_model != agent.get("model_snapshot"):
            raise LabError("에이전트 생성 후 모델 배포 구성이 바뀌었습니다. 같은 기반 버전으로 실험을 다시 고정하세요.")
        metadata["model_snapshot"] = before_model
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential) as project:
            remote = project.agents.get_version(agent_name=agent["name"], agent_version=agent["version"])
            if remote.definition.model != agent["model_deployment"]:
                raise LabError("원격 에이전트 모델과 로컬 버전 기록이 다릅니다.")
            save_json(run_dir / "metadata.json", metadata)
            records = []
            with project.get_openai_client(max_retries=0, timeout=120.0) as client:
                for index, case in enumerate(cases, start=1):
                    record = capture_case(client, agent, case)
                    records.append(record)
                    save_json(run_dir / "raw" / f"{case['id']}.json", record)
                    write_jsonl(run_dir / "outputs.jsonl", records)
                    print(f"[{index}/{len(cases)}] {case['id']}: {'ERROR' if record['error'] else 'captured'}", flush=True)
    final_status = "completed_with_errors" if any(r["error"] for r in records) else "completed"
    metadata["status"] = "verifying_model"
    metadata["retrieval"] = retrieval_observation(records)
    metadata["completed_at"] = datetime.now(timezone.utc).isoformat()
    save_json(run_dir / "metadata.json", metadata)
    try:
        after_model = model_snapshot(config, agent["model_deployment"])
    except LabError as exc:
        metadata["status"] = "unverified_model_after_capture"
        metadata["model_verification_error"] = str(exc)
        save_json(run_dir / "metadata.json", metadata)
        raise
    if after_model != before_model:
        metadata["status"] = "invalid_model_drift"
        metadata["model_snapshot_after"] = after_model
        save_json(run_dir / "metadata.json", metadata)
        raise LabError("실행 도중 모델 배포가 바뀌었습니다. 캡처는 보존했지만 비교 근거로 승인하지 않습니다.")
    metadata["status"] = final_status
    save_json(run_dir / "metadata.json", metadata)
    export_evaluation(run_dir, cases, records)
    if stage != "baseline" and metadata["retrieval"]["rows_with_tool_output"] == 0:
        print("WARNING: IQ 도구의 정상 출력이 한 건도 관찰되지 않았습니다. 검색 효과를 판단하지 말고 연결/권한/지시를 확인하세요.", file=sys.stderr)
    return metadata


def export_evaluation(run_dir: Path, cases: list[dict], records: list[dict]) -> None:
    from lab.evidence import score_row, strict_json_loads

    exported = []
    format_invalid = 0
    known_citations = {doc["id"] for doc in read_json(ROOT / "data/knowledge/documents.json")}
    for case, record in zip(cases, records, strict=True):
        if case["id"] != record["id"]:
            raise LabError("질문과 응답의 ID가 서로 다릅니다. 평가 내보내기를 중단합니다.")
        if record["error"]:
            continue
        scored = score_row(case, record["raw_output"], known_citations=known_citations)
        if not scored["schema_valid"]:
            format_invalid += 1
            continue
        expected = strict_json_loads(case["ground_truth"])
        if not isinstance(expected, dict) or not isinstance(expected.get("answer"), str):
            raise LabError(f"{case['id']} ground_truth에 자연어 answer가 없습니다.")
        exported.append({
            "case_id": case["id"],
            "query": case["query"],
            "response": scored["response"]["answer"],
            "context": case["context"],
            "ground_truth": expected["answer"],
            "retrieved_context": record["retrieved_context"],
        })
    if exported:
        write_jsonl(run_dir / "foundry-eval.jsonl", exported)
    save_json(run_dir / "export-notes.json", {
        "total_cases": len(cases),
        "exported_rows": len(exported),
        "failed_rows": len(cases) - len(exported),
        "format_invalid_rows": format_invalid,
        "response_projection": "Only the answer field of schema-valid JSON responses and ground_truth; routing is scored separately.",
        "context_definition": "Fixed reference policy excerpts; not claimed to be the agent's retrieved context.",
        "retrieved_context_definition": "Actual MCP output when present. Empty means retrieval was not observed.",
        "warning": "Service errors remain failures in local scores. A managed-eval subset cannot grant a release pass.",
    })


def score_run(run_id: str) -> dict:
    from lab.evidence import score_row, summarize, write_report

    run_dir = safe_run_dir(run_id)
    metadata = read_json(run_dir / "metadata.json")
    if metadata.get("status") not in {"completed", "completed_with_errors"}:
        raise LabError("완료되지 않은 실행입니다. 부분 결과를 성공으로 요약하지 않습니다.")
    dataset_path = ROOT / "data/splits" / f"{metadata['source_split']}.jsonl"
    if sha256_file(dataset_path) != metadata["dataset_sha256"]:
        raise LabError("실행 후 데이터셋이 변경되었습니다. 원본 데이터로 복구하거나 새 실행을 만드세요.")
    case_map = {case["id"]: case for case in read_jsonl(dataset_path)}
    records = read_jsonl(run_dir / "outputs.jsonl")
    if [r["id"] for r in records] != metadata["row_ids"]:
        raise LabError("실행의 행 목록과 응답 기록이 다릅니다.")
    known_citations = {doc["id"] for doc in read_json(ROOT / "data/knowledge/documents.json")}
    judge_path = run_dir / "judge-scores.json"
    judge_scores = read_json(judge_path) if judge_path.exists() else {}
    rows = [
        score_row(
            case_map[record["id"]], record["raw_output"],
            known_citations=known_citations, latency_ms=record["latency_ms"],
            usage=record["usage"], error=record["error"],
            judge=judge_scores.get(record["id"]),
        )
        for record in records
    ]
    summary = summarize(rows, metadata=metadata)
    save_json(run_dir / "summary.json", summary)
    write_report(summary, run_dir / "report.md")
    if metadata.get("target_type") == "agent":
        observed = retrieval_observation(records)
        with (run_dir / "report.md").open("a", encoding="utf-8") as report:
            report.write(
                "\n## IQ 도구 관찰 (품질 점수와 별개)\n\n"
                f"- 호출: {observed['knowledge_tool_calls']}회; 오류: {observed['tool_error_calls']}회\n"
                f"- 정상 도구 출력을 관찰한 질문: {observed['rows_with_tool_output']}/{len(records)}\n"
                "- 호출 성공은 의미상의 검색 품질을 보증하지 않습니다. 거절·일반 확인 질문은 검색이 불필요할 수 있습니다.\n"
            )
            if metadata["stage"] != "baseline" and observed["rows_with_tool_output"] == 0:
                report.write("- **주의: 실제 IQ 사용이 관찰되지 않았습니다. 이 실행으로 검색 개선 효과를 결론 내리지 마세요.**\n")
    return summary
