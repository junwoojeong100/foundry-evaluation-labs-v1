"""Import preserved portal output without inventing an optimizer API or job ID."""

from datetime import datetime, timezone
import difflib
import hashlib
from pathlib import Path

from lab.config import Config, LabError
from lab.files import ARTIFACTS, artifact_reference, read_json, sha256_file, write_once_json


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
    directory = ARTIFACTS / "prompt-optimizer"
    record = {
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
