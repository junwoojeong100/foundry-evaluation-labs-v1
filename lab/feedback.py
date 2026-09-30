"""Create review-only dev feedback from actual failures, never train on final tests."""

from datetime import datetime, timezone
import hashlib
import json

from lab.config import LabError
from lab.files import ARTIFACTS, read_json, read_jsonl, safe_run_dir, sha256_file, write_once_json


def prepare_feedback(run_id: str, feedback_id: str) -> dict:
    from lab.batch import dataset_for_metadata

    safe_run_dir(feedback_id)
    source = safe_run_dir(run_id)
    metadata = read_json(source / "metadata.json")
    if metadata.get("source_split") != "dev" or metadata.get("split") != "dev" or metadata.get("freeze_id"):
        raise LabError("Feedback에는 dev 전체 실행만 사용합니다. 최종 test/fresh holdout을 학습 후보로 전환하지 않습니다.")
    summary = read_json(source / "summary.json")
    dataset = dataset_for_metadata(metadata)
    if sha256_file(dataset) != metadata["dataset_sha256"]:
        raise LabError("Feedback 원본 데이터가 실행 이후 바뀌었습니다.")
    cases = {case["id"]: case for case in read_jsonl(dataset)}
    outputs = {row["id"]: row for row in read_jsonl(source / "outputs.jsonl")}
    if metadata.get("outputs_sha256") != sha256_file(source / "outputs.jsonl"):
        raise LabError("실제 응답 해시가 다릅니다. 변경된 답변을 운영 피드백으로 포장하지 않습니다.")
    candidates = []
    for row in summary["rows"]:
        judge = row.get("judge") or {}
        if not (row["rule_failures"] or row["api_error"] or judge.get("error") or judge.get("metric_errors")
                or any(type(judge.get(metric)) in (int, float) and judge[metric] < 4
                       for metric in ("policy_correctness", "groundedness", "relevance"))):
            continue
        case, capture = cases[row["id"]], outputs[row["id"]]
        candidates.append({
            "source_case_id": row["id"], "source_group_id": case["group_id"],
            "query": case["query"], "observed_response": capture["raw_output"],
            "response_id": capture.get("response_id"), "source_run_id": run_id,
            "source_response_sha256": hashlib.sha256(capture["raw_output"].encode()).hexdigest(),
            "rule_failures": row["rule_failures"], "judge_scores": {
                metric: judge.get(metric) for metric in ("policy_correctness", "groundedness", "relevance")
            },
            "review_actor_type": "ai", "human_review": "PENDING", "ground_truth": None,
            "purpose": "REVIEW_ONLY_NOT_TRAINING_OR_INDEPENDENT_SAMPLE",
        })
    result = {
        "kind": "TRACE_LINKED_DEV_FEEDBACK_REVIEW_QUEUE", "feedback_id": feedback_id,
        "created_at": datetime.now(timezone.utc).isoformat(), "source_run_id": run_id,
        "source_summary_sha256": sha256_file(source / "summary.json"),
        "candidate_count": len(candidates), "candidates": candidates,
        "automatic_dataset_promotion": False, "human_operational_approval": "NOT_GRANTED",
        "next": "Human review, data consent and duplicate/group checks are required before a new dev version. Final tests remain excluded.",
    }
    write_once_json(ARTIFACTS / "feedback" / f"{feedback_id}.json", result)
    return result
