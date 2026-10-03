"""Authored teaching examples, deliberately independent of every cloud SDK."""

from datetime import datetime, timezone
import json
from pathlib import Path

from lab.config import LabError
from lab.content import language_metadata, selected_language, text


EXAMPLES = (
    {
        "id": "demo-refund-boundary",
        "query": "9월 10일 최초 월 구독을 샀고 오늘은 9월 15일입니다. 환불해 주세요.",
        "plausible_wrong_answer": "14일 안이므로 환불이 승인되었고 내일 입금됩니다.",
        "find_the_problem": "기간만으로 승인·실행 완료까지 말할 수 있을까요?",
        "policy": "ATLAS-REF-001: 최초 월 구매·14일 이내·프로덕션 작업 없음·유료 크레딧 사용 없음이 모두 필요하다. 자격은 승인이나 송금 완료가 아니다.",
        "correction": "결제 시각·시간대, 프로덕션 작업과 유료 크레딧 사용 여부를 확인해 주세요. 조건을 충족하면 결제 소유자가 콘솔에서 심사를 신청할 수 있습니다. 이 대화에서 환불을 실행하지는 않았습니다.",
        "policy_task_correctness": {"wrong": 0, "corrected": 1, "scale": "authored binary teaching labels"},
    },
    {
        "id": "demo-stale-retrieval",
        "query": "2026년 9월 최초 월 구매의 환불 기한은 며칠인가요?",
        "retrieved_excerpt": "오래된 예시 검색 조각: 모든 최초 월 구매의 기한은 7일입니다.",
        "plausible_wrong_answer": "검색 문서에 따라 환불 기한은 7일입니다.",
        "find_the_problem": "검색 문서와 일치하는 답변이면 업무적으로도 맞을까요?",
        "policy": "ATLAS-REF-001: 2026-09-01 이후 최초 월 구매는 14일이다. 그 이전 구매는 7일이다.",
        "correction": "이 작성된 예제의 답은 검색 조각에는 충실하지만 최신 거래 정책에는 틀립니다. 검색의 적용 시점과 권위 있는 정책을 별도로 확인해야 합니다.",
        "retrieval_groundedness": {"wrong": 1, "scale": "authored binary teaching label; NOT a live search score"},
        "policy_task_correctness": {"wrong": 0, "scale": "authored binary teaching label"},
    },
)

ENGLISH_EXAMPLE_TEXT = (
    {
        "query": "I bought my first monthly subscription on September 10, and today is September 15. Please refund it.",
        "plausible_wrong_answer": "You are within 14 days, so your refund has been approved and the money will arrive tomorrow.",
        "find_the_problem": "Does meeting a deadline establish approval or completed execution?",
        "policy": "ATLAS-REF-001: First monthly purchase, within 14 days, no production jobs, and no paid-credit use are all required. Eligibility is not approval or completed payment.",
        "correction": "Please confirm the payment time and time zone, production jobs, and paid-credit use. If eligible, the billing owner can request a review in the console. No refund has been executed in this conversation.",
    },
    {
        "query": "What is the refund deadline for a first monthly purchase in September 2026?",
        "retrieved_excerpt": "Outdated example search excerpt: the deadline for every first monthly purchase is seven days.",
        "plausible_wrong_answer": "According to the retrieved document, the refund deadline is seven days.",
        "find_the_problem": "If an answer matches retrieval, is it necessarily correct for the business?",
        "policy": "ATLAS-REF-001: First monthly purchases from 2026-09-01 have a 14-day deadline. Earlier purchases have a seven-day deadline.",
        "correction": "This authored answer matches its retrieved excerpt but contradicts the current transaction policy. Check the effective date and authoritative policy separately.",
    },
)


def run_demo(out: Path | None = None) -> dict:
    examples = [
        {**original, **translated}
        for original, translated in zip(EXAMPLES, ENGLISH_EXAMPLE_TEXT, strict=True)
    ] if selected_language() == "en" else list(EXAMPLES)
    result = {
        **language_metadata(),
        "kind": "AUTHORED_DEMO_NOT_LIVE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "author_type": "ai",
        "notice": text(
            "AI가 작성한 합성 교육 예제입니다. 실제 Azure 응답·검색·Judge 평가·사람 검토·품질 통과 증거가 아닙니다.",
            "AI-authored synthetic teaching examples, not actual Azure responses, retrieval, Judge results, human review, or evidence of a quality pass.",
        ),
        "network_calls": 0,
        "credential_access": False,
        "azure_cost_incurred_by_this_demo": False,
        "examples": examples,
        "conversation": [
            {"role": "user", "source": "authored_script", "text": text("환불을 받고 싶어요.", "I would like a refund.")},
            {"role": "assistant", "source": "authored_script", "route": "clarify", "text": text(
                "최초 월 구매인가요? 결제 시각과 유료 작업·크레딧 사용 여부를 알려 주세요.",
                "Is this your first monthly purchase? Please provide the payment time and whether paid jobs ran or paid credits were used.",
            )},
            {"role": "user", "source": "scripted_followup_not_human_approval", "text": text(
                "최초 월 구매이고 2026-09-10 09:00 KST에 결제했습니다. 오늘은 9월 15일이고 작업과 유료 크레딧은 사용하지 않았습니다.",
                "This is my first monthly purchase, paid at 2026-09-10 09:00 KST. Today is September 15; no jobs ran and no paid credits were used.",
            )},
            {"role": "assistant", "source": "authored_script", "route": "answer", "text": text(
                "제공한 조건상 환불 심사 신청 자격이 있습니다. 결제 소유자가 콘솔에서 신청하세요. 승인이나 입금 완료는 아닙니다.",
                "The stated conditions make you eligible to request a refund review. The billing owner should apply in the console. This is not approval or completed payment.",
            )},
        ],
        "states": {
            "execution": "DEMO_COMPLETED",
            "quality": "NOT_EVALUATED_LIVE",
            "human_review": "PENDING",
            "operational_approval": "NOT_APPROVED",
        },
        "next": text(
            "가이드 02. 환경 연결: guide/handbook.md#prepare. 기존 실습 환경과 현재 승인을 확인하며 재배포하지 않습니다. DEMO 결과를 LIVE 분모에 합치지 않습니다.",
            "Step 02: connect your environment at guide/en/handbook.md#prepare. Verify the dedicated environment and current approval without redeployment. Keep DEMO results outside LIVE denominators.",
        ),
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            with out.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write("\n")
        except FileExistsError as exc:
            raise LabError("DEMO 출력이 이미 있습니다. 기존 예제를 덮어쓰지 않고 새 경로를 지정해야 합니다.") from exc
    return result
