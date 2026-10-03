"""Prepare honest local handoffs; these operations do not run cloud services."""

import json
from pathlib import Path
import shutil
import subprocess
import sys

from lab.config import LabError
from lab.content import content_path, language_metadata, require_content_language, selected_language
from lab.files import ARTIFACTS, ROOT, read_json, read_jsonl, safe_run_dir, sha256_file, write_jsonl
from lab.preflight import save_json


def validate_generated_data() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_datasets.py"), "--check", "--language", selected_language()],
        cwd=ROOT, check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise LabError("데이터 검증 실패:\n" + result.stdout + result.stderr)


def prepare_optimizer(run_id: str) -> Path:
    from lab.governance import assert_dataset_use

    validate_generated_data()
    run_dir = safe_run_dir(run_id)
    metadata = read_json(run_dir / "metadata.json")
    require_content_language(metadata)
    if metadata.get("split") != "dev" or metadata.get("status") != "completed":
        raise LabError("Optimizer에는 오류 없이 완료된 dev 전체 실행만 사용합니다. test/smoke/부분 실행 금지.")
    if metadata.get("stage") != "iq":
        raise LabError("이 경로는 IQ 연결 후의 dev 실행을 Optimizer의 기준선으로 사용합니다.")
    if metadata.get("retrieval", {}).get("rows_with_tool_output", 0) == 0:
        raise LabError("실제 IQ 도구 출력이 없는 기준선입니다. 도구 연결·권한·지시를 고치고 새 dev 실행을 사용해야 합니다.")
    source = content_path(ROOT, "data/splits/dev.jsonl")
    assert_dataset_use(source, "optimization")
    assert_dataset_use(content_path(ROOT, "data/optimizer/dev.jsonl"), "optimization")
    if metadata["dataset_sha256"] != sha256_file(source):
        raise LabError("dev 데이터가 기준선 실행 이후 변경되었습니다.")
    prompt = ROOT / metadata["prompt_snapshot"]
    if sha256_file(prompt) != metadata["prompt_sha256"]:
        raise LabError("기록된 기준선 프롬프트와 실제 스냅샷이 다릅니다.")
    target = ARTIFACTS / "optimizer"
    if (target / "handoff.json").exists():
        raise LabError("Optimizer 준비 기록이 이미 있습니다. 기존 실험을 보존하고 새 패키지에서 준비해야 합니다.")
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(prompt, target / "input-prompt.txt")
    shutil.copyfile(content_path(ROOT, "data/optimizer/dev.jsonl"), target / "dev-upload.jsonl")
    if (run_dir / "report.md").exists():
        shutil.copyfile(run_dir / "report.md", target / "baseline-report.md")
    save_json(target / "handoff.json", {
        "kind": "agent-optimizer-handoff",
        "status": "PREPARED_NOT_SUBMITTED",
        "source_run_id": run_id,
        "source_split": "dev",
        **language_metadata(),
        "dataset_sha256": sha256_file(source),
        "upload_sha256": sha256_file(target / "dev-upload.jsonl"),
        "input_prompt_sha256": metadata["prompt_sha256"],
        "agent_name": metadata["agent_name"],
        "agent_version": metadata["agent_version"],
        "test_data_included": False,
        "next": f"Continue at guide/{'en/' if selected_language() == 'en' else ''}handbook.md#optimize (step 05): use the Agent Optimizer portal wizard with one instruction-only candidate.",
        "not_created": ["optimizer job", "optimized prompt", "new deployed agent", "improved evaluation score"],
    })
    return target


def prepare_tuning(kind: str) -> Path:
    from lab.governance import assert_dataset_use

    if kind not in {"frontier", "sft"}:
        raise LabError("지원하는 준비 유형은 frontier 또는 sft입니다.")
    validate_generated_data()
    target = ARTIFACTS / "tuning" / kind
    if target.exists():
        raise LabError(f"이미 존재하는 학습 준비 기록은 덮어쓰지 않습니다: {target}")
    target.mkdir(parents=True, exist_ok=True)
    manifest = {
        **language_metadata(),
        "kind": f"{kind}-preparation",
        "status": "PREPARED_NOT_SUBMITTED",
        "region_requested": "northcentralus",
        "test_data_included": False,
        "frontier_entitlement": "NOT_VERIFIED",
        "training_job_id": None,
        "trained_model_id": None,
        "deployment_name": None,
        "files": {},
        "required_before_submission": [
            "Feature entitlement and supported NCUS model/version/training type",
            "Data-processing geography and approval for the selected training SKU",
            "Training, evaluation and ongoing hosting budget approval",
            "Correct service-specific schema and holdout separation",
            "Base-model baseline, calibrated grader if applicable, and rollback owner",
        ],
    }
    for split in ("train", "validation"):
        if kind == "frontier":
            source = content_path(ROOT, "data/splits") / f"{split}.jsonl"
            destination = target / f"{split}.jsonl"
            note = "Neutral lab examples, NOT a claimed Frontier Tuning API upload schema."
        else:
            source = content_path(ROOT, "data/tuning") / f"sft-{split}.jsonl"
            destination = target / f"sft-{split}.jsonl"
            note = "General supervised fine-tuning messages format; NOT Frontier Tuning."
        assert_dataset_use(source, "training")
        if kind == "sft":
            destination.write_text(source.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")
        else:
            shutil.copyfile(source, destination)
        manifest["files"][destination.name] = {
            "rows": len(read_jsonl(destination)),
            "sha256": sha256_file(destination),
            "bytes": destination.stat().st_size,
            "schema_note": note,
        }
    save_json(target / "manifest.json", manifest)
    save_json(target / "experiment-brief.json", {
        "goal": "Improve grounded support behavior, clarification and escalation without claiming an action was executed.",
        "knowledge_strategy": "Current policy stays in Foundry IQ; do not train the model to memorize changing policy.",
        "candidate_behavior": ["JSON response contract", "correct route", "explicit uncertainty", "no false completed actions"],
        "reward_design": "Format alone is insufficient. Use task correctness, reference support and critical-rule failures.",
        "evaluation": "Choose on dev/validation, then compare base and candidate on the same sealed test set.",
        "outcome": "NO_TRAINING_EXECUTED",
    })
    return target
