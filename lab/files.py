"""Local artifact helpers shared by workshop commands."""

import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4

from lab.config import Config, LabError
from lab.preflight import save_json


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> object:
    if not path.is_file():
        raise LabError(f"필요한 파일이 없습니다: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LabError(f"올바른 JSON 파일이 아닙니다: {path}:{exc.lineno}") from exc


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise LabError(f"필요한 JSONL 파일이 없습니다: {path}")
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            raise LabError(f"JSONL 빈 행: {path}:{line_number}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LabError(f"JSONL 문법 오류: {path}:{line_number}") from exc
        if not isinstance(row, dict):
            raise LabError(f"JSONL 각 행은 객체여야 합니다: {path}:{line_number}")
        rows.append(row)
    if not rows:
        raise LabError(f"비어 있는 데이터셋: {path}")
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def safe_run_dir(run_id: str) -> Path:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", run_id):
        raise LabError("run-id는 1~64자의 영문·숫자·하이픈·밑줄이어야 합니다.")
    return ARTIFACTS / "runs" / run_id


def workspace(config: Config, *, create: bool = False) -> dict:
    path = ARTIFACTS / "workspace.json"
    scope = {
        "project_id": config.project_id,
        "search_id": config.search_id,
        "prefix": config.prefix,
    }
    if path.exists():
        state = read_json(path)
        if not isinstance(state, dict) or any(state.get(k) != v for k, v in scope.items()):
            raise LabError("기록된 실습 범위와 .env가 다릅니다. 기존 아티팩트를 보존하고 별도 패키지에서 시작하세요.")
        return state
    if not create:
        raise LabError("실습 작업 기록이 없습니다. 에이전트 생성 단계부터 진행하세요.")
    state = {**scope, "workspace_id": str(uuid4()), "created": []}
    save_json(path, state)
    return state


def record_created(config: Config, record: dict) -> None:
    state = workspace(config)
    state["created"].append(record)
    save_json(ARTIFACTS / "workspace.json", state)
