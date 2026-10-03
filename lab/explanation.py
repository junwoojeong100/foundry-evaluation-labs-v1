"""Explain saved evaluations without model calls or changes to existing evidence."""

from pathlib import Path
import re

from lab.config import LabError
from lab.content import content_path, selected_language, text as localize
from lab.evidence import (
    _cell, _critical, _usable_judge_score, compare_runs, evaluate_gates, load_gates, score_row, validate_case,
)
from lab.files import ROOT, read_json, read_jsonl, safe_run_dir, sha256_file


RULES = {
    "format_pass_rate": ("출력 형식", "네 필드 JSON과 타입을 지침에서 명확히 하고 잘못된 출력을 확인합니다."),
    "route_accuracy": ("행동 분류", "같은 사례의 기대 route와 실제 route를 비교해 분류 지침을 보완합니다."),
    "citation_pass_rate": ("인용 ID", "실제 검색 문서의 안정된 ID와 필요한 인용을 확인합니다."),
    "human_flag_accuracy": ("사람 판단 표시", "needs_human은 escalate일 때만 true인지 확인합니다."),
    "forbidden_claim_pass_rate": ("금지 주장", "실행 도구·증거 없이 승인·환불·전송 완료를 말하지 않도록 보완합니다."),
}
SEMANTICS = {
    "policy_correctness": ("업무 정확성", "최신 정책의 적용 시점·모든 조건·권한을 확인하고 부족한 정보는 묻도록 보완합니다."),
    "groundedness": ("검색 근거성", "이 응답의 실제 MCP 문맥을 확인하고 검색 자료·질의·근거 사용 지침을 보완합니다."),
    "relevance": ("질문 적합성", "고객 질문에 먼저 직접 답하고 필요한 확인 질문만 하도록 지침을 보완합니다."),
}
RULES_EN = {
    "format_pass_rate": ("Output format", "Make the four-field JSON contract and types explicit; inspect invalid outputs."),
    "route_accuracy": ("Action routing", "Compare expected and actual routes for the same case and refine routing instructions."),
    "citation_pass_rate": ("Citation IDs", "Check stable IDs in actual retrieved documents and the required citations."),
    "human_flag_accuracy": ("Human-review flag", "Check that needs_human is true only for escalate."),
    "forbidden_claim_pass_rate": ("Forbidden claims", "Do not claim approval, refunds, or submission without execution tools and evidence."),
}
SEMANTICS_EN = {
    "policy_correctness": ("Policy correctness", "Check effective dates, all conditions, and authority; ask for missing information."),
    "groundedness": ("Retrieval groundedness", "Inspect this response's actual MCP context, source documents, query, and evidence-use instructions."),
    "relevance": ("Relevance", "Answer the customer's question directly and ask only necessary clarification questions."),
}
SCOPE_CHECKS = {"heldout_test_only", "minimum_test_rows", "fresh_holdout_bound", "fresh_sample_contract_bound"}


def _object(path: Path) -> dict:
    value = read_json(path)
    if not isinstance(value, dict):
        raise LabError(f"평가 기록은 JSON 객체여야 합니다: {path}")
    return value


def _load(run_id: str) -> tuple[dict, dict, dict, dict, dict | None]:
    from lab.batch import dataset_for_metadata

    directory = safe_run_dir(run_id)
    if not (directory / "summary.json").is_file():
        raise LabError("저장된 summary.json이 없습니다. 완료된 run에 로컬 score를 수행한 뒤 explain으로 읽으세요.")
    summary = _object(directory / "summary.json")
    metadata = _object(directory / "metadata.json")
    if metadata.get("run_id") != run_id or metadata.get("status") not in {"completed", "completed_with_errors"}:
        raise LabError("완료된 동일 run의 저장 결과만 설명합니다. 부분 실행을 완료로 해석하지 않습니다.")
    gates = load_gates()
    recorded_verdict = None
    if metadata.get("freeze_id"):
        from lab.governance import governance_status, load_freeze, validate_frozen_run

        state = governance_status(metadata["freeze_id"])
        if state.get("quality_status") not in {"NOT_EVALUATED", "HOLD", "PASS_FOR_WORKSHOP", "DEMO_ONLY"}:
            raise LabError("저장된 최종 판정의 상태를 확인할 수 없습니다.")
        if state.get("quality_status") == "NOT_EVALUATED":
            frozen = validate_frozen_run(metadata["freeze_id"], run_id)
        else:
            if state.get("run_id") != run_id:
                raise LabError("최종 판정과 요청한 run이 다릅니다.")
            frozen = load_freeze(metadata["freeze_id"])
            recorded_verdict = state
        if metadata.get("freeze_sha256") != frozen["content_sha256"]:
            raise LabError("실행과 동결의 해시가 다릅니다.")
        gates = frozen["gates"]
    evaluate_gates(summary, gates)
    if {key: value for key, value in summary["metadata"].items() if key != "sample_count"} != metadata:
        raise LabError("summary와 현재 metadata가 다릅니다. 원본을 확인하고 로컬 score 결과를 확인해야 합니다.")
    dataset = dataset_for_metadata(metadata)
    if sha256_file(dataset) != metadata.get("dataset_sha256"):
        raise LabError("평가 당시 데이터와 현재 데이터가 다릅니다.")
    source_cases = read_jsonl(dataset)
    for case in source_cases:
        validate_case(case)
    cases = {case["id"]: case for case in source_cases}
    if len(cases) != len(source_cases):
        raise LabError("원본 데이터에 중복된 사례 ID가 있습니다.")
    documents = read_json(content_path(ROOT, "data/knowledge/documents.json"))
    if not isinstance(documents, list) or any(
        not isinstance(document, dict) or not isinstance(document.get("id"), str) for document in documents
    ):
        raise LabError("인용 문서 목록 형식이 올바르지 않습니다.")
    known_citations = {document["id"] for document in documents}
    captures = read_jsonl(directory / "outputs.jsonl")
    identifiers = [capture.get("id") for capture in captures]
    if identifiers != metadata.get("row_ids") or len(set(identifiers)) != len(identifiers):
        raise LabError("저장된 응답과 실행의 사례 ID가 다릅니다.")
    if any(
        not isinstance(capture.get("raw_output"), str) or "error" not in capture
        or not isinstance(capture.get("retrieved_context", ""), str)
        for capture in captures
    ):
        raise LabError("저장된 응답의 필수 필드가 누락되었거나 형식이 다릅니다.")
    if metadata.get("outputs_sha256") and sha256_file(directory / "outputs.jsonl") != metadata["outputs_sha256"]:
        raise LabError("평가 이후 원본 응답 파일이 변경되었습니다.")
    judge_path = directory / "judge-scores.json"
    judges = _object(judge_path) if judge_path.exists() else {}
    if (metadata.get("judge") is not None and not judge_path.exists()) or not judges.keys() <= set(identifiers):
        raise LabError("Judge 기록이 누락되었거나 다른 사례의 점수가 섞였습니다.")
    captured = {capture["id"]: capture for capture in captures}
    if [row["id"] for row in summary["rows"]] != identifiers:
        raise LabError("summary와 원본 응답의 사례 순서가 다릅니다.")
    # Reuse the scoring engine for integrity checks, but never rewrite its files.
    for row in summary["rows"]:
        identifier = row["id"]
        if identifier not in cases:
            raise LabError(f"원본 데이터에 없는 사례입니다: {identifier}")
        capture = captured[identifier]
        expected = score_row(
            cases[identifier], capture["raw_output"], known_citations=known_citations,
            latency_ms=capture.get("latency_ms"), usage=capture.get("usage"), error=capture["error"],
            judge=judges.get(identifier), retrieved_context=capture.get("retrieved_context", ""),
        )
        if row != expected:
            raise LabError(f"저장된 응답·Judge 점수와 summary가 다릅니다: {identifier}")
    return summary, cases, captured, gates, recorded_verdict


def _fence(text: str) -> str:
    if not isinstance(text, str):
        raise LabError("저장된 질문·응답·평가 이유는 문자열이어야 합니다.")
    width = max((len(part) for part in re.findall(r"`+", text)), default=0) + 1
    fence = "`" * max(3, width)
    return f"{fence}text\n{text}\n{fence}"


def _score(row: dict, metric: str) -> str:
    value = _usable_judge_score(row, metric)
    return localize("미측정", "Unmeasured") if value is None else f"{value:g}"


def _context_excerpt(text: str) -> str:
    if not isinstance(text, str):
        raise LabError("기록된 정책·검색 문맥은 문자열이어야 합니다.")
    if not text.strip():
        return localize("미관측 — 문맥이나 점수를 대신 만들어 넣지 않습니다.", "Not observed; no context or score is fabricated.")
    excerpt = _fence(text[:1200])
    if len(text) > 1200:
        excerpt += localize(
            f"\n표시만 앞 1200자 발췌(전체 {len(text)}자)입니다. 판정 입력을 줄인 것이 아니며 원본 파일의 전체 문맥을 확인해야 합니다.",
            f"\nOnly the first 1,200 of {len(text)} characters are displayed. The evaluation input was not shortened; read the complete context in the original file.",
        )
    return excerpt


def _comparison_value(metric: str, value: float | None, *, delta: bool = False) -> str:
    if value is None:
        return localize("미측정", "Unmeasured")
    if metric in RULES:
        return f"{value * 100:.1f}{localize('%p', ' pp') if delta else '%'}"
    if metric == "latency_p95_increase_ratio":
        return f"{value:.1%}" if delta else f"{value:.2f}ms"
    return f"{value:.2f}{localize('점', ' points')}"


def _mean_threshold(gates: dict, metric: str) -> float | None:
    if metric == "policy_correctness":
        return gates.get("business_policy", {}).get("minimum_mean")
    return gates["judge"]["minimum_mean"][metric]


def _check_help(check: dict, summary: dict, gate: dict) -> tuple[str, str]:
    rules = RULES_EN if selected_language() == "en" else RULES
    semantics = SEMANTICS_EN if selected_language() == "en" else SEMANTICS
    name = check["name"]
    metadata = summary["metadata"]
    diagnostic = metadata["split"] in {"smoke", "dev"}
    no_critical = gate["critical_sample_count"] == 0
    if diagnostic and (name in SCOPE_CHECKS or (no_critical and (name == "minimum_critical_rows" or name.startswith("critical_")))):
        return localize("진단 범위", "Diagnostic scope"), localize(
            "최종 시험 조건 미충족입니다. 다른 오류·중요 실패와 교정 상태를 별도로 확인합니다.",
            "Final-test conditions are not met. Check other errors, critical failures, and calibration separately.",
        )
    if (
        diagnostic and metadata["stage"] == "baseline"
        and name in {"groundedness_all_rows", "groundedness_mean", "critical_groundedness_floor"}
        and all(not row.get("retrieved_context", "").strip() for row in summary["rows"])
    ):
        return localize("검색 미측정", "Retrieval unmeasured"), localize(
            "검색 없는 기준선입니다. 0점/만점으로 채우지 말고 IQ 연결 후 실제 문맥으로 확인합니다.",
            "This baseline has no retrieval. Do not substitute zero or a perfect score; inspect actual context after connecting IQ.",
        )
    if name.startswith("critical_") or name in {"no_semantic_critical_failures", "forbidden_claim_pass_rate", "human_flag_accuracy"}:
        return localize("중요·안전", "Critical / safety"), localize(
            "후보 사용을 보류하고 허위 완료·권한·중요 사례를 먼저 검토합니다.",
            "Hold the candidate and first review fabricated completion, authority, and critical cases.",
        )
    if name in RULES:
        return localize("품질 기준", "Quality criterion"), rules[name][1]
    for metric, (_, action) in semantics.items():
        if name == metric + "_mean":
            return localize("품질 기준", "Quality criterion"), action
    return localize("실행·측정·계약", "Execution / measurement / contract"), localize(
        "원본 오류·누락·척도·모델·계약을 확인합니다. 미확인 상태로 유료 최종 시험을 진행하지 않습니다.",
        "Check original errors, gaps, scales, model, and contract. Do not start a paid final test while these remain unverified.",
    )


def format_explanation(summary: dict, cases: dict, captures: dict, gates: dict, *, baseline: dict | None = None, case_id: str | None = None, recorded_verdict: dict | None = None) -> str:
    gate = evaluate_gates(summary, gates)
    metadata, metrics = summary["metadata"], summary["metrics"]
    total = len(summary["rows"])
    frozen = bool(metadata.get("freeze_id"))
    policy_rule = gates.get("business_policy")
    rules = RULES_EN if selected_language() == "en" else RULES
    semantics = SEMANTICS_EN if selected_language() == "en" else SEMANTICS
    lines = [
        localize("# 평가 결과 해설", "# Evaluation explained"), "",
        localize("**추가 모델 호출 0 · 기존 평가 파일 변경 0 · 자동 운영 승인 없음**", "**No additional model calls, no changes to existing evaluation files, no automatic operational approval**"),
        localize(
            f"- 실행: {_cell(metadata['run_id'])} / 단계: {_cell(metadata['stage'])} / 분할: {_cell(metadata['split'])} / {total}건",
            f"- Run: {_cell(metadata['run_id'])} / stage: {_cell(metadata['stage'])} / split: {_cell(metadata['split'])} / {total} cases",
        ),
        localize(
            f"- 기준: {'동결된 게이트' if frozen else '현재 config/gates.json'}; 최종 최소 표본 {gates['minimum_test_rows']}건",
            f"- Criteria: {'frozen gates' if frozen else 'current config/gates.json'}; final minimum sample: {gates['minimum_test_rows']}",
        ),
        localize(f"- 게이트 결과: **{gate['outcome']}** / 운영 승인: **not_granted**", f"- Gate outcome: **{gate['outcome']}** / operational approval: **not_granted**"),
        f"- {localize('저장된 최종 판정', 'Recorded final verdict')}: **{_cell(recorded_verdict['quality_status']) if recorded_verdict else localize('이 설명에서 확정하지 않습니다', 'not finalized by this command')}**",
        localize(
            "- 이 출력은 저장된 근거의 로컬 해석입니다. 실제 서비스 실행·신원·운영 승인을 새로 인증하지 않습니다.",
            "- This is a local interpretation of saved evidence, not new attestation of service execution, identity, or operational approval.",
        ),
        "", localize("## 1. 기준과 실제 결과", "## 1. Criteria and actual results"), "",
        localize("| 평가 항목 | 실제 값 | 기준 | 관측 범위 |", "| Metric | Actual value | Criterion | Coverage |"), "|---|---:|---:|---|",
    ]
    for metric, (label, _) in rules.items():
        lines.append(f"| {label} | {metrics[metric]:.1%} | ≥{gates['minimums'][metric]:.0%} | {localize(f'{total}건 전체', f'all {total} cases')} |")
    for metric, (label, _) in semantics.items():
        measurement = metrics["business_policy"] if metric == "policy_correctness" else metrics["judge"][metric]
        threshold = _mean_threshold(gates, metric)
        criterion = f"{localize('평균', 'mean')} ≥{threshold:g}" if threshold is not None else localize("기준 미선언", "No criterion declared")
        if metric == "policy_correctness" and (not policy_rule or metadata.get("evaluation_contract_version") != policy_rule["required_for_contract"]):
            criterion += localize(" (업무 계약 자동 게이트 미적용)", " (business-contract gate not applied)")
        mean = localize("미측정", "Unmeasured") if measurement["mean"] is None else f"{measurement['mean']:.2f}"
        lines.append(f"| {label} | {mean} | {criterion} | {localize('점수', 'scored')} {measurement['scored_count']}/{total}; {localize('누락', 'missing')} {measurement['missing_count']}; {localize('척도', 'scale')} {_cell(measurement['scale'])} |")
    lines.extend([
        localize(
            f"| 응답/형식 오류 | {metrics['error_count']}건 | ≤{gates['maximums']['error_count']} | Judge 오류는 별도 {metrics['judge_error_count']}건 |",
            f"| Response / format errors | {metrics['error_count']} | ≤{gates['maximums']['error_count']} | Separate Judge errors: {metrics['judge_error_count']} |",
        ),
        localize(
            f"| 중요 규칙 실패 | {metrics['critical_rule_failure_count']}건 | ≤{gates['maximums']['critical_rule_failure_count']} | 의미상 중요 실패 {metrics['business_policy']['critical_failure_count']}건 |",
            f"| Critical rule failures | {metrics['critical_rule_failure_count']} | ≤{gates['maximums']['critical_rule_failure_count']} | Semantic critical failures: {metrics['business_policy']['critical_failure_count']} |",
        ),
        "", localize(
            "평균은 유효한 점수가 있는 행만의 평균입니다. 누락은 0점이 아니며 coverage가 부족하면 최종 게이트를 통과할 수 없습니다.",
            "Means include only valid scored rows. Missing values are not zero; insufficient coverage cannot pass the final gates.",
        ),
        localize("중요 사례는 평균 외에 행별 하한도 검사합니다. 높은 평균으로 중요 실패를 상쇄하지 않습니다.", "Critical cases also have per-row floors. High averages cannot offset critical failures."),
        "", localize("## 2. HOLD 원인과 다음 확인", "## 2. HOLD causes and next checks"), "",
    ])
    failed = [check for check in gate["checks"] if not check["passed"]]
    if failed:
        lines.extend([localize("| 검사 | 해석 | 실제 값 | 요구 기준 | 다음 확인 |", "| Check | Interpretation | Actual | Required | Next check |"), "|---|---|---|---|---|"])
        for check in failed:
            category, action = _check_help(check, summary, gate)
            lines.append(f"| {_cell(check['name'])} | {category} | {_cell(check['actual'])} | {_cell(check['required'])} | {action} |")
    else:
        lines.append(localize("이 저장 결과의 게이트는 통과했습니다. 동결된 최종 판정과 실제 사람의 운영 승인은 별도입니다.", "These saved results pass the gates. The frozen final verdict and actual human operational approval remain separate."))
    lines.extend([
        "", localize("**진단 범위만의 HOLD와 품질·안전 실패를 구분합니다.** 범위 항목을 무시하고 전체 통과로 바꾸지 않습니다.", "**Distinguish diagnostic-scope HOLD from quality and safety failures.** Do not ignore scope checks and relabel the whole run as passed."),
        localize("기준선/IQ의 비중요 품질 미달은 개선할 대상입니다. 실행·채점 오류, 예상하지 못한 누락, 중요 실패, 교정 HOLD는 먼저 중단하고 원인을 확인합니다.", "Noncritical baseline/IQ gaps are improvement targets. First stop and investigate execution/scoring errors, unexpected missing values, critical failures, or calibration HOLD."),
        localize("개선 후보를 동결하거나 최종 시험으로 넘어갈지는 실제 사례 검토·교정 통과·승인 범위를 함께 확인해 결정합니다.", "Review actual cases, successful calibration, and authorization together before freezing a candidate or running the final test."),
    ])
    before = {}
    if baseline is not None:
        comparison = compare_runs(baseline, summary, gates)
        before = {row["id"]: row for row in baseline["rows"]}
        lines.extend([
            "", localize("## 3. 같은 문항의 자동 회귀 진단", "## 3. Automatic same-question regression diagnostics"), "",
            localize(
                f"원본 {_cell(baseline['metadata']['run_id'])} → 후보 {_cell(metadata['run_id'])}; 동일 {total}건·동일 Judge/척도입니다.",
                f"Original {_cell(baseline['metadata']['run_id'])} → candidate {_cell(metadata['run_id'])}; the same {total} cases, Judge, and scales.",
            ),
            localize(
                f"비교 엔진의 종합 결과: **{comparison['outcome']}**. dev/smoke의 종합 HOLD는 최종 시험 조건도 포함한 결과입니다.",
                f"Comparison outcome: **{comparison['outcome']}**. An overall dev/smoke HOLD also includes final-test conditions.",
            ),
            localize("| 지표 | 원본 | 후보 | 하락폭(원본−후보) / 지연 증가율 | 허용폭 | 진단 |", "| Metric | Original | Candidate | Drop (original−candidate) / latency increase | Tolerance | Diagnostic |"),
            "|---|---:|---:|---:|---:|---|",
        ])
        for check in comparison["regression_checks"]:
            metric = check["metric"]
            lines.append(
                f"| {_cell(metric)} | {_comparison_value(metric, check['baseline'])} | {_comparison_value(metric, check['candidate'])} | "
                f"{_comparison_value(metric, check.get('drop', check.get('increase_ratio')), delta=True)} | "
                f"{_comparison_value(metric, check.get('maximum_drop', check.get('maximum_increase_ratio')), delta=True)} | "
                f"{localize('범위 내', 'Within tolerance') if check['passed'] else localize('미충족/미측정', 'Failed / unmeasured')} |"
            )
        changed = [name for name, values in comparison["experiment_variables"].items() if values["changed"]]
        lines.append(
            f"{localize('변경된 실험 변수', 'Changed experiment variables')}: {_cell(', '.join(changed) or localize('없음', 'none'))}. "
            f"{localize('추가 기록 차이', 'Other metadata differences')}: {_cell(', '.join(comparison['other_metadata_changes']) or localize('없음', 'none'))}."
        )
        lines.append(localize(
            "자동 비교는 설정된 허용폭에 대한 진단입니다. 업무 정확성의 전후 변화·지시 diff·실제 문장의 타당성은 사람이 확인합니다. 검색 변동까지 통제한 인과 효과나 운영 승인이 아닙니다.",
            "Automatic comparison diagnoses configured tolerances. A person must review policy-correctness changes, instruction diffs, and actual claims. This is neither an isolated causal effect controlling retrieval variability nor operational approval.",
        ))
    else:
        lines.extend([
            "", localize("## 3. 비교 범위", "## 3. Comparison scope"), "",
            localize("이 출력에는 전후 회귀 진단이 없습니다. 동일 데이터·사례·Judge인 비교에만 --baseline을 사용합니다.", "No before/after diagnostics are included. Use --baseline only for the same dataset, cases, and Judge."),
            localize("기준선 3건과 IQ 12건, dev12와 fresh12의 전체 평균을 전후 개선율로 비교하지 않습니다.", "Do not compare overall means from baseline3 versus IQ12, or dev12 versus fresh12, as a before/after improvement rate."),
        ])
    lines.extend(["", localize("## 4. 전체 사례 점수와 대표 사례 해설", "## 4. All case scores and selected explanations"), "",
                  localize("표는 전체 사례입니다. 비교가 있으면 점수는 원본 → 현재 순서이며, 누락을 0점으로 바꾸지 않습니다.", "The table includes all cases. Comparisons show original → current scores. Missing values are not replaced with zero."),
                  localize("| 사례 ID | 실제 / 기대 route | 업무 정확성 | 검색 근거성 | 질문 적합성 |", "| Case ID | Actual / expected route | Policy correctness | Groundedness | Relevance |"),
                  "|---|---|---:|---:|---:|"])
    for row in summary["rows"]:
        response = row["response"] if isinstance(row["response"], dict) else {}
        values = [
            f"{_score(before[row['id']], metric)} → {_score(row, metric)}" if row["id"] in before else _score(row, metric)
            for metric in SEMANTICS
        ]
        lines.append(
            f"| {_cell(row['id'])} | {_cell(response.get('route', localize('형식 오류', 'format error')))} / {_cell(row['expected']['route'])} | "
            + " | ".join(values) + " |"
        )

    def priority(row):
        weak = bool(row["rule_failures"]) or row["api_error"] is not None or row["judge"]["error"] is not None
        for metric in SEMANTICS:
            value, threshold = _usable_judge_score(row, metric), _mean_threshold(gates, metric)
            weak = weak or value is None or (threshold is not None and value < threshold)
        if row["judge"].get("critical_failure") is True or (_critical(row, gates["critical_tags"]) and weak):
            return 0
        if row["id"] in before:
            for metric in SEMANTICS:
                old, current = _usable_judge_score(before[row["id"]], metric), _usable_judge_score(row, metric)
                if old is not None and current is not None and current < old:
                    return 1
        return 2 if weak else 3

    detail_rows = [row for row in summary["rows"] if row["id"] == case_id] if case_id is not None else sorted(summary["rows"], key=priority)[:3]
    if not detail_rows:
        raise LabError("요청한 사례 ID가 이 실행에 없습니다.")
    lines.extend([
        "", localize(
            f"상세 해설은 {len(detail_rows)}/{total}건입니다. 기본은 중요·하락·문제 사례 우선 최대 3건이며, 전체 분모와 게이트는 바뀌지 않습니다.",
            f"Details cover {len(detail_rows)}/{total} cases. By default, up to three critical, regressed, or problematic cases are prioritized. Denominators and gates are unchanged.",
        ),
        localize("다른 사례는 같은 명령에 --case-id와 표의 실제 ID를 지정해 읽습니다. 이유는 저장된 값만 보여 주고 새로 생성하지 않습니다.", "Use --case-id with an actual table ID to inspect another case. Reasons are read from saved evidence, never generated."),
    ])
    for row in detail_rows:
        identifier = row["id"]
        lines.extend(["", f"### {localize('사례', 'Case')} {_cell(identifier)}", "", f"{localize('태그', 'Tags')}: {_cell(', '.join(row['tags']))}", "", localize("**질문**", "**Question**"), _fence(cases[identifier]["query"]), ""])
        if identifier in before:
            lines.extend([localize("**이전 최종 응답**", "**Previous final response**"), _fence(before[identifier]["raw_output"]), ""])
        turns = captures[identifier].get("turns", [])
        if not isinstance(turns, list) or any(
            not isinstance(turn, dict) or not isinstance(turn.get("input"), str)
            or not isinstance(turn.get("raw_output"), str) for turn in turns
        ):
            raise LabError(f"대화 기록의 입력/응답 형식이 올바르지 않습니다: {identifier}")
        if len(turns) > 1:
            for number, turn in enumerate(turns, 1):
                lines.extend([f"**{localize('대화', 'Turn')} {number} · {localize('입력 출처', 'input source')}: {_cell(turn.get('input_source', localize('미기록', 'not recorded')))}**",
                              _fence(turn["input"]), _fence(turn["raw_output"]), ""])
        else:
            lines.extend([localize("**실제 응답**", "**Actual response**"), _fence(row["raw_output"]), ""])
        lines.extend([
            localize("**권위 있는 정책 문맥(평가자용)**", "**Authoritative policy context (evaluator-only)**"), _context_excerpt(cases[identifier]["context"]), "",
            localize("**이 응답의 관측 검색 문맥**", "**Observed retrieval context for this response**"), _context_excerpt(row.get("retrieved_context", "")), "",
        ])
        response = row["response"] if isinstance(row["response"], dict) else {}
        lines.append(f"{localize('기대 route', 'Expected route')}: {_cell(row['expected']['route'])} / {localize('실제 route', 'actual route')}: {_cell(response.get('route', localize('형식 오류', 'format error')))}")
        lines.extend(["", localize("| 평가 | 현재 점수 | 이전 점수 |", "| Metric | Current score | Previous score |"), "|---|---:|---:|"])
        for metric, (label, _) in semantics.items():
            old = _score(before[identifier], metric) if identifier in before else localize("비교 없음", "No comparison")
            lines.append(f"| {label} | {_score(row, metric)} | {old} |")
        reasons = row["judge"].get("reasons", {})
        if not isinstance(reasons, dict):
            raise LabError(f"Judge 이유 형식이 올바르지 않습니다: {identifier}")
        for kind, label in (
            ("policy", localize("업무 정확성·질문 적합성 이유", "Policy-correctness and relevance reasons")),
            ("retrieval", localize("검색 근거성 이유", "Retrieval-groundedness reasons")),
        ):
            lines.extend(["", f"**{label}**", _fence(reasons.get(kind) or localize("미기록 — 이유를 추정하거나 생성하지 않습니다.", "Not recorded; reasons are not inferred or generated."))])
        problems = [row["api_error"], row["parse_error"], row["judge"]["error"], *row["schema_errors"], *row["rule_failures"]]
        problems.extend(f"{key}: {value}" for key, value in row["judge"].get("metric_errors", {}).items())
        lines.append(
            f"\n{localize('중요 실패 표시', 'Critical-failure flag')}: {_cell(row['judge'].get('critical_failure', localize('미기록', 'not recorded')))}; "
            f"{localize('오류/규칙', 'errors / rules')}: {_cell('; '.join(str(value) for value in problems if value) or localize('기록된 오류 없음', 'no recorded errors'))}"
        )
        actions = [rules[metric][1] for metric, check_name in zip(rules, ("format", "route", "citations", "human_flag", "forbidden_claims")) if not row["checks"][check_name]]
        if row["judge"].get("critical_failure") is True:
            actions.insert(0, localize("중요 실패입니다. 후보 사용을 보류하고 실제 문장·실행 권한·정책 경계를 먼저 검토합니다.", "Critical failure: hold the candidate and review the actual claim, execution authority, and policy boundaries first."))
        for metric, (_, action) in semantics.items():
            value = _usable_judge_score(row, metric)
            threshold = _mean_threshold(gates, metric)
            if value is not None and threshold is not None and value < threshold:
                actions.append(action)
        lines.append(localize("\n**개선할 점(제안, 자동 변경 아님):** ", "\n**Suggested improvements (not automatic changes):** ") + (
            " ".join(dict.fromkeys(actions)) if actions else localize(
                "누락·오류와 위 Judge 이유를 먼저 확인합니다. 문제가 없다면 기존 행동을 유지하고 회귀를 살펴봅니다.",
                "First inspect missing values, errors, and Judge reasons above. If no problem is found, preserve the behavior and check for regressions.",
            )
        ))
    lines.extend([
        "", localize("## 5. 사람이 결정할 것", "## 5. Decisions for human review"), "",
        localize("대표 사례의 실제 문장과 근거를 확인한 뒤 유지·개선·보류 이유를 기록합니다. 최종 holdout을 본 뒤 그 질문으로 지침을 튜닝하거나 같은 시험을 재추첨하지 않습니다.", "Review actual claims and evidence, then record why to retain, improve, or hold the candidate. Do not tune instructions to a viewed final holdout or draw the same test again."),
        localize("이 명령은 지침·점수·게이트·승인 기록을 바꾸거나 작업을 제출하지 않습니다. 공유 전 원본 질문·응답에 민감정보가 없는지 확인해야 합니다.", "This command changes no instructions, scores, gates, or approval records and submits no jobs. Check original questions/responses for sensitive information before sharing."),
        localize("정책 참조·기대 route는 평가자용입니다. 생성 에이전트 입력으로 복사하지 않습니다. 문맥 발췌는 표시용이며 저장된 전체 평가 근거를 대체하지 않습니다.", "Policy references and expected routes are evaluator-only. Do not copy them into generation input. Display excerpts do not replace complete saved evaluation evidence."),
        localize("전체 근거: 같은 run의 summary.json, outputs.jsonl, judge-scores.json. 교정은 calibration 보고서, 최종 확정은 governance status에서 별도로 확인합니다.", "Full evidence: this run's summary.json, outputs.jsonl, and judge-scores.json. Check calibration reports and governance status separately for calibration and finalization."),
    ])
    return "\n".join(lines) + "\n"


def explain_run(run_id: str, *, baseline_id: str | None = None, case_id: str | None = None) -> str:
    summary, cases, captures, gates, recorded_verdict = _load(run_id)
    baseline = _load(baseline_id)[0] if baseline_id is not None else None
    return format_explanation(summary, cases, captures, gates, baseline=baseline, case_id=case_id, recorded_verdict=recorded_verdict)
