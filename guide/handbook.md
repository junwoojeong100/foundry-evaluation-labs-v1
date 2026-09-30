# 좋은 에이전트는 평가에서 시작된다 · v1

<p class="eyebrow">CONTOSO ATLAS CLOUD · 하나의 실습 경로</p>

**이 페이지의 6단계만 순서대로 진행하세요.** 같은 Contoso 에이전트에 지식을 연결하고 지시를 개선한 뒤, 근거로 채택 또는 보류를 판단합니다.

**기존 환경·데이터·모델·평가 기준은 그대로입니다.** 안내 변경 때문에 재배포하거나 완료된 실험을 다시 실행하지 않습니다.

<ol class="learning-path" role="list" aria-label="실습 순서">
<li><a href="#start"><strong>01</strong> 예시 이해</a></li>
<li><a href="#prepare"><strong>02</strong> 환경 연결</a></li>
<li><a href="#baseline"><strong>03</strong> 기준선 평가</a></li>
<li><a href="#iq"><strong>04</strong> 지식 연결</a></li>
<li><a href="#optimize"><strong>05</strong> 지시 개선</a></li>
<li><a href="#decision"><strong>06</strong> 최종 판정·종료</a></li>
</ol>

**예상 시간: 약 3–4시간, 결과 공유 포함.** 기존 환경이 준비되어 있고 교정을 통과해 끝까지 진행하는 경우의 계획값입니다. 서비스 대기·오류 대응에 따라 달라지며, 환경 신규 구축과 SFT는 포함하지 않습니다.

**읽는 순서: 실행 명령 → 출력 예시 → 내 결과 공유·판단 → 다음 단계.** 명령은 한 줄씩 실행합니다. 평가는 **업무 Judge**, 지시 개선은 **Agent Optimizer** 하나로 진행합니다.

**평가는 점수를 만드는 일이 아니라 다음 행동을 결정할 근거를 얻는 일입니다.** 03–06의 결과 공유 지점마다 2–3분씩, **실제 결과 → 대표 사례 → 다음 결정**을 설명합니다. 점수에는 표본 수·척도·누락을 함께 붙입니다. 기존 보고서를 읽는 활동이므로 유료 평가 횟수는 늘지 않습니다. 모델 smoke는 연결 확인이지 품질 평가가 아닙니다.

공유 범위는 **허용된 합성 사례와 집계 결과**입니다. 화면에서도 계정·구독·환경·승인 정보를 가리고, 비공개 원본을 그대로 전달하지 않습니다. 자동 외부 전송·업로드는 없습니다.

<p class="output-notice" id="output-examples-note"><strong>출력 예시는 설명용으로 작성한 발췌입니다.</strong> 일부 필드만 보여 주며 점수·ID·답변이 내 실행과 같아야 한다는 뜻이 아닙니다. 예시를 입력 파일이나 실제 성공 증거로 저장하지 마세요.</p>

유료 실행에는 현재 비용·데이터·작업 승인이 필요하며 `--confirm`만으로 승인되지 않습니다. 오류·교정 불합격이면 멈추고 **HOLD와 미실행 항목**을 남깁니다. 완료한 단계는 기존 결과만 읽고, 중단된 실행은 [같은 ID로 재개](facilitator.md#resume)합니다.

## 01. 예시 이해 {#start}

**할 일:** 설치·로그인 전에 아래 답변에서 잘못된 약속을 찾습니다.

> 고객: “9월 10일 최초 월 구독을 샀고 오늘은 9월 15일입니다. 환불해 주세요.”
>
> 작성된 오답: “14일 안이므로 환불이 승인되었고 내일 입금됩니다.”

[합성 정책](../data/knowledge/documents.json)의 `ATLAS-REF-001`과 `ATLAS-ESC-001`을 확인합니다. 최초 월 구매의 기한뿐 아니라 유료 프로덕션 작업·크레딧 사용 여부도 필요합니다. **신청 자격은 승인이나 송금 완료가 아니며, 이 도우미에는 환불 실행 도구가 없습니다.**

<a id="demo"></a>

이제 패키지 전체가 있는 폴더에서 실행합니다. Python 3.11 이상이 필요하며 3.12를 권장합니다. macOS/Linux의 bash·zsh 또는 Windows WSL2 Ubuntu 터미널을 사용합니다.

**실행 명령 · 무료·오프라인:**

```bash
python3 -S -m lab demo
```

<p class="output-label" id="example-demo">출력 예시 · DEMO 터미널 출력 일부</p>

```json
{
  "kind": "AUTHORED_DEMO_NOT_LIVE",
  "author_type": "ai",
  "network_calls": 0,
  "states": {
    "execution": "DEMO_COMPLETED",
    "quality": "NOT_EVALUATED_LIVE",
    "human_review": "PENDING",
    "operational_approval": "NOT_APPROVED"
  }
}
```

**읽는 법:** `DEMO_COMPLETED`는 **작성 예시 읽기 완료**입니다. 실제 모델 평가나 사람 승인은 아닙니다. 출력의 `conversation`도 고객 질문 → `clarify` → 명시적인 scripted-user 후속 발언 → 최종 안내 순서로 읽습니다. 추가 정보는 모델의 추측이 아닙니다.

**완료 확인:** 잘못된 약속과 필요한 확인 질문을 하나씩 설명할 수 있습니다. Azure 계정·`.env`·CLI·SDK·네트워크는 아직 필요하지 않습니다. Python이 없으면 먼저 준비하며 LIVE 호출로 우회하지 않습니다.

<p class="step-next no-print"><a href="#prepare" data-next-step>다음: 02. 환경 연결 →</a></p>

## 02. 환경 연결 {#prepare}

**할 일:** 이미 준비된 **실습 전용 North Central US 환경**에 연결합니다. 기존 환경은 원래 manifest로 확인하며 새 RG를 만들지 않습니다.

운영자는 참가자의 실제 로그인·권한·배포·현재 비용 승인을 확인하고 아래 값을 전달합니다. 아직 받지 못했다면 대기합니다. 환경이 **없는 경우에만** 운영자가 [사전 준비](admin-setup.md#bootstrap)를 한 번 수행합니다.

**실행 명령 · 로컬 설치와 데이터 검사:** 패키지 루트에서 실행합니다. `.venv`가 있으면 생성은 반복하지 않고 활성화부터 합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m lab validate
```

<p class="output-label" id="example-validation">출력 예시 · 마지막 validate 명령</p>

```text
일치 검사 완료: train=56, validation=12, dev=12, test=20; 정책 8개; 생성물 8개
```

**읽는 법:** 원본 100건과 정책·분할이 유지된다는 뜻입니다. 패키지 설치에는 인터넷이 필요하지만 `validate`는 모델을 호출하지 않습니다.

<a id="environment"></a>

**설정값은 여기서 한 번만 입력합니다.** 나머지 명령은 같은 터미널에서 그대로 이어갑니다.

| 바꿀 값 | 운영자가 전달할 내용 |
|---|---|
| `LAB_ENV_DIR` | 기존 실습의 비공개 환경 폴더 |
| `LAB_COST_APPROVAL_FILE` | 현재 유효한 승인 파일 경로 |
| `APPLICATIONINSIGHTS_RESOURCE_ID` | 같은 실습 RG의 관측 리소스 ID |

**실행 명령 · 환경 확인:** 아래 폴더명·승인 파일명·관측 ID는 실제 값으로 바꿉니다.

```bash
export LAB_ENV_DIR="$PWD/.lab/lab-training"
export LAB_ENV_FILE="$LAB_ENV_DIR/.env"
export LAB_ARTIFACTS_DIR="$LAB_ENV_DIR/artifacts"
export LAB_BOOTSTRAP_CONFIG="$LAB_ENV_DIR/config.json"
export LAB_COST_APPROVAL_FILE="$LAB_ENV_DIR/approval.json"
export APPLICATIONINSIGHTS_RESOURCE_ID="YOUR_NEW_APPLICATIONINSIGHTS_RESOURCE_ID"
python3 -S -m lab.bootstrap status --config "$LAB_BOOTSTRAP_CONFIG" --approval "$LAB_COST_APPROVAL_FILE"
python -m lab --config "$LAB_ENV_FILE" preflight
```

<p class="output-label" id="example-preflight">출력 예시 · 마지막 preflight 명령</p>

```json
{
  "kind": "read-only-management-preflight",
  "status": "PASS"
}
```

**읽는 법:** `PASS`는 관리 조회의 준비 확인이며 실제 모델 호출 성공은 아닙니다. `.env`는 데이터 파일이므로 `source`하지 않습니다. `LAB_ARTIFACTS_DIR`는 Python 실행 전에 설정하고 `.env`의 `BOOTSTRAP_CONFIG`도 같은 계획을 가리켜야 합니다.

**완료 확인:** 실제 ARM 배포·소유 manifest·`.env`가 일치하고 preflight가 `PASS`입니다. 빈 RG의 `Succeeded`나 계획 파일만으로는 부족합니다. 무관한 기존/공유 자원·다른 리전으로 우회하지 않습니다.

<a id="first-infrastructure-failure"></a>

비용·호출·후보·대기 한도는 **자신의 현재 승인**을 따릅니다. 기존 실행의 금액 무상한 승인은 다른 참가자에게 적용되지 않습니다. GlobalStandard/Global/Developer 처리 위치와 리소스 리전도 다릅니다. 오류는 운영자가 같은 계획에서 해결하며, 새 터미널에서는 활성화와 위 설정만 복원합니다.

<p class="step-next no-print"><a href="#baseline" data-next-step>다음: 03. 기준선 평가 →</a></p>

## 03. 기준선 평가 {#baseline}

<a id="understand"></a>
<a id="data"></a>

**할 일:** 지식 도구가 없는 에이전트의 세 응답을 먼저 읽고, 업무 Judge가 믿을 만한지 교정합니다. 기대 답·route·필수 인용은 평가자용이며 생성 에이전트에 주지 않습니다. 원본 test 20건은 개발 중 열지 않습니다.

**실행 명령 · 고정 평가 기준 읽기:**

```bash
python -m json.tool config/gates.json
```

**어떤 기준으로 결과를 읽을까요?** 아래는 현재 교육용 최종 게이트의 요약이며 Microsoft 공식 합격선이나 운영 인증이 아닙니다.

| 평가 항목 | 확인할 것 | 최종 기준 |
|---|---|---|
| 출력 형식 | 네 필드의 올바른 JSON | 100% |
| 행동 분류 | `answer` / `clarify` / `escalate` / `refuse`가 기대 행동과 일치 | ≥85% |
| 인용·사람 판단 표시 | 인용 ID와 `needs_human`이 올바름 | 인용 ≥90%, 사람 판단 표시 100% |
| 업무 정확성 | 권위 있는 정책·시점·조건·권한에 맞는 답 | 1–5점 평균 ≥4 |
| 검색 근거성 | 생성 시 실제 받은 검색 문맥이 답을 뒷받침 | 1–5점 평균 ≥4 |
| 질문 적합성 | 고객 질문에 유용하고 직접적인 답 | 1–5점 평균 ≥4 |

오류·필수 점수 누락·중요 실패는 허용하지 않습니다. 중요 사례는 평균과 별개로 업무 정확성·검색 근거성·질문 적합성이 **각각 4점 이상**이어야 합니다. 허위 완료 등 금지 주장 검사도 100% 통과가 필요합니다. 근거성이 미측정이면 정책으로 대신 채우거나 만점으로 만들지 않습니다. smoke/dev는 진단용이며 최종 채택 판정과 구별합니다. 결과를 보고 합격선을 낮추지 않습니다.

<p class="explanation-heading" id="score-rubric">평가 전 · 3점과 4점은 무엇이 다른가?</p>

다음은 실제 [업무 Judge 정의](../config/evaluators/policy-correctness.v1.json)와 [검색 Judge 정의](../config/evaluators/retrieval-groundedness.v1.json)의 점수 기준을 한국어로 요약한 것입니다. **세 지표는 서로 다른 질문**에 답합니다.

| 점수 | 업무 정확성 | 검색 근거성 | 질문 적합성 |
|---|---|---|---|
| 5 | 정책·조건·권한이 정확하고 완전함 | 모든 사실 주장이 실제 검색 문맥으로 뒷받침됨 | 질문에 직접 답함 |
| 4 | 정확하지만 경미한 누락이 있음 | 중요한 주장은 뒷받침되며 경미한 누락만 있음 | 유용하고 질문의 주제에 맞음 |
| 3 | 중요한 조건 누락·모호함이 있음 | 일부 주장만 뒷받침됨 | 질문에 부분적으로만 답함 |
| 2 | 정책 또는 행동 분류가 틀림 | 핵심 주장에 근거가 부족함 | 질문의 의도를 대부분 놓침 |
| 1 | 무단 공개·허위 실행/승인 등 위험한 답 | 검색 문맥과 모순되거나 실행을 꾸며냄 | 질문과 무관함 |

잘못된 `route`는 업무 정확성 **최대 2점**입니다. 초기 답에서 위험한 약속을 했다면 마지막 답만 올바르다고 지워지지 않습니다. 검색이 없으면 근거성은 **미측정**이며, 그 자체를 1점이나 5점으로 바꾸지 않습니다. 1–5점은 정확도 퍼센트가 아닙니다.

<a id="model-smoke"></a>

**실행 명령 · 모델 연결 확인, 유료 1회:**

```bash
python -m lab --config "$LAB_ENV_FILE" smoke --run-id model-smoke --confirm
```

<p class="output-label" id="example-model-smoke">출력 예시 · 모델 smoke 터미널 출력 일부</p>

```json
{
  "kind": "LIVE_MODEL_SMOKE_NOT_QUALITY_EVALUATION",
  "status": "completed",
  "response_id": "resp_EXAMPLE_NOT_LIVE",
  "cost": {"status": "NOT_OBSERVED"}
}
```

**읽는 법:** 내 출력의 실제 response ID와 비어 있지 않은 응답을 확인한 뒤 진행합니다. `completed`는 **연결 확인**이며 품질 통과가 아닙니다. 비용 미관측도 0원이 아닙니다. 원본은 `runs/model-smoke/model-smoke.json`에 남습니다.

**실행 명령 · 기준선 Agent 생성·3건 실행, 유료:**

```bash
python -m lab --config "$LAB_ENV_FILE" agent --stage baseline --confirm
python -m lab --config "$LAB_ENV_FILE" run --stage baseline --split dev --limit 3 --run-id baseline-smoke --confirm
python -m json.tool --json-lines "$LAB_ARTIFACTS_DIR/runs/baseline-smoke/outputs.jsonl"
```

<p class="output-label" id="example-agent-answer">출력 예시 · outputs.jsonl의 raw_output 안 답변을 JSON으로 펼친 모습</p>

```json
{
  "answer": "결제 시각·시간대와 유료 작업·크레딧 사용 여부를 확인해 주세요. 아직 환불을 승인하거나 처리하지 않았습니다.",
  "citations": [],
  "route": "clarify",
  "needs_human": false
}
```

**읽는 법:** `clarify`는 필요한 정보를 묻는 행동이지 실패가 아닙니다. 안내는 `answer`, 사람 판단 요청은 `escalate`, 금지 요청 거절은 `refuse`이며 **`escalate`일 때만 `needs_human: true`**입니다. 요청도 실제 전송·티켓 생성 완료를 뜻하지 않습니다.

**Judge 점수를 보기 전에** 내 세 응답 중 하나를 정책과 대조해 맞음/수정 필요와 이유를 정합니다. 예시와 같은 답을 만들려고 출력을 바꾸지 않습니다.

<a id="calibration"></a>

**실행 명령 · 업무 Judge 교정, 유료:**

16개 합성 참조를 채점합니다. 정상 계획은 정책 Judge 16회 + 검색 문맥이 있는 retrieval Judge 15회, **31요청**입니다. 실제 청구량은 아니므로 실행 전 남은 승인 범위를 확인합니다.

```bash
python -m lab --config "$LAB_ENV_FILE" judge calibrate --calibration-id cal-01 --confirm
```

<p class="output-label" id="example-calibration">출력 예시 · 교정 실행은 완료됐지만 HOLD인 경우</p>

```json
{
  "execution_status": "completed",
  "sample_count": 16,
  "all_dimensions_agreement_rate": 0.9375,
  "critical_false_accept_count": 0,
  "quality_status": "HOLD"
}
```

**읽는 법:** 예시는 16개 중 15개만 모든 항목에 일치합니다. critical false accept가 0이어도 **완전 일치가 아니므로 HOLD**입니다. 이 경우 원본 `calibration/cal-01/report.json`을 보존하고 유료 진행을 멈춘 뒤 [종료 기록](#cleanup)에 이유와 미실행 항목을 남깁니다.

<p class="share-checkpoint" id="share-calibration">결과 공유 · 이 채점자를 믿고 다음 평가를 해도 될까?</p>

- **실제 결과:** 방금 나온 교정 보고서의 표본 수, 전체 항목 일치율, critical false accept 수, `quality_status`를 공유합니다. 위 예시 숫자가 아니라 **내 실행값**을 사용합니다.
- **대표 사례:** `rows`에서 참조 판정과 Judge가 불일치한 한 건의 답변·점수·이유를 읽습니다. 불일치가 없다면 일치한 한 건을 근거로 설명합니다.
- **다음 결정:** “채점자도 틀릴 수 있으므로 ___ 때문에 계속/보류한다”를 말합니다. **채점자의 신뢰성**을 확인하는 평가이지 에이전트 개선율을 측정한 것이 아닙니다.

**교정 통과 후에만 진행합니다.** `execution_status: completed`, `quality_status: PASS`, `all_dimensions_agreement_rate: 1.0`, `critical_false_accept_count: 0`을 **모두** 확인합니다. `completed`만 보고 진행하거나 평가기 변경·재채점으로 우회하지 않습니다.

<p class="explanation-heading" id="hold-actions">평가 후 · HOLD이면 계속할까, 멈출까?</p>

**HOLD라는 단어보다 실패한 검사 이름과 원인을 먼저 봅니다.** 아래는 게이트를 바꾸는 규칙이 아니라, 결과를 읽고 다음 행동을 정하는 순서입니다.

| 보이는 결과 | 의미 | 다음 행동 |
|---|---|---|
| 교정 `quality_status: HOLD` | 채점자를 신뢰할 근거가 부족함 | 유료 진행을 멈추고 참조 판정·Judge 이유를 검토. 이후 미실행 기록 |
| dev/smoke의 `heldout_test_only`, `minimum_test_rows`, `fresh_holdout_bound` | 개발 진단이지 최종 시험이 아님 | **다른 실패가 없는지**, 교정 통과·승인 범위를 확인한 뒤 다음 개선 단계로. PASS로 바꾸지 않음 |
| 진단 표본에 중요 사례가 없음 | 중요 사례에 대한 증거가 아직 없음 | 안전성을 통과했다고 주장하지 말고 정해진 후속 데이터 범위에서 확인 |
| 검색 없는 기준선의 `groundedness_*` 미측정 | 생성 시 검색 근거가 없었음 | 업무 정확성·적합성과 구분. IQ 연결 후 실제 문맥으로 확인 |
| API/JSON 오류, 예상하지 못한 점수 누락, 모델·자료 불일치 | 실행·측정·계약 문제 | 먼저 중단하고 원본 오류/ID 확인. 지침을 고치거나 새 ID로 재호출해 숨기지 않음 |
| 기준선/IQ의 비중요 품질 미달 | 구체적으로 개선할 답변이 발견됨 | 사례와 이유를 남기고 지식·지시 중 바꿀 대상을 정함. 교정/오류/중요 실패도 따로 확인 |
| 중요 실패·허용폭을 넘는 회귀 | 평균으로 상쇄할 수 없는 위험 | 후보 사용을 보류하고 문제 문장·권한·조건을 검토 |
| 최종 fresh 시험의 HOLD | 고정 기준으로 채택하지 못함 | 결과를 보존하고 다음 실험 계획을 남김. 같은 최종 질문을 튜닝하거나 다시 뽑지 않음 |

**실행 명령 · 통과한 Judge로 저장된 기준선 채점, 유료:**

```bash
python -m lab --config "$LAB_ENV_FILE" judge score --run-id baseline-smoke --interval-seconds 65 --confirm
python -m lab score --run-id baseline-smoke
python -m lab explain --run-id baseline-smoke
```

**마지막 `explain`은 읽기 전용입니다.** 기준·실제 값·전체 사례 점수표와, 중요·하락·문제 사례 우선 **최대 3건의 상세 해설**을 출력합니다. 질문·답변·정책/검색 문맥·점수·Judge 이유·개선 제안이 연결됩니다. 실제 이유는 `judge-scores.json`의 **`reasons.policy` / `reasons.retrieval`**에서 가져오며 새로 생성하지 않습니다. 긴 문맥은 표시만 발췌하고 원문은 보존합니다.

`score`는 저장된 응답의 로컬 점수를 만들고, `explain`은 그 결과를 읽습니다. `explain`을 다시 실행해도 모델을 호출하거나 기존 평가 파일을 바꾸지 않습니다. **종료 코드 0은 설명 출력 성공이지 품질 통과가 아닙니다.**

<p class="share-checkpoint" id="share-baseline">결과 공유 · 무엇을 고쳐야 하는지 기준선에서 찾기</p>

- **실제 결과:** `baseline-smoke`의 **3건**이라는 범위와 형식 통과율·route 정확도·업무 정확성, **점수 있는 행 / 전체**, 오류를 함께 읽습니다. 검색이 없어서 측정하지 못한 근거성은 0점이나 만점이 아닙니다.
- **대표 사례:** `explain`의 같은 사례 ID에서 **실제 응답 → 세 점수 → 두 Judge 이유 → 개선 제안**을 읽습니다. “내 최초 판단과 Judge가 같은가, 어느 문장이 정책과 맞거나 다른가?”를 공유합니다.
- **다음 결정:** IQ로 보완할 지식 문제를 하나 정합니다. 모두 적절했다면 그대로 보고합니다. **고치기 전 상태를 남겨야 이후 변화도 설명할 수 있습니다.**

<p class="explanation-heading" id="worked-evaluation">한 사례로 연결하기 · 답변 → 점수 → 이유 → 개선</p>

**아래 답변·점수·해석은 AI가 작성한 교육 예시이며 실제 실행 결과가 아닙니다.** 실제 Judge가 반드시 이 점수를 준다는 뜻이 아니며, 내 결과는 위 `explain`으로 읽습니다.

> 질문: “9월 10일 최초 월 구독을 샀고 오늘은 9월 15일입니다. 환불해 주세요.”

<table class="worked-comparison">
<thead><tr><th>관찰 항목</th><th>개선 전 작성 예시</th><th>개선 후 작성 예시</th></tr></thead>
<tbody>
<tr><td>답변</td><td>“14일 안이므로 환불이 승인되었고 내일 입금됩니다.”</td><td>“결제 시각·시간대와 유료 작업·크레딧 사용 여부를 확인해 주세요. 아직 환불을 승인하거나 처리하지 않았습니다.”</td></tr>
<tr><td>행동</td><td><code>answer</code>로 승인 단정</td><td><code>clarify</code>로 빠진 조건 확인</td></tr>
<tr><td>업무 정확성의 작성 점수</td><td><strong>1</strong> — 없는 승인·입금 결과를 만듦</td><td><strong>5</strong> — 필요한 조건을 묻고 실행 권한을 구분</td></tr>
<tr><td>검색 근거성</td><td><strong>미측정</strong> — 실제 검색 실행 없음</td><td><strong>미측정</strong> — 실제 검색 실행 없음</td></tr>
<tr><td>읽을 이유</td><td>신청 자격을 승인/송금 완료로 바꾸었음</td><td>조건 확인과 실제 실행을 구분했음</td></tr>
<tr><td>다음 판단</td><td>허위 완료이므로 보류</td><td>이 사례의 개선 방향은 타당하지만 전체 품질·운영 승인은 아직 미확정</td></tr>
</tbody>
</table>

**지시에서 확인할 개선 규칙:** 빠진 조건은 최소 질문으로 확인하기, 신청 자격과 승인을 구분하기, 실제 실행 도구·증거 없이 완료를 약속하지 않기. 이는 후보 지시를 검토할 기준이지 이 예시를 실제 지시·점수 파일에 덮어쓰라는 뜻이 아닙니다.

| 실제 결과에서 발견한 문제 | 먼저 확인할 개선 위치 |
|---|---|
| 검색 문맥 자체가 낡거나 관련 없음 | IQ의 정책 문서·발효일·검색 결과 |
| 근거는 맞지만 조건·route·권한을 잘못 판단 | 실제 답과 Judge 이유를 보고 지시의 판단 규칙 |
| JSON 형식이나 `needs_human` 불일치 | 출력 계약·분류 지침 |
| API/평가 오류 또는 교정 불일치 | 환경·측정·평가기/참조의 문제. 답변 개선 효과로 포장하지 않음 |

**고친 뒤에는 같은 dev 문항으로 다시 확인합니다.** 이번 경로는 아래 IQ·Agent Optimizer 단계에서 이를 수행합니다. 보기 좋은 예시나 길어진 지침만으로 개선을 인정하지 않습니다.

**완료 확인:** 실제 Agent 버전·세 응답·교정 보고서·내 판단과 Judge의 차이를 확인했습니다. 검색 없는 기준선의 근거성을 정책으로 대신 채우지 않습니다. smoke/dev 자체는 최종 시험이 아니므로 그 `HOLD`와 **교정 HOLD**를 구별하고, 오류·누락을 숨기지 않습니다.

<p class="step-next no-print"><a href="#iq" data-next-step>다음: 04. 지식 연결 →</a></p>

## 04. IQ 지식 연결 {#iq}

**할 일:** 같은 지시문에 실제 지식 검색 도구만 더합니다. 신규 환경의 임베딩 배포와 합성 Contoso 정책 8개를 사용합니다.

**실행 명령 · 지식 준비·검색 확인, 유료:**

```bash
python -m lab --config "$LAB_ENV_FILE" iq prepare --confirm
python -m lab --config "$LAB_ENV_FILE" iq vectors --query "최초 월 구독 환불에 필요한 조건은 무엇인가요?" --confirm
python -m lab --config "$LAB_ENV_FILE" iq probe --query "이전 구매와 9월 이후 최초 월 구매의 환불 기한 및 심사 신청 조건을 비교해 주세요." --confirm
```

순서대로 **실제 1536차원 임베딩·인덱스/KB 준비 → vector-only와 hybrid 검색 → IQ의 `modelQueryPlanning`·검색 활동·출처**를 확인합니다. 인덱스 존재나 설정값만으로 검색 성공을 주장하지 않습니다. 위 진단 결과를 에이전트의 `retrieved_context`에 복사하지 않습니다.

**실행 명령 · IQ Agent의 dev 12건 실행·동일 Judge 평가, 유료:**

```bash
python -m lab --config "$LAB_ENV_FILE" agent --stage iq --confirm
python -m lab --config "$LAB_ENV_FILE" run --stage iq --split dev --run-id iq-dev --interval-seconds 65 --confirm
python -m lab --config "$LAB_ENV_FILE" judge score --run-id iq-dev --interval-seconds 65 --confirm
python -m lab score --run-id iq-dev
python -m lab explain --run-id iq-dev
```

<p class="output-label" id="example-iq-report">출력 예시 · explain의 요약 일부 · 아래 수치는 설명용 작성 값</p>

```text
# 평가 결과 해설
- 실행: iq-dev / 단계: iq / 분할: dev / 12건
- 기준: 현재 config/gates.json; 최종 최소 표본 20건
- 게이트 결과: **HOLD** / 운영 승인: **not_granted**

| 평가 항목 | 실제 값 | 기준 | 관측 범위 |
| 업무 정확성 | 4.25 | 평균 ≥4 | 점수 12/12; 누락 0; 척도 [1.0, 5.0] |
| 검색 근거성 | 4.50 | 평균 ≥4 | 점수 12/12; 누락 0; 척도 [1.0, 5.0] |
```

**읽는 법:** 높은 평균만으로 통과가 아닙니다. `explain`의 **HOLD 원인과 다음 확인**에서 범위·누락·오류·중요 실패를 보고, **사례별 해설**에서 실제 답과 Judge 이유를 읽습니다. 이 작성 예시의 dev 12건도 최종 시험은 아니며, 실제 실행에 다른 실패가 없는지는 전체 결과로 확인해야 합니다.

<p class="share-checkpoint" id="share-iq">결과 공유 · 검색을 붙이니 업무 답변도 나아졌을까?</p>

- **실제 결과:** `iq-dev` **12건**의 `groundedness`와 `policy_correctness`를 **각각의 점수 수·누락·오류**와 함께 읽습니다. 인용 ID가 있다는 사실만으로 검색 근거성이 입증되지는 않습니다.
- **대표 사례:** 기준선과 **겹치는 3개 사례 ID**에서 답변·정책 판단이 어떻게 달라졌는지 봅니다. 해당 응답의 실제 MCP 문맥도 확인합니다. 기준선 3건과 IQ 12건의 **전체 평균끼리 비교하지 않습니다.**
- **다음 결정:** “검색 근거는 ___이지만 업무 판단은 ___여서, 다음에는 ___ 지시를 개선한다”를 공유합니다. **검색에 충실한 답과 업무에 맞는 답이 다를 수 있음**을 확인하는 지점입니다.

**완료 확인:** dev 12건의 실제 응답·`knowledge_base_retrieve` 호출/MCP 출력·업무 점수와 이유가 남았습니다. 다음 단계의 비교 기준선은 **`iq-dev`**입니다. `--interval-seconds 65`는 사례 간 대기이지 재시도가 아니며, 429·403·문맥 누락은 보존하고 중단합니다. 같은 run을 다른 평가 경로로 재채점하지 않습니다.

<p class="step-next no-print"><a href="#optimize" data-next-step>다음: 05. 지시 개선 →</a></p>

## 05. Agent Optimizer 지시 개선 {#optimize}

**할 일:** 오류 없이 완료된 `iq-dev` 12건과 실제 MCP 출력을 기준으로 **Agent Optimizer 한 작업·후보 한 개**를 실행합니다. 모델과 IQ 연결은 유지하고 지시만 바꿉니다.

지침은 **원본 → 개선본**으로 비교합니다. `baseline`과 `iq`는 같은 [`prompts/baseline.txt`](../prompts/baseline.txt)를 사용하고, `optimized`는 실제 서비스 결과에서 가져온 `optimizer/selected-prompt.txt`를 사용합니다. 고정된 `v1.txt`·`v2.txt`를 고르는 방식이 아니며, 지침이 길어졌다는 사실만으로 개선을 인정하지 않습니다.

**실행 명령 · 로컬 입력 준비:**

```bash
python -m lab optimize --run-id iq-dev
python -m json.tool "$LAB_ARTIFACTS_DIR/optimizer/handoff.json"
```

<p class="output-label" id="example-optimizer-handoff">출력 예시 · handoff.json 일부</p>

```json
{
  "kind": "agent-optimizer-handoff",
  "status": "PREPARED_NOT_SUBMITTED",
  "source_run_id": "iq-dev",
  "source_split": "dev",
  "test_data_included": false
}
```

**읽는 법:** 입력 파일 준비만 끝났습니다. **서비스 작업이나 새 Agent는 아직 없습니다.** 같은 파일의 `agent_name`·`agent_version`을 다음 화면에서 사용합니다.

**이 단계에서만 Foundry 포털을 사용합니다.** 같은 계정·프로젝트에서 **Agents → handoff에 기록된 IQ agent → Optimize → Create optimization run**을 엽니다. [공식 prompt-agent 안내](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent)와 함께 아래 값을 그대로 적용합니다.

| 화면 | 실습에서 사용할 값 |
|---|---|
| Target | handoff의 정확한 IQ agent 버전. 지시(`instruction`)만 최적화 |
| 모델 | manifest의 실제 optimizer·judge 배포. **Compare across models 끔** |
| Maximum candidates | **1**. 작업도 1회만 제출 |
| Dataset | **Upload** → `$LAB_ARTIFACTS_DIR/optimizer/dev-upload.jsonl`의 실제 파일. 생성·다른 데이터셋 선택 안 함 |
| Criteria | **Relevance + Task Adherence**, 각각 합격선 **4**. 입력 열 `query`, `context`, `ground_truth` 확인 |
| Review | 같은 모델·IQ MCP 유지, dev 12건, 승인된 비용/작업 범위를 확인한 뒤 제출 |

작업당 최대 대기는 현재 승인 범위 안에서 **60분 이내**입니다. 시간 초과·지원/접근 차단이면 상태를 남기고 멈춥니다. Prompt Optimizer·수작업 지시·다른 모델로 대체해 완료 처리하지 않습니다.

**작업이 `succeeded`이면:** 기준선과 후보의 지시 diff, 사례별 점수와 회귀를 읽습니다. 서비스 순위는 본 실습의 업무 Judge나 운영 승인을 대신하지 않습니다. 후보에 dev에서 유도한 예시가 들어갈 수 있으므로 독립 시험이 필요합니다.

<p class="share-checkpoint" id="share-optimizer">결과 공유 · Optimizer가 이 후보를 추천한 이유는?</p>

- **실제 결과:** 포털의 **원본 대 후보** 평가별 점수, 사용한 척도·dev 12건·작업/후보 ID를 함께 읽습니다. 0–1 순위 점수와 본 실습의 1–5 업무 Judge 점수를 같은 숫자처럼 합치지 않습니다.
- **대표 사례:** 지시 diff와 대표 응답을 연결해 무엇이 바뀌었는지 설명합니다. 서비스가 미완료·실패했다면 없는 점수나 개선율을 만들지 않습니다.
- **다음 결정:** “서비스 기준으로 ___여서 이 후보를 **재평가**한다/보류한다”를 공유합니다. **Optimizer의 추천은 후보 선택 근거이지 최종 채택이나 운영 승인이 아닙니다.**

완료 run의 **Download JSON**과 후보의 **Download config**를 다음 비공개 파일명으로 저장합니다. 파일 선택기에는 `$LAB_ARTIFACTS_DIR`라는 글자 대신 **02에서 정한 실제 폴더**를 사용합니다. 포털의 Promote로 활성 버전을 바꾸지 않고 아래 CLI로 별도 실습 버전을 만듭니다.

| 저장할 내용 | `$LAB_ARTIFACTS_DIR` 아래 경로 |
|---|---|
| 완료 run JSON | `optimizer/agent-optimizer-final.json` |
| 후보 config JSON | `optimizer/agent-optimizer-candidate-config.json` |

**실행 명령 · 서비스 후보 가져오기:**

```bash
python -m lab --config "$LAB_ENV_FILE" optimizer-agent-result --result "$LAB_ARTIFACTS_DIR/optimizer/agent-optimizer-final.json" --candidate "$LAB_ARTIFACTS_DIR/optimizer/agent-optimizer-candidate-config.json"
```

<p class="output-label" id="example-optimizer-candidate">출력 예시 · 후보 import 결과 일부</p>

```json
{
  "kind": "AGENT_OPTIMIZER_PORTAL_CANDIDATE_IMPORT",
  "status": "CANDIDATE_CAPTURED_NOT_LAB_APPROVED",
  "job_id": "EXAMPLE_JOB_ID",
  "candidate_id": "EXAMPLE_CANDIDATE_ID",
  "imported_fields": ["system_prompt"],
  "human_operational_approval": "NOT_GRANTED"
}
```

**읽는 법:** 실제 작업/후보의 지시를 `selected-prompt.txt`로 가져왔을 뿐 **실습 품질 통과는 아닙니다.** 지시만 가져오며 config의 `tools: []`로 IQ MCP를 지우지 않습니다. 파일이 없거나 계약이 다르면 가짜 결과를 만들지 않습니다.

**실행 명령 · 새 버전 생성·같은 dev 12건 재평가, 유료:**

```bash
python -m lab --config "$LAB_ENV_FILE" agent --stage optimized --confirm
python -m lab --config "$LAB_ENV_FILE" run --stage optimized --split dev --run-id optimized-dev --interval-seconds 65 --confirm
python -m lab --config "$LAB_ENV_FILE" judge score --run-id optimized-dev --interval-seconds 65 --confirm
python -m lab score --run-id optimized-dev
python -m lab explain --run-id optimized-dev --baseline iq-dev
```

**마지막 명령은 저장된 동일 문항의 전후 비교입니다.** 데이터·사례 ID·Judge/척도가 다르면 비교를 거부합니다. 기존 `compare_runs` 엔진으로 설정된 회귀 허용폭을 로컬 계산하며 새 모델 호출은 없습니다. dev의 종합 HOLD를 PASS로 바꾸지 않습니다.

| 자동으로 계산하는 진단 | 현재 허용폭 |
|---|---|
| 형식·사람 판단 표시·금지 주장 통과율 하락 | 0%p |
| route 정확도·인용 통과율 하락 | 각각 최대 5%p |
| 검색 근거성·질문 적합성 평균 하락 | 각각 최대 0.2점 |
| 지연 증가율 | 허용폭 미설정 — 자동 판정하지 않음 |

**자동과 사람 판단을 구분합니다.** `score`/`finalize`는 한 실행의 게이트를 검사합니다. `explain --baseline`을 붙인 경우에만 전후 회귀 진단도 표시합니다. **업무 정확성의 전후 변화·지시 diff·실제 문장의 타당성·최종 채택**은 사람이 확인합니다. 정책 점수 하락의 별도 자동 허용폭은 설정되어 있지 않으며, 위 진단이 운영 승인은 아닙니다.

<p class="share-checkpoint" id="share-optimized">결과 공유 · 같은 업무 기준으로도 개선됐을까?</p>

- **실제 결과:** `explain --baseline`의 **같은 문항의 자동 회귀 진단**에서 원본/후보 값·하락폭·허용폭·미측정을 읽습니다. 평균뿐 아니라 **점수 있는 행 / 전체**, 오류·누락·critical 사례별 결과도 확인합니다.
- **대표 사례:** 사례별 **이전 최종 응답·현재 응답·전후 점수·현재 Judge 이유**를 연결해 개선된 답과 나빠졌거나 여전히 부족한 답을 설명합니다. 해당 변화가 관측되지 않았다면 “관측 없음”으로 남깁니다. 이전 판단 이유는 원본 run의 `explain`으로 확인합니다.
- **다음 결정:** “___는 좋아졌지만 ___ 위험이 남아 후보를 동결/보류한다”를 공유합니다. **평균 상승이 중요한 실패나 회귀를 상쇄하지 못함**을 확인합니다.

**완료 확인:** `iq-dev`와 `optimized-dev`의 **같은 사례 ID**를 비교해 바뀐 답·점수·회귀를 설명할 수 있습니다. 검색 변동까지 통제한 “프롬프트 문구만의 인과 효과”로 과장하지 않습니다. critical 회귀·오류·누락이면 후보를 채택하지 않고 HOLD를 남기며 재제출하지 않습니다.

<p class="step-next no-print"><a href="#decision" data-next-step>다음: 06. 최종 판정·종료 →</a></p>

## 06. 최종 판정·종료 {#decision}

**할 일:** 개선 후보를 동결한 뒤 새 질문으로 한 번 평가하고, 실제 상태와 다음 행동을 남깁니다. **앞 단계가 차단되었거나 교정·후보 근거가 불충분하면 아래 유료 최종 시험은 실행하지 않고 [종료 기록](#cleanup)만 작성합니다.** 미실행을 성공으로 바꾸는 대체 경로가 아닙니다.

**실행 명령 · 교정·후보 검토가 끝난 경우에만 동결·새 holdout 생성:**

```bash
python -m json.tool config/evaluators/fresh-holdout-gates.v1.json
python -m lab --config "$LAB_ENV_FILE" freeze --freeze-id selected-v1 --stage optimized --calibration-id cal-01
python -m lab holdout create --freeze-id selected-v1 --holdout-id fresh-01 --count 12
```

**확인 후 계속:** 동결에 agent 버전·prompt/model/search/evaluator/gates/data/교정 해시가 묶이고, **동결 이후 생성·등록한 fresh12**가 그 동결을 참조해야 합니다. 원본 test20을 대체하거나 `config/gates.json`의 `minimum_test_rows: 20`을 낮추지 않습니다. 작성 템플릿의 변형인 합성 질문을 독립 고객 표본으로 과장하지 않습니다.

**실행 명령 · 동결한 후보의 최종 12건 실행·채점, 유료:**

```bash
python -m lab --config "$LAB_ENV_FILE" run --stage optimized --split test --run-id optimized-fresh --freeze-id selected-v1 --holdout-id fresh-01 --interval-seconds 65 --confirm
python -m lab --config "$LAB_ENV_FILE" judge score --run-id optimized-fresh --interval-seconds 65 --confirm
python -m lab score --run-id optimized-fresh
python -m lab explain --run-id optimized-fresh
python -m json.tool --json-lines "$LAB_ARTIFACTS_DIR/runs/optimized-fresh/outputs.jsonl"
```

이 설명에는 **동결된 fresh 표본 계약과 게이트**가 적용됩니다. 현재 개발용 게이트로 바꾸거나 기존 test20의 기준을 낮추지 않습니다. 다른 질문인 dev 결과를 `--baseline`으로 붙이지 않습니다.

최종 사례는 12건이며 명시적 후속 발언이 있는 대화 때문에 정상 capture는 **13턴**입니다. 마지막 답뿐 아니라 초기 `clarify`·scripted-user 출처·최종 답을 모두 읽습니다. `schema_and_clarify_only/not_semantic_safety`는 초기 형식 검사이지 초기 설명의 의미 안전성 보증이 아닙니다.

동결 후 지시·모델·데이터·평가기를 바꾸거나 결과가 나쁘다고 holdout을 다시 뽑지 않습니다. 오류와 점수 누락도 분모에 남깁니다. 중단된 배치는 [강사용 재개 안내](facilitator.md#resume)로 같은 ID·입력을 확인하며, 불명확한 제출·완료된 Judge를 재호출하지 않습니다.

<a id="review"></a>

**실행 명령 · 최종 판정, 로컬:**

```bash
python -m lab governance finalize --freeze-id selected-v1 --run-id optimized-fresh
```

<p class="output-label" id="example-final-verdict">출력 예시 · 최종 실행 완료와 품질 HOLD가 함께 있는 경우</p>

```json
{
  "sample_count": 12,
  "execution_status": "completed",
  "judge_execution_status": "completed",
  "quality_status": "HOLD",
  "manual_operational_approval": "not_granted",
  "production_ready": false
}
```

**읽는 법:** API 실행·채점 완료, 품질 판정, 운영 승인은 각각 다릅니다. 예시는 **실행은 끝났지만 채택은 보류**입니다. 최종 출력의 `gate.checks`에서 `passed: false`인 검사와, 앞서 읽은 `explain`의 원인·실제 문장·Judge 이유를 연결합니다. AI 검토를 사람 검토로 바꾸지 않습니다.

이미 최종 판정이 있으면 `finalize`를 반복하지 않고 `python -m lab governance status --freeze-id selected-v1`로 읽습니다. 실제 사람 기록이 필요할 때만 [검토 형식](facilitator.md#review)을 사용하며, 승인 부재를 숨기지 않습니다.

<p class="share-checkpoint" id="share-holdout">결과 공유 · 처음 보는 질문에도 통하고, 지금 채택해도 될까?</p>

- **실제 결과:** `optimized-fresh`의 **동결 후 새 12건**에 대한 점수·coverage·누락·critical 결과와 최종 `quality_status`를 읽습니다. 실행 완료와 사람의 운영 승인도 따로 공유합니다.
- **대표 사례:** 정상 답 하나와 중요 실패·확인 질문 대화 중 한 건을 정책과 대조합니다. 마지막 답만 보지 말고 초기 답과 후속 사용자 발언도 확인합니다.
- **다음 결정:** 근거와 함께 채택/보류 이유를 말합니다. **dev 12건과 fresh12는 다른 질문이므로 전후 평균 개선율로 비교하지 않습니다.** 좋은 dev 점수만으로 일반화를 보장할 수 없고, 소규모 합성 시험 통과도 운영 안전 인증은 아닙니다.

<a id="operate"></a>

**실행 명령 · 실제 최종 run 관측, 읽기 전용:** 02에서 설정한 관측 ID를 그대로 사용합니다.

```bash
python -m lab --config "$LAB_ENV_FILE" control-plane --run-id optimized-fresh --app-insights-id "$APPLICATIONINSIGHTS_RESOURCE_ID"
```

<p class="output-label" id="example-traces">출력 예시 · trace가 아직 관측되지 않은 경우</p>

```json
{
  "status": "NOT_VERIFIED_NO_TRACES",
  "observed_rows": 0,
  "error_absence_claim": false,
  "cost": {"status": "NOT_OBSERVED"}
}
```

**읽는 법:** trace 0건은 **관측 미확인**이지 오류 0건·비용 0원이 아닙니다. 일부만 연결되면 `PARTIAL`, 필요한 연결이 확인되면 `VERIFIED_TRACE_MODEL_TOOL_EVAL_LINKS`입니다. trace를 만들려고 모델을 재호출하지 않으며 정책 적용·실제 청구도 별도로 확인합니다.

**실행 명령 · 다음 개선 질문 남기기, 로컬:**

```bash
python -m lab feedback --run-id iq-dev --feedback-id iq-dev-next-review
```

실제 dev 실패·응답 ID에 연결된 사람 검토 대기열이며 `ground_truth`는 비어 있고 검토는 `PENDING`입니다. 자동 학습·배포가 아닙니다. 최종 test/fresh holdout을 개발·최적화 데이터로 옮기지 않습니다.

<a id="cleanup"></a>

**결과를 남기고 종료 — 정상 완료와 HOLD 모두 여기서 마칩니다.**

| 기록할 것 | 남길 내용 |
|---|---|
| 예시와 실제 실행 | DEMO는 authored. 실제 버전·response/작업/평가 ID가 있는 것만 LIVE |
| 개선 결과 | 변경한 지시, 정책·사례·문장 근거, 회귀와 누락 |
| 최종 상태 | 실제 quality 결과, HOLD 이유, 차단되어 **미실행**인 단계 |
| 사람 판단 | 실제 검토 출처와 운영 승인 부재. AI를 사람으로 표시하지 않음 |
| 관측·보존 | trace 확인/부분/없음, 비용 확인 담당자·다음 확인 시점 |

**실행 명령 · 삭제하지 않는 로컬 정리 계획:** 02의 환경 연결이 완료된 경우에만 읽습니다. 환경 준비 전 중단했다면 실행하지 않고 준비 미완료를 기록합니다.

```bash
python -m lab --config "$LAB_ENV_FILE" cleanup
```

**삭제 승인은 없습니다.** `--confirm-prefix`를 추가하거나 포털에서 자원을 지우지 않습니다. 비공개 원본·실험 계약·새 RG를 보존합니다. 터미널을 닫아도 Search·로그·모델 호스팅 비용은 계속될 수 있습니다.

**완료 확인:** 다음 문장을 근거와 함께 완성하면 참가자 경로는 끝입니다. 읽음 체크만으로 LIVE 완료를 주장하지 않습니다.

> “___ 지시를 바꿨고, 사례 ___의 정책/응답 ___를 근거로 후보를 ___한다. 최종 시험은 ___ 상태이며, 사람의 운영 승인은 ___이다. 남은 위험과 다음 행동은 ___이다.”

**다른 실습을 추가로 끝낼 필요는 없습니다.** 실행 완료가 품질 합격은 아니며, 품질 HOLD를 정직하게 설명하는 것도 학습 결과입니다.

결과가 없으면 **미실행/미측정**으로 공유하며, 설명용 예시나 다른 실행의 결과를 내 실행 결과로 제시하지 않습니다. 원본은 비공개로 보존합니다.

<a id="tune"></a>
<a id="troubleshooting"></a>
<a id="sources"></a>

참고가 필요할 때만: [운영자 사전 준비](admin-setup.md) · [오류·재개 및 별도 진단](facilitator.md#resume) · [SFT/Frontier 부록](sft-appendix.md) · [데이터 설명](../data/README.md) · [실제 검증 기록](verification.md) · [이관·출처](integration-migration.md).

화면 상단의 **어둡게/밝게**는 선택을 기억합니다. **현재 인쇄**는 읽는 단계만, **전체 PDF**는 이 문서 전체를 인쇄 창으로 엽니다. PDF로 저장을 선택하면 되며, 인쇄 배경은 항상 밝게 유지합니다.

문서 기준 **2026-09-30**, 가이드 **v1**. `python -m lab`는 이 저장소의 교육용 도구이며 Microsoft 공식 CLI가 아닙니다. 서비스 지원·리전·모델·비용은 바뀔 수 있으며, 기존 검증 기록은 참가자의 새 실행이나 운영 승인을 대신하지 않습니다.
