"""Delete only recorded, scope-checked lab objects; never delete shared resources."""

import re

from azure.ai.projects import AIProjectClient
from azure.core.exceptions import ResourceNotFoundError
from openai import NotFoundError

from lab.auth import credential_for
from lab.config import Config, LabError
from lab.files import ARTIFACTS, read_json, read_jsonl, workspace
from lab.http import ARM_SCOPE, SEARCH_SCOPE, CloudRequestError, JsonHttp
from lab.knowledge import CONNECTION_API, resource_names, search_url
from lab.preflight import save_json


def cleanup_plan(config: Config) -> dict:
    state = workspace(config)
    names = resource_names(config, state)
    allowed = {
        "search_index": (names["index"], search_url(config, "indexes", names["index"])),
        "knowledge_source": (names["source"], search_url(config, "knowledgesources", names["source"])),
        "knowledge_base": (names["base"], search_url(config, "knowledgebases", names["base"])),
        "project_connection": (
            names["connection"],
            f"https://management.azure.com{config.project_id}/connections/{names['connection']}?api-version={CONNECTION_API}",
        ),
    }
    allowed_agents = {config.agent_name(stage) for stage in ("baseline", "iq", "optimized", "tuned")}
    actions = []
    for record in state["created"]:
        kind = record.get("kind")
        if kind == "agent_version":
            if record.get("name") not in allowed_agents or not re.fullmatch(r"[A-Za-z0-9_-]+", str(record.get("version", ""))):
                raise LabError("정리 기록의 에이전트 범위가 다릅니다. 삭제하지 않습니다.")
        elif kind in allowed:
            if (record.get("name"), record.get("url")) != allowed[kind]:
                raise LabError("정리 기록의 Search/프로젝트 범위가 다릅니다. 삭제하지 않습니다.")
        else:
            raise LabError(f"자동 정리를 지원하지 않는 기록 유형: {kind}")
        actions.append(dict(record))
    for metadata_path in (ARTIFACTS / "runs").glob("*/metadata.json"):
        metadata = read_json(metadata_path)
        if metadata.get("workspace_id") != state["workspace_id"]:
            continue
        if metadata.get("project_endpoint") != config.project_endpoint:
            raise LabError("응답 정리 대상의 프로젝트 endpoint가 다릅니다.")
        outputs_path = metadata_path.parent / "outputs.jsonl"
        if not outputs_path.exists():
            continue
        for row in read_jsonl(outputs_path):
            identifier = row.get("response_id")
            if identifier:
                if not re.fullmatch(r"resp_[A-Za-z0-9_-]+", identifier):
                    raise LabError("알 수 없는 response ID 형식입니다. 자동 삭제하지 않습니다.")
                actions.append({"kind": "response", "id": identifier})
    order = {"response": 0, "agent_version": 1, "project_connection": 2, "knowledge_base": 3, "knowledge_source": 4, "search_index": 5}
    actions.sort(key=lambda action: order[action["kind"]])
    return {
        "mode": "LOCAL_PLAN_ONLY",
        "project_id": config.project_id,
        "prefix": config.prefix,
        "workspace_id": state["workspace_id"],
        "actions": actions,
        "never_deleted": [
            "resource group", "Foundry account/project", "shared model deployments",
            "Search service", "Application Insights/Log Analytics", "RBAC assignments",
        ],
        "manual_follow_up": [
            "Managed evaluation jobs/files are retained for evidence; inspect recorded IDs and remove in the portal if required.",
            "SFT/FDE training jobs, uploaded training files and model deployments require their own scoped cleanup.",
            "An empty stable agent entry may remain after deleting its recorded versions; inspect ownership before removing it in the portal.",
        ],
    }


def cleanup(config: Config, *, confirm_prefix: str | None = None) -> dict:
    plan = cleanup_plan(config)
    if confirm_prefix is None:
        return plan
    if confirm_prefix != config.prefix:
        raise LabError("--confirm-prefix가 현재 LAB_PREFIX와 다릅니다. 삭제하지 않았습니다.")
    with credential_for(config) as credential:
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential) as project:
            with project.get_openai_client(max_retries=0, timeout=60.0) as client:
                search = JsonHttp(credential, scope=SEARCH_SCOPE, allowed_origin=config.search_endpoint)
                arm = JsonHttp(credential, scope=ARM_SCOPE, allowed_origin="https://management.azure.com")
                inspected = []
                for action in plan["actions"]:
                    item = {**action, "exists": True}
                    kind = action["kind"]
                    if kind == "agent_version":
                        try:
                            remote = project.agents.get_version(agent_name=action["name"], agent_version=action["version"])
                        except ResourceNotFoundError:
                            item["exists"] = False
                        else:
                            if (remote.metadata or {}).get("workspace") != plan["workspace_id"]:
                                raise LabError("원격 에이전트 소유 표식이 다릅니다. 아무 대상도 삭제하지 않았습니다.")
                    elif kind == "response":
                        try:
                            response = client.responses.retrieve(action["id"])
                        except NotFoundError:
                            item["exists"] = False
                        else:
                            if (response.metadata or {}).get("lab_workspace") != plan["workspace_id"]:
                                raise LabError("원격 응답 소유 표식이 다릅니다. 아무 대상도 삭제하지 않았습니다.")
                    else:
                        transport = arm if kind == "project_connection" else search
                        try:
                            remote = transport.request("GET", action["url"])
                        except CloudRequestError as exc:
                            if exc.status != 404:
                                raise
                            item["exists"] = False
                        else:
                            if action.get("etag") and remote.etag and action["etag"] != remote.etag:
                                raise LabError("생성 후 원격 리소스 구성이 변경되었습니다. 정리 대상을 직접 검토하세요.")
                            item["current_etag"] = remote.etag
                    inspected.append(item)
                completed = []
                for action in inspected:
                    if not action["exists"]:
                        completed.append({**action, "result": "already_absent"})
                        continue
                    kind = action["kind"]
                    if kind == "response":
                        client.responses.delete(action["id"])
                    elif kind == "agent_version":
                        project.agents.delete_version(agent_name=action["name"], agent_version=action["version"])
                    else:
                        transport = arm if kind == "project_connection" else search
                        transport.request("DELETE", action["url"], etag=action.get("current_etag"))
                    completed.append({**action, "result": "delete_request_succeeded"})
                    save_json(ARTIFACTS / "cleanup.json", {**plan, "mode": "DELETING", "completed": completed})
                remaining = []
                for action in inspected:
                    kind = action["kind"]
                    if kind == "response":
                        try:
                            client.responses.retrieve(action["id"])
                        except NotFoundError:
                            continue
                    elif kind == "agent_version":
                        try:
                            project.agents.get_version(agent_name=action["name"], agent_version=action["version"])
                        except ResourceNotFoundError:
                            continue
                    else:
                        transport = arm if kind == "project_connection" else search
                        try:
                            transport.request("GET", action["url"])
                        except CloudRequestError as exc:
                            if exc.status == 404:
                                continue
                            raise
                    remaining.append(action)
    result = {
        **plan,
        "mode": "OWNED_OBJECTS_ABSENT" if not remaining else "DELETION_PENDING",
        "completed": completed,
        "remaining": remaining,
    }
    save_json(ARTIFACTS / "cleanup.json", result)
    return result
