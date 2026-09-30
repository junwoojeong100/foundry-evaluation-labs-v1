"""Create an allowlisted, credential-free summary from a private lab environment."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(environment: Path) -> dict:
    config, manifest = read(environment / "config.json"), read(environment / "manifest.json")
    artifacts = environment / "artifacts"
    resources = []
    for key, value in manifest["resources"].items():
        resources.append({
            "key": key, "relative_resource_id": value["id"].split("/resourceGroups/", 1)[-1],
            "type": value["type"], "state": value["status"], "sku": value.get("sku"),
        })
    runs = {}
    for directory in sorted((artifacts / "runs").glob("*")):
        if not directory.is_dir():
            continue
        smoke = directory / "model-smoke.json"
        metadata_path = directory / "metadata.json"
        if smoke.exists():
            value = read(smoke)
            runs[directory.name] = {key: value.get(key) for key in (
                "kind", "status", "response_id", "deployment", "model_snapshot",
                "usage", "latency_ms", "started_at", "cost",
            )}
            runs[directory.name]["source_sha256"] = digest(smoke)
        if not metadata_path.exists():
            continue
        metadata = read(metadata_path)
        record = {key: metadata.get(key) for key in (
            "status", "stage", "target_type", "source_split", "split", "created_at", "completed_at",
            "row_ids", "agent_name", "agent_version", "model_deployment", "model_snapshot",
            "parameters", "dataset_sha256", "prompt_sha256", "knowledge_sha256",
            "outputs_sha256", "retrieval", "evaluation_contract_version", "judge_execution_status",
            "freeze_id", "holdout_id", "sample_contract_sha256", "pair_id", "arm", "technique",
        )}
        code = metadata.get("code", {})
        record["code"] = {key: code.get(key) for key in (
            "git_commit", "worktree_dirty", "python_sources_sha256", "runtime",
        )}
        output = directory / "outputs.jsonl"
        if output.exists():
            rows = [json.loads(line) for line in output.read_text().splitlines()]
            record["responses"] = [{
                "case_id": row["id"], "response_id": row.get("response_id"),
                "response_status": (row.get("response") or {}).get("status"),
                "error_present": bool(row.get("error")),
                "actual_retrieved_characters": len(row.get("retrieved_context", "")),
                "raw_output_sha256": hashlib.sha256(row.get("raw_output", "").encode()).hexdigest(),
                "turns": [{key: turn.get(key) for key in (
                    "turn_index", "input_source", "scripted_user_source", "state", "response_id", "previous_response_id",
                )} for turn in row.get("turns", [])],
            } for row in rows]
        summary = directory / "summary.json"
        if summary.exists():
            record["metrics"] = read(summary)["metrics"]
            record["summary_sha256"] = digest(summary)
        managed = directory / "managed-eval.json"
        if managed.exists():
            record["managed_evaluation"] = {key: read(managed).get(key) for key in (
                "eval_id", "run_id", "status", "collection_status",
            )}
        observations = sorted((directory / "control-plane").glob("*.json"))
        if observations:
            value = read(observations[-1])
            record["control_plane"] = {key: value.get(key) for key in (
                "status", "checked_at", "observed_rows", "expected_responses", "response_coverage",
                "model_rows", "tool_rows", "evaluation_rows", "policy_enforcement", "error_absence_claim",
            )}
        runs[directory.name] = record
    calibrations = {}
    for path in sorted((artifacts / "calibration").glob("*/report.json")):
        value = read(path)
        calibrations[path.parent.name] = {
            **{key: value.get(key) for key in (
                "execution_mode", "execution_status", "quality_status", "sample_count", "metrics",
                "disagreement_ids", "critical_false_accept_count", "model_snapshot",
            )},
            "evaluator_sha256": value["metadata"]["evaluator_sha256"],
            "fixture_sha256": value["metadata"]["fixtures_sha256"],
            "created_at": value["metadata"]["created_at"], "report_sha256": digest(path),
            "human_review_state": "not_reviewed",
        }
    training = {"status": "NOT_SUBMITTED"}
    state_path = artifacts / "tuning/sft/sft-state.json"
    if state_path.exists():
        state = read(state_path)
        job = state["job"]
        response = job.get("response", {})
        training = {
            "technique": "Foundry SFT, not Frontier Tuning",
            "status": state["status"], "base_model": state["base_model"],
            "training_type": state["training_type"], "job_id": job.get("id"),
            "job_status": job.get("status"), "terminal_verified": job.get("terminal_verified"),
            "fine_tuned_model": job.get("fine_tuned_model"),
            "created_at": response.get("created_at"), "finished_at": response.get("finished_at"),
            "trained_tokens": response.get("trained_tokens"), "state_sha256": digest(state_path),
            "file_ids": {key: value.get("id") for key, value in state["files"].items()},
            "deployments": {key: {"status": value.get("status"), "request": value["request"],
                                 "cost": value.get("cost")}
                            for key, value in state.get("deployments", {}).items()},
        }
    knowledge = {}
    setup = artifacts / "knowledge/setup.json"
    if setup.exists():
        value = read(setup)
        knowledge = {key: value.get(key) for key in (
            "status", "names", "documents_sha256", "payload_sha256", "retrieval",
            "uploaded_documents", "embedding_usage", "probe_scope",
        )}
        knowledge["vector_hybrid_probes"] = [read(path) for path in sorted((artifacts / "knowledge/probes").glob("*/result.json"))]
        knowledge["iq_plan_probes"] = [{
            "response_sha256": digest(path), "reference_count": len(read(path).get("references", [])),
            "activity": read(path).get("activity", []),
        } for path in sorted((artifacts / "knowledge/probes").glob("*/iq-response.json"))]
    optimizer = {}
    prompt = artifacts / "prompt-optimizer/result.json"
    if prompt.exists():
        value = read(prompt)
        optimizer["prompt"] = {key: value.get(key) for key in (
            "kind", "status", "created_at", "request_sha256", "response_sha256",
            "original_sha256", "candidate_sha256", "remote_job_id", "job_id_note",
        )}
    for name, filename in (("agent_submission", "agent-optimizer-submit-response.json"),
                           ("agent_result", "agent-optimizer-final.json")):
        path = artifacts / "optimizer" / filename
        if path.exists():
            value = read(path)
            optimizer[name] = {key: value.get(key) for key in (
                "id", "status", "created_at", "updated_at", "completed_at",
                "best_candidate_id", "baseline_score", "best_score",
            )}
            optimizer[name]["error_present"] = bool(value.get("error"))
            optimizer[name]["source_sha256"] = digest(path)
            if name == "agent_result":
                optimizer[name]["progress"] = value.get("progress")
                optimizer[name]["result"] = {key: value.get("result", {}).get(key) for key in (
                    "baseline", "best", "candidate_ids", "token_usage", "latency_usage",
                )}
    native = artifacts / "optimizer/native-rule-comparison.json"
    if native.exists():
        optimizer["native_rule_comparison"] = read(native)
    governance = []
    for path in sorted((artifacts / "governance/freezes").glob("*.json")):
        value = read(path)
        governance.append({key: value.get(key) for key in (
            "freeze_id", "created_at", "stage", "execution_mode", "content_sha256", "hashes",
            "sample_contract", "calibration_state", "manual_review_state", "manual_operational_approval",
        )})
    holdouts = {}
    for path in sorted((artifacts / "governance/holdouts").glob("*/metadata.json")):
        value = read(path)
        holdouts[path.parent.name] = {key: value.get(key) for key in (
            "holdout_id", "freeze_id", "created_at", "generated_at", "sample_count",
            "dataset_sha256", "provenance", "disjointness", "sample_contract_sha256", "purpose",
        )}
    reviews = []
    for path in sorted((artifacts / "governance/reviews").glob("*.json")):
        value = read(path)
        reviews.append({key: value.get(key) for key in (
            "review_id", "actor_type", "created_at", "manual_review_state", "manual_operational_approval",
        )})
    gate_observation = environment / "fresh-gate-stderr.local.txt"
    cost_file = environment / "cost-management-response.local.json"
    cost_query = None
    if cost_file.exists():
        cost_data = read(cost_file).get("properties", {})
        cost_query = {
            "source_sha256": digest(cost_file),
            "reported_rows": cost_data.get("rows", []),
            "columns": cost_data.get("columns", []),
            "billing_lag_warning": "No rows or a zero total does not prove zero incurred cost.",
        }
    return {
        "kind": "SANITIZED_LIVE_SUMMARY_NOT_RAW_TELEMETRY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "resource_group": config["names"]["resource_group"], "region": config["location"],
        "bootstrap_phase": manifest["phase"], "resources": resources,
        "source_manifest_sha256": digest(environment / "manifest.json"),
        "runs": runs, "calibrations": calibrations, "knowledge": knowledge,
        "optimizers": optimizer, "sft": training, "freezes": governance, "holdouts": holdouts, "reviews": reviews,
        "fresh_gate": {
            "enforcement_checked": gate_observation.exists(),
            "status": "BLOCKED_CALIBRATION_HOLD" if governance and any(
                item["calibration_state"]["quality_status"] == "HOLD" for item in governance
            ) else "NOT_VERIFIED",
            "run_created": (artifacts / "runs/optimized-fresh").exists(),
            "attempt_created": (artifacts / "governance/attempts/selected-v2.json").exists(),
        },
        "human_operational_approval": "NOT_GRANTED",
        "frontier": {"status": "NOT_VERIFIED", "ordinary_sft_is_not_frontier": True},
        "retention": "PRESERVE_FOR_REVIEW_NO_DELETION_AUTHORIZED",
        "cost": {
            "actual_invoice": None, "status": "NOT_OBSERVED_NOT_ZERO",
            "reference_currency": "USD", "search_basic_per_hour": 0.101,
            "fine_tuned_standard_hosting_per_hour": 1.7,
            "reference_prices_are_not_an_invoice": True,
            "cost_management_observation": cost_query,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.environment.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(args.out)


if __name__ == "__main__":
    main()
