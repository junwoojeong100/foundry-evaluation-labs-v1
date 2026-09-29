"""One entry point for the workshop's small, explicit operations."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from azure.core.exceptions import AzureError
from openai import OpenAIError

from lab.config import LabError, load_config
from lab.files import ARTIFACTS, ROOT, read_json, safe_run_dir
from lab.preflight import run_preflight, save_json


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="python -m lab",
        description="Foundry learning loop: explicit evidence, no simulated cloud success.",
    )
    result.add_argument("--config", type=Path, default=ROOT / ".env")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Validate synthetic data and export freshness locally")
    commands.add_parser("preflight", help="Read-only Azure identity, region and deployment checks")
    create = commands.add_parser("agent", help="Create an owned, versioned prompt-agent candidate")
    create.add_argument("--stage", choices=("baseline", "iq", "optimized", "tuned"), required=True)
    create.add_argument("--prompt", type=Path)
    create.add_argument("--new-version", action="store_true")
    create.add_argument("--confirm", action="store_true")
    batch = commands.add_parser("run", help="Capture real agent responses; incurs usage charges")
    batch.add_argument("--stage", choices=("baseline", "iq", "optimized", "tuned"), required=True)
    batch.add_argument("--split", choices=("dev", "test"), required=True)
    batch.add_argument("--run-id", required=True)
    batch.add_argument("--limit", type=int)
    batch.add_argument("--confirm", action="store_true")
    score = commands.add_parser("score", help="Score captured outputs locally without model calls")
    score.add_argument("--run-id", required=True)
    compare = commands.add_parser("compare", help="Compare paired, held-out evidence locally")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--candidate", required=True)
    compare.add_argument("--out", type=Path, default=ARTIFACTS / "decision.json")
    iq = commands.add_parser("iq", help="Create or probe a real Search knowledge base")
    iq.add_argument("action", choices=("prepare", "probe"))
    iq.add_argument("--query", default="Contoso Atlas Cloud의 환불 조건을 알려주세요.")
    iq.add_argument("--confirm", action="store_true")
    evaluate = commands.add_parser("evaluate", help="Submit or inspect a managed Foundry evaluation")
    evaluate.add_argument("action", choices=("submit", "collect"))
    evaluate.add_argument("--run-id", required=True)
    evaluate.add_argument("--confirm", action="store_true")
    optimize = commands.add_parser("optimize", help="Prepare an Agent Optimizer handoff (not a service execution)")
    optimize.add_argument("--run-id", required=True)
    tune = commands.add_parser("tune-prepare", help="Prepare training artifacts, not a training job")
    tune.add_argument("--kind", choices=("frontier", "sft"), default="frontier")
    cleanup = commands.add_parser("cleanup", help="Plan or remove only locally recorded lab-owned objects")
    cleanup.add_argument("--confirm-prefix")
    return result


def require_confirmation(args: argparse.Namespace) -> None:
    if not args.confirm:
        raise LabError("클라우드 데이터 전송·비용·변경 단계입니다. 대상을 확인한 후 --confirm을 추가하세요.")


def execute(args: argparse.Namespace) -> int:
    if args.command == "validate":
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_datasets.py"), "--check"],
            cwd=ROOT, check=False,
        ).returncode
    if args.command == "score":
        from lab.batch import score_run

        summary = score_run(args.run_id)
        print(json.dumps(summary["metrics"], ensure_ascii=False, indent=2))
        print(safe_run_dir(args.run_id) / "report.md")
        return 0
    if args.command == "compare":
        from lab.evidence import compare_runs

        decision = compare_runs(
            read_json(safe_run_dir(args.baseline) / "summary.json"),
            read_json(safe_run_dir(args.candidate) / "summary.json"),
            read_json(ROOT / "config/gates.json"),
        )
        save_json(args.out, decision)
        print(json.dumps(decision, ensure_ascii=False, indent=2))
        return 0 if decision["outcome"] == "PASS_FOR_WORKSHOP" else 1
    if args.command == "optimize":
        from lab.handoffs import prepare_optimizer

        print(prepare_optimizer(args.run_id))
        return 0
    if args.command == "tune-prepare":
        from lab.handoffs import prepare_tuning

        print(prepare_tuning(args.kind))
        return 0
    config = load_config(args.config)
    if args.command == "preflight":
        report = run_preflight(config)
        save_json(ARTIFACTS / "preflight.json", report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" else 1
    if args.command == "agent":
        from lab.agents import create_agent

        require_confirmation(args)
        default_prompts = {
            "baseline": ROOT / "prompts/baseline.txt",
            "iq": ROOT / "prompts/baseline.txt",
            "optimized": ARTIFACTS / "optimizer/selected-prompt.txt",
            "tuned": ARTIFACTS / "optimizer/selected-prompt.txt",
        }
        record = create_agent(config, args.stage, args.prompt or default_prompts[args.stage], new_version=args.new_version)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0
    if args.command == "run":
        from lab.batch import run_batch

        require_confirmation(args)
        result = run_batch(config, args.stage, args.split, args.run_id, limit=args.limit)
        print(safe_run_dir(args.run_id))
        return 1 if result["status"] == "completed_with_errors" else 0
    if args.command == "iq":
        from lab.knowledge import prepare_knowledge, probe_knowledge

        require_confirmation(args)
        output = prepare_knowledge(config) if args.action == "prepare" else probe_knowledge(config, args.query)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    if args.command == "evaluate":
        from lab.managed_eval import collect_evaluation, submit_evaluation

        if args.action == "submit":
            require_confirmation(args)
            output = submit_evaluation(config, args.run_id)
        else:
            output = collect_evaluation(config, args.run_id)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    if args.command == "cleanup":
        from lab.cleanup import cleanup

        output = cleanup(config, confirm_prefix=args.confirm_prefix)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 1 if output["mode"] == "DELETION_PENDING" else 0
    raise LabError(f"지원하지 않는 명령: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return execute(args)
    except (LabError, AzureError, OpenAIError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
