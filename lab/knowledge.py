"""Real Foundry IQ: push index -> knowledge source -> knowledge base -> MCP."""

from azure.ai.projects.models import MCPTool

from lab.auth import credential_for
from lab.config import Config, LabError
from lab.files import ARTIFACTS, ROOT, read_json, record_created, sha256_file, workspace
from lab.http import ARM_SCOPE, SEARCH_SCOPE, CloudRequestError, JsonHttp
from lab.preflight import az_json, save_json


SEARCH_API = "2026-08-01-preview"
CONNECTION_API = "2025-10-01-preview"


def resource_names(config: Config, state: dict) -> dict:
    stem = f"{config.prefix}-{state['workspace_id'].replace('-', '')[:8]}"
    return {name: f"{stem}-{suffix}" for name, suffix in (
        ("index", "docs"), ("source", "source"), ("base", "kb"), ("connection", "mcp"),
    )}


def search_url(config: Config, resource: str, name: str, action: str = "") -> str:
    return f"{config.search_endpoint}/{resource}/{name}{action}?api-version={SEARCH_API}"


def knowledge_payloads(config: Config, names: dict, planner_model: str) -> dict:
    return {
        "index": {
            "name": names["index"],
            "fields": [
                {"name": "id", "type": "Edm.String", "key": True, "filterable": True, "retrievable": True},
                {"name": "title", "type": "Edm.String", "searchable": True, "retrievable": True, "analyzer": "ko.microsoft"},
                {"name": "content", "type": "Edm.String", "searchable": True, "retrievable": True, "analyzer": "ko.microsoft"},
                {"name": "effective_date", "type": "Edm.String", "filterable": True, "retrievable": True},
            ],
            "semantic": {
                "defaultConfiguration": "support-semantic",
                "configurations": [{
                    "name": "support-semantic",
                    "prioritizedFields": {
                        "titleField": {"fieldName": "title"},
                        "prioritizedContentFields": [{"fieldName": "content"}],
                    },
                }],
            },
        },
        "source": {
            "name": names["source"],
            "kind": "searchIndex",
            "searchIndexParameters": {
                "searchIndexName": names["index"],
                "semanticConfigurationName": "support-semantic",
                "sourceDataFields": [{"name": field} for field in ("id", "title", "content", "effective_date")],
            },
        },
        "base": {
            "name": names["base"],
            "description": "Synthetic Contoso policies. Stable ATLAS document IDs are in titles and source data.",
            "knowledgeSources": [{"name": names["source"]}],
            "models": [{
                "kind": "azureOpenAI",
                "azureOpenAIParameters": {
                    "resourceUri": config.openai_endpoint,
                    "deploymentId": config.planner,
                    "modelName": planner_model,
                },
            }],
            "retrievalReasoningEffort": {"kind": "low"},
            "outputMode": "extractiveData",
        },
        "connection": {
            "properties": {
                "authType": "ProjectManagedIdentity",
                "category": "RemoteTool",
                "target": search_url(config, "knowledgebases", names["base"], "/mcp"),
                "isSharedToAll": True,
                "audience": "https://search.azure.com/",
                "metadata": {"ApiType": "Azure"},
            },
        },
    }


def _ensure_created(config: Config, http: JsonHttp, kind: str, name: str, url: str, payload: dict) -> dict:
    state = workspace(config)
    owned = [item for item in state["created"] if item.get("kind") == kind and item.get("name") == name]
    try:
        existing = http.request("GET", url)
    except CloudRequestError as exc:
        if exc.status != 404:
            raise
        existing = None
    if existing is not None:
        if not owned:
            raise LabError(f"{name}이 이미 존재하지만 이 실습의 생성 기록이 없습니다. 덮어쓰지 않습니다.")
        return existing.body
    result = http.request("PUT", url, payload, create_only=True)
    if result.status not in {200, 201}:
        raise LabError(f"{name}: 비동기/예상 밖 상태 {result.status}. 완료로 기록하지 않습니다.")
    record_created(config, {"kind": kind, "name": name, "url": url, "etag": result.etag})
    return result.body


def prepare_knowledge(config: Config) -> dict:
    state = workspace(config, create=True)
    names = resource_names(config, state)
    documents_path = ROOT / "data/knowledge/documents.json"
    documents = read_json(documents_path)
    content_hash = sha256_file(documents_path)
    setup_path = ARTIFACTS / "knowledge/setup.json"
    if setup_path.exists():
        previous = read_json(setup_path)
        if previous.get("documents_sha256") != content_hash or previous.get("names") != names:
            raise LabError("기존 지식 준비와 원본/범위가 다릅니다. 다른 실험을 기존 인덱스에 덮어쓰지 않습니다.")
    with credential_for(config) as credential:
        planner = az_json([
            "cognitiveservices", "account", "deployment", "show",
            "--subscription", config.subscription_id, "--resource-group", config.resource_group,
            "--name", config.account, "--deployment-name", config.planner,
        ])
        model = planner.get("properties", {}).get("model", {})
        if not model.get("name"):
            raise LabError("IQ planner의 실제 모델 이름을 확인할 수 없습니다.")
        # This workshop's main lane was researched for gpt-5.5, not arbitrary
        # answer models that may be unsupported by the knowledge-base planner.
        if model["name"] != "gpt-5.5":
            raise LabError("이 경로의 IQ planner는 확인된 gpt-5.5 배포를 요구합니다. 다른 모델로 자동 전환하지 않습니다.")
        payloads = knowledge_payloads(config, names, model["name"])
        setup = {
            "status": "preparing", "workspace_id": state["workspace_id"], "names": names,
            "project_id": config.project_id, "documents_sha256": content_hash,
            "planner": {"deployment": config.planner, "model": model},
            "search_api_version": SEARCH_API,
            "retrieval": {"reasoning": "low", "output": "extractiveData", "embedding_model": None},
        }
        save_json(setup_path, setup)
        search = JsonHttp(credential, scope=SEARCH_SCOPE, allowed_origin=config.search_endpoint)
        index_url = search_url(config, "indexes", names["index"])
        _ensure_created(config, search, "search_index", names["index"], index_url, payloads["index"])
        uploaded = [{
            "@search.action": "mergeOrUpload",
            "id": doc["id"], "title": f"{doc['id']} | {doc['title']}",
            "content": f"[{doc['id']}]\n{doc['content']}",
            "effective_date": doc["effective_date"],
        } for doc in documents]
        upload = search.request(
            "POST", search_url(config, "indexes", names["index"], "/docs/index"), {"value": uploaded},
        )
        statuses = upload.body.get("value", [])
        if (
            len(statuses) != len(uploaded)
            or {item.get("key") for item in statuses} != {doc["id"] for doc in documents}
            or any(item.get("status") is not True for item in statuses)
        ):
            save_json(ARTIFACTS / "knowledge/upload-error.json", upload.body)
            raise LabError("일부 문서 업로드가 실패했습니다. knowledge/upload-error.json을 확인하세요.")
        _ensure_created(
            config, search, "knowledge_source", names["source"],
            search_url(config, "knowledgesources", names["source"]), payloads["source"],
        )
        _ensure_created(
            config, search, "knowledge_base", names["base"],
            search_url(config, "knowledgebases", names["base"]), payloads["base"],
        )
        connection_url = (
            f"https://management.azure.com{config.project_id}/connections/"
            f"{names['connection']}?api-version={CONNECTION_API}"
        )
        arm = JsonHttp(credential, scope=ARM_SCOPE, allowed_origin="https://management.azure.com")
        _ensure_created(config, arm, "project_connection", names["connection"], connection_url, payloads["connection"])
        setup["status"] = "created_not_retrieval_tested"
        setup["mcp_endpoint"] = payloads["connection"]["properties"]["target"]
        setup["connection_name"] = names["connection"]
        setup["uploaded_documents"] = len(uploaded)
        save_json(setup_path, setup)
        save_json(ARTIFACTS / "knowledge/documents-snapshot.json", documents)
        return setup


def load_knowledge(config: Config) -> dict:
    state = workspace(config)
    setup = read_json(ARTIFACTS / "knowledge/setup.json")
    if (
        setup.get("workspace_id") != state["workspace_id"]
        or setup.get("project_id") != config.project_id
        or setup.get("names") != resource_names(config, state)
        or setup.get("status") not in {"created_not_retrieval_tested", "retrieval_verified"}
    ):
        raise LabError("지식 베이스 준비 기록이 현재 실습 범위와 다르거나 아직 완료되지 않았습니다.")
    return setup


def probe_knowledge(config: Config, query: str) -> dict:
    setup = load_knowledge(config)
    if not query.strip():
        raise LabError("지식 검색 질문이 비어 있습니다.")
    names = setup["names"]
    with credential_for(config) as credential:
        http = JsonHttp(credential, scope=SEARCH_SCOPE, allowed_origin=config.search_endpoint)
        result = http.request(
            "POST", search_url(config, "knowledgebases", names["base"], "/retrieve"),
            {
                "messages": [{"role": "user", "content": [{"type": "text", "text": query}]}],
                "outputMode": "extractiveData",
                "maxOutputSize": 6000,
                "knowledgeSourceParams": [{
                    "knowledgeSourceName": names["source"], "kind": "searchIndex",
                    "includeReferences": True, "includeReferenceSourceData": True,
                    "resultsProcessing": "rerank", "failOnError": True,
                }],
            },
        )
    save_json(ARTIFACTS / "knowledge/retrieve-response.json", result.body)
    if not result.body.get("response") or not result.body.get("references") or not result.body.get("activity"):
        raise LabError("검색 응답·출처·활동 중 일부가 없습니다. retrieve-response.json을 확인하고 완료 처리하지 마세요.")
    setup["status"] = "retrieval_verified"
    setup["probe_scope"] = "Human CLI identity; deployed-agent managed identity must still be verified by an agent call."
    save_json(ARTIFACTS / "knowledge/setup.json", setup)
    return {"status": setup["status"], "references": result.body["references"], "activity": result.body["activity"], "scope": setup["probe_scope"]}


def knowledge_tool(config: Config) -> MCPTool:
    setup = load_knowledge(config)
    if setup["status"] != "retrieval_verified":
        raise LabError("먼저 python -m lab iq probe --confirm 으로 실제 검색을 확인하세요.")
    return MCPTool(
        server_label="contoso-knowledge",
        server_url=setup["mcp_endpoint"],
        server_description="Read-only Contoso Atlas Cloud policies. Cite stable ATLAS document IDs shown in the returned title/content, not numeric retrieval reference IDs.",
        allowed_tools=["knowledge_base_retrieve"],
        require_approval="never",
        project_connection_id=setup["connection_name"],
    )

