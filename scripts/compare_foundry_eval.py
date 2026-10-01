"""Compare complete managed runs and expose only allowlisted synthetic case evidence."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab.evidence import _schema_errors, strict_json_loads
from scripts.add_foundry_eval_run import evaluation_contract, verify_agent_execution

METRICS = {"Relevance": (1, 5), "TaskAdherence": (0, 1)}


def _public_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} is not a recorded string.")
    if re.search(
        r"(?i)(?:[?&](?:sig|x-amz-signature)=|-----BEGIN .*PRIVATE KEY-----|"
        r"\bBearer\s+[A-Za-z0-9._~-]{20,}|\beyJ[A-Za-z0-9_-]{12,}\.eyJ|"
        r"\bgh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})",
        value,
    ):
        raise ValueError(f"{field} contains a potential credential or signed URL; do not publish it.")
    return value


def compare_pair(*, dataset: list[dict], baseline: dict, candidate: dict,
                 baseline_agent: dict, candidate_agent: dict,
                 baseline_evaluation: dict, candidate_evaluation: dict,
                 baseline_items: list[dict], candidate_items: list[dict]) -> dict:
    if not dataset or any(not isinstance(row, dict) or not isinstance(row.get("query"), str) for row in dataset):
        raise ValueError("A nonempty source dataset with string queries is required.")
    by_query = {row["query"]: row for row in dataset}
    if len(by_query) != len(dataset):
        raise ValueError("The dataset has duplicate queries; positional matching is forbidden.")
    contract = evaluation_contract(baseline_evaluation)
    if contract != evaluation_contract(candidate_evaluation):
        raise ValueError("The managed evaluator contract changed.")
    if baseline["eval_id"] != candidate["eval_id"]:
        raise ValueError("Both runs must belong to the same evaluation definition.")
    if baseline["id"] == candidate["id"]:
        raise ValueError("A run cannot be compared with itself.")
    if baseline["status"] != "completed" or candidate["status"] != "completed":
        raise ValueError("Both managed runs must be completed; preserve failed runs separately.")
    expected_source = deepcopy(baseline["data_source"])
    expected_source["target"]["version"] = candidate["data_source"]["target"]["version"]
    if expected_source != candidate["data_source"]:
        raise ValueError("More than the explicit target version changed in the data source.")
    if baseline["data_source"]["target"]["version"] == candidate["data_source"]["target"]["version"]:
        raise ValueError("The candidate must have distinct, actually executed instructions.")
    if {key: value for key, value in baseline_agent["definition"].items() if key != "instructions"} != {
        key: value for key, value in candidate_agent["definition"].items() if key != "instructions"
    }:
        raise ValueError("The model, tools or generation settings changed between the agents.")
    if baseline_agent["definition"]["instructions"] == candidate_agent["definition"]["instructions"]:
        raise ValueError("The instructions are identical; do not resample an unchanged candidate until favorable.")
    known_ids = {
        document["id"]
        for document in json.loads((ROOT / "data/en/knowledge/documents.json").read_text())
    }
    arms = {}
    mapped = {}
    for label, run, agent, items in (
        ("baseline", baseline, baseline_agent, baseline_items),
        ("candidate", candidate, candidate_agent, candidate_items),
    ):
        queries = [item["datasource_item"]["query"] for item in items]
        if len(queries) != len(dataset) or len(set(queries)) != len(dataset) or set(queries) != set(by_query):
            raise ValueError(f"{label} output does not contain every original case exactly once.")
        target = run["data_source"]["target"]
        execution = verify_agent_execution(
            items, agent_name=target["name"], version=target["version"],
            instructions=agent["definition"]["instructions"],
        )
        mapped[label] = {}
        for item in items:
            source = item["datasource_item"]
            query = source["query"]
            for field in ("context", "ground_truth"):
                if source.get(field) != by_query[query].get(field):
                    raise ValueError(f"{label} changed the source {field}.")
            raw = _public_text(source.get("sample.output_text"), f"{label} response")
            format_errors = []
            parsed = None
            try:
                parsed = strict_json_loads(raw)
            except ValueError as error:
                format_errors.append(str(error))
            format_errors.extend(_schema_errors(parsed))
            if isinstance(parsed, dict):
                if not isinstance(parsed.get("answer"), str) or not parsed["answer"].strip():
                    format_errors.append("answer must be a nonempty string")
                citations = parsed.get("citations")
                if isinstance(citations, list) and all(isinstance(value, str) for value in citations):
                    if set(citations) - known_ids:
                        format_errors.append("citations contain unknown or retrieval-only IDs")
            metrics = {}
            for result in item["results"]:
                name = result.get("name")
                if not isinstance(name, str) or name not in METRICS or name in metrics:
                    raise ValueError(f"{label} has missing, extra or duplicated evaluator results.")
                score, passed = result.get("score"), result.get("passed")
                minimum, maximum = METRICS[name]
                if type(score) not in (int, float) or score not in range(minimum, maximum + 1) or type(passed) is not bool:
                    raise ValueError(f"{label} has an unavailable or invalid {name} result; do not omit the row.")
                if passed != (score >= contract["thresholds"][name]):
                    raise ValueError(f"{label} service pass result disagrees with the frozen threshold.")
                metrics[name] = {
                    "score": score, "passed": passed,
                    "reason": _public_text(result.get("reason"), f"{label} {name} reason"),
                }
            if set(metrics) != set(METRICS):
                raise ValueError(f"{label} is missing an evaluator result.")
            mapped[label][query] = {
                "response": raw, "metrics": metrics,
                "response_contract_errors": format_errors,
                "latency_ms": item["sample"]["latency_ms"],
                "response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            }
        passed_count = sum(all(metric["passed"] for metric in row["metrics"].values()) for row in mapped[label].values())
        counts = run["result_counts"]
        if (
            counts["total"] != len(dataset) or counts["passed"] != passed_count
            or counts["failed"] != len(dataset) - passed_count
            or counts.get("errored") != 0 or counts.get("skipped", 0) != 0
        ):
            raise ValueError(f"{label} item-level results disagree with service totals.")
        agent_usage = [
            item for item in run["per_model_usage"] if item["model_name"] == agent["definition"]["model"]
        ]
        if len(agent_usage) != 1 or type(agent_usage[0].get("total_tokens")) is not int:
            raise ValueError(f"{label} has no unique measured agent-token total; unknown is not zero.")
        arms[label] = {
            "run_id": run["id"], "agent_version": target["version"], "cases": len(dataset),
            "passed_all": passed_count, "errored": counts["errored"],
            "metrics": {
                name: {
                    "passed": sum(row["metrics"][name]["passed"] for row in mapped[label].values()),
                    "mean": statistics.mean(row["metrics"][name]["score"] for row in mapped[label].values()),
                }
                for name in METRICS
            },
            "latency": run["latency"],
            "agent_tokens": agent_usage[0]["total_tokens"],
            "execution": execution,
        }
    failures = []
    if arms["candidate"]["passed_all"] < arms["baseline"]["passed_all"]:
        failures.append("all-criteria pass count declined")
    for name in METRICS:
        if arms["candidate"]["metrics"][name]["passed"] < arms["baseline"]["metrics"][name]["passed"]:
            failures.append(f"{name} pass count declined")
        if arms["candidate"]["metrics"][name]["mean"] < arms["baseline"]["metrics"][name]["mean"]:
            failures.append(f"{name} mean declined")
    if any(row["response_contract_errors"] for row in mapped["candidate"].values()):
        failures.append("candidate response-contract errors remain")
    improved = (
        arms["candidate"]["passed_all"] > arms["baseline"]["passed_all"]
        or any(arms["candidate"]["metrics"][name]["mean"] > arms["baseline"]["metrics"][name]["mean"] for name in METRICS)
    )
    if not improved:
        failures.append("no strict measured quality improvement")
    report = {
        "kind": "REAL_MANAGED_EVALUATION_LATEST_PAIR",
        "evaluation_id": baseline["eval_id"], "language": "en", "case_count": len(dataset),
        "contract": contract, "arms": arms,
        "decision": {
            "measured_quality_improved_without_regression": not failures,
            "failed_checks": failures,
            "remaining_requirements": "Review response truthfulness and operational latency/cost tradeoffs before any adoption.",
            "guarantees_future_results": False, "production_approval": "NOT_GRANTED",
            "statistical_significance": "USE_NATIVE_COMPARISON_NOT_INFERRED_FROM_THIS_GATE",
        },
        "cases": [
            {
                "case_number": number, "query": _public_text(row["query"], "query"),
                "reference_context": _public_text(row["context"], "reference context"),
                "reference_answer": _public_text(row["ground_truth"], "reference answer"),
                "baseline": mapped["baseline"][row["query"]],
                "candidate": mapped["candidate"][row["query"]],
            }
            for number, row in enumerate(dataset, 1)
        ],
        "publication_boundary": "Synthetic questions, actual responses, scores and reasons only; credentials, signed URLs, conversations and raw account metadata are excluded.",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--baseline-agent", type=Path, required=True)
    parser.add_argument("--candidate-agent", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/en/optimizer/dev.jsonl")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    report = compare_pair(
        dataset=[json.loads(line) for line in args.dataset.read_text().splitlines()],
        baseline=load(args.baseline / "run-latest.json"),
        candidate=load(args.candidate / "run-latest.json"),
        baseline_agent=load(args.baseline_agent), candidate_agent=load(args.candidate_agent),
        baseline_evaluation=load(args.baseline / "evaluation.json"),
        candidate_evaluation=load(args.candidate / "evaluation.json"),
        baseline_items=load(args.baseline / "output-items.json")["items"],
        candidate_items=load(args.candidate / "output-items.json")["items"],
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"arms": report["arms"], "decision": report["decision"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
