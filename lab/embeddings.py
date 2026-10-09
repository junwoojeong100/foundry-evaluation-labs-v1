"""Real, cached Azure embeddings. Unknown paid submissions are never replayed."""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time

from lab.config import Config, LabError
from lab.content import text as localized_text
from lab.files import code_provenance, read_json
from lab.preflight import model_snapshot, save_json


DIMENSIONS = 1536


def validate_vectors(payload: dict, count: int) -> list[list[float]]:
    if not isinstance(payload, dict):
        raise LabError(localized_text("Embedding 응답은 JSON 객체여야 합니다.", "The embedding response must be a JSON object."))
    entries = payload.get("data")
    if not isinstance(entries, list) or len(entries) != count:
        raise LabError(localized_text(
            "Embedding 응답 수가 입력 수와 다릅니다.", "The number of embedding responses differs from the number of inputs.",
        ))
    if any(not isinstance(entry, dict) or type(entry.get("index")) is not int for entry in entries):
        raise LabError(localized_text(
            "Embedding 응답마다 정수 index가 필요합니다.", "Every embedding response needs an integer index.",
        ))
    if {entry.get("index") for entry in entries} != set(range(count)):
        raise LabError(localized_text(
            "Embedding 응답의 index가 누락되거나 중복되었습니다.", "Embedding response indexes are missing or duplicated.",
        ))
    vectors = []
    for entry in sorted(entries, key=lambda value: value["index"]):
        vector = entry.get("embedding")
        if (
            not isinstance(vector, list) or len(vector) != DIMENSIONS
            or any(type(value) not in (int, float) or not math.isfinite(value) for value in vector)
            or not any(value != 0 for value in vector)
        ):
            raise LabError(localized_text(
                "실제 1536차원의 유한한 비영 벡터가 필요합니다. 가짜/빈 벡터는 허용하지 않습니다.",
                "A real, finite, non-zero 1536-dimension vector is required. Fake or empty vectors are not accepted.",
            ))
        vectors.append(vector)
    return vectors


def embed(config: Config, texts: list[str], cache_path: Path) -> dict:
    if not config.embedding or not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
        raise LabError(localized_text(
            "EMBEDDING_DEPLOYMENT와 비어 있지 않은 embedding 입력이 필요합니다.",
            "EMBEDDING_DEPLOYMENT and non-empty embedding input are required.",
        ))
    deployment = model_snapshot(config, config.embedding)
    if deployment["model"].get("name") != "text-embedding-3-small":
        raise LabError(localized_text(
            "이 인덱스의 동결 계약은 text-embedding-3-small/1536입니다. 자동 대체하지 않습니다.",
            "This index's frozen contract is text-embedding-3-small/1536. It is never replaced automatically.",
        ))
    contract = {
        "endpoint": config.openai_endpoint, "deployment": deployment,
        "dimensions": DIMENSIONS,
        "input_sha256": hashlib.sha256(json.dumps(texts, ensure_ascii=False).encode()).hexdigest(),
        "count": len(texts),
    }
    if cache_path.exists():
        previous = read_json(cache_path)
        if previous.get("contract") != contract:
            raise LabError(localized_text(
                "기존 embedding 실행과 입력/모델/범위가 다릅니다. 기존 기록을 보존해야 합니다.",
                "The input, model or scope differs from the earlier embedding run. Preserve the existing record.",
            ))
        if previous.get("status") != "completed":
            raise LabError(localized_text(
                "이 embedding 요청은 실패 또는 결과 불명입니다. 원격 요청을 확인하기 전 재호출하지 않습니다.",
                "This embedding request failed or its outcome is unknown. Do not call it again before checking the remote request.",
            ))
        validate_vectors(previous["response"], len(texts))
        return previous
    from azure.identity import get_bearer_token_provider
    from openai import APIError, OpenAI
    from azure.core.exceptions import AzureError
    from lab.auth import credential_for

    record = {"kind": "LIVE_AZURE_EMBEDDING", "contract": contract, "status": "submitting",
              "code": code_provenance(),
              "started_at": datetime.now(timezone.utc).isoformat(), "cost": {"status": "NOT_OBSERVED"}}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with cache_path.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
    except FileExistsError as exc:
        raise LabError(localized_text(
            "동시 embedding 실행을 차단했습니다. 기존 기록을 확인해야 합니다.",
            "A concurrent embedding run was blocked. Check the existing record.",
        )) from exc
    started = time.perf_counter()
    try:
        with credential_for(config) as credential:
            with OpenAI(
                base_url=f"{config.openai_endpoint}/openai/v1/",
                api_key=get_bearer_token_provider(credential, "https://ai.azure.com/.default"),
                max_retries=0, timeout=120,
            ) as client:
                response = client.embeddings.create(
                    model=config.embedding, input=texts, dimensions=DIMENSIONS, encoding_format="float",
                )
                record["response"] = response.model_dump(mode="json")
                record["request_id"] = getattr(response, "_request_id", None)
                save_json(cache_path, record)
                validate_vectors(record["response"], len(texts))
    except (APIError, AzureError, LabError) as exc:
        record.update(status="failed_or_unknown", error={"type": type(exc).__name__, "message": str(exc)})
        save_json(cache_path, record)
        raise
    record.update(status="completed", latency_ms=(time.perf_counter() - started) * 1000,
                  completed_at=datetime.now(timezone.utc).isoformat())
    save_json(cache_path, record)
    return record
