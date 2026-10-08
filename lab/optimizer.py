"""Import preserved portal output without inventing an optimizer API or job ID."""

from datetime import datetime, timezone
import difflib
import hashlib
from pathlib import Path

from lab.config import Config, LabError
from lab.content import content_path, language_metadata, require_content_language
from lab.files import ROOT, artifacts_dir, artifact_reference, read_json, read_jsonl, sha256_file, write_once_json


def collect_prompt(config: Config, request_path: Path, response_path: Path) -> dict:
    request, response = read_json(request_path), read_json(response_path)
    parameters = request.get("params", {})
    payload = parameters.get("payload", {})
    original, candidate = payload.get("developer_message"), response.get("new_developer_message")
    if (
        request.get("query") != "optimizePromptResolver"
        or parameters.get("resourceId", "").lower() != config.project_id.lower()
        or not isinstance(original, str) or not original.strip()
        or not isinstance(candidate, str) or not candidate.strip()
        or response.get("new_messages") not in (None, [])
        or not isinstance(response.get("comments"), list)
    ):
        raise LabError("현재 프로젝트의 실제 Prompt Optimizer 요청/응답 계약을 확인할 수 없습니다.")
    if original == candidate:
        raise LabError("최적화 응답의 원본과 후보가 같습니다. 개선 후보라고 등록하지 않습니다.")
    directory = artifacts_dir() / "prompt-optimizer"
    record = {
        **language_metadata(),
        "kind": "PROMPT_OPTIMIZER_PORTAL_RESPONSE_IMPORT",
        "status": "CANDIDATE_CAPTURED_NOT_EVALUATED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_endpoint": config.project_endpoint,
        "request_sha256": sha256_file(request_path), "response_sha256": sha256_file(response_path),
        "original_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
        "requested_changes": payload.get("requested_changes"),
        "service_comments": response["comments"],
        "model_deployment": payload.get("model_deployment_name"),
        "remote_job_id": None,
        "job_id_note": "This ephemeral Prompt Optimizer response exposes no persistent job ID. Do not fabricate one.",
        "service_identity_assurance": "External capture, verify portal account/project separately; local import is not an authentication proof.",
        "human_operational_approval": "NOT_GRANTED", "cost": {"status": "NOT_OBSERVED"},
        "candidate_path": artifact_reference(directory / "candidate.txt"),
    }
    manifest = directory / "result.json"
    if manifest.exists():
        previous = read_json(manifest)
        require_content_language(previous)
        if previous.get("response_sha256") == record["response_sha256"] and previous.get("request_sha256") == record["request_sha256"]:
            if sha256_file(directory / "candidate.txt") != previous["candidate_sha256"]:
                raise LabError("보존한 서비스 후보가 변경되었습니다.")
            return previous
        raise LabError("Prompt Optimizer 결과가 이미 있습니다. 원본 실험을 덮어쓰지 않습니다.")
    write_once_json(directory / "result-intent.json", record)
    for name, text in (
        ("original.txt", original), ("candidate.txt", candidate),
        ("changes.diff", "".join(difflib.unified_diff(original.splitlines(True), candidate.splitlines(True),
                                                    fromfile="original", tofile="service-candidate"))),
    ):
        with (directory / name).open("x", encoding="utf-8") as stream:
            stream.write(text)
    write_once_json(manifest, record)
    return record


def collect_agent(config: Config, result_path: Path, candidate_path: Path) -> dict:
    result, candidate = read_json(result_path), read_json(candidate_path)
    inputs = result.get("inputs", {})
    source = inputs.get("agent", {})
    options = inputs.get("options", {})
    prompt = candidate.get("system_prompt")
    directory = artifacts_dir() / "optimizer"
    handoff = read_json(directory / "handoff.json")
    require_content_language(handoff)
    if (
        result.get("status") != "succeeded" or not result.get("id")
        or source.get("agent_name") != handoff.get("agent_name")
        or source.get("agent_version") != handoff.get("agent_version")
        or candidate.get("agentName") != source.get("agent_name")
        or candidate.get("agentVersion") != source.get("agent_version")
        or options.get("target_attributes") != ["instruction"]
        or type(options.get("max_candidates")) is not int or not 1 <= options["max_candidates"] <= 2
        or not isinstance(prompt, str) or not prompt.strip()
        or candidate.get("skills") not in (None, []) or candidate.get("tools") not in (None, [])
    ):
        raise LabError("완료된 동일 원본 Agent의 instruction-only Optimizer 결과가 아닙니다.")
    original = options.get("optimization_config", {}).get("system_prompt", "")
    if hashlib.sha256(original.encode()).hexdigest() != handoff["input_prompt_sha256"]:
        raise LabError("Optimizer 원본 지시와 dev 기준선의 프롬프트 해시가 다릅니다.")
    best = result.get("result", {}).get("best")
    if not best or best not in result.get("result", {}).get("candidate_ids", []):
        raise LabError("실제 반환된 후보 ID가 없습니다.")
    record = {
        **language_metadata(),
        "kind": "AGENT_OPTIMIZER_PORTAL_CANDIDATE_IMPORT",
        "status": "CANDIDATE_CAPTURED_NOT_LAB_APPROVED",
        "job_id": result["id"], "candidate_id": best,
        "source_agent": source, "project_endpoint": config.project_endpoint,
        "result_sha256": sha256_file(result_path), "config_sha256": sha256_file(candidate_path),
        "original_prompt_sha256": handoff["input_prompt_sha256"],
        "candidate_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "service_progress": result.get("progress"), "service_token_usage": result.get("result", {}).get("token_usage"),
        "service_evaluators": inputs.get("evaluators"),
        "imported_fields": ["system_prompt"],
        "mcp_connection": "Preserved by lab agent creation; the optimizer's empty function-tools export does not replace MCP.",
        "model": "Existing deployment preserved; model comparison was not selected.",
        "warning": "Candidate embeds dev-derived policy examples. Service score improvement is not independent holdout or human approval.",
        "human_operational_approval": "NOT_GRANTED",
    }
    write_once_json(directory / "selected-candidate.json", record)
    with (directory / "selected-prompt.txt").open("x", encoding="utf-8") as stream:
        stream.write(prompt)
    with (directory / "agent-changes.diff").open("x", encoding="utf-8") as stream:
        stream.write("".join(difflib.unified_diff(original.splitlines(True), prompt.splitlines(True),
                                               fromfile="iq-baseline", tofile="agent-optimizer-candidate")))
    return record


def native_answer(messages: list[dict]) -> str:
    import json

    texts = []
    for message in messages:
        if message.get("role") != "assistant":
            continue
        content = message.get("content")
        if not isinstance(content, str):
            raise LabError("Native assistant message content must be a recorded string.")
        try:
            parts = json.loads(content)
        except json.JSONDecodeError:
            texts.append(content)
            continue
        if isinstance(parts, list) and all(isinstance(part, dict) and "type" in part for part in parts):
            for part in parts:
                if part["type"] == "output_text":
                    if not isinstance(part.get("text"), str):
                        raise LabError("Native output_text part has no text.")
                    texts.append(part["text"])
                elif part["type"] == "tool_call":
                    if part.get("name") != "knowledge_base_retrieve" or not part.get("tool_call_id"):
                        raise LabError("Native run used an unexpected tool; do not discard its action evidence.")
                elif part["type"] not in {"mcp_call", "mcp_list_tools", "function_call", "reasoning"}:
                    raise LabError("Unknown native assistant part; do not silently discard it.")
        else:
            texts.append(content)
    if not texts:
        raise LabError("Native run exposes no assistant answer text.")
    return "\n".join(texts)


def check_native_pair(baseline_items: Path, candidate_items: Path) -> dict:
    from lab.evidence import score_row, summarize

    cases = read_jsonl(content_path(ROOT, "data/splits/dev.jsonl"))
    agent = read_json(artifacts_dir() / "agents/iq.json")
    selected = read_json(artifacts_dir() / "optimizer/selected-candidate.json")
    require_content_language(agent)
    require_content_language(selected)
    by_query = {case["query"]: case for case in cases}
    known = {document["id"] for document in read_json(content_path(ROOT, "data/knowledge/documents.json"))}
    result = {
        **language_metadata(),
        "kind": "OFFLINE_CHECK_OF_ACTUAL_NATIVE_OPTIMIZER_RESPONSES",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "new_model_calls": 0, "dataset_sha256": sha256_file(content_path(ROOT, "data/splits/dev.jsonl")),
        "human_operational_approval": "NOT_GRANTED", "arms": {},
    }
    for arm, path in (("baseline", baseline_items), ("candidate", candidate_items)):
        items = read_json(path)["items"]
        if len(items) != len(cases):
            raise LabError("Native pair must contain every original dev case, including failures.")
        if len({(item.get("eval_id"), item.get("run_id")) for item in items}) != 1:
            raise LabError("Native items contain mixed evaluation/run identities.")
        scored, response_records = {}, []
        for item in items:
            source = item.get("datasource_item", {})
            query = source.get("query")
            if query not in by_query or by_query[query]["id"] in scored:
                raise LabError("Native output has an unknown or duplicate query; positional merging is forbidden.")
            case = by_query[query]
            sample = item.get("sample") or {}
            user_inputs = [message.get("content") for message in sample.get("input", []) if message.get("role") == "user"]
            if user_inputs != [query]:
                raise LabError("Native Agent input is not exactly the unlabeled original query.")
            raw = native_answer(sample.get("output", []))
            error = sample.get("error") or item.get("error")
            if item.get("status") not in {"completed", "pass", "fail"}:
                error = error or "Native item is not complete."
            scored[case["id"]] = score_row(case, raw, known_citations=known, error=str(error) if error else None)
            response_records.append({
                "case_id": case["id"], "service_item_id": item["id"], "eval_run_id": item["run_id"],
                "raw_answer_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "query_only_input_verified": True,
            })
        if set(scored) != {case["id"] for case in cases}:
            raise LabError("Native pair has missing case IDs.")
        summary = summarize([scored[case["id"]] for case in cases], metadata={
            "source_split": "dev", "split": "dev", "run_id": f"native-optimizer-{arm}", "status": "completed",
            "stage": "iq" if arm == "baseline" else "optimized",
            "dataset_sha256": result["dataset_sha256"],
            "knowledge_sha256": agent["knowledge_sha256"], "model_deployment": agent["model_deployment"],
            "prompt_sha256": agent["prompt_sha256"] if arm == "baseline" else selected["candidate_prompt_sha256"],
            "judge": None,
        })
        result["arms"][arm] = {
            "source_sha256": sha256_file(path), "sample_count": len(cases),
            "metrics": summary["metrics"], "response_mapping": response_records,
        }
    result["interpretation"] = "Same original dev questions and deterministic lab rules; not a fresh holdout, calibrated semantic pass, or operational approval."
    write_once_json(artifacts_dir() / "optimizer/native-rule-comparison.json", result)
    return result
