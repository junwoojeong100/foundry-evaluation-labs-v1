"""Local artifact helpers shared by workshop commands."""

import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

from lab.config import Config, LabError
from lab.content import language_metadata, require_content_language
from lab.preflight import save_json


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = Path(os.environ.get("LAB_ARTIFACTS_DIR", str(ROOT / "artifacts"))).expanduser().resolve()


def artifact_reference(path: Path, *, root: Path = ROOT) -> str:
    resolved = path.resolve()
    root = root.resolve()
    return str(resolved.relative_to(root)) if resolved.is_relative_to(root) else str(resolved)


def code_provenance() -> dict:
    sources = {str(path.relative_to(ROOT)): sha256_file(path) for path in sorted((ROOT / "lab").glob("*.py"))}
    packages = {}
    for name in ("azure-ai-projects", "azure-identity", "openai"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "NOT_INSTALLED_IN_THIS_INTERPRETER"
    record = {
        "python_sources_sha256": hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest(),
        "python_sources": sources, "git_commit": None, "worktree_dirty": None,
        "source_mode": "distribution_without_git",
        "runtime": {"python": sys.version.split()[0], "packages": packages},
    }
    if (ROOT / ".git").exists():
        results = []
        for arguments in (["rev-parse", "HEAD"], ["status", "--porcelain", "--untracked-files=all"]):
            result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
            if result.returncode:
                raise LabError("코드 커밋/변경 상태 확인 실패. 확인되지 않은 리비전을 기록하지 않습니다.")
            results.append(result.stdout.strip())
        record.update(git_commit=results[0], worktree_dirty=bool(results[1]), source_mode="git_worktree")
    return record


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


def write_once_json(path: Path, value: dict) -> None:
    """Claim a paid operation before submission, including against concurrent processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise LabError("동시 또는 이전 실행의 요청 기록이 있습니다. 중복 제출하지 않고 중단합니다.") from exc


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
        **language_metadata(),
    }
    if path.exists():
        state = read_json(path)
        if not isinstance(state, dict) or any(state.get(k) != v for k, v in scope.items()):
            raise LabError("기록된 실습 범위와 .env가 다릅니다. 기존 아티팩트를 보존하고 별도 패키지에서 시작하세요.")
        require_content_language(state)
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
