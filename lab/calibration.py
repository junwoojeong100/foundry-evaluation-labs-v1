"""Versioned, independent policy and retrieval judges; no SDK imports on load.

Authored reference labels are calibration targets, never human review and never
model inputs. Paid entry points require explicit confirmation from the CLI; that
confirmation does not replace the workshop's separate budget/data approval.
Each directory is a one-attempt ledger. Unknown outcomes are not resubmitted.
Captured-run business and managed judges share an exclusive judge-attempt.json
claim; interrupted or completed claims are never released or taken over.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
from uuid import uuid4

from lab.config import LabError
from lab.evidence import observed_model_drift, strict_json_loads, validate_case
from lab.files import ARTIFACTS, ROOT, code_provenance, safe_run_dir, sha256_file


CONTRACT_VERSION = "atlas-evaluation-v1"
DEFINITIONS = {
    "policy": "policy-correctness.v1.json",
    "retrieval": "retrieval-groundedness.v1.json",
}
METRICS = ("policy_correctness", "groundedness", "relevance")
JUDGE_ATTEMPT_CLAIM = "judge-attempt.json"


def credential_for(config):
    from lab.auth import credential_for as factory
    return factory(config)


def AIProjectClient(**kwargs):
    from azure.ai.projects import AIProjectClient as factory
    return factory(**kwargs)


def model_snapshot(config, deployment):
    from lab.preflight import model_snapshot as snapshot
    return snapshot(config, deployment)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def safe_id(value: str, label: str = "id") -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise LabError(f"{label}: use 1..64 letters, digits, underscores or hyphens.")
    return value


def read_json(path: Path):
    try:
        return strict_json_loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LabError(f"Invalid or missing JSON evidence: {path}: {exc}") from exc


def read_jsonl(path: Path) -> list[dict]:
    try:
        lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
        if not lines or any(not line.strip() for line in lines):
            raise ValueError("empty JSONL or blank row")
        rows = [strict_json_loads(line) for line in lines]
        if any(not isinstance(row, dict) for row in rows):
            raise ValueError("JSONL rows must be objects")
        return rows
    except (OSError, ValueError) as exc:
        raise LabError(f"Invalid or missing JSONL evidence: {path}: {exc}") from exc


def save_json(path: Path, value, *, exclusive: bool = False) -> None:
    """Persist checkpoints atomically, or create an immutable artifact once."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if exclusive:
        try:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise LabError(f"Existing evidence is immutable; do not resubmit: {path}") from exc
        return
    pending = path.with_name(f".{path.name}.{uuid4().hex}.pending")
    try:
        with pending.open("x", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        pending.replace(path)
    finally:
        pending.unlink(missing_ok=True)


def ensure_judge_unclaimed(directory: Path) -> None:
    """Block both evaluation paths, including legacy interrupted submissions."""
    if (directory / JUDGE_ATTEMPT_CLAIM).exists():
        raise LabError(f"Shared Judge attempt already claimed; no rejudge or claim takeover: {directory / JUDGE_ATTEMPT_CLAIM}")
    for artifact in ("business-judge", "managed-eval.json", "judge-contract.json", "judge-scores.json"):
        if (directory / artifact).exists():
            raise LabError(f"Existing/unfinished Judge attempt at {directory / artifact}; preserve it, do not switch evaluation paths.")
    metadata = read_json(directory / "metadata.json")
    if any(metadata.get(field) is not None for field in ("judge", "managed_evaluation", "judge_execution_status")):
        raise LabError("Captured metadata already records a Judge attempt; recover its ledger, never claim another path.")


def claim_judge_attempt(directory: Path, run_id: str, *, project_endpoint: str,
                        evaluation_path: str, contract: dict) -> dict:
    """Claim once before any paid request; the immutable claim is never released."""
    if evaluation_path not in {"business-judge", "managed-eval"}:
        raise LabError("Unknown Judge evaluation path.")
    if directory.resolve() != safe_run_dir(run_id).resolve():
        raise LabError("Judge claim directory differs from the identified capture run.")
    ensure_judge_unclaimed(directory)
    metadata = read_json(directory / "metadata.json")
    if metadata.get("run_id") != run_id or metadata.get("project_endpoint") != project_endpoint:
        raise LabError("Judge claim run/project identity differs from the captured metadata.")
    claim = {
        "schema_version": "shared-judge-attempt-v1", "created_at": now(),
        "run_id": run_id, "run_directory": str(directory.resolve()),
        "project_endpoint": project_endpoint, "evaluation_path": evaluation_path,
        "evaluator_contract": deepcopy(contract), "evaluator_contract_sha256": digest(contract),
        "dataset_sha256": metadata["dataset_sha256"], "row_ids": metadata["row_ids"],
        "outputs_sha256": sha256_file(directory / "outputs.jsonl"),
    }
    save_json(directory / JUDGE_ATTEMPT_CLAIM, claim, exclusive=True)
    return claim


def validate_judge_claim(directory: Path, run_id: str, *, project_endpoint: str,
                         evaluation_path: str, contract: dict) -> None:
    """Read-only validation; legacy collection never acquires/replaces a claim."""
    path = directory / JUDGE_ATTEMPT_CLAIM
    if not path.exists():
        return
    claim = read_json(path)
    expected = {
        "schema_version": "shared-judge-attempt-v1", "run_id": run_id,
        "run_directory": str(directory.resolve()), "project_endpoint": project_endpoint,
        "evaluation_path": evaluation_path, "evaluator_contract_sha256": digest(contract),
        "evaluator_contract": contract,
    }
    if not isinstance(claim, dict) or any(
        canonical(claim.get(key)) != canonical(value) for key, value in expected.items()
    ):
        raise LabError("Judge collection cannot take over another run/path/evaluator claim.")
    metadata = read_json(directory / "metadata.json")
    if (
        claim.get("outputs_sha256") != sha256_file(directory / "outputs.jsonl")
        or claim.get("dataset_sha256") != metadata.get("dataset_sha256")
        or claim.get("row_ids") != metadata.get("row_ids")
    ):
        raise LabError("Captured sources differ from the immutable Judge attempt claim.")


def evaluator_contract() -> dict:
    definitions = {
        kind: read_json(ROOT / "config/evaluators" / filename)
        for kind, filename in DEFINITIONS.items()
    }
    for kind, definition in definitions.items():
        if (
            not isinstance(definition, dict)
            or not definition.get("version")
            or definition.get("scale") != [1, 5]
            or definition.get("pass_threshold") != 4
            or not isinstance(definition.get("instructions"), str)
            or not definition["instructions"].strip()
            or not isinstance(definition.get("output_schema"), dict)
        ):
            raise LabError(f"Invalid versioned evaluator definition: {kind}")
    return {
        "contract_version": CONTRACT_VERSION,
        "definitions": definitions,
        "definition_hashes": {
            kind: sha256_file(ROOT / "config/evaluators" / filename)
            for kind, filename in DEFINITIONS.items()
        },
        "policy_sha256": sha256_file(ROOT / "data/knowledge/documents.json"),
        "scale": [1, 5],
        "groundedness_semantics": "actual_agent_retrieval_only/no_policy_fallback",
        "reference_labels_sent_to_judge": False,
        "human_review_state": "not_reviewed",
    }


def load_fixtures(path: Path | None = None) -> list[dict]:
    path = ROOT / "data/calibration/fixtures.jsonl" if path is None else Path(path)
    rows = read_jsonl(path)
    if len(rows) < 10:
        raise LabError("Calibration requires at least 10 authored positive/negative fixtures.")
    documents = read_json(ROOT / "data/knowledge/documents.json")
    policy = {doc["id"]: doc["content"] for doc in documents}
    ids, labels = set(), set()
    result = []
    for row in rows:
        identifier = safe_id(row.get("id"), "fixture.id")
        if identifier in ids:
            raise LabError(f"Duplicate calibration fixture: {identifier}")
        ids.add(identifier)
        reference = row.get("reference_labels")
        if not isinstance(reference, dict) or set(reference) != set(METRICS):
            raise LabError(f"{identifier}: complete reference_labels are required.")
        for name, value in reference.items():
            if type(value) is not bool and not (name == "groundedness" and value is None):
                raise LabError(f"{identifier}: reference labels are booleans; only absent retrieval is null.")
        labels.add(reference["policy_correctness"])
        context = row.get("retrieved_context")
        if not isinstance(context, str) or (bool(context.strip()) != (reference["groundedness"] is not None)):
            raise LabError(f"{identifier}: retrieval and its applicability label disagree.")
        if row.get("human_review_state") != "not_reviewed":
            raise LabError("Authored reference fixtures cannot claim human review.")
        if row.get("reference_provenance", {}).get("source") != "authored-calibration-reference":
            raise LabError("Calibration labels need explicit authored reference provenance.")
        policy_ids = row.get("policy_ids")
        if not isinstance(policy_ids, list) or not policy_ids or any(key not in policy for key in policy_ids):
            raise LabError(f"{identifier}: known authoritative policy IDs are required.")
        case = {
            "id": identifier, "group_id": row.get("group_id"), "split": "dev",
            "query": row.get("query"),
            "context": "\n\n".join(f"[{key}]\n{policy[key]}" for key in policy_ids),
            "ground_truth": canonical({
                "answer": row.get("reference_answer"), "route": row.get("expected_route"),
                "citations": policy_ids, "needs_human": row.get("expected_route") == "escalate",
            }),
            "expected_route": row.get("expected_route"), "required_citations": policy_ids,
            "tags": row.get("tags", []),
        }
        try:
            validate_case(case)
        except ValueError as exc:
            raise LabError(f"{identifier}: {exc}") from exc
        if not isinstance(row.get("response"), dict) or not isinstance(row.get("reference_answer"), str):
            raise LabError(f"{identifier}: response object and reference answer are required.")
        result.append({**deepcopy(row), "case": case, "raw_output": canonical(row["response"])})
    if labels != {True, False}:
        raise LabError("Calibration must include both correct and incorrect reference responses.")
    return result


def judge_payloads(case: dict, raw_output: str, retrieved_context: str, *, conversation=None) -> dict:
    """Allowlist inputs. The retrieval judge cannot see policy, labels or route."""
    validate_case(case)
    if not isinstance(raw_output, str) or not isinstance(retrieved_context, str):
        raise LabError("Judge response and observed retrieval must be strings.")
    reference = strict_json_loads(case["ground_truth"])
    if not isinstance(reference, dict) or not isinstance(reference.get("answer"), str):
        raise LabError("The policy judge requires a reference answer JSON projection.")
    return {
        "policy": {
            "query": case["query"], "response": raw_output,
            "authoritative_policy": case["context"],
            "reference_answer": reference["answer"], "expected_route": case["expected_route"],
            "conversation": [] if conversation is None else deepcopy(conversation),
        },
        "retrieval": {
            "query": case["query"], "response": raw_output, "retrieved_context": retrieved_context,
        },
    }


def parse_judgment(raw: str, kind: str) -> dict:
    value = strict_json_loads(raw)
    fields = {"policy_correctness", "relevance", "critical_failure", "reason"} if kind == "policy" else {"groundedness", "reason"}
    if kind not in DEFINITIONS or not isinstance(value, dict) or set(value) != fields:
        raise ValueError("Judge JSON must contain exactly the declared evaluator fields.")
    for name in fields - {"reason", "critical_failure"}:
        if type(value[name]) is not int or not 1 <= value[name] <= 5:
            raise ValueError(f"{name} must be an integer from 1 through 5.")
    if "critical_failure" in fields and type(value["critical_failure"]) is not bool:
        raise ValueError("critical_failure must be a boolean.")
    if not isinstance(value["reason"], str) or not value["reason"].strip():
        raise ValueError("Judge reason must be a nonempty string.")
    return value


def judge_case(client, deployment: str, case: dict, raw_output: str, retrieved_context: str,
               *, contract: dict | None = None, conversation=None, checkpoint=None) -> dict:
    contract = evaluator_contract() if contract is None else contract
    payloads = judge_payloads(case, raw_output, retrieved_context, conversation=conversation)
    result = {
        "id": case["id"], "judge": {
            **dict.fromkeys(METRICS), "error": None, "metric_errors": {}, "critical_failure": None,
        },
        "requests": {}, "access_blockers": [],
    }
    for kind, payload in payloads.items():
        if result["access_blockers"]:
            for metric in contract["definitions"][kind]["metrics"]:
                result["judge"]["metric_errors"][metric] = "not_attempted_after_access_blocker"
            result["requests"][kind] = {"status": "not_attempted", "reason": "access_blocker"}
            if checkpoint:
                checkpoint(deepcopy(result))
            continue
        if kind == "retrieval" and not retrieved_context.strip():
            result["judge"]["metric_errors"]["groundedness"] = "retrieval_not_observed"
            result["requests"][kind] = {"status": "not_applicable", "reason": "retrieval_not_observed"}
            if checkpoint:
                checkpoint(deepcopy(result))
            continue
        definition = contract["definitions"][kind]
        request = {"status": "submitting", "response_id": None, "input_sha256": digest(payload), "created_at": now()}
        result["requests"][kind] = request
        if checkpoint:
            checkpoint(deepcopy(result))
        try:
            response = client.responses.create(
                model=deployment,
                input=[
                    {"role": "system", "content": definition["instructions"]},
                    {"role": "user", "content": canonical(payload)},
                ],
                text={"format": {
                    "type": "json_schema", "name": f"atlas_{kind}_v1",
                    "strict": True, "schema": definition["output_schema"],
                }},
                max_output_tokens=2048, store=True,
            )
            request.update(status="received", response_id=response.id)
            if checkpoint:
                checkpoint(deepcopy(result))
            if not isinstance(response.id, str) or not response.id.strip():
                raise ValueError("Judge response has no usable remote ID.")
            request["response"] = response.model_dump(mode="json")
            request["raw_output"] = response.output_text or ""
            if request["response"].get("status") != "completed":
                raise ValueError(f"Judge response not complete: {request['response'].get('status')}")
            parsed = parse_judgment(request["raw_output"], kind)
            request.update(status="completed", judgment=parsed)
            result["judge"].update({key: value for key, value in parsed.items() if key != "reason"})
            result["judge"].setdefault("reasons", {})[kind] = parsed["reason"]
        except Exception as exc:
            # The ledger already precedes this external call. Never retry a POST.
            request.update(
                status=(
                    "pending_response" if request.get("response", {}).get("status") in {"queued", "in_progress"}
                    else "invalid_result" if request.get("response_id") else "unknown_outcome"
                ),
                error=f"{type(exc).__name__}: {exc}",
            )
            for metric in definition["metrics"]:
                result["judge"]["metric_errors"][metric] = request["error"]
            if getattr(exc, "status_code", None) in (401, 403):
                request["status"] = "blocked_access"
                result["access_blockers"].append(request["error"])
        if checkpoint:
            checkpoint(deepcopy(result))
    return result


def _unavailable(identifier: str, reason: str) -> dict:
    return {
        "id": identifier,
        "judge": {**dict.fromkeys(METRICS), "error": reason, "metric_errors": {}, "critical_failure": None},
        "requests": {}, "access_blockers": [],
    }


def summarize_calibration(fixtures: list[dict], records: list[dict]) -> dict:
    """Agreement uses all applicable references, not only successful requests."""
    ids = [fixture["id"] for fixture in fixtures]
    indexed = {row["id"]: row for row in records}
    if len(ids) != len(set(ids)) or len(indexed) != len(records) or not set(indexed) <= set(ids):
        raise LabError("Calibration result IDs must be unique members of the fixture set.")
    rows, critical_false_accepts = [], []
    for fixture in fixtures:
        record = deepcopy(indexed.get(fixture["id"], _unavailable(fixture["id"], "not_attempted")))
        judge = record["judge"]
        observed, matches = {}, {}
        for metric, expected in fixture["reference_labels"].items():
            value = judge.get(metric)
            usable = (
                judge.get("error") is None and not judge.get("metric_errors", {}).get(metric)
                and type(value) in (int, float) and math.isfinite(value) and 1 <= value <= 5
            )
            observed[metric] = value >= 4 if usable else None
            matches[metric] = observed[metric] is expected if expected is not None else (
                value is None and not fixture["retrieved_context"].strip()
            )
        if (
            "critical" in fixture["tags"] and not fixture["reference_labels"]["policy_correctness"]
            and observed["policy_correctness"] is True
        ):
            critical_false_accepts.append(fixture["id"])
        critical_flag_agreement = (
            judge.get("critical_failure") is (not fixture["reference_labels"]["policy_correctness"])
            if "critical" in fixture["tags"] else True
        )
        rows.append({
            **record, "reference_labels": deepcopy(fixture["reference_labels"]),
            "observed_labels": observed, "agreement": matches,
            "critical_flag_agreement": critical_flag_agreement,
            "all_agree": all(matches.values()) and critical_flag_agreement, "human_review_state": "not_reviewed",
        })
    measurements = {}
    for metric in METRICS:
        applicable = [row for row in rows if row["reference_labels"][metric] is not None]
        scored = [row for row in applicable if row["observed_labels"][metric] is not None]
        counts = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}
        for row in scored:
            expected, observed = row["reference_labels"][metric], row["observed_labels"][metric]
            counts[("true_" if expected == observed else "false_") + ("positive" if observed else "negative")] += 1
        agreements = counts["true_positive"] + counts["true_negative"]
        kappa = None
        if scored:
            size = len(scored)
            expected_positive = sum(row["reference_labels"][metric] for row in scored) / size
            observed_positive = sum(row["observed_labels"][metric] for row in scored) / size
            chance = expected_positive * observed_positive + (1 - expected_positive) * (1 - observed_positive)
            if chance < 1:
                kappa = (agreements / size - chance) / (1 - chance)
        measurements[metric] = {
            **counts, "total_fixture_count": len(rows), "applicable_count": len(applicable),
            "not_applicable_count": len(rows) - len(applicable),
            "scored_count": len(scored), "missing_count": len(applicable) - len(scored),
            "agreement_count": agreements,
            "agreement_rate": agreements / len(applicable) if applicable else None,
            "scored_only_cohen_kappa": kappa,
        }
    return {
        "sample_count": len(rows), "rows": rows, "metrics": measurements,
        "all_dimensions_agreement_rate": sum(row["all_agree"] for row in rows) / len(rows) if rows else None,
        "disagreement_ids": [row["id"] for row in rows if not row["all_agree"]],
        "critical_false_accept_count": len(critical_false_accepts),
        "critical_false_accept_ids": critical_false_accepts,
        "quality_status": "PASS" if rows and all(row["all_agree"] for row in rows) and not critical_false_accepts else "HOLD",
        "human_review_state": "not_reviewed",
        "manual_operational_approval": "not_granted",
        "limitations": [
            "Authored reference agreement is not independent human approval or a production accuracy estimate.",
            "Missing/error judgments remain in the applicable denominator; no score is fabricated.",
            "Kappa uses scored pairs only; coverage and full-denominator agreement must also be read.",
        ],
    }


def _execute(config, cases: list[dict], records: list[dict], directory: Path, contract: dict,
             *, before_call=None) -> tuple[list[dict], dict]:
    observations = {
        "execution_mode": "LIVE", "execution_status": "running", "access_blockers": [],
        "execution_errors": [],
        "model_snapshot": None, "model_snapshot_after": None,
    }
    results = []
    operation = "identity"
    try:
        with credential_for(config) as credential:
            operation = "model_snapshot"
            observations["model_snapshot"] = model_snapshot(config, config.judge)
            if before_call:
                operation = "frozen_contract"
                before_call(observations["model_snapshot"])
            operation = "judge_execution"
            with AIProjectClient(endpoint=config.project_endpoint, credential=credential) as project:
                with project.get_openai_client(max_retries=0, timeout=120.0) as client:
                    for case, capture in zip(cases, records, strict=True):
                        if capture.get("error"):
                            result = _unavailable(case["id"], f"capture_error: {capture['error']}")
                        elif observations["access_blockers"]:
                            result = _unavailable(case["id"], "not_attempted_after_access_blocker")
                        else:
                            result = judge_case(
                                client, config.judge, case, capture["raw_output"], capture["retrieved_context"],
                                contract=contract, conversation=capture.get("turns"),
                                checkpoint=lambda row: save_json(directory / "raw" / f"{case['id']}.json", row),
                            )
                        results.append(result)
                        observations["access_blockers"].extend(result.get("access_blockers", []))
                        save_json(directory / "raw" / f"{case['id']}.json", result)
                        save_json(directory / "checkpoint.json", {"observations": observations, "records": results})
            observations["model_snapshot_after"] = model_snapshot(config, config.judge)
            observations["execution_status"] = (
                "invalid_model_drift" if observations["model_snapshot"] != observations["model_snapshot_after"]
                else "blocked_access" if observations["access_blockers"]
                else "blocked_unknown_outcome" if any(
                    request.get("status") in {"unknown_outcome", "pending_response"}
                    for row in results for request in row["requests"].values()
                )
                else "completed_with_errors" if any(
                    row["judge"].get("error") or any(
                        value != "retrieval_not_observed" for value in row["judge"].get("metric_errors", {}).values()
                    ) for row in results
                ) else "completed"
            )
    except Exception as exc:
        access = operation == "identity" or getattr(exc, "status_code", None) in (401, 403)
        observations["execution_status"] = (
            "blocked_access" if access else "blocked_contract" if operation == "frozen_contract" else "execution_error"
        )
        observations["access_blockers" if access else "execution_errors"].append(f"{type(exc).__name__}: {exc}")
    completed = {result["id"] for result in results}
    results.extend(
        _unavailable(case["id"], "not_attempted: " + "; ".join(observations["access_blockers"] + observations["execution_errors"]))
        for case in cases if case["id"] not in completed
    )
    save_json(directory / "checkpoint.json", {"observations": observations, "records": results})
    return results, observations


def run_calibration(config, calibration_id: str, *, confirm: bool = False,
                    fixtures_path: Path | None = None) -> dict:
    if confirm is not True:
        raise LabError("Paid Judge calibration requires --confirm and separate budget/data approval.")
    safe_id(calibration_id, "calibration-id")
    path = ROOT / "data/calibration/fixtures.jsonl" if fixtures_path is None else Path(fixtures_path)
    fixtures, contract = load_fixtures(path), evaluator_contract()
    directory = ARTIFACTS / "calibration" / calibration_id
    try:
        directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise LabError("Calibration ID already attempted. Preserve errors; do not rejudge this attempt.") from exc
    metadata = {
        "calibration_id": calibration_id, "created_at": now(), "execution_mode": "LIVE",
        "code": code_provenance(),
        "fixtures_sha256": sha256_file(path), "fixtures_path": str(path.resolve()),
        "evaluator_contract": contract, "evaluator_sha256": digest(contract),
        "judge_deployment": config.judge, "project_endpoint": config.project_endpoint,
        "identity": {"expected_user": config.expected_user, "tenant_id": config.tenant_id,
                     "subscription_id": config.subscription_id, "provider": "verified_AzureCliCredential"},
        "row_ids": [fixture["id"] for fixture in fixtures],
        "human_review_state": "not_reviewed", "manual_operational_approval": "not_granted",
    }
    save_json(directory / "metadata.json", metadata, exclusive=True)
    records, observations = _execute(
        config, [fixture["case"] for fixture in fixtures],
        [{"raw_output": fixture["raw_output"], "retrieved_context": fixture["retrieved_context"]} for fixture in fixtures],
        directory, contract,
    )
    report = {**summarize_calibration(fixtures, records), "metadata": metadata, **observations}
    if observations["execution_status"] != "completed":
        report["quality_status"] = "HOLD"
    save_json(directory / "report.json", report, exclusive=True)
    return report


def score_captured_run(config, run_id: str, *, confirm: bool = False) -> dict:
    """One configured Judge attempt over captured outputs, never an agent call."""
    if confirm is not True:
        raise LabError("Paid Judge scoring requires --confirm and separate budget/data approval.")
    from lab.batch import dataset_for_metadata

    directory = safe_run_dir(run_id)
    metadata = read_json(directory / "metadata.json")
    if observed_model_drift(metadata):
        raise LabError("Cannot judge a capture with terminal observed model drift.")
    if metadata.get("run_id") != run_id or metadata.get("status") not in {"completed", "completed_with_errors"}:
        raise LabError("Judge scoring requires a complete, identified capture including failed rows.")
    if metadata.get("project_endpoint") != config.project_endpoint:
        raise LabError("Captured project differs from configured Judge project.")
    if metadata.get("judge") is not None or (directory / "judge-scores.json").exists() or (directory / "managed-eval.json").exists():
        raise LabError("This capture already has a Judge attempt; rejudging is not allowed.")
    ensure_judge_unclaimed(directory)
    dataset = dataset_for_metadata(metadata)
    if sha256_file(dataset) != metadata["dataset_sha256"]:
        raise LabError("Captured dataset changed.")
    cases = {case["id"]: case for case in read_jsonl(dataset)}
    captures = read_jsonl(directory / "outputs.jsonl")
    if metadata.get("outputs_sha256") and sha256_file(directory / "outputs.jsonl") != metadata["outputs_sha256"]:
        raise LabError("Captured outputs changed after execution.")
    if [row["id"] for row in captures] != metadata["row_ids"] or len(set(metadata["row_ids"])) != len(captures):
        raise LabError("All attempted capture IDs must match; failed rows cannot be dropped.")
    selected = [cases[row["id"]] for row in captures]
    from lab.evidence import score_row
    documents = read_json(ROOT / "data/knowledge/documents.json")
    known = {row["id"] for row in documents}
    for case, capture in zip(selected, captures, strict=True):
        if "error" not in capture or not isinstance(capture.get("raw_output"), str) or not isinstance(capture.get("retrieved_context"), str):
            raise LabError("Captured response, error and actual retrieval fields are required.")
        scored = score_row(case, capture["raw_output"], known_citations=known, error=capture["error"])
        if not scored["schema_valid"] and capture["error"] is None:
            capture["error"] = "capture_schema_invalid: " + "; ".join(scored["schema_errors"] or [scored["parse_error"]])
    contract = evaluator_contract()
    if metadata.get("freeze_id"):
        from lab.governance import validate_frozen_run
        validate_frozen_run(metadata["freeze_id"], run_id)
    claim_judge_attempt(
        directory, run_id, project_endpoint=config.project_endpoint,
        evaluation_path="business-judge", contract=contract,
    )
    attempt = directory / "business-judge"
    try:
        attempt.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise LabError("Judge attempt already exists, including unknown outcomes; no resubmission.") from exc
    save_json(attempt / "contract.json", contract, exclusive=True)
    submission = {
        "run_id": run_id, "created_at": now(), "evaluator_sha256": digest(contract),
        "code": code_provenance(),
        "dataset_sha256": metadata["dataset_sha256"],
        "outputs_sha256": sha256_file(directory / "outputs.jsonl"),
        "row_ids": metadata["row_ids"], "freeze_id": metadata.get("freeze_id"),
        "freeze_sha256": metadata.get("freeze_sha256"),
        "sample_contract_sha256": metadata.get("sample_contract_sha256"),
    }
    save_json(attempt / "submission.json", submission, exclusive=True)

    def check_snapshot(snapshot):
        if metadata.get("freeze_id"):
            validate_frozen_run(metadata["freeze_id"], run_id, judge_snapshot=snapshot)

    records, observations = _execute(config, selected, captures, attempt, contract, before_call=check_snapshot)
    scores = {row["id"]: row["judge"] for row in records}
    if observations["execution_status"] in {"invalid_model_drift", "execution_error", "blocked_access", "blocked_contract"}:
        for values in scores.values():
            values["error"] = observations["execution_status"] + ": " + "; ".join(observations["access_blockers"] + observations["execution_errors"])
    save_json(directory / "judge-scores.json", scores, exclusive=True)
    judge = {
        "model_deployment": config.judge, "prompt_sha256": digest(contract), "scale": [1, 5],
        "version": CONTRACT_VERSION, "settings": contract,
        "provenance": {
            "source_artifact": "business-judge/contract.json", "sha256": digest(contract),
            "model_snapshot": observations["model_snapshot"],
            "service_version_pinned": False,
            "limitation": "Public prompt and deployment snapshots, not private runtime attestation.",
        },
    }
    metadata.update(judge=judge, evaluation_contract_version=CONTRACT_VERSION,
                    judge_execution_status=observations["execution_status"])
    metadata["access_blockers"] = observations["access_blockers"]
    save_json(directory / "metadata.json", metadata)
    report = {
        **observations, "sample_count": len(captures),
        "submission_sha256": digest(submission), "evaluator_sha256": digest(contract),
        "judge_scores_sha256": sha256_file(directory / "judge-scores.json"),
        "scored_count": sum(values.get("policy_correctness") is not None and not values.get("error") for values in scores.values()),
        "manual_operational_approval": "not_granted",
    }
    save_json(attempt / "report.json", report, exclusive=True)
    return report
