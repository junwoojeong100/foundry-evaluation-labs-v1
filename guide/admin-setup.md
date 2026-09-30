# 운영자 사전 준비 · 격리된 NCUS 워크숍 {#operator-guide}

[참가자 경로](handbook.md#start) · [강사 안내](facilitator.md#prepare) · [실측 검증](verification.md)

참가자가 시작하기 **전에** 프로젝트와 예제 에이전트를 준비합니다. 참가자 경로는 데이터셋 준비, 관리형 Evaluation, 실패 분석, 지시 전용 Agent Optimizer, 동일 조건 재평가이며 인프라 배포가 아닙니다.

## 준비된 실습 환경에서 시작 {#start}

운영자는 이번 리허설을 위해 **새로운 격리된 North Central US(NCUS) 리소스 그룹**을 준비했습니다. 실제 대상·소유·준비 상태는 비공개 준비 근거로 확인합니다. 문서가 바뀌었다고 다시 만들거나 공유 운영 환경을 사용하지 않습니다.

**리소스 존재**, **의도한 런타임 동작**, **허용 가능한 업무 품질**을 구분합니다. 배포 성공은 Agent 실행이나 관리형 평가자 지원을 증명하지 않습니다. 준비·실행 실측 결과는 화면의 상태를 복사하지 말고 [검증 기록](verification.md)에 남깁니다.

<figure class="portal-shot" id="portal-resource-group">
<img src="../web/assets/portal/en/00-resource-group.png" alt="영어 리허설용 신규 전용 리소스 그룹의 자원과 배포 상태. 한국어 실행 결과가 아님" width="1600" height="1000" loading="lazy">
<figcaption><strong>준비된 리소스 그룹.</strong> 영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님. Failed 건수에는 로그 대상을 찾지 못한 별도 조직 정책 배포 실패가 포함됩니다. 숨기거나 워크숍에서 공유 정책을 고치거나 실습 배포 상태와 혼동하지 않습니다. <a href="../web/assets/portal/en/00-resource-group.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

## 세 모델 역할을 별도로 검증 {#prepare}

승인된 프로젝트를 확인한 뒤 배포 선택 필드에는 모델 계열 이름이 아닌 **아래 실제 배포 이름**을 사용합니다. 별도 영어 기준선 **`contoso-eval-en` 버전 `1`**이 실제 동작하며 기존 **읽기 전용 지식 연결을 유지**한 상태입니다. 전후 비교 동안 역할 배치를 바꾸지 않습니다.

| 역할 | 필요한 결정 |
|---|---|
| Agent 런타임 | **`lab-agent-dea3cec5` → `gpt-4.1-mini` / `2025-04-14`**, **`contoso-eval-en` v1**에서 실제 동작 확인. 읽기 전용 지식 연결 유지. `gpt-6-luna` Responses·Agent 검증은 이 환경에서 실패 |
| 평가 Judge | **`lab-judge-luna-dea3cec5` → `gpt-6-luna` / `2026-09-22`**. 실제 관리형 기준선·후보 평가에서 사용 확인 |
| Optimizer 지시 생성 모델 | **`lab-planner-dea3cec5` → `gpt-5.5` / `2026-04-24`**. [공식 최적화 모델 목록](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)에는 `gpt-6-luna`가 **없음** |

**관측한 기능 호환성 근거:** `gpt-6-luna` 버전 `2026-09-22`는 NCUS의 **GlobalStandard**에서 GA입니다. 신규 배포 이름은 `lab-agent-luna-dea3cec5`, `lab-judge-luna-dea3cec5`이며 Chat Completions는 **READY**를 반환했습니다. 실제 네이티브 Foundry **Relevance** 평가가 **작성된 호환성 fixture 한 건에서 passed 1 / total 1 / errors 0**으로 완료되었습니다. evaluation ID는 `eval_589a069bfd8343cf980b4b88f57771e8`, run ID는 `evalrun_e662077a904543d6bd1420b202a1b078`입니다.

이 앞선 기록은 Judge 기능 호환성이지 **Agent 품질** 검증이 아닙니다. 아래 설정 파일럿 및 수정된 비교와 별개이므로 건수·ID를 합치지 않습니다.

**런타임 한계:** 직접 Responses 호출과 **명시적으로 고정한 `gpt-6-luna` 프롬프트 에이전트 v2**는 모두 **이 환경에서 HTTP 500**을 반환했습니다. 모델 전체가 미지원이라고 주장하지 않습니다. 여기서 런타임 검증이 실패한 것이므로 공급자 문제가 해결될 때까지 검증된 `gpt-4.1-mini` 에이전트를 유지하며 실험용 에이전트로 조용히 바꾸지 않습니다.

`gpt-4.1-mini` / `2025-04-14`의 Azure 사용 중단 예정일은 **2027-04-14**입니다. 공개 문서의 **Deprecated** 표시는 신규 구독의 사용을 제한할 수 있으나 기존 배포에서 관측한 사용 가능성을 없애는 것은 아닙니다. 모든 신규 구독에 접근을 약속하지 말고 인수 전에 실제 계정과 기존 배포를 확인합니다.

사용자 요청은 세 역할의 지원 범위가 다를 수 있음을 전제로 **지원되는 곳에서** `gpt-6-luna`를 사용하는 것입니다. 카탈로그 표시·배포 성공·채팅 응답이 모든 API와 런타임을 검증하지는 않습니다. 기준선 이후 역할을 조용히 바꾸거나 모델 교체 효과를 지시만 바꾼 개선으로 보고하지 않습니다.

최적화 모델은 **후보 지시를 작성**합니다. 개선 대상 에이전트 모델, 응답을 채점하는 Judge와 다른 역할입니다. 직접 Evaluation·Optimizer 평가·직접 재평가에는 동일한 검증 Judge를 사용합니다.

<figure class="portal-shot" id="portal-models">
<img src="../web/assets/portal/en/02-model-deployments.png" alt="리허설의 역할별 배포 이름과 모델 버전을 보여 주는 Foundry 배포 목록. 한국어 실행 결과가 아님" width="1271" height="820" loading="lazy">
<figcaption><strong>배포 목록은 역할 입력이지 런타임 증거가 아닙니다.</strong> 영문 UI·영문 데이터 리허설 화면; 한국어 실행 결과가 아님. 모델 버전·배포 이름을 비공개 인수 자료와 대조합니다. 목록만으로 Agent·Responses·평가자·Optimizer 호환성을 확인할 수 없습니다. <a href="../web/assets/portal/en/02-model-deployments.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

## 프로젝트와 예제 에이전트 준비 {#bootstrap}

공식 [직접 에이전트 평가 사전 요구 사항](https://learn.microsoft.com/azure/foundry/observability/how-to/evaluate-agent#prerequisites)과 [프롬프트 에이전트 Optimizer 사전 요구 사항](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent#prerequisites)을 따릅니다. 지원되는 프로젝트·에이전트·모델·접근 조건을 확인하며 참가자에게 기존 전체 bootstrap 절차를 필수로 실행하게 하지 않습니다.

| 준비 항목 | 인수 전에 필요한 근거 |
|---|---|
| 의도한 계정·프로젝트 | 실제 로그인 테넌트·계정, 구독, 리소스 그룹, 프로젝트가 승인된 실습 범위와 일치. 포털과 운영자가 사용하는 CLI·SDK 신원은 각각 확인 |
| 준비된 Contoso 에이전트 | 영어는 **`lab-agent-dea3cec5`**의 기존 **`contoso-eval-en` 버전 `1`**, 읽기 전용 지식 연결 유지. 한국어는 **`contoso-eval-ko` v1**과 한국어 네 키 응답 계약의 운영자 준비를 별도 확인 |
| 런타임 | 의도한 런타임에서 고정 에이전트가 반환한 실제 응답. 모델 채팅 smoke로 대체하지 않음 |
| 관리형 Evaluation | **`contoso-en-learning-loop`**가 **Completed**: 12행, 전체 통과 10·실패 2·오류 0, Relevance 10/12·이진 TaskAdherence 12/12. 파일럿과 분리 |
| Agent Optimizer | Optimize Preview 접근, Instruction-only 대상, Max candidates 1, **`lab-planner-dea3cec5`**, 동일 Judge **`lab-judge-luna-dea3cec5`** |
| 데이터셋 | 영어 **`contoso-eval-en-dev12` 버전 `1`**은 변경 없는 `data/en/optimizer/dev.jsonl` 12행으로 등록됨. 한국어는 `data/optimizer/dev.jsonl`의 **`contoso-eval-ko-dev12`** 등록·버전·SHA-256을 별도 확인 |

정책 접근은 수업 전에 구성한 뒤 그대로 유지합니다. 참가자가 더 좋은 점수를 얻으려고 별도 지식 시스템을 구축하거나 인프라를 고치지 않습니다. 에이전트에 필요한 근거가 없다면 참고 답변을 입력에 붙이지 말고 준비 차단 사유로 보고합니다.

아직 v1인 새 기준선은 **Pin currently latest** 뒤 해제된 체크박스를 재선택하고 **Next 전에 대상 1개**를 확인합니다. 실제 Agent는 후보 v2를 유지하되 **활성 버전을 1로 복원**했습니다. “최신”과 활성을 같다고 보지 말고 명시적 버전·저장된 평가 ID를 사용합니다. 실패한 `gpt-6-luna` v2는 다른 Agent입니다.

영어 파일럿에서는 스키마가 맞는 **Existing dataset** 선택 후 **Field mapping이 자동 해결**되어 **Configure agents → custom prompt override 미설정 → Criteria**로 이어졌습니다. 수정된 실행에서는 제안 23개의 나머지를 제거하고 정확히 **Relevance Threshold 4**, **TaskAdherence 이진 통과값 1**(범용 UI가 보이면 **Threshold 1**)을 사용합니다.

[공식 에이전트 평가자 정의](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators)는 TaskAdherence를 1–5점이 아닌 **Binary Pass/Fail, 원시값 0/1**로 명시합니다. 파일럿 UI는 TaskAdherence Threshold 4를 허용했지만 실제 `score=1`이 `passed=true`로 반환되어 그 범용 설정은 의미가 없었습니다. 과거 정의를 고쳐 쓰지 말고 파일럿을 유지한 채 수정된 새 비교를 시작합니다.

영어는 `contoso-eval-en`과 영어 데이터, 한국어는 운영자가 준비하는 **`contoso-eval-ko` v1**, `data/optimizer/dev.jsonl`, `contoso-eval-ko-dev12`, 한국어 응답 계약을 사용합니다. **이번 리허설에서 한국어를 재실행하지 않았으며 새로운 한국어 실측 결과나 등록 완료를 주장하지 않습니다.** 영어 근거를 바꾸어 표시하지 말고 한국어 준비를 따로 확인합니다.

**보존된 CONFIGURATION PILOT(설정 파일럿) — 포털 실행이며 수정된 기준선이 아님:**

| 기록 항목 | 값 |
|---|---|
| 파일럿 Evaluation name | `contoso-en-baseline-luna-judge` |
| 파일럿 평가 정의 ID | `eval_06d9c6cb93df4c7bad2bc3a62da9bc90` |
| 파일럿 run ID | `evalrun_98ac1b10a98d4ebe9d72bed5c66ed0f2` |
| 입력 | `contoso-eval-en` 고정 v1, `contoso-eval-en-dev12` 버전 1, 전체 12문항 |
| 파일럿 설정 문제 | Relevance 임계값 4. TaskAdherence의 범용 임계값 4는 **이진 결과에 유효하지 않았음**. Judge: `lab-judge-luna-dea3cec5` / `gpt-6-luna` |
| 보고된 상태 | **Completed, 출력 항목 12개** |
| 파일럿 Agent 사용량 | **12회 호출**, `gpt-4.1-mini`의 고정 `contoso-eval-en` v1 |
| 파일럿 서비스 보고 Judge 사용량 | **`gpt-6-luna-2026-09-22` 24회 호출, 83,492토큰**. 수정된 비교 사용량이 아님 |

**완료된 정식 영어 기준선 — 포털, 아래에서 SDK 후보 실행도 검증됨:**

| 기록 항목 | 값 |
|---|---|
| 수정된 Evaluation name | **`contoso-en-learning-loop`** |
| 수정된 evaluation ID | `eval_94feef6f6f644fabb22a5680f5f24fb1` |
| 수정된 기준선 run ID | `evalrun_cde9948ac9d946929661bc3d9e60432a` |
| 입력 | `contoso-eval-en` 고정 v1, `contoso-eval-en-dev12` 버전 1, 같은 12문항 |
| 기준·Judge | Relevance 임계값 4, TaskAdherence 이진 임계값·통과값 1, `lab-judge-luna-dea3cec5` / `gpt-6-luna` |
| 확인된 응답 연결 | Relevance `response={{sample.output_text}}`, TaskAdherence `response={{sample.output_items}}` |
| 실행·전체 | **Completed, 12행, 10 passed / 2 failed / 0 errored** |
| 평가자별 결과 | **Relevance 10/12**, 임계값 4. **TaskAdherence 12/12**, 이진값 1 |
| Relevance 실패 | `atlas-dev-001`: 구독 축소 답변이 모호하며 참고는 명시적 추가 확인 요구. `atlas-dev-011`: 정직한 미확인 기능 답변을 불완전하다고 판단 |
| 근거의 경계 | HTTP 201 제출 이후 완료를 별도 확인한 기준선 결과. 후보 결과가 아니며 점수 때문에 정책 사실을 바꾸지 않음 |

기준선은 **Evaluation name → Submit**으로 제출됐습니다. 같은 정의의 후보 **Add run**은 끝까지 동작하지 않았습니다. Pin v2 / Individual turns 뒤 **Configure agents: Config required → Add custom prompt / User prompt**가 나타났고 `{{item.query}}`를 넣어도 **`Unable to create data source configuration from item schema`** 클라이언트 오류가 났습니다. **이 포털 시도로 원격 후보 run은 제출되지 않았습니다.** 새 정의를 만들어 우회하지 않습니다.

**Optimizer는 후보 하나로 성공했습니다:** `opt_e44bcf5701a348deb62a1cd4f9cb3910`, 지시 전용, 같은 데이터셋, `gpt-5.5` 생성, `gpt-6-luna` Judge, 모델 비교 없음입니다. UI 점수 **0.635 → 0.646**, **UI 표시 변화 +0.010**, **보고 토큰 264,260**을 그대로 기록합니다. 표시값으로 다른 변화량을 산출하지 않으며 직접 후보 평가 결과와 구분합니다.

**포털 Promote로 실습 전용 `contoso-eval-en` v2가 생성됐습니다.** 운영자가 후보 지시의 정확한 일치와 모델·지식 도구 불변을 검증했습니다. **최신 활성 버전은 모든 채널에 영향을 주므로 격리된 미게시 실습 Agent에서만 승격하며 운영 환경에서는 절대 사용하지 않습니다.** v1은 명시적 기준선으로 남고 승격을 반복하거나 운영 승인으로 해석하지 않습니다.

Optimizer **Criteria**의 **No custom evaluators available**은 필터 상태입니다. **Custom only를 OFF**로 바꾸거나 **View built-in evaluators**를 누릅니다. Relevance·TaskAdherence 행 선택으로 **Configure...**를 열어 **Relevance 4 / TaskAdherence 1**을 설정하고 **Apply**합니다. 우회용 사용자 정의 평가자를 추가하지 않습니다.

<a id="sdk-prerequisites"></a>

**단일 SDK 단계의 사전 준비:** Python 3.11 이상(3.12 권장), Azure CLI, 운영자가 제공하는 `scripts/add_foundry_eval_run.py`, 현재 `requirements.lock`을 준비합니다. 저장소 루트에서 모델 배포 주소로 추측하지 말고 승인된 **프로젝트 endpoint·구독**을 사용합니다.

```bash
export AZURE_AI_PROJECT_ENDPOINT="OPERATOR_PROJECT_ENDPOINT"
export AZURE_SUBSCRIPTION_ID="OPERATOR_SUBSCRIPTION_ID"
```

`.venv`가 없을 때만 `python3 -m venv .venv`로 한 번 준비합니다. 고정 환경을 활성화·설치하고 실제 계정을 확인합니다.

```bash
source .venv/bin/activate
python -m pip install -r requirements.lock
az login
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
az account show --query "{user:user.name,tenant:tenantId,subscription:id}" -o json
```

사용자·테넌트·구독을 운영자 승인 및 포털 신원과 대조하며 다른 캐시 계정으로 진행하지 않습니다. 이 확인은 역할 할당이 아닙니다. `FOUNDRY_EVALUATION_ID`·`FOUNDRY_BASELINE_RUN_ID`는 정식 기준선 포털 URL 또는 **Raw JSON**에서 복사합니다. 위 실제 영어 ID 또는 해당 한국어 기준선 ID를 사용하며 파일럿·Optimizer job ID와 혼동하지 않습니다.

[06단계의 단일 명령](handbook.md#decision)은 Azure AI Projects/OpenAI Evals SDK로 기준선 `data_source`·기존 기준을 재사용하고 대상 버전만 2로 바꿉니다. 동일한 모델·도구를 확인하며 **같은 evalID 아래 실제 Foundry run 하나**를 제출합니다. 로컬 Judge나 별도 클라우드 채점 구현이 아닙니다. 비공개 `.lab/foundry-evaluations/candidate-v2.json` receipt를 유지하고 동일 명령을 반복해 같은 run을 수집합니다. 재시도하려고 receipt·이름·경로·정의를 바꾸지 않습니다.

**실제 끝까지 검증된 영어 SDK 실행:** helper가 **동일한 `eval_94feef6f6f644fabb22a5680f5f24fb1`** 아래 **`contoso-eval-en` v2**의 후보 run **`evalrun_f3b710fc835d444fb8aa0d2bb7797bdf`**를 제출했습니다. **Completed, 12행, 11 passed / 1 failed / 0 errored**이며 기준선은 **10 passed / 2 failed / 0 errored**였습니다. 같은 데이터셋·평가자·Judge·모델·도구를 helper가 확인했고 지시·버전만 바뀌었습니다.

receipt를 재사용하고 **`contoso-en-learning-loop` → Evaluation runs → 두 run 체크박스 → Compare runs**를 엽니다. **Baseline 드롭다운은 원래 `contoso-eval-en`으로 지정합니다.** 기본값이 처음 선택한 행이며 실제로 `candidate-v2`였으므로 방향을 먼저 확인합니다. 포털 item-schema 실패는 그대로이며 후보 run은 SDK로 완료됐습니다.

| 최종 관측 비교, n = 12 | 기준선 v1 | 후보 v2 |
|---|---|---|
| 전체 기준 통과; 오류 | 10/12; 0 | 11/12; 0 |
| Relevance 통과; 평균(1–5) | 10/12; 4.4167 | 11/12; 4.3333 |
| TaskAdherence 통과; 이진 평균 | 12/12; 1.0 | 12/12; 1.0 |
| Relevance 행 1 / 2 / 6 / 11 | 3 / 5 / 5 / 3 | 4 / 4 / 4 / 3 |
| 지연 p50 (ms) | 5,891.09 | 7,287.52 |
| 지연 p95 (ms) | 8,817.33 | 16,038.35 |
| Agent 토큰 | 35,187 | 43,751 |

네이티브 **PairedTTest는 Relevance·TaskAdherence 모두 Inconclusive**입니다. 행 1은 통과 임계값을 넘었지만 행 2·6은 하락했고 행 11은 근거 없는 확답 대신 정직한 불확실성을 유지하며 3입니다. 점수 때문에 정책 사실을 바꾸지 않습니다. **채택 HOLD, 추가 검토·새 대표 사례까지 고정 v1 유지**입니다. 통과 건수 증가만으로 평균 하락·지연·토큰 상충 관계를 상쇄하거나 전반적 개선을 입증하지 못하며 운영 승인은 없습니다.

## 실제 워크숍 범위 제한 {#scope}

<a id="approval"></a>

**실제 계정·프로젝트·데이터·처리 위치·비용**의 현재 승인 범위를 정합니다. 다른 리허설의 승인이 그대로 적용되는 것은 아닙니다. GlobalStandard는 처리 방식이며 모든 요청이 NCUS 안에서만 처리된다는 약속이 아닙니다.

| 작업 | 범위 |
|---|---|
| 기준선 | 전체 12건의 올바르게 설정한 직접 관리형 평가 한 번. 보존된 파일럿은 이 기준선이 아님 |
| 최적화 | 지시 전용 작업 한 번, **Max candidates 1**, **최대 60분** 대기 |
| 후보 확인 | SDK로 **같은 evalID**에 실제 Foundry run 하나 제출. 같은 데이터·버전·해시·Relevance 4·TaskAdherence 이진 통과값 1·Judge, receipt 재수집과 포털 비교 |
| 에이전트 변경 | 실습 v2만 사용. 최신 활성 버전은 모든 채널에 영향. 격리된 미게시 Agent에서만 승격하며 운영 환경 금지 |
| 추가 기능 | 검증되지 않은 기능은 실행하지 않으며 다른 실습으로 완료를 대체하지 않음 |

준비 검사의 사용량도 별도 승인 범위이며 Optimizer 작업 하나에서 여러 내부 호출이 발생할 수 있습니다. 오류가 났다고 작업을 반복하거나 범위·리전을 바꾸거나 유리한 결과가 나올 때까지 실행하지 않습니다.

## 신원과 최소 권한 확인 {#rbac}

현재 [Foundry RBAC 안내](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry)를 실제 작업과 대조합니다. 역할 할당 권한과 에이전트 실행 권한은 별개입니다.

| 주체 | 적절한 최소 실습 범위에서 확인할 접근 |
|---|---|
| 참가자·운영자 | 프로젝트 열기, 고정 에이전트 읽기, 데이터셋 업로드·선택, 평가 생성·읽기, Agent Optimizer 사용 |
| 프로젝트 관리 ID | 필요한 모델 및 기존 도구·연결 접근 |
| 지원 서비스 ID | 준비된 에이전트의 실제 연결에 필요한 접근만 |
| 실습 관리 운영자 | 승인된 버전 생성, 자원·비용 조회, 별도 승인된 수명주기 작업 |

편의를 위해 참가자에게 구독 전체 Owner를 주거나 자격 증명을 노출하거나 조직 정책을 바꾸거나 네트워크 제한을 우회하지 않습니다. 포털 탭의 계정 표시만으로 다른 클라이언트의 신원도 같다고 단정하지 않습니다.

## 비용과 종료 책임 {#cost}

에이전트 응답, Judge 평가, 지시 생성, Optimizer 내부 호출, 정책 도구, 지속 실행되는 지원 자원·로그의 비용을 포함합니다. **미확인 비용은 0원이 아니며**, quota는 무료 할당이 아니고 브라우저를 닫아도 호스팅 과금이 멈추지 않습니다.

남은 작업·비용 확인·승인된 실습 자원 정리의 책임 운영자를 정합니다. 자원 삭제나 광범위한 계정 변경을 참가자 실습으로 만들지 않습니다. 자격 증명·비공개 설정·원본 계정 식별자는 공유 문서와 패키지에 넣지 않습니다.

## 참가자가 사용할 계약 인수 {#handoff}

| 전달할 항목 | 필요한 구체성 |
|---|---|
| 포털 대상 | 올바른 프로젝트와 한국어 **`contoso-eval-ko`**의 별도 준비 확인. 실제 영어 대상은 **`contoso-eval-en`** |
| Agent 버전 | **활성 v1 복원**, 기록된 기준선 v1·보존된 후보 v2. **`lab-agent-dea3cec5`**, `gpt-4.1-mini` / `2025-04-14`, 명시적 버전·근거 유지 |
| 모델 역할 | Agent **`lab-agent-dea3cec5`**, Judge **`lab-judge-luna-dea3cec5`**, Optimizer **`lab-planner-dea3cec5`**, 각 버전과 지원 한계 |
| 데이터셋 | 영어 **`contoso-eval-en-dev12` 버전 `1`** 등록 확인. 한국어는 **`contoso-eval-ko-dev12`** 별도 확인. 각 원본 파일, n = 12, SHA-256 |
| 평가 계약 | 같은 수정된 정의, **Relevance 1–5점·임계값 4 / TaskAdherence 이진 0/1·통과값 1**, 범용 TaskAdherence Threshold가 보이면 1. query 전용 입력, custom override 없음 |
| 범위·책임 | 승인 범위, 후보 하나, 최적화 대기 60분, 비용·정리 책임자, 차단 시 연락 대상 |
| SDK 준비 | 검증된 venv·의존성·`az login` 계정, 운영자 프로젝트 endpoint·구독, 기준선 URL/Raw JSON ID, helper와 고정 receipt 경로 |
| 근거 | 완료된 기준선·SDK 후보, 입력 일치, 최종 지표·행별 회귀·PairedTTest Inconclusive. 추가 검토·새 대표 사례까지 채택 HOLD, 파일럿 제외 |

**생성된 매핑을 기록하되 덮어쓰지 않습니다.** 수정된 제출에서 **Relevance `response={{sample.output_text}}`**, **TaskAdherence `response={{sample.output_items}}`**를 확인했습니다. UI 기본값에는 `query={{item.query}}`, TaskAdherence의 `tool_definitions={{sample.tool_definitions}}`도 있었습니다. **Raw JSON**을 확인하되 TaskAdherence를 이전 UI의 output-text 값으로 바꾸지 않습니다. 추가 데이터셋 열도 아닙니다.

**버전 한계:** 카탈로그 링크에는 `relevance` **v14**, `task_adherence` **v17**이 보였지만 실제 서비스 기준의 **`evaluator_version`은 비어 있거나 기본값**이었습니다. 이름·설정, Judge·데이터셋 버전과 이 한계를 기록합니다. 같은 정의를 재사용해도 비공개 서비스 루브릭 버전이 완전히 고정됐다는 증거는 아닙니다.

**실행은 성공했지만 채택은 HOLD입니다.** 두 run·receipt·측정된 상충 관계를 유지하고 선택 기준선은 고정 v1으로 둡니다. 실습 v2 활성화는 모든 채널에 영향을 주는 별도 운영자 문제입니다. Optimizer +0.010·네이티브 통과 건수 증가를 전반적 개선·통계적 유의성·운영 승인·포털 오류 해결·새 한국어 결과로 해석하지 않습니다.

**실행된 최종 실습 상태:** `contoso-eval-en`의 **Details → Agent configuration → Active version → Edit → Version 1**에서 활성 버전을 **1**로 복원했습니다. 후보 v2·평가 run·receipt는 삭제하지 않고 유지합니다. **운영용 Publish는 없었고 운영 채널·트래픽도 구성하지 않았습니다.** 다만 Foundry는 Publish 없이 **RBAC-only Responses/preview endpoints**를 자동 제공하므로 endpoint 존재와 운영 게시를 구분합니다.
