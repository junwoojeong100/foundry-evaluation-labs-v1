"""Real Foundry IQ: push index -> knowledge source -> knowledge base -> MCP."""

from datetime import datetime, timezone
import hashlib
import json

from azure.ai.projects.models import MCPTool

from lab.auth import credential_for
from lab.config import Config, LabError
from lab.content import content_path, language_metadata, require_content_language
from lab.embeddings import DIMENSIONS, embed, validate_vectors
from lab.files import ARTIFACTS, ROOT, read_json, record_created, sha256_file, workspace, write_once_json
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
    if not config.embedding:
        raise LabError("벡터 검색을 위해 EMBEDDING_DEPLOYMENT를 명시하세요.")
    return {
        "index": {
            "name": names["index"],
            "fields": [
                {"name": "id", "type": "Edm.String", "key": True, "filterable": True, "retrievable": True},
                {"name": "title", "type": "Edm.String", "searchable": True, "retrievable": True, "analyzer": "ko.microsoft"},
                {"name": "content", "type": "Edm.String", "searchable": True, "retrievable": True, "analyzer": "ko.microsoft"},
                {"name": "effective_date", "type": "Edm.String", "filterable": True, "retrievable": True},
                {"name": "content_vector", "type": "Collection(Edm.Single)", "searchable": True,
                 "retrievable": False, "dimensions": DIMENSIONS, "vectorSearchProfile": "contoso-vector"},
            ],
            "vectorSearch": {
                "algorithms": [{"name": "contoso-hnsw", "kind": "hnsw", "hnswParameters": {"metric": "cosine"}}],
                "profiles": [{"name": "contoso-vector", "algorithm": "contoso-hnsw", "vectorizer": "contoso-embedding"}],
                "vectorizers": [{
                    "name": "contoso-embedding", "kind": "azureOpenAI",
                    "azureOpenAIParameters": {
                        "resourceUri": config.openai_endpoint, "deploymentId": config.embedding,
                        "modelName": "text-embedding-3-small",
                    },
                }],
            },
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
                "searchFields": [{"name": field} for field in ("title", "content", "content_vector")],
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
                "isSharedToAll": False,
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
    documents_path = content_path(ROOT, "data/knowledge/documents.json")
    documents = read_json(documents_path)
    content_hash = sha256_file(documents_path)
    setup_path = ARTIFACTS / "knowledge/setup.json"
    previous = None
    if setup_path.exists():
        previous = read_json(setup_path)
        require_content_language(previous)
        if previous.get("documents_sha256") != content_hash or previous.get("names") != names:
            raise LabError("기존 지식 준비와 원본/범위가 다릅니다. 다른 실험을 기존 인덱스에 덮어쓰지 않습니다.")
        if previous.get("status") in {"created_not_retrieval_tested", "retrieval_verified"}:
            if previous.get("retrieval", {}).get("embedding_deployment") != config.embedding:
                raise LabError("준비된 인덱스의 embedding 계약이 다릅니다. 새 실험을 생성하세요.")
            return previous
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
        payload_hash = hashlib.sha256(json.dumps(payloads, sort_keys=True).encode()).hexdigest()
        if previous and previous.get("payload_sha256") != payload_hash:
            raise LabError("미완료 검색 설정의 구성 계약이 바뀌었습니다. 같은 인덱스에 덮어쓰지 않습니다.")
        setup = {
            **language_metadata(),
            "status": "preparing", "workspace_id": state["workspace_id"], "names": names,
            "project_id": config.project_id, "documents_sha256": content_hash,
            "planner": {"deployment": config.planner, "model": model},
            "search_api_version": SEARCH_API,
            "payload_sha256": payload_hash,
            "retrieval": {
                "reasoning": "low", "output": "extractiveData",
                "embedding_model": "text-embedding-3-small", "embedding_deployment": config.embedding,
                "dimensions": DIMENSIONS, "index_algorithm": "hnsw", "metric": "cosine",
                "query_modes": ["vector", "hybrid", "agentic-iq-mcp"],
                "direct_probe_is_agent_evidence": False,
            },
        }
        save_json(setup_path, setup)
        save_json(ARTIFACTS / "knowledge/config-snapshot.json", payloads)
        search = JsonHttp(credential, scope=SEARCH_SCOPE, allowed_origin=config.search_endpoint)
        index_url = search_url(config, "indexes", names["index"])
        _ensure_created(config, search, "search_index", names["index"], index_url, payloads["index"])
        embedding = embed(
            config, [f"{doc['title']}\n{doc['content']}" for doc in documents],
            ARTIFACTS / "knowledge/document-embeddings.json",
        )
        vectors = validate_vectors(embedding["response"], len(documents))
        uploaded = [{
            "@search.action": "mergeOrUpload",
            "id": doc["id"], "title": f"{doc['id']} | {doc['title']}",
            "content": f"[{doc['id']}]\n{doc['content']}",
            "effective_date": doc["effective_date"],
            "content_vector": vector,
        } for doc, vector in zip(documents, vectors, strict=True)]
        upload_path = ARTIFACTS / "knowledge/upload-response.json"
        upload_contract = {"documents_sha256": content_hash, "payload_sha256": payload_hash,
                           "embedding_sha256": sha256_file(ARTIFACTS / "knowledge/document-embeddings.json")}
        if upload_path.exists():
            upload_record = read_json(upload_path)
            if upload_record.get("contract") != upload_contract or upload_record.get("status") != "completed":
                raise LabError("업로드 계약 변경 또는 결과 불명입니다. 업로드를 반복하지 말고 실제 인덱스 상태를 확인하세요.")
            upload_body = upload_record["response"]
        else:
            write_once_json(upload_path, {"status": "submitting", "contract": upload_contract})
            upload = search.request(
                "POST", search_url(config, "indexes", names["index"], "/docs/index"), {"value": uploaded},
            )
            upload_body = upload.body
            save_json(upload_path, {"status": "response_received", "contract": upload_contract, "response": upload_body})
        statuses = upload_body.get("value", [])
        if (
            len(statuses) != len(uploaded)
            or {item.get("key") for item in statuses} != {doc["id"] for doc in documents}
            or any(item.get("status") is not True for item in statuses)
        ):
            save_json(ARTIFACTS / "knowledge/upload-error.json", upload_body)
            raise LabError("일부 문서 업로드가 실패했습니다. knowledge/upload-error.json을 확인하세요.")
        save_json(upload_path, {"status": "completed", "contract": upload_contract, "response": upload_body})
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
        setup["embedding_usage"] = embedding["response"].get("usage")
        save_json(setup_path, setup)
        save_json(ARTIFACTS / "knowledge/documents-snapshot.json", documents)
        return setup


def load_knowledge(config: Config) -> dict:
    state = workspace(config)
    setup = read_json(ARTIFACTS / "knowledge/setup.json")
    require_content_language(setup)
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
    request = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": query}]}],
        "outputMode": "extractiveData",
        "maxOutputSize": 6000,
        "knowledgeSourceParams": [{
            "knowledgeSourceName": names["source"], "kind": "searchIndex",
            "includeReferences": True, "includeReferenceSourceData": True,
            "resultsProcessing": "rerank", "failOnError": True,
        }],
    }
    key = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
    directory = ARTIFACTS / "knowledge/probes" / key
    intent_path, response_path = directory / "iq-request.json", directory / "iq-response.json"
    if response_path.exists():
        if read_json(intent_path) != request:
            raise LabError("기존 IQ 요청 계약이 다릅니다. 원본 기록을 보존하세요.")
        body = read_json(response_path)
    else:
        if intent_path.exists():
            raise LabError("이 IQ probe는 결과 불명입니다. planner를 다시 유료 호출하지 말고 원격 요청을 확인하세요.")
        write_once_json(intent_path, request)
        with credential_for(config) as credential:
            http = JsonHttp(credential, scope=SEARCH_SCOPE, allowed_origin=config.search_endpoint)
            result = http.request(
                "POST", search_url(config, "knowledgebases", names["base"], "/retrieve"), request,
            )
        body = result.body
        save_json(response_path, body)
    if not (ARTIFACTS / "knowledge/retrieve-response.json").exists():
        save_json(ARTIFACTS / "knowledge/retrieve-response.json", body)
    if not body.get("response") or not body.get("references") or not body.get("activity"):
        raise LabError("검색 응답·출처·활동 중 일부가 없습니다. 보존한 iq-response.json을 확인하고 완료 처리하지 마세요.")
    setup["status"] = "retrieval_verified"
    setup["probe_scope"] = "Human CLI identity; deployed-agent managed identity must still be verified by an agent call."
    save_json(ARTIFACTS / "knowledge/setup.json", setup)
    return {"status": setup["status"], "references": body["references"], "activity": body["activity"], "scope": setup["probe_scope"]}


def probe_vectors(config: Config, query: str) -> dict:
    """Diagnostic probes are not evidence that these documents reached an agent."""
    setup = load_knowledge(config)
    if not query.strip():
        raise LabError("벡터 검색 질문이 비어 있습니다.")
    probe_key = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
    directory = ARTIFACTS / "knowledge/probes" / probe_key
    result_path = directory / "result.json"
    if result_path.exists():
        return read_json(result_path)
    embedding = embed(config, [query], directory / "query-embedding.json")
    vector = validate_vectors(embedding["response"], 1)[0]
    result = {
        "kind": "LIVE_SEARCH_DIAGNOSTIC_NOT_AGENT_CONTEXT",
        "query": query, "checked_at": datetime.now(timezone.utc).isoformat(),
        "index": setup["names"]["index"], "modes": {}, "cost": {"status": "NOT_OBSERVED"},
    }
    with credential_for(config) as credential:
        http = JsonHttp(credential, scope=SEARCH_SCOPE, allowed_origin=config.search_endpoint)
        for mode in ("vector", "hybrid"):
            request = {
                "vectorQueries": [{"kind": "vector", "vector": vector, "fields": "content_vector", "k": 5}],
                "select": "id,title,content,effective_date", "top": 5,
            }
            if mode == "hybrid":
                request["search"] = query
            path = directory / f"{mode}.json"
            if path.exists():
                response = read_json(path)
            else:
                intent_path = directory / f"{mode}-request.json"
                if intent_path.exists():
                    raise LabError(f"{mode} probe의 결과가 불명입니다. 같은 유료 요청을 자동 반복하지 않습니다.")
                write_once_json(intent_path, request)
                response = http.request(
                    "POST", search_url(config, "indexes", setup["names"]["index"], "/docs/search"), request,
                ).body
                save_json(path, response)
            hits = response.get("value")
            if not isinstance(hits, list) or not hits or any(not hit.get("id") or not hit.get("content") for hit in hits):
                raise LabError(f"{mode} 검색에 실제 문서/내용이 없습니다. 빈 화면을 성공으로 처리하지 않습니다.")
            result["modes"][mode] = {"count": len(hits), "ids": [hit["id"] for hit in hits],
                                     "scores": [hit.get("@search.score") for hit in hits]}
    result["status"] = "VERIFIED_VECTOR_AND_HYBRID_ONLY"
    save_json(result_path, result)
    return result


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
