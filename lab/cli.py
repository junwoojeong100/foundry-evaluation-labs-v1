"""One entry point for the workshop's small, explicit operations."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from lab.config import Config, LabError, load_config, use_config
from lab.content import content_path, selected_language, text
from lab.files import ROOT, artifacts_dir, read_json, safe_run_dir
from lab.preflight import run_preflight, save_json


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="python -m lab",
        description="Foundry learning loop: explicit evidence, no simulated cloud success.",
        epilog=(
            "The ten-step guide uses only these commands: bootstrap, preflight, smoke, iq, native-agent, "
            "native-evals and cleanup. The other commands are advanced and optional."
        ),
    )
    result.add_argument("--config", type=Path, help="Environment .env; also selects saved language and record folder")
    commands = result.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Free authored examples; no SDK, credentials, login or network")
    demo.add_argument("--out", type=Path)
    bootstrap = commands.add_parser("bootstrap", help="Guided Microsoft Foundry setup or advanced plan/preflight/apply/status", add_help=False)
    bootstrap.add_argument("bootstrap_args", nargs=argparse.REMAINDER)
    commands.add_parser("validate", help="Validate synthetic data and export freshness locally")
    commands.add_parser("preflight", help="Read-only Azure identity, region and deployment checks")
    smoke = commands.add_parser("smoke", help="One real model response before Agent creation; not a quality score")
    smoke.add_argument("--run-id", required=True)
    smoke.add_argument("--confirm", action="store_true")
    create = commands.add_parser("agent", help="Create an owned, versioned prompt-agent candidate")
    create.add_argument("--stage", choices=("baseline", "iq", "optimized", "tuned"), required=True)
    create.add_argument("--prompt", type=Path)
    create.add_argument("--new-version", action="store_true")
    create.add_argument("--confirm", action="store_true")
    native = commands.add_parser("native-agent", help="Create/reuse policy-connected strict-JSON v1 or instruction-only v2")
    native.add_argument("--version", choices=("1", "2"), required=True)
    native.add_argument("--prompt", type=Path, help="Reviewed instructions; required for v2")
    native.add_argument("--confirm", action="store_true")
    native_evals = commands.add_parser("native-evals", help="Read evaluation/run IDs by exact portal evaluation name; never submit")
    native_evals.add_argument("--name", required=True)
    batch = commands.add_parser("run", help="Capture real agent responses; incurs usage charges")
    batch.add_argument("--stage", choices=("baseline", "iq", "optimized", "tuned"), required=True)
    batch.add_argument("--split", choices=("dev", "test"), required=True)
    batch.add_argument("--run-id", required=True)
    batch.add_argument("--limit", type=int)
    batch.add_argument("--resume", action="store_true")
    batch.add_argument("--freeze-id")
    batch.add_argument("--holdout-id")
    batch.add_argument("--interval-seconds", type=float, default=0, help="Explicit 0–120s pacing between cases and scripted turns; not a retry")
    batch.add_argument("--dialogue", action="store_true", help="Separate authored dev dialogue with an explicit scripted follow-up")
    batch.add_argument("--confirm", action="store_true")
    score = commands.add_parser("score", help="Score captured outputs locally without model calls")
    score.add_argument("--run-id", required=True)
    explain = commands.add_parser("explain", help="Read saved criteria, scores, Judge reasons and improvement hints; no model calls or evidence writes")
    explain.add_argument("--run-id", required=True)
    explain.add_argument("--baseline", help="Optional existing run with identical data/cases/Judge for local regression diagnostics")
    explain.add_argument("--case-id", help="Show one case in detail without changing full-run metrics or gates")
    compare = commands.add_parser("compare", help="Compare paired, held-out evidence locally")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--candidate", required=True)
    compare.add_argument("--out", type=Path)
    iq = commands.add_parser("iq", help="Create or probe a real Search knowledge base")
    iq.add_argument("action", choices=("prepare", "probe", "vectors"))
    iq.add_argument("--query")
    iq.add_argument("--confirm", action="store_true")
    evaluate = commands.add_parser("evaluate", help="Submit or inspect a managed Foundry evaluation")
    evaluate.add_argument("action", choices=("submit", "collect"))
    evaluate.add_argument("--run-id", required=True)
    evaluate.add_argument("--confirm", action="store_true")
    judge = commands.add_parser("judge", help="Versioned business/retrieval Judge calibration and one-shot scoring")
    judge_actions = judge.add_subparsers(dest="judge_action", required=True)
    calibrate = judge_actions.add_parser("calibrate")
    calibrate.add_argument("--calibration-id", required=True)
    calibrate.add_argument("--fixtures", type=Path)
    calibrate.add_argument("--interval-seconds", type=float, default=0, help="Explicit 0–120s pacing between calibration cases; not a retry")
    calibrate.add_argument("--confirm", action="store_true")
    judge_score = judge_actions.add_parser("score")
    judge_score.add_argument("--run-id", required=True)
    judge_score.add_argument("--confirm", action="store_true")
    judge_score.add_argument("--interval-seconds", type=float, default=0)
    review = commands.add_parser("review", help="AI advice or externally claimed, unverified manual review")
    reviews = review.add_subparsers(dest="review_action", required=True)
    ai_review = reviews.add_parser("ai")
    ai_review.add_argument("--review-id", required=True)
    ai_review.add_argument("--subject", type=Path, required=True)
    ai_review.add_argument("--actor", required=True)
    ai_review.add_argument("--notes", required=True)
    manual_review = reviews.add_parser("import")
    manual_review.add_argument("--path", type=Path, required=True)
    freeze = commands.add_parser("freeze", help="Seal exact candidate/Judge/search/gates before fresh holdout")
    freeze.add_argument("--freeze-id", required=True)
    freeze.add_argument("--stage", choices=("baseline", "iq", "optimized", "tuned"), required=True)
    freeze.add_argument("--calibration-id", required=True)
    freeze.add_argument("--review-id", action="append", default=[])
    freeze.add_argument("--mode", choices=("LIVE", "DEMO"), default="LIVE")
    holdout = commands.add_parser("holdout", help="Create/register synthetic fresh cases only after a verified freeze")
    holdouts = holdout.add_subparsers(dest="holdout_action", required=True)
    for action in ("create", "register"):
        child = holdouts.add_parser(action)
        child.add_argument("--freeze-id", required=True)
        child.add_argument("--holdout-id", required=True)
        if action == "create":
            child.add_argument("--count", type=int)
        else:
            child.add_argument("--source", type=Path, required=True)
            child.add_argument("--generated-at", required=True)
            child.add_argument("--provenance", required=True)
    governance = commands.add_parser("governance", help="One-shot verdict and independent review/approval states")
    governance.add_argument("action", choices=("finalize", "status"))
    governance.add_argument("--freeze-id", required=True)
    governance.add_argument("--run-id")
    control = commands.add_parser("control-plane", help="Read actual traces; empty telemetry remains NOT_VERIFIED")
    control.add_argument("--run-id", required=True)
    control.add_argument("--app-insights-id", required=True)
    feedback = commands.add_parser("feedback", help="Export actual dev failures to a review-only queue, never final-test training")
    feedback.add_argument("--run-id", required=True)
    feedback.add_argument("--feedback-id", required=True)
    optimize = commands.add_parser("optimize", help="Prepare an agent optimizer handoff (not a service execution)")
    optimize.add_argument("--run-id", required=True)
    optimizer_result = commands.add_parser("optimizer-result", help="Preserve actual portal Prompt Optimizer output, not execute the service")
    optimizer_result.add_argument("--request", type=Path, required=True)
    optimizer_result.add_argument("--response", type=Path, required=True)
    agent_optimizer_result = commands.add_parser("optimizer-agent-result", help="Import actual completed instruction-only agent optimizer output")
    agent_optimizer_result.add_argument("--result", type=Path, required=True)
    agent_optimizer_result.add_argument("--candidate", type=Path, required=True)
    optimizer_check = commands.add_parser("optimizer-check", help="Apply local rules to all actual native optimizer responses without new model calls")
    optimizer_check.add_argument("--baseline-items", type=Path, required=True)
    optimizer_check.add_argument("--candidate-items", type=Path, required=True)
    tune = commands.add_parser("tune-prepare", help="Prepare training artifacts, not a training job")
    tune.add_argument("--kind", choices=("frontier", "sft"), default="frontier")
    cleanup = commands.add_parser("cleanup", help="Plan or remove only locally recorded lab-owned objects")
    cleanup.add_argument("--confirm-prefix")
    return result


def require_confirmation(args: argparse.Namespace) -> None:
    if not args.confirm:
        raise LabError(text(
            "클라우드 데이터 전송·비용·변경 단계입니다. 대상을 확인한 후 --confirm을 추가해야 합니다.",
            "This step can transfer data, incur costs, or change cloud resources. Verify the target and add --confirm.",
        ))


def execute(args: argparse.Namespace) -> int:
    without_config = {
        "bootstrap", "demo", "validate", "explain", "optimizer-check", "feedback", "review",
        "holdout", "governance", "score", "compare", "optimize", "tune-prepare",
    }
    if args.command in {"bootstrap", "demo"} or (args.command in without_config and args.config is None):
        return _execute(args)
    config = load_config(args.config or ROOT / ".env")
    with use_config(config):
        return _execute(args, config)


def _execute(args: argparse.Namespace, config: Config | None = None) -> int:
    if args.command == "explain":
        from lab.explanation import explain_run

        print(explain_run(args.run_id, baseline_id=args.baseline, case_id=args.case_id), end="")
        return 0
    if args.command == "optimizer-check":
        from lab.optimizer import check_native_pair

        result = check_native_pair(args.baseline_items, args.candidate_items)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "feedback":
        from lab.feedback import prepare_feedback

        result = prepare_feedback(args.run_id, args.feedback_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "bootstrap":
        from lab.bootstrap import main as bootstrap_main

        return bootstrap_main(args.bootstrap_args)
    if args.command == "demo":
        from lab.demo import run_demo

        result = run_demo(args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "review":
        from lab.governance import import_manual_review, record_ai_review

        result = (
            record_ai_review(args.review_id, args.subject, actor=args.actor, notes=args.notes)
            if args.review_action == "ai" else import_manual_review(args.path)
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "holdout":
        from lab.governance import create_holdout, register_holdout

        result = (
            create_holdout(args.freeze_id, args.holdout_id, count=args.count)
            if args.holdout_action == "create"
            else register_holdout(
                args.freeze_id, args.holdout_id, args.source,
                generated_at=args.generated_at, provenance=args.provenance,
            )
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "governance":
        from lab.governance import finalize_holdout, governance_status

        if args.action == "finalize" and not args.run_id:
            raise LabError(text(
                "governance finalize에는 --run-id가 필요합니다.", "governance finalize requires --run-id.",
            ))
        result = (
            finalize_holdout(args.freeze_id, args.run_id) if args.action == "finalize"
            else governance_status(args.freeze_id)
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "validate":
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_datasets.py"), "--check", "--language", selected_language()],
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
        save_json(args.out or artifacts_dir() / "decision.json", decision)
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
    if config is None:
        raise LabError("This command requires an environment configuration.")
    if args.command == "optimizer-result":
        from lab.optimizer import collect_prompt

        print(json.dumps(collect_prompt(config, args.request, args.response), ensure_ascii=False, indent=2))
        return 0
    if args.command == "optimizer-agent-result":
        from lab.optimizer import collect_agent

        print(json.dumps(collect_agent(config, args.result, args.candidate), ensure_ascii=False, indent=2))
        return 0
    if args.command == "freeze":
        from lab.governance import freeze_candidate

        result = freeze_candidate(
            config, args.freeze_id, args.stage, calibration_id=args.calibration_id,
            review_ids=args.review_id, mode=args.mode,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    from azure.core.exceptions import AzureError
    from openai import OpenAIError

    try:
        return execute_cloud(args, config)
    except (AzureError, OpenAIError) as exc:
        raise LabError(f"{type(exc).__name__}: {exc}") from exc


def execute_cloud(args: argparse.Namespace, config) -> int:
    if getattr(args, "confirm", False):
        from lab.auth import require_owned_scope

        require_owned_scope(config)
    if args.command == "smoke":
        from lab.agents import smoke_model

        require_confirmation(args)
        print(json.dumps(smoke_model(config, args.run_id), ensure_ascii=False, indent=2))
        return 0
    if args.command == "judge":
        from lab.calibration import run_calibration, score_captured_run

        require_confirmation(args)
        result = (
            run_calibration(
                config, args.calibration_id, confirm=True, fixtures_path=args.fixtures,
                interval_seconds=args.interval_seconds,
            )
            if args.judge_action == "calibrate"
            else score_captured_run(config, args.run_id, confirm=True, interval_seconds=args.interval_seconds)
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["execution_status"] == "completed" else 1
    if args.command == "control-plane":
        from lab.control_plane import collect

        output = collect(config, args.run_id, args.app_insights_id)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if output["status"] == "VERIFIED_TRACE_MODEL_TOOL_EVAL_LINKS" else 1
    if args.command == "preflight":
        report = run_preflight(config)
        save_json(artifacts_dir() / "preflight.json", report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" else 1
    if args.command == "agent":
        from lab.agents import create_agent

        require_confirmation(args)
        default_prompts = {
            "baseline": content_path(ROOT, "prompts/baseline.txt"),
            "iq": content_path(ROOT, "prompts/baseline.txt"),
            "optimized": artifacts_dir() / "optimizer/selected-prompt.txt",
            "tuned": artifacts_dir() / "optimizer/selected-prompt.txt",
        }
        record = create_agent(config, args.stage, args.prompt or default_prompts[args.stage], new_version=args.new_version)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0
    if args.command == "native-agent":
        from lab.agents import create_native_agent

        require_confirmation(args)
        if args.version == "2" and args.prompt is None:
            raise LabError("Native Agent v2 requires --prompt with the reviewed candidate instructions.")
        prompt = args.prompt if args.prompt is not None else content_path(ROOT, "prompts/baseline.txt")
        record = create_native_agent(config, args.version, prompt)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0
    if args.command == "native-evals":
        from lab.managed_eval import list_native_evaluations

        print(json.dumps(list_native_evaluations(config, args.name), ensure_ascii=False, indent=2))
        return 0
    if args.command == "run":
        from lab.batch import run_batch

        require_confirmation(args)
        result = run_batch(
            config, args.stage, args.split, args.run_id, limit=args.limit, resume=args.resume,
            freeze_id=args.freeze_id, holdout_id=args.holdout_id,
            interval_seconds=args.interval_seconds,
            dialogue=args.dialogue,
        )
        print(safe_run_dir(args.run_id))
        return 0 if result["status"] == "completed" else 1
    if args.command == "iq":
        from lab.knowledge import prepare_knowledge, probe_knowledge, probe_vectors

        require_confirmation(args)
        query = args.query if args.query is not None else text(
            "Contoso Atlas Cloud의 환불 조건을 알려주세요.",
            "What are the refund conditions for Contoso Atlas Cloud?",
        )
        output = (
            prepare_knowledge(config) if args.action == "prepare"
            else probe_vectors(config, query) if args.action == "vectors"
            else probe_knowledge(config, query)
        )
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
    raise LabError(text(f"지원하지 않는 명령: {args.command}", f"Unsupported command: {args.command}"))


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        return execute(args)
    except (LabError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
