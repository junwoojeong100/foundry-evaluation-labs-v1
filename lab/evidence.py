"""Offline, stdlib-only evidence for the bilingual Foundry workshop.

Public contracts:
* ``score_row`` takes a dataset case and the *unmodified* model output. Invalid
  model JSON is evidence, not an exception; malformed evaluator inputs raise
  ValueError. ``expected`` records route/citations/literal forbidden claims.
* ``summarize`` accepts only score_row results, rejects duplicate/mixed-split
  rows, and returns ``{metadata, rows, metrics}``. It adds metadata.sample_count.
* Metadata requires run_id, stage, split, dataset_sha256, model_deployment,
  prompt_sha256, knowledge_sha256 and judge. Before managed evaluation, judge
  may be null; summaries remain available and release comparisons HOLD.
  Otherwise judge metadata declares model_deployment, prompt_sha256 and scale
  ({groundedness: [low, high], relevance: [low, high]}; a shared [low, high]
  remains accepted, or all three fields may be null for a disabled judge).
  Paired comparisons additionally require explicit judge version, settings
  (object), and provenance (nonempty string/object) for every non-null judge.
  A smoke run uses split="smoke", source_split=<actual dataset split>; rows
  retain their original split. Optional metadata.row_ids must match all rows.
* Row judge input is {groundedness: number|null, relevance: number|null,
  error: string|null}; additional JSON provenance is retained. Missing scores
  remain null. Scores on failed or schema-invalid responses are not averaged.
* Usage is measured input_tokens/output_tokens/total_tokens (nonnegative
  integers). prompt_tokens/completion_tokens are accepted API aliases. Missing
  measurements stay null; totals and currency costs are never invented.
* ``load_gates`` reads config/gates.json; ``evaluate_gates`` checks one run;
  ``compare_runs`` checks paired identity, candidate gates and regression.
  PASS_FOR_WORKSHOP is never a production-release authorization.
* Pedagogical critical-case gates (not a Microsoft standard) cannot be hidden
  by averages: minimum_critical_rows defaults to 1 (positive integer), and
  judge.critical_minimum_score defaults to {groundedness: 4, relevance: 4}.
  Both optional configuration fields retain these defaults when omitted.
  Explicit per-metric floors must include both metrics with finite 1..5 values.
  Critical rows always need usable scores on declared 1..5 scales, even if
  judge.required_metrics opts out of overall mean gates. Null/error never pass.

Citation checks only compare source IDs. Literal forbidden-claim checks are
case-sensitive substring rules, NOT semantic groundedness or safety graders.
Quantiles use linear interpolation at (n - 1) * q (Hyndman-Fan type 7).
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import NormalDist
from typing import Any

from lab.content import selected_language, text as localize

ROUTES = frozenset({"answer", "clarify", "escalate", "refuse"})
SPLITS = frozenset({"train", "validation", "dev", "test"})
RUN_SPLITS = SPLITS | {"smoke"}
HELDOUT_STAGES = frozenset({"baseline", "iq", "optimized", "tuned", "candidate", "test", "heldout", "release"})
CHECKS = ("format", "route", "citations", "human_flag", "forbidden_claims")
JUDGE_METRICS = ("groundedness", "relevance")
POLICY_METRIC = "policy_correctness"
RATE_METRICS = (
    "format_pass_rate",
    "route_accuracy",
    "citation_pass_rate",
    "human_flag_accuracy",
    "forbidden_claim_pass_rate",
)
DEFAULT_GATES_PATH = Path(__file__).resolve().parents[1] / "config" / "gates.json"
DEFAULT_MINIMUM_CRITICAL_ROWS = 1
DEFAULT_CRITICAL_JUDGE_FLOORS = {"groundedness": 4.0, "relevance": 4.0}
LIMITATIONS = [
    "이 엔진은 오프라인으로 입력 artifact만 평가하며 실제 모델/API 실행 여부를 인증하지 않습니다.",
    "인용 ID의 문자 일치와 포함률은 답변의 groundedness(근거 충실성)를 증명하지 않습니다.",
    "금지 주장은 대소문자를 구분하는 리터럴 부분 문자열 검사이며 의미·안전성 평가가 아닙니다.",
    "PASS_FOR_WORKSHOP은 교육용 판정입니다. 운영 배포 승인 또는 production-ready 주장이 아닙니다.",
    "critical 최소 표본 수와 행별 judge 하한은 워크숍 교육용 정책이며 Microsoft 공식 평가 기준이 아닙니다.",
    "20개 단일 held-out test는 의도적으로 작습니다. 반복 실험·독립 검토·더 큰 표본이 필요합니다.",
    "라우팅 Wilson 95% 구간은 독립 Bernoulli 표본 가정입니다. 그룹 상관·다중 비교·데이터 편향은 반영하지 않습니다.",
    "지연 p50/p95는 관측값의 type-7 선형 보간입니다. 작은 표본의 p95를 운영 SLO로 해석하지 않습니다.",
    "토큰은 API에서 관측된 수만 합산합니다. 누락은 0이 아니며 가격·USD 비용을 추정하지 않습니다.",
]


def _require_fields(value: Any, fields: set[str], label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    missing = fields - value.keys()
    if missing:
        raise ValueError(f"{label} missing fields: {', '.join(sorted(missing))}")


def _text(value: Any, label: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(f"{label} must be {'a' if empty else 'a nonempty'} string")
    return value


def _number(value: Any, label: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{label} must be finite") from exc
    if not math.isfinite(result) or (minimum is not None and result < minimum):
        raise ValueError(f"{label} must be finite and >= {minimum}")
    return result


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def _json_value(value: Any, label: str) -> None:
    def visit(item: Any, ancestors: set[int]) -> None:
        if item is None or isinstance(item, (str, bool)):
            return
        if isinstance(item, (int, float)):
            _number(item, label)
            return
        if isinstance(item, dict) and all(isinstance(key, str) for key in item):
            children = item.values()
        elif isinstance(item, list):
            children = item
        else:
            raise ValueError(f"{label} must contain only finite JSON values")
        identity = id(item)
        if identity in ancestors:
            raise ValueError(f"{label} contains a cycle, not JSON")
        ancestors.add(identity)
        for child in children:
            visit(child, ancestors)
        ancestors.remove(identity)

    try:
        visit(value, set())
    except RecursionError as exc:
        raise ValueError(f"{label} nesting exceeds the supported depth") from exc


def _same_json(left: Any, right: Any) -> bool:
    """JSON equality must not treat true/false as numeric 1/0."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_same_json(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_same_json(a, b) for a, b in zip(left, right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


def observed_model_drift(metadata: dict) -> bool:
    """Recorded drift is terminal evidence, not cleared by later restoration.

    Older captures may lack the explicit marker, so contradictory before/after
    snapshots still invalidate a subsequently rewritten ``completed`` status.
    """
    if metadata.get("model_drift_detected") is True or any(
        metadata.get(field) == "invalid_model_drift"
        for field in ("status", "execution_status", "judge_execution_status")
    ):
        return True
    after = metadata.get("model_snapshot_after")
    return after is not None and not _same_json(metadata.get("model_snapshot"), after)


def _strings(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list of strings")
    for item in value:
        _text(item, label)
    if len(value) != len(set(value)):
        raise ValueError(f"{label} must not contain duplicates")
    return value


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{label} must be a lowercase SHA256 hex digest")
    return value


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json_loads(raw: str) -> Any:
    """Parse JSON without repairs; reject duplicate keys, NaN, and infinities."""
    _text(raw, "JSON text", empty=True)
    try:
        value = json.loads(
            raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant
        )
        _json_value(value, "JSON")
    except RecursionError as exc:
        raise ValueError("JSON nesting exceeds the supported depth") from exc
    return value


def validate_case(case: dict) -> None:
    """Validate the shared dataset contract, without inferring semantic truth."""
    _require_fields(
        case,
        {
            "id", "group_id", "split", "query", "context", "ground_truth",
            "expected_route", "required_citations", "tags",
        },
        "case",
    )
    _json_value(case, "case")
    for field in ("id", "group_id", "query"):
        _text(case[field], f"case.{field}")
    for field in ("context", "ground_truth"):
        _text(case[field], f"case.{field}", empty=True)
    if not isinstance(case["split"], str) or case["split"] not in SPLITS:
        raise ValueError("case.split must be train, validation, dev, or test")
    if not isinstance(case["expected_route"], str) or case["expected_route"] not in ROUTES:
        raise ValueError("case.expected_route is invalid")
    for field in ("required_citations", "tags", "forbidden_claims"):
        _strings(case.get(field, []), f"case.{field}")
    if "follow_up" in case:
        _text(case["follow_up"], "case.follow_up")
        _text(case.get("scripted_user_source"), "case.scripted_user_source")


def _usage(usage: dict | None) -> dict:
    if usage is None:
        return dict.fromkeys(("input_tokens", "output_tokens", "total_tokens"))
    if not isinstance(usage, dict):
        raise ValueError("usage must be an object or null")
    _json_value(usage, "usage")
    result = {}
    for key, alias in (
        ("input_tokens", "prompt_tokens"),
        ("output_tokens", "completion_tokens"),
        ("total_tokens", "total_tokens"),
    ):
        value = usage.get(key, usage.get(alias))
        if key in usage and alias in usage and usage[key] != usage[alias]:
            raise ValueError(f"conflicting usage.{key} and usage.{alias}")
        if value is not None:
            _integer(value, f"usage.{key}")
        result[key] = value
    if all(value is not None for value in result.values()):
        if result["total_tokens"] != result["input_tokens"] + result["output_tokens"]:
            raise ValueError("usage.total_tokens must equal input_tokens + output_tokens")
    return result


def _judge(judge: dict | None) -> dict:
    if judge is None:
        return {"groundedness": None, "relevance": None, "error": None}
    if not isinstance(judge, dict):
        raise ValueError("judge must be an object or null")
    _json_value(judge, "judge")
    result = deepcopy(judge)
    for metric in JUDGE_METRICS:
        value = judge.get(metric)
        result[metric] = None if value is None else _number(value, f"judge.{metric}")
    if POLICY_METRIC in judge:
        value = judge[POLICY_METRIC]
        if value is not None:
            value = _number(value, f"judge.{POLICY_METRIC}")
            if not 1 <= value <= 5:
                raise ValueError("policy_correctness must use the declared 1..5 scale")
        result[POLICY_METRIC] = value
    if "metric_errors" in judge:
        errors = judge["metric_errors"]
        if not isinstance(errors, dict) or not errors.keys() <= {*JUDGE_METRICS, POLICY_METRIC}:
            raise ValueError("judge.metric_errors must use declared metric names")
        for name, value in errors.items():
            _text(value, f"judge.metric_errors.{name}")
    if judge.get("critical_failure") is not None and type(judge["critical_failure"]) is not bool:
        raise ValueError("judge.critical_failure must be boolean or null")
    result.setdefault("error", None)
    if result["error"] is not None:
        _text(result["error"], "judge.error")
    return result


def _schema_errors(response: Any) -> list[str]:
    fields = {"answer", "citations", "route", "needs_human"}
    if not isinstance(response, dict):
        return ["response must be a JSON object"]
    errors = []
    if set(response) != fields:
        errors.append("response must contain exactly answer,citations,route,needs_human")
    if not isinstance(response.get("answer"), str):
        errors.append("answer must be a string")
    citations = response.get("citations")
    if (
        not isinstance(citations, list)
        or not all(isinstance(item, str) and item.strip() for item in citations)
        or len(citations) != len(set(citations))
    ):
        errors.append("citations must be a unique list of nonempty source IDs")
    route = response.get("route")
    if not isinstance(route, str) or route not in ROUTES:
        errors.append("route must be answer,clarify,escalate,refuse")
    if type(response.get("needs_human")) is not bool:
        errors.append("needs_human must be a boolean")
    elif isinstance(route, str) and route in ROUTES:
        if response["needs_human"] != (route == "escalate"):
            errors.append("needs_human must be true if and only if route is escalate")
    return errors


def _response_evidence(
    expected: dict, raw_output: str, known_citations: set[str], error: str | None
) -> dict:
    parse_error = None
    response = None
    try:
        response = strict_json_loads(raw_output)
    except ValueError as exc:
        parse_error = str(exc)
    json_valid = parse_error is None
    schema_errors = _schema_errors(response) if json_valid else []
    schema_valid = json_valid and not schema_errors
    content = response if isinstance(response, dict) else {}
    answer = content.get("answer")
    route = content.get("route")
    human = content.get("needs_human")
    supplied = content.get("citations")
    citations_valid_type = isinstance(supplied, list) and all(
        isinstance(item, str) and bool(item.strip()) for item in supplied
    )
    citations = set(supplied) if citations_valid_type else set()
    required = set(expected["required_citations"])
    missing = sorted(required - citations)
    unknown = sorted(citations - known_citations)
    api_success = error is None
    coverage = len(required & citations) / len(required) if required else 1.0
    if not api_success or not json_valid or not citations_valid_type:
        coverage = 0.0
    forbidden_hits = [
        claim for claim in expected["forbidden_claims"]
        if isinstance(answer, str) and claim in answer
    ]
    checks = {
        "format": api_success and schema_valid,
        "route": api_success and route == expected["route"],
        "citations": (
            api_success and json_valid and citations_valid_type
            and len(supplied) == len(citations) and not missing and not unknown
        ),
        "human_flag": (
            api_success and isinstance(route, str) and route in ROUTES
            and type(human) is bool and human == (route == "escalate")
            and human == (expected["route"] == "escalate")
        ),
        "forbidden_claims": (
            api_success and isinstance(answer, str) and not forbidden_hits
        ),
    }
    return {
        "raw_output": raw_output,
        "response": response,
        "api_error": error,
        "parse_error": parse_error,
        "schema_errors": schema_errors,
        "json_valid": json_valid,
        "schema_valid": schema_valid,
        "checks": checks,
        "citation_coverage": coverage,
        "missing_citations": missing,
        "unknown_citations": unknown,
        "forbidden_claim_hits": forbidden_hits,
        "rule_failures": [name for name in CHECKS if not checks[name]],
    }


def score_row(
    case: dict,
    raw_output: str,
    *,
    known_citations: set[str],
    latency_ms: float | None = None,
    usage: dict | None = None,
    error: str | None = None,
    judge: dict | None = None,
    retrieved_context: str | None = None,
) -> dict:
    """Score one attempt; failed API calls must still be passed here as rows.

    ``error`` denotes an API/transport error, not a judge error. Even if raw
    output is supplied alongside an error, all deterministic checks fail.
    Raw output is always retained verbatim. No API, SDK, or network is used.
    """
    validate_case(case)
    _text(raw_output, "raw_output", empty=True)
    if not isinstance(known_citations, (set, frozenset)):
        raise ValueError("known_citations must be a set of source IDs")
    for source in known_citations:
        _text(source, "known_citations")
    if not set(case["required_citations"]) <= known_citations:
        raise ValueError("case.required_citations contains an unknown source ID")
    if error is not None:
        _text(error, "error")
    if latency_ms is not None:
        latency_ms = _number(latency_ms, "latency_ms", minimum=0)
    expected = {
        "route": case["expected_route"],
        "required_citations": list(case["required_citations"]),
        "forbidden_claims": list(case.get("forbidden_claims", [])),
    }
    case_json = json.dumps(
        case, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    if retrieved_context is not None:
        _text(retrieved_context, "retrieved_context", empty=True)
    return {
        "id": case["id"],
        "group_id": case["group_id"],
        "split": case["split"],
        "tags": list(case["tags"]),
        "case_sha256": hashlib.sha256(case_json.encode("utf-8")).hexdigest(),
        "expected": expected,
        "known_citations": sorted(known_citations),
        **_response_evidence(expected, raw_output, known_citations, error),
        "latency_ms": latency_ms,
        "usage": _usage(usage),
        "judge": _judge(judge),
        **({"retrieved_context": retrieved_context} if retrieved_context is not None else {}),
    }


def _scale_range(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{label} must be [minimum, maximum]")
    low, high = (_number(item, label) for item in value)
    if low >= high:
        raise ValueError(f"{label} minimum must be smaller than maximum")
    return [low, high]


def _scale(value: Any) -> list[float] | dict[str, list[float]] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        _require_fields(value, set(JUDGE_METRICS), "judge.scale")
        if set(value) != set(JUDGE_METRICS):
            raise ValueError("judge.scale contains unsupported metric names")
        return {
            name: _scale_range(value[name], f"judge.scale.{name}")
            for name in JUDGE_METRICS
        }
    return _scale_range(value, "judge.scale")


def _metric_scale(value: Any, name: str) -> list[float] | None:
    return value.get(name) if isinstance(value, dict) else value


def _metadata(metadata: dict, count: int) -> dict:
    _require_fields(
        metadata,
        {
            "run_id", "stage", "split", "dataset_sha256", "model_deployment",
            "prompt_sha256", "knowledge_sha256", "judge",
        },
        "metadata",
    )
    _json_value(metadata, "metadata")
    for name in ("run_id", "stage", "model_deployment"):
        _text(metadata[name], f"metadata.{name}")
    if not isinstance(metadata["split"], str) or metadata["split"] not in RUN_SPLITS:
        raise ValueError("metadata.split is invalid")
    if metadata["split"] == "smoke" and "source_split" not in metadata:
        raise ValueError("smoke metadata requires source_split")
    source_split = metadata.get("source_split", metadata["split"])
    if not isinstance(source_split, str) or source_split not in SPLITS:
        raise ValueError("metadata.source_split is invalid")
    if metadata["split"] != "smoke" and source_split != metadata["split"]:
        raise ValueError("metadata.source_split differs from split (possible leakage)")
    if "row_ids" in metadata:
        _strings(metadata["row_ids"], "metadata.row_ids")
        if len(metadata["row_ids"]) != count:
            raise ValueError("metadata.row_ids count does not match all attempted rows")
    if "status" in metadata:
        _text(metadata["status"], "metadata.status")
    for name in ("dataset_sha256", "prompt_sha256", "knowledge_sha256"):
        _sha256(metadata[name], f"metadata.{name}")
    judge = metadata["judge"]
    if judge is not None:
        _require_fields(judge, {"model_deployment", "prompt_sha256", "scale"}, "metadata.judge")
        if judge["model_deployment"] is not None:
            _text(judge["model_deployment"], "metadata.judge.model_deployment")
        if judge["prompt_sha256"] is not None:
            _sha256(judge["prompt_sha256"], "metadata.judge.prompt_sha256")
        scale = _scale(judge["scale"])
        declared = [judge["model_deployment"] is not None, judge["prompt_sha256"] is not None, scale is not None]
        if any(declared) and not all(declared):
            raise ValueError("judge deployment, prompt SHA256 and scale must be declared together")
    if "sample_count" in metadata:
        _integer(metadata["sample_count"], "metadata.sample_count", minimum=1)
        if metadata["sample_count"] != count:
            raise ValueError("metadata.sample_count does not match rows")
    result = deepcopy(metadata)
    result["sample_count"] = count
    return result


def _comparison_judge(judge: dict | None) -> None:
    if judge is None:
        return
    _require_fields(judge, {"version", "settings", "provenance"}, "metadata.judge for comparison")
    if judge["version"] is not None:
        _text(judge["version"], "metadata.judge.version")
    elif judge["model_deployment"] is not None:
        raise ValueError("an enabled judge requires an explicit version")
    if not isinstance(judge["settings"], dict):
        raise ValueError("metadata.judge.settings must be an object")
    provenance = judge["provenance"]
    if isinstance(provenance, str):
        _text(provenance, "metadata.judge.provenance")
    elif not isinstance(provenance, dict) or not provenance:
        raise ValueError("metadata.judge.provenance must be a nonempty string or object")


def _validate_row(row: dict) -> None:
    _require_fields(
        row,
        {
            "id", "group_id", "split", "tags", "case_sha256", "expected",
            "known_citations", "raw_output", "response", "api_error", "parse_error",
            "schema_errors", "json_valid", "schema_valid", "checks", "citation_coverage",
            "missing_citations", "unknown_citations", "forbidden_claim_hits",
            "rule_failures", "latency_ms", "usage", "judge",
        },
        "row",
    )
    _json_value(row, "row")
    for name in ("id", "group_id"):
        _text(row[name], f"row.{name}")
    _sha256(row["case_sha256"], "row.case_sha256")
    if not isinstance(row["split"], str) or row["split"] not in SPLITS:
        raise ValueError("row.split is invalid")
    _strings(row["tags"], "row.tags")
    expected = row["expected"]
    _require_fields(expected, {"route", "required_citations", "forbidden_claims"}, "row.expected")
    if not isinstance(expected["route"], str) or expected["route"] not in ROUTES:
        raise ValueError("row.expected.route is invalid")
    for name in ("required_citations", "forbidden_claims"):
        _strings(expected[name], f"row.expected.{name}")
    known = set(_strings(row["known_citations"], "row.known_citations"))
    if not set(expected["required_citations"]) <= known:
        raise ValueError("row.expected.required_citations contains unknown sources")
    _text(row["raw_output"], "row.raw_output", empty=True)
    if row["api_error"] is not None:
        _text(row["api_error"], "row.api_error")
    _require_fields(row["checks"], set(CHECKS), "row.checks")
    if set(row["checks"]) != set(CHECKS) or any(type(v) is not bool for v in row["checks"].values()):
        raise ValueError("row.checks must contain exactly the boolean rule checks")
    for name in ("json_valid", "schema_valid"):
        if type(row[name]) is not bool:
            raise ValueError(f"row.{name} must be boolean")
    derived = _response_evidence(expected, row["raw_output"], known, row["api_error"])
    if any(not _same_json(row[key], value) for key, value in derived.items()):
        raise ValueError(f"row {row['id']} evidence does not match its raw output")
    if row["latency_ms"] is not None:
        _number(row["latency_ms"], "row.latency_ms", minimum=0)
    if _usage(row["usage"]) != row["usage"]:
        raise ValueError("row.usage must contain canonical measured token fields")
    if _judge(row["judge"]) != row["judge"]:
        raise ValueError("row.judge must contain groundedness, relevance and error")
    if "retrieved_context" in row:
        _text(row["retrieved_context"], "row.retrieved_context", empty=True)


def wilson_interval(successes: int, total: int, confidence: float = 0.95) -> dict:
    """Two-sided Wilson score interval; independent Bernoulli assumption."""
    _integer(total, "total", minimum=1)
    _integer(successes, "successes")
    if successes > total:
        raise ValueError("successes must be <= total")
    confidence = _number(confidence, "confidence")
    probability = (1 + confidence) / 2
    if not 0 < confidence < 1 or not 0 < probability < 1:
        raise ValueError("confidence must be strictly between 0 and 1")
    z = NormalDist().inv_cdf(probability)
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    # The score interval is exactly 0 at no successes and exactly 1 at all successes;
    # pinning those ends keeps the result identical across floating-point libraries.
    return {
        "lower": 0.0 if successes == 0 else max(0.0, center - half),
        "upper": 1.0 if successes == total else min(1.0, center + half),
        "confidence": confidence,
        "method": "Wilson score, two-sided; independent Bernoulli assumption",
    }


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return _number(math.fsum(value / len(values) for value in values), "mean")


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    weight = position - lower
    return _number(values[lower] * (1 - weight) + values[upper] * weight, "quantile")


def _critical(row: dict, configured_tags: list[str] | None = None) -> bool:
    return any(
        tag == "critical" or tag.startswith("critical:")
        or tag in (configured_tags or [])
        for tag in row["tags"]
    )


def _rates(rows: list[dict]) -> dict:
    count = len(rows)
    values = {
        metric: (sum(row["checks"][check] for row in rows) / count if count else None)
        for metric, check in zip(RATE_METRICS, CHECKS)
    }
    return {
        "sample_count": count,
        **values,
        "rule_failure_count": sum(bool(row["rule_failures"]) for row in rows),
    }


def _usable_judge_score(row: dict, name: str) -> float | None:
    if (
        not row["checks"]["format"] or row["judge"]["error"] is not None
        or row["judge"].get("metric_errors", {}).get(name)
        or (name == "groundedness" and "retrieved_context" in row and not row["retrieved_context"].strip())
    ):
        return None
    return row["judge"].get(name)


def _judge_measurements(rows: list[dict], name: str, scale: Any) -> dict:
    values = [
        value for row in rows
        if (value := _usable_judge_score(row, name)) is not None
    ]
    count = len(values)
    return {
        "mean": _mean(values),
        "scored_count": count,
        "missing_count": len(rows) - count,
        "coverage": count / len(rows),
        "status": "unavailable" if not count else "complete" if count == len(rows) else "partial",
        "scale": deepcopy(scale),
    }


def summarize(rows: list[dict], *, metadata: dict) -> dict:
    """Aggregate every attempted row; unavailable judge values are never zero."""
    if not isinstance(rows, list) or not rows:
        raise ValueError("rows must be a nonempty list; empty datasets are not evidence")
    metadata = _metadata(metadata, len(rows))
    identifiers = set()
    judge_scale = None if metadata["judge"] is None else metadata["judge"]["scale"]
    scale = _scale(judge_scale)
    for row in rows:
        _validate_row(row)
        if row["id"] in identifiers:
            raise ValueError(f"duplicate row id: {row['id']}")
        identifiers.add(row["id"])
        if row["split"] != metadata.get("source_split", metadata["split"]):
            raise ValueError("row split differs from metadata source split (possible leakage)")
        for metric in JUDGE_METRICS:
            value = row["judge"][metric]
            metric_scale = _metric_scale(scale, metric)
            if value is not None and (
                metric_scale is None or not metric_scale[0] <= value <= metric_scale[1]
            ):
                raise ValueError(f"row {row['id']} judge.{metric} is outside the declared scale")
        value = row["judge"].get(POLICY_METRIC)
        if value is not None and _metric_scale(scale, POLICY_METRIC) != [1, 5]:
            raise ValueError("policy_correctness requires an explicit shared 1..5 judge scale")
    if "row_ids" in metadata and set(metadata["row_ids"]) != identifiers:
        raise ValueError("metadata.row_ids do not match all attempted row IDs")
    latencies = [row["latency_ms"] for row in rows if row["latency_ms"] is not None]
    critical_rows = [row for row in rows if _critical(row)]
    tags = sorted({tag for row in rows for tag in row["tags"]})
    tokens = {}
    for name in ("input_tokens", "output_tokens", "total_tokens"):
        measured = [row["usage"][name] for row in rows if row["usage"][name] is not None]
        tokens[name] = {
            "sum": sum(measured) if measured else None,
            "measured_rows": len(measured),
            "missing_rows": len(rows) - len(measured),
        }
    metrics = {
        **_rates(rows),
        "citation_coverage_mean": _mean([row["citation_coverage"] for row in rows]),
        "route_accuracy_wilson_95": wilson_interval(sum(row["checks"]["route"] for row in rows), len(rows)),
        "api_error_count": sum(row["api_error"] is not None for row in rows),
        "format_error_count": sum(not row["schema_valid"] for row in rows),
        "error_count": sum(row["api_error"] is not None or not row["schema_valid"] for row in rows),
        "judge_error_count": sum(
            row["judge"]["error"] is not None or any(
                value != "retrieval_not_observed" for value in row["judge"].get("metric_errors", {}).values()
            ) for row in rows
        ),
        "unknown_citation_row_count": sum(bool(row["unknown_citations"]) for row in rows),
        "forbidden_claim_row_count": sum(bool(row["forbidden_claim_hits"]) for row in rows),
        "critical": _rates(critical_rows),
        "critical_rule_failure_count": sum(bool(row["rule_failures"]) for row in critical_rows),
        "critical_subsets": {
            tag: _rates([row for row in rows if tag in row["tags"]])
            for tag in tags if tag == "critical" or tag.startswith("critical:")
        },
        "by_tag": {tag: _rates([row for row in rows if tag in row["tags"]]) for tag in tags},
        "judge": {
            name: _judge_measurements(rows, name, _metric_scale(judge_scale, name))
            for name in JUDGE_METRICS
        },
        "business_policy": {
            **_judge_measurements(rows, POLICY_METRIC, _metric_scale(judge_scale, POLICY_METRIC)),
            "critical_failure_count": sum(row["judge"].get("critical_failure") is True for row in rows),
            "critical_failure_ids": [row["id"] for row in rows if row["judge"].get("critical_failure") is True],
            "semantics": "authoritative_policy_and_expected_task/not_retrieval_support",
        },
        "latency_ms": {
            "measured_rows": len(latencies),
            "missing_rows": len(rows) - len(latencies),
            "p50": _quantile(latencies, 0.50),
            "p95": _quantile(latencies, 0.95),
            "method": "Hyndman-Fan type 7: linear interpolation at (n - 1) * q",
        },
        "tokens": tokens,
    }
    result = {"metadata": metadata, "rows": deepcopy(rows), "metrics": metrics}
    _json_value(result, "summary")
    return result


def _validate_run(run: dict, *, comparison: bool = False) -> dict:
    _require_fields(run, {"metadata", "rows", "metrics"}, "run")
    _json_value(run, "run")
    _require_fields(run["metadata"], {"sample_count"}, "run.metadata")
    expected = summarize(run["rows"], metadata=run["metadata"])
    if not isinstance(run["metrics"], dict) or not _same_json(run["metrics"], expected["metrics"]):
        raise ValueError("run.metrics are missing, altered, or inconsistent with rows")
    if comparison:
        _comparison_judge(run["metadata"]["judge"])
    return expected


def _validate_gates(gates: dict) -> None:
    _require_fields(
        gates,
        {"version", "minimums", "maximums", "critical_tags", "judge", "regression", "minimum_test_rows"},
        "gates",
    )
    _json_value(gates, "gates")
    _text(gates["version"], "gates.version")
    _integer(gates["minimum_test_rows"], "gates.minimum_test_rows", minimum=1)
    _integer(
        gates.get("minimum_critical_rows", DEFAULT_MINIMUM_CRITICAL_ROWS),
        "gates.minimum_critical_rows", minimum=1,
    )
    _strings(gates["critical_tags"], "gates.critical_tags")
    _require_fields(gates["minimums"], set(RATE_METRICS), "gates.minimums")
    if set(gates["minimums"]) != set(RATE_METRICS):
        raise ValueError("gates.minimums contains unsupported metrics")
    for name, value in gates["minimums"].items():
        if not 0 <= _number(value, f"gates.minimums.{name}") <= 1:
            raise ValueError("rate thresholds must be between 0 and 1")
    _require_fields(gates["maximums"], {"error_count", "critical_rule_failure_count"}, "gates.maximums")
    if set(gates["maximums"]) != {"error_count", "critical_rule_failure_count"}:
        raise ValueError("gates.maximums contains unsupported metrics")
    for name, value in gates["maximums"].items():
        _integer(value, f"gates.maximums.{name}")
    judge = gates["judge"]
    _require_fields(judge, {"required_metrics", "minimum_mean", "scale"}, "gates.judge")
    _strings(judge["required_metrics"], "gates.judge.required_metrics")
    if not set(judge["required_metrics"]) <= set(JUDGE_METRICS):
        raise ValueError("unsupported judge metric")
    declared_gate_scale = _scale(judge["scale"])
    if any(_metric_scale(declared_gate_scale, name) != [1.0, 5.0] for name in JUDGE_METRICS):
        raise ValueError("workshop judge gates require declared scale [1, 5]")
    _require_fields(judge["minimum_mean"], set(JUDGE_METRICS), "gates.judge.minimum_mean")
    for name in JUDGE_METRICS:
        if not 1 <= _number(judge["minimum_mean"][name], f"gates.judge.{name}") <= 5:
            raise ValueError("judge thresholds must be on the declared 1..5 scale")
    critical_floors = judge.get("critical_minimum_score", DEFAULT_CRITICAL_JUDGE_FLOORS)
    _require_fields(critical_floors, set(JUDGE_METRICS), "gates.judge.critical_minimum_score")
    if set(critical_floors) != set(JUDGE_METRICS):
        raise ValueError("gates.judge.critical_minimum_score contains unsupported metrics")
    for name, value in critical_floors.items():
        if not 1 <= _number(value, f"gates.judge.critical_minimum_score.{name}") <= 5:
            raise ValueError("critical judge floors must be on the declared 1..5 scale")
    regression = gates["regression"]
    _require_fields(regression, {"maximum_drop", "maximum_judge_drop", "maximum_latency_p95_increase_ratio"}, "gates.regression")
    _require_fields(regression["maximum_drop"], set(RATE_METRICS), "gates.regression.maximum_drop")
    if set(regression["maximum_drop"]) != set(RATE_METRICS):
        raise ValueError("unsupported regression metric")
    for name, value in regression["maximum_drop"].items():
        if not 0 <= _number(value, f"gates.regression.{name}") <= 1:
            raise ValueError("rate regression margins must be between 0 and 1")
    _require_fields(regression["maximum_judge_drop"], set(JUDGE_METRICS), "gates.regression.maximum_judge_drop")
    for name, value in regression["maximum_judge_drop"].items():
        _number(value, f"gates.regression.{name}", minimum=0)
    latency = regression["maximum_latency_p95_increase_ratio"]
    if latency is not None:
        _number(latency, "maximum_latency_p95_increase_ratio", minimum=0)
    if "business_policy" in gates:
        policy = gates["business_policy"]
        _require_fields(policy, {"required_for_contract", "minimum_mean", "critical_minimum_score"}, "gates.business_policy")
        _text(policy["required_for_contract"], "gates.business_policy.required_for_contract")
        for name in ("minimum_mean", "critical_minimum_score"):
            if not 1 <= _number(policy[name], f"gates.business_policy.{name}") <= 5:
                raise ValueError("business policy floors must be on the 1..5 scale")
    if "sample_contract" in gates:
        sample = gates["sample_contract"]
        _require_fields(sample, {"id", "version", "purpose", "minimum_rows"}, "gates.sample_contract")
        for field in ("id", "version", "purpose"):
            _text(sample[field], f"gates.sample_contract.{field}")
        _strings(sample.get("limitations", []), "gates.sample_contract.limitations")
        _integer(sample["minimum_rows"], "gates.sample_contract.minimum_rows", minimum=1)
        if sample["minimum_rows"] != gates["minimum_test_rows"]:
            raise ValueError("gate minimum must match its explicit sample contract")


def load_gates(path: Path | None = None) -> dict:
    """Read a strict JSON gate file; missing/malformed files raise ValueError."""
    path = DEFAULT_GATES_PATH if path is None else Path(path)
    try:
        gates = strict_json_loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read gate configuration: {path}") from exc
    _validate_gates(gates)
    return gates


def _at_least(value: float, threshold: float) -> bool:
    return value >= threshold or math.isclose(value, threshold, rel_tol=0, abs_tol=1e-12)


def _at_most(value: float, threshold: float) -> bool:
    return value <= threshold or math.isclose(value, threshold, rel_tol=0, abs_tol=1e-12)


def evaluate_gates(summary: dict, gates: dict) -> dict:
    """Apply educational gates; never conceal critical failures behind means.

    critical_judge exposes the minimum observed score, unavailable IDs and
    below-floor IDs per metric. Floors apply independently of required_metrics.
    No critical examples, missing scores, invalid responses or judge errors HOLD.
    """
    run = _validate_run(summary)
    _validate_gates(gates)
    metadata, metrics = run["metadata"], run["metrics"]
    checks = []

    def check(name: str, passed: bool, actual: Any, required: Any) -> None:
        checks.append({"name": name, "passed": passed, "actual": actual, "required": required})

    heldout = (
        metadata["split"] == "test"
        and metadata["stage"].casefold() in HELDOUT_STAGES
    )
    check("heldout_test_only", heldout, {"split": metadata["split"], "stage": metadata["stage"]},
          "split=test; stage=baseline|iq|optimized|tuned|candidate|test|heldout|release (never smoke/dev)")
    if "status" in metadata:
        check("run_completed", metadata["status"] in {"completed", "completed_with_errors"},
              metadata["status"], "completed or completed_with_errors; every attempted row included")
    check("no_observed_model_drift", not observed_model_drift(metadata), {
        "model_drift_detected": metadata.get("model_drift_detected"),
        "model_snapshot": metadata.get("model_snapshot"),
        "model_snapshot_after": metadata.get("model_snapshot_after"),
        "judge_execution_status": metadata.get("judge_execution_status"),
    }, "no recorded drift; restoring a deployment never revalidates affected captures")
    check("judge_metadata_available", metadata["judge"] is not None,
          metadata["judge"] is not None, "declared judge metadata; null is unavailable")
    check("minimum_test_rows", len(run["rows"]) >= gates["minimum_test_rows"],
          len(run["rows"]), gates["minimum_test_rows"])
    for name, threshold in gates["minimums"].items():
        check(name, _at_least(metrics[name], threshold), metrics[name], threshold)
    configured_critical = [row for row in run["rows"] if _critical(row, gates["critical_tags"])]
    minimum_critical_rows = gates.get("minimum_critical_rows", DEFAULT_MINIMUM_CRITICAL_ROWS)
    check("minimum_critical_rows", len(configured_critical) >= minimum_critical_rows,
          len(configured_critical), minimum_critical_rows)
    critical_failures = sum(bool(row["rule_failures"]) for row in configured_critical)
    for name, threshold in gates["maximums"].items():
        actual = critical_failures if name == "critical_rule_failure_count" else metrics[name]
        check(name, actual <= threshold, actual, threshold)
    for name in gates["judge"]["required_metrics"]:
        measurement = metrics["judge"][name]
        check(f"{name}_all_rows", measurement["scored_count"] == len(run["rows"]),
              measurement["scored_count"], len(run["rows"]))
        required_scale = _metric_scale(gates["judge"]["scale"], name)
        check(f"{name}_scale", measurement["scale"] == required_scale,
              measurement["scale"], required_scale)
        value = measurement["mean"]
        threshold = gates["judge"]["minimum_mean"][name]
        check(f"{name}_mean", value is not None and _at_least(value, threshold), value, threshold)
    critical_judge = {}
    critical_floors = gates["judge"].get("critical_minimum_score", DEFAULT_CRITICAL_JUDGE_FLOORS)
    for name, floor in critical_floors.items():
        scores = {row["id"]: _usable_judge_score(row, name) for row in configured_critical}
        observed = [value for value in scores.values() if value is not None]
        unavailable_ids = sorted(identifier for identifier, value in scores.items() if value is None)
        declared_scale = metrics["judge"][name]["scale"]
        required_scale = _metric_scale(gates["judge"]["scale"], name)
        scale_compatible = declared_scale == required_scale
        below_floor_ids = sorted(
            identifier for identifier, value in scores.items()
            if scale_compatible and value is not None and not _at_least(value, floor)
        )
        passed = bool(scores) and scale_compatible and not unavailable_ids and not below_floor_ids
        measurement = {
            "minimum_required": floor,
            "minimum_observed": min(observed) if observed else None,
            "scored_count": len(observed),
            "missing_count": len(unavailable_ids),
            "unavailable_ids": unavailable_ids,
            "below_floor_ids": below_floor_ids,
            "scale": deepcopy(declared_scale),
            "required_scale": deepcopy(required_scale),
            "scale_compatible": scale_compatible,
            "status": "unavailable" if not observed else "partial" if unavailable_ids else "complete",
            "passed": passed,
        }
        critical_judge[name] = measurement
        check(f"critical_{name}_floor", passed, measurement, floor)
    if metadata["judge"] is None:
        check("judge_provenance", False, None, "explicit version, settings and provenance")
    else:
        try:
            _comparison_judge(metadata["judge"])
        except ValueError as exc:
            check("judge_provenance", False, str(exc), "explicit version, settings and provenance")
        else:
            check("judge_provenance", True, metadata["judge"], "explicit version, settings and provenance")
    policy_gates = gates.get("business_policy")
    if policy_gates and metadata.get("evaluation_contract_version") == policy_gates["required_for_contract"]:
        policy = metrics["business_policy"]
        check("policy_correctness_all_rows", policy["scored_count"] == len(run["rows"]),
              policy["scored_count"], len(run["rows"]))
        check("policy_correctness_mean",
              policy["mean"] is not None and _at_least(policy["mean"], policy_gates["minimum_mean"]),
              policy["mean"], policy_gates["minimum_mean"])
        bad_ids = [
            row["id"] for row in configured_critical
            if (value := _usable_judge_score(row, POLICY_METRIC)) is None
            or not _at_least(value, policy_gates["critical_minimum_score"])
        ]
        check("critical_policy_correctness_floor", bool(configured_critical) and not bad_ids,
              bad_ids, policy_gates["critical_minimum_score"])
        check("no_semantic_critical_failures", policy["critical_failure_count"] == 0,
              policy["critical_failure_ids"], [])
        check("semantic_critical_decisions_complete",
              all(type(row["judge"].get("critical_failure")) is bool for row in run["rows"]),
              sum(type(row["judge"].get("critical_failure")) is bool for row in run["rows"]), len(run["rows"]))
        check("actual_retrieval_provenance", all("retrieved_context" in row for row in run["rows"]),
              sum("retrieved_context" in row for row in run["rows"]), len(run["rows"]))
        check("fresh_holdout_bound", bool(metadata.get("freeze_id") and metadata.get("freeze_sha256") and metadata.get("holdout_id")),
              {"freeze_id": metadata.get("freeze_id"), "holdout_id": metadata.get("holdout_id")},
              "one exact freeze and one post-freeze registered holdout attempt")
    sample_contract = gates.get("sample_contract")
    if sample_contract is not None:
        sample_hash = hashlib.sha256(json.dumps(
            sample_contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
        check(
            "fresh_sample_contract_bound",
            metadata.get("sample_contract_sha256") == sample_hash
            and bool(metadata.get("freeze_id") and metadata.get("freeze_sha256") and metadata.get("holdout_id"))
            and bool(policy_gates)
            and metadata.get("evaluation_contract_version") == policy_gates["required_for_contract"],
            metadata.get("sample_contract_sha256"), sample_hash,
        )
    outcome = "PASS_FOR_WORKSHOP" if all(item["passed"] for item in checks) else "HOLD"
    return {
        "outcome": outcome,
        "execution_status": metadata.get("status", "not_recorded"),
        "quality_status": outcome,
        "manual_operational_approval": "not_granted",
        "access_blockers": deepcopy(metadata.get("access_blockers", [])),
        "scope": "workshop_only",
        "production_ready": False,
        "release_eligible": heldout,
        "checks": checks,
        "critical_sample_count": len(configured_critical),
        "minimum_critical_rows": minimum_critical_rows,
        "critical_judge": critical_judge,
        "sample_contract": deepcopy(sample_contract),
        "limitations": [
            limitation for limitation in LIMITATIONS
            if not sample_contract or "20개 단일 held-out test" not in limitation
        ] + (list(sample_contract.get("limitations", [])) if sample_contract else []),
    }


def compare_runs(baseline: dict, candidate: dict, gates: dict) -> dict:
    """Compare strictly paired artifacts; malformed/unpaired inputs raise ValueError.

    Drop is baseline minus candidate; ``drop <= maximum_drop`` is inclusive
    (absolute floating-point tolerance 1e-12). Order of identical IDs may differ.
    Model/prompt/knowledge changes are recorded, never mistaken for paired keys.
    An explicitly null judge on either run returns HOLD with
    judge_comparison.status="unavailable"; two declared judges must match.
    """
    baseline = _validate_run(baseline, comparison=True)
    candidate = _validate_run(candidate, comparison=True)
    _validate_gates(gates)
    left, right = baseline["metadata"], candidate["metadata"]
    for name in ("dataset_sha256", "split", "sample_count"):
        if not _same_json(left[name], right[name]):
            raise ValueError(f"paired comparison requires identical {name}")
    if left.get("source_split", left["split"]) != right.get("source_split", right["split"]):
        raise ValueError("paired comparison requires identical source_split")
    judge_comparable = left["judge"] is not None and right["judge"] is not None
    if judge_comparable and not _same_json(left["judge"], right["judge"]):
        raise ValueError("paired comparison requires identical judge")
    before = {row["id"]: row for row in baseline["rows"]}
    after = {row["id"]: row for row in candidate["rows"]}
    if before.keys() != after.keys():
        raise ValueError("paired comparison requires identical row IDs")
    for identifier in before:
        for field in ("case_sha256", "group_id", "split", "tags", "expected"):
            if before[identifier][field] != after[identifier][field]:
                raise ValueError(f"paired case {identifier} differs in {field}")
        if (
            set(before[identifier]["known_citations"]) != set(after[identifier]["known_citations"])
            and left["knowledge_sha256"] == right["knowledge_sha256"]
        ):
            raise ValueError("changed citation catalog requires a recorded knowledge_sha256 change")
    gate = evaluate_gates(candidate, gates)
    model_stable = not observed_model_drift(left) and not observed_model_drift(right)
    regression_checks = []

    def regression(name: str, old: float | None, new: float | None, margin: float) -> None:
        drop = None if old is None or new is None else old - new
        regression_checks.append({
            "metric": name, "baseline": old, "candidate": new,
            "drop": drop, "maximum_drop": margin,
            "status": "unavailable" if drop is None else "available",
            "passed": drop is not None and _at_most(drop, margin),
        })

    for name, margin in gates["regression"]["maximum_drop"].items():
        regression(name, baseline["metrics"][name], candidate["metrics"][name], margin)
    for name in gates["judge"]["required_metrics"]:
        old = baseline["metrics"]["judge"][name]
        new = candidate["metrics"]["judge"][name]
        required_scale = _metric_scale(gates["judge"]["scale"], name)
        available = (
            old["scored_count"] == left["sample_count"]
            and new["scored_count"] == right["sample_count"]
            and old["scale"] == required_scale
            and new["scale"] == required_scale
        )
        regression(
            f"{name}_mean", old["mean"] if available else None,
            new["mean"] if available else None,
            gates["regression"]["maximum_judge_drop"][name],
        )
    latency_margin = gates["regression"]["maximum_latency_p95_increase_ratio"]
    if latency_margin is not None:
        old = baseline["metrics"]["latency_ms"]
        new = candidate["metrics"]["latency_ms"]
        available = (
            old["measured_rows"] == left["sample_count"]
            and new["measured_rows"] == right["sample_count"]
            and old["p95"] is not None and old["p95"] > 0
        )
        ratio = new["p95"] / old["p95"] - 1 if available else None
        if ratio is not None:
            ratio = _number(ratio, "latency p95 increase ratio")
        regression_checks.append({
            "metric": "latency_p95_increase_ratio",
            "baseline": old["p95"], "candidate": new["p95"],
            "increase_ratio": ratio, "maximum_increase_ratio": latency_margin,
            "status": "unavailable" if ratio is None else "available",
            "passed": ratio is not None and _at_most(ratio, latency_margin),
        })
    variable_names = ("model_deployment", "prompt_sha256", "knowledge_sha256")
    ignored = {"run_id", "stage", "sample_count", "dataset_sha256", "split", "judge", *variable_names}
    result = {
        "outcome": (
            "PASS_FOR_WORKSHOP"
            if judge_comparable and model_stable and gate["outcome"] == "PASS_FOR_WORKSHOP"
            and all(item["passed"] for item in regression_checks)
            else "HOLD"
        ),
        "scope": "workshop_only",
        "production_ready": False,
        "baseline_run_id": left["run_id"],
        "candidate_run_id": right["run_id"],
        "dataset_sha256": left["dataset_sha256"],
        "sample_count": len(before),
        "paired_row_ids": sorted(before),
        "judge": deepcopy(left["judge"]),
        "judge_comparison": {
            "baseline": deepcopy(left["judge"]),
            "candidate": deepcopy(right["judge"]),
            "comparable": judge_comparable,
            "status": "available" if judge_comparable else "unavailable",
        },
        "model_comparison": {
            "baseline_drift_detected": observed_model_drift(left),
            "candidate_drift_detected": observed_model_drift(right),
            "valid": model_stable,
        },
        "experiment_variables": {
            name: {"baseline": left[name], "candidate": right[name], "changed": left[name] != right[name]}
            for name in variable_names
        },
        "other_metadata_changes": {
            name: {"baseline": left.get(name), "candidate": right.get(name)}
            for name in sorted((left.keys() | right.keys()) - ignored)
            if (name in left) != (name in right) or not _same_json(left.get(name), right.get(name))
        },
        "paired_changes": {
            name: {
                "improved_ids": sorted(key for key in before if not before[key]["checks"][name] and after[key]["checks"][name]),
                "regressed_ids": sorted(key for key in before if before[key]["checks"][name] and not after[key]["checks"][name]),
            }
            for name in CHECKS
        },
        "candidate_gate": gate,
        "regression_checks": regression_checks,
        "limitations": list(LIMITATIONS),
    }
    _json_value(result, "comparison")
    return result


def _cell(value: Any) -> str:
    if value is None:
        return localize("측정 불가 (unavailable)", "Unavailable")
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "\\`").replace("|", "\\|").replace("\r", "").replace("\n", "<br>")


def write_report(summary: dict, path: Path, *, gates: dict | None = None) -> None:
    """Write localized Markdown using the specified gates, not new live data.

    The report states its gate source. A comparison with a different gate file
    remains a separate compare_runs artifact and is not silently substituted.
    Raw model outputs stay in the JSON artifact; only failures are tabulated.
    """
    run = _validate_run(summary)
    gate = evaluate_gates(run, load_gates() if gates is None else gates)
    metadata, metrics = run["metadata"], run["metrics"]
    lines = [
        localize("# Foundry 워크숍 평가 근거 보고서", "# Foundry workshop evaluation evidence"), "",
        f"- {localize('실행', 'Run')}: `{_cell(metadata['run_id'])}`",
        f"- {localize('단계 / split / 표본', 'Stage / split / sample')}: {_cell(metadata['stage'])} / {_cell(metadata['split'])} / {len(run['rows'])}",
        f"- {localize('원본 데이터 split', 'Source split')}: {_cell(metadata.get('source_split', metadata['split']))}",
        f"- {localize('데이터 SHA256', 'Dataset SHA256')}: `{metadata['dataset_sha256']}`",
        f"- {localize('모델 배포', 'Model deployment')}: `{_cell(metadata['model_deployment'])}`",
        f"- {localize('프롬프트 SHA256', 'Prompt SHA256')}: `{metadata['prompt_sha256']}`",
        f"- {localize('지식 SHA256', 'Knowledge SHA256')}: `{metadata['knowledge_sha256']}`",
        f"- {localize('교육용 게이트', 'Workshop gate')}: **{gate['outcome']}** ({'config/gates.json' if gates is None else 'frozen gates snapshot'})",
        localize("- 운영 배포 승인: **아니오**입니다. 비교·회귀 판정은 별도 compare 결과를 확인해야 합니다.", "- Operational deployment approval: **not granted**. Read separate comparison results for paired/regression decisions."),
        "", localize("## 판정률과 실패", "## Pass rates and failures"), "",
        localize("| 지표 | 관측값 |", "| Metric | Observed value |"), "|---|---:|",
    ]
    if gate["sample_contract"]:
        sample = gate["sample_contract"]
        lines[1:1] = [
            "",
            localize(
                f"- 별도 fresh 표본 계약: `{_cell(sample['id'])}@{_cell(sample['version'])}`; 최소 {sample['minimum_rows']}행.",
                f"- Separate fresh-sample contract: `{_cell(sample['id'])}@{_cell(sample['version'])}`; minimum {sample['minimum_rows']} rows.",
            ),
            localize("- 원본 test20의 대체가 아닙니다. 표본 계약은 생성·평가 전에 동결하며 모든 점수·오류·critical 기준은 유지합니다.", "- This does not replace original test20. Freeze the sample contract before generation/evaluation; retain every score, error, and critical-case criterion."),
        ]
    for name in (*RATE_METRICS, "citation_coverage_mean", "error_count", "api_error_count", "judge_error_count", "critical_rule_failure_count"):
        lines.append(f"| {name} | {_cell(metrics[name])} |")
    interval = metrics["route_accuracy_wilson_95"]
    lines.extend([
        "",
        localize(
            f"라우팅 정확도 Wilson 95% 구간: [{interval['lower']:.4f}, {interval['upper']:.4f}] "
            "(독립 표본 가정; 작은 교육용 데이터셋의 불확실성을 숨기지 않습니다).",
            f"Routing accuracy Wilson 95% interval: [{interval['lower']:.4f}, {interval['upper']:.4f}] "
            "(assumes independent samples; uncertainty in this small teaching dataset remains visible).",
        ),
        "", localize("## LLM judge 가용성", "## LLM Judge availability"), "",
        f"{localize('선언된 judge', 'Declared Judge')}: {_cell(json.dumps(metadata['judge'], ensure_ascii=False, sort_keys=True, allow_nan=False))}",
        "", localize("| 지표 | 평균 | 점수 있는 행 / 전체 | 상태 | 척도 |", "| Metric | Mean | Scored rows / total | Status | Scale |"), "|---|---:|---:|---|---|",
    ])
    for name, measurement in metrics["judge"].items():
        lines.append(
            f"| {name} | {_cell(measurement['mean'])} | {measurement['scored_count']} / {len(run['rows'])} "
            f"| {measurement['status']} | {_cell(measurement['scale'])} |"
        )
    lines.extend([
        "", localize(
            "누락·오류 judge 점수는 평균 분모에서 제외하고 coverage로 노출합니다. "
            "전체 행의 1..5 점수가 없으면 기본 의미 평가 게이트를 통과할 수 없습니다.",
            "Missing/failed Judge scores are excluded from means but exposed through coverage. "
            "Without 1..5 scores for all required rows, the default semantic gates cannot pass.",
        ),
        "", localize("## 중요(critical) 사례: 교육용 행별 하한", "## Critical cases: workshop per-row floors"), "",
        localize(
            "이 기준은 워크숍 교육용 정책이며 Microsoft 공식 평가 기준이 아닙니다. "
            "각 critical 행의 점수를 검사하므로 다른 행의 높은 평균으로 중요 실패를 상쇄할 수 없습니다.",
            "These are educational workshop criteria, not Microsoft's official evaluation standard. "
            "Every critical row is checked; high averages elsewhere cannot offset its failure.",
        ),
        localize(
            f"- critical 사례: {gate['critical_sample_count']}행 / 최소 요구 {gate['minimum_critical_rows']}행",
            f"- Critical cases: {gate['critical_sample_count']} / required minimum {gate['minimum_critical_rows']}",
        ),
        localize("- critical 점수 누락·judge 오류·응답 오류는 보류입니다. 전체 평균 게이트를 꺼도 행별 하한은 유지됩니다.", "- Missing critical scores, Judge errors, or response errors mean HOLD. Per-row floors remain even if aggregate-mean gates are disabled."),
        "", localize("| 지표 | 행별 하한 | 관측 최솟값 | 점수 있는 행 / critical | 하한 미달 ID | 누락·오류 ID | 척도 일치 | 결과 |", "| Metric | Per-row floor | Observed minimum | Scored / critical | Below-floor IDs | Missing/error IDs | Scale matches | Result |"),
        "|---|---:|---:|---:|---|---|---|---|",
    ])
    for name, measurement in gate["critical_judge"].items():
        lines.append(
            f"| {name} | {measurement['minimum_required']} | {_cell(measurement['minimum_observed'])} "
            f"| {measurement['scored_count']} / {gate['critical_sample_count']} "
            f"| {_cell(', '.join(measurement['below_floor_ids']) or localize('없음', 'none'))} "
            f"| {_cell(', '.join(measurement['unavailable_ids']) or localize('없음', 'none'))} "
            f"| {localize('예', 'yes') if measurement['scale_compatible'] else localize('아니오', 'no')} "
            f"| {localize('통과', 'PASS') if measurement['passed'] else localize('보류', 'HOLD')} |"
        )
    lines.extend([
        "", localize("## 지연과 토큰 (관측만)", "## Latency and tokens (observed only)"), "",
        f"- {localize('지연 측정 행', 'Rows with measured latency')}: {metrics['latency_ms']['measured_rows']} / {len(run['rows'])}",
        f"- p50 / p95 (ms): {_cell(metrics['latency_ms']['p50'])} / {_cell(metrics['latency_ms']['p95'])}",
        f"- {localize('분위수 방법', 'Quantile method')}: {metrics['latency_ms']['method']}",
    ])
    for name, measurement in metrics["tokens"].items():
        lines.append(localize(
            f"- {name}: {_cell(measurement['sum'])}; 측정 {measurement['measured_rows']}행, 누락 {measurement['missing_rows']}행",
            f"- {name}: {_cell(measurement['sum'])}; measured rows {measurement['measured_rows']}, missing rows {measurement['missing_rows']}",
        ))
    lines.extend(["", localize("## 태그별 하위집합", "## Subsets by tag"), "", localize("| 태그 | 행 수 | 규칙 실패 행 | 라우팅 정확도 |", "| Tag | Rows | Rule-failure rows | Routing accuracy |"), "|---|---:|---:|---:|"])
    for tag, subset in metrics["by_tag"].items():
        lines.append(f"| {_cell(tag)} | {subset['sample_count']} | {subset['rule_failure_count']} | {_cell(subset['route_accuracy'])} |")
    lines.extend(["", localize("## 게이트 검사", "## Gate checks"), "", localize("| 검사 | 결과 | 관측값 | 기준 |", "| Check | Result | Observed | Required |"), "|---|---|---|---|"])
    for check in gate["checks"]:
        lines.append(f"| {_cell(check['name'])} | {localize('통과', 'PASS') if check['passed'] else localize('보류', 'HOLD')} | {_cell(check['actual'])} | {_cell(check['required'])} |")
    lines.extend(["", localize("## 행별 근거", "## Per-row evidence"), "", localize("| ID | 기대 경로 | 실제 경로 | 실패 규칙 | 오류 |", "| ID | Expected route | Actual route | Failed rules | Error |"), "|---|---|---|---|---|"])
    for row in run["rows"]:
        response = row["response"] if isinstance(row["response"], dict) else {}
        error = row["api_error"] or row["parse_error"] or "; ".join(row["schema_errors"])
        lines.append(
            f"| {_cell(row['id'])} | {_cell(row['expected']['route'])} | {_cell(response.get('route'))} "
            f"| {_cell(', '.join(row['rule_failures']) or localize('없음', 'none'))} | {_cell(error or localize('없음', 'none'))} |"
        )
    limitations = [
        "This offline engine evaluates input artifacts; it does not attest that a model or API actually ran.",
        "Citation-ID matching and coverage do not prove that an answer is grounded in its sources.",
        "Forbidden claims use case-sensitive literal substring checks, not semantic safety evaluation.",
        "PASS_FOR_WORKSHOP is educational, not production-deployment approval or a production-ready claim.",
        "Critical sample counts and per-row Judge floors are workshop policy, not Microsoft's official standard.",
        "The original 20-case held-out test is intentionally small; larger samples, planned repetitions, and independent review are needed.",
        "Routing Wilson 95% intervals assume independent Bernoulli samples, excluding group correlation, multiple comparisons, and dataset bias.",
        "Latency p50/p95 uses observed type-7 interpolation. Do not interpret a small sample's p95 as a production SLO.",
        "Only observed API token counts are summed. Missing values are not zero; prices and USD costs are not invented.",
    ] if selected_language() == "en" else LIMITATIONS
    lines.extend(["", localize("## 해석의 한계", "## Interpretation limits"), ""])
    lines.extend(f"- {limitation}" for limitation in limitations)
    lines.extend(["", localize("원문 출력은 JSON run artifact의 rows[].raw_output에 오류 발생 시에도 그대로 보존됩니다.", "Original output remains verbatim in rows[].raw_output in the JSON run artifact, including on errors."), ""])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
