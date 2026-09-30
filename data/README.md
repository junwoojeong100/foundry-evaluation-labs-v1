# 한국어 합성 평가 데이터 {#data-guide}

[참가자 데이터셋 단계](../guide/handbook.md#start) · [운영자 인수](../guide/admin-setup.md#handoff) · [English data guide](README.en.md)

## 워크숍 파일을 변경 없이 사용 {#start}

한국어 워크숍은 **[data/optimizer/dev.jsonl](optimizer/dev.jsonl)**을 직접 Microsoft Foundry 관리형 Evaluation, Agent Optimizer, 별도 직접 재평가에 사용합니다. `query`, `context`, `ground_truth`로 구성된 **정확히 12개 JSONL 레코드**입니다. 폴더 이름과 관계없이 전체 평가 흐름이 공유하는 데이터셋입니다.

한국어는 운영자가 준비한 **`contoso-eval-ko` 버전 `1`**과 **`contoso-eval-ko-dev12`**를 사용합니다. 등록 상태를 별도로 확인하고 이미 등록됐다면 중복 업로드하지 않습니다. 실제 데이터셋 버전과 원본 파일의 **SHA-256**을 기록하며 기준선·최적화·재평가에서 유지합니다. 등록은 평가 결과가 아닙니다.

**실제 등록이 확인된 영어 데이터셋은 `contoso-eval-en-dev12` 버전 `1`**이며 원본 `data/en/optimizer/dev.jsonl` 12행을 네이티브 Evaluation 마법사로 등록했습니다. 영어 에이전트는 **`contoso-eval-en` 버전 `1`**입니다. **이번 리허설에서 한국어를 재실행하지 않았으며 새로운 한국어 실측 결과는 없습니다.** 한국어 응답은 한국어, 영어 응답은 영어여야 합니다. 언어가 다른 실행은 지시 개선의 동일 조건 비교 근거가 아닙니다.

이전 영어 **`contoso-en-baseline-luna-judge`**는 **CONFIGURATION PILOT(설정 파일럿)**으로 유지합니다. 정식 **`contoso-en-learning-loop`**는 같은 고정 Agent·데이터 v1과 `gpt-6-luna` Judge에서 **Completed, 12행, 10 passed / 2 failed / 0 errored, Relevance 10/12·TaskAdherence 12/12(이진값 1)**입니다. 실제 ID는 [03단계](../guide/handbook.md#baseline)에 있으며 후보 개선이 아닌 기준선만의 결과입니다.

지시 전용 작업 **`opt_e44bcf5701a348deb62a1cd4f9cb3910`**이 같은 데이터셋·`gpt-5.5` 생성·`gpt-6-luna` Judge·모델 비교 없음으로 **후보 하나를 생성해 성공**했습니다. **0.635 → 0.646**, **UI 표시 +0.010**, **보고 토큰 264,260**은 직접 후보 점수가 아닌 Optimizer 결과입니다. Promote로 실습 v2를 만들고 지시 일치·모델·지식 도구 불변을 확인했습니다. **최신 활성 버전은 모든 채널에 영향: 격리된 미게시 실습만 허용, 운영 승격 금지**입니다.

## 목적과 한계 {#scope}

Contoso Atlas Cloud는 **완전히 가상인 시나리오**입니다. 정책 8개, 질문, 참고 답변, 작업 공간 예시는 합성 자료입니다. 실제 비공개 고객 대화·계정·자격 증명·운영 승인이 포함되어 있지 않으며 실제 공급자의 약관도 아닙니다.

방법은 **평가 → 실패에서 학습 → 개선 → 재평가**입니다. 애플리케이션에는 공개 벤치마크 점수만 보는 것보다 회사가 보유한 대표 업무, 정책 경계 사례, 알려진 실패가 더 유용합니다. 이 자료는 회사의 비공개 데이터를 쓰지 않고 그런 판단을 살펴보는 방법을 보여 줍니다.

합성 자료 작성은 사람 검토 완료를 의미하지 않습니다. 행 수·해시는 데이터 무결성이지 모델 품질 지표가 아닙니다. 개발 사례 12건으로 운영 행동·일반화·정책 준수·안전을 인증할 수 없습니다.

## 원본 구성과 워크숍 경계 {#composition}

원본 [data/cases.jsonl](cases.jsonl)에는 고정 분할 라벨의 **100건**이 있습니다.

| 원본 분할 | 행 수 | 이번 워크숍 용도 |
|---|---:|---|
| `train` | 56 | 미사용·예약된 원본 분할 |
| `validation` | 12 | 미사용·예약된 원본 분할 |
| `dev` | 12 | 유일한 사용 사례. `data/optimizer/dev.jsonl`로 제공 |
| `test` | 20 | 미사용·예약된 원본 분할 |

dev12 대신 원본 100건을 업로드하거나 분할을 합치거나 쉬운 질문만 고르거나 행을 복제하지 않습니다. 원래 데이터 자산을 유지하며 다른 분할은 참가자 실습에 포함하지 않습니다.

[한국어 정책 문서](knowledge/documents.json)는 안정된 `ATLAS-*` ID와 정책 원문 발췌를 제공합니다. 에이전트의 정책 접근은 운영자 사전 준비이며 별도 데이터셋·지식 구축 실습이 아닙니다.

## 업로드·응답 계약 {#schema}

각 줄은 다음 세 열만 가진 JSON 객체 하나입니다.

| 열 | 형식 | 경계 |
|---|---|---|
| `query` | 문자열 | **에이전트에는 이 필드만 전송** |
| `context` | 문자열 | 지원되는 평가자와 검토자를 위한 정책 원문. 생성 입력에 붙이지 않음 |
| `ground_truth` | 중첩 객체가 아닌 **JSON 문자열** | 지원되는 평가자·검토용 참고 응답. 생성 입력으로 사용 금지 |

**미리 채운 `response`는 없습니다.** Foundry가 선택한 에이전트 버전을 실행해 실제 응답을 얻습니다. `response`를 만들거나 열 이름을 바꾸거나 레코드를 JSON 배열로 감싸거나 다른 작업 스키마를 추가하지 않습니다.

`ground_truth`를 해석하면 정확히 네 키의 객체가 됩니다. 에이전트도 같은 응답 계약을 사용합니다.

| 키 | 기대 값 |
|---|---|
| `answer` | 비어 있지 않은 **한국어** 문장. 짧은 계약 예시는 “구매일을 확인해 주세요.” |
| `citations` | `["ATLAS-REF-001"]`처럼 근거가 되는 안정된 정책 ID 배열. 없는 ID 생성 금지 |
| `route` | 일반 안내 `answer`, 필요한 정보 확인 `clarify`, 필수 사람 판단 `escalate`, 금지 요청 거절 `refuse` |
| `needs_human` | 불리언. **`route`가 `escalate`일 때만** `true` |

위 값은 스키마 예시이지 실제 생성 답변이 아닙니다. `escalate`가 이미 사람에게 연락했다는 뜻은 아닙니다. 에이전트에는 업무 실행 도구가 없으므로 승인·티켓 ID·환불·삭제·접근 변경 완료를 만들어서는 안 됩니다.

원본 사례 ID, 행동 라벨, 나머지 메타데이터는 원본에 남기며 생성 입력에 추가하지 않습니다. 결과 검토 시 실제 질문과 안정된 행 위치·원본 사례를 기준으로 평가 행을 대응시킵니다.

정책 발췌는 참고 자료이지 에이전트 도구가 실제 검색한 내용의 증거가 아닙니다. 질문·문서 안에 인용된 지시를 상위 명령으로 바꾸지 않습니다. 답변 글자의 완전 일치가 아니라 의미와 정책 판단을 비교합니다.

## 한 번 등록하고 같은 버전 선택 {#upload}

아직 v1인 새 한국어 Agent에서 **Foundry New experience → Build → Evaluations → Create → Create new evaluation → Agent → `contoso-eval-ko`**를 선택합니다. 구성 변경 전 고정·체크박스 재선택·Next 전 대상 1개를 확인하고 Individual turns / One time / Existing dataset을 사용합니다. 실제 영어 Agent는 v2를 보존한 채 활성 v1으로 복원됐으므로 “최신”을 추정하지 말고 저장된 v1 기준선·데이터를 사용합니다.

한국어 데이터셋이 아직 등록되지 않았다면 **Upload new dataset → 이름 → Choose file**에서 `data/optimizer/dev.jsonl`을 선택해 **Upload**합니다. 등록된 같은 버전이 있다면 다시 업로드하지 않습니다. 선택과 미리 보기를 확인하되 화면은 **처음 5행만** 보여 주므로 원본의 **전체 12개 레코드**를 유지하고 SHA-256을 확인합니다.

관측한 영어 마법사에서는 일치하는 스키마로 **Field mapping이 자동 해결**되어 바로 **Configure agents**로 이어졌습니다. **custom prompt override는 미설정**, Agent 입력은 **`query`만** 유지하고 **Criteria**로 진행합니다. 한국어 경로에서 선택한 스키마의 매핑 화면이 나타나면 **query → query**를 사용합니다.

**제안 23개**의 나머지를 제거하고 정확히 **Relevance + TaskAdherence**, **`lab-judge-luna-dea3cec5`**를 사용합니다. **Relevance는 1–5점·임계값 4**, **TaskAdherence는 Binary Pass/Fail·원시 0/1·통과값 1**이며 범용 UI가 보이면 **Threshold 1**로 설정 후 Update합니다. [공식 정의](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators)를 따릅니다. 영어 **Evaluation name `contoso-en-learning-loop` → Submit**은 HTTP 201로 확인됐으므로 다시 제출하지 않습니다. 한국어는 별도 수정 정의를 사용합니다.

**생성된 매핑을 확인하되 덮어쓰지 않습니다.** 수정된 제출은 **Relevance `response={{sample.output_text}}`**, **TaskAdherence `response={{sample.output_items}}`**를 확인했습니다. UI 기본값에는 **`query={{item.query}}`**, TaskAdherence의 **`tool_definitions={{sample.tool_definitions}}`**도 있었습니다. **Raw JSON**을 읽되 TaskAdherence를 이전 UI output-text 값으로 되돌리지 않습니다. 업로드에 미리 채운 `response`는 없고 Agent 입력은 `query`만입니다.

**버전 한계:** 카탈로그 링크에는 `relevance` **v14**, `task_adherence` **v17**이 보였지만 실제 서비스의 **`evaluator_version`은 비어 있거나 기본값**이었습니다. 이름·설정, Judge·데이터셋 버전과 비공개 서비스 루브릭 버전 고정이 입증되지 않았다는 한계를 기록합니다.

Agent Optimizer는 **Next → Select dataset and criteria**, **같은 등록 dev12 버전**을 사용합니다. Criteria의 **No custom evaluators available**에서는 **Custom only를 OFF**로 바꾸거나 **View built-in evaluators**를 누릅니다. 행 선택으로 **Configure...**를 열어 **Relevance 4 / TaskAdherence 1**을 각각 **Apply**합니다. 이진 통과값 1·같은 Judge를 유지하며 사용자 정의 평가자는 필요하지 않습니다. [Optimizer 단계](../guide/handbook.md#optimize)를 확인합니다.

## 근거를 바꾸지 않고 비교 {#compare}

| 동일하게 유지 | 각 실제 실행에서 기록 |
|---|---|
| 전체 12문항, 참고 자료, 언어, 데이터셋 버전, 파일 SHA-256 | 같은 평가 정의 ID, 서로 다른 run ID, 명시적 Agent 버전, 최종 상태 |
| 같은 수정 정의, Relevance 임계값 4, TaskAdherence 이진 통과값 1, 기록한 설정 | Relevance 1–5점·TaskAdherence 0/1 결과, 지표별 통과 건수·범위·오류와 서비스 버전 한계 |
| Judge 배포·모델 버전, 에이전트 모델, 도구·연결 | 실제 답변·이유, 지시 차이, 사례별 회귀 |

실패·최저 Relevance 사례와 존재한다면 좋은 사례를 읽습니다. 누락·오류도 **n = 12**에 남깁니다. **Relevance 1–5점은 백분율 정확도가 아니며 TaskAdherence 0/1은 Fail/Pass**이지 5점 척도가 아닙니다. 누락 점수를 0으로 채우지 않으며 Completed는 품질 통과가 아닙니다.

실제 답변은 행의 **conversation_id → User view**에서 읽습니다. 질문·JSON 응답 화면이지 인라인 Judge 이유 패널이 아닙니다. **Detailed metrics result**로 돌아가 **`Relevance.reason` / `TaskAdherence.reason`**을 참고 정책과 대조하며 점수만 높이려고 정책 사실을 바꾸지 않습니다.

**포털 후보 제출 차단:** Add run → Pin v2 / Individual turns에서 Config required → Add custom prompt / User prompt를 요구했고 `{{item.query}}`에도 **`Unable to create data source configuration from item schema`** 클라이언트 오류가 났습니다. 이 시도로 원격 후보 run은 제출되지 않았습니다. 데이터셋 수정·가짜 response·새 평가 정의로 우회하지 않습니다.

[venv·`requirements.lock`·`az login` 계정 확인](../guide/admin-setup.md#sdk-prerequisites) 뒤 `scripts/add_foundry_eval_run.py`의 [단일 SDK 명령](../guide/handbook.md#decision)을 사용합니다. endpoint·구독은 운영자가 제공하고 evaluation/기준선 run ID는 기준선 포털 URL 또는 Raw JSON에서 복사합니다. Azure AI Projects/OpenAI Evals helper는 기준선 `data_source`·기존 기준을 재사용하고 대상 버전만 **2**로 바꾸며 모델·도구를 검증해 **같은 evalID의 실제 Foundry run**을 제출합니다. 로컬 Judge가 아닙니다.

**검증된 영어 네이티브 결과:** helper가 같은 **`eval_94feef6f6f644fabb22a5680f5f24fb1`** 아래 `contoso-eval-en` v2의 **`evalrun_f3b710fc835d444fb8aa0d2bb7797bdf`**를 제출했습니다. **12행, 11 passed / 1 failed / 0 errored**로 완료됐으며 기준선은 **10 passed / 2 failed / 0 errored**였습니다. 데이터셋·평가자·Judge·모델·도구가 같고 지시·버전만 바뀌었습니다.

원래 receipt·동일 명령으로 기존 run만 수집합니다. 영어는 **`contoso-en-learning-loop` → Evaluation runs → 두 체크박스 → Compare runs**를 열고 **Baseline 드롭다운에서 원래 `contoso-eval-en`을 선택**합니다. 기본값은 처음 선택한 행이며 실제로 `candidate-v2`였으므로 방향부터 확인합니다. 한국어 정의·receipt는 분리합니다.

최종 v1→v2 관측은 **Relevance 통과 10/12→11/12, 평균 4.4167→4.3333**, **TaskAdherence 양쪽 12/12·이진 평균 1.0**, 양쪽 오류 0입니다. Relevance 행 1은 **3→4**, 행 2·6은 **5→4**, 근거 없는 확답 대신 정직한 불확실성을 유지한 행 11은 **3**입니다. 정책 사실을 바꾸지 않습니다.

지연 **p50 5,891.09→7,287.52 ms**, **p95 8,817.33→16,038.35 ms**, Agent 토큰 **35,187→43,751**이 증가했습니다. 네이티브 **PairedTTest는 두 지표 모두 Inconclusive**입니다. **채택 HOLD, 추가 검토·새 대표 사례까지 고정 v1 유지**이며 통과 건수나 Optimizer +0.010만으로 전반적 개선을 주장하지 않습니다.

같은 dev12의 관측이며 **통계적 유의성·독립적인 일반화·운영 승인을 입증하지 않습니다**. 실제 SDK run은 원격 실행의 근거지만 로컬 파일·매니페스트만으로는 증명되지 않습니다. 원래 데이터 자산을 유지합니다.

**최종 실습 상태:** 채택 HOLD, 활성 버전 **1**로 복원, 후보 v2·평가 run·receipt는 삭제하지 않고 보존했습니다. 운영용 Publish·운영 채널·트래픽 구성은 없습니다. Foundry는 Publish 없이 **RBAC-only Responses/preview endpoints**를 자동 제공하며 이것을 운영 배포의 증거로 해석하지 않습니다.
