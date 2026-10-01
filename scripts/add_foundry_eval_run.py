#!/usr/bin/env python3
"""Add a real Foundry evaluation run with the baseline's dataset and criteria."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab.calibration import save_json
from lab.files import write_once_json


def as_object(value) -> dict:
    if hasattr(value, "as_dict"):
        value = value.as_dict()
    elif hasattr(value, "model_dump"):
        value = value.model_dump(mode="json", warnings=False)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object from Foundry.")
    return value


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def evaluation_contract(evaluation: dict) -> dict:
    expected = {
        "Relevance": ("builtin.relevance", 4, "{{sample.output_text}}"),
        "TaskAdherence": ("builtin.task_adherence", 1, "{{sample.output_items}}"),
    }
    criteria = evaluation.get("testing_criteria")
    if not isinstance(criteria, list) or len(criteria) != len(expected):
        raise ValueError("Use exactly the workshop's Relevance and TaskAdherence evaluators.")
    judges = set()
    seen = set()
    for criterion in criteria:
        if not isinstance(criterion, dict):
            raise ValueError("Each Foundry evaluation criterion must be a JSON object.")
        name = criterion.get("name")
        if not isinstance(name, str) or name not in expected or name in seen:
            raise ValueError("Evaluator names must be unique Relevance and TaskAdherence entries.")
        seen.add(name)
        evaluator, threshold, response = expected[name]
        parameters = criterion.get("initialization_parameters") or {}
        mapping = criterion.get("data_mapping") or {}
        if (
            criterion.get("type") != "azure_ai_evaluator"
            or criterion.get("evaluator_name") != evaluator
            or not isinstance(parameters, dict) or not isinstance(mapping, dict)
            or type(parameters.get("threshold")) not in (int, float)
            or parameters["threshold"] != threshold
            or mapping.get("query") != "{{item.query}}"
            or mapping.get("response") != response
        ):
            raise ValueError(f"{name} has a different evaluator, threshold, or response mapping.")
        judge = parameters.get("deployment_name")
        if not isinstance(judge, str) or not judge.strip():
            raise ValueError(f"{name} has no explicit Judge deployment in the remote definition.")
        judges.add(judge)
    if len(judges) != 1:
        raise ValueError("Both workshop evaluators must use the same explicit Judge deployment.")
    return {
        "judge_deployment": judges.pop(),
        "thresholds": {"Relevance": 4, "TaskAdherence": 1},
        "source": "existing_remote_evaluation_definition_not_local_environment_defaults",
        "testing_criteria_sha256": digest({"criteria": criteria}),
    }


def verify_agent_execution(items: list[dict], *, agent_name: str, version: str, instructions: str) -> dict:
    if not items or not isinstance(instructions, str) or not instructions.strip():
        raise ValueError("Per-item output and the pinned agent's actual instructions are required.")
    for item in items:
        source = item.get("datasource_item") if isinstance(item, dict) else None
        if (
            not isinstance(source, dict)
            or source.get("agent_name") != agent_name
            or str(source.get("agent_version")) != version
        ):
            raise ValueError("An output item did not execute the requested pinned agent version.")
        messages = source.get("sample.output_items")
        if not isinstance(messages, list) or not any(
            isinstance(message, dict)
            and message.get("role") in {"system", "developer"}
            and message.get("content") == instructions
            for message in messages
        ):
            raise ValueError("An output item does not attest the pinned agent's actual instructions.")
    return {
        "agent_name": agent_name, "agent_version": version, "items_verified": len(items),
        "instructions_sha256": hashlib.sha256(instructions.encode()).hexdigest(),
    }


def candidate_source(baseline: dict, *, evaluation_id: str, version: str) -> dict:
    if baseline.get("eval_id") != evaluation_id or baseline.get("status") != "completed":
        raise ValueError("Use a completed baseline run from this exact Foundry evaluation.")
    source = deepcopy(baseline.get("data_source"))
    if not isinstance(source, dict) or source.get("type") != "azure_ai_target_completions":
        raise ValueError("The baseline must be an agent-targeted Foundry evaluation.")
    target = source.get("target", {})
    if target.get("type") != "azure_ai_agent" or not target.get("name"):
        raise ValueError("The baseline must identify a Foundry agent.")
    original = str(target.get("version", ""))
    pinned_version = r"(?:[1-9]\d*|draft-[1-9]\d*)"
    if not re.fullmatch(pinned_version, original) or not re.fullmatch(pinned_version, version):
        raise ValueError("Pin explicit numeric or draft agent versions, not latest.")
    if original == version:
        raise ValueError("The candidate version must differ from the baseline.")
    dataset = source.get("source", {})
    if dataset.get("type") != "file_id" or not dataset.get("id"):
        raise ValueError("The baseline must use an identified, registered dataset.")
    messages = source.get("input_messages", {})
    template = messages.get("template", [])
    if messages.get("type") != "template" or len(template) != 1 or template[0].get("role") != "user":
        raise ValueError("Use one query-only user message, without reference-answer leakage.")
    content = template[0].get("content")
    query = content if isinstance(content, str) else content.get("text") if isinstance(content, dict) else None
    if query != "{{item.query}}":
        raise ValueError("This workshop sends only {{item.query}} to the agent.")
    target["version"] = version
    return source


def submit_or_resume(project, client, *, evaluation_id: str, baseline_run_id: str,
                     version: str, name: str, output: Path) -> dict:
    intent = {
        "evaluation_id": evaluation_id, "baseline_run_id": baseline_run_id,
        "candidate_version": version, "name": name,
    }
    if output.exists():
        saved = json.loads(output.read_text(encoding="utf-8"))
        if saved.get("intent") != intent:
            raise ValueError("This receipt belongs to a different evaluation or candidate.")
        if not saved.get("run_id"):
            raise ValueError("Submission outcome is unknown. Inspect Foundry before any new submission; preserve this receipt.")
        return saved
    baseline = as_object(client.evals.runs.retrieve(run_id=baseline_run_id, eval_id=evaluation_id))
    source = candidate_source(baseline, evaluation_id=evaluation_id, version=version)
    agent_name = source["target"]["name"]
    original_version = str(baseline["data_source"]["target"]["version"])
    before = as_object(project.agents.get_version(agent_name=agent_name, agent_version=original_version))["definition"]
    after = as_object(project.agents.get_version(agent_name=agent_name, agent_version=version))["definition"]
    if not isinstance(after.get("instructions"), str) or not after["instructions"].strip():
        raise ValueError("The candidate has no actual instructions.")
    if {key: value for key, value in before.items() if key != "instructions"} != {
        key: value for key, value in after.items() if key != "instructions"
    }:
        raise ValueError("Model, tools, or other agent settings changed. This is not an instruction-only comparison.")
    for existing in client.evals.runs.list(eval_id=evaluation_id, limit=100):
        existing = as_object(existing)
        if existing.get("name") == name:
            raise ValueError(
                f"Foundry already has a run named {name}: {existing.get('id')}. "
                "Open that run or restore its original receipt; do not create a duplicate."
            )
    evaluation = as_object(client.evals.retrieve(evaluation_id))
    contract = evaluation_contract(evaluation)
    saved = {
        "intent": intent,
        "status": "submitting",
        "run_id": None,
        "agent_name": agent_name,
        "dataset": source["source"],
        "testing_criteria_sha256": contract["testing_criteria_sha256"],
        "evaluation_contract": contract,
        "request": {"eval_id": evaluation_id, "name": name, "data_source": source},
        "production_approval": "NOT_GRANTED",
    }
    write_once_json(output, saved)
    # An interrupted POST intentionally leaves an unknown outcome, not permission to retry.
    run = as_object(client.evals.runs.create(**saved["request"]))
    if not run.get("id") or run.get("eval_id") != evaluation_id:
        raise ValueError("Foundry returned no matching evaluation-run identity; preserve the submission receipt.")
    saved.update(status=run["status"], run_id=run["id"], run=run)
    save_json(output, saved)
    return saved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True, help="The same Foundry project endpoint as the baseline")
    parser.add_argument("--subscription", required=True, help="The explicitly selected Azure CLI subscription")
    parser.add_argument("--evaluation", required=True, help="Existing eval_... ID; no new evaluation definition is created")
    parser.add_argument("--baseline", required=True, help="Completed baseline evalrun_... ID")
    parser.add_argument("--version", required=True, help="Explicit candidate agent version")
    parser.add_argument("--name", default="candidate-v2")
    parser.add_argument("--out", type=Path, default=Path(".lab/foundry-evaluations/candidate-v2.json"))
    parser.add_argument("--wait-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    try:
        endpoint = urlsplit(args.endpoint)
        if (
            endpoint.scheme != "https" or endpoint.username or endpoint.password
            or endpoint.port or endpoint.query or endpoint.fragment
            or not re.fullmatch(r"[a-z0-9-]+\.services\.ai\.azure\.com", endpoint.hostname or "")
            or not re.fullmatch(r"/api/projects/[A-Za-z0-9_.()-]+/?", endpoint.path)
        ):
            raise ValueError("Use the exact HTTPS Foundry project endpoint, without credentials or query parameters.")
        if not 1 <= args.wait_seconds <= 3600:
            raise ValueError("--wait-seconds must be between 1 and 3600.")
        account = subprocess.run(
            ["az", "account", "show", "--subscription", args.subscription, "-o", "json"],
            capture_output=True, text=True, check=True, timeout=30,
        )
        identity = json.loads(account.stdout)
        if identity.get("id", "").lower() != args.subscription.lower() or identity.get("state") != "Enabled":
            raise ValueError("Azure CLI did not confirm the intended enabled subscription.")
        from azure.ai.projects import AIProjectClient
        from azure.identity import AzureCliCredential

        with AzureCliCredential(subscription=args.subscription, process_timeout=30) as credential:
            with AIProjectClient(endpoint=args.endpoint, credential=credential, retry_total=0) as project:
                with project.get_openai_client(max_retries=0, timeout=120) as client:
                    saved = submit_or_resume(
                        project, client, evaluation_id=args.evaluation, baseline_run_id=args.baseline,
                        version=args.version, name=args.name, output=args.out,
                    )
                    print(f"Foundry evaluation: {args.evaluation}\nRun: {saved['run_id']}", flush=True)
                    deadline = time.monotonic() + args.wait_seconds
                    while True:
                        run = as_object(client.evals.runs.retrieve(run_id=saved["run_id"], eval_id=args.evaluation))
                        saved.update(status=run["status"], run=run)
                        save_json(args.out, saved)
                        if run["status"] in {"completed", "failed", "canceled", "cancelled"}:
                            if run["status"] == "completed":
                                items = [
                                    as_object(item) for item in client.evals.runs.output_items.list(
                                        run_id=saved["run_id"], eval_id=args.evaluation,
                                    )
                                ]
                                saved["output_items"] = items
                                save_json(args.out, saved)
                                if len(items) != (run.get("result_counts") or {}).get("total"):
                                    raise ValueError("Completed-run output is incomplete; preserve the receipt.")
                                agent = as_object(project.agents.get_version(
                                    agent_name=saved["agent_name"], agent_version=args.version,
                                ))
                                saved["execution_verification"] = verify_agent_execution(
                                    items, agent_name=saved["agent_name"], version=args.version,
                                    instructions=agent["definition"]["instructions"],
                                )
                                save_json(args.out, saved)
                            print(json.dumps({
                                "status": run["status"], "result_counts": run.get("result_counts"),
                                "report_url": run.get("report_url"), "production_approval": "NOT_GRANTED",
                            }, indent=2))
                            return 0 if run["status"] == "completed" else 1
                        if time.monotonic() >= deadline:
                            print("Still running. Repeat this exact command to collect the same run; do not delete the receipt.", file=sys.stderr)
                            return 2
                        time.sleep(15)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
