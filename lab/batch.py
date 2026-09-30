"""Capture actual outputs with durable recovery and terminal drift invalidation.

Restoring a deployment cannot rehabilitate a run that observed model drift.
Such captures remain available for inspection, never resume or quality approval.
"""

from copy import deepcopy
from functools import wraps
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time

from lab.config import Config, LabError
from lab.files import ROOT, code_provenance, read_json, read_jsonl, safe_run_dir, sha256_file, write_jsonl
from lab.preflight import model_snapshot, save_json


def AIProjectClient(**kwargs):
    from azure.ai.projects import AIProjectClient as factory
    return factory(**kwargs)


def load_agent(config, stage):
    from lab.agents import load_agent as load
    return load(config, stage)


def credential_for(config):
    from lab.auth import credential_for as factory
    return factory(config)


def _capture_lock(function):
    @wraps(function)
    def guarded(config, stage, split, run_id, **kwargs):
        from lab.calibration import save_json as durable_json

        directory = safe_run_dir(run_id)
        lock = directory.parent / f".{run_id}.capture-lock.json"
        try:
            durable_json(lock, {"run_id": run_id, "state": "capture_in_progress"}, exclusive=True)
        except LabError as exc:
            raise LabError(
                f"Capture lock exists: {lock}. Confirm no capture process is active before "
                "manually recovering a stale lock; never delete per-case submission checkpoints."
            ) from exc
        try:
            return function(config, stage, split, run_id, **kwargs)
        finally:
            lock.unlink(missing_ok=True)
    return guarded


def _retrieval_error(item: dict) -> bool:
    if item.get("error") is not None:
        return True
    output = item.get("output")
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
        except ValueError:
            parsed = None
        if isinstance(parsed, dict):
            return parsed.get("isError") is True or (
                isinstance(parsed.get("result"), dict) and parsed["result"].get("isError") is True
            )
    return False


def response_context(payload: dict) -> str:
    outputs = []
    for item in payload.get("output", []):
        if (
            item.get("type") == "mcp_call" and item.get("name") == "knowledge_base_retrieve"
            and isinstance(item.get("output"), str) and not _retrieval_error(item)
        ):
            outputs.append(item["output"])
        elif item.get("type") == "file_search_call" and item.get("status") == "completed":
            for result in item.get("results", []) or []:
                if isinstance(result, dict) and isinstance(result.get("text"), str):
                    outputs.append(result["text"])
    return "\n\n".join(outputs)


def retrieval_observation(records: list[dict]) -> dict:
    successful_rows = []
    calls = 0
    errors = 0
    for record in records:
        found = False
        payloads = [turn.get("response") or {} for turn in record.get("turns", [])] or [record.get("response") or {}]
        for item in [item for payload in payloads for item in payload.get("output", [])]:
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


def _case_inputs(case: dict) -> list[str]:
    inputs = [case["query"]]
    if not isinstance(inputs[0], str) or not inputs[0].strip():
        raise LabError("Agent query must be a nonempty string.")
    if "follow_up" in case:
        if not isinstance(case["follow_up"], str) or not case["follow_up"].strip():
            raise LabError("A scripted conversation needs an explicit nonempty follow_up.")
        if not isinstance(case.get("scripted_user_source"), str) or not case["scripted_user_source"].strip():
            raise LabError("A follow-up must name its scripted-user source, not imply human approval.")
        inputs.append(case["follow_up"])
    return inputs


def _aggregate_case(case: dict, turns: list[dict], error: str | None = None) -> dict:
    last = turns[-1]
    usage = {}
    for metric in ("input_tokens", "output_tokens", "total_tokens"):
        values = [(turn.get("usage") or {}).get(metric) for turn in turns]
        usage[metric] = sum(values) if all(type(value) is int and value >= 0 for value in values) else None
    latencies = [turn.get("latency_ms") for turn in turns]
    return {
        "id": case["id"], "raw_output": last.get("raw_output", ""),
        "latency_ms": sum(latencies) if all(value is not None for value in latencies) else None,
        "usage": usage, "response_id": last.get("response_id"),
        "retrieved_context": "\n\n".join(turn["retrieved_context"] for turn in turns if turn.get("retrieved_context")),
        "error": error or last.get("error"), "response": last.get("response"),
        "state": "failed" if error else last["state"], "turns": deepcopy(turns),
        "conversation_mode": "scripted_follow_up" if "follow_up" in case else "single_turn",
        "initial_turn_validation": "schema_and_clarify_only/not_semantic_safety" if "follow_up" in case else None,
        "manual_operational_approval": "not_granted",
    }


def capture_case(client, agent: dict, case: dict, *, checkpoint=None, resume_record: dict | None = None,
                 interval_seconds: float = 0) -> dict:
    """Capture one/two explicit user turns; checkpoints precede every POST.

    A known pending response is retrieved once on resume. A missing response ID
    after a submission intent is uncertain, never permission to resubmit.
    """
    from lab.evidence import _schema_errors, strict_json_loads

    inputs = _case_inputs(case)
    turns = deepcopy((resume_record or {}).get("turns", []))
    if resume_record and not turns:
        if resume_record.get("state") in {"completed", "failed"} or (
            "state" not in resume_record and resume_record.get("error") is None
        ):
            return resume_record
        raise LabError("Legacy/unknown incomplete capture has no recoverable turn checkpoint. Do not resubmit.")
    for index, user_input in enumerate(inputs):
        if index < len(turns):
            turn = turns[index]
            if turn.get("input") != user_input:
                raise LabError("Scripted input changed since the checkpoint.")
            if turn.get("state") == "failed":
                return _aggregate_case(case, turns)
            if turn.get("state") == "completed":
                continue
            if not turn.get("response_id"):
                raise LabError("Unknown submission outcome: preserve checkpoint and recover a verified response ID; no blind resubmission.")
            recovering = True
        else:
            if index:
                try:
                    initial = strict_json_loads(turns[0]["raw_output"])
                    valid = not _schema_errors(initial) and initial["route"] == "clarify"
                except ValueError:
                    valid = False
                if not valid:
                    result = _aggregate_case(case, turns, "script_protocol: initial response was not a schema-valid clarification")
                    if checkpoint:
                        checkpoint(result)
                    return result
                if interval_seconds:
                    time.sleep(interval_seconds)
            turn = {
                "turn_index": index, "input": user_input,
                "input_source": "scripted_user" if index else "dataset_query",
                "scripted_user_source": case.get("scripted_user_source") if index else None,
                "state": "submitting", "response_id": None, "raw_output": "", "retrieved_context": "",
                "response": None, "usage": None, "latency_ms": None, "error": None,
                "previous_response_id": turns[index - 1]["response_id"] if index else None,
            }
            turns.append(turn)
            recovering = False
        if checkpoint:
            checkpoint(_aggregate_case(case, turns))
        started = time.perf_counter()
        try:
            if recovering:
                response = client.responses.retrieve(turn["response_id"])
                if response.id != turn["response_id"]:
                    raise ValueError("Recovered response ID differs from the saved checkpoint.")
            else:
                arguments = {
                    "input": user_input,
                    "extra_body": {"agent_reference": {
                        "type": "agent_reference", "name": agent["name"], "version": agent["version"],
                    }},
                    "max_output_tokens": 4096, "max_tool_calls": 3, "store": True,
                    "metadata": {
                        "lab_workspace": agent["workspace_id"], "lab_case": case["id"],
                        "lab_agent": agent["name"], "lab_turn": str(index),
                    },
                }
                if turn["previous_response_id"]:
                    arguments["previous_response_id"] = turn["previous_response_id"]
                response = client.responses.create(**arguments)
            turn.update(response_id=response.id, state="received")
            if checkpoint:
                checkpoint(_aggregate_case(case, turns))
            if not isinstance(response.id, str) or not response.id:
                raise ValueError("Response has no usable remote ID.")
            payload = response.model_dump(mode="json")
            if recovering:
                identity = payload.get("metadata") or {}
                if any(identity.get(key) != value for key, value in {
                    "lab_case": case["id"], "lab_agent": agent["name"],
                    "lab_workspace": agent["workspace_id"], "lab_turn": str(index),
                }.items()):
                    raise ValueError("Recovered response metadata does not match this case/agent/turn.")
            status = payload.get("status")
            turn.update(
                response=payload, raw_output=response.output_text or "", usage=payload.get("usage"),
                retrieved_context=response_context(payload),
                latency_ms=None if recovering else (time.perf_counter() - started) * 1000,
                state="completed" if status == "completed" else "pending_response" if status in {"queued", "in_progress"} else "failed",
                error=None if status == "completed" else f"Response status={status}; details={payload.get('error') or payload.get('incomplete_details')}",
            )
        except Exception as exc:
            turn.update(
                state="failed" if getattr(exc, "status_code", None) in {400, 401, 403, 404, 422} else "unknown_outcome",
                error=f"{type(exc).__name__}: {exc}",
                access_blocker=getattr(exc, "status_code", None) in {401, 403},
            )
        if checkpoint:
            checkpoint(_aggregate_case(case, turns))
        if turn["state"] != "completed":
            return _aggregate_case(case, turns)
    return _aggregate_case(case, turns)


def dataset_for_metadata(metadata: dict) -> Path:
    if metadata.get("dialogue_diagnostic") is True:
        if metadata.get("source_split") != "dev" or metadata.get("freeze_id"):
            raise LabError("Scripted dialogue diagnostics are separate dev data, never final holdout.")
        return ROOT / "data/dialogue/dev.jsonl"
    if metadata.get("holdout_id"):
        from lab.governance import load_holdout
        if not metadata.get("freeze_id"):
            raise LabError("Fresh holdout metadata requires its exact freeze.")
        holdout, path = load_holdout(metadata["freeze_id"], metadata["holdout_id"])
        if metadata.get("dataset_sha256") != holdout["dataset_sha256"]:
            raise LabError("Run and registered holdout hashes differ.")
        return path
    split = metadata.get("source_split")
    if not isinstance(split, str) or split not in {"dev", "test"}:
        raise LabError("Captured dataset source_split must be dev/test.")
    return ROOT / "data/splits" / f"{split}.jsonl"


@_capture_lock
def run_batch(config: Config, stage: str, split: str, run_id: str, *, limit: int | None = None,
              resume: bool = False, freeze_id: str | None = None, holdout_id: str | None = None,
              interval_seconds: float = 0, dialogue: bool = False) -> dict:
    from lab.evidence import observed_model_drift, validate_case

    if split not in {"dev", "test"}:
        raise LabError("평가 실행 데이터는 dev 또는 test만 허용합니다.")
    if type(interval_seconds) not in (int, float) or not 0 <= interval_seconds <= 120:
        raise LabError("interval-seconds는 0~120초여야 합니다.")
    if bool(freeze_id) != bool(holdout_id):
        raise LabError("freeze-id and holdout-id must be supplied together.")
    if dialogue and (split != "dev" or freeze_id):
        raise LabError("대화 진단은 별도 dev 사례이며 최종 holdout과 섞지 않습니다.")
    frozen = None
    if freeze_id:
        from lab.governance import bind_holdout_attempt, load_freeze, load_holdout
        if split != "test" or limit is not None:
            raise LabError("Frozen holdout evaluation is full test only, never a limited smoke run.")
        frozen = load_freeze(freeze_id)
        if frozen["stage"] != stage or frozen["execution_mode"] != "LIVE":
            raise LabError("Frozen stage/mode differs; DEMO evidence cannot trigger a LIVE batch.")
        _, dataset_path = load_holdout(freeze_id, holdout_id)
    else:
        dataset_path = ROOT / "data/dialogue/dev.jsonl" if dialogue else ROOT / "data/splits" / f"{split}.jsonl"
    cases = read_jsonl(dataset_path)
    for case in cases:
        validate_case(case)
        if case["split"] != split:
            raise LabError("선택한 파일과 사례의 split이 다릅니다. 호출 전에 데이터를 수정하세요.")
        _case_inputs(case)
    ids = [case.get("id") for case in cases]
    if (
        any(not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value) for value in ids)
        or len(set(ids)) != len(ids)
    ):
        raise LabError("데이터셋 ID가 중복되거나 안전한 파일 이름 형식이 아닙니다.")
    if limit is not None:
        if type(limit) is not int or limit < 1 or limit > len(cases):
            raise LabError(f"limit은 1~{len(cases)} 사이여야 합니다.")
        cases = cases[:limit]
    run_dir = safe_run_dir(run_id)
    if run_dir.exists() and not resume:
        raise LabError(f"{run_dir}이 이미 존재합니다. 원본 근거를 덮어쓰지 말고 새 run-id를 지정하세요.")
    if resume and not run_dir.exists():
        raise LabError("--resume requires the original run/checkpoint, not a new run-id.")
    agent = load_agent(config, stage)
    if stage != "baseline" and sha256_file(ROOT / "data/knowledge/documents.json") != agent["knowledge_sha256"]:
        raise LabError("에이전트 생성 후 지식 원본이 바뀌었습니다. 새 지식·에이전트 버전을 기록하세요.")
    metadata = {
        "run_id": run_id,
        "code": code_provenance(),
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
        "model_snapshot": agent["model_snapshot"],
        "execution_mode": "LIVE", "evaluation_contract_version": "atlas-evaluation-v1",
        "quality_status": "NOT_EVALUATED", "manual_operational_approval": "not_granted",
        "access_blockers": [],
    }
    if interval_seconds:
        metadata["parameters"]["interval_seconds"] = interval_seconds
    if dialogue:
        metadata["dialogue_diagnostic"] = True
        metadata["diagnostic_scope"] = "One authored multi-turn dev case; not part of the original 100 or independent real-world sample."
    if frozen:
        metadata.update(freeze_id=freeze_id, freeze_sha256=frozen["content_sha256"], holdout_id=holdout_id)
        metadata["sample_contract_sha256"] = frozen["hashes"]["sample_contract"]
    if resume:
        previous = read_json(run_dir / "metadata.json")
        if previous.get("code") and (
            previous["code"].get("python_sources_sha256") != metadata["code"]["python_sources_sha256"]
        ):
            raise LabError("실행 코드가 바뀌었습니다. 이전 캡처를 새 코드의 실험으로 재인증하지 않습니다.")
        if observed_model_drift(previous):
            raise LabError("Captured run has terminal observed model drift. Preserve its evidence; deployment restoration cannot resume or revalidate it.")
        contract_fields = (
            "run_id", "stage", "split", "source_split", "dataset_sha256", "row_ids", "project_endpoint",
            "agent_name", "agent_version", "workspace_id", "prompt_sha256", "knowledge_sha256",
            "model_deployment", "model_snapshot", "parameters", "freeze_id", "freeze_sha256", "holdout_id",
            "sample_contract_sha256",
            "dialogue_diagnostic",
        )
        if any(previous.get(key) != metadata.get(key) for key in contract_fields):
            raise LabError("Resume contract changed (candidate/data/parameters). Do not reuse or resubmit this run.")
        metadata = previous
        if metadata["status"] in {"completed", "completed_with_errors"}:
            if metadata.get("outputs_sha256") and sha256_file(run_dir / "outputs.jsonl") != metadata["outputs_sha256"]:
                raise LabError("Completed capture hash changed; do not rerun.")
            records = read_jsonl(run_dir / "outputs.jsonl")
            if [row["id"] for row in records] != metadata["row_ids"]:
                raise LabError("Completed capture is incomplete/corrupt; do not silently rerun.")
            for record in records:
                saved = read_json(run_dir / "raw" / f"{record['id']}.json")
                if saved != record:
                    raise LabError("Completed capture/raw checkpoint mismatch.")
            return metadata
        for case in cases:
            checkpoint = run_dir / "raw" / f"{case['id']}.json"
            if checkpoint.exists():
                record = read_json(checkpoint)
                if any(
                    turn.get("state") not in {"completed", "failed"} and not turn.get("response_id")
                    for turn in record.get("turns", [])
                ):
                    raise LabError("Unknown submission outcome has no response ID. Recover it before resume; no blind resubmission.")
    if frozen:
        bind_holdout_attempt(freeze_id, holdout_id, run_id, resume=resume)
    if not resume:
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise LabError("Concurrent capture directory exists; do not resubmit this run.") from exc
    save_json(run_dir / "metadata.json", metadata)
    records = []
    try:
        credential = credential_for(config)
    except Exception as exc:
        metadata.update(status="blocked_access", access_blockers=[f"{type(exc).__name__}: {exc}"])
        save_json(run_dir / "metadata.json", metadata)
        raise
    with credential as credential:
        try:
            before_model = model_snapshot(config, agent["model_deployment"])
        except Exception as exc:
            metadata.update(status="blocked_model_verification", execution_error=f"{type(exc).__name__}: {exc}")
            save_json(run_dir / "metadata.json", metadata)
            raise
        if before_model != agent.get("model_snapshot"):
            if resume and any((run_dir / "raw" / f"{case['id']}.json").exists() for case in cases):
                metadata.update(
                    status="invalid_model_drift", model_snapshot_after=before_model,
                    model_drift_detected=True, quality_status="HOLD",
                )
            else:
                metadata["status"] = "invalid_model_before_capture"
            save_json(run_dir / "metadata.json", metadata)
            raise LabError("에이전트 생성 후 모델 배포 구성이 바뀌었습니다. 같은 기반 버전으로 실험을 다시 고정하세요.")
        metadata["model_snapshot"] = before_model
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential, retry_total=0) as project:
            try:
                remote = project.agents.get_version(agent_name=agent["name"], agent_version=agent["version"])
            except Exception as exc:
                metadata.update(status="blocked_agent_verification", execution_error=f"{type(exc).__name__}: {exc}")
                if getattr(exc, "status_code", None) in {401, 403}:
                    metadata["access_blockers"].append(metadata["execution_error"])
                save_json(run_dir / "metadata.json", metadata)
                raise
            if remote.definition.model != agent["model_deployment"]:
                raise LabError("원격 에이전트 모델과 로컬 버전 기록이 다릅니다.")
            save_json(run_dir / "metadata.json", metadata)
            with project.get_openai_client(max_retries=0, timeout=120.0) as client:
                for index, case in enumerate(cases, start=1):
                    from lab.calibration import save_json as checkpoint_json
                    path = run_dir / "raw" / f"{case['id']}.json"
                    prior = read_json(path) if path.exists() else None
                    if index > 1 and prior is None and interval_seconds:
                        time.sleep(interval_seconds)
                    if metadata["access_blockers"] and prior is None:
                        record = {
                            "id": case["id"], "raw_output": "", "retrieved_context": "",
                            "error": "not_attempted_after_access_blocker", "state": "failed",
                            "usage": None, "latency_ms": None, "response_id": None, "response": None,
                            "turns": [], "manual_operational_approval": "not_granted",
                        }
                    else:
                        record = capture_case(
                            client, agent, case, resume_record=prior,
                            checkpoint=lambda value, path=path: checkpoint_json(path, value),
                            interval_seconds=interval_seconds,
                        )
                    records.append(record)
                    checkpoint_json(path, record)
                    write_jsonl(run_dir / "outputs.jsonl", records)
                    blockers = [
                        turn["error"] for turn in record.get("turns", []) if turn.get("access_blocker")
                    ]
                    metadata["access_blockers"].extend(blockers)
                    if record["state"] in {"unknown_outcome", "pending_response", "received", "submitting"}:
                        metadata["status"] = "blocked_unknown_outcome" if record["state"] != "pending_response" else "pending_response"
                        save_json(run_dir / "metadata.json", metadata)
                        return metadata
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
        metadata["model_drift_detected"] = True
        metadata["quality_status"] = "HOLD"
        save_json(run_dir / "metadata.json", metadata)
        raise LabError("실행 도중 모델 배포가 바뀌었습니다. 캡처는 보존했지만 비교 근거로 승인하지 않습니다.")
    metadata["status"] = final_status
    metadata["outputs_sha256"] = sha256_file(run_dir / "outputs.jsonl")
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
        "context_definition": "Authoritative policy reference, retained locally for business evaluation; never mapped to retrieval groundedness.",
        "retrieved_context_definition": "Actual MCP output when present. Empty means retrieval was not observed.",
        "warning": "Service errors remain failures in local scores. A managed-eval subset cannot grant a release pass.",
    })


def score_run(run_id: str) -> dict:
    from lab.evidence import observed_model_drift, score_row, summarize, write_report

    run_dir = safe_run_dir(run_id)
    metadata = read_json(run_dir / "metadata.json")
    if observed_model_drift(metadata):
        raise LabError("Cannot score an invalidated capture with observed model drift, even after deployment restoration.")
    if metadata.get("status") not in {"completed", "completed_with_errors"}:
        raise LabError("완료되지 않은 실행입니다. 부분 결과를 성공으로 요약하지 않습니다.")
    gates = None
    if metadata.get("freeze_id"):
        from lab.governance import validate_frozen_run
        gates = validate_frozen_run(metadata["freeze_id"], run_id)["gates"]
    dataset_path = dataset_for_metadata(metadata)
    if sha256_file(dataset_path) != metadata["dataset_sha256"]:
        raise LabError("실행 후 데이터셋이 변경되었습니다. 원본 데이터로 복구하거나 새 실행을 만드세요.")
    case_map = {case["id"]: case for case in read_jsonl(dataset_path)}
    records = read_jsonl(run_dir / "outputs.jsonl")
    if [r["id"] for r in records] != metadata["row_ids"]:
        raise LabError("실행의 행 목록과 응답 기록이 다릅니다.")
    if metadata.get("outputs_sha256") and sha256_file(run_dir / "outputs.jsonl") != metadata["outputs_sha256"]:
        raise LabError("Captured output hash changed after execution.")
    known_citations = {doc["id"] for doc in read_json(ROOT / "data/knowledge/documents.json")}
    judge_path = run_dir / "judge-scores.json"
    judge_scores = read_json(judge_path) if judge_path.exists() else {}
    if not isinstance(judge_scores, dict) or not judge_scores.keys() <= set(metadata["row_ids"]):
        raise LabError("Judge scores contain unknown case IDs; no positional or subset relabeling.")
    rows = [
        score_row(
            case_map[record["id"]], record["raw_output"],
            known_citations=known_citations, latency_ms=record.get("latency_ms"),
            usage=record.get("usage"), error=record["error"],
            judge=judge_scores.get(record["id"]),
            retrieved_context=record.get("retrieved_context", ""),
        )
        for record in records
    ]
    summary = summarize(rows, metadata=metadata)
    save_json(run_dir / "summary.json", summary)
    write_report(summary, run_dir / "report.md", gates=gates)
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
