<p class="eyebrow">PORTAL ONLY · v1.1 · 한국어</p>

# Microsoft Foundry 평가·최적화 실습 v1.1

**새 리소스 그룹 → 정책을 검색하는 Agent → 기준선 평가 → 지침 최적화 → 같은 조건으로 재평가.** Azure Portal과 Foundry Portal에서 클릭하고 입력하는 실습입니다. 터미널, Cloud Shell, 설치, 스크립트 실행은 필요하지 않습니다.
{: .hero-summary}

<div class="hero-summary">
<div><strong>Azure Portal</strong><span>새 리소스 그룹을 만들고 실제 자원을 확인합니다.</span></div>
<div><strong>Foundry Portal</strong><span>Agent·평가·Optimize를 실행합니다.</span></div>
<div><strong>완성 결과</strong><span>두 Agent 버전의 답변·점수·오류를 같은 조건으로 비교합니다.</span></div>
</div>

[실제 포털 녹화 보기](../docs/media/portal.v1.1.html) · [기존 v1 가이드](handbook.md)

**이 가이드는 별도 경로입니다.** 기존 v1의 환경·명령·모델 설정을 섞지 않습니다. Contoso Atlas Cloud 정책과 질문은 실습용 합성 자료이며 Microsoft 또는 실제 고객의 약관이 아닙니다. 운영 게시와 실제 환불·삭제·권한 변경은 하지 않습니다.

**교육용 비교입니다.** 기준선은 정책 검색과 정상 JSON이 동작하는 **기본 FAQ 초안**입니다. 다만 짧은 일반 정책 요약에 머물러 복잡한 조건 계산과 누락 정보 확인이 부족하도록 설계했습니다. Optimizer가 지침을 고친 뒤 **Relevance와 TaskAdherence를 각각 비교**합니다. 질문·정답·모델·평가 기준을 바꿔 점수를 올리지 않습니다. 이 데모를 일반적인 운영 성능이나 미지의 질문에 대한 개선 증거로 해석하지 않습니다.

그림은 개인정보를 가린 실제 포털 화면입니다. 화면 속 과거 점수는 자신의 실행 결과나 보장된 목표 점수가 아닙니다.

## 01. 계정과 실습 파일 준비 {#portal-setup}

**필요한 것:** 조직 계정, 사용을 승인받은 Azure 구독, 리소스 생성·모델 배포·Agent/평가/Optimize 실행 권한, 모델 할당량과 비용 승인입니다. 권한이나 할당량이 없으면 관리자에게 요청한 뒤 진행합니다. 이 실습을 위해 비밀번호·키·토큰을 공유하지 않습니다.

1. 브라우저 탭 두 개에서 [Azure Portal](https://portal.azure.com/)과 [Foundry Portal](https://ai.azure.com/)을 엽니다.
2. **두 포털 모두 같은 조직 계정**으로 로그인합니다. 계정이 여러 개면 Azure에서 선택한 구독에 접근할 수 있는 계정을 사용합니다.
3. 아래 파일 두 개를 내 PC에 저장합니다. 웹 가이드에서는 파일 링크를 오른쪽 클릭해 **다른 이름으로 링크 저장**을 선택합니다. GitHub에서는 파일 화면의 **Download raw file**을 사용합니다. 파일 확장자를 바꾸지 않습니다.

| 저장할 파일 | 사용 위치 | 내용 |
|---|---|---|
| [documents.v1.1.json](../data/knowledge/documents.v1.1.json) | 05 · File search 업로드 | 합성 정책 8개 |
| [dev.v1.1.jsonl](../data/optimizer/dev.v1.1.jsonl) | 06 · 평가 데이터셋 업로드 | 질문 12개와 평가 참고 자료 |

파일을 편집하거나 질문을 골라 빼지 않습니다. v1.1 파일은 기존 한국어 정책·평가 데이터와 내용이 같습니다.

**이름 규칙:** 직접 정하는 새 이름에는 `v1.1`을 붙입니다. 마침표가 허용되지 않는 이름에는 `v1-1`을 사용합니다. 아래 날짜는 예시이며, 자신의 날짜나 짧은 식별자로 바꿔도 됩니다. 서비스가 자동 부여하는 run ID·숫자 버전·내부 관리 객체 이름은 직접 입력하는 이름이 아닙니다.

**완료 기준:** 두 포털에 로그인되어 있고, PC에 두 파일이 있습니다. 브라우저를 닫아도 Azure 과금은 멈추지 않습니다.
{: .completion-check}

## 02. Azure Portal에서 새 리소스 그룹 만들기 {#portal-resource-group}

**조작 위치:** Azure Portal → 상단 검색 → **Resource groups**.
{: .step-route}

1. **Create**를 선택합니다.
2. **Basics**에 아래 값을 입력합니다.

| 항목 | 입력·선택 |
|---|---|
| Subscription | 사용을 승인받은 자신의 구독 |
| Resource group name | `rg-foundry-eval-v1.1-20261104` |
| Region | **(US) North Central US** |

3. **Tags**에서 이름 `lab-version`, 값 `v1.1`을 추가합니다.
   {: value="3"}
4. **Review + create → Create**를 선택합니다.
5. 생성한 그룹을 엽니다. **Overview**에서 그룹 이름을 확인하고, 아직 실습 자원이 없는지 확인합니다.

![새 리소스 그룹의 Basics 입력 화면](../web/assets/portal/v1.1/01-resource-group-basics.v1.1.png)

기존 실습 그룹을 재사용하지 않습니다. 같은 이름이 이미 있으면 이름 뒤에 `-02`를 붙이고, 이후 단계에서도 그 그룹을 선택합니다.

**완료 기준:** 방금 만든 **빈 리소스 그룹**이 Azure Portal에 보입니다.
{: .completion-check}

## 03. Foundry 리소스와 프로젝트 만들기 {#portal-project}

**조작 위치:** Foundry Portal → **Create new → Create a project**. 생성 화면을 확인하기 위해 이 단계만 기존 화면을 사용하고, 생성 뒤 New Foundry로 전환합니다.
{: .step-route}

1. Foundry Portal의 **New Foundry** 스위치가 켜져 있으면 끕니다.
2. 홈의 **Create new**에서 프로젝트 생성 화면을 엽니다.
3. **Project**에 `proj-foundry-eval-v1-1`을 입력합니다.
4. **Advanced options**를 펼치고 아래 값을 확인합니다. 자동으로 선택된 다른 구독·리소스 그룹을 그대로 사용하지 않습니다.

| 항목 | 입력·선택 |
|---|---|
| Microsoft Foundry resource | `ai-foundry-eval-v1-1-20261104` |
| Subscription | 02에서 선택한 구독 |
| Resource group | **02에서 만든 새 그룹** |
| Region | **North Central US** |

5. **Create**를 한 번 선택하고 프로젝트 홈이 열릴 때까지 기다립니다. 이름이 이미 사용 중이면 Foundry 리소스 이름 끝에 짧은 식별자를 더합니다.
   {: value="5"}
6. **New Foundry**를 켭니다. 계정 선택이 나오면 Azure Portal과 같은 계정을 선택합니다.
7. 상단 프로젝트가 `proj-foundry-eval-v1-1`인지 확인합니다.
8. Azure Portal의 새 리소스 그룹으로 돌아가 **Refresh**합니다. **Foundry 리소스와 Foundry project**가 생성되어 있는지 확인합니다.

![기존 화면에서 새 그룹을 지정한 Foundry 프로젝트 생성](../web/assets/portal/v1.1/05-foundry-project-create.v1.1.png)

**오류가 나면:** 입력 검증 성공은 배포 성공이 아닙니다. 생성 오류가 났다면 새 그룹의 **Overview와 Deployments**를 확인합니다. 이미 생성된 객체가 있으면 먼저 그 객체를 열어 확인하고 중복 생성하지 않습니다. 이 가이드는 Azure Portal의 Foundry 생성 창 대신 위 Foundry Portal 경로를 사용합니다.

**완료 기준:** 새 그룹에 두 자원이 있고, New Foundry에서 새 프로젝트 홈이 열립니다.
{: .completion-check}

## 04. 모델을 세 역할로 배포하기 {#portal-models}

**조작 위치:** New Foundry → **Catalog → Models**.
{: .step-route}

같은 모델을 두 역할에 사용해도 **배포 이름은 구분**합니다. Agent가 답하고, Judge가 채점하며, Optimizer가 개선 지침을 만듭니다.

| 역할 | 모델 / 모델 버전 | Deployment name | Capacity |
|---|---|---|---|
| Agent | **gpt-5.5 / 2026-04-24** | `agent-v1-1` | 150K TPM |
| Judge | **gpt-6-luna / 2026-09-22** | `judge-v1-1` | 100K TPM |
| Optimizer | **gpt-5.5 / 2026-04-24** | `optimizer-v1-1` | 150K TPM |

1. **Models** 탭에서 `gpt-5.5`를 검색하고 모델을 엽니다.
2. **Deploy → Custom settings**를 선택합니다.
3. 첫 번째 행의 **Deployment name**을 입력합니다. 배포 유형은 **Global Standard**, 버전은 표의 버전을 선택합니다.
4. **Model version settings → Model version upgrade policy**를 열어 **Opt out of automatic model version upgrades**를 선택합니다.
5. Capacity를 확인하고 **Deploy**합니다.
6. 같은 경로로 Judge와 Optimizer도 배포합니다.
7. 왼쪽 **Models**에서 세 배포의 이름·모델·버전·**Succeeded**를 확인합니다.

![Agent 모델의 이름·버전·자동 업그레이드 정책 설정](../web/assets/portal/v1.1/07-agent-model-deploy.v1.1.png)

**지원 조건:** 이 경로의 Agent는 File search를 지원하는 `gpt-5.5`입니다. 기존 v1의 `gpt-6-sol`로 바꾸지 않습니다. 배포 또는 File search가 지원되지 않거나 할당량이 부족하면 그 상태에서 멈추고 지원·할당량을 확인합니다. 비교 도중 모델이나 버전을 바꾸지 않습니다. Global Standard는 전역 배포 유형이므로 실제 고객의 지역 제한 데이터는 업로드하지 않습니다.

File search 등 관리형 기능이 내부 데이터셋이나 임베딩 배포를 자동 생성할 수 있습니다. 자신이 만든 세 배포와 구분하고, 역할이 확인되지 않은 자동 생성 객체를 이름 정리 목적으로 삭제하지 않습니다.

**완료 기준:** 세 역할의 배포가 Succeeded이고 자동 모델 버전 변경이 꺼져 있습니다.
{: .completion-check}

## 05. Agent에 지침과 File search 연결하기 {#portal-agent}

**조작 위치:** **Agents → New agent → Build an agent**.
{: .step-route}

1. **Agent name**에 `atlas-support-v1-1`을 입력합니다. 이 실습에서는 Microsoft Copilot harness를 선택하지 않습니다.
2. **Create agent and open playground**를 선택합니다.
3. **Model**에서 **gpt-5.5 / agent-v1-1**을 선택합니다. 자동 선택된 모델을 그대로 두지 않습니다.
4. **Instructions**에 아래 **지침 v1(기준선)** 전체를 붙여 넣습니다. [같은 지침 파일](../prompts/baseline.v1.1.txt)도 제공합니다. 이것은 포털 입력 내용이며 실행 명령이 아닙니다.

```text
Contoso Atlas Cloud의 고객지원 도우미입니다. 한국어로 친절하게 답합니다.
정책 질문은 연결한 File search에서 근거를 찾아 답합니다.
answer는 한 문장, 80자 이내로 작성하고 찾은 정책의 일반 규칙만 짧게 요약합니다.
날짜·기한·금액·비율의 개별 계산이나 여러 조건을 함께 비교하는 판단은 하지 않습니다.
조건이 모호하거나 부족해도 추가 확인 질문을 하지 않고 안내 가능한 일반 정책을 설명합니다.
응답은 다음 네 필드만 가진 JSON 객체 하나로 작성합니다. 마크다운은 쓰지 않습니다.
{"answer":"답변","citations":["실제로 사용한 정책 문서 ID"],"route":"answer","needs_human":false}
route는 answer, clarify, escalate, refuse 중 하나입니다. needs_human은 route가 escalate일 때만 true입니다.
이 도우미는 안내만 합니다. 실제 접수, 승인, 환불, 데이터 삭제, 권한 변경을 수행했다고 주장하지 않습니다.
권한 없는 타인 데이터 접근이나 인증 우회 요청은 거절하고, 비밀번호·키·토큰 등 비밀정보를 요청하지 않습니다.
구체적인 평가 문항, 날짜, 정답 예시를 지침에 저장하지 않습니다.
```

5. **Tools**에 기본 **Web search**가 있으면 해당 도구 메뉴의 **Remove**로 제거합니다. 정책 근거는 업로드한 자료로 고정합니다.
   {: value="5"}
6. **Tools → Add → Add tools → File search → Add tool**을 선택합니다.
7. **Attach files**가 열리면 **Vector index name**에 `atlas-policy-v1-1`을 입력합니다.
8. **browse for files**에서 `documents.v1.1.json` **한 개만** 선택합니다. 업로드 상태가 **Success**이면 **Attach**합니다.
9. Tools에 **File search**가 연결되었는지 확인하고 **Save**합니다.
10. 화면 위 **Version**의 숫자를 **기준선 버전**으로 기록합니다. 저장 횟수에 따라 숫자가 달라지므로 반드시 1일 필요는 없습니다.
11. 대화창에 **“Standard 요금제에서 조직 SSO를 사용할 수 있나요?”**를 입력하고 전송합니다.
12. 응답의 도구 표시를 펼쳐 **File search 호출**, 모델 `agent-v1-1`, JSON 응답을 확인합니다. 공개 정책상 SSO는 Pro에만 있으며 근거 ID는 `ATLAS-FEAT-001`입니다. 기본 정책 질문에 답할 수 있어야 합니다.
13. 연결 자체를 확인하려면 **Tools → File search** 카드를 다시 엽니다. `atlas-policy-v1-1`에 정책 파일 한 개가 **Completed**인지 확인한 뒤 **Cancel**로 닫습니다. 파일을 다시 업로드하거나 새 버전을 저장하지 않습니다.

![기존 File search에 정책 파일 한 개가 Completed로 연결된 것을 확인한 화면](../web/assets/portal/v1.1/10-policy-upload.v1.1.png)

**혼동하지 않기:** **Knowledge → Add**는 Foundry IQ 연결 경로입니다. 이번 v1.1은 **Tools의 File search**를 사용하므로 별도 Search 리소스나 Foundry IQ 설정을 만들지 않습니다. File search 카드가 비활성화되어 있으면 먼저 Agent의 실제 선택 모델을 확인합니다.

이 출발점은 모든 질문에 실패하는 Agent가 아닙니다. 기본 검색·형식은 유지하면서 **일반 규칙을 개별 사례에 적용하고 필요한 확인 질문을 하는 능력**을 개선합니다. 이후에는 지침만 바꾸며 정책·도구·모델은 유지합니다. 실습 에디션 **v1.1**과 포털의 **Agent Version 숫자**는 다른 개념입니다.

**완료 기준:** 정책 파일 한 개가 연결된 기준선 버전을 저장했고, 기본 질문의 File search 호출과 정상 JSON 답변을 확인했습니다.
{: .completion-check}

## 06. 12문항으로 기준선 평가 실행하기 {#portal-evaluation}

**조작 위치:** Agent의 **Evaluation → Automatic Evaluation → Create**. 아래 순서는 하나의 평가 생성 화면에서 이어집니다.
{: .step-route}

1. **Target**에서 `atlas-support-v1-1`과 05에서 기록한 **기준선 버전**을 확인합니다.
2. **Scope: Individual turns**, **Frequency: One time**으로 진행합니다.
3. **Data → Existing dataset → Upload dataset**에서 `dev.v1.1.jsonl`을 선택합니다. 데이터셋 이름은 `atlas-dev12-v1-1`, 버전은 `1`로 저장한 뒤 선택합니다.
4. 미리보기에서 **12행**, `query`, `context`, `ground_truth`를 확인합니다. `ground_truth`는 정답 참고 자료이며 JSON 문자열입니다.
5. **Configure agents → Configure**를 엽니다. **USER** 입력란에 아래 값 **한 개만** 넣고 **Save**합니다.

```text
{{item.query}}
```

![Agent 입력에 query만 전달하는 포털 매핑](../web/assets/portal/v1.1/12-query-only-mapping.v1.1.png)

`context`나 `ground_truth`를 이 입력란에 덧붙이지 않습니다. Agent가 정답을 미리 읽지 않고, 실제 File search로 정책을 찾아 답해야 합니다. 매핑 단계가 자동으로 생략되어도 **Configure agents**는 직접 확인합니다.

6. **Criteria → Judge model**을 **judge-v1-1**로 설정합니다. 기본 평가 항목은 **Clear selection**하고 **Relevance**, **Task adherence** 두 개만 선택합니다.
   {: value="6"}
7. 각 평가기를 열어 다음 설정을 확인합니다. Judge는 둘 다 **judge-v1-1**을 선택합니다.

| 설정 | Relevance | Task adherence |
|---|---|---|
| 포털 결과의 지표명 | Relevance | TaskAdherence |
| Judge deployment | `judge-v1-1` | `judge-v1-1` |
| Threshold | **4** | **1** |
| Probability_threshold | 해당 없음 | **0.5** |
| Query | `{{item.query}}` | `{{item.query}}` |
| Response | `{{sample.output_text}}` | `{{sample.output_text}}` |
| Tool definitions | 해당 없음 | 기본 `{{sample.tool_definitions}}` 유지 |

**TaskAdherence 주의:** 이진 0/1 지표입니다. 화면의 공통 Threshold 입력칸에 기본값 3이 보여도 **1**로 바꿉니다. Probability_threshold는 숫자 입력칸의 **0.5**를 확인합니다.

8. **Criteria** 단계의 **Next**를 선택합니다. 평가기 목록의 다음 페이지 버튼과 혼동하지 않습니다.
   {: value="8"}
9. **Review**에서 이름 `atlas-portal-eval-v1-1`을 입력하고 Agent 버전·데이터·평가기 두 개를 다시 확인합니다.
10. **Submit**을 한 번 선택합니다. 목록에서 상태가 끝날 때까지 기다립니다. 같은 평가를 다시 만들지 않습니다.

![기준선 평가의 Review 화면](../web/assets/portal/v1.1/14-baseline-review.v1.1.png)

**완료 기준:** 평가 정의와 실제 run이 생성되었으며, run에서 문항별 응답·점수 또는 오류를 확인할 수 있습니다. 제출 성공만으로 12문항 평가 성공이라고 판단하지 않습니다.
{: .completion-check}

## 07. 점수보다 답변과 오류 먼저 읽기 {#portal-analysis}

**조작 위치:** **Evaluations → atlas-portal-eval-v1-1 → 생성한 run → Detailed metrics**.
{: .step-route}

1. 전체 **12문항**이 있는지 확인합니다. 표에 10행만 보이면 **Next page**로 나머지 2행도 확인합니다.
2. **Error** 열이 있으면 먼저 확인합니다. 오류 없는 페이지에서는 이 열이 표시되지 않을 수 있습니다. 응답 생성 실패와 Judge 채점 실패를 구분합니다.
3. 낮은 **Relevance** 행에서 표를 가로로 스크롤해 `sample.output_text` 열의 **View JSON**을 엽니다. 질문, 실제 답변, **Relevance.reason**을 함께 읽습니다.
4. **TaskAdherence**와 그 이유도 읽습니다. 지침 준수와 업무상 충분한 답변은 다른 기준입니다.
5. 기준선 버전, 평가 정의, 데이터셋 버전, 두 평가기의 설정, 오류 문항을 자신의 비공개 기록에 남깁니다.

| 확인할 질문 | 판단 |
|---|---|
| 일반 규칙만 설명하고 질문의 조건을 놓치지 않았나요? | 계산·조건 비교·필수 확인 질문의 누락을 찾습니다. |
| 정책에 있는 기한·금액을 질문에 맞게 설명했나요? | 단순히 “지원팀 확인”으로 끝났는지 봅니다. |
| 정보가 부족한 질문에 필요한 조건을 물었나요? | 예: 요금제, 월간/연간, 대상 월 등 실제 누락 조건을 봅니다. |
| 공개 자료에 없는 기능을 미확인이라고 했나요? | 낮은 점수를 받았어도 허위 확답으로 바꾸지 않습니다. |
| 승인·접수·삭제를 실제 수행한 것처럼 말했나요? | 안내용 Agent가 할 수 없는 행동을 주장하면 안 됩니다. |
| 채점 이유가 표시된 답변과 일치하나요? | 불일치하면 전체 대화·도구 이력을 확인하고 판정을 보류합니다. |

**Partial / 모델 제공자 차단:** run 상세에 **Completed**가 보여도 정의 목록에는 **Partial**일 수 있습니다. 성공한 문항 수와 오류 수를 함께 기록합니다. 예를 들어 11문항만 채점되었다면 그 통과율을 12문항 전체의 통과율로 읽지 않습니다. `cyber_policy` 등 제공자 차단은 Agent의 거절 답변이나 일반 오답과 구분합니다. 차단을 피하려고 보호 장치를 끄거나 질문을 바꾸지 않습니다.

**완료 기준:** 낮은 점수 1건 이상에서 실제 답변과 이유를 읽고, 지침으로 개선할 점과 서비스 오류를 구분합니다. 오류가 남으면 **전체 개선 판정은 보류**합니다.
{: .completion-check}

## 08. Instruction만 최적화하기 {#portal-optimize}

**조작 위치:** **Agents → atlas-support-v1-1 → 기준선 버전 → Optimize → Optimize my agent → Agent**.
{: .step-route}

첫 소개 화면의 예시 benchmark는 자신의 실습 결과가 아닙니다.

1. **Target**에서 기준선 Agent 버전을 확인합니다.
2. **Optimization approach → Choose targets**를 선택합니다. 자동 선택 상태를 믿지 말고 아래처럼 설정합니다.

| 항목 | 설정 |
|---|---|
| Instruction | **선택** |
| Tool description | **선택 해제** |
| Model / Compare across models | **선택 해제 / 끔** |
| Optimization model | **optimizer-v1-1** |
| Max candidates | **1** |
| Evaluation model | **judge-v1-1** |

![Instruction만 선택하고 생성 모델·Judge·후보 수를 고정한 화면](../web/assets/portal/v1.1/17-optimizer-settings.v1.1.png)

3. **Next → Data source → Select dataset and criteria**를 선택합니다. Generate data나 production traces는 사용하지 않습니다.
   {: value="3"}
4. **Dataset**에서 `atlas-dev12-v1-1`, 버전 `1`을 선택합니다.
5. **Criteria**의 **Custom only**가 켜져 있으면 끕니다. 검색으로 다음 두 평가기를 선택합니다. 선택할 때 설정 창이 열리면 값을 확인하고 **Apply**합니다.

| Optimizer 화면의 평가기 | 버전 | 설정 |
|---|---|---|
| Relevance-Evaluator | 15 | Threshold **4** |
| Task-Adherence-Evaluator-(Preview) | 18 | Threshold **1**, Probability_threshold **0.5** |

6. 다른 평가기가 추가되지 않았는지 확인하고 **Next**를 선택합니다.
   {: value="6"}
7. **Review**에서 **Optimization targets: Instruction**, 같은 데이터셋, 같은 Judge, 후보 **1개**를 확인합니다. **Estimated cost**도 읽습니다. 예상치는 실제 청구 금액이나 상한 보장이 아닙니다.
8. **Submit**을 한 번 선택합니다. 실행 목록의 자동 생성 **Run ID**를 열고 기다립니다. 별도 실행 이름 입력란이 없으므로 그 ID를 비공개 기록에 남깁니다.
9. **Additional settings**에서 Instruction·모델·후보 수가 의도와 같은지 확인합니다.
10. 실행이 끝나면 **Candidate results**에서 baseline과 각 후보의 **Changes / View changes**, score details를 엽니다.

![지침만 변경하는 Optimizer 실행의 Review 화면](../web/assets/portal/v1.1/18-optimizer-review.v1.1.png)

**후보 검토:** 점수가 높아도 정책 숫자·정답을 지침에 통째로 외우게 하거나, 미확인 기능을 확답하거나, 실제 수행하지 않은 일을 완료했다고 주장하면 채택하지 않습니다. 권한 우회와 비밀정보 요청도 허용하지 않습니다. 허용할 변화는 답변 구조·근거 사용·필요한 확인 질문 같은 **일반적인 지침 개선**입니다.

Optimizer의 **Task-weighted average (0–1)**는 평가 화면의 개별 통과율과 같은 숫자가 아닙니다. 학습에 사용한 12문항의 점수 상승만으로 일반화·운영 품질을 입증할 수도 없습니다.

**완료 기준:** 실제 후보 지침과 채점 이유를 읽고 보관할 후보가 있는지 판단합니다. 실패하면 오류를 보존합니다. 같은 설정을 유리한 점수가 나올 때까지 재실행하지 않습니다.
{: .completion-check}

## 09. 검토수정본을 새 버전으로 저장하고 비교하기 {#portal-compare}

**조작 위치:** Agent의 **Playground → Instructions → Save**와 기존 평가 정의의 **Add run / Compare runs**.
{: .step-route}

Optimizer 후보에는 평가 문항의 날짜·정답 예시가 그대로 들어갈 수 있습니다. 그런 원본은 점수가 올라도 그대로 승격하지 않습니다. 이 경로에서는 일반적인 답변·검색·라우팅 개선을 반영한 **[지침 v2 · 검토수정본 reviewed.v1.1.txt](../prompts/reviewed.v1.1.txt)**을 사용합니다. **사람이 작성·검토한 보완본이며 Optimizer의 원본 출력이 아닙니다.** 원본에 남은 글자 수·계산 금지·확인 질문 금지 제약도 사람이 수정했습니다. 원본 후보의 점수를 이 수정본의 점수로 인용하거나 개선을 Optimizer 단독 효과로 해석하지 않습니다.

1. Agent의 **Playground**에서 **기준선 버전**을 엽니다. Instructions를 위 파일의 전체 내용으로 교체하고 **Save**를 선택합니다. **Publish**는 누르지 않습니다.
2. 생성된 Agent 버전 숫자를 **비교 버전**으로 기록합니다. 기준선과 지침만 다르고 모델 `agent-v1-1`, File search, 정책 파일은 같은지 확인합니다. 원본 기준선 버전은 그대로 남습니다.
3. **Evaluations → atlas-portal-eval-v1-1 → Add run**을 선택합니다. 새 평가 정의를 만들지 않습니다.
4. **Target**에서 같은 Agent의 행을 선택합니다. Version 메뉴에서 **Pin v숫자**로 기록한 비교 버전을 고릅니다. **Latest available**로 두지 않습니다.
5. **Scope: Individual turns → Next**로 진행합니다. **Data**가 나오면 **Existing dataset**에서 같은 `atlas-dev12-v1-1`, 버전 `1`을 다시 선택하고 **Next**합니다. **Configure agents → Configure**에서 **User prompt**에 `{{item.query}}`만 입력하고 **Save → Submit**합니다. Judge·평가기는 기존 정의를 재사용합니다. 실행 후 12행과 Error를 다시 확인합니다.
6. 평가 정의로 돌아가 처음 기준선 run과 비교 버전 run의 **행 체크박스 두 개를 먼저 선택**한 뒤 **Compare runs**를 누릅니다.
7. 통계 비교 화면의 **Baseline**을 처음 기준선 run으로 지정합니다. **자동으로 최신 run이 기준선이 될 수 있습니다.** 이름이 같아 구분되지 않으면 각 run 상세에서 기록한 평균 점수와 **Baseline** 표시 열의 값을 대조합니다. 기준 방향을 거꾸로 읽지 않습니다.
8. 이 화면은 **평균 점수와 통계 판정**을 보여 줍니다. 개별 문항은 평가 목록으로 돌아가 두 run을 각각 열고 **Detailed metrics**의 **같은 Index**에서 응답·점수·이유·오류를 비교합니다. 지연과 토큰 사용도 함께 확인합니다.

![두 실행의 평균 점수와 Baseline 방향을 확인하는 통계 비교 화면](../web/assets/portal/v1.1/24-compare-runs.v1.1.png)

| 비교 조건 | 고정할 값 |
|---|---|
| 질문·참고 자료 | `atlas-dev12-v1-1`, 같은 버전, 전체 12문항 |
| Agent 입력 | `{{item.query}}`만 |
| Agent 모델·정책·도구 | `agent-v1-1`, 같은 File search와 정책 파일 |
| Judge·평가기 | `judge-v1-1`, Relevance 4, TaskAdherence 1 / 0.5 |
| 유일한 의도적 변경 | 검토한 Agent 지침 |

**결론은 셋 중 하나입니다.** 전체 문항이 유효하고 두 품질 지표에 회귀가 없으며 하나 이상이 개선되고 실제 답변도 올바르면 이번 표본의 관측 개선으로 기록합니다. 지표가 같거나 하나라도 악화되면 기준선을 유지하고 원인을 검토합니다. **Partial·누락·제공자 차단이 남으면 전체 개선은 입증되지 않았다고 기록**합니다. Overall 상승이 다른 품질 지표의 하락을 없애 주지는 않습니다. 실습용 비교 버전을 저장한 것과 운영 채택은 다릅니다.

자신이 검토한 다른 지침을 사용한다면 원본과 수동 수정 부분을 구분합니다. 적절한 수정본이 없으면 기준선을 유지하고 10으로 이동합니다. 비교를 만들기 위해 정답을 지침에 복사하거나, 실패 문항을 삭제하거나, 기준선 결과를 덮어쓰지 않습니다.

**이번 녹화의 실제 결과 · 2026-11-04**

| 지표 | 지침 v1 · Agent v6 | 검토한 지침 v2 · Agent v7 |
|---|---|---|
| Relevance 통과율 | **7/11 · 64%** | **11/11 · 100%** |
| TaskAdherence 통과율 | **8/11 · 73%** | **11/11 · 100%** |
| Relevance 평균 | 3.64 | 4.91 |
| TaskAdherence 평균 | 0.73 | 1.00 |
| P50 / P95 응답 지연 | 5.4s / 7.7s | 4.6s / 6.8s |

![같은 정의의 두 실행에서 두 지표의 통과율이 상승한 실제 결과](../web/assets/portal/v1.1/23-evaluation-runs.v1.1.png)

두 run 모두 **12문항 중 같은 Index 9 한 건이 `cyber_policy`로 차단된 Partial**입니다. 위 분모는 공통 유효 문항 **11개**입니다. 통계 화면은 Relevance를 **Improved by 1.27**, TaskAdherence를 **Inconclusive**로 판정했습니다. **두 관측 통과율의 상승은 확인했지만, 전체 12문항의 개선이나 두 지표 모두의 통계적 유의성을 입증한 것은 아닙니다.**

Optimizer 자체의 별도 실행은 후보 **1개**, **6m 23s**였으며 Task-weighted average는 **0.625 → 0.781**이었습니다. 원본에는 정책 날짜·예시와 기존 제약이 남아 있어 그대로 승격하지 않았습니다. 위 표는 그 원본의 점수가 아니라 **사람이 보완한 v2를 같은 평가 정의에서 다시 측정한 결과**입니다. 기본 검색·JSON이 동작하는 기준선에서, v2는 취소/하향의 의도를 묻고 환불 기한을 계산하는 등 실제 답변도 개선했습니다.

**완료 기준:** 같은 조건의 두 run을 실제로 비교했거나, 후보를 채택하지 않은 이유를 남겼습니다. 운영 게시와 통계적 개선 보장은 하지 않습니다.
{: .completion-check}

## 10. 결과 보관과 자원 정리 {#portal-finish}

**조작 위치:** Foundry Portal의 결과 화면과 Azure Portal의 전용 리소스 그룹.
{: .step-route}

1. 재개할 계획이면 프로젝트·Agent 이름, 기준선/비교 버전, 데이터셋 버전, 평가·Optimizer run ID, 오류·판단을 **비공개**로 기록합니다.
2. 결과를 내려받을 때는 포털의 **Download results / Download JSON**을 사용합니다. 다운로드 링크의 서명된 주소, 계정·구독 식별자, 키·토큰을 공개 문서에 넣지 않습니다.
3. **보존**한다면 비용 책임과 다음 검토·삭제일을 정하고 새 그룹을 유지합니다. 불필요한 재생성·재평가를 하지 않습니다.
4. **삭제**한다면 먼저 공유 자원이 아닌 자신의 전용 그룹인지 확인합니다. Azure Portal에서 그 그룹의 **Delete resource group**을 선택하고 그룹 이름을 입력한 뒤 승인된 삭제만 실행합니다.
5. 삭제 완료 후 **Resource groups → Refresh**에서 해당 그룹이 없어졌는지 확인합니다. 공유·외부 자원을 따로 삭제하지 않습니다.

이 녹화에 사용한 환경은 검토·재개를 위해 **보존**했습니다. 영상이 끝났다고 실제 삭제가 수행된 것은 아닙니다. File search 저장 공간과 모델 사용량 등은 해당 서비스 요금 정책을 확인합니다.

**재개:** Azure Portal에서 자신의 그룹을 열고, Foundry Portal에서 같은 프로젝트를 선택합니다. Agents의 버전과 Evaluations의 기존 run을 먼저 확인한 뒤 필요한 다음 단계만 진행합니다.

**자주 막히는 지점**

| 증상 | 포털에서 확인할 것 |
|---|---|
| 새 프로젝트가 안 보임 | 같은 조직 계정·구독인지, 상단 프로젝트 선택이 맞는지 확인합니다. |
| 생성 검증은 성공했지만 자원이 없음 | 그룹의 Overview·Deployments와 오류를 확인합니다. 검증만 성공한 상태를 생성 성공으로 취급하지 않습니다. |
| File search가 비활성화됨 | Agent 모델이 이 경로의 `gpt-5.5 / agent-v1-1`인지 확인합니다. |
| Knowledge에서 파일 업로드를 못 찾음 | **Tools → File search**로 이동합니다. Foundry IQ 경로가 아닙니다. |
| 정책 파일이 두 번 표시됨 | Attach 전 중복 항목을 제거하고 한 파일의 Success를 확인합니다. |
| TaskAdherence가 모두 실패함 | 이진 지표의 Threshold가 **1**, Probability_threshold가 **0.5**인지 확인합니다. |
| Partial 또는 `cyber_policy` 오류 | Error와 성공·실패 분모를 보존합니다. 보호 장치 해제나 질문 변경으로 우회하지 않습니다. |
| 삭제한 모델이 목록에 남아 보임 | 화면을 새로 고친 후 실제 목록을 확인합니다. |

**완료 기준:** 결과와 오류를 보관했고, 자원의 보존 또는 삭제 여부를 확인했습니다. 브라우저 종료를 정리 완료로 보지 않습니다.
{: .completion-check}

공식 참고: [프로젝트 생성](https://learn.microsoft.com/azure/foundry/how-to/create-projects) · [평가](https://learn.microsoft.com/azure/foundry/how-to/evaluate-generative-ai-app) · [File search](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search) · [Agent Optimizer](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview).
