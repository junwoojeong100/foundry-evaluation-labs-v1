"""Read actual traces for this lab's responses; an empty table is not a clean bill of health."""

from datetime import datetime, timezone
import json
import re
from uuid import UUID

from lab.config import Config, LabError
from lab.files import read_json, read_jsonl, safe_run_dir
from lab.preflight import az_json, check_identity, save_json


def trace_query(response_ids: list[str], agent_name: str, agent_version: str) -> str:
    if not response_ids or any(not re.fullmatch(r"[A-Za-z0-9_.:-]{1,180}", value) for value in response_ids):
        raise LabError("실제로 반환된 response ID가 필요합니다.")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", agent_name) or not re.fullmatch(r"[A-Za-z0-9_.-]+", agent_version):
        raise LabError("기록된 에이전트 이름과 고정 버전이 필요합니다.")
    ids = json.dumps(response_ids, ensure_ascii=True)
    return f"""// Recorded agent: {agent_name}:{agent_version}. Anchor only to this run's response IDs.
let wanted = dynamic({ids});
let matching = materialize(
    union dependencies, requests
    | where timestamp > ago(24h)
    | extend responseId = tostring(customDimensions["gen_ai.response.id"])
    | where responseId in (wanted)
    | where isnotempty(operation_Id)
    | distinct operation_Id
);
union withsource=source dependencies, requests, customEvents, traces
| where timestamp > ago(24h)
| extend responseId = tostring(customDimensions["gen_ai.response.id"]),
         operation = tostring(customDimensions["gen_ai.operation.name"]),
         evaluation = tostring(customDimensions["gen_ai.evaluation.name"]),
         tool = tostring(customDimensions["gen_ai.tool.name"]),
         model = tostring(customDimensions["gen_ai.request.model"])
| where operation_Id in (matching) or responseId in (wanted)
| project timestamp, source, operation_Id, operation_ParentId, responseId, operation,
          evaluation, tool, model, customDimensions
| order by timestamp asc
| take 500"""


def classify_trace_result(payload: dict, expected_response_ids: list[str]) -> dict:
    if not expected_response_ids:
        raise LabError("관측 판정에는 현재 실행의 response ID 집합이 필요합니다.")
    tables = payload.get("tables")
    if not isinstance(tables, list):
        raise LabError("관측 API의 tables 응답이 없습니다.")
    rows = []
    for table in tables:
        columns = [column["name"] for column in table.get("columns", [])]
        for values in table.get("rows", []):
            if len(values) != len(columns):
                raise LabError("관측 API 행과 열 개수가 다릅니다.")
            rows.append(dict(zip(columns, values, strict=True)))
    coverage = {}
    relevant_operations = set()
    for response_id in expected_response_ids:
        trace_ids = {row["operation_Id"] for row in rows
                     if row.get("responseId") == response_id and row.get("operation_Id")
                     and row.get("source") in {"dependencies", "requests"}}
        related = [row for row in rows if row.get("operation_Id") in trace_ids]
        relevant_operations.update(trace_ids)
        coverage[response_id] = {
            "trace_ids": sorted(trace_ids),
            "model_linked": any(row.get("source") == "dependencies" and
                                (row.get("model") or row.get("operation") == "chat") for row in related),
            "tool_linked": any(row.get("source") == "dependencies" and
                               (row.get("tool") or row.get("operation") == "execute_tool") for row in related),
            "evaluation_linked": any(row.get("source") == "customEvents" and
                                     row.get("responseId") == response_id and row.get("evaluation") for row in rows),
        }
    relevant = [row for row in rows if row.get("operation_Id") in relevant_operations
                or row.get("responseId") in expected_response_ids]
    operations = sorted({row.get("operation") for row in relevant if row.get("operation")})
    tools = sum(bool(row.get("tool")) or row.get("operation") == "execute_tool" for row in relevant)
    evaluations = sum(bool(row.get("evaluation")) and row.get("responseId") in expected_response_ids for row in relevant)
    models = sum(bool(row.get("model")) or row.get("operation") == "chat" for row in relevant)
    complete = all(item["trace_ids"] and item["model_linked"] and item["tool_linked"] and item["evaluation_linked"]
                   for item in coverage.values())
    return {
        "status": "VERIFIED_TRACE_MODEL_TOOL_EVAL_LINKS" if complete else "PARTIAL" if relevant else "NOT_VERIFIED_NO_TRACES",
        "observed_rows": len(relevant), "unrelated_rows_excluded": len(rows) - len(relevant), "operations": operations,
        "expected_responses": len(expected_response_ids), "response_coverage": coverage,
        "model_rows": models, "tool_rows": tools, "evaluation_rows": evaluations,
        "error_absence_claim": False,
        "policy_enforcement": "NOT_APPLIED_OR_VERIFIED_BY_THIS_READ_ONLY_QUERY",
        "human_operational_approval": "PENDING",
        "cost": {"status": "NOT_OBSERVED"},
        "resume": "Allow ingestion delay, then query this same resource and recorded response IDs. Empty results do not prove success or absence of errors.",
    }


def collect(config: Config, run_id: str, insights_resource_id: str) -> dict:
    prefix = (
        f"/subscriptions/{config.subscription_id}/resourceGroups/{config.resource_group}"
        "/providers/Microsoft.Insights/components/"
    )
    if not insights_resource_id.lower().startswith(prefix.lower()) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+", insights_resource_id[len(prefix):],
    ):
        raise LabError("현재 새 실습 RG의 Application Insights만 조회할 수 있습니다.")
    directory = safe_run_dir(run_id)
    metadata = read_json(directory / "metadata.json")
    if metadata.get("project_endpoint") != config.project_endpoint or metadata.get("target_type") == "model":
        raise LabError("현재 Foundry 프로젝트의 실제 에이전트 실행만 관측할 수 있습니다.")
    outputs = read_jsonl(directory / "outputs.jsonl")
    response_ids = sorted({row["response_id"] for row in outputs if row.get("response_id")})
    query = trace_query(response_ids, metadata.get("agent_name", ""), str(metadata.get("agent_version", "")))
    check_identity(config)
    resource = az_json(["resource", "show", "--ids", insights_resource_id, "--api-version", "2020-02-02",
                        "--subscription", config.subscription_id])
    app_id = resource.get("properties", {}).get("AppId", "")
    try:
        UUID(app_id)
    except (ValueError, TypeError) as exc:
        raise LabError("조회 대상 Application Insights의 실제 AppId를 확인하지 못했습니다.") from exc
    print(f"```kql\n{query}\n```", flush=True)
    payload = az_json([
        "rest", "--method", "post", "--url", f"https://api.applicationinsights.io/v1/apps/{app_id}/query",
        "--resource", "https://api.applicationinsights.io/",
        "--subscription", config.subscription_id, "--body", json.dumps({"query": query, "timespan": "P1D"}),
    ])
    result = classify_trace_result(payload, response_ids)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    observation = {
        "kind": "LIVE_READ_ONLY_CONTROL_PLANE_QUERY", "checked_at": stamp,
        "run_id": run_id, "application_insights_resource_id": insights_resource_id,
        "response_ids": response_ids, "query": query, "response": payload, **result,
    }
    save_json(directory / "control-plane" / f"{stamp}.json", observation)
    return observation
