"""Optional, real Foundry SFT. This is NOT Frontier Tuning or an IQ agent run.

The preparation manifest is immutable. sft-state.json journals cloud mutations;
an uncertain POST is never retried automatically. Status performs bounded reads.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time

from azure.ai.projects import AIProjectClient
from azure.core.exceptions import AzureError
from openai import APIError, APIStatusError

from lab.auth import credential_for, require_owned_scope
from lab.batch import export_evaluation, score_run
from lab.config import Config, LabError, load_config
from lab.files import ARTIFACTS, ROOT, artifact_reference, code_provenance, read_json, read_jsonl, safe_run_dir, sha256_file, write_jsonl
from lab.handoffs import validate_generated_data
from lab.http import ARM_SCOPE, CloudRequestError, JsonHttp
from lab.preflight import az_json, save_json


BASE_MODEL_NAME = "gpt-4.1-mini"
BASE_MODEL_VERSION = "2025-04-14"
BASE_MODEL = f"{BASE_MODEL_NAME}-{BASE_MODEL_VERSION}"
FINE_TUNE_USAGE = "OpenAI.Standard.gpt4.1-mini-finetune"
TRAINING_TYPE = "Standard"
TECHNIQUE = "Foundry SFT"
TERMINAL = {"succeeded", "failed", "cancelled", "canceled"}
STATE_FILE = "sft-state.json"
INFERENCE = {"temperature": 0, "max_tokens": 4096, "seed": 105}
BASELINE_ARTIFACTS = ("metadata.json", "outputs.jsonl", "prompt.txt", "summary.json", "report.md")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _directory() -> Path:
    return ARTIFACTS / "tuning/sft"


def _confirm(confirmed: bool) -> None:
    if not confirmed:
        raise LabError("선택형 Foundry SFT의 업로드·학습·취소·유료 추론에는 --confirm이 필요합니다.")


def _scope(config: Config) -> dict:
    config.validate()
    return {
        "tenant_id": config.tenant_id,
        "subscription_id": config.subscription_id,
        "account_id": config.account_id,
        "project_id": config.project_id,
        "project_endpoint": config.project_endpoint,
        "location": config.location,
        "prefix": config.prefix,
    }


def _object(value) -> dict:
    result = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
    if not isinstance(result, dict):
        raise LabError("서비스 또는 기록의 응답이 JSON 객체가 아닙니다.")
    return result


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LabError(f"{label}에 실제 비어 있지 않은 문자열이 필요합니다.")
    return value


def _persist(state: dict) -> None:
    path = _directory() / STATE_FILE
    pending = path.with_name(path.name + ".next")
    with pending.open("w", encoding="utf-8") as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)


@contextmanager
def _locked():
    directory = _directory()
    if not directory.is_dir():
        raise LabError("먼저 python -m lab tune-prepare --kind sft 를 실행하세요.")
    path = directory / "operation.lock"
    try:
        stream = path.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise LabError("SFT operation.lock이 있습니다. 동시 실행 또는 중단된 작업을 먼저 확인하세요.") from exc
    try:
        with stream:
            stream.write(f"pid={os.getpid()}\nstarted_at={_now()}\n")
        yield
    finally:
        path.unlink()


@contextmanager
def _client(config: Config):
    require_owned_scope(config)
    with credential_for(config) as credential:
        with AIProjectClient(endpoint=config.project_endpoint, credential=credential) as project:
            with project.get_openai_client(max_retries=0, timeout=120.0) as client:
                yield client


def model_messages(case: dict, system: str) -> list[dict]:
    user = json.dumps(
        {"query": _text(case.get("query"), "query"), "context": _text(case.get("context"), "context")},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _preparation() -> dict:
    from lab.governance import assert_dataset_use

    validate_generated_data()
    directory = _directory()
    manifest_path = directory / "manifest.json"
    manifest = _object(read_json(manifest_path))
    if (
        manifest.get("kind") != "sft-preparation"
        or manifest.get("status") != "PREPARED_NOT_SUBMITTED"
        or manifest.get("test_data_included") is not False
        or manifest.get("region_requested") != "northcentralus"
    ):
        raise LabError("원본 SFT 준비 매니페스트가 아니거나 동결 데이터/리전 계약이 다릅니다.")
    system = (ROOT / "prompts/tuning-system.txt").read_text(encoding="utf-8").strip()
    files = {}
    for split, count in (("train", 56), ("validation", 12)):
        name = f"sft-{split}.jsonl"
        path = directory / name
        info = manifest.get("files", {}).get(name, {})
        rows = read_jsonl(path)
        assert_dataset_use(path, "training")
        if (
            not path.read_bytes().startswith(b"\xef\xbb\xbf")
            or path.stat().st_size >= 512 * 1024 * 1024
            or len(rows) != count
            or info.get("rows") != count
            or info.get("bytes") != path.stat().st_size
            or info.get("sha256") != sha256_file(path)
            or rows != read_jsonl(ROOT / "data/tuning" / name)
        ):
            raise LabError(f"{name}: UTF-8 BOM, 행 수, 크기, 해시 또는 원본 분할이 다릅니다.")
        source = read_jsonl(ROOT / "data/splits" / f"{split}.jsonl")
        expected = [
            {"messages": model_messages(case, system) + [{"role": "assistant", "content": case["ground_truth"]}]}
            for case in source
        ]
        if rows != expected:
            raise LabError(f"{name}: system 또는 query/context 전용 입력 계약이 다릅니다.")
        files[split] = {
            "name": name, "sha256": info["sha256"], "bytes": info["bytes"], "rows": count,
            "id": None, "phase": "not_uploaded", "status": None,
        }
    return {
        "manifest_sha256": sha256_file(manifest_path),
        "prompt_sha256": sha256_file(ROOT / "prompts/tuning-system.txt"),
        "knowledge_sha256": sha256_file(ROOT / "data/knowledge/documents.json"),
        "files": files,
    }


def _new_state(config: Config, preparation: dict) -> dict:
    return {
        "kind": "foundry-sft", "technique": TECHNIQUE, "not_frontier_tuning": True,
        "code": code_provenance(),
        "scope": _scope(config), "base_model": BASE_MODEL, "training_type": TRAINING_TYPE,
        "status": "PREPARED_NOT_SUBMITTED", "created_at": _now(), **preparation,
        "baseline": None, "baseline_history": [],
        "job": {
            "id": None, "phase": "not_submitted", "status": None,
            "fine_tuned_model": None, "terminal_verified": False,
        },
    }


def _load_state(config: Config) -> dict:
    state = _object(read_json(_directory() / STATE_FILE))
    if (
        state.get("kind") != "foundry-sft"
        or state.get("scope") != _scope(config)
        or state.get("base_model") != BASE_MODEL
        or state.get("training_type") != TRAINING_TYPE
    ):
        raise LabError("기록된 SFT 계정·프로젝트·테넌트·prefix 또는 학습 계약과 설정이 다릅니다.")
    return state


def _unchanged(state: dict, preparation: dict) -> None:
    for key in ("manifest_sha256", "prompt_sha256", "knowledge_sha256"):
        if state.get(key) != preparation[key]:
            raise LabError(f"SFT 준비 이후 {key}가 변경되었습니다. 원본 실험을 보존하세요.")
    for split, expected in preparation["files"].items():
        actual = state["files"][split]
        if any(actual.get(key) != expected[key] for key in ("name", "sha256", "bytes", "rows")):
            raise LabError(f"SFT {split} 파일이 이전 기록과 다릅니다.")


def _error(exc: Exception) -> dict:
    return {
        "type": type(exc).__name__, "message": str(exc),
        "status_code": getattr(exc, "status_code", None),
        "request_id": getattr(exc, "request_id", None),
        "body": getattr(exc, "body", None),
    }


def _outcome(exc: Exception) -> str:
    if isinstance(exc, APIStatusError) and 400 <= exc.status_code < 500 and exc.status_code != 408:
        return "rejected"
    return "unknown"


def upload_files(config: Config, *, confirm: bool = False) -> dict:
    _confirm(confirm)
    with _locked():
        preparation = _preparation()
        state = _load_state(config) if (_directory() / STATE_FILE).exists() else _new_state(config, preparation)
        _unchanged(state, preparation)
        pending = [entry for entry in state["files"].values() if not entry["id"]]
        if any(entry["phase"] not in {"not_uploaded", "rejected"} for entry in pending):
            raise LabError("결과 불명 업로드가 있습니다. 재업로드하지 말고 포털에서 실제 파일을 확인하세요.")
        if not pending:
            return state
        if state["job"]["phase"] != "not_submitted":
            raise LabError("학습 요청 이후에는 파일을 추가 업로드하지 않습니다.")
        with _client(config) as client:
            for entry in pending:
                entry["phase"] = "uploading"
                state["status"] = "UPLOADING"
                _persist(state)
                try:
                    with (_directory() / entry["name"]).open("rb") as stream:
                        payload = _object(client.files.create(file=stream, purpose="fine-tune"))
                    entry["id"] = _text(payload.get("id"), "uploaded file ID")
                except Exception as exc:
                    entry.update(phase=_outcome(exc), error=_error(exc))
                    state["status"] = f"UPLOAD_{entry['phase'].upper()}"
                    _persist(state)
                    raise LabError("파일 업로드 실패. sft-state.json과 포털을 확인하세요. 자동 재시도하지 않습니다.") from exc
                entry.update(phase="uploaded", status=payload.get("status"), response=payload, error=None)
                # Commit each returned ID before attempting the next upload.
                _persist(state)
        state["status"] = "FILES_UPLOADED"
        _persist(state)
        return state


def _refresh_files(client, state: dict) -> None:
    for entry in state["files"].values():
        if not entry["id"]:
            continue
        payload = _object(client.files.retrieve(entry["id"]))
        if payload.get("id") != entry["id"] or payload.get("purpose") != "fine-tune":
            raise LabError("조회한 파일 ID 또는 purpose가 기록과 다릅니다.")
        if payload.get("bytes") != entry["bytes"]:
            raise LabError("원격 학습 파일 크기가 업로드 기록과 다릅니다.")
        entry.update(status=payload.get("status"), response=payload)
        _persist(state)


def _request(state: dict) -> dict:
    return {
        "model": BASE_MODEL,
        "training_file": state["files"]["train"]["id"],
        "validation_file": state["files"]["validation"]["id"],
        "seed": 105,
        "method": {"type": "supervised", "supervised": {"hyperparameters": {"n_epochs": 1}}},
        "extra_body": {"trainingType": TRAINING_TYPE},
    }


def _observe_job(response, state: dict, *, retrieved: bool) -> None:
    payload = _object(response)
    job = state["job"]
    job_id = _text(payload.get("id"), "fine-tuning job ID")
    if job["id"] and job["id"] != job_id:
        raise LabError("원격 작업 ID가 기록된 SFT 작업과 다릅니다.")
    save_json(_directory() / "job-observations" / f"{time.time_ns()}.json", {
        "observed_at": _now(), "retrieved": retrieved, "response": payload,
    })
    job.update(id=job_id, response=payload, fine_tuned_model=None, terminal_verified=False)
    _persist(state)
    expected = _request(state)
    if any(payload.get(key) != expected[key] for key in ("model", "training_file", "validation_file")):
        raise LabError("원격 작업의 기반 모델 또는 학습·검증 파일이 기록과 다릅니다.")
    observed_type = payload.get("trainingType", payload.get("training_type"))
    if observed_type is not None and (
        not isinstance(observed_type, str) or observed_type.lower() != TRAINING_TYPE.lower()
    ):
        raise LabError("원격 작업이 Standard 학습이 아닙니다. 자동 대체를 허용하지 않습니다.")
    job["status"] = _text(payload.get("status"), "actual job status")
    job["phase"] = "recorded"
    job["observed_at"] = _now()
    job["terminal_verified"] = retrieved and job["status"] in TERMINAL
    state["status"] = f"JOB_{job['status'].upper()}"
    _persist(state)
    if job["status"] == "succeeded":
        model_id = _text(payload.get("fine_tuned_model"), "succeeded fine_tuned_model")
        if model_id == BASE_MODEL:
            raise LabError("학습 결과 ID가 기반 모델과 같습니다. 실제 학습 모델을 확인하세요.")
        job["fine_tuned_model"] = model_id
    _persist(state)


def submit_job(config: Config, *, confirm: bool = False) -> dict:
    _confirm(confirm)
    with _locked():
        state = _load_state(config)
        if state["job"]["phase"] != "not_submitted" or state["job"]["id"]:
            raise LabError("이미 제출했거나 결과 불명인 학습 요청입니다. submit을 반복하지 말고 status/포털을 확인하세요.")
        _unchanged(state, _preparation())
        baseline = _baseline_evidence(state)
        if not all(entry["id"] for entry in state["files"].values()):
            raise LabError("학습·검증 파일 모두 먼저 upload 해야 합니다.")
        with _client(config) as client:
            _verify_account(config)
            current = _deployment(config, baseline["model_deployment"], tuned_model=None)
            if _deployment_contract(current) != _deployment_contract(baseline["deployment_evidence"]):
                raise LabError("학습 전 baseline 이후 배포 설정이 변경되었습니다. 새 run-id로 baseline을 다시 기록하세요.")
            _refresh_files(client, state)
            if any(entry["status"] != "processed" for entry in state["files"].values()):
                raise LabError("두 파일 모두 processed여야 합니다. status로 확인 후 수동으로 submit 하세요.")
            request = _request(state)
            state["job"].update(
                phase="submitting", request=request, requested_at=_now(),
                baseline_run_id=baseline["run_id"], baseline_deployment_at_submit=current,
            )
            state["status"] = "SUBMITTING"
            _persist(state)
            try:
                response = client.fine_tuning.jobs.create(**request)
            except Exception as exc:
                state["job"].update(phase=f"submission_{_outcome(exc)}", error=_error(exc))
                state["status"] = state["job"]["phase"].upper()
                _persist(state)
                raise LabError("학습 요청 실패/결과 불명. 포털에서 실제 작업을 확인하세요. 재제출은 차단했습니다.") from exc
            _observe_job(response, state, retrieved=False)
        return state


def job_status(config: Config) -> dict:
    with _locked():
        if not (_directory() / STATE_FILE).exists():
            return _new_state(config, _preparation())
        state = _load_state(config)
        if state["job"]["id"] or any(entry["id"] for entry in state["files"].values()):
            with _client(config) as client:
                if state["job"]["id"]:
                    _observe_job(client.fine_tuning.jobs.retrieve(state["job"]["id"]), state, retrieved=True)
                else:
                    _refresh_files(client, state)
        return state


def wait_job(config: Config, *, timeout_seconds: int = 3600, interval_seconds: int = 60) -> dict:
    if not 1 <= timeout_seconds <= 3600 or not 1 <= interval_seconds <= 120:
        raise LabError("SFT 대기는 최대 3600초, 조회 간격은 1~120초입니다.")
    deadline = time.monotonic() + timeout_seconds
    while True:
        state = job_status(config)
        if not state["job"]["id"]:
            raise LabError("조회할 실제 학습 작업 ID가 없습니다. wait는 새 작업을 제출하지 않습니다.")
        if state["job"]["terminal_verified"]:
            return state
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise LabError(f"SFT 대기 한도 도달. 원격 작업 {state['job']['id']}는 보존했습니다. status로 재개하세요.")
        print(f"{state['job']['id']}: {state['job']['status']}; waiting without resubmission", flush=True)
        time.sleep(min(interval_seconds, remaining))


def cancel_job(config: Config, *, confirm: bool = False) -> dict:
    _confirm(confirm)
    with _locked():
        state = _load_state(config)
        job = state["job"]
        if not job["id"]:
            raise LabError("취소할 기록된 작업 ID가 없습니다. 결과 불명 요청은 포털에서 먼저 확인하세요.")
        with _client(config) as client:
            _observe_job(client.fine_tuning.jobs.retrieve(job["id"]), state, retrieved=True)
            if job["status"] in TERMINAL:
                return state
            if job.get("cancellation"):
                raise LabError("이미 취소 요청을 시도했습니다. status로 실제 종료 상태를 확인하세요.")
            job["cancellation"] = {"phase": "requesting", "requested_at": _now()}
            _persist(state)
            try:
                response = client.fine_tuning.jobs.cancel(job["id"])
            except Exception as exc:
                job["cancellation"].update(phase=_outcome(exc), error=_error(exc))
                _persist(state)
                raise LabError("취소 결과를 단정할 수 없습니다. status/포털로 확인하세요.") from exc
            job["cancellation"]["phase"] = "requested"
            _observe_job(response, state, retrieved=False)
        return state


def _deployment(config: Config, name: str, *, tuned_model: str | None) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", name):
        raise LabError("실제 모델 배포 이름을 지정하세요. 리소스 ID나 URL은 허용하지 않습니다.")
    deployment = _object(az_json([
        "cognitiveservices", "account", "deployment", "show",
        "--subscription", config.subscription_id, "--resource-group", config.resource_group,
        "--name", config.account, "--deployment-name", name,
    ]))
    expected_id = f"{config.account_id}/deployments/{name}"
    properties = deployment.get("properties", {})
    model = properties.get("model", {})
    expected_model = (
        {"format": "OpenAI", "name": tuned_model, "version": "1"} if tuned_model
        else {"format": "OpenAI", "name": BASE_MODEL_NAME, "version": BASE_MODEL_VERSION}
    )
    if (
        str(deployment.get("id", "")).lower() != expected_id.lower()
        or properties.get("provisioningState") != "Succeeded"
        or any(model.get(key) != value for key, value in expected_model.items())
        or deployment.get("sku", {}).get("name") != "Standard"
    ):
        raise LabError(f"{name}: 지정 계정의 준비된 Standard 배포 또는 실제 기반/학습 모델과 다릅니다.")
    return deployment


def _verify_account(config: Config) -> None:
    account = _object(az_json([
        "cognitiveservices", "account", "show", "--subscription", config.subscription_id,
        "--resource-group", config.resource_group, "--name", config.account,
    ]))
    if (
        str(account.get("id", "")).lower() != config.account_id.lower()
        or str(account.get("location", "")).lower().replace(" ", "") != config.location
    ):
        raise LabError("기반/학습 배포의 실제 계정 또는 NCUS 리전이 설정과 다릅니다.")


def _deployment_contract(deployment: dict) -> dict:
    properties = deployment.get("properties", {})
    return {
        "id": str(deployment.get("id", "")).lower(),
        "model": properties.get("model"),
        "sku": deployment.get("sku"),
        "rai_policy_name": properties.get("raiPolicyName"),
        "version_upgrade_option": properties.get("versionUpgradeOption"),
    }


def deploy_tuned_model(config: Config, name: str, *, capacity: int = 10, confirm: bool = False) -> dict:
    """Only deploy the retrieved result of this owned SFT job; never update another deployment."""
    _confirm(confirm)
    require_owned_scope(config)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", name) or type(capacity) is not int or not 1 <= capacity <= 20:
        raise LabError("배포 이름과 1~20의 명시적인 Standard capacity가 필요합니다.")
    with _locked():
        state = _load_state(config)
        with _client(config) as client:
            if not state["job"]["id"]:
                raise LabError("실제 학습 작업 ID가 없습니다.")
            _observe_job(client.fine_tuning.jobs.retrieve(state["job"]["id"]), state, retrieved=True)
        if state["job"]["status"] != "succeeded" or not state["job"]["terminal_verified"]:
            raise LabError("서비스에서 종료 확인한 succeeded SFT 작업만 배포할 수 있습니다.")
        _verify_account(config)
        expected = {
            "sku": {"name": "Standard", "capacity": capacity},
            "properties": {
                "model": {"format": "OpenAI", "name": state["job"]["fine_tuned_model"], "version": "1"},
                "versionUpgradeOption": "NoAutoUpgrade",
            },
        }
        deployments = state.setdefault("deployments", {})
        record = deployments.get(name)
        if record and record.get("request") != expected:
            raise LabError("기록된 학습 모델 배포 계약과 다릅니다. 기존 배포를 덮어쓰지 않습니다.")
        url = f"https://management.azure.com{config.account_id}/deployments/{name}?api-version=2025-06-01"
        with credential_for(config) as credential:
            http = JsonHttp(credential, scope=ARM_SCOPE, allowed_origin="https://management.azure.com")
            try:
                remote = http.request("GET", url).body
            except CloudRequestError as exc:
                if exc.status != 404:
                    raise
                remote = None
            if remote is not None:
                if record is None:
                    raise LabError("동일 이름의 배포가 있지만 이 학습 실습의 소유 기록이 없습니다.")
                observed = remote.get("properties", {})
                if (
                    any(observed.get("model", {}).get(key) != value for key, value in expected["properties"]["model"].items())
                    or any(remote.get("sku", {}).get(key) != value for key, value in expected["sku"].items())
                ):
                    raise LabError("원격 학습 모델/배포 SKU가 기록과 다릅니다.")
                record.update(status=observed.get("provisioningState"), response=remote, observed_at=_now())
                _persist(state)
                return record
            if record is not None:
                raise LabError("이 배포 제출은 결과 불명입니다. ARM 상태를 확인하기 전 다시 생성하지 않습니다.")
            models = _object(az_json([
                "rest", "--method", "get", "--url",
                f"https://management.azure.com/subscriptions/{config.subscription_id}/providers/"
                f"Microsoft.CognitiveServices/locations/{config.location}/usages?api-version=2023-05-01",
            ]))
            quota = next((item for item in models.get("value", [])
                          if item.get("name", {}).get("value") == FINE_TUNE_USAGE), None)
            if not quota or quota.get("limit", 0) - quota.get("currentValue", 0) < capacity:
                raise LabError(f"NCUS {FINE_TUNE_USAGE}의 여유 quota가 부족하거나 확인되지 않았습니다.")
            record = {
                "request": expected, "url": url, "status": "SUBMITTING", "requested_at": _now(),
                "cost": {"status": "NOT_OBSERVED", "ongoing_hosting": True},
                "retention": "No automatic deletion. Hosting charges continue until an approved cleanup.",
            }
            deployments[name] = record
            _persist(state)
            response = http.request("PUT", url, expected, create_only=True)
            record.update(status=response.body.get("properties", {}).get("provisioningState", "SUBMITTED"),
                          response=response.body, http_status=response.status)
            _persist(state)
            return record


def capture_model(client, deployment: str, case: dict, system: str) -> dict:
    request = {"model": deployment, "messages": model_messages(case, system), **INFERENCE}
    started = time.perf_counter()
    record = {
        "id": case["id"], "raw_output": "", "usage": None, "response_id": None,
        "retrieved_context": "", "error": None, "response": None, "request": request,
    }
    try:
        payload = _object(client.chat.completions.create(**request))
    except (APIError, AzureError) as exc:
        record.update(error=f"{type(exc).__name__}: {exc}", error_details=_error(exc))
    else:
        record.update(response=payload, response_id=payload.get("id"), usage=payload.get("usage"))
        choices = payload.get("choices") or []
        choice = choices[0] if len(choices) == 1 else {}
        message = choice.get("message") or {}
        content = message.get("content")
        record["raw_output"] = content if isinstance(content, str) else ""
        if choice.get("finish_reason") != "stop" or message.get("refusal") or not record["raw_output"].strip():
            record["error"] = (
                f"Incomplete/refused/empty completion; finish_reason={choice.get('finish_reason')}; "
                f"refusal={message.get('refusal')}"
            )
    record["latency_ms"] = (time.perf_counter() - started) * 1000
    return record


def _evaluation_cases(split: str) -> tuple[Path, list[dict]]:
    if split not in {"dev", "test"}:
        raise LabError("모델 평가 데이터는 dev 또는 test만 허용합니다.")
    dataset = ROOT / "data/splits" / f"{split}.jsonl"
    cases = read_jsonl(dataset)
    ids = [case.get("id") for case in cases]
    if (
        len(cases) != {"dev": 12, "test": 20}[split]
        or any(not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value) for value in ids)
        or len(set(ids)) != len(ids)
        or any(case.get("split") != split for case in cases)
    ):
        raise LabError("모든 dev 12행/test 20행과 유효한 행 ID·source split이 필요합니다.")
    return dataset, cases


def _capture_runs(
    config: Config, state: dict, client, split: str, directories: dict, names: dict,
    deployments: dict, *, phase: str, pair_id: str | None = None, interval_seconds: float = 0,
) -> dict:
    if type(interval_seconds) not in (int, float) or not 0 <= interval_seconds <= 120:
        raise LabError("SFT interval-seconds는 0~120초여야 합니다.")
    dataset, cases = _evaluation_cases(split)
    prompt = ROOT / "prompts/tuning-system.txt"
    system = prompt.read_text(encoding="utf-8").strip()
    metadata, records = {}, {arm: [] for arm in directories}
    for arm, directory in directories.items():
        directory.mkdir(parents=True, exist_ok=False)
        snapshot = directory / "prompt.txt"
        snapshot.write_bytes(prompt.read_bytes())
        metadata[arm] = {
            "run_id": directory.name, "stage": "candidate" if arm == "base" else "tuned",
            "code": code_provenance(),
            "split": split, "source_split": split, "dataset_sha256": sha256_file(dataset),
            "model_deployment": names[arm], "prompt_sha256": state["prompt_sha256"],
            "knowledge_sha256": state["knowledge_sha256"],
            "prompt_snapshot": artifact_reference(snapshot, root=ROOT),
            "project_endpoint": config.project_endpoint, "scope": state["scope"],
            "judge": None, "row_ids": [case["id"] for case in cases], "status": "running", "created_at": _now(),
            "parameters": {**INFERENCE, "retries": 0, "timeout_seconds": 120},
            "target_type": "model", "technique": TECHNIQUE, "arm": arm,
            "pair_id": pair_id, "training_job_id": state["job"]["id"],
            "training_base_model": BASE_MODEL, "training_type": TRAINING_TYPE,
            "experiment_phase": phase, "deployment_evidence": deployments[arm],
            "comparison": "Reference-context-conditioned model comparison; NOT IQ agent execution or Frontier Tuning.",
            "execution_order": (
                "Single base arm, full dev before training submission." if phase == "pretraining-baseline"
                else "Interleaved base then tuned for each row."
            ),
        }
        if interval_seconds:
            metadata[arm]["parameters"]["interval_seconds"] = interval_seconds
        save_json(directory / "metadata.json", metadata[arm])
    try:
        first_request = True
        for case in cases:
            for arm, directory in directories.items():
                if not first_request and interval_seconds:
                    time.sleep(interval_seconds)
                first_request = False
                record = capture_model(client, names[arm], case, system)
                records[arm].append(record)
                save_json(directory / "raw" / f"{case['id']}.json", record)
                write_jsonl(directory / "outputs.jsonl", records[arm])
                print(f"{directory.name} {case['id']}: {'ERROR' if record['error'] else 'captured'}", flush=True)
        for arm, directory in directories.items():
            export_evaluation(directory, cases, records[arm])
            metadata[arm]["status"] = (
                "completed_with_errors" if any(row["error"] for row in records[arm]) else "completed"
            )
            metadata[arm]["completed_at"] = _now()
            save_json(directory / "metadata.json", metadata[arm])
    except BaseException:
        for arm, directory in directories.items():
            if metadata[arm]["status"] == "running":
                metadata[arm]["status"] = "interrupted"
                save_json(directory / "metadata.json", metadata[arm])
        raise
    return metadata


def run_baseline(config: Config, base_deployment: str, run_id: str, *, confirm: bool = False,
                 interval_seconds: float = 0) -> dict:
    _confirm(confirm)
    directory = safe_run_dir(run_id)
    if directory.exists():
        raise LabError("baseline 실행 폴더가 이미 있습니다. 새 --run-id를 지정하세요.")
    with _locked():
        preparation = _preparation()
        state = _load_state(config) if (_directory() / STATE_FILE).exists() else _new_state(config, preparation)
        _unchanged(state, preparation)
        if state["job"]["phase"] != "not_submitted" or state["job"]["id"]:
            raise LabError("학습 요청 이후에는 pretraining baseline을 만들 수 없습니다.")
        _evaluation_cases("dev")
        with _client(config) as client:
            _verify_account(config)
            deployment = _deployment(config, base_deployment, tuned_model=None)
            if state.get("baseline"):
                state.setdefault("baseline_history", []).append(state["baseline"])
            state["baseline"] = {"run_id": run_id, "phase": "capturing", "started_at": _now(),
                                 "interval_seconds": interval_seconds}
            state["status"] = "BASELINE_RUNNING"
            _persist(state)
            try:
                metadata = _capture_runs(
                    config, state, client, "dev", {"base": directory}, {"base": base_deployment},
                    {"base": deployment}, phase="pretraining-baseline",
                    interval_seconds=interval_seconds,
                )["base"]
                score_run(run_id)
            except BaseException:
                state["baseline"]["phase"] = "interrupted"
                state["status"] = "BASELINE_INTERRUPTED"
                _persist(state)
                raise
            state["baseline"].update(
                phase="completed", recorded_at=_now(), status=metadata["status"],
                model_deployment=base_deployment, source_split="dev",
                artifacts_sha256={name: sha256_file(directory / name) for name in BASELINE_ARTIFACTS},
            )
            state["status"] = "BASELINE_RECORDED"
            _persist(state)
        return state


def _baseline_evidence(state: dict) -> dict:
    reference = state.get("baseline")
    if not isinstance(reference, dict) or reference.get("phase") != "completed":
        raise LabError("먼저 baseline --base-deployment ... --run-id ... --confirm 으로 학습 전 dev 기준선을 완료하세요.")
    directory = safe_run_dir(_text(reference.get("run_id"), "baseline run-id"))
    hashes = reference.get("artifacts_sha256", {})
    if set(hashes) != set(BASELINE_ARTIFACTS):
        raise LabError("baseline의 불변 실행·로컬 점수 근거 해시가 없습니다.")
    for name in BASELINE_ARTIFACTS:
        path = directory / name
        if not path.is_file() or sha256_file(path) != hashes[name]:
            raise LabError(f"baseline 근거가 누락되거나 변경되었습니다: {name}")
    metadata = _object(read_json(directory / "metadata.json"))
    dataset, cases = _evaluation_cases("dev")
    expected = {
        "run_id": reference["run_id"], "stage": "candidate", "split": "dev", "source_split": "dev",
        "scope": state["scope"], "project_endpoint": state["scope"]["project_endpoint"],
        "experiment_phase": "pretraining-baseline", "training_job_id": None,
        "training_base_model": BASE_MODEL, "training_type": TRAINING_TYPE,
        "target_type": "model", "technique": TECHNIQUE, "arm": "base",
        "model_deployment": reference["model_deployment"],
        "dataset_sha256": sha256_file(dataset), "prompt_sha256": state["prompt_sha256"],
        "knowledge_sha256": state["knowledge_sha256"],
        "prompt_snapshot": artifact_reference(directory / "prompt.txt", root=ROOT),
        "row_ids": [case["id"] for case in cases],
        "parameters": {**INFERENCE, "retries": 0, "timeout_seconds": 120},
    }
    if reference.get("interval_seconds"):
        expected["parameters"]["interval_seconds"] = reference["interval_seconds"]
    if (
        any(metadata.get(key) != value for key, value in expected.items())
        or metadata.get("status") not in {"completed", "completed_with_errors"}
        or hashes["prompt.txt"] != metadata["prompt_sha256"]
    ):
        raise LabError("baseline의 dev 전체 분할·프롬프트·지식·배포 또는 학습 전 출처가 현재 실험과 다릅니다.")
    records = read_jsonl(directory / "outputs.jsonl")
    if [record.get("id") for record in records] != expected["row_ids"]:
        raise LabError("baseline에는 오류를 포함한 모든 dev 행의 실제 캡처가 필요합니다.")
    system = (directory / "prompt.txt").read_text(encoding="utf-8").strip()
    for case, record in zip(cases, records, strict=True):
        request = {"model": metadata["model_deployment"], "messages": model_messages(case, system), **INFERENCE}
        if record.get("request") != request or read_json(directory / "raw" / f"{case['id']}.json") != record:
            raise LabError("baseline의 query/context 전용 요청 또는 원본 응답 기록이 다릅니다.")
    has_errors = any(record.get("error") for record in records)
    if has_errors != (metadata["status"] == "completed_with_errors"):
        raise LabError("baseline 완료 상태와 실패 행 기록이 다릅니다.")
    return metadata


def run_pair(
    config: Config, base_deployment: str, tuned_deployment: str, split: str, run_prefix: str,
    *, confirm: bool = False, interval_seconds: float = 0,
) -> dict:
    _confirm(confirm)
    if split not in {"dev", "test"} or base_deployment == tuned_deployment:
        raise LabError("dev/test와 서로 다른 기반·학습 배포 이름을 지정하세요.")
    directories = {arm: safe_run_dir(f"{run_prefix}-{arm}") for arm in ("base", "tuned")}
    if any(path.exists() for path in directories.values()):
        raise LabError("실행 폴더가 이미 있습니다. 덮어쓰기 없이 새 --run-prefix를 지정하세요.")
    with _locked():
        state = _load_state(config)
        _unchanged(state, _preparation())
        _evaluation_cases(split)
        if not state["job"]["id"]:
            raise LabError("실제 제출한 SFT 작업 ID가 없습니다.")
        with _client(config) as client:
            _observe_job(client.fine_tuning.jobs.retrieve(state["job"]["id"]), state, retrieved=True)
            if state["job"]["status"] != "succeeded" or not state["job"]["fine_tuned_model"]:
                raise LabError("실제 succeeded 작업과 fine_tuned_model 없이는 비교할 수 없습니다.")
            _verify_account(config)
            deployments = {
                "base": _deployment(config, base_deployment, tuned_model=None),
                "tuned": _deployment(config, tuned_deployment, tuned_model=state["job"]["fine_tuned_model"]),
            }
            names = {"base": base_deployment, "tuned": tuned_deployment}
            metadata = _capture_runs(
                config, state, client, split, directories, names, deployments,
                phase="posttraining-pair", pair_id=run_prefix,
                interval_seconds=interval_seconds,
            )
        return metadata


def status_summary(state: dict) -> dict:
    job = state["job"]
    summary = {
        "technique": TECHNIQUE, "not_frontier_tuning": True, "base_model": BASE_MODEL,
        "training_type": TRAINING_TYPE, "workflow_status": state["status"],
        "files": {
            split: {key: entry.get(key) for key in ("id", "phase", "status", "error")}
            for split, entry in state["files"].items()
        },
        "job_id": job["id"], "submission_phase": job["phase"], "actual_status": job["status"],
        "terminal_verified_by_retrieve": job["terminal_verified"],
        "cancellation": job.get("cancellation"), "error": job.get("error"),
        "baseline": state.get("baseline"),
        "deployments": state.get("deployments", {}),
    }
    if job["status"] == "succeeded" and job["fine_tuned_model"]:
        summary["fine_tuned_model"] = job["fine_tuned_model"]
    for key in ("result_files", "trained_tokens"):
        if key in job.get("response", {}):
            summary[key] = job["response"][key]
    return summary


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Optional REAL Foundry SFT — NOT Frontier Tuning. 유료 작업은 명시적으로 승인합니다.")
    result.add_argument("--config", type=Path, default=Path(".env"))
    commands = result.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("baseline", "학습 전 동일 기반 모델의 dev 12행 유료 캡처·로컬 점수"),
        ("upload", "준비한 56 train/12 validation만 업로드"),
        ("submit", "processed 파일로 Standard SFT 작업 1회 요청"),
        ("status", "기록된 파일/작업을 한 번 조회 (클라우드 읽기 전용)"),
        ("wait", "기록된 학습 작업만 최대 60분 대기·조회; 새 제출 없음"),
        ("cancel", "기록된 작업만 취소 요청; status로 종료 확인"),
        ("run-pair", "동일 기반/실제 학습 모델의 dev 또는 test 유료 추론"),
        ("deploy", "종료 확인한 학습 모델만 새 Standard 배포로 생성; 지속 호스팅 비용 발생"),
    ):
        command = commands.add_parser(name, help=help_text)
        if name not in {"status", "wait"}:
            command.add_argument("--confirm", action="store_true")
        if name == "baseline":
            command.add_argument("--base-deployment", required=True)
            command.add_argument("--run-id", required=True)
            command.add_argument("--interval-seconds", type=float, default=0)
        if name == "run-pair":
            command.add_argument("--base-deployment", required=True)
            command.add_argument("--tuned-deployment", required=True)
            command.add_argument("--split", choices=("dev", "test"), required=True)
            command.add_argument("--run-prefix", required=True)
            command.add_argument("--interval-seconds", type=float, default=0)
        if name == "deploy":
            command.add_argument("--deployment", required=True)
            command.add_argument("--capacity", type=int, default=10)
        if name == "wait":
            command.add_argument("--timeout-seconds", type=int, default=3600)
            command.add_argument("--interval-seconds", type=int, default=60)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command not in {"status", "wait"}:
            _confirm(args.confirm)
        config = load_config(args.config)
        if args.command == "baseline":
            result = status_summary(run_baseline(config, args.base_deployment, args.run_id,
                                                 confirm=args.confirm, interval_seconds=args.interval_seconds))
        elif args.command == "run-pair":
            result = run_pair(
                config, args.base_deployment, args.tuned_deployment, args.split, args.run_prefix,
                confirm=args.confirm,
                interval_seconds=args.interval_seconds,
            )
        elif args.command == "status":
            result = status_summary(job_status(config))
        elif args.command == "wait":
            state = wait_job(config, timeout_seconds=args.timeout_seconds, interval_seconds=args.interval_seconds)
            result = status_summary(state)
            if state["job"]["status"] != "succeeded":
                print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
                return 1
        elif args.command == "deploy":
            result = deploy_tuned_model(config, args.deployment, capacity=args.capacity, confirm=args.confirm)
        else:
            operation = {"upload": upload_files, "submit": submit_job, "cancel": cancel_job}[args.command]
            result = status_summary(operation(config, confirm=args.confirm))
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (LabError, APIError, AzureError, OSError) as exc:
        print(f"SFT 중단: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
