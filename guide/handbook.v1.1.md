<p class="eyebrow">PORTAL ONLY · v1.1 · 한국어</p>

# Microsoft Foundry 평가·최적화 실습 v1.1

**새 리소스 그룹 → 정책을 검색하는 Agent → 기준선 평가 → 지침 최적화 → 같은 조건으로 재평가.** Azure Portal과 Foundry Portal에서 클릭하고 입력하는 실습입니다. 터미널, Cloud Shell, 설치, 스크립트 실행은 필요하지 않습니다.
{: .hero-summary}

<div class="hero-summary">
<div><strong>Azure Portal</strong><span>새 리소스 그룹을 만들고 실제 자원을 확인합니다.</span></div>
<div><strong>Foundry Portal</strong><span>Agent·평가·Optimize를 실행합니다.</span></div>
<div><strong>완성 결과</strong><span>두 Agent 버전의 답변·점수·오류를 같은 조건으로 비교합니다.</span></div>
</div>

[English guide](en/handbook.v1.1.md) · [실제 포털 녹화 보기 · 한국어 자막](../docs/media/portal.v1.1.html) · [기존 v1 가이드](handbook.md)

**이 가이드는 별도 경로입니다.** 기존 v1의 환경·명령·모델 설정을 섞지 않습니다. Contoso Atlas Cloud 정책과 질문은 실습용 합성 자료이며 Microsoft 또는 실제 고객의 약관이 아닙니다. 운영 게시와 실제 환불·삭제·권한 변경은 하지 않습니다.

**교육용 비교입니다.** 기준선은 정책 검색과 정상 JSON이 동작하는 **기본 FAQ 초안**입니다. 다만 짧은 일반 정책 요약에 머물러 복잡한 조건 계산과 누락 정보 확인이 부족하도록 설계했습니다. Optimizer가 지침을 고친 뒤 **Relevance와 TaskAdherence를 각각 비교**합니다. 질문·정답·모델·평가 기준을 바꿔 점수를 올리지 않습니다. 이 데모를 일반적인 운영 성능이나 미지의 질문에 대한 개선 증거로 해석하지 않습니다.

그림은 기존 녹화·캡처에서 가져온 실제 포털 화면입니다. 클릭·입력할 곳이 잘 보이도록 일부 화면을 잘랐으며 개인정보를 가렸습니다. 제품의 점수·답변·상태는 바꾸지 않았습니다. 화면 속 과거 점수는 자신의 실행 결과나 보장된 목표 점수가 아닙니다.

**진행 방법:** 01부터 10까지 위에서 아래로 진행합니다. **번호대로 조작 → 바로 아래 화면과 대조 → 다음 번호** 순서입니다. 작은 글씨는 각 그림의 **원본 크기로 보기**로 확인합니다. 국문·영문 가이드는 같은 한국어 정책·질문·지침·실측 화면을 사용합니다. 가이드 언어만 바꾸며, 별도의 영어 데이터 평가 결과를 주장하지 않습니다.

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

<figure class="portal-shot" id="shot-resource-group-v1-1">
  <img src="../web/assets/portal/v1.1/01-resource-group-basics.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="새 리소스 그룹의 Basics 입력 화면">
  <figcaption><strong>구독·새 그룹 이름·지역을 확인합니다.</strong> 기존 그룹을 선택하는 화면이 아니라 새 그룹의 생성 화면입니다. <a href="../web/assets/portal/v1.1/01-resource-group-basics.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

3. **Tags** 탭을 엽니다. **Name**과 **Value** 입력란을 찾습니다.
   {: value="3"}

<figure class="portal-shot" id="shot-resource-group-tags-v1-1">
  <img src="../web/assets/portal/v1.1/29-resource-group-tags.v1.1.png" width="830" height="310" loading="lazy" decoding="async" alt="Tags 탭의 비어 있는 Name과 Value 입력란">
  <figcaption><strong>왼쪽 Name, 오른쪽 Value에 입력합니다.</strong> 아직 값을 넣기 전 화면입니다. 다음 번호에서 두 칸을 채웁니다. <a href="../web/assets/portal/v1.1/29-resource-group-tags.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

4. **Name**에 `lab-version`, **Value**에 `v1.1`을 입력하고 **Review + create**를 선택합니다.
   {: value="4"}

<figure class="portal-shot" id="shot-resource-group-review-v1-1">
  <img src="../web/assets/portal/v1.1/30-resource-group-review.v1.1.png" width="920" height="650" loading="lazy" decoding="async" alt="생성 전 검토 화면의 새 그룹 이름, North Central US, lab-version v1.1">
  <figcaption><strong>그룹 이름·지역·태그를 제출 전에 확인합니다.</strong> 이름은 자신이 입력한 값이어야 합니다. 이 화면은 검토 단계이며 아직 생성 완료가 아닙니다. <a href="../web/assets/portal/v1.1/30-resource-group-review.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

5. 입력값과 검증 결과를 확인하고 화면 아래 **Create**를 한 번 선택합니다.
   {: value="5"}
6. 생성한 그룹을 엽니다. **Overview**에서 그룹 이름을 확인하고, 아직 실습 자원이 없는지 확인합니다.

<figure class="portal-shot" id="shot-empty-group-v1-1">
  <img src="../web/assets/portal/v1.1/02-empty-resource-group.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="자원 0개와 No deployments가 표시된 새 리소스 그룹">
  <figcaption><strong>자원 0개·No deployments·태그 v1.1을 확인합니다.</strong> 아직 Foundry를 만들기 전 상태입니다. 필터가 전체인지도 확인합니다. <a href="../web/assets/portal/v1.1/02-empty-resource-group.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

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

<figure class="portal-shot" id="shot-project-create-v1-1">
  <img src="../web/assets/portal/v1.1/05-foundry-project-create.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Advanced options에서 새 그룹을 지정한 Foundry 프로젝트 생성 화면">
  <figcaption><strong>Advanced options의 리소스 그룹을 확인합니다.</strong> 02에서 만든 그룹과 같은 구독·지역을 지정합니다. <a href="../web/assets/portal/v1.1/05-foundry-project-create.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

5. **Create**를 한 번 선택하고 프로젝트 홈이 열릴 때까지 기다립니다. 이름이 이미 사용 중이면 Foundry 리소스 이름 끝에 짧은 식별자를 더합니다.
   {: value="5"}
6. **New Foundry**를 켭니다. 계정 선택이 나오면 Azure Portal과 같은 계정을 선택합니다.
7. 상단 프로젝트가 `proj-foundry-eval-v1-1`인지 확인합니다.

<figure class="portal-shot" id="shot-project-home-v1-1">
  <img src="../web/assets/portal/v1.1/06-project-home.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="New Foundry가 켜진 새 프로젝트 홈과 왼쪽 Agents, Models, Evaluations 메뉴">
  <figcaption><strong>상단 프로젝트와 New Foundry 스위치를 확인합니다.</strong> 이후 사용할 Agents·Models·Evaluations는 왼쪽 메뉴에 있습니다. 홈의 추천 모델을 추가로 배포하지 않습니다. <a href="../web/assets/portal/v1.1/06-project-home.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

8. **Azure Portal 탭**으로 전환해 새 리소스 그룹에서 **Refresh**합니다. **Foundry 리소스와 Foundry project** 두 자원을 확인합니다.
   {: value="8"}

<figure class="portal-shot" id="shot-created-resources-v1-1">
  <img src="../web/assets/portal/v1.1/15-created-resources.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="전용 그룹에 Foundry와 Foundry project 두 자원이 생성된 목록">
  <figcaption><strong>Type 열의 Foundry와 Foundry project 두 행을 확인합니다.</strong> 이름이 비슷해도 서로 다른 두 자원입니다. 같은 환경의 생성 확인 화면이며 추가 생성 지시가 아닙니다. <a href="../web/assets/portal/v1.1/15-created-resources.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**오류가 나면:** 입력 검증 성공은 배포 성공이 아닙니다. 생성 오류가 났다면 새 그룹의 **Overview와 Deployments**를 확인합니다. 이미 생성된 객체가 있으면 먼저 그 객체를 열어 확인하고 중복 생성하지 않습니다. 이 가이드는 Azure Portal의 Foundry 생성 창 대신 위 Foundry Portal 경로를 사용합니다.

**완료 기준:** 새 그룹에 두 자원이 있고, New Foundry에서 새 프로젝트 홈이 열립니다.
{: .completion-check}

## 04. 모델을 세 역할로 배포하기 {#portal-models}

**조작 위치:** **Foundry Portal 탭** → New Foundry → **Catalog → Models**.
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

<figure class="portal-shot" id="shot-model-deploy-v1-1">
  <img src="../web/assets/portal/v1.1/07-agent-model-deploy.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Agent 배포 이름과 모델 버전, 자동 업그레이드 해제 설정">
  <figcaption><strong>배포 이름·고정 버전·자동 업그레이드 해제를 확인합니다.</strong> 같은 모델이라도 Agent와 Optimizer의 배포 이름은 다릅니다. <a href="../web/assets/portal/v1.1/07-agent-model-deploy.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

5. Capacity를 확인하고 **Deploy**합니다.
   {: value="5"}
6. **Catalog → Models**에서 `gpt-6-luna`를 열고 **Deploy → Custom settings**를 선택합니다. 이름 `judge-v1-1`, **Global Standard**, 버전 **2026-09-22**, 자동 업그레이드 **Opt out**, Capacity **100000 TPM**을 설정합니다.

<figure class="portal-shot" id="shot-judge-model-settings-v1-1" data-capture-layout="dialog">
  <img src="../web/assets/portal/v1.1/31-judge-model-settings.v1.1.png" width="592" height="1000" loading="lazy" decoding="async" alt="Judge 배포 패널의 judge-v1-1, gpt-6-luna, 고정 버전과 100000 TPM">
  <figcaption><strong>Judge는 별도 모델·이름으로 설정합니다.</strong> 배포 패널만 확대했습니다. 숫자 입력란의 100000은 이 배포의 TPM이며 오른쪽 최대 할당량과 다릅니다. <a href="../web/assets/portal/v1.1/31-judge-model-settings.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

7. **Deploy**로 Judge를 배포합니다. 이어서 Catalog의 `gpt-5.5`에서 **Deploy → Custom settings**를 엽니다. 이름 `optimizer-v1-1`, **Global Standard**, 버전 **2026-04-24**, 자동 업그레이드 **Opt out**, Capacity **150000 TPM**을 설정합니다.
   {: value="7"}

<figure class="portal-shot" id="shot-optimizer-model-settings-v1-1" data-capture-layout="dialog">
  <img src="../web/assets/portal/v1.1/32-optimizer-model-settings.v1.1.png" width="592" height="1000" loading="lazy" decoding="async" alt="Optimizer 배포 패널의 optimizer-v1-1, gpt-5.5, 고정 버전과 150000 TPM">
  <figcaption><strong>Agent와 모델이 같아도 이름은 optimizer-v1-1입니다.</strong> 이전 배포를 재사용하는 대신 Optimizer용 배포를 만듭니다. <a href="../web/assets/portal/v1.1/32-optimizer-model-settings.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

8. **Deploy**로 Optimizer를 배포합니다. 왼쪽 **Models**에서 세 배포의 이름·모델·버전을 대조하고 모두 **Succeeded**가 될 때까지 기다립니다.
   {: value="8"}

<figure class="portal-shot" id="shot-models-succeeded-v1-1">
  <img src="../web/assets/portal/v1.1/08-models-succeeded.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="agent-v1-1, judge-v1-1, optimizer-v1-1이 Succeeded인 배포 목록">
  <figcaption><strong>직접 만든 세 배포의 이름·모델·버전·Succeeded를 대조합니다.</strong> 이 그림은 같은 환경에서 File search 준비 후 확인한 목록이라 자동 생성된 text-embedding-ada-002도 보입니다. 네 번째 모델을 수동 배포하라는 뜻이 아닙니다. <a href="../web/assets/portal/v1.1/08-models-succeeded.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**지원 조건:** 이 경로의 Agent는 File search를 지원하는 `gpt-5.5`입니다. 기존 v1의 `gpt-6-sol`로 바꾸지 않습니다. 배포 또는 File search가 지원되지 않거나 할당량이 부족하면 그 상태에서 멈추고 지원·할당량을 확인합니다. 비교 도중 모델이나 버전을 바꾸지 않습니다. Global Standard는 전역 배포 유형이므로 실제 고객의 지역 제한 데이터는 업로드하지 않습니다.

File search 등 관리형 기능이 내부 데이터셋이나 임베딩 배포를 자동 생성할 수 있습니다. 자신이 만든 세 배포와 구분하고, 역할이 확인되지 않은 자동 생성 객체를 이름 정리 목적으로 삭제하지 않습니다.

**완료 기준:** 세 역할의 배포가 Succeeded이고 자동 모델 버전 변경이 꺼져 있습니다.
{: .completion-check}

## 05. Agent에 지침과 File search 연결하기 {#portal-agent}

**조작 위치:** **Agents → New agent → Build an agent**.
{: .step-route}

1. **Agent name**에 `atlas-support-v1-1`을 입력하고 **Text**를 선택합니다. Microsoft Copilot harness는 선택하지 않습니다.

<figure class="portal-shot" id="shot-create-agent-v1-1">
  <img src="../web/assets/portal/v1.1/09-create-agent.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Agent 이름, Text 모드, 선택하지 않은 Microsoft Copilot harness가 보이는 생성 창">
  <figcaption><strong>이름·Text·harness 선택 해제를 확인합니다.</strong> 이 상태에서 아래의 생성 버튼을 선택합니다. <a href="../web/assets/portal/v1.1/09-create-agent.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

2. **Create agent and open playground**를 선택합니다.
   {: value="2"}
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

<figure class="portal-shot" id="shot-baseline-instructions-v1-1" data-capture-layout="dialog">
  <img src="../web/assets/portal/v1.1/33-baseline-instructions.v1.1.png" width="460" height="195" loading="lazy" decoding="async" alt="Playground의 Instructions 입력란에 표시된 기준선 지침 시작 부분">
  <figcaption><strong>Instructions 입력란에 위 본문 전체를 넣습니다.</strong> 입력 위치만 확대한 화면이라 지침 일부만 보입니다. 그림의 일부 문장을 복사하지 말고 위 블록 전체를 사용합니다. Improve instructions는 누르지 않습니다. <a href="../web/assets/portal/v1.1/33-baseline-instructions.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

5. **Tools**에 기본 **Web search**가 있으면 해당 도구 메뉴의 **Remove**로 제거합니다. 정책 근거는 업로드한 자료로 고정합니다.
   {: value="5"}
6. **Tools → Add → Add tools**를 선택해 **Select a tool** 창을 엽니다.

<figure class="portal-shot" id="shot-select-file-search-v1-1">
  <img src="../web/assets/portal/v1.1/34-select-file-search.v1.1.png" width="1200" height="800" loading="lazy" decoding="async" alt="Select a tool 창 왼쪽 첫 번째의 File search와 오른쪽 아래 Add tool">
  <figcaption><strong>왼쪽 첫 번째 File search를 선택합니다.</strong> Azure AI search나 Web search가 아닙니다. 도구를 고르면 오른쪽 아래 Add tool을 사용할 수 있습니다. <a href="../web/assets/portal/v1.1/34-select-file-search.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

7. **File search → Add tool**을 선택합니다. **Attach files**의 **Index option**은 **Create a new index**, **Vector index name**은 `atlas-policy-v1-1`로 설정합니다.
   {: value="7"}

<figure class="portal-shot" id="shot-create-vector-index-v1-1" data-capture-layout="dialog">
  <img src="../web/assets/portal/v1.1/35-create-vector-index.v1.1.png" width="690" height="253" loading="lazy" decoding="async" alt="Attach files 창의 Create a new index, atlas-policy-v1-1과 browse for files">
  <figcaption><strong>새 인덱스 이름을 입력한 뒤 browse for files를 사용합니다.</strong> 입력·파일 선택 영역만 잘랐습니다. 이 그림은 파일 업로드나 연결 완료를 뜻하지 않습니다. <a href="../web/assets/portal/v1.1/35-create-vector-index.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

8. **browse for files**에서 `documents.v1.1.json` **한 개만** 선택합니다. 업로드 상태가 **Success**이면 **Attach**합니다.
   {: value="8"}
9. Tools에 **File search**가 연결되었는지 확인하고 **Save**합니다.
10. **Tools → File search** 카드를 엽니다. `atlas-policy-v1-1`에 정책 파일 한 개가 **Completed**인지 확인합니다.

<figure class="portal-shot" id="shot-policy-upload-v1-1">
  <img src="../web/assets/portal/v1.1/10-policy-upload.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="File search 인덱스에 정책 파일 한 개가 Completed로 연결된 화면">
  <figcaption><strong>파일 한 개와 Completed 상태를 확인합니다.</strong> 이미 저장한 File search 연결입니다. 파일을 다시 업로드하거나 Attach하지 않습니다. <a href="../web/assets/portal/v1.1/10-policy-upload.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

11. **Cancel**로 확인 창을 닫습니다. 화면 위 **Version**의 숫자를 **기준선 버전**으로 기록합니다. 저장 횟수에 따라 숫자가 달라지므로 반드시 1일 필요는 없습니다.
   {: value="11"}
12. 대화창에 **“Standard 요금제에서 조직 SSO를 사용할 수 있나요?”**를 입력하고 전송합니다.
13. 응답의 도구 표시를 펼쳐 **File search 호출**, 모델 `agent-v1-1`, JSON 응답을 확인합니다. SSO는 Pro에만 있으며 근거 ID는 `ATLAS-FEAT-001`입니다.

<figure class="portal-shot" id="shot-agent-retrieval-v1-1">
  <img src="../web/assets/portal/v1.1/11-agent-retrieval.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="기준선 v6의 File search 호출과 ATLAS-FEAT-001을 인용한 정상 JSON 응답">
  <figcaption><strong>모델·File search·JSON 근거를 함께 확인합니다.</strong> 응답은 Standard에 SSO가 없고 Pro에 있다고 설명하며 ATLAS-FEAT-001을 인용합니다. 그림의 Version 6은 이 실행의 기준선 번호일 뿐, 반드시 맞출 숫자가 아닙니다. <a href="../web/assets/portal/v1.1/11-agent-retrieval.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**혼동하지 않기:** **Knowledge → Add**는 Foundry IQ 연결 경로입니다. 이번 v1.1은 **Tools의 File search**를 사용하므로 별도 Search 리소스나 Foundry IQ 설정을 만들지 않습니다. File search 카드가 비활성화되어 있으면 먼저 Agent의 실제 선택 모델을 확인합니다.

이 출발점은 모든 질문에 실패하는 Agent가 아닙니다. 기본 검색·형식은 유지하면서 **일반 규칙을 개별 사례에 적용하고 필요한 확인 질문을 하는 능력**을 개선합니다. 이후에는 지침만 바꾸며 정책·도구·모델은 유지합니다. 실습 에디션 **v1.1**과 포털의 **Agent Version 숫자**는 다른 개념입니다.

**완료 기준:** 정책 파일 한 개가 연결된 기준선 버전을 저장했고, 기본 질문의 File search 호출과 정상 JSON 답변을 확인했습니다.
{: .completion-check}

## 06. 12문항으로 기준선 평가 실행하기 {#portal-evaluation}

**조작 위치:** Agent의 **Evaluation → Automatic Evaluation**. 아래 순서는 하나의 평가 생성 화면에서 이어집니다.
{: .step-route}

1. Agent의 **Evaluation → Automatic Evaluation** 탭을 엽니다. 오른쪽 **Create** 버튼을 찾습니다.

<figure class="portal-shot" id="shot-open-automatic-evaluation-v1-1">
  <img src="../web/assets/portal/v1.1/36-open-automatic-evaluation.v1.1.png" width="1174" height="209" loading="lazy" decoding="async" alt="Agent의 Evaluation과 Automatic Evaluation 탭, 오른쪽 Create 버튼">
  <figcaption><strong>Automatic Evaluation의 Create로 시작합니다.</strong> 위쪽 Create evaluator 안내 버튼이나 Human Evaluation이 아닙니다. <a href="../web/assets/portal/v1.1/36-open-automatic-evaluation.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

2. **Create**를 선택합니다. **Target**에서 `atlas-support-v1-1`을 선택하고 **Version → Pin v숫자**로 05에서 기록한 **기준선 버전**을 고정합니다. **Next** 후 **Scope**에서 **Individual turns**를 선택합니다.
   {: value="2"}

<figure class="portal-shot" id="shot-individual-turns-v1-1">
  <img src="../web/assets/portal/v1.1/37-individual-turns.v1.1.png" width="1184" height="499" loading="lazy" decoding="async" alt="평가 생성 Scope에서 선택된 Individual turns와 Next">
  <figcaption><strong>한 질문·한 응답 단위로 평가합니다.</strong> Full conversations가 아니라 Individual turns를 선택한 상태입니다. <a href="../web/assets/portal/v1.1/37-individual-turns.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

3. **Next → Frequency: One time → Next**로 진행합니다. **Data → Existing dataset → Upload new dataset**을 엽니다. **New dataset name**에 `atlas-dev12-v1-1`을 입력하고 **Choose file**로 `dev.v1.1.jsonl`을 선택한 뒤 **Upload**합니다.
   {: value="3"}

<figure class="portal-shot" id="shot-upload-evaluation-dataset-v1-1" data-capture-layout="dialog">
  <img src="../web/assets/portal/v1.1/38-upload-evaluation-dataset.v1.1.png" width="520" height="394" loading="lazy" decoding="async" alt="Upload new dataset 창의 atlas-dev12-v1-1 이름과 dev.v1.1.jsonl 업로드 진행 상태">
  <figcaption><strong>데이터셋 이름과 선택한 파일을 대조합니다.</strong> 그림은 Upload 처리 중입니다. 다시 누르지 말고 완료되어 목록에 나타날 때까지 기다립니다. <a href="../web/assets/portal/v1.1/38-upload-evaluation-dataset.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

4. 목록에서 `atlas-dev12-v1-1`, 버전 `1`을 선택합니다. 미리보기의 `query`, `context`, `ground_truth` 열을 확인합니다. `ground_truth`는 JSON 문자열인 정답 참고 자료입니다. **Top 5 rows는 미리보기 제한**이며 전체 문항 수가 아닙니다. 실제 전체 **12행**은 실행 후 07에서 확인합니다.
   {: value="4"}

<figure class="portal-shot" id="shot-evaluation-dataset-preview-v1-1">
  <img src="../web/assets/portal/v1.1/39-evaluation-dataset-preview.v1.1.png" width="1184" height="859" loading="lazy" decoding="async" alt="Existing dataset의 선택된 atlas-dev12-v1-1 버전 1과 context, ground_truth, query 미리보기">
  <figcaption><strong>선택한 행의 이름·버전과 미리보기 열을 확인합니다.</strong> 파일을 다시 업로드하지 않습니다. 이 세 열을 모두 Agent의 입력에 넣으라는 뜻은 아닙니다. <a href="../web/assets/portal/v1.1/39-evaluation-dataset-preview.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

5. **Next → Configure agents → Configure**를 엽니다. **USER** 입력란에 아래 값 **한 개만** 넣습니다.
   {: value="5"}

```text
{{item.query}}
```

<figure class="portal-shot" id="shot-query-only-v1-1">
  <img src="../web/assets/portal/v1.1/12-query-only-mapping.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="평가 생성 화면의 USER 입력란에 item.query만 입력한 매핑">
  <figcaption><strong>USER 입력은 질문 하나뿐입니다.</strong> 저장 전에 위 입력값과 화면을 대조합니다. 정답이나 context를 추가하지 않습니다. <a href="../web/assets/portal/v1.1/12-query-only-mapping.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

`context`나 `ground_truth`를 이 입력란에 덧붙이지 않습니다. Agent가 정답을 미리 읽지 않고, 실제 File search로 정책을 찾아 답해야 합니다. 매핑 단계가 자동으로 생략되어도 **Configure agents**는 직접 확인합니다.

6. **Save**로 매핑 창을 닫고 **Next**로 **Criteria**에 이동합니다. **Judge model**을 **judge-v1-1**로 설정합니다. **Clear selection** 후 **Relevance**, **Task adherence** 두 개만 선택합니다.
   {: value="6"}
7. 먼저 **Relevance**의 설정을 엽니다. 아래 표의 Relevance 열대로 Judge **judge-v1-1**, Threshold **4**와 입력 매핑을 설정합니다.

| 설정 | Relevance | Task adherence |
|---|---|---|
| 포털 결과의 지표명 | Relevance | TaskAdherence |
| Judge deployment | `judge-v1-1` | `judge-v1-1` |
| Threshold | **4** | **1** |
| Probability_threshold | 해당 없음 | **0.5** |
| Query | `{{item.query}}` | `{{item.query}}` |
| Response | `{{sample.output_text}}` | `{{sample.output_text}}` |
| Tool definitions | 해당 없음 | 기본 `{{sample.tool_definitions}}` 유지 |

<figure class="portal-shot" id="shot-relevance-settings-v1-1">
  <img src="../web/assets/portal/v1.1/40-relevance-settings.v1.1.png" width="1038" height="447" loading="lazy" decoding="async" alt="Relevance 설정의 Judge judge-v1-1과 Threshold 4">
  <figcaption><strong>Relevance의 임계값은 4입니다.</strong> Advanced settings에서 Query·Response도 표와 대조합니다. 다음 번호에서 Update로 반영합니다. <a href="../web/assets/portal/v1.1/40-relevance-settings.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

8. **Update**로 Relevance 설정을 반영한 뒤 **Task adherence** 설정을 엽니다. Judge **judge-v1-1**, Threshold **1**, Probability_threshold **0.5**와 표의 입력 매핑을 확인합니다.
   {: value="8"}

**TaskAdherence 주의:** 이진 0/1 지표입니다. 화면의 공통 Threshold 입력칸에 기본값 3이 보여도 **1**로 바꿉니다. Probability_threshold는 숫자 입력칸의 **0.5**를 확인합니다.

<figure class="portal-shot" id="shot-task-adherence-v1-1">
  <img src="../web/assets/portal/v1.1/13-task-adherence-settings.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Task-Adherence 설정의 Judge judge-v1-1, Threshold 1, Probability_threshold 0.5">
  <figcaption><strong>Judge·1·0.5를 각각 확인합니다.</strong> 서로 다른 두 임계값을 혼동하지 않습니다. Advanced settings의 Query와 Response도 위 표와 대조한 뒤 Update 또는 Apply로 반영합니다. <a href="../web/assets/portal/v1.1/13-task-adherence-settings.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

9. **Update / Apply**로 설정을 반영한 뒤 **Criteria** 단계의 **Next**를 선택합니다. 평가기 목록의 다음 페이지 버튼과 혼동하지 않습니다.
   {: value="9"}
10. **Review**에서 이름 `atlas-portal-eval-v1-1`을 입력하고 Agent 버전·데이터·평가기 두 개를 다시 확인합니다.

<figure class="portal-shot" id="shot-baseline-review-v1-1">
  <img src="../web/assets/portal/v1.1/14-baseline-review.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="기준선 Agent 버전과 데이터셋, 두 평가기를 확인하는 Review 화면">
  <figcaption><strong>기준선 버전·데이터·평가기 두 개를 확인합니다.</strong> Review는 제출 전 설정 요약이지 평가 성공이나 점수 화면이 아닙니다. <a href="../web/assets/portal/v1.1/14-baseline-review.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

11. **Submit**을 한 번 선택합니다. 목록에서 상태가 끝날 때까지 기다립니다. 같은 평가를 다시 만들지 않습니다.
    {: value="11"}

**완료 기준:** 평가 정의와 실제 run이 생성되었으며, run에서 문항별 응답·점수 또는 오류를 확인할 수 있습니다. 제출 성공만으로 12문항 평가 성공이라고 판단하지 않습니다.
{: .completion-check}

## 07. 점수보다 답변과 오류 먼저 읽기 {#portal-analysis}

**조작 위치:** **Evaluations → atlas-portal-eval-v1-1**.
{: .step-route}

1. 실행 목록에서 **Target**의 기준선 버전, **Status**, Relevance·TaskAdherence의 통과 건수와 분모를 확인합니다.

<figure class="portal-shot" id="shot-baseline-results-v1-1">
  <img src="../web/assets/portal/v1.1/16-baseline-results.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="기준선 Agent v6의 Partial 상태와 Relevance 7/11, TaskAdherence 8/11 결과">
  <figcaption><strong>Partial과 각 지표의 분모를 먼저 읽습니다.</strong> 이 기준선의 Relevance는 7/11(64%), TaskAdherence는 8/11(73%)입니다. Overall 68%의 15/22는 두 지표의 판정 합계이며 문항 22개를 뜻하지 않습니다. 자신의 실행은 다른 결과가 나올 수 있습니다. <a href="../web/assets/portal/v1.1/16-baseline-results.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

2. 해당 run을 열고 **Detailed metrics**로 이동합니다. 첫 페이지의 **Index 0–9**와 각 행의 점수·오류를 확인합니다.
   {: value="2"}

<figure class="portal-shot" id="shot-baseline-detailed-metrics-v1-1">
  <img src="../web/assets/portal/v1.1/41-baseline-detailed-metrics.v1.1.png" width="1174" height="752" loading="lazy" decoding="async" alt="기준선 Detailed metrics 첫 페이지의 Index 0부터 9, Relevance 실패 행과 Index 9 Error">
  <figcaption><strong>전체 평균 대신 문항별 행을 읽습니다.</strong> 첫 페이지에는 10행과 오른쪽 아래 Next가 있습니다. 대화·추적 식별자 셀만 가렸으며 질문·점수·Error는 그대로입니다. <a href="../web/assets/portal/v1.1/41-baseline-detailed-metrics.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

3. **Error** 열이 있으면 먼저 확인합니다. 오류 없는 페이지에서는 이 열이 표시되지 않을 수 있습니다. 응답 생성 실패와 Judge 채점 실패를 구분합니다.
   {: value="3"}
4. 낮은 **Relevance** 행에서 가로로 스크롤해 `sample.output_text`의 **View JSON**을 엽니다. 질문, 실제 답변, **Relevance.reason**, **TaskAdherence**와 그 이유를 함께 읽고 창을 닫습니다. 지침 준수와 업무상 충분한 답변은 다른 기준입니다.
5. 표 오른쪽 아래 **Next**로 다음 페이지를 엽니다. **Index 10·11**도 확인해 제출한 전체 **12행**의 점수·오류를 빠짐없이 읽습니다.

<figure class="portal-shot" id="shot-baseline-final-cases-v1-1">
  <img src="../web/assets/portal/v1.1/42-baseline-final-cases.v1.1.png" width="1174" height="400" loading="lazy" decoding="async" alt="Detailed metrics 다음 페이지의 Index 10과 11 및 Relevance 2점과 3점">
  <figcaption><strong>나머지 두 행도 평가 대상입니다.</strong> 이 기준선의 Index 10·11은 Relevance 2·3점입니다. 첫 페이지와 합쳐 12문항이지만, 오류 한 건을 제외한 채점 분모는 11입니다. <a href="../web/assets/portal/v1.1/42-baseline-final-cases.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

6. 기준선 버전, 평가 정의, 데이터셋 버전, 두 평가기의 설정, 오류 문항을 자신의 비공개 기록에 남깁니다.
   {: value="6"}

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

**조작 위치:** **Agents → atlas-support-v1-1 → 기준선 버전 → Playground → 왼쪽 아래 Optimize**.
{: .step-route}

첫 소개 화면의 예시 benchmark는 자신의 실습 결과가 아닙니다.

1. **Playground** 왼쪽 아래 **Optimize** 메뉴를 엽니다.

<figure class="portal-shot" id="shot-optimize-agent-menu-v1-1" data-capture-layout="dialog">
  <img src="../web/assets/portal/v1.1/43-optimize-agent-menu.v1.1.png" width="306" height="265" loading="lazy" decoding="async" alt="Optimize 메뉴의 Agent, Cost, Prompt 선택지">
  <figcaption><strong>맨 위 Agent로 진행합니다.</strong> Cost나 Prompt, Instructions 아래의 Improve instructions와는 다른 경로입니다. <a href="../web/assets/portal/v1.1/43-optimize-agent-menu.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

2. **Agent**를 선택합니다. 소개 화면이 나오면 **Optimize my agent**로 진행합니다. **Target**에서 기준선 버전을 확인하고 **Optimization approach → Choose targets**를 선택해 아래처럼 설정합니다.
   {: value="2"}

| 항목 | 설정 |
|---|---|
| Instruction | **선택** |
| Tool description | **선택 해제** |
| Model / Compare across models | **선택 해제 / 끔** |
| Optimization model | **optimizer-v1-1** |
| Max candidates | **1** |
| Evaluation model | **judge-v1-1** |

<figure class="portal-shot" id="shot-optimizer-settings-v1-1">
  <img src="../web/assets/portal/v1.1/17-optimizer-settings.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Instruction만 선택하고 optimizer-v1-1, judge-v1-1, 후보 한 개를 지정한 설정">
  <figcaption><strong>Instruction만 바꾸고 모델·도구는 고정합니다.</strong> 생성 모델·평가 모델·Max candidates 1도 표와 대조합니다. <a href="../web/assets/portal/v1.1/17-optimizer-settings.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

3. **Next → Data source → Select dataset and criteria**를 선택합니다. Generate data나 production traces는 사용하지 않습니다.
   {: value="3"}
4. 오른쪽 **Dataset** 검색란에 `atlas-dev12-v1-1`을 입력합니다. 결과의 이름·버전 `1`을 확인합니다.

<figure class="portal-shot" id="shot-optimizer-dataset-search-v1-1">
  <img src="../web/assets/portal/v1.1/44-optimizer-dataset-search.v1.1.png" width="1148" height="338" loading="lazy" decoding="async" alt="Select dataset and criteria와 atlas-dev12-v1-1 버전 1 검색 결과의 선택 원">
  <figcaption><strong>기준선과 같은 데이터셋 행을 찾습니다.</strong> 그림에서는 아직 오른쪽 행을 선택하지 않아 Next가 비활성입니다. 다음 번호에서 행 앞의 원을 선택합니다. 새 파일이나 자동 생성 데이터는 사용하지 않습니다. <a href="../web/assets/portal/v1.1/44-optimizer-dataset-search.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

5. 해당 데이터셋 행 앞의 **원 → Next**를 선택합니다. **Criteria**의 **Custom only**가 켜져 있으면 끕니다. 검색으로 다음 두 평가기를 선택합니다. 설정 창이 열리면 값을 확인하고 **Apply**합니다.
   {: value="5"}

| Optimizer 화면의 평가기 | 버전 | 설정 |
|---|---|---|
| Relevance-Evaluator | 15 | Threshold **4** |
| Task-Adherence-Evaluator-(Preview) | 18 | Threshold **1**, Probability_threshold **0.5** |

<figure class="portal-shot" id="shot-optimizer-evaluator-selection-v1-1">
  <img src="../web/assets/portal/v1.1/45-optimizer-evaluator-selection.v1.1.png" width="1148" height="287" loading="lazy" decoding="async" alt="Custom only를 끄고 Task-Adherence와 Relevance 두 선택 칩이 표시된 Optimizer Criteria">
  <figcaption><strong>선택된 두 평가기는 목록 위 칩으로 확인합니다.</strong> 검색어가 Relevance여도 위쪽에는 두 개가 남아 있어야 합니다. 다른 평가기를 추가하지 않습니다. <a href="../web/assets/portal/v1.1/45-optimizer-evaluator-selection.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

6. 다른 평가기가 추가되지 않았는지 확인하고 **Next**를 선택합니다.
   {: value="6"}
7. **Review**에서 **Optimization targets: Instruction**, 같은 데이터셋, 같은 Judge, 후보 **1개**를 확인합니다. **Estimated cost**도 읽습니다. 예상치는 실제 청구 금액이나 상한 보장이 아닙니다.

<figure class="portal-shot" id="shot-optimizer-review-v1-1">
  <img src="../web/assets/portal/v1.1/18-optimizer-review.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="Instruction과 동일 데이터셋, Judge, 후보 수를 요약한 Optimizer Review">
  <figcaption><strong>Submit 전에 변경 범위를 다시 확인합니다.</strong> 그림의 Estimated cost는 아직 Estimating cost 상태입니다. 자신의 화면에서 추정이 끝나면 비용을 읽고 승인 범위인지 확인합니다. 추정이 제공되지 않으면 승인된 비용 기준 없이 제출하지 않습니다. <a href="../web/assets/portal/v1.1/18-optimizer-review.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

8. **Submit**을 한 번 선택합니다. 실행 목록의 자동 생성 **Run ID**를 엽니다. 별도 실행 이름 입력란이 없으므로 그 ID를 비공개 기록에 남깁니다.
   {: value="8"}
9. **Additional settings**에서 Instruction·모델·후보 수를 확인하고 실행이 끝날 때까지 기다립니다.
10. **Candidate results**에서 baseline과 후보의 점수를 확인하고 score details를 읽습니다.

<figure class="portal-shot" id="shot-optimizer-results-v1-1">
  <img src="../web/assets/portal/v1.1/19-optimizer-results.v1.1.png" width="1172" height="362" loading="lazy" decoding="async" alt="원본 Optimizer 후보 한 개의 Task-weighted average가 0.625에서 0.781로 상승한 결과 카드">
  <figcaption><strong>실제 Optimizer 원본 후보의 0.625 → 0.781을 확인합니다.</strong> 후보 1개·6m 23s의 별도 실행입니다. 09에서 사람이 보완한 v2의 Relevance·TaskAdherence 통과율과는 다른 측정입니다. 실행 식별자를 제외하도록 결과 카드 영역만 잘랐으며 제품 점수는 바꾸지 않았습니다. <a href="../web/assets/portal/v1.1/19-optimizer-results.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**후보 검토:** 점수가 높아도 정책 숫자·정답을 지침에 통째로 외우게 하거나, 미확인 기능을 확답하거나, 실제 수행하지 않은 일을 완료했다고 주장하면 채택하지 않습니다. 권한 우회와 비밀정보 요청도 허용하지 않습니다. 허용할 변화는 답변 구조·근거 사용·필요한 확인 질문 같은 **일반적인 지침 개선**입니다.

11. 후보의 **Changes / View changes**를 엽니다. 기준선과 원본 후보의 지침을 비교하며 위 검토 기준을 확인합니다.
   {: value="11"}

<figure class="portal-shot" id="shot-review-candidate-v1-1">
  <img src="../web/assets/portal/v1.1/20-review-candidate.v1.1.png" width="1038" height="622" loading="lazy" decoding="async" alt="기준선과 원본 Optimizer 후보의 지침 변경 비교 창">
  <figcaption><strong>Changes 창은 최종 v2가 아니라 원본 후보입니다.</strong> 오른쪽에 정책 예시와 기존 계산·확인 질문 제한이 남아 있는지 읽습니다. 보이는 초록색이나 높은 점수만으로 Promote하지 않습니다. 이 화면을 복사해 지침으로 쓰지 않고 09의 검토수정본과 구분합니다. 개인정보 보호를 위해 변경 비교 창만 잘랐습니다. <a href="../web/assets/portal/v1.1/20-review-candidate.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

12. **Close**로 변경 비교 창을 닫습니다. **Promote candidate**는 누르지 않습니다. 다음 단계에서 검토수정본을 새 버전으로 저장합니다.
   {: value="12"}

Optimizer의 **Task-weighted average (0–1)**는 평가 화면의 개별 통과율과 같은 숫자가 아닙니다. 학습에 사용한 12문항의 점수 상승만으로 일반화·운영 품질을 입증할 수도 없습니다.

**완료 기준:** 실제 후보 지침과 채점 이유를 읽고 보관할 후보가 있는지 판단합니다. 실패하면 오류를 보존합니다. 같은 설정을 유리한 점수가 나올 때까지 재실행하지 않습니다.
{: .completion-check}

## 09. 검토수정본을 새 버전으로 저장하고 비교하기 {#portal-compare}

**조작 위치:** Agent의 **Playground → Instructions → Save**와 기존 평가 정의의 **Add run / Compare runs**.
{: .step-route}

Optimizer 후보에는 평가 문항의 날짜·정답 예시가 그대로 들어갈 수 있습니다. 그런 원본은 점수가 올라도 그대로 승격하지 않습니다. 이 경로에서는 일반적인 답변·검색·라우팅 개선을 반영한 **[지침 v2 · 검토수정본 reviewed.v1.1.txt](../prompts/reviewed.v1.1.txt)**을 사용합니다. **사람이 작성·검토한 보완본이며 Optimizer의 원본 출력이 아닙니다.** 원본에 남은 글자 수·계산 금지·확인 질문 금지 제약도 사람이 수정했습니다. 원본 후보의 점수를 이 수정본의 점수로 인용하거나 개선을 Optimizer 단독 효과로 해석하지 않습니다.

| 비교 조건 | 고정할 값 |
|---|---|
| 질문·참고 자료 | `atlas-dev12-v1-1`, 같은 버전, 전체 12문항 |
| Agent 입력 | `{{item.query}}`만 |
| Agent 모델·정책·도구 | `agent-v1-1`, 같은 File search와 정책 파일 |
| Judge·평가기 | `judge-v1-1`, Relevance 4, TaskAdherence 1 / 0.5 |
| 유일한 의도적 변경 | 검토한 Agent 지침 |

1. Agent의 **Playground → Version**에서 기록한 **기준선 버전**을 엽니다. 원래 FAQ 지침, 모델, File search를 확인합니다.

<figure class="portal-shot" id="shot-baseline-preserved-v1-1">
  <img src="../web/assets/portal/v1.1/25-baseline-preserved.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="기준선 v6의 원래 FAQ 지침과 모델 및 File search를 확인한 화면">
  <figcaption><strong>수정 전 기준선을 먼저 확인합니다.</strong> 녹화의 기준선은 v6입니다. 다음 저장은 새 버전을 만들며, 이 원래 지침과 기존 평가 결과는 그대로 유지합니다. <a href="../web/assets/portal/v1.1/25-baseline-preserved.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

2. **Instructions**를 위 지침 v2 파일의 전체 내용으로 교체하고 **Save**를 선택합니다. **Publish**는 누르지 않습니다.
   {: value="2"}
3. 새 Agent 버전 숫자를 **비교 버전**으로 기록합니다. 지침만 바뀌고 모델 `agent-v1-1`, File search, 정책 파일은 같은지 확인합니다.

<figure class="portal-shot" id="shot-reviewed-agent-v1-1">
  <img src="../web/assets/portal/v1.1/21-reviewed-agent.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="검토수정본을 저장한 Agent v7과 유지된 agent-v1-1 모델 및 File search">
  <figcaption><strong>새 버전에서 바뀐 것은 지침입니다.</strong> 이 실행의 비교 버전은 7이며, 모델과 File search는 유지되어 있습니다. 저장된 화면이지 Publish한 운영 배포가 아닙니다. <a href="../web/assets/portal/v1.1/21-reviewed-agent.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

4. **Evaluations → atlas-portal-eval-v1-1 → Add run**을 선택합니다. 새 평가 정의를 만들지 않습니다.
   {: value="4"}

<figure class="portal-shot" id="shot-add-run-target-version-v1-1">
  <img src="../web/assets/portal/v1.1/46-add-run-target-version.v1.1.png" width="1184" height="264" loading="lazy" decoding="async" alt="Add run의 선택된 atlas-support-v1-1과 아직 Latest available인 Version 드롭다운">
  <figcaption><strong>Version 드롭다운에서 비교 버전을 고정해야 합니다.</strong> 그림은 Add run 진입 직후라 아직 Latest available입니다. 이 기본값을 그대로 제출하지 않습니다. <a href="../web/assets/portal/v1.1/46-add-run-target-version.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

5. **Target**에서 같은 Agent를 선택하고 Version을 **Pin v숫자**로 기록한 비교 버전에 고정합니다. **Latest available**로 두지 않습니다. **Next → Scope: Individual turns → Next**로 진행합니다. **Data → Existing dataset**에서 같은 `atlas-dev12-v1-1`, 버전 `1`을 선택합니다.
   {: value="5"}

<figure class="portal-shot" id="shot-add-run-existing-dataset-v1-1">
  <img src="../web/assets/portal/v1.1/47-add-run-existing-dataset.v1.1.png" width="1184" height="608" loading="lazy" decoding="async" alt="Add run의 Existing dataset에서 다시 선택한 atlas-dev12-v1-1 버전 1">
  <figcaption><strong>이미 등록한 같은 버전을 다시 선택합니다.</strong> Upload new dataset이나 Synthetic generation은 사용하지 않습니다. 미리보기 로드가 끝나 Next가 활성화될 때까지 기다립니다. <a href="../web/assets/portal/v1.1/47-add-run-existing-dataset.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

6. **Next → Configure agents → Configure**를 엽니다. **User prompt**에 `{{item.query}}`만 입력하고, Target이 비교 버전인지 확인합니다.
   {: value="6"}

<figure class="portal-shot" id="shot-add-run-query-only-v1-1">
  <img src="../web/assets/portal/v1.1/22-add-run-query-only.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="기존 평가의 Add run에서 v7을 선택하고 USER에 item.query만 입력한 화면">
  <figcaption><strong>재평가도 query-only입니다.</strong> 왼쪽 Target 카드의 v7과 USER 입력을 함께 확인합니다. 기존 정의를 사용해도 입력 매핑을 생략하지 않습니다. <a href="../web/assets/portal/v1.1/22-add-run-query-only.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

7. **Save → Submit**하고 실행이 끝날 때까지 기다립니다. Judge·평가기는 기존 정의를 재사용합니다.
   {: value="7"}
8. **비교 버전 run**을 열고 **Detailed metrics** 첫 페이지를 확인합니다. 07에서 기록한 기준선의 **같은 Index**와 응답·점수·이유·오류를 대조하고 지연·토큰 사용·평균도 기록합니다.

<figure class="portal-shot" id="shot-reviewed-detailed-metrics-v1-1">
  <img src="../web/assets/portal/v1.1/48-reviewed-detailed-metrics.v1.1.png" width="1174" height="752" loading="lazy" decoding="async" alt="검토수정본 v7의 첫 페이지 통과 행과 여전히 Error인 Index 9">
  <figcaption><strong>정상 행의 개선과 남은 오류를 함께 확인합니다.</strong> 위의 100%는 유효 11문항의 결과입니다. 같은 Index 9의 Error가 사라진 것이 아니며 식별자 셀만 가렸습니다. <a href="../web/assets/portal/v1.1/48-reviewed-detailed-metrics.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

9. **Next**로 마지막 두 행까지 확인합니다. 전체 **12행**을 대조한 뒤 평가 정의의 실행 목록으로 이동합니다. 두 행의 **Target**, 상태, Relevance·TaskAdherence 통과율과 분모를 확인합니다.
   {: value="9"}

<figure class="portal-shot" id="shot-evaluation-runs-v1-1">
  <img src="../web/assets/portal/v1.1/23-evaluation-runs.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="동일 평가 정의에서 Agent v6과 v7의 두 지표 통과율 및 Partial 상태를 비교한 목록">
  <figcaption><strong>두 행의 Target·Partial·분모를 대조합니다.</strong> v6의 64%·73%에서 v7의 100%·100%로 오른 것은 공통 유효 11문항의 관측 통과율입니다. 제출 12문항 전체가 성공한 결과가 아닙니다. <a href="../web/assets/portal/v1.1/23-evaluation-runs.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**이번 녹화의 실제 결과 · 2026-11-04**

| 지표 | 지침 v1 · Agent v6 | 검토한 지침 v2 · Agent v7 |
|---|---|---|
| Relevance 통과율 | **7/11 · 64%** | **11/11 · 100%** |
| TaskAdherence 통과율 | **8/11 · 73%** | **11/11 · 100%** |
| Relevance 평균 | 3.64 | 4.91 |
| TaskAdherence 평균 | 0.73 | 1.00 |
| P50 / P95 응답 지연 | 5.4s / 7.7s | 4.6s / 6.8s |

10. 기준선·비교 run의 **행 왼쪽 체크박스 두 개**를 선택합니다. **2 runs selected**를 확인합니다.
    {: value="10"}

<figure class="portal-shot" id="shot-select-comparison-runs-v1-1">
  <img src="../web/assets/portal/v1.1/49-select-comparison-runs.v1.1.png" width="2348" height="660" loading="lazy" decoding="async" alt="Agent v6과 v7 두 행의 선택된 체크박스와 2 runs selected">
  <figcaption><strong>이름 링크가 아니라 행의 체크박스를 선택합니다.</strong> Target 숫자 6·7과 두 선택 표시를 대조합니다. 두 행 모두 Partial인 사실도 유지됩니다. <a href="../web/assets/portal/v1.1/49-select-comparison-runs.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

11. 목록 위 **Compare runs**가 활성화되면 누릅니다. 통계 화면의 **Baseline**을 처음 기준선 run으로 지정합니다. **자동으로 최신 run이 기준선이 될 수 있습니다.** 이름이 같으면 기록한 평균 점수와 Baseline 열의 값을 대조합니다.
    {: value="11"}

<figure class="portal-shot" id="shot-compare-runs-v1-1">
  <img src="../web/assets/portal/v1.1/24-compare-runs.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="기준선 방향과 평균 점수, Relevance Improved 및 TaskAdherence Inconclusive를 표시한 통계 비교">
  <figcaption><strong>Baseline 방향과 통계 판정을 함께 읽습니다.</strong> 이 실행은 Relevance가 Improved by 1.27, TaskAdherence가 Inconclusive입니다. 두 통과율의 상승을 두 지표 모두의 통계적 유의성으로 해석하지 않습니다. <a href="../web/assets/portal/v1.1/24-compare-runs.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

12. **평균 점수와 통계 판정**을 읽고, 앞서 확인한 오류와 실제 답변을 포함해 아래 기준으로 결론을 기록합니다.
    {: value="12"}

두 run 모두 **12문항 중 같은 Index 9 한 건이 `cyber_policy`로 차단된 Partial**입니다. 위 분모는 공통 유효 문항 **11개**입니다. 통계 화면은 Relevance를 **Improved by 1.27**, TaskAdherence를 **Inconclusive**로 판정했습니다. **두 관측 통과율의 상승은 확인했지만, 전체 12문항의 개선이나 두 지표 모두의 통계적 유의성을 입증한 것은 아닙니다.**

**결론은 셋 중 하나입니다.** 전체 문항이 유효하고 두 품질 지표에 회귀가 없으며 하나 이상이 개선되고 실제 답변도 올바르면 이번 표본의 관측 개선으로 기록합니다. 지표가 같거나 하나라도 악화되면 기준선을 유지하고 원인을 검토합니다. **Partial·누락·제공자 차단이 남으면 전체 개선은 입증되지 않았다고 기록**합니다. Overall 상승이 다른 품질 지표의 하락을 없애 주지는 않습니다. 실습용 비교 버전을 저장한 것과 운영 채택은 다릅니다.

비교를 만들기 위해 정답을 지침에 복사하거나, 실패 문항을 삭제하거나, 기준선 결과를 덮어쓰지 않습니다.

Optimizer 자체의 별도 실행은 후보 **1개**, **6m 23s**였으며 Task-weighted average는 **0.625 → 0.781**이었습니다. 원본에는 정책 날짜·예시와 기존 제약이 남아 있어 그대로 승격하지 않았습니다. 위 표는 그 원본의 점수가 아니라 **사람이 보완한 v2를 같은 평가 정의에서 다시 측정한 결과**입니다. 기본 검색·JSON이 동작하는 기준선에서, v2는 취소/하향의 의도를 묻고 환불 기한을 계산하는 등 실제 답변도 개선했습니다.

**완료 기준:** 같은 조건의 두 run을 실제로 비교했거나, 후보를 채택하지 않은 이유를 남겼습니다. 운영 게시와 통계적 개선 보장은 하지 않습니다.
{: .completion-check}

## 10. 결과 보관과 자원 정리 {#portal-finish}

**조작 위치:** Foundry Portal의 결과 화면과 Azure Portal의 전용 리소스 그룹.
{: .step-route}

1. 재개할 계획이면 프로젝트·Agent 이름, 기준선/비교 버전, 데이터셋 버전, 평가·Optimizer run ID, 오류·판단을 **비공개**로 기록합니다.
2. 결과를 내려받을 때는 포털의 **Download results / Download JSON**을 사용합니다. 다운로드 링크의 서명된 주소, 계정·구독 식별자, 키·토큰을 공개 문서에 넣지 않습니다.
3. Foundry Portal의 **Models**에서 실습에 사용한 배포를 확인합니다. 이 목록이 정리 대상이며, 다시 배포할 필요는 없습니다.

<figure class="portal-shot" id="shot-retained-models-v1-1">
  <img src="../web/assets/portal/v1.1/28-retained-models.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="실습 종료 시 남아 있는 세 모델 역할과 자동 임베딩 배포">
  <figcaption><strong>실습 종료 시 남은 배포를 확인합니다.</strong> 이 데모에는 세 역할과 자동 임베딩이 유지되어 있습니다. 아래에서 보존 또는 승인된 삭제를 결정합니다. <a href="../web/assets/portal/v1.1/28-retained-models.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

4. **Azure Portal 탭 → Resource groups → 자신의 새 그룹 → Refresh**로 이동합니다. 그룹 이름과 실습 자원을 확인합니다.
   {: value="4"}

<figure class="portal-shot" id="shot-retained-group-v1-1">
  <img src="../web/assets/portal/v1.1/27-retained-resource-group.v1.1.png" width="1440" height="1000" loading="lazy" decoding="async" alt="실습 종료 시 Foundry와 Foundry project가 남아 있는 전용 리소스 그룹">
  <figcaption><strong>종료 시 그룹과 두 자원이 남아 있습니다.</strong> 이 상태는 삭제 완료가 아닙니다. 자신의 전용 실습 그룹인지 확인한 뒤 마지막 결정을 진행합니다. <a href="../web/assets/portal/v1.1/27-retained-resource-group.v1.1.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

5. 아래에서 **보존 또는 승인된 삭제 중 하나**를 실행하고 확인하여 실습을 마칩니다.
   {: value="5"}

| 마지막 결정 | 실행과 확인 |
|---|---|
| **보존** | 비용 책임과 다음 검토·삭제일을 기록하고 그룹을 유지합니다. 불필요한 재생성·재평가를 하지 않습니다. |
| **승인된 삭제** | 자신의 전용 그룹에서 **Delete resource group → 그룹 이름 입력 → Delete**를 실행합니다. 삭제 완료 후 **Resource groups → Refresh**에서 그룹이 없어졌는지 확인합니다. 공유·외부 자원을 따로 삭제하지 않습니다. |

이 녹화의 환경은 검토·재개를 위해 **보존**했습니다. 영상이 끝났다고 실제 삭제가 수행된 것은 아닙니다. File search 저장 공간과 모델 사용량 등은 해당 서비스 요금 정책을 확인합니다.

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
