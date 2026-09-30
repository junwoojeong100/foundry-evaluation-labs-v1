# 강사 안내 · 평가 중심 학습 흐름 {#facilitator-guide}

[참가자 6단계](handbook.md#start) · [운영자 사전 준비](admin-setup.md#handoff) · [실측 검증](verification.md)

**평가 → 실패에서 학습 → 개선 → 재평가**를 가르칩니다. “점수가 올랐다”가 아니라 실제 질문·답변·평가 이유·정책 근거를 요구합니다. 회사가 보유한 대표 업무, 정책 경계 사례, 알려진 실패가 도메인 평가를 유용하게 만듭니다. 이 워크숍은 그 방법을 합성 Contoso 데이터로만 보여 줍니다.

## 수업 시작 전 {#prepare}

환경·예제 Agent·SDK 사전 준비는 운영자가 담당합니다. 참가자는 데이터셋부터 시작해 **Microsoft Foundry 관리형 Evaluation**, **지시 전용 Agent Optimizer**, **SDK 명령 하나로 실제 후보 run 생성 후 포털 Compare runs**를 사용합니다. 로컬 Judge가 아니며 평가자 두 개·6단계를 유지합니다.

- [운영자 인수](admin-setup.md#handoff)에서 프로젝트와 승인을 확인합니다. 실제 확인한 영어 준비는 **`contoso-eval-en` 버전 `1`**, **`lab-agent-dea3cec5`**, 기존 **읽기 전용 지식 연결 유지**입니다. 한국어 대응 대상 **`contoso-eval-ko`**는 운영자 준비를 별도로 확인하며 한국어 새 실행·실측 결과는 없습니다.
- 영어 **`contoso-eval-en-dev12` 버전 `1`**은 변경 없는 `data/en/optimizer/dev.jsonl` 12건으로 등록되었습니다. 원본 SHA-256을 유지합니다. 한국어는 `data/optimizer/dev.jsonl` 12건과 **`contoso-eval-ko-dev12`**의 별도 등록 확인이 필요합니다.
- 단일 fixture의 **`gpt-6-luna` / `2026-09-22` 호환성 검사**, 완료된 설정 파일럿, 수정된 새 비교를 구분합니다. 직접 Responses·고정 프롬프트 에이전트 v2의 HTTP 500은 이 환경의 실패이지 모델 전체의 미지원이 아닙니다. Agent는 **`gpt-4.1-mini` / `2025-04-14`**로 유지합니다.
- `gpt-6-luna` Judge는 **`lab-judge-luna-dea3cec5`**, **`gpt-5.5` / `2026-04-24`** 지시 생성 모델은 **`lab-planner-dea3cec5`**를 사용합니다. 생성 모델은 개선 대상 Agent나 Judge와 다른 역할입니다. `gpt-6-luna`는 [지원 최적화 모델 목록](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)에 없습니다.
- Agent Optimizer 접근과 후보 하나 설정을 확인합니다. 필수 역할이 미검증이면 지원을 확인한 것처럼 참가자에게 제출을 진행시키지 않습니다.
- [SDK 준비](admin-setup.md#sdk-prerequisites)를 마칩니다. 준비된 venv·`requirements.lock`, `az login` 계정·구독 확인, 운영자 프로젝트 endpoint·구독, 기준선 URL/Raw JSON의 ID가 필요합니다. helper·의존성이 없다고 다른 채점 방식으로 바꾸지 않습니다.

그림은 **영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님**을 안내합니다. 현재 참가자의 결과도 아니며 조작 위치를 설명하는 용도입니다. 현재 실측 상태는 검증 기록에서 확인합니다. 과거 그림이나 읽음 체크를 실행 증거로 바꾸지 않습니다.

**정식 영어 기준선 완료:** `contoso-en-learning-loop`는 고정 v1·같은 Judge에서 **12행, 10 passed / 2 failed / 0 errored, Relevance 10/12·이진 TaskAdherence 12/12**입니다. 이전 `contoso-en-baseline-luna-judge`는 **CONFIGURATION PILOT**으로 분리합니다. 실제 ID는 [03단계](handbook.md#baseline)에 있으며 파일럿 집계를 정식 비교에 섞지 않습니다.

**Optimizer 후보 하나로 성공:** `opt_e44bcf5701a348deb62a1cd4f9cb3910`, 같은 데이터셋·`gpt-5.5` 생성·`gpt-6-luna` Judge·모델 비교 없음입니다. **0.635 → 0.646**, **UI 표시 +0.010**, **보고 토큰 264,260**은 최적화 결과이지 최종 직접 비교가 아닙니다. Promote로 실습 v2를 만들고 후보 지시 일치·모델·지식 도구 불변을 검증했습니다.

**승격 경고:** 활성 버전 변경은 **모든 채널에 영향**이 있어 **격리된 미게시 실습만 허용하며 운영 환경에서는 금지**합니다. HOLD 후 활성 v1으로 복원했고 후보 v2는 남아 있습니다. “최신”을 활성과 같다고 추정하지 말고 명시적 버전·저장된 기준선을 사용합니다.

**네이티브 SDK 실행 검증, 채택 HOLD:** 후보 **`evalrun_f3b710fc835d444fb8aa0d2bb7797bdf`**, v2가 **`eval_94feef6f6f644fabb22a5680f5f24fb1`** 아래 **12행, 11 passed / 1 failed / 0 errored**로 완료됐고 v1은 **10 passed / 2 failed / 0 errored**였습니다. 데이터셋·평가자·Judge·모델·도구가 같고 지시·버전만 바뀌었습니다. Relevance 통과는 10/12→11/12지만 평균은 **4.4167→4.3333**, TaskAdherence는 양쪽 **12/12·이진 평균 1.0**입니다. 포털 **PairedTTest는 두 지표 모두 Inconclusive**이며 전반적 개선의 증거가 아닙니다.

관측 지연도 **p50 5,891.09→7,287.52 ms, p95 8,817.33→16,038.35 ms**로 증가했고 Agent 토큰은 **35,187→43,751**입니다. 추가 검토·새 대표 사례까지 고정 v1을 유지하며 Optimizer +0.010이나 통과 건수 증가만으로 성공을 주장하지 않습니다.

## 6단계 경로를 분명하게 유지 {#checkpoints}

| 참가자 단계 | 포털 조작과 정확한 선택 | 완료 신호 |
|---|---|---|
| [01 데이터셋](handbook.md#start) | 최신이 v1인 새 Agent에서 New experience → Build → Evaluations → Create, Pin currently latest, 해제된 대상 1개 재선택. Individual turns / One time / Existing dataset. 승격된 실제 영어 Agent는 기존 v1 기준선 읽기 | 고정 버전·데이터, n = 12·해시. 최신 v2를 기준선 v1로 혼동하지 않음 |
| [02 평가 기준](handbook.md#prepare) | query만 입력, custom override 없음. **Relevance 임계값 4 + TaskAdherence 이진 통과값 1**, 범용 TaskAdherence UI가 보이면 **Threshold 1**, 명시적 Judge | 두 기준의 서로 다른 척도·설정 기록 |
| [03 기준선](handbook.md#baseline) | 완료된 영어 **`contoso-en-learning-loop`**를 열고 재제출하지 않음. 한국어는 별도 준비 확인 | 파일럿과 구분된 영어 12행·정식 지표 결과 |
| [04 분석](handbook.md#analyze) | **Detailed metrics result**의 이유 확인. **conversation_id → User view**는 질문·JSON 응답이며 Judge 패널이 아님 | 실제 응답, Relevance.reason / TaskAdherence.reason, 정책 근거 연결 |
| [05 최적화](handbook.md#optimize) | 성공한 작업의 원본·후보·차이 읽기. 새 설정은 Custom only OFF → 내장 행 → Configure... → Apply, Relevance 4 / TaskAdherence 1 | 실제 후보 하나·검증된 실습 v2, 최신 활성 버전 경고 준수 |
| [06 비교](handbook.md#decision) | **`scripts/add_foundry_eval_run.py`**로 완료된 run의 receipt 재사용. **Evaluation runs → 두 체크박스 → Compare runs → Baseline 드롭다운: 원래 `contoso-eval-en`**, 처음 선택된 `candidate-v2` 제외 | 실행·상충 관계 검증, 두 지표 PairedTTest Inconclusive, 채택 HOLD·운영 승인 없음 |

데이터 미리 보기는 전체가 아니라 **처음 5행**만 보여 줍니다. 관측한 영어 마법사에서는 일치하는 스키마로 **Field mapping이 자동 해결**되어 **Configure agents → custom prompt override 미설정 → Criteria**로 이어졌습니다. 매핑 화면이 나타나면 **query → query**를 사용합니다. `context`·`ground_truth`를 생성 입력에 붙이지 않으며 승인된 프로젝트에 등록이 없는 경우에만 Upload new dataset을 사용합니다.

**제안 23개**의 나머지를 제거합니다. **Relevance는 1–5점·임계값 4**, **TaskAdherence는 Binary Pass/Fail·원시 0/1·통과값 1**이며 범용 UI가 보이면 **Threshold 1**을 사용합니다. [공식 정의](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators)가 이 차이를 명시합니다. 파일럿의 TaskAdherence Threshold 4에서도 `score=1`, `passed=true`가 반환됐으므로 그 범용 설정이 유효한 5점 루브릭을 만든 것은 아닙니다.

**`lab-judge-luna-dea3cec5`**를 사용합니다. 카탈로그에는 `relevance` **v14** / `task_adherence` **v17**이 보였지만 서비스의 **`evaluator_version`은 비어 있거나 기본값**이므로 비공개 루브릭 버전이 완전히 고정됐다고 가르치지 않습니다.

수정된 제출에서 **Relevance `response={{sample.output_text}}`**, **TaskAdherence `response={{sample.output_items}}`**를 확인했습니다. UI 기본값에는 `query={{item.query}}`, TaskAdherence의 `tool_definitions={{sample.tool_definitions}}`도 있었습니다. **Raw JSON**을 확인하고 **생성된 매핑을 TaskAdherence의 이전 UI output-text 값으로 덮어쓰지 않습니다**. 추가 데이터셋 필드나 생성 입력이 아닙니다.

새 기준선은 구성 변경 전에 **Pin currently latest**가 v1인지 확인하고 해제된 체크박스를 재선택합니다. 실제 후보는 이미 v2로 승격됐으므로 v1은 저장된 기준선 run에서 읽고 06단계 SDK는 명시적 버전 2를 사용합니다. `gpt-4.1-mini`의 Azure 사용 중단 예정일은 **2027-04-14**이며 공개 **Deprecated** 표시는 신규 구독을 제한할 수 있습니다.

**평가자 미지원이 아닌 Optimizer 필터:** Criteria의 **No custom evaluators available**에서는 **Custom only를 OFF**로 바꾸거나 **View built-in evaluators**를 누릅니다. 행 선택으로 **Configure...**를 열고 Relevance **4**, TaskAdherence **1**을 각각 **Apply**합니다. 직접 Evaluation의 Edit/Update와 다른 조작이며 사용자 정의 평가자가 필요하지 않습니다.

## 원하는 점수가 아니라 근거 토론 {#evaluation-sharing}

기준선 결과, Optimizer 지시 차이, 직접 재평가 뒤에 각각 몇 분씩 토론합니다. 이미 나온 결과를 읽는 시간이지 추가 제출 단계가 아닙니다.

| 토론 지점 | 요구할 근거 |
|---|---|
| 기준선 | run ID, **n = 12**, 지표별 채점 행/전체·통과 건수·누락·오류, 실패·최저점 사례와 존재한다면 좋은 사례 |
| 후보 | 실제 job/candidate ID, 원본·후보의 평가자별 결과, 바뀐 지시와 가능한 회귀 |
| 재평가 | 같은 정의 아래 새 직접 run ID, 동일 데이터·버전·해시·기록한 평가자·Judge 설정, 같은 사례의 실제 전후 답변·이유와 루브릭 버전 한계 |

아래 빈 형식을 토론에 사용합니다.

> “수정된 실행 ___에서 지표 ___의 척도는 ___, 통과 규칙은 ___입니다(Relevance ≥4, TaskAdherence =1). 12건 중 ___건 채점·___건 통과·누락/오류 ___건이며 실제 답변 ___는 정책 ___와 ___ 때문에 일치·불일치합니다. 다음 결정은 ___입니다.”

실패나 좋은 사례가 없으면 그 관측을 그대로 보고합니다. 사례를 만들거나 기준선을 약화하거나 그림의 수치를 복사하거나 반드시 개선된 후보를 요구하지 않습니다.

## 지표가 증명하지 않는 것 설명 {#interpret-results}

<a id="review"></a>

**Completed는 품질 통과가 아닙니다.** Relevance의 **1–5점은 백분율 정확도가 아닙니다**. TaskAdherence는 5점 척도가 아닌 **이진 0/1**이며 1은 Pass, 0은 Fail입니다. 누락·오류를 채점된 0으로 바꾸지 않고 지표별 올바른 형식·건수·범위·이유를 보고합니다.

Relevance는 질문을 다루는 응답인지, TaskAdherence는 에이전트의 과제 지시·제약을 따르는지 평가합니다. 어느 쪽도 모든 정책·인용·권한 경계·안전 속성을 인증하지 않습니다. 일부 평가자는 참고 열을 쓰지 않더라도 참가자는 실제 답변·이유를 원래 정책·참고 답변과 대조합니다.

이 애플리케이션에는 정책 발효일 경계, 필요한 추가 질문, 근거 없는 승인 주장, 제한 요청의 안전한 처리가 중요합니다. 실제 행 하나로 공개 벤치마크가 이런 도메인 판단을 대신하지 못하는 이유를 설명합니다.

**정식 v1 기준선의 Relevance 실패:** `atlas-dev-001`은 구독 축소 안내가 모호했고 참고는 명시적 추가 확인을 요구했습니다. `atlas-dev-011`은 미확인 기능을 정직하게 설명했지만 불완전하다고 판단됐습니다. TaskAdherence는 둘 다 통과했으며 이는 후보 회귀 결과가 아닙니다. 점수 때문에 정책 사실·정당한 불확실성을 바꾸지 않습니다.

화면 19는 `atlas-dev-001`의 **conversation_id → User view**로 질문과 실제 JSON 응답을 보여 주며 **인라인 Judge 이유 패널이 아닙니다**. **Detailed metrics result**로 돌아가 **`Relevance.reason` / `TaskAdherence.reason`**을 참고 정책과 대조합니다. 실제 run에 없는 인용문·이유를 만들지 않습니다.

모델·도구·언어·12문항·데이터 버전·해시·**Relevance 4 / TaskAdherence 이진 통과값 1**·Judge를 유지합니다. SDK helper는 기준선 `data_source`·기존 기준을 재사용하고 대상 버전만 바꾸며 모델·도구를 검증해 같은 evalID에 실제 Foundry run을 제출합니다. 동일 명령·receipt 경로 반복은 재제출이 아닌 안전한 수집입니다. 별도 클라우드 채점이나 새 정의가 아닙니다.

포털 **Add run**에서 Pin v2 / Individual turns 뒤 **Configure agents → Config required → Add custom prompt / User prompt**가 나타났고 `{{item.query}}`에도 **`Unable to create data source configuration from item schema`** 클라이언트 오류가 발생했습니다. **이 시도로 원격 후보 run은 제출되지 않았습니다.** 새 정의·작성 점수로 우회하지 말고 SDK를 사용합니다. 비공개 서비스 루브릭 버전 고정도 여전히 입증되지 않았습니다.

**관측 행별 변화:** Relevance 행 1은 **3→4**, 행 2·6은 **5→4**, 정직한 불확실성을 유지한 행 11은 **3**입니다. 평균이 내려가도 임계값을 넘은 행 때문에 통과 건수는 늘 수 있습니다. Relevance·TaskAdherence **PairedTTest: Inconclusive**는 개선이나 동등성의 증명이 아닙니다. 재사용 dev12는 통계적 유의성·독립적인 일반화·운영 승인이 아닙니다.

## 실험 조건을 바꾸지 않고 복구 {#resume}

먼저 기존 run/job과 정확한 입력을 확인합니다. 제출 상태가 불명확하면 새로 만들지 말고 운영자와 기존 요청을 찾습니다. 실패와 누락 행을 계속 드러냅니다.

| 증상 | 안전한 대응 |
|---|---|
| 다른 계정·프로젝트, 401/403, 네트워크 제한 | 운영자가 신원과 승인된 접근을 확인. 공유 권한 확대나 제한 우회 금지 |
| 카탈로그 모델은 보이지만 런타임·평가자 실패 | 역할·배포·오류·request/run ID 기록. 카탈로그 표시가 런타임 증거는 아님 |
| `gpt-6-luna` Responses·고정 Agent v2 HTTP 500 | 해당 런타임은 이 환경에서 미검증으로 두고 Agent는 검증된 `gpt-4.1-mini` 유지. 별도 네이티브 Relevance Judge 호환성 결과를 부정하거나 모델 전체가 미지원이라고 하지 않음 |
| 업로드 미리 보기에 5행만 표시 | 변경 없는 로컬 파일이 12행이며 올바른 등록 데이터셋인지 확인 |
| 스키마·입력 불일치 | 정확한 세 열 파일 사용. `ground_truth`는 JSON 문자열, Agent 입력은 `query`만 |
| 버전 고정 후 대상 선택이 사라짐 | 해당 행 체크박스가 해제됨. 다시 선택하고 Next 전에 대상 1개 확인 |
| UI와 제출된 TaskAdherence 매핑이 다름 | 생성된 `sample.output_items` 연결을 유지하고 Raw JSON 확인. `sample.output_text`로 덮어쓰지 않음 |
| Compare runs 비활성화 | 같은 정의의 Evaluation runs에서 기준선·후보 두 행 선택. 결과 해석은 완료 후 수행 |
| 비교 방향이 반대로 보임 | Baseline 기본값은 처음 선택된 행이며 여기서는 candidate-v2였음. 차이·검정을 읽기 전에 Baseline 드롭다운에서 원래 contoso-eval-en 명시 선택 |
| 부분 평가·점수 누락 | n = 12와 채점·누락·오류 건수를 보고. 행 제거·이유 생성 금지 |
| Optimizer Max candidates 비활성화 | Model 해제, Instruction only 선택, Tool description 끄기, Max candidates 1 |
| Optimizer Criteria의 No custom evaluators available | Custom only OFF 또는 View built-in evaluators → 행 선택 → Configure... → Relevance 4 / TaskAdherence 1 → Apply |
| 포털 후보 Submit의 item-schema 오류 | 실패한 폼은 원격 run을 만들지 않음. 단일 SDK 명령 사용, 새 정의로 우회 금지 |
| SDK receipt가 있거나 run이 처리 중 | 같은 `.lab/foundry-evaluations/candidate-v2.json`과 동일 명령으로 수집. 새 제출을 강제하려고 receipt 삭제·변경 금지 |
| SDK 신원·모델·도구 검증 실패 | 운영자 환경을 확인하고 중단. 검증 우회·모델 교체·로컬 Judge 점수 대체 금지 |
| 첫 Optimizer 화면에 세금 에이전트 벤치마크 | Contoso 결과가 아닌 제품 예시라고 표시. Optimize my agent → Agent 사용 |
| 최적화 60분 초과 | 실제 작업 상태를 남기고 대기·추가 제출 중단. 이후 확인·남은 비용은 운영자가 담당 |
| 후보가 모델·도구를 변경하거나 평가 계약이 다름 | 지시만 바꾼 개선이라고 주장하지 않고 불일치 기록, 기준선 유지 |
| Optimizer·재평가 차단 | 미실행으로 기록. 다른 기능·수작업 후보·유리한 반복 실행으로 대체하지 않음 |

## 흔한 오해 바로잡기 {#misconceptions}

| 주장 | 설명 |
|---|---|
| “업로드나 Review가 성공했으니 평가도 완료죠.” | 준비는 제출이 아님. 실제 evaluation/run ID와 최종 결과가 필요 |
| “Relevance 4/5점은 정확도 80%죠.” | Relevance의 순서형 점수이며 정확도 추정치가 아님 |
| “TaskAdherence 1이면 5점 중 1점이라 나쁜 답이죠.” | 아님. **이진 Pass = 1**이며 5점 척도나 임계값 4를 적용하지 않음 |
| “세 역할은 전부 같은 모델이어야 하죠.” | 런타임·Judge·지시 생성 모델의 지원 조건은 서로 다름 |
| “후보 순위가 높으니 운영에 승격하죠.” | 금지. 최신 활성 버전은 모든 채널에 영향이 있어 격리된 미게시 실습에서만 승격. 직접 평가·운영 승인은 별개 |
| “개선이 없으니 계속 돌려야겠죠.” | 개선 없음으로 보고하고 기준선 유지. 유리할 때까지 반복하지 않음 |
| “영어 그림이 있으니 한국어 경로도 실행됐죠.” | UI 설명일 뿐. 언어별 실행에는 별도 실제 근거가 필요 |
| “비공개 도메인 평가 수업이니 고객 데이터도 쓴 거죠.” | Contoso는 합성 자료. 실제 회사 자료는 별도 승인·개인정보 보호·대표성 검토가 필요 |

## 정직한 결과로 종료 {#finish}

<a id="next-loop"></a>

공유하는 평가 정의 ID, 서로 다른 기준선·후보 run ID, optimization job/candidate ID, 고정 Agent 버전·모델 역할, 데이터셋 버전·해시, 기록한 기준·설정·서비스 버전 한계, 지표별 비교, 사례 설명, 회귀, 결정을 요청합니다. 진행 중·실패·미실행은 명시적으로 미완료 상태로 남깁니다.

**최종 실습 결정: 채택 HOLD, 고정 기준선 v1 유지.** 통과 건수는 늘었지만 Relevance 평균·행별 점수가 하락하고 지연·토큰 사용량이 증가했으며 두 지표의 PairedTTest도 Inconclusive입니다. 추가 검토·새 대표 사례는 다음 승인된 주기로 남기며 필수 실습을 늘리거나 유리할 때까지 반복하지 않습니다. 통계적 유의성·운영 승인을 주장하지 않습니다.

**HOLD를 실행했습니다:** Compare에서 원래 Baseline을 명시 선택한 뒤 운영자가 **Details → Agent configuration → Active version → Edit → Version 1**로 활성 v1을 복원했습니다. 후보 v2·두 평가 run·receipt는 삭제하지 않습니다. 운영용 Publish나 운영 채널·트래픽 구성은 없지만 **RBAC-only Responses/preview endpoints는 Publish 없이 자동 제공**됩니다. 미게시를 endpoint 없음으로 가르치지 않습니다.

비용·정리 담당자와 남은 차단 사유를 정합니다. 승인된 합성 예시와 가림 처리한 요약만 공유합니다. 이후 회사 보유 데이터 평가를 하려면 별도로 사용 승인을 받고 대표 업무와 알려진 실패를 선정합니다. 이 12문항 실습으로 운영을 인증했다고 주장하지 않습니다.
