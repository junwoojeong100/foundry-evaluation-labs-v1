"""Managed judges for captured outputs; this module never invokes an agent.

The CLI owns consent for ``submit_evaluation``. ``collect_evaluation`` performs
one status read, then bounded, paginated reads only when the run is completed.
``managed-eval.json`` is the submission/recovery ledger; do not delete it to
retry an uncertain POST. ``judge-contract.json`` is immutable canonical judge
provenance, not the inaccessible built-in evaluator's private prompt. Run IDs,
timestamps and report URLs deliberately do not belong in that judge contract.
They are mirrored under the top-level ``metadata.managed_evaluation`` key.
The evidence importer receives a shared ``scale: [1, 5]`` and per-case
``{groundedness: float, relevance: float, error: null}`` scores.
Catalog version selectors and a read-only judge deployment snapshot are public
configuration evidence, not an attestation of the private managed rubric.
``judge.version`` therefore stays ``service-managed/unpinned`` and
``service_version_pinned`` stays false.
Only API-successful, schema-valid captures are eligible. The export already
contains plain ``answer`` projections; only the raw source response/reference
JSON is parsed to verify those projections. Excluded attempts remain in the
capture metadata and never receive invented judge scores.

SDK contracts:
https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-datasets
https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-results
https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/evaluations/agentic_evaluators
"""

from collections.abc import Mapping
from copy import deepcopy
import hashlib
from importlib.metadata import version
from itertools import islice
import json
import logging
import math
from pathlib import Path
import re

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import TestingCriterionAzureAIEvaluator
from openai import APIError, BaseModel
from openai.types.eval_create_params import DataSourceConfigCustom
from openai.types.evals.create_eval_jsonl_run_data_source_param import (
    CreateEvalJSONLRunDataSourceParam,
    SourceFileContent,
    SourceFileContentContent,
)

from lab.auth import credential_for
from lab.config import Config, LabError
from lab.evidence import score_row, strict_json_loads
from lab.files import ROOT, safe_run_dir, sha256_file
from lab.preflight import az_json, save_json


METRICS = ("groundedness", "relevance")
FIELDS = ("case_id", "query", "response", "context", "ground_truth", "retrieved_context")
CONTEXT_DEFINITION = (
    "Fixed reference policy excerpts, identical across candidates; "
    "policy-groundedness, not evidence of agent retrieval."
)
RESPONSE_PROJECTION = (
    "Only answer from schema-valid captured response JSON and reference ground_truth JSON. "
    "Exported response and ground_truth are plain strings, not JSON to parse again; "
    "routing and citations are evaluated separately."
)
SERVICE_VERSION = "service-managed/unpinned"
REPRODUCIBILITY_LIMITATION = (
    "Only public configuration and submission-time deployment metadata are recorded. "
    "The private managed rubric/runtime is not attested or pinned, even when a catalog "
    "version selector is available. Deployment auto-upgrades and service changes can "
    "affect reproducibility; matching artifacts do not guarantee an identical private rubric."
)
LEDGER = "managed-eval.json"
CONTRACT = "judge-contract.json"
MANAGED_METADATA = "managed_evaluation"
FAILED = frozenset({"failed", "canceled", "cancelled"})
LOGGER = logging.getLogger(__name__)


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _object(value: object, label: str) -> dict:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_unset=True)
    if not isinstance(value, Mapping):
        raise LabError(f"{label}: 객체 형식이 필요합니다.")
    result = dict(value)
    try:
        _canonical(result)
    except (TypeError, ValueError) as exc:
        raise LabError(f"{label}: 유한한 JSON 값만 허용합니다.") from exc
    return result


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LabError(f"{label}: 비어 있지 않은 문자열이 필요합니다.")
    return value


def _read(path: Path, *, jsonl: bool = False, array: bool = False):
    if not path.is_file():
        raise LabError(f"필요한 근거 파일이 없습니다: {path}")
    try:
        text = path.read_text(encoding="utf-8")
        if not jsonl:
            value = strict_json_loads(text)
            if array:
                if not isinstance(value, list):
                    raise LabError(f"JSON 배열이 필요합니다: {path}")
                return [_object(item, str(path)) for item in value]
            return _object(value, str(path))
        lines = text.splitlines()
        if not lines or any(not line.strip() for line in lines):
            raise LabError(f"비어 있는 JSONL 또는 빈 행입니다: {path}")
        return [_object(strict_json_loads(line), str(path)) for line in lines]
    except ValueError as exc:
        raise LabError(f"JSON 근거 형식 오류: {path}: {exc}") from exc


def _index(rows: list[dict], field: str, label: str) -> dict[str, dict]:
    indexed = {}
    for row in rows:
        key = _text(row.get(field), f"{label}.{field}")
        if key in indexed:
            raise LabError(f"{label}: 중복 ID {key}; 위치 기반 병합은 하지 않습니다.")
        indexed[key] = row
    return indexed


def _load_source(config: Config, run_id: str) -> tuple[Path, dict, dict, dict]:
    directory = safe_run_dir(run_id)
    metadata = _read(directory / "metadata.json")
    if metadata.get("run_id") != run_id:
        raise LabError("metadata.run_id와 요청한 run-id가 다릅니다.")
    if metadata.get("project_endpoint") != config.project_endpoint:
        raise LabError("캡처된 실행과 현재 Foundry 프로젝트가 다릅니다. 원래 설정으로 수집하세요.")
    if metadata.get("status") not in ("completed", "completed_with_errors"):
        raise LabError("완료된 캡처만 평가합니다. 부분 실행을 성공으로 처리하지 않습니다.")
    split = metadata.get("source_split")
    if split not in ("dev", "test") or metadata.get("split") not in (split, "smoke"):
        raise LabError("평가 source_split/split은 캡처된 dev/test 또는 smoke여야 합니다.")
    for field in ("stage", "model_deployment"):
        _text(metadata.get(field), f"metadata.{field}")
    for field in ("dataset_sha256", "prompt_sha256", "knowledge_sha256"):
        value = metadata.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise LabError(f"metadata.{field}: SHA256 근거가 필요합니다.")
    row_ids = metadata.get("row_ids")
    if not isinstance(row_ids, list) or not row_ids:
        raise LabError("metadata.row_ids에 모든 시도 행의 ID가 필요합니다.")
    for value in row_ids:
        _text(value, "metadata.row_ids")
    if len(set(row_ids)) != len(row_ids):
        raise LabError("metadata.row_ids에 중복 ID가 있습니다.")

    dataset_path = ROOT / "data/splits" / f"{split}.jsonl"
    cases = _index(_read(dataset_path, jsonl=True), "id", "dataset")
    if sha256_file(dataset_path) != metadata["dataset_sha256"]:
        raise LabError("캡처 후 데이터셋이 변경되었습니다. 원본 근거를 복구하거나 새 실행을 만드세요.")
    if not set(row_ids) <= cases.keys():
        raise LabError("캡처된 행 ID가 원본 데이터셋에 없습니다.")
    records = _index(_read(directory / "outputs.jsonl", jsonl=True), "id", "outputs")
    if records.keys() != set(row_ids):
        raise LabError("outputs.jsonl은 실패를 포함한 모든 metadata.row_ids와 정확히 일치해야 합니다.")
    successful = {}
    for case_id, record in records.items():
        if "error" not in record or (
            record["error"] is not None
            and (not isinstance(record["error"], str) or not record["error"].strip())
        ):
            raise LabError(f"{case_id}: 캡처 error는 null 또는 오류 문자열이어야 합니다.")
        if any(not isinstance(record.get(key), str) for key in ("raw_output", "retrieved_context")):
            raise LabError(f"{case_id}: raw_output/retrieved_context는 원본 문자열이어야 합니다.")
        if record["error"] is None:
            successful[case_id] = record
    has_errors = len(successful) != len(records)
    if has_errors != (metadata["status"] == "completed_with_errors"):
        raise LabError("metadata.status와 캡처 오류 행이 일치하지 않습니다.")
    if not successful:
        raise LabError("성공적으로 캡처한 행이 없습니다. 유료 평가를 제출하지 않습니다.")

    citations = set(_index(
        _read(ROOT / "data/knowledge/documents.json", array=True), "id", "knowledge",
    ))
    projected = {}
    for case_id, record in successful.items():
        case = cases[case_id]
        if case.get("split") != split:
            raise LabError(f"{case_id}: 원본 사례의 split이 캡처 metadata와 다릅니다.")
        try:
            scored = score_row(case, record["raw_output"], known_citations=citations)
            if not scored["schema_valid"]:
                continue
            reference = score_row(case, case["ground_truth"], known_citations=citations)
        except ValueError as exc:
            raise LabError(f"{case_id}: 원본 사례/캡처 스키마 오류: {exc}") from exc
        if not reference["schema_valid"]:
            raise LabError(f"{case_id}: 원본 ground_truth가 응답 JSON 스키마를 따르지 않습니다.")
        projected[case_id] = {
            "case_id": case_id,
            "query": case["query"],
            "response": scored["response"]["answer"],
            "context": case["context"],
            "ground_truth": reference["response"]["answer"],
            "retrieved_context": record["retrieved_context"],
        }
    if not projected:
        raise LabError("API 성공·JSON 형식 유효 조건을 만족하는 답변이 없습니다. 유료 평가를 제출하지 않습니다.")

    rows = _index(_read(directory / "foundry-eval.jsonl", jsonl=True), "case_id", "foundry-eval")
    if rows.keys() != projected.keys():
        raise LabError("foundry-eval.jsonl은 API 성공·JSON 형식 유효 캡처 ID만 빠짐없이 포함해야 합니다.")
    for case_id, row in rows.items():
        if set(row) != set(FIELDS) or any(not isinstance(row.get(key), str) for key in FIELDS):
            raise LabError(f"{case_id}: 평가 입력은 {', '.join(FIELDS)} 문자열 필드만 허용합니다.")
        if row != projected[case_id]:
            raise LabError(
                f"{case_id}: 평가 입력이 원본 질문·정책·answer 투영과 다릅니다. "
                "context는 고정 참조 정책이며 retrieved_context로 대체하지 않습니다."
            )
    source = {
        "metadata": {
            key: value for key, value in metadata.items() if key not in {"judge", MANAGED_METADATA}
        },
        "outputs_sha256": sha256_file(directory / "outputs.jsonl"),
        "foundry_eval_sha256": sha256_file(directory / "foundry-eval.jsonl"),
    }
    return directory, metadata, rows, source


def _evaluator_versions(project) -> dict:
    versions = {
        f"builtin.{metric}": {
            "name": f"builtin.{metric}", "version": None, "id": None,
            "reported_version": None, "version_source": "not_exposed",
        }
        for metric in METRICS
    }
    observed = set()
    # Catalog selectors are retained when exposed; they are not a fingerprint
    # of the private rubric or an attestation of the managed service runtime.
    for index, item in enumerate(project.beta.evaluators.list(type="builtin", limit=100)):
        if index >= 500:
            raise LabError("Evaluator 목록이 500개를 초과했습니다. 자동 버전 선택을 중단합니다.")
        if not isinstance(item, Mapping):
            raise LabError("Evaluator 목록의 각 항목은 SDK 객체 또는 JSON 객체여야 합니다.")
        name = item.get("name")
        if name not in tuple(f"builtin.{metric}" for metric in METRICS):
            continue
        if name in observed:
            raise LabError(f"Evaluator 목록의 버전이 모호합니다: {name}")
        observed.add(name)
        reported_version = item.get("version")
        if reported_version is not None:
            _text(reported_version, f"{name}.version")
        value = None if reported_version is None or reported_version.lower() == "latest" else reported_version
        identifier = item.get("id")
        if identifier is not None:
            _text(identifier, f"{name}.id")
        versions[name] = {
            "name": name, "version": value, "id": identifier, "reported_version": reported_version,
            "version_source": "service_catalog" if value is not None else "not_exposed",
        }
    return versions


def _judge_deployment(config: Config) -> dict:
    deployments = az_json([
        "cognitiveservices", "account", "deployment", "list",
        "--subscription", config.subscription_id,
        "--resource-group", config.resource_group, "--name", config.account,
    ])
    if not isinstance(deployments, list):
        raise LabError("Judge 배포 조회 결과가 목록이 아닙니다.")
    matches = [
        deployment for item in deployments
        if (deployment := _object(item, "deployment")).get("name") == config.judge
    ]
    if len(matches) != 1:
        raise LabError("JUDGE_DEPLOYMENT의 실제 배포를 유일하게 확인하지 못했습니다. 설정과 읽기 권한을 확인하세요.")
    deployment = matches[0]
    identifier = deployment.get("id")
    if identifier is not None:
        _text(identifier, "judge deployment.id")
        if identifier.lower() != f"{config.account_id}/deployments/{config.judge}".lower():
            raise LabError("Judge 배포의 리소스 범위가 현재 계정과 다릅니다.")
    properties = _object(deployment.get("properties"), "judge deployment.properties")
    if properties.get("provisioningState") != "Succeeded":
        raise LabError("Judge 모델 배포가 Succeeded 상태가 아닙니다. 유료 평가를 제출하지 않습니다.")
    model = _object(properties.get("model"), "judge deployment.model")
    _text(model.get("name"), "judge deployment.model.name")
    for field in ("format", "version"):
        if model.get(field) is not None:
            _text(model[field], f"judge deployment.model.{field}")
    upgrade = properties.get("versionUpgradeOption")
    if upgrade is not None:
        _text(upgrade, "judge deployment.versionUpgradeOption")
    return {
        "deployment_name": deployment["name"],
        "resource_id": identifier,
        "model": {field: model.get(field) for field in ("format", "name", "version")},
        "version_upgrade_option": upgrade,
        "observation": "Read-only Azure management-plane lookup before submission; not runtime attestation.",
    }


def _contract(config: Config, versions: dict, deployment: dict) -> dict:
    criteria = []
    for metric in METRICS:
        mapping = {"query": "{{item.query}}", "response": "{{item.response}}"}
        if metric == "groundedness":
            mapping["context"] = "{{item.context}}"
        criterion = TestingCriterionAzureAIEvaluator(
            type="azure_ai_evaluator",
            name=metric,
            evaluator_name=f"builtin.{metric}",
            initialization_parameters={"deployment_name": config.judge, "threshold": 4},
            data_mapping=mapping,
        )
        if versions[f"builtin.{metric}"]["version"] is not None:
            criterion["evaluator_version"] = versions[f"builtin.{metric}"]["version"]
        criteria.append(criterion)
    return {
        "contract_version": "foundry-policy-reference-v3",
        "api": "Foundry project /openai/v1/evals",
        "model_deployment": config.judge,
        "judge_deployment": deployment,
        "service_version_pinned": False,
        "reproducibility_limitation": REPRODUCIBILITY_LIMITATION,
        "data_source_config": DataSourceConfigCustom(
            type="custom",
            include_sample_schema=False,
            item_schema={
                "type": "object",
                "properties": {field: {"type": "string"} for field in FIELDS},
                "required": list(FIELDS),
                "additionalProperties": False,
            },
        ),
        "testing_criteria": criteria,
        "evaluators": versions,
        "scale": [1, 5],
        "context_definition": CONTEXT_DEFINITION,
        "response_projection": RESPONSE_PROJECTION,
        "retrieved_context_definition": "Unmodified observed MCP output; retained, not mapped to a judge.",
        "sdk_versions": {name: version(name) for name in ("azure-ai-projects", "openai")},
    }


def _judge_metadata(contract: dict) -> dict:
    return {
        "model_deployment": contract["model_deployment"],
        "prompt_sha256": _digest(contract),
        "scale": contract["scale"],
        "version": SERVICE_VERSION,
        "service_version_pinned": False,
        "settings": deepcopy(contract),
        "provenance": {
            "source_artifact": CONTRACT,
            "sha256": _digest(contract),
            "hash_scope": (
                "Canonical public evaluator configuration, including observed deployment "
                "and SDK client settings; not the private managed prompt."
            ),
            "service_version_pinned": False,
            "limitation": REPRODUCIBILITY_LIMITATION,
        },
    }


def _immutable(path: Path, value: dict) -> None:
    if path.exists():
        if _canonical(_read(path)) != _canonical(value):
            raise LabError(f"기존 평가 근거가 다릅니다. 덮어쓰지 않습니다: {path}")
    else:
        save_json(path, value)


def _save_state(directory: Path, state: dict, *, judge: dict | None = None) -> None:
    save_json(directory / LEDGER, state)
    metadata = _read(directory / "metadata.json")
    metadata[MANAGED_METADATA] = {
        key: state.get(key) for key in ("eval_id", "run_id", "report_url")
    }
    if judge is not None:
        metadata["judge"] = judge
    save_json(directory / "metadata.json", metadata)


def _recovery(directory: Path, state: dict) -> str:
    return (
        f"평가 제출 기록: {directory / LEDGER} "
        f"(eval_id={state.get('eval_id')}, run_id={state.get('run_id')}). "
        "기록을 삭제하거나 재제출하지 마세요. Foundry에서 기존 실행을 확인한 뒤 "
        "확인된 ID로 이 기록을 복구하고 evaluate collect를 실행하세요."
    )


def _result(state: dict, run_id: str) -> dict:
    result = {key: state.get(key) for key in ("eval_id", "run_id", "report_url", "status", "collection_status")}
    if state.get("collection_status") != "collected" or state.get("status") != "completed":
        result["next_step"] = f"python -m lab evaluate collect --run-id {run_id}"
        result["instruction"] = "아직 점수를 수집하지 않았습니다. 위 명령으로 상태를 다시 조회하세요."
    else:
        result["scored_rows"] = state["scored_rows"]
        result["unscored_capture_ids"] = state["unscored_capture_ids"]
    return result


def _remember_run(directory: Path, state: dict, run: dict) -> None:
    if run.get("id") != state.get("run_id") or run.get("eval_id") != state.get("eval_id"):
        raise LabError("서비스 평가 ID/run ID가 로컬 제출 기록과 다릅니다.")
    state["status"] = _text(run.get("status"), "run.status")
    report = run.get("report_url")
    if report is not None:
        if not isinstance(report, str):
            raise LabError("run.report_url은 문자열 또는 null이어야 합니다.")
        state["report_url"] = report
    _save_state(directory, state)
    save_json(directory / "managed-eval-run.json", run)
    if state["status"] in FAILED:
        raise LabError(
            f"관리형 평가가 {state['status']}로 종료되었습니다: {run.get('error')}. "
            + _recovery(directory, state)
        )
    if state["status"] == "completed" and run.get("error"):
        raise LabError(f"완료 응답에 서비스 오류가 있습니다: {run['error']}")


def submit_evaluation(config: Config, run_id: str) -> dict:
    """Submit once, after CLI confirmation; never generate another agent output."""
    directory = safe_run_dir(run_id)
    if (directory / LEDGER).exists():
        state = _read(directory / LEDGER)
        raise LabError("기존 또는 불확실한 제출이 있어 중복 제출을 차단합니다. " + _recovery(directory, state))
    directory, metadata, rows, source = _load_source(config, run_id)
    if metadata.get(MANAGED_METADATA) is not None:
        raise LabError("metadata에 기존 평가 기록이 있습니다. managed-eval.json을 복구하고 collect를 사용하세요.")
    if metadata.get("judge") is not None or (directory / "judge-scores.json").exists():
        raise LabError("이미 judge 근거가 있습니다. 기존 평가를 덮어쓰거나 다시 제출하지 않습니다.")
    with credential_for(config) as credential:
        deployment = _judge_deployment(config)
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential) as project:
            contract = _contract(config, _evaluator_versions(project), deployment)
            state = {
                "eval_id": None, "run_id": None, "report_url": None,
                "status": "creating_evaluation", "collection_status": "not_collected",
                "project_endpoint": config.project_endpoint,
                "source": source, "judge_contract_sha256": _digest(contract),
            }
            try:
                (directory / LEDGER).touch(exist_ok=False)
            except FileExistsError as exc:
                raise LabError("다른 제출 기록이 생성되었습니다. 중복 제출을 중단합니다.") from exc
            _save_state(directory, state)
            _immutable(directory / CONTRACT, contract)
            with project.get_openai_client(max_retries=0, timeout=120.0) as client:
                try:
                    evaluation = _object(client.evals.create(
                        name=f"{config.prefix}-{run_id}-captured",
                        data_source_config=contract["data_source_config"],
                        testing_criteria=contract["testing_criteria"],
                        metadata={"local_run_id": run_id, "judge_contract_sha256": _digest(contract)},
                    ), "evaluation")
                    state["eval_id"] = evaluation.get("id")
                    state["status"] = "evaluation_created"
                    _save_state(directory, state)
                    save_json(directory / "managed-eval-definition.json", evaluation)
                    _text(state["eval_id"], "evaluation.id; 제출 기록을 보존하고 Foundry에서 확인하세요")
                    state["status"] = "creating_run"
                    _save_state(directory, state)
                    run = _object(client.evals.runs.create(
                        eval_id=state["eval_id"],
                        name=f"{config.prefix}-{run_id}-captured",
                        metadata={"local_run_id": run_id, "judge_contract_sha256": _digest(contract)},
                        data_source=CreateEvalJSONLRunDataSourceParam(
                            type="jsonl",
                            source=SourceFileContent(
                                type="file_content",
                                content=[SourceFileContentContent(item=row) for row in rows.values()],
                            ),
                        ),
                    ), "run")
                except APIError as exc:
                    state["status"] += "_unknown"
                    state["submission_error"] = str(exc)
                    _save_state(directory, state)
                    recovery = _recovery(directory, state)
                    exc.add_note(recovery)
                    LOGGER.error(recovery)
                    raise
                state["run_id"] = run.get("id")
                state["report_url"] = run.get("report_url")
                _save_state(directory, state)
                _text(state["run_id"], "run.id; 제출 기록을 보존하고 Foundry에서 확인하세요")
                _remember_run(directory, state, run)
    return _result(state, run_id)


def _parse_scores(items: list[dict], expected: dict, state: dict, contract: dict) -> dict:
    scores, service_ids = {}, set()
    for item in items:
        service_id = _text(item.get("id"), "output_item.id")
        if service_id in service_ids:
            raise LabError(f"중복 output_item.id: {service_id}")
        service_ids.add(service_id)
        if item.get("eval_id") != state["eval_id"] or item.get("run_id") != state["run_id"]:
            raise LabError("output_items에 다른 평가/실행의 행이 있습니다.")
        source = _object(item.get("datasource_item"), "output_item.datasource_item")
        if "item" in source:
            if "case_id" in source:
                raise LabError("datasource_item의 case_id 위치가 모호합니다.")
            source = _object(source["item"], "output_item.datasource_item.item")
        case_id = _text(source.get("case_id"), "output_item.datasource_item.case_id")
        if case_id not in expected or case_id in scores:
            raise LabError(f"알 수 없거나 중복된 case_id: {case_id}; 위치 기반 병합을 금지합니다.")
        if any(source.get(key) != expected[case_id][key] for key in FIELDS):
            raise LabError(f"{case_id}: 서비스 입력이 제출한 캡처와 다릅니다.")
        sample = item.get("sample")
        if sample is not None and not isinstance(sample, dict):
            raise LabError(f"{case_id}: sample 형식 오류입니다.")
        if item.get("status") not in ("pass", "fail") or item.get("error") or (sample or {}).get("error"):
            raise LabError(f"{case_id}: 서비스 행 상태/오류를 확인하세요. 점수를 추정하지 않습니다.")
        results = item.get("results")
        if not isinstance(results, list):
            raise LabError(f"{case_id}: evaluator results 목록이 없습니다.")
        row_scores = {}
        for result in results:
            result = _object(result, f"{case_id}.result")
            name = _text(result.get("name"), f"{case_id}.result.name").lower()
            metric = result.get("metric", name)
            if metric not in METRICS or name != metric or metric in row_scores:
                raise LabError(f"{case_id}: 중복·알 수 없거나 불일치한 evaluator metric입니다.")
            if result.get("type") != "azure_ai_evaluator" or result.get("error"):
                raise LabError(f"{case_id}.{metric}: evaluator 형식 또는 서비스 오류입니다.")
            grader_sample = result.get("sample")
            if grader_sample is not None and (
                not isinstance(grader_sample, dict) or grader_sample.get("error")
            ):
                raise LabError(f"{case_id}.{metric}: evaluator sample 오류입니다.")
            expected_evaluator = contract["evaluators"][f"builtin.{metric}"]
            for key, value in (
                ("evaluator_name", expected_evaluator["name"]),
                ("evaluator_version", expected_evaluator["version"]),
            ):
                if key in result:
                    if key == "evaluator_version" and value is None:
                        if result[key] is not None:
                            _text(result[key], f"{case_id}.{metric}.{key}")
                    elif result[key] != value:
                        raise LabError(f"{case_id}.{metric}: 서비스 {key}이 제출 계약과 다릅니다.")
            score = result.get("score")
            if (
                isinstance(score, bool) or not isinstance(score, (int, float))
                or not 1 <= score <= 5 or not math.isfinite(score)
            ):
                raise LabError(f"{case_id}.{metric}: 실제 1~5 유한 점수가 필요합니다.")
            if "threshold" in result and (isinstance(result["threshold"], bool) or result["threshold"] != 4):
                raise LabError(f"{case_id}.{metric}: 서비스 threshold가 제출한 4와 다릅니다.")
            passed = score >= 4
            if "passed" in result and (type(result["passed"]) is not bool or result["passed"] != passed):
                raise LabError(f"{case_id}.{metric}: score와 passed가 일치하지 않습니다.")
            if "label" in result and result["label"] != ("pass" if passed else "fail"):
                raise LabError(f"{case_id}.{metric}: score와 label이 일치하지 않습니다.")
            if "reason" in result and not isinstance(result["reason"], str):
                raise LabError(f"{case_id}.{metric}: reason 형식 오류입니다.")
            row_scores[metric] = float(score)
        if row_scores.keys() != set(METRICS):
            raise LabError(f"{case_id}: groundedness/relevance 점수가 모두 필요합니다.")
        row_scores["error"] = None
        scores[case_id] = row_scores
    if scores.keys() != expected.keys():
        missing = sorted(expected.keys() - scores.keys())
        raise LabError(f"output_items에 case_id가 누락되었습니다: {', '.join(missing)}")
    return {case_id: scores[case_id] for case_id in expected}


def collect_evaluation(config: Config, run_id: str) -> dict:
    """Read status once and collect only complete, ID-joined, validated scores."""
    directory, metadata, rows, source = _load_source(config, run_id)
    state = _read(directory / LEDGER)
    if state.get("project_endpoint") != config.project_endpoint:
        raise LabError("평가 제출 기록과 현재 프로젝트가 다릅니다.")
    if _canonical(state.get("source")) != _canonical(source):
        raise LabError("제출 이후 캡처/정책/출처가 변경되었습니다. 원본 근거를 복구하세요.")
    contract = _read(directory / CONTRACT)
    if state.get("judge_contract_sha256") != _digest(contract) or contract.get("model_deployment") != config.judge:
        raise LabError("평가 제출 후 judge 계약/배포가 변경되었습니다. 원래 JUDGE_DEPLOYMENT/계약으로 수집하세요.")
    if not state.get("eval_id") or not state.get("run_id"):
        raise LabError("평가 제출이 불완전하거나 결과가 불확실합니다. " + _recovery(directory, state))
    _text(state["eval_id"], "managed-eval.eval_id")
    _text(state["run_id"], "managed-eval.run_id")
    with credential_for(config) as credential:
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential) as project:
            with project.get_openai_client(max_retries=0, timeout=120.0) as client:
                run = _object(client.evals.runs.retrieve(
                    run_id=state["run_id"], eval_id=state["eval_id"],
                ), "run")
                _remember_run(directory, state, run)
                if state["status"] != "completed":
                    return _result(state, run_id)
                state["collection_status"] = "validating"
                _save_state(directory, state)
                try:
                    counts = _object(run.get("result_counts"), "run.result_counts")
                    if type(counts.get("total")) is not int or counts["total"] != len(rows):
                        raise LabError("서비스 total 행 수가 제출한 성공 캡처 행 수와 다릅니다.")
                    for key in ("passed", "failed", "errored"):
                        if key in counts and (type(counts[key]) is not int or counts[key] < 0):
                            raise LabError(f"서비스 result_counts.{key} 형식 오류입니다.")
                    if counts.get("errored", 0) != 0:
                        raise LabError("서비스 evaluator 오류 행이 있습니다. report_url에서 원인을 확인하세요.")
                    if all(key in counts for key in ("passed", "failed", "errored")) and (
                        counts["passed"] + counts["failed"] + counts["errored"] != counts["total"]
                    ):
                        raise LabError("서비스 result_counts 합계가 total과 다릅니다.")
                    items = [
                        _object(item, "output_item")
                        for item in islice(
                            client.evals.runs.output_items.list(
                                run_id=state["run_id"], eval_id=state["eval_id"], limit=100,
                            ),
                            len(rows) + 1,
                        )
                    ]
                    save_json(directory / "managed-eval-output-items.json", {"items": items})
                    scores = _parse_scores(items, rows, state, contract)
                    judge = _judge_metadata(contract)
                    if metadata.get("judge") is not None and _canonical(metadata["judge"]) != _canonical(judge):
                        raise LabError("기존 judge 출처가 다릅니다. 새 점수로 덮어쓰지 않습니다.")
                    _immutable(directory / "judge-scores.json", scores)
                except LabError as exc:
                    state["collection_status"] = "invalid_results"
                    state["collection_error"] = str(exc)
                    _save_state(directory, state)
                    raise
    state.update(
        collection_status="collected",
        scored_rows=len(scores),
        unscored_capture_ids=[case_id for case_id in metadata["row_ids"] if case_id not in scores],
    )
    state.pop("collection_error", None)
    _save_state(directory, state, judge=judge)
    return _result(state, run_id)
