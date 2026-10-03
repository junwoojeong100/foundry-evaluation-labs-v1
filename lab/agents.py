"""Create immutable prompt-agent candidates; never invoke a mutable latest version."""

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import time

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.core.exceptions import ResourceNotFoundError

from lab.auth import credential_for
from lab.config import Config, LabError
from lab.content import content_path, language_metadata, require_content_language
from lab.files import ARTIFACTS, ROOT, artifact_reference, code_provenance, read_json, record_created, safe_run_dir, sha256_file, workspace, write_once_json
from lab.preflight import model_snapshot, save_json


def native_response_format() -> dict:
    contract = read_json(ROOT / "schemas/response.schema.json")
    schema = {
        key: deepcopy(contract[key])
        for key in ("type", "additionalProperties", "required", "properties")
    }
    # Routing conditions and citation uniqueness remain validation requirements;
    # the model's structured-output subset does not support allOf/uniqueItems.
    schema["properties"]["citations"].pop("uniqueItems")
    schema["properties"]["route"]["type"] = "string"
    return {"format": {
        "type": "json_schema", "name": "contoso_support_response", "strict": True,
        "schema": schema,
    }}


def ensure_fixed_release(project: AIProjectClient, *, project_endpoint: str, agent_name: str,
                         version: str, definition: dict, receipt: Path,
                         workspace_id: str | None = None) -> dict:
    if version not in {"1", "2"}:
        raise LabError("This workshop permits only released v1 and v2; use drafts for experiments.")
    if definition.get("kind") != "prompt" or not isinstance(definition.get("instructions"), str) or not definition["instructions"].strip():
        raise LabError("A nonempty prompt-agent definition is required.")
    intent = {
        "project_endpoint": project_endpoint, "agent_name": agent_name, "version": version,
        "definition_sha256": hashlib.sha256(
            json.dumps(definition, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
    if workspace_id is not None:
        intent["workspace_id"] = workspace_id
    previous = read_json(receipt) if receipt.exists() else None
    if previous is not None and previous["intent"] != intent:
        raise LabError("The fixed-version receipt belongs to a different definition or environment.")
    try:
        existing = project.agents.get_version(agent_name=agent_name, agent_version=version).as_dict()
    except ResourceNotFoundError:
        existing = None
    if existing is not None:
        if workspace_id is not None and (existing.get("metadata") or {}).get("workspace") != workspace_id:
            raise LabError("The existing Agent version belongs to a different workspace; no changes were made.")
        if existing["definition"] != definition:
            raise LabError("The released version is immutable and differs from this source; no new version was created.")
        record = {"intent": intent, "status": "verified", "agent": existing}
        if previous is None:
            write_once_json(receipt, record)
        else:
            save_json(receipt, record)
        return record
    if previous is not None:
        raise LabError("The creation outcome is unknown; inspect the receipt and remote state, do not resubmit.")
    try:
        releases = [
            item.as_dict() for item in project.agents.list_versions(agent_name=agent_name)
            if not item.draft and not item.version.startswith("draft-")
        ]
    except ResourceNotFoundError:
        releases = []
    if {item["version"] for item in releases} != ({"1"} if version == "2" else set()):
        raise LabError("Unexpected release history; refusing to create v3 or reset existing versions.")
    if version == "2":
        if workspace_id is not None and (releases[0].get("metadata") or {}).get("workspace") != workspace_id:
            raise LabError("The baseline Agent belongs to a different workspace; no changes were made.")
        baseline = releases[0]["definition"]
        if {key: value for key, value in baseline.items() if key != "instructions"} != {
            key: value for key, value in definition.items() if key != "instructions"
        }:
            raise LabError("V1 and v2 must keep the same model, tools and generation settings.")
        if baseline["instructions"] == definition["instructions"]:
            raise LabError("Identical instructions are not a new improvement candidate.")
    record = {"intent": intent, "status": "creating", "agent": None}
    write_once_json(receipt, record)
    metadata = {"lab": "foundry-evaluation-optimizer", "release_policy": "fixed-v1-v2"}
    if workspace_id is not None:
        metadata["workspace"] = workspace_id
    created = project.agents.create_version(
        agent_name=agent_name, definition=PromptAgentDefinition(definition), draft=False,
        metadata=metadata,
        description=f"Fixed workshop v{version}; separate managed evaluation is required.",
    ).as_dict()
    record.update(status="created", agent=created)
    save_json(receipt, record)
    if (
        created["version"] != version or created["definition"] != definition
        or (workspace_id is not None and (created.get("metadata") or {}).get("workspace") != workspace_id)
    ):
        raise LabError("The created version differs from the requested fixed version; receipt preserved.")
    return record


def create_native_agent(config: Config, version: str, prompt: Path) -> dict:
    """Connect the prepared policy tool to a fixed, strict-output workshop Agent."""
    from lab.knowledge import knowledge_tool

    if version not in {"1", "2"}:
        raise LabError("The native workshop Agent permits only versions 1 and 2.")
    if not prompt.is_file() or not prompt.read_text(encoding="utf-8").strip():
        raise LabError(f"A nonempty instruction file is required: {prompt}")
    state = workspace(config)
    tool = knowledge_tool(config)
    snapshot = model_snapshot(config, config.model)
    snapshot_path = ARTIFACTS / "agents/native-model.json"
    if snapshot_path.exists():
        if read_json(snapshot_path) != snapshot:
            raise LabError("The Agent model deployment changed after setup; preserve the original comparison.")
    elif version == "2":
        raise LabError("Create and verify native Agent v1 before preparing v2.")
    else:
        write_once_json(snapshot_path, snapshot)
    definition = {
        "kind": "prompt",
        "model": config.model,
        "instructions": prompt.read_text(encoding="utf-8"),
        "tools": [tool.as_dict()],
        "text": native_response_format(),
    }
    receipt = ARTIFACTS / "agents" / f"native-v{version}.json"
    with credential_for(config) as credential:
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential, retry_total=0) as project:
            result = ensure_fixed_release(
                project, project_endpoint=config.project_endpoint, agent_name=config.agent_name("iq"),
                version=version, definition=definition, receipt=receipt,
                workspace_id=state["workspace_id"],
            )
    created = {"kind": "agent_version", "name": config.agent_name("iq"), "version": version}
    if created not in workspace(config)["created"]:
        record_created(config, created)
    return {
        "status": result["status"], "agent_name": config.agent_name("iq"), "version": version,
        "receipt": str(receipt), "model_snapshot": snapshot,
        "evaluation_status": "NOT_RUN", "production_approval": "NOT_GRANTED",
    }


def smoke_model(config: Config, run_id: str) -> dict:
    directory = safe_run_dir(run_id)
    path = directory / "model-smoke.json"
    if path.exists():
        previous = read_json(path)
        require_content_language(previous)
        if previous.get("project_endpoint") != config.project_endpoint or previous.get("deployment") != config.model:
            raise LabError("기존 model smoke의 환경/배포가 다릅니다.")
        if previous.get("status") != "completed":
            raise LabError("이 model smoke는 실패 또는 결과 불명입니다. 원본을 확인하기 전 재호출하지 않습니다.")
        return previous
    snapshot = model_snapshot(config, config.model)
    record = {
        **language_metadata(),
        "kind": "LIVE_MODEL_SMOKE_NOT_QUALITY_EVALUATION", "status": "submitting",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "code": code_provenance(),
        "project_endpoint": config.project_endpoint, "deployment": config.model,
        "model_snapshot": snapshot, "response_id": None, "cost": {"status": "NOT_OBSERVED"},
        "request": {"input": "Synthetic Contoso lab connectivity check. Reply with the single word READY.", "max_output_tokens": 128},
    }
    write_once_json(path, record)
    started = time.perf_counter()
    with credential_for(config) as credential:
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential, retry_total=0) as project:
            with project.get_openai_client(max_retries=0, timeout=120.0) as client:
                response = client.responses.create(model=config.model, **record["request"], store=True)
                record["response_id"] = response.id
                record["response"] = response.model_dump(mode="json")
                record["usage"] = record["response"].get("usage")
                record["latency_ms"] = (time.perf_counter() - started) * 1000
                record["status"] = "completed" if (
                    record["response"].get("status") == "completed"
                    and isinstance(response.id, str) and response.id.strip()
                    and isinstance(response.output_text, str) and response.output_text.strip()
                ) else "failed"
                save_json(path, record)
    if record["status"] != "completed":
        raise LabError("모델 smoke가 완료된 비어 있지 않은 응답을 반환하지 않았습니다.")
    return record


def create_agent(config: Config, stage: str, prompt: Path, *, new_version: bool = False) -> dict:
    if not prompt.is_file() or not prompt.read_text(encoding="utf-8").strip():
        raise LabError(f"프롬프트가 없거나 비어 있습니다: {prompt}")
    instructions = prompt.read_text(encoding="utf-8")
    state = workspace(config, create=True)
    name = config.agent_name(stage)
    model = config.tuned_model if stage == "tuned" else config.model
    if not model:
        raise LabError("실제 학습 완료 모델의 배포 이름 TUNED_MODEL_DEPLOYMENT가 필요합니다.")
    record_path = ARTIFACTS / "agents" / f"{stage}.json"
    if record_path.exists() and not new_version:
        raise LabError(
            f"{stage} 버전 기록이 이미 있습니다. 재사용하거나, 의도적인 변경에만 --new-version을 추가해야 합니다."
        )
    if record_path.exists():
        prior = read_json(record_path)
        prior_version = ARTIFACTS / "agents/versions" / f"{prior['name']}-v{prior['version']}.json"
        if not prior_version.exists():
            write_once_json(prior_version, prior)
    tools = []
    if stage != "baseline":
        from lab.knowledge import knowledge_tool

        tools = [knowledge_tool(config)]
    with credential_for(config) as credential:
        deployment = model_snapshot(config, model)
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential, retry_total=0) as project:
            try:
                existing = project.agents.get(agent_name=name)
            except ResourceNotFoundError:
                existing = None
            if existing is not None:
                if not record_path.exists():
                    raise LabError(f"원격에 {name}이 이미 존재하지만 이 실습의 소유 기록이 없습니다. 중단합니다.")
                previous = read_json(record_path)
                remote_version = project.agents.get_version(
                    agent_name=name, agent_version=previous["version"],
                )
                if (remote_version.metadata or {}).get("workspace") != state["workspace_id"]:
                    raise LabError("원격 에이전트의 실습 소유 표식이 다릅니다. 변경하지 않습니다.")
            agent = project.agents.create_version(
                agent_name=name,
                definition=PromptAgentDefinition(
                    model=model,
                    instructions=instructions,
                    tools=tools,
                ),
                metadata={
                    **language_metadata(),
                    "lab": "foundry-learning-loop-v1.1",
                    "workspace": state["workspace_id"],
                    "stage": stage,
                },
                description=f"Contoso synthetic workshop candidate: {stage}",
            )
            record = {
                **language_metadata(),
                "id": agent.id,
                "name": agent.name,
                "version": agent.version,
                "stage": stage,
                "project_endpoint": config.project_endpoint,
                "model_deployment": model,
                "model_snapshot": deployment,
                "prompt_file": str(prompt.resolve().relative_to(ROOT)) if prompt.resolve().is_relative_to(ROOT) else str(prompt.resolve()),
                "prompt_sha256": sha256_file(prompt),
                "prompt_source": "repository-authored-example" if prompt.resolve() == content_path(ROOT, "prompts/candidate.txt").resolve() else "operator-provided-local-file",
                "knowledge_sha256": sha256_file(content_path(ROOT, "data/knowledge/documents.json")) if tools else hashlib.sha256(b"").hexdigest(),
                "workspace_id": state["workspace_id"],
                "code": code_provenance(),
            }
            record_created(config, {"kind": "agent_version", "name": agent.name, "version": agent.version})
            snapshot = ARTIFACTS / "agents/prompts" / f"{agent.name}-v{agent.version}.txt"
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_text(instructions, encoding="utf-8")
            record["prompt_snapshot"] = artifact_reference(snapshot)
            write_once_json(ARTIFACTS / "agents/versions" / f"{agent.name}-v{agent.version}.json", record)
            save_json(record_path, record)
    return record


def load_agent(config: Config, stage: str) -> dict:
    state = workspace(config)
    record = read_json(ARTIFACTS / "agents" / f"{stage}.json")
    require_content_language(record)
    if (
        record.get("workspace_id") != state["workspace_id"]
        or record.get("project_endpoint") != config.project_endpoint
        or record.get("name") != config.agent_name(stage)
    ):
        raise LabError("에이전트 기록과 현재 실습 범위가 다릅니다.")
    return record
