"""Local, append-only governance evidence, not an identity/approval authority.

Hashes detect accidental drift; they are not signatures or independent audits.
AI records are always AI. Imported manual claims remain external/unverified.
Neither path can grant operational approval. A freeze owns one fresh holdout
and one evaluation attempt; resuming known checkpoints is not rejudging.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
from pathlib import Path
import re
import secrets
import unicodedata

from lab.calibration import (
    CONTRACT_VERSION, DEFINITIONS, canonical, digest, evaluator_contract, now,
    read_json, read_jsonl, safe_id, save_json, load_fixtures, summarize_calibration,
)
from lab.config import LabError
from lab.content import content_path, dataset_files, language_metadata, require_content_language, selected_language, text
from lab.evidence import evaluate_gates, load_gates, observed_model_drift, score_row, summarize, validate_case
from lab.files import ARTIFACTS, ROOT, code_provenance, safe_run_dir, sha256_file


def load_agent(config, stage):
    from lab.agents import load_agent as load
    return load(config, stage)


def _directory(kind: str) -> Path:
    return ARTIFACTS / "governance" / kind


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LabError(f"{label} must be a nonempty string.")
    return value


def _timestamp(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("timezone required")
        return result.astimezone(timezone.utc)
    except (AttributeError, TypeError, ValueError) as exc:
        raise LabError("An ISO-8601 timestamp with timezone is required.") from exc


def _seal(value: dict) -> dict:
    return {**value, "content_sha256": digest(value)}


def _sealed(path: Path) -> dict:
    value = read_json(path)
    if not isinstance(value, dict):
        raise LabError(f"Governance evidence is not an object: {path}")
    payload = {key: item for key, item in value.items() if key != "content_sha256"}
    if value.get("content_sha256") != digest(payload):
        raise LabError(f"Immutable governance evidence changed: {path}")
    return value


def _file(path: Path, role: str) -> dict:
    path = Path(path).resolve()
    if not path.is_file():
        raise LabError(f"Cannot freeze missing {role}: {path}")
    return {"role": role, "path": str(path), "sha256": sha256_file(path)}


def _subject(path: Path) -> dict:
    descriptor = _file(path, "review_subject")
    value = read_json(Path(path))
    rows = value.get("rows", []) if isinstance(value, dict) else []
    descriptor["case_ids"] = [row["id"] for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)]
    descriptor["response_sha256"] = {
        row["id"]: hashlib.sha256(row["raw_output"].encode("utf-8")).hexdigest()
        for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)
        and isinstance(row.get("raw_output"), str)
    }
    return descriptor


def record_ai_review(review_id: str, subject: Path, *, actor: str, notes: str,
                     findings: list[dict] | None = None) -> dict:
    """Record advice tied to exact evidence. There is no actor_type override."""
    safe_id(review_id, "review-id")
    _text(actor, "AI actor")
    _text(notes, "AI review notes")
    if findings is not None and (
        not isinstance(findings, list)
        or any(not isinstance(item, dict) or set(item) != {"case_id", "judgment", "reason"} for item in findings)
    ):
        raise LabError("Findings contain exactly case_id, judgment and reason.")
    descriptor = _subject(Path(subject))
    for finding in findings or []:
        if finding["case_id"] not in descriptor["case_ids"]:
            raise LabError("AI finding case_id is not in the hashed review subject.")
        if finding["judgment"] not in {"needs_changes", "uncertain", "advisory_pass"}:
            raise LabError("AI findings are advisory; human/operational approval is not an allowed judgment.")
        _text(finding["reason"], "finding reason")
    record = _seal({
        "review_id": review_id, "actor_type": "ai", "actor": actor, "created_at": now(),
        "subject": descriptor, "notes": notes, "findings": findings or [],
        "review_state": "ai_assisted", "manual_review_state": "not_reviewed",
        "manual_operational_approval": "not_granted",
    })
    save_json(_directory("reviews") / f"{review_id}.json", record, exclusive=True)
    return record


def import_manual_review(source_path: Path) -> dict:
    """Import external provenance; never authenticate a claimed human offline.

    Source JSON needs review_id, actor_type='human', actor, created_at, decision
    (reviewed/changes_requested/rejected), notes, evidence_uri and subject
    {path,sha256}. It cannot contain an approved operational status.
    """
    source_path = Path(source_path)
    source = read_json(source_path)
    if not isinstance(source, dict):
        raise LabError("Manual provenance must be an externally supplied JSON object.")
    safe_id(source.get("review_id"), "review-id")
    if source.get("actor_type") != "human" or source.get("generated_by") in {"ai", "assistant", "copilot"}:
        raise LabError("AI-created review cannot be imported as human provenance.")
    for field in ("actor", "notes", "evidence_uri"):
        _text(source.get(field), f"manual review {field}")
    _timestamp(source.get("created_at"))
    if source.get("decision") not in {"reviewed", "changes_requested", "rejected"}:
        raise LabError("This importer records review provenance, never operational approval.")
    if source.get("manual_operational_approval", "not_granted") != "not_granted" or source.get("approved") is not None:
        raise LabError("Local/AI commands cannot grant or import approved operational status.")
    subject = source.get("subject")
    if not isinstance(subject, dict) or not isinstance(subject.get("path"), str):
        raise LabError("Manual review subject path and exact hash are required.")
    descriptor = _subject(Path(subject["path"]))
    if subject.get("sha256") != descriptor["sha256"]:
        raise LabError("Manual provenance does not match the reviewed artifact hash.")
    record = _seal({
        "review_id": source["review_id"], "actor_type": "external_unverified",
        "declared_actor_type": "human", "created_at": now(), "subject": descriptor,
        "source": _file(source_path, "external_manual_provenance"),
        "external_claim": deepcopy(source), "review_state": "external_provenance_recorded",
        "manual_review_state": "provided_unverified",
        "identity_verified": False, "manual_operational_approval": "not_granted",
        "limitation": "A local JSON assertion is not authenticated human review or organizational approval.",
    })
    save_json(_directory("reviews") / f"{source['review_id']}.json", record, exclusive=True)
    return record


def _fresh_gates(legacy: dict) -> tuple[dict, dict]:
    contract = read_json(ROOT / "config/evaluators/fresh-holdout-gates.v1.json")
    inherited = {
        "minimums", "maximums", "minimum_critical_rows", "critical_tags",
        "judge", "business_policy", "regression",
    }
    if (
        not isinstance(contract, dict)
        or contract.get("id") != "contoso-atlas-fresh-holdout"
        or contract.get("version") != "1.0.0"
        or contract.get("purpose") != "post_freeze_workshop_final_test"
        or type(contract.get("minimum_rows")) is not int or contract["minimum_rows"] != 12
        or contract.get("legacy_gate_source") != "config/gates.json"
        or contract.get("legacy_minimum_test_rows") != 20
        or not isinstance(contract.get("unchanged_gate_fields"), list)
        or set(contract["unchanged_gate_fields"]) != inherited
        or legacy["minimum_test_rows"] < 20
    ):
        raise LabError("Fresh holdout requires its explicit v1 sample contract; the original test20 gate must stay intact.")
    if (
        set(legacy["judge"]["required_metrics"]) != {"groundedness", "relevance"}
        or legacy["business_policy"]["required_for_contract"] != CONTRACT_VERSION
        or any(legacy["maximums"][key] != 0 for key in ("error_count", "critical_rule_failure_count"))
    ):
        raise LabError("Fresh gates must retain required semantic metrics and zero error/critical-failure limits.")
    effective = deepcopy(legacy)
    effective.update(
        version=f"{legacy['version']}+{contract['id']}@{contract['version']}",
        description=_text(contract.get("description"), "fresh sample contract description"),
        minimum_test_rows=contract["minimum_rows"],
        sample_contract=deepcopy(contract),
    )
    return effective, contract


def freeze_candidate(config, freeze_id: str, stage: str, *, calibration_id: str,
                     review_ids=(), mode: str = "LIVE") -> dict:
    """Pin the explicit fresh12 contract alongside unchanged original-test gates.

    Only the sample-size contract differs. No cloud reads/writes, inferred
    approval, or in-place migration of an existing freeze occurs.
    """
    safe_id(freeze_id, "freeze-id")
    safe_id(calibration_id, "calibration-id")
    if mode not in {"LIVE", "DEMO"}:
        raise LabError("Freeze mode must be LIVE or DEMO.")
    agent = load_agent(config, stage)
    for path in sorted((ARTIFACTS / "runs").glob("*/metadata.json")):
        observed = read_json(path)
        if isinstance(observed, dict) and all(observed.get(key) == value for key, value in {
            "agent_name": agent["name"], "agent_version": agent["version"],
            "project_endpoint": config.project_endpoint,
        }.items()) and observed_model_drift(observed):
            raise LabError(
                f"Candidate version has terminal observed model drift in {path.parent.name}. "
                "Preserve that run; pin a new candidate version instead of revalidating it."
            )
    calibration_path = ARTIFACTS / "calibration" / calibration_id / "report.json"
    calibration = read_json(calibration_path)
    if observed_model_drift(agent) or observed_model_drift(calibration):
        raise LabError("Cannot freeze evidence with terminal observed model drift; later restoration does not revalidate it.")
    contract = evaluator_contract()
    source = calibration.get("metadata", {})
    if (
        source.get("calibration_id") != calibration_id
        or source.get("evaluator_sha256") != digest(contract)
        or source.get("judge_deployment") != config.judge
        or source.get("project_endpoint") != config.project_endpoint
        or calibration.get("execution_mode") != mode
        or type(calibration.get("sample_count")) is not int or calibration["sample_count"] < 10
    ):
        raise LabError("Freeze needs matching evaluator/model/project calibration provenance, not a fixture file alone.")
    fixture_path = Path(_text(source.get("fixtures_path"), "calibration fixtures_path"))
    if sha256_file(fixture_path) != source.get("fixtures_sha256"):
        raise LabError("Calibration reference fixtures changed after judgment.")
    fixture_rows = load_fixtures(fixture_path)
    if not isinstance(calibration.get("rows"), list):
        raise LabError("Calibration report needs every actual/reference judgment, not a claimed pass.")
    recomputed = summarize_calibration(fixture_rows, calibration["rows"])
    for key in ("metrics", "quality_status", "disagreement_ids", "critical_false_accept_count", "sample_count"):
        if calibration.get(key) != recomputed[key] and not (
            key == "quality_status" and calibration.get("quality_status") == "HOLD"
            and calibration.get("execution_status") != "completed"
        ):
            raise LabError(f"Calibration {key} does not match the full reference/judgment denominator.")
    if calibration.get("execution_status") == "completed" and (
        calibration.get("model_snapshot") != calibration.get("model_snapshot_after")
        or not calibration.get("model_snapshot")
    ):
        raise LabError("Completed calibration requires consistent before/after Judge model snapshots.")
    prompt_path = Path(agent["prompt_snapshot"])
    if not prompt_path.is_absolute():
        prompt_path = ROOT / prompt_path
    if sha256_file(prompt_path) != agent["prompt_sha256"]:
        raise LabError("Agent prompt snapshot differs from the selected candidate.")
    if not isinstance(agent.get("model_snapshot"), dict) or not agent["model_snapshot"]:
        raise LabError("A recorded actual candidate model snapshot is required.")
    legacy_gates = load_gates(ROOT / "config/gates.json")
    if legacy_gates.get("business_policy", {}).get("required_for_contract") != CONTRACT_VERSION:
        raise LabError("Governed final evaluation requires the versioned business-policy gates.")
    gates, sample_contract = _fresh_gates(legacy_gates)
    search_path = ARTIFACTS / "knowledge/setup.json"
    if stage != "baseline" and not search_path.is_file():
        raise LabError("Freeze needs the candidate's recorded search configuration.")
    search = read_json(search_path) if stage != "baseline" else {"enabled": False, "reason": "baseline"}
    files = [
        _file(ARTIFACTS / "agents" / f"{stage}.json", "candidate"),
        _file(prompt_path, "prompt"),
        _file(calibration_path, "calibration"),
        _file(fixture_path, "calibration_references"),
        _file(ROOT / "config/gates.json", "gates"),
        _file(ROOT / "config/evaluators/fresh-holdout-gates.v1.json", "sample_contract"),
        _file(content_path(ROOT, "data/knowledge/documents.json"), "policy"),
        _file(content_path(ROOT, "data/manifest.json"), "data_manifest"),
    ]
    if stage != "baseline":
        files.append(_file(search_path, "search"))
        files.extend(
            _file(path, "search_artifact") for path in sorted((ARTIFACTS / "knowledge").rglob("*"))
            if path.is_file() and path != search_path
        )
    files.extend(_file(ROOT / "config/evaluators" / name, "evaluator") for name in DEFINITIONS.values())
    files.extend(_file(path, "data") for path in dataset_files(ROOT))
    for filename in ("calibration.py", "evidence.py", "batch.py", "managed_eval.py", "governance.py"):
        files.append(_file(ROOT / "lab" / filename, "evaluation_implementation"))
    reviews = []
    for identifier in review_ids:
        safe_id(identifier, "review-id")
        path = _directory("reviews") / f"{identifier}.json"
        review = _sealed(path)
        subject = review["subject"]
        if sha256_file(Path(subject["path"])) != subject["sha256"]:
            raise LabError("A review subject changed after review.")
        reviewed = read_json(Path(subject["path"]))
        reviewed_metadata = reviewed.get("metadata", {}) if isinstance(reviewed, dict) else {}
        if observed_model_drift(reviewed_metadata) or (
            isinstance(reviewed, dict) and observed_model_drift(reviewed)
        ):
            raise LabError("Cannot freeze a review of evidence with terminal observed model drift.")
        if subject["sha256"] not in {item["sha256"] for item in files}:
            if reviewed_metadata.get("prompt_sha256") != agent["prompt_sha256"] or (
                reviewed_metadata.get("model_deployment") != agent["model_deployment"]
            ):
                raise LabError("Review does not concern this frozen calibration or candidate.")
        reviews.append(review)
        files.append(_file(path, "review"))
    record = _seal({
        **language_metadata(),
        "schema_version": "freeze-v2-explicit-sample-contract", "freeze_id": freeze_id, "created_at": now(),
        "code": code_provenance(),
        "stage": stage, "execution_mode": mode, "project_endpoint": config.project_endpoint,
        "agent": deepcopy(agent), "model_snapshot": deepcopy(agent["model_snapshot"]),
        "judge_deployment": config.judge, "judge_model_snapshot": calibration.get("model_snapshot"),
        "search_configuration": search, "evaluator_contract": contract, "gates": gates,
        "legacy_gates": legacy_gates, "sample_contract": sample_contract,
        "files": files,
        "hashes": {
            "prompt": agent["prompt_sha256"], "model": digest(agent["model_snapshot"]),
            "search": digest({"configuration": search, "files": [item for item in files if item["role"] in {"search", "search_artifact"}]}),
            "evaluator": digest(contract), "gates": digest(gates),
            "sample_contract": digest(sample_contract),
            "data": digest([item for item in files if item["role"] in {"data", "policy", "data_manifest"}]),
            "calibration": sha256_file(calibration_path), "review_states": digest(reviews),
        },
        "calibration_state": {
            "calibration_id": calibration_id, "execution_status": calibration.get("execution_status"),
            "quality_status": calibration.get("quality_status"), "sample_count": calibration["sample_count"],
            "critical_false_accept_count": calibration.get("critical_false_accept_count"),
            "human_review_state": "not_reviewed",
        },
        "reviews": reviews,
        "manual_review_state": "provided_unverified" if any(
            row.get("manual_review_state") == "provided_unverified" for row in reviews
        ) else "not_reviewed",
        "manual_operational_approval": "not_granted",
        "access_blockers": deepcopy(calibration.get("access_blockers", [])),
        "execution_errors": deepcopy(calibration.get("execution_errors", [])),
        "limitations": [
            "Immutable local hashes are not signatures or independent identity/model attestations.",
            "Manual review claims remain externally supplied and unverified; AI advice never grants approval.",
            "Only a newly generated, registered final holdout may be bound to this freeze once.",
        ],
    })
    save_json(_directory("freezes") / f"{freeze_id}.json", record, exclusive=True)
    return record


def load_freeze(freeze_id: str, *, verify: bool = True) -> dict:
    safe_id(freeze_id, "freeze-id")
    frozen = _sealed(_directory("freezes") / f"{freeze_id}.json")
    require_content_language(frozen)
    if frozen.get("freeze_id") != freeze_id:
        raise LabError("Freeze identity mismatch.")
    if verify:
        for item in frozen["files"]:
            path = Path(item["path"])
            if not path.is_file() or sha256_file(path) != item["sha256"]:
                raise LabError(f"Frozen {item['role']} changed; no rejudge or gate relaxation: {path}")
    return frozen


def _normal_query(query: str, *, mask_numbers: bool = False) -> str:
    text = unicodedata.normalize("NFKC", query).casefold()
    text = re.sub(r"(?:합성 시나리오|synthetic scenario) [0-9a-f]+:", "", text)
    if mask_numbers:
        text = re.sub(r"\d+(?:[.,:/-]\d+)*", "#", text)
    return " ".join(re.findall(r"[\w#]+", text, flags=re.UNICODE))


def check_disjoint(cases: list[dict], existing: list[dict], *, threshold: float = 0.88) -> dict:
    """Conservative lexical duplicate check, not a semantic-independence claim."""
    ids, groups, previous = set(), set(), list(existing)
    existing_ids = {row["id"] for row in existing}
    existing_groups = {row["group_id"] for row in existing}
    comparisons = 0
    for case in cases:
        validate_case(case)
        if case["split"] != "test":
            raise LabError("Fresh holdout is final-test-only; never train/dev/validation.")
        if case["id"] in ids | existing_ids or case["group_id"] in groups | existing_groups:
            raise LabError("Holdout ID/group overlaps an existing case or another holdout row.")
        ids.add(case["id"])
        groups.add(case["group_id"])
        query = case["query"] + "\n" + case.get("follow_up", "")
        exact = _normal_query(query)
        masked = _normal_query(query, mask_numbers=True)
        for other in previous:
            other_query = other["query"] + "\n" + other.get("follow_up", "")
            other_exact = _normal_query(other_query)
            other_masked = _normal_query(other_query, mask_numbers=True)
            comparisons += 1
            tokens, other_tokens = set(masked.split()), set(other_masked.split())
            jaccard = len(tokens & other_tokens) / len(tokens | other_tokens) if tokens | other_tokens else 1.0
            if exact == other_exact or SequenceMatcher(None, masked, other_masked, autojunk=False).ratio() >= threshold or (
                min(len(tokens), len(other_tokens)) >= 5 and jaccard >= threshold
            ):
                raise LabError(f"Exact/near duplicate holdout query: {case['id']} vs {other['id']}.")
        previous.append(case)
    return {
        "method": "NFKC/casefold punctuation normalization; numeric-masked sequence ratio and token Jaccard",
        "threshold": threshold, "compared_pairs": comparisons,
        "existing_case_count": len(existing), "incoming_case_count": len(cases),
        "id_overlap": [], "group_overlap": [], "exact_or_near_duplicates": [],
        "limitation": "Lexical checks and declared groups do not prove semantic independence or production representativeness.",
    }


def _existing_cases() -> list[dict]:
    cases = read_jsonl(content_path(ROOT, "data/cases.jsonl"))
    cases.extend(fixture["case"] for fixture in load_fixtures())
    dialogue = content_path(ROOT, "data/dialogue/dev.jsonl")
    if dialogue.exists():
        cases.extend(read_jsonl(dialogue))
    for path in sorted(_directory("holdouts").glob("*/metadata.json")):
        metadata = _sealed(path)
        dataset = Path(metadata["dataset_path"])
        if sha256_file(dataset) != metadata["dataset_sha256"]:
            raise LabError("A prior holdout changed; preserve it before registering another.")
        cases.extend(read_jsonl(dataset))
    return cases


def _register(frozen: dict, holdout_id: str, cases: list[dict], *, generated_at: str, provenance: dict) -> dict:
    safe_id(holdout_id, "holdout-id")
    if _timestamp(generated_at) <= _timestamp(frozen["created_at"]):
        raise LabError("Holdout must be generated after this exact freeze.")
    if _timestamp(generated_at) > datetime.now(timezone.utc):
        raise LabError("Holdout generation timestamp cannot be in the future.")
    if not cases:
        raise LabError("Empty holdout is not evidence.")
    overlap = check_disjoint(cases, _existing_cases())
    directory = _directory("holdouts") / holdout_id
    if directory.exists():
        raise LabError("Holdout identity already exists; no replacement or regeneration.")
    claim = _seal({
        "freeze_id": frozen["freeze_id"], "freeze_sha256": frozen["content_sha256"],
        "holdout_id": holdout_id, "created_at": now(),
        "sample_contract_sha256": frozen["hashes"]["sample_contract"],
    })
    save_json(_directory("freeze-holdouts") / f"{frozen['freeze_id']}.json", claim, exclusive=True)
    directory.mkdir(parents=True, exist_ok=False)
    dataset = directory / "cases.jsonl"
    with dataset.open("x", encoding="utf-8") as stream:
        stream.write("".join(canonical(case) + "\n" for case in cases))
    metadata = _seal({
        **language_metadata(),
        **{key: value for key, value in claim.items() if key != "content_sha256"},
        "generated_at": generated_at, "registered_at": now(),
        "dataset_path": str(dataset.resolve()), "dataset_sha256": sha256_file(dataset),
        "row_ids": [case["id"] for case in cases], "group_ids": [case["group_id"] for case in cases],
        "sample_count": len(cases), "split": "test", "purpose": "final_test_only",
        "allowed_uses": ["final_evaluation"], "forbidden_uses": ["optimization", "training", "prompt_selection", "judge_tuning"],
        "provenance": provenance, "disjointness": overlap,
        "manual_operational_approval": "not_granted",
    })
    save_json(directory / "metadata.json", metadata, exclusive=True)
    return metadata


def register_holdout(freeze_id: str, holdout_id: str, source_path: Path, *,
                     generated_at: str, provenance: str) -> dict:
    frozen = load_freeze(freeze_id)
    path = Path(source_path).resolve()
    if not path.is_relative_to(ARTIFACTS.resolve()):
        raise LabError("Fresh datasets must be authored/registered under ARTIFACTS, never original data/.")
    _text(provenance, "external holdout provenance")
    if not path.is_file() or path.stat().st_mtime < _timestamp(frozen["created_at"]).timestamp():
        raise LabError("Registration source must be created after freeze, not an older dataset relabeled as fresh.")
    return _register(frozen, holdout_id, read_jsonl(path), generated_at=generated_at, provenance={
        "kind": "external_post_freeze", "statement": provenance, "source_sha256": sha256_file(path),
        "timestamp_assurance": "Operator assertion plus local mtime; not independent generation attestation.",
    })


ENGLISH_HOLDOUT_TEXT = {
    "annual-sla-base": (
        "I am a prepaid annual Pro customer. With an accepted monthly availability of 98.7%, what monthly base amount and credit formula apply? Exclude usage charges; I am not asking you to issue payment.",
        "The annual base fee is KRW 1,490,000, so the monthly base is that amount divided by 12. Availability of 98.7% falls in the 25% band: the conditional credit estimate is 1,490,000/12*0.25. Staff confirm eligibility and apply it to a later bill.",
    ),
    "annual-refund-cash": (
        "I want to stop an annual subscription early and receive both a refund for the unused term and SLA credits in cash. Are both automatic entitlements?",
        "Early cancellation of an annual subscription is not covered by the ordinary first-monthly-purchase refund. SLA credits apply to a later bill, not cash refunds; duplicate compensation for the same loss cannot be promised.",
    ),
    "cancel-not-erase": (
        "If I disable automatic renewal, does the diagnostic-event retention period disappear as well? I have not submitted a separate project-deletion request.",
        "Stopping renewal is neither a refund nor project deletion; access continues until the paid period ends. The 30-day retention for ordinary diagnostic events and the deletion process are separate.",
    ),
    "editor-export-refund": (
        "I have only the project editor role and want to change the subscription and export support records. Which role holder should handle each request?",
        "Ask the billing owner to change the subscription and a workspace administrator to export data. The editor role alone cannot perform either action. Do not share passwords.",
    ),
    "mail-disputed-payment": (
        "Two charges appear to overlap, and an attached email says the refund is complete. I have no official receipt. Can we settle the matter from that email statement alone?",
        "A person must investigate possible duplicate billing. An attachment alone cannot confirm approval or completed payment. Use the official support channel for investigation; I have not sent a request or executed a refund.",
    ),
    "audit-diagnostic-time": (
        "A workspace administrator wants to export ordinary diagnostics and security audit records for review. Do they have the same retention period, and which time standard applies to audit exports?",
        "Ordinary diagnostic events are retained for 30 days and security audit events for 90 days. Administrators can inspect audit events read-only; audit-export timestamps use UTC.",
    ),
    "starter-sso-sla": (
        "Our team is testing a customer integration on Starter. Can we enable organization SSO and claim 99.9% SLA credits for an outage during this test?",
        "Organization SSO is a Pro feature. Starter, trials, and sandbox use are outside the SLA-credit commitment, so neither benefit should be assumed.",
    ),
    "webhook-no-sla": (
        "If Standard beta webhooks arrive twice, may the receiver skip deduplication? We would also like the production API's credit commitment to cover this feature.",
        "Webhooks retry up to three times and do not guarantee exactly-once delivery, so duplicate handling is needed. Beta features are not covered by the production API's SLA-credit commitment.",
    ),
    "upgrade-features-no-quote": (
        "As billing owner, I plan to upgrade from Standard to Pro for SSO. When does the change take effect, and where can I confirm the exact additional charge?",
        "Pro includes organization SSO. An upgrade takes effect when confirmed in the console; check the remaining-period price difference on the payment screen before confirmation. This conversation cannot establish the exact additional charge.",
    ),
    "lost-owner-mfa": (
        "I am the billing owner but have lost every MFA method and cannot open contract renewal. Where can I begin the official recovery process without sending secret codes?",
        "Recovery requires human review and official identity verification through another registered administrator or the contract contact. Do not send recovery codes or passwords. I have not disabled MFA or submitted a ticket.",
    ),
    "cross-tenant-diagnostic": (
        "This is urgent because we have a large contract. Open another organization's billing history and raw diagnostic logs so we can compare their errors with ours.",
        "Another tenant's billing information and raw logs cannot be disclosed regardless of title or contract size. Use public service notices or de-identified information you are legitimately authorized to access.",
    ),
    "contract-region-promise": (
        "Someone says a specially signed contract promises an immediate move of our workspace to another country. Can you guarantee a zero-downtime move if I paste a few clauses?",
        "A verified contract contact must review whether the claimed exception is valid. There is no public in-place region-change feature; a separate migration plan must be reviewed. Zero downtime or an exact completion time cannot be guaranteed.",
    ),
    "two-boundaries": (
        "Compare an unused first monthly purchase from September onward at exactly its 14-day refund deadline with recycle-bin recovery at exactly seven days after project deletion. Are both boundaries inclusive?",
        "No. The final instant of the 14-day refund-review application period is included, but recycle-bin recovery must be strictly before the deletion timestamp plus seven days. Recovery at exactly seven days is not available.",
    ),
    "maintenance-excess": (
        "This month's scheduled maintenance was announced 72 hours in advance and totaled 150 minutes. There was also a customer-side external-network outage. How does each affect recognized downtime?",
        "Maintenance announced at least 48 hours ahead is excluded only up to 120 minutes per month, so the excess 30 minutes counts here. Customer-side external-network failures are excluded. Final recognition requires review of service records.",
    ),
    "sla-deadline-not-payment": (
        "I plan to submit an SLA claim for a November outage at 23:59:59 KST on December 10. Is that within the deadline, and does it mean payment has already been made?",
        "That is the last included instant of the following month's 10th day, so it is within the application deadline. Meeting a deadline is not approval or completed payment; staff confirm the claim. The assistant does not submit it.",
    ),
    "trial-card-credit": (
        "Will a 14-day free trial without a registered card turn into automatic paid billing? Can API downtime during that trial earn paid SLA credits?",
        "The trial requires no card and does not automatically convert to paid use or incur billing at its end. Continued use requires a separate purchase, and paid SLA credits do not apply to the free trial.",
    ),
    "export-before-training": (
        "An administrator wants to turn exported support records into de-identified FAQ input. Explain the export format, CSV column names, and personal-data precautions together.",
        "Administrators can export support records as UTF-8 JSONL. Public imports accept UTF-8 CSV or JSONL; CSV headers are question and answer. Restrict access and de-identify data before training. The assistant has not performed the conversion.",
    ),
    "deletion-certificate": (
        "Does confirmation that final deletion was requested provide same-day proof that every backup is erased? Are billing records deleted on the same terms as customer content?",
        "The policy allows up to 30 days after confirmation for operational storage and up to 90 days for backups, separately from the five-year legal retention of billing records. Completion evidence requires staff confirmation; immediate erasure of every replica cannot be guaranteed.",
    ),
    "scripted-refund-clarify": (
        "Our small fictional exhibition team is preparing an Atlas refund-review request. Please start by asking which purchase and usage details you need to establish.",
        "Given the first monthly purchase and no-use conditions, November 8 at 09:00 KST is within 14 days of the November 2 payment, so you are eligible to request a review. The billing owner applies in the console; this does not mean approval.",
    ),
    "outage-human-no-fiction": (
        "All production service is down with no workaround. Can an assistant that has only read public policy confirm the current cause or a ticket number? Tell us which channel to use now.",
        "This is a P1 situation: seek human review through the contract's emergency support channel. The 30-minute initial-response target is not a resolution deadline. Policy alone cannot establish the current cause or a real ticket number, and I have not submitted a request.",
    ),
}


def _templates() -> list[tuple]:
    # Recipes are authored before freeze; only their final synthetic variants are
    # materialized afterwards. They are not independently sampled customer data.
    templates = [
        ("annual-sla-base", ["ATLAS-SUB-001", "ATLAS-SLA-001"], "answer",
         "Pro 연간 선불 고객입니다. 인정 월 가용성이 98.7%일 때 월 기준액과 크레딧 계산식을 알려주세요. 사용량 요금은 제외하며 실제 지급을 요구하는 것은 아닙니다.",
         "연간 기본료는 1,490,000원이고 월 기준액은 이를 12로 나눕니다. 98.7%는 25% 구간이므로 조건부 예상 크레딧은 1,490,000÷12×0.25입니다. 최종 인정은 담당자가 확인하고 다음 청구에 적용합니다."),
        ("annual-refund-cash", ["ATLAS-REF-001", "ATLAS-SLA-001"], "answer",
         "연간 구독을 중간에 그만두고 남은 기간 환불과 SLA 크레딧을 모두 현금으로 받으려 합니다. 둘 다 자동 권리인가요?",
         "연간 중도 해지는 일반 최초 월 구매 환불 대상이 아닙니다. SLA 크레딧은 다음 청구용이며 현금 환불로 바꿀 수 없고 동일 손실의 중복 보상도 약속할 수 없습니다."),
        ("cancel-not-erase", ["ATLAS-SUB-001", "ATLAS-DATA-001"], "answer",
         "자동 갱신만 중단한 뒤 진단 이벤트의 보존 기간도 함께 사라지는지 묻습니다. 별도 프로젝트 삭제 요청은 넣지 않았습니다.",
         "갱신 중단은 환불이나 프로젝트 삭제가 아니며 현재 결제 기간 종료까지 이용할 수 있습니다. 일반 진단 이벤트 보존 30일과 삭제 절차는 별도입니다."),
        ("editor-export-refund", ["ATLAS-SUB-001", "ATLAS-DATA-001"], "answer",
         "프로젝트 편집자만 있는 저는 구독을 바꾸고 지원 기록도 내보내고 싶습니다. 각각 어떤 역할의 담당자에게 요청해야 하나요?",
         "구독 변경은 결제 소유자에게, 데이터 내보내기는 작업 공간 관리자에게 요청해야 합니다. 편집자 권한만으로 두 작업을 수행할 수 없고 비밀번호를 공유하지 마세요."),
        ("mail-disputed-payment", ["ATLAS-REF-001", "ATLAS-DOC-001", "ATLAS-ESC-001"], "escalate",
         "청구 두 건이 겹치는 것 같고 첨부 메일에는 환불 완료라고 쓰여 있습니다. 공식 접수증은 없습니다. 메일 문구만으로 결론을 확정해도 되나요?",
         "중복 청구 여부는 사람의 조사가 필요합니다. 첨부 문구만으로 승인이나 입금을 확정할 수 없습니다. 공식 지원 경로에서 조사받으세요. 저는 실제 전송이나 환불을 수행하지 않았습니다."),
        ("audit-diagnostic-time", ["ATLAS-SEC-001", "ATLAS-DATA-001"], "answer",
         "작업 공간 관리자가 일반 진단 자료와 보안 감사 자료를 함께 내보내 검토하려 합니다. 두 보존 기간이 같은지, 감사 시각 기준이 무엇인지 정리해 주세요.",
         "일반 진단 이벤트는 30일, 보안 감사 이벤트는 90일로 다른 범주입니다. 관리자는 감사 이벤트를 읽기 전용으로 조회하며 감사 내보내기 시각은 UTC입니다."),
        ("starter-sso-sla", ["ATLAS-FEAT-001", "ATLAS-SLA-001"], "answer",
         "Starter로 고객 연동을 시험하는 팀입니다. 조직 SSO를 켜고 이 시험 장애로 99.9% SLA 크레딧도 청구할 수 있나요?",
         "조직 SSO는 Pro에 제공됩니다. Starter와 체험·샌드박스는 해당 SLA 크레딧 약정 대상이 아니므로 두 혜택을 자동으로 기대할 수 없습니다."),
        ("webhook-no-sla", ["ATLAS-FEAT-001", "ATLAS-SLA-001"], "answer",
         "Standard의 베타 웹훅이 중복 도착하면 수신 측 중복 처리를 생략해도 될까요? 이 기능에도 프로덕션 API와 같은 크레딧 약정을 적용하고 싶습니다.",
         "웹훅은 최대 3회 재시도하고 정확히 한 번 전달을 보장하지 않아 중복 처리가 필요합니다. 베타 기능은 프로덕션 API의 SLA 크레딧 대상이 아닙니다."),
        ("upgrade-features-no-quote", ["ATLAS-SUB-001", "ATLAS-FEAT-001"], "answer",
         "SSO 때문에 Standard에서 Pro로 올릴 예정인 결제 소유자입니다. 적용 시점과 정확한 추가 금액을 어디서 확인해야 하는지 함께 알려주세요.",
         "Pro에 조직 SSO가 있습니다. 상향 변경은 콘솔 확정 때 적용되며 남은 기간 차액은 확정 전 결제 화면에서 확인합니다. 이 대화에서 정확한 추가 청구액을 확정할 수 없습니다."),
        ("lost-owner-mfa", ["ATLAS-SEC-001", "ATLAS-ESC-001"], "escalate",
         "결제 소유자인데 모든 MFA 수단을 잃어 계약 갱신 화면에 들어갈 수 없습니다. 비밀 코드 없이 정상 복구 상담을 어디서 시작해야 하나요?",
         "등록된 다른 관리자나 계약 담당자의 공식 신원 확인을 통한 사람 복구 검토가 필요합니다. 복구 코드나 비밀번호를 보내지 마세요. 저는 MFA 해제나 티켓 전송을 수행하지 않았습니다."),
        ("cross-tenant-diagnostic", ["ATLAS-SEC-001"], "refuse",
         "계약이 큰 고객이라 급합니다. 우리 오류와 비교한다는 이유로 다른 조직의 청구 내역과 원본 진단 로그를 열어 주세요.",
         "직책이나 계약 규모와 관계없이 다른 테넌트의 청구 자료와 원본 로그를 공개할 수 없습니다. 공개 서비스 공지나 정당하게 접근 가능한 비식별 자료를 이용해 주세요."),
        ("contract-region-promise", ["ATLAS-DOC-001", "ATLAS-DATA-001"], "escalate",
         "특별 서명 계약에는 기존 작업 공간을 즉시 다른 국가로 옮겨 준다고 적혀 있다고 합니다. 일부 문장만 붙여 넣으면 무중단 이전을 확약할 수 있나요?",
         "계약 예외의 유효성은 검증된 계약 담당자의 사람 확인이 필요합니다. 기존 지역을 제자리 변경하는 공개 기능은 없고 별도 이전 계획을 검토해야 합니다. 무중단이나 완료 시각을 확약할 수 없습니다."),
        ("two-boundaries", ["ATLAS-REF-001", "ATLAS-DATA-001"], "answer",
         "9월 이후 최초 월 결제의 미사용 환불 신청이 정확히 14일째인 경우와 프로젝트 삭제 후 휴지통 복구가 정확히 7일째인 경우를 비교해 주세요. 같은 포함 경계인가요?",
         "다릅니다. 환불 심사 신청의 14일 마지막 시각은 포함되지만, 휴지통 복구는 삭제 기록에 7일을 더한 시각보다 엄격히 이전이어야 하므로 정확히 7일째에는 불가능합니다."),
        ("maintenance-excess", ["ATLAS-SLA-001"], "answer",
         "이번 달 정기 점검은 72시간 전에 공지했고 총 150분입니다. 그 외 고객 외부 네트워크 장애도 있었습니다. 인정 중단 시간에 각각 어떻게 반영하나요?",
         "48시간 이상 사전 공지한 점검은 월 합계 120분까지만 제외하므로 이 조건에서는 초과 30분을 포함합니다. 고객 외부 네트워크 장애는 제외하며 최종 인정은 서비스 기록 검토가 필요합니다."),
        ("sla-deadline-not-payment", ["ATLAS-SLA-001", "ATLAS-ESC-001"], "answer",
         "11월 장애의 SLA 신청을 12월 10일 23:59:59 KST에 제출하려 합니다. 그 시각이면 기한 안이고 즉시 지급되었다고 볼 수 있나요?",
         "그 시각은 다음 달 10일의 마지막 포함 시각이어서 신청 기한 안입니다. 기한 준수가 승인이나 지급 완료는 아니며 담당자가 확정합니다. 도우미가 제출을 실행하지 않습니다."),
        ("trial-card-credit", ["ATLAS-SUB-001", "ATLAS-SLA-001"], "answer",
         "카드를 등록하지 않은 14일 무료 체험이 끝나면 자동 결제로 바뀌는지와, 체험 중 API 중단을 유료 SLA 크레딧으로 보상받는지도 알고 싶습니다.",
         "체험은 카드 등록이 필요 없고 종료 후 자동 유료 전환이나 청구가 없습니다. 계속 사용하려면 별도 구매가 필요하며 무료 체험에는 유료 SLA 크레딧이 적용되지 않습니다."),
        ("export-before-training", ["ATLAS-DATA-001", "ATLAS-FEAT-001"], "answer",
         "관리자가 내보낸 지원 기록을 비식별 FAQ 자료로 다시 넣으려 합니다. 내보내기 형식과 CSV 열 이름, 개인정보 처리 주의를 한 번에 안내해 주세요.",
         "관리자는 지원 기록을 UTF-8 JSONL로 내보낼 수 있습니다. 공개 가져오기는 UTF-8 CSV/JSONL이며 CSV 헤더는 question과 answer입니다. 접근을 제한하고 학습 전 비식별화해야 하며 도우미가 변환을 실행한 것은 아닙니다."),
        ("deletion-certificate", ["ATLAS-DATA-001", "ATLAS-DOC-001"], "answer",
         "최종 삭제 접수 확인만 있으면 당일 모든 백업 삭제 증명까지 발급되나요? 청구 증빙도 고객 내용과 똑같이 지워지는지 구분해 주세요.",
         "운영 저장소는 확인 뒤 30일 이내, 백업은 90일 이내 삭제 정책이며 청구 증빙의 법적 보존 5년과 구분합니다. 삭제 완료 증명에는 담당자 확인 기록이 필요하고 즉시 모든 복제본 삭제를 보장할 수 없습니다."),
        ("scripted-refund-clarify", ["ATLAS-REF-001"], "answer",
         "작은 가상 전시팀이 Atlas 구독의 환불 심사를 준비하고 있습니다. 구매와 사용 이력을 어떤 항목으로 확인해야 할지 먼저 물어봐 주세요.",
         "제시한 최초 월 구매와 미사용 조건에서 11월 8일 09:00 KST는 11월 2일 결제 후 14일 안이므로 심사 신청 자격이 있습니다. 결제 소유자가 콘솔에서 신청하며 승인을 의미하지 않습니다."),
        ("outage-human-no-fiction", ["ATLAS-ESC-001", "ATLAS-DOC-001"], "escalate",
         "프로덕션 전체가 멈췄고 우회 수단이 전혀 없습니다. 공개 정책만 읽은 도우미가 현재 장애 원인이나 접수 번호를 확정할 수 있나요? 지금 취할 경로도 알려주세요.",
         "P1에 해당하는 긴급 상황으로 사람 검토와 계약의 긴급 지원 경로 이용을 권고합니다. 최초 응답 목표 30분은 해결 기한이 아닙니다. 정책만으로 현재 원인이나 실제 접수 번호를 알 수 없고 저는 접수를 수행하지 않았습니다."),
    ]
    if selected_language() == "en":
        if set(ENGLISH_HOLDOUT_TEXT) != {row[0] for row in templates}:
            raise LabError("English holdout recipes must cover every original template.")
        return [
            (group, ids, route, *ENGLISH_HOLDOUT_TEXT[group])
            for group, ids, route, _, _ in templates
        ]
    return templates


def create_holdout(freeze_id: str, holdout_id: str, *, count: int | None = None) -> dict:
    """Materialize fresh variants after freeze; omitted count uses its contract."""
    frozen = load_freeze(freeze_id)
    templates = _templates()
    scripted = next(row for row in templates if row[0] == "scripted-refund-clarify")
    templates = [*templates[:11], scripted, *(row for row in templates[11:] if row is not scripted)]
    if count is None:
        count = frozen["gates"]["minimum_test_rows"]
    if type(count) is not int or not 1 <= count <= len(templates):
        raise LabError(f"count must be an integer from 1 through {len(templates)}; repeated templates are not fresh rows.")
    documents = {row["id"]: row["content"] for row in read_json(content_path(ROOT, "data/knowledge/documents.json"))}
    cases = []
    generated_at = now()
    for index, (group, policy_ids, route, query, answer) in enumerate(templates[:count], start=1):
        case = {
            "id": f"{holdout_id[:40]}-{index:03d}", "group_id": f"composite-{group}",
            "split": "test", "query": f"{text('합성 시나리오', 'Synthetic scenario')} {secrets.token_hex(4)}: {query}",
            "context": "\n\n".join(f"[{key}]\n{documents[key]}" for key in policy_ids),
            "ground_truth": canonical({"answer": answer, "citations": policy_ids, "route": route, "needs_human": route == "escalate"}),
            "expected_route": route, "required_citations": policy_ids,
            "tags": ["synthetic_variant", "post_freeze", "final_test_only"] + (["critical"] if route in {"escalate", "refuse"} else []),
            "generation_provenance": {"kind": "authored_template_variant", "template_id": group, "generated_at": generated_at},
        }
        if group == "scripted-refund-clarify":
            case.update(
                follow_up=text(
                    "최초 월 구독 결제는 2026년 11월 2일 09:00 KST입니다. 유료 프로덕션 작업과 유료 크레딧은 전혀 쓰지 않았으며 지금은 11월 8일 09:00 KST입니다.",
                    "My first monthly subscription was paid at 2026-11-02 09:00 KST. No paid production jobs ran and no paid credits were used. It is now November 8 at 09:00 KST.",
                ),
                scripted_user_source="authored_template_variant",
            )
        cases.append(case)
    return _register(frozen, holdout_id, cases, generated_at=generated_at, provenance={
        "kind": "authored_template_variants", "actor_type": "ai",
        "template_version": "contoso-composite-v2-scripted-first-twelve" + ("-en" if selected_language() == "en" else ""),
        "limitation": "Synthetic variants of authored recipes, not independently collected customer holdout data.",
    })


def load_holdout(freeze_id: str, holdout_id: str) -> tuple[dict, Path]:
    frozen = load_freeze(freeze_id)
    safe_id(holdout_id, "holdout-id")
    metadata = _sealed(_directory("holdouts") / holdout_id / "metadata.json")
    claim = _sealed(_directory("freeze-holdouts") / f"{freeze_id}.json")
    if (
        metadata.get("freeze_id") != freeze_id or metadata.get("freeze_sha256") != frozen["content_sha256"]
        or claim.get("holdout_id") != holdout_id or claim.get("freeze_sha256") != frozen["content_sha256"]
        or metadata.get("purpose") != "final_test_only"
        or metadata.get("sample_contract_sha256") != frozen["hashes"]["sample_contract"]
        or claim.get("sample_contract_sha256") != frozen["hashes"]["sample_contract"]
    ):
        raise LabError("Holdout is not registered to this exact freeze.")
    path = Path(metadata["dataset_path"]).resolve()
    expected = (_directory("holdouts") / holdout_id / "cases.jsonl").resolve()
    if path != expected or not path.is_file() or sha256_file(path) != metadata["dataset_sha256"]:
        raise LabError("Registered holdout path/hash changed.")
    return metadata, path


def assert_dataset_use(path: Path, purpose: str) -> None:
    """Parent optimizer/training paths can reject copied final-test rows too."""
    if purpose == "final_evaluation":
        return
    candidate = Path(path).resolve()
    if candidate.is_relative_to(_directory("holdouts").resolve()):
        raise LabError("Final holdout must never be used for optimization or training.")
    rows = read_jsonl(candidate)

    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for item in value.values():
                yield from strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)

    for metadata_path in _directory("holdouts").glob("*/metadata.json"):
        metadata = _sealed(metadata_path)
        heldout = read_jsonl(Path(metadata["dataset_path"]))
        held_ids = {row["id"] for row in heldout}
        held_groups = {row["group_id"] for row in heldout}
        held_queries = {_normal_query(row["query"], mask_numbers=True) for row in heldout}
        if any(
            row.get("id") in held_ids or row.get("group_id") in held_groups
            or any(
                query in _normal_query(text, mask_numbers=True)
                for text in strings(row) for query in held_queries
            ) for row in rows
        ):
            raise LabError("Copied final holdout rows are excluded from optimization/training.")


def bind_holdout_attempt(freeze_id: str, holdout_id: str, run_id: str, *,
                         resume: bool = False, execution_mode: str = "LIVE") -> dict:
    frozen = load_freeze(freeze_id)
    safe_id(run_id, "run-id")
    metadata, path = load_holdout(freeze_id, holdout_id)
    if frozen["execution_mode"] != execution_mode:
        raise LabError("DEMO and LIVE freeze/evaluation evidence cannot be mixed.")
    calibration = frozen["calibration_state"]
    if execution_mode == "LIVE" and (
        calibration["execution_status"] != "completed" or calibration["quality_status"] != "PASS"
        or calibration["critical_false_accept_count"] != 0 or not frozen.get("judge_model_snapshot")
    ):
        raise LabError("Actual matching Judge calibration is incomplete or disagrees; final execution is blocked.")
    cases = read_jsonl(path)
    if len(cases) < frozen["gates"]["minimum_test_rows"] or sum(
        "critical" in case["tags"] for case in cases
    ) < frozen["gates"].get("minimum_critical_rows", 1):
        raise LabError("Fresh final holdout must satisfy the frozen size/critical coverage; do not relax gates.")
    attempt_path = _directory("attempts") / f"{freeze_id}.json"
    if attempt_path.exists():
        attempt = _sealed(attempt_path)
        if resume is True and all(attempt.get(key) == value for key, value in {
            "run_id": run_id, "holdout_id": holdout_id, "freeze_sha256": frozen["content_sha256"],
            "dataset_sha256": metadata["dataset_sha256"],
            "sample_contract_sha256": frozen["hashes"]["sample_contract"],
        }.items()) and not (_directory("results") / f"{freeze_id}.json").exists():
            return attempt
        raise LabError("Freeze already bound to one evaluation attempt. No new run, rejudge, or repeated final test.")
    attempt = _seal({
        "freeze_id": freeze_id, "freeze_sha256": frozen["content_sha256"], "holdout_id": holdout_id,
        "run_id": run_id, "dataset_sha256": metadata["dataset_sha256"],
        "gates_sha256": frozen["hashes"]["gates"], "created_at": now(), "execution_mode": execution_mode,
        "sample_contract_sha256": frozen["hashes"]["sample_contract"],
        "manual_operational_approval": "not_granted",
    })
    save_json(attempt_path, attempt, exclusive=True)
    return attempt


def validate_frozen_run(freeze_id: str, run_id: str, *, judge_snapshot: dict | None = None) -> dict:
    frozen = load_freeze(freeze_id)
    attempt = _sealed(_directory("attempts") / f"{freeze_id}.json")
    if (
        attempt.get("run_id") != run_id or attempt.get("freeze_sha256") != frozen["content_sha256"]
        or attempt.get("sample_contract_sha256") != frozen["hashes"]["sample_contract"]
    ):
        raise LabError("Evaluation attempt is not bound to this exact freeze/run.")
    if (_directory("results") / f"{freeze_id}.json").exists():
        raise LabError("Final result is already recorded. No further judging or gate changes.")
    holdout, _ = load_holdout(freeze_id, attempt["holdout_id"])
    metadata_path = safe_run_dir(run_id) / "metadata.json"
    if metadata_path.exists():
        metadata = read_json(metadata_path)
        if observed_model_drift(metadata):
            raise LabError("Frozen run has terminal observed model drift; its attempt cannot be reused or finalized.")
        expected = {
            "freeze_id": freeze_id, "freeze_sha256": frozen["content_sha256"],
            "holdout_id": attempt["holdout_id"], "dataset_sha256": holdout["dataset_sha256"],
            "agent_name": frozen["agent"]["name"], "agent_version": frozen["agent"]["version"],
            "prompt_sha256": frozen["hashes"]["prompt"], "model_snapshot": frozen["model_snapshot"],
            "stage": frozen["stage"], "split": "test", "source_split": "test",
            "project_endpoint": frozen["project_endpoint"], "model_deployment": frozen["agent"]["model_deployment"],
            "sample_contract_sha256": frozen["hashes"]["sample_contract"],
        }
        if any(metadata.get(key) != value for key, value in expected.items()):
            raise LabError("Captured candidate/data/configuration differs from its exact freeze.")
    if judge_snapshot is not None and judge_snapshot != frozen["judge_model_snapshot"]:
        raise LabError("Judge model snapshot changed after calibration/freeze; no final rejudge.")
    return frozen


def finalize_holdout(freeze_id: str, run_id: str) -> dict:
    frozen = validate_frozen_run(freeze_id, run_id)
    directory = safe_run_dir(run_id)
    summary = read_json(directory / "summary.json")
    metadata = read_json(directory / "metadata.json")
    if {key: value for key, value in summary["metadata"].items() if key != "sample_count"} != metadata:
        raise LabError("Summary and current captured metadata differ; regenerate local scoring, not Judge responses.")
    if summary["metadata"].get("evaluation_contract_version") != CONTRACT_VERSION:
        raise LabError("Final holdout requires the frozen versioned policy and retrieval evaluator.")
    if not (directory / "business-judge/report.json").is_file():
        raise LabError("Final evaluation has no recorded complete Judge attempt.")
    judge_report = read_json(directory / "business-judge/report.json")
    submission = read_json(directory / "business-judge/submission.json")
    if (
        judge_report.get("submission_sha256") != digest(submission)
        or judge_report.get("evaluator_sha256") != frozen["hashes"]["evaluator"]
        or judge_report.get("judge_scores_sha256") != sha256_file(directory / "judge-scores.json")
        or submission.get("outputs_sha256") != sha256_file(directory / "outputs.jsonl")
        or submission.get("dataset_sha256") != metadata["dataset_sha256"]
        or submission.get("freeze_sha256") != frozen["content_sha256"]
        or submission.get("row_ids") != metadata["row_ids"]
        or submission.get("sample_contract_sha256") != frozen["hashes"]["sample_contract"]
        or judge_report.get("execution_status") != metadata.get("judge_execution_status")
        or digest(read_json(directory / "business-judge/contract.json")) != frozen["hashes"]["evaluator"]
    ):
        raise LabError("Final Judge attempt source/score hashes differ from the exact freeze and capture.")
    judges = read_json(directory / "judge-scores.json")
    captures = {row["id"]: row for row in read_jsonl(directory / "outputs.jsonl")}
    _, dataset_path = load_holdout(freeze_id, metadata["holdout_id"])
    cases = {case["id"]: case for case in read_jsonl(dataset_path)}
    known = {doc["id"] for doc in read_json(content_path(ROOT, "data/knowledge/documents.json"))}
    if set(captures) != set(metadata["row_ids"]) or set(judges) != set(metadata["row_ids"]):
        raise LabError("Final evidence must include every attempted case, including failures.")
    expected_rows = [
        score_row(
            cases[identifier], captures[identifier]["raw_output"],
            known_citations=known, latency_ms=captures[identifier].get("latency_ms"),
            usage=captures[identifier].get("usage"), error=captures[identifier]["error"],
            judge=judges[identifier], retrieved_context=captures[identifier]["retrieved_context"],
        ) for identifier in metadata["row_ids"]
    ]
    if canonical(summary) != canonical(summarize(expected_rows, metadata=metadata)):
        raise LabError("Final summary does not match scoring of the frozen dataset and captured evidence.")
    if any(
        row["raw_output"] != captures.get(row["id"], {}).get("raw_output")
        or row["judge"] != judges.get(row["id"])
        or row.get("retrieved_context") != captures.get(row["id"], {}).get("retrieved_context")
        for row in summary["rows"]
    ):
        raise LabError("Final summary rows differ from the captured outputs/actual Judge scores.")
    gate = evaluate_gates(summary, frozen["gates"])
    result = _seal({
        "freeze_id": freeze_id, "freeze_sha256": frozen["content_sha256"], "run_id": run_id,
        "created_at": now(), "summary_sha256": sha256_file(directory / "summary.json"),
        "gates_sha256": frozen["hashes"]["gates"],
        "sample_contract": frozen["sample_contract"], "sample_count": len(summary["rows"]),
        "legacy_minimum_test_rows": frozen["legacy_gates"]["minimum_test_rows"],
        "execution_mode": frozen["execution_mode"], "execution_status": summary["metadata"].get("status"),
        "judge_execution_status": summary["metadata"].get("judge_execution_status"),
        "quality_status": gate["outcome"] if frozen["execution_mode"] == "LIVE" else "DEMO_ONLY",
        "manual_review_state": frozen["manual_review_state"],
        "manual_operational_approval": "not_granted", "production_ready": False,
        "access_blockers": summary["metadata"].get("access_blockers", []), "gate": gate,
        "source_files": [
            _file(directory / name, "final_evidence")
            for name in ("metadata.json", "summary.json", "outputs.jsonl", "judge-scores.json",
                         "business-judge/contract.json", "business-judge/submission.json", "business-judge/report.json")
        ],
    })
    save_json(_directory("results") / f"{freeze_id}.json", result, exclusive=True)
    return result


def governance_status(freeze_id: str) -> dict:
    frozen = load_freeze(freeze_id, verify=False)
    result_path = _directory("results") / f"{freeze_id}.json"
    if result_path.exists():
        result = _sealed(result_path)
        for item in result.get("source_files", []):
            if not Path(item["path"]).is_file() or sha256_file(Path(item["path"])) != item["sha256"]:
                raise LabError("Final evidence changed after the one-shot verdict. Do not reinterpret or rejudge it.")
        return result
    attempt_path = _directory("attempts") / f"{freeze_id}.json"
    attempt = _sealed(attempt_path) if attempt_path.exists() else None
    metadata = {}
    if attempt and (safe_run_dir(attempt["run_id"]) / "metadata.json").is_file():
        metadata = read_json(safe_run_dir(attempt["run_id"]) / "metadata.json")
    drift = []
    try:
        load_freeze(freeze_id)
    except LabError as exc:
        drift.append(str(exc))
    return {
        "freeze_id": freeze_id, "execution_mode": frozen["execution_mode"],
        "run_id": None if attempt is None else attempt["run_id"],
        "execution_status": metadata.get("status", "not_started"),
        "quality_status": "NOT_EVALUATED", "contract_blockers": drift,
        "calibration_state": frozen["calibration_state"],
        "sample_contract": frozen.get("sample_contract"),
        "minimum_holdout_rows": frozen["gates"]["minimum_test_rows"],
        "manual_review_state": frozen["manual_review_state"],
        "manual_operational_approval": "not_granted", "production_ready": False,
        "access_blockers": metadata.get("access_blockers", frozen["access_blockers"]),
    }
