# 좋은 에이전트는 평가에서 시작합니다 · v1 {#좋은-에이전트는-평가에서-시작된다-v1}

<p class="eyebrow">CONTOSO ATLAS CLOUD · 하나의 실습 경로</p>

**Azure 환경을 준비하고, 직접 만든 Agent를 평가·개선한 뒤, 사용한 리소스를 삭제하는 실습입니다.** 처음 사용하는 경우 01부터 진행합니다. 이미 준비된 환경을 받은 경우에도 계정·권한과 인수 정보를 먼저 확인합니다.

Microsoft Foundry는 모델 배포, Agent 버전 관리와 평가를 한 프로젝트에서 다루는 개발 플랫폼입니다. 이 실습에서는 가상의 **Contoso Atlas Cloud 고객지원 Agent**를 만들고, 같은 정책과 질문 12개로 응답을 비교합니다. 여기서 학습은 **평가 결과를 읽고 지침을 개선하는 과정**이며 모델 가중치를 다시 학습시키는 과정은 아닙니다.

<div class="hero-summary" aria-label="실습의 목적과 결과">
<div><strong>실습 목표</strong><span>정책을 검색하는 고객지원 Agent와 실제 응답·평가 이유를 담은 비교 기록을 만듭니다.</span></div>
<div><strong>중요한 이유</strong><span>그럴듯한 답변 하나만으로 품질을 판단하지 않고, 같은 조건의 점수·근거·실패로 개선 여부를 설명합니다.</span></div>
<div><strong>진행 방식</strong><span>환경 준비 → v1 평가 → 약점 분석 → 지침 개선 → 같은 기준의 재평가 → 정리 순서로 진행합니다.</span></div>
<div><strong>완료 산출물</strong><span>실제 실행 ID, 데이터 해시, 개선·유지·보류 이유와 리소스 삭제 또는 보존 인계 기록이 남습니다.</span></div>
</div>

<ol class="learning-path" role="list" aria-label="실습 순서">
<li><a href="#setup"><strong>01</strong> 계정·PC·권한 확인</a></li>
<li><a href="#resources"><strong>02</strong> Foundry 환경 생성</a></li>
<li><a href="#agent"><strong>03</strong> 정책 연결·Agent 생성</a></li>
<li><a href="#start"><strong>04</strong> 데이터셋 등록</a></li>
<li><a href="#prepare"><strong>05</strong> 평가 기준 선택</a></li>
<li><a href="#baseline"><strong>06</strong> Foundry Evaluation 실행</a></li>
<li><a href="#analyze"><strong>07</strong> 점수와 이유 읽기</a></li>
<li><a href="#optimize"><strong>08</strong> Agent Optimizer로 지침 개선</a></li>
<li><a href="#decision"><strong>09</strong> 재평가·v1/v2 비교</a></li>
<li><a href="#cleanup"><strong>10</strong> 결과 보관·리소스 삭제</a></li>
</ol>

공개 벤치마크만 보는 대신 **대표적인 자사 과제와 업무 기준**으로 평가합니다. 합성 Contoso 정책을 사용해 고객 원본 데이터를 공개하지 않고 **평가 → 학습 → 개선 → 재평가**를 경험합니다.

| 실행 위치 | 여기에서 하는 일 |
|---|---|
| [Azure Portal](https://portal.azure.com) | 계정·구독·권한, 실제 리소스 목록과 삭제 범위를 확인합니다. |
| 로컬 터미널 | 실습 파일·가상환경을 준비하고 승인된 생성 명령과 ID 조회 명령을 실행합니다. |
| [Microsoft Foundry](https://ai.azure.com) | 프로젝트·Agent·정책 도구를 확인하고 평가·Optimizer·비교 결과를 읽습니다. |

**가이드 읽는 순서:** 각 단계의 **하는 일·이유·방법**을 먼저 읽고, 명령이나 번호 순서대로 진행합니다. 그림에서는 캡션에 적힌 메뉴·필드를 찾습니다. 마지막 **완료 기준**을 확인한 뒤 다음 단계로 이동하며, 화면을 열었거나 읽음 표시를 했다는 이유만으로 실행 완료로 판단하지 않습니다.

**진행 방식입니다.** 01–03에서 실습 기반을 만들고, 04–09는 Foundry 포털에서 평가·개선을 진행합니다. 명령은 별도 표시가 없으면 저장소의 최상위 폴더에서 실행합니다. `YOUR_...`는 자신의 값으로 교체하는 자리표시자입니다. 리소스 이름과 endpoint는 자신의 계획 파일과 `.env` 값을 사용합니다.

| 시작 전에 확인할 항목 | 안내 |
|---|---|
| 시간 | 처음 준비하는 경우 반나절을 확보합니다. 권한·할당량 승인 대기 시간은 별도입니다. |
| 비용 | 모델·평가·최적화 호출과 Search·로그 보관에 비용이 발생할 수 있습니다. 무료 구독이 모든 모델을 지원한다는 뜻은 아닙니다. |
| 실행 권한 | 직접 생성·정리할 수 있는 전용 실습 환경을 사용합니다. 권한이 없으면 운영자가 해당 단계만 수행하고 인수표를 전달합니다. |
| 이미 준비된 환경 | [운영자 인수표](admin-setup.md#handoff)의 모든 값을 받은 뒤 02–03의 완료 기준을 확인하고 04로 이동합니다. 새 리소스를 중복 생성하지 않습니다. |
| 종료 조건 | 평가 결과를 기록하는 데서 끝나지 않고, 10의 삭제 확인 또는 승인된 보존 인계를 완료합니다. |

**버전 의미:** v1/v2는 Foundry Agent 전체 구성 버전입니다. 같은 모델·도구·출력 형식을 유지하고 지침만 바꿉니다. v1을 약화하거나 측정 전에 개선을 보장하지 않습니다. 새 실습의 v2는 먼저 비교할 후보이며 생성 자체가 채택이나 운영 승인은 아닙니다.

## 01. 계정·PC·권한을 확인합니다 {#setup}

<a id="environment"></a><a id="sdk-prerequisites"></a>

<div class="lab-concept" data-learning-frame="setup">
<p><strong>이 단계에서 하는 일:</strong> 사용할 Azure 구독·권한과 로컬 실행 환경을 확인합니다.</p>
<p><strong>중요한 이유:</strong> 브라우저와 CLI가 다른 계정이나 구독을 사용하면 권한 오류가 나거나 잘못된 환경에 자원을 만들 수 있습니다.</p>
<p><strong>진행 방법·위치:</strong> Azure Portal에서 구독과 접근 권한을 확인한 뒤 터미널에서 도구·로그인·언어 설정을 대조합니다. 아직 Azure 리소스는 생성하지 않습니다.</p>
</div>

### Azure 계정과 구독을 확인합니다 {#setup-account}

1. [Azure Portal](https://portal.azure.com)에 로그인합니다. 계정이 없으면 [Azure 계정 안내](https://azure.microsoft.com/pricing/purchase-options/azure-account)를 따라 본인 또는 조직의 계정을 준비합니다. 조직 계정은 관리자의 구독 접근 승인을 먼저 받습니다.
2. 상단 검색창에 **Subscriptions**를 입력하고 사용할 구독을 엽니다. 포털 상태가 **Active**인지 확인하고 **Subscription ID**와 **Directory/Tenant ID**를 기록합니다. 같은 정상 구독은 CLI에서 **Enabled**로 표시합니다. 구독이 보이지 않으면 우측 상단 계정의 디렉터리·구독 필터를 확인합니다.
3. **Access control (IAM) → Check access**에서 본인의 할당을 확인합니다. 이전 UI에서는 **View my access**로 표시할 수 있습니다. 자동 생성 경로에는 리소스 생성과 역할 할당 권한이 모두 필요합니다. Contributor만으로 역할 할당까지 가능하다고 가정하지 않습니다. [필요 권한과 관리자 요청 방법](admin-setup.md#rbac)을 확인합니다.
4. 실습 비용 한도, 사용 종료 시각, 리소스 삭제 담당자를 정합니다. 권한·구독·비용 승인이 없으면 생성 명령을 실행하지 않습니다. 구독 전체 Owner를 새로 부여하거나 조직 보안 정책을 해제하는 방식으로 해결하지 않습니다.

<figure class="portal-shot" id="portal-subscription-overview" data-capture-scope="shared">
<img src="../web/assets/portal/shared/21-subscription-overview.png" alt="Azure 구독 Overview의 Essentials에서 Subscription ID·Directory·Status·My role을 확인하는 화면입니다." width="1440" height="347" loading="lazy">
<figcaption><strong>구독과 상태를 확인합니다.</strong> Essentials에서 Subscription ID, Directory, Status, My role을 찾습니다. 포털의 <strong>Active</strong>와 CLI의 <strong>Enabled</strong>는 같은 정상 사용 상태를 나타냅니다. <a href="../web/assets/portal/shared/21-subscription-overview.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-check-access" data-capture-scope="shared">
<img src="../web/assets/portal/shared/22-check-access.png" alt="Access control IAM의 Check access에서 활성 역할과 Scope를 확인하는 화면입니다." width="1440" height="850" loading="lazy">
<figcaption><strong>역할 이름과 Scope를 함께 읽습니다.</strong> Access control (IAM) → Check access에서 자신의 활성 할당을 확인합니다. 역할 이름만 보지 않고 적용 범위를 대조하며 필요한 범위보다 큰 권한을 추가하지 않습니다. <a href="../web/assets/portal/shared/22-check-access.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

### 도구와 실습 파일을 준비합니다 {#setup-local}

[Python](https://www.python.org/downloads/) **3.11–3.14**, [Git](https://git-scm.com/downloads), [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)를 설치합니다. 이 안내는 일반 Python 터미널이 아니라 **macOS/Linux 터미널 또는 Windows PowerShell**에서 진행합니다. 설치 뒤 새 터미널을 엽니다.

```bash
git --version
az version
git clone https://github.com/junwoojeong100/foundry-evaluation-labs-v1.git
cd foundry-evaluation-labs-v1
```

이미 내려받았다면 clone을 반복하지 않고 해당 폴더로 이동합니다. GitHub의 **Code → Download ZIP**으로 받은 경우 먼저 압축을 풀고 `pyproject.toml`과 `requirements.lock`이 있는 폴더를 엽니다. HTML 파일 한 개만 내려받으면 코드·데이터·그림이 누락됩니다.

**macOS/Linux에서는 다음을 실행합니다.**

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell에서는 다음을 실행합니다.**

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

PowerShell 실행 정책 때문에 활성화가 차단되면 조직 정책을 변경하지 않습니다. 이후 명령의 `python`을 `.\.venv\Scripts\python.exe`로 바꾸어 실행합니다. 기존 `.venv`가 있다면 다른 작업의 환경인지 확인하고 임의로 덮어쓰지 않습니다.

**가상환경을 준비한 뒤 다음 공통 명령을 실행합니다.**

```bash
python -m pip install -r requirements.lock
python -m lab --help
python scripts/build_datasets.py --language ko --check
```

명령 목록과 데이터 검사 성공을 확인합니다. `ModuleNotFoundError`가 나오면 `python -m pip --version`으로 `.venv`의 Python을 사용하는지 확인합니다. 시스템 Python에 임의로 패키지를 설치하지 않습니다.

### CLI 로그인과 언어를 고정합니다 {#setup-login}

```bash
az login
az account list --query "[].{name:name,id:id,state:state}" -o table
az account set --subscription "YOUR_SUBSCRIPTION_ID"
az account show --query "{user:user.name,tenant:tenantId,subscription:id,state:state}" -o json
```

`YOUR_SUBSCRIPTION_ID`를 앞에서 기록한 ID로 교체합니다. 마지막 출력의 `user`, `tenant`, `subscription`을 포털과 대조하고 이후 계획에 사용할 값으로 기록합니다. 브라우저와 CLI의 로그인은 별개입니다. 다른 디렉터리가 선택됐다면 승인된 디렉터리로 `az login --tenant "YOUR_TENANT_ID"`를 실행합니다.

이 한국어 실습의 환경 이름은 **`lab-ko`**로 사용합니다. 같은 이름의 로컬 계획이 이미 있으면 새로 만들지 않고 원래 기록을 재개합니다. 별도 수업이면 `lab-ko-02`처럼 새 이름을 정하고 이후 모든 경로와 prefix도 함께 바꿉니다.

**macOS/Linux에서는 다음 환경 변수를 지정합니다.**

```bash
export LAB_LANGUAGE=ko
export LAB_ARTIFACTS_DIR="$PWD/.lab/lab-ko/artifacts"
```

**Windows PowerShell에서는 다음 환경 변수를 지정합니다.**

```powershell
$env:LAB_LANGUAGE = "ko"
$env:LAB_ARTIFACTS_DIR = Join-Path (Get-Location).Path ".lab/lab-ko/artifacts"
```

새 터미널을 열 때마다 가상환경 활성화와 이 두 변수를 다시 지정합니다. `LAB_LANGUAGE`를 바꾸면서 기존 실행 폴더를 재사용하지 않습니다. 생성되는 `.env`는 설정 파일이며 `source`나 PowerShell 스크립트로 실행하지 않습니다.

**완료 기준:** 같은 사용자·테넌트·구독을 확인했고, Python 명령과 한국어 데이터 검사가 성공합니다. 문제가 있으면 [환경 오류 해결](troubleshooting.md#environment)을 확인합니다.

<p class="step-next no-print"><a href="#resources" data-next-step>다음: 02. Foundry 환경 생성 →</a></p>

## 02. Foundry 환경을 생성합니다 {#resources}

<a id="first-infrastructure-failure"></a>

<div class="lab-concept" data-learning-frame="resources">
<p><strong>이 단계에서 하는 일:</strong> 전용 리소스 그룹 안에 Foundry 프로젝트·모델·Search·모니터링 기반을 준비합니다.</p>
<p><strong>중요한 이유:</strong> 리소스 그룹은 비용과 정리 범위를 묶고, 프로젝트는 Agent·평가를 구분합니다. 빈 프로젝트 하나만으로 정책 검색까지 준비되지는 않습니다.</p>
<p><strong>진행 방법·위치:</strong> 터미널에서 계획·승인·생성을 순서대로 수행한 뒤 두 포털에서 결과를 대조합니다. 준비된 환경은 새로 만들지 않고 인수 정보만 확인합니다.</p>
</div>

```text
Azure 구독
└─ 전용 실습 리소스 그룹
   ├─ Foundry 리소스
   │  ├─ 역할별 모델 배포 4개
   │  └─ 프로젝트 → Agent·평가·데이터
   ├─ Azure AI Search → 읽기 전용 Contoso 정책 검색
   └─ Application Insights + Log Analytics → 관측·로그
```

프로젝트는 Agent·평가를 담는 작업 공간입니다. 모델 이름은 제품명이며, **배포 이름은 실제 호출할 모델에 붙인 사용자 환경의 이름**입니다. 프로젝트 endpoint와 Azure OpenAI endpoint는 서로 바꾸어 사용하지 않습니다.

### 로컬 생성 계획을 만듭니다 {#resources-plan}

01에서 확인한 세 값을 넣습니다. 이 명령은 `.lab/lab-ko/`에 계획·미승인 승인서 예시만 만들고 Azure를 호출하지 않습니다.

```bash
python -m lab bootstrap plan --subscription "YOUR_SUBSCRIPTION_ID" --tenant "YOUR_TENANT_ID" --expected-user "YOUR_SIGN_IN_NAME" --environment lab-ko --location northcentralus
```

`plan_status: CREATED_LOCAL_ONLY`, `mutations_performed: false`와 `config_path`를 확인합니다. `BLOCKED_AWAITING_APPROVAL`은 아직 비용 승인이 없다는 뜻이며 생성 실패나 Azure 생성 완료가 아닙니다.

| 생성 파일 | 확인할 내용 |
|---|---|
| `.lab/lab-ko/config.json` | 구독·테넌트·사용자, 자동 생성 리소스 이름, 모델·버전·용량입니다. 직접 수정하지 않습니다. |
| `.lab/lab-ko/approval.example.json` | 아직 승인되지 않은 비용·변경 범위입니다. |
| `.lab/lab-ko/manifest.json` | 생성·소유권·중단 상태를 추적하는 기록입니다. 보존합니다. |
| `.lab/lab-ko/.env` | 아직 없습니다. 실제 생성이 완료된 뒤 만들어지는 런타임 설정입니다. |

이 저장소의 기본 생성 지역은 **North Central US (`northcentralus`)**입니다. 기본 배포는 Agent `gpt-6-sol`, Judge `gpt-6-luna`, Optimizer/검색 planner `gpt-5.5`, embedding `text-embedding-3-small`입니다. 정확한 버전·SKU·요청 용량은 [모델 표](admin-setup.md#prepare)와 계획 파일에서 확인합니다. 다른 지역·모델로 조용히 대체하지 않습니다.

### 준비 상태와 비용 승인을 확인합니다 {#resources-approval}

```bash
python -m lab bootstrap preflight --config .lab/lab-ko/config.json
```

`readiness_status: READY`인지 확인합니다. 권한·리소스 공급자 등록·모델 버전·할당량·용량이 막히면 `reason`을 읽고 [생성 오류 대응](troubleshooting.md#provisioning)으로 이동합니다. 아직 승인서가 없으므로 readiness가 READY여도 전체 상태는 승인 대기일 수 있습니다. 지역이나 환경 이름을 바꾸어 반복 생성하지 않습니다.

실제 비용 승인 담당자가 `.lab/lab-ko/approval.example.json`을 편집기에서 열고 **다른 이름으로 저장**하여 `.lab/lab-ko/approval.json`을 만듭니다. 원본 `scope_sha256`, `models`, `retention_days`는 유지합니다. **[승인서 작성표](admin-setup.md#approval)의 모든 필드**를 실제 승인에 맞춰 채웁니다. 특히 승인자, 현재 유효한 시작·만료 시각, 통화·예산, 대기·보관 시간과 리소스 생성·RBAC·Global 처리 동의가 필요합니다.

`approved: true`만 바꾸면 완료되지 않습니다. 예산 숫자는 Azure의 자동 과금 차단 장치가 아니며, 문서의 예시가 사용자의 지출 승인을 대신하지 않습니다.

```bash
python -m lab bootstrap preflight --config .lab/lab-ko/config.json --approval .lab/lab-ko/approval.json
```

**`readiness_status: READY`와 `status: READY_FOR_APPROVED_APPLY`를 모두 확인한 뒤에만 다음 생성 명령을 실행합니다.**

### 승인한 환경을 생성하고 포털에서 확인합니다 {#resources-create}

```bash
python -m lab bootstrap apply --config .lab/lab-ko/config.json --approval .lab/lab-ko/approval.json
python -m lab bootstrap status --config .lab/lab-ko/config.json --approval .lab/lab-ko/approval.json
```

첫 명령은 리소스·모델·연결·리소스 범위 역할을 실제로 생성합니다. 시간이 걸릴 수 있으므로 다른 창에서 같은 `apply`를 실행하지 않습니다. `apply`의 **APPLIED**, `.lab/lab-ko/.env` 생성, `status`의 `phase: succeeded`와 대상 리소스의 존재를 확인합니다. 대기 초과이면 `status`부터 확인하며 [재개 절차](troubleshooting.md#provisioning)를 따릅니다.

1. [Azure Portal](https://portal.azure.com) → **Resource groups**에서 `config.json`의 `names.resource_group`을 검색합니다. 구독·지역·리소스 목록을 확인합니다.
2. [Foundry](https://ai.azure.com)를 열고 **New Foundry**를 사용합니다. **Select a project to continue**가 나타나면 `names.project`와 같은 프로젝트를 선택하고 **Let's go**를 누릅니다. 환영 안내가 나타나면 읽고 **Close**로 닫습니다. 이미 New Foundry라면 좌측 상단 프로젝트 선택을 사용합니다. Classic의 hub 기반 프로젝트와 혼동하지 않습니다.
3. 프로젝트의 **Overview**에서 endpoint를 확인합니다. `.env`의 `AZURE_AI_PROJECT_ENDPOINT`와 같은 `https://계정명.services.ai.azure.com/api/projects/프로젝트명` 형식이어야 합니다.
4. **Models + endpoints** 또는 **Build → Models**에서 `.env`의 `MODEL_DEPLOYMENT`, `JUDGE_DEPLOYMENT`, `OPTIMIZER_DEPLOYMENT`, `EMBEDDING_DEPLOYMENT`에 대응하는 실제 배포를 확인합니다. 메뉴 명칭이 달라지면 [화면 위치 안내](admin-setup.md#prepare)를 참고합니다.

<figure class="portal-shot" id="portal-created-resources">
<img src="../web/assets/portal/23-resource-group.png" alt="리소스 그룹 Overview에서 Foundry·프로젝트·Search·관측 리소스와 배포 상태를 확인하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>생성 계획과 실제 자원을 대조합니다.</strong> 그룹 이름·Location을 확인하고 Resources에서 Foundry, Foundry project, Search, Application Insights, Log Analytics를 찾습니다. Deployments에서는 각 배포의 상태와 실패 원인을 확인합니다. <a href="../web/assets/portal/23-resource-group.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-select-project" data-capture-layout="dialog">
<img src="../web/assets/portal/24-select-project.png" alt="New Foundry에서 사용할 프로젝트를 선택하고 Let's go로 여는 대화상자입니다." width="640" height="474" loading="lazy">
<figcaption><strong>만든 프로젝트를 선택합니다.</strong> 이름을 계획의 <code>names.project</code>와 대조하고 Let's go로 엽니다. 이 화면은 기존 프로젝트 선택이며 추가 생성이 아닙니다. 이미 bootstrap을 완료했다면 Create a new project로 중복 생성하지 않습니다. <a href="../web/assets/portal/24-select-project.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-project-endpoint">
<img src="../web/assets/portal/25-project-overview.png" alt="Foundry 프로젝트 Home의 프로젝트 선택, View deployments, Project endpoint와 Azure OpenAI endpoint 위치입니다." width="1440" height="492" loading="lazy">
<figcaption><strong>프로젝트와 endpoint를 확인합니다.</strong> 좌측 상단 프로젝트 이름과 <strong>Project endpoint</strong>를 자신의 설정과 대조합니다. Azure OpenAI endpoint와 혼동하지 않으며 모델 목록은 View deployments로 엽니다. <a href="../web/assets/portal/25-project-overview.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

```bash
python -m lab --config .lab/lab-ko/.env preflight
```

**완료 기준:** 런타임 preflight가 `PASS`이고, 자신의 프로젝트와 역할별 배포를 확인합니다. 이는 읽기 전용 구성 확인이며 실제 모델 응답 성공은 다음 단계에서 확인합니다.

<p class="step-next no-print"><a href="#agent" data-next-step>다음: 03. 정책 연결·Agent 생성 →</a></p>

## 03. 정책을 연결하고 Agent를 생성합니다 {#agent}

<a id="model-smoke"></a><a id="iq"></a>

<div class="lab-concept" data-learning-frame="agent">
<p><strong>이 단계에서 하는 일:</strong> 합성 정책을 검색하는 읽기 전용 도구와 비교 기준인 v1 Agent를 연결합니다.</p>
<p><strong>중요한 이유:</strong> 모델이 기억으로 답하는 것과 실제 정책을 검색해 답하는 것은 다릅니다. 검색이 사용자 권한으로 성공해도 Agent의 관리 ID 권한은 별도로 확인해야 합니다.</p>
<p><strong>진행 방법·위치:</strong> 터미널에서 모델·검색·Agent를 준비하고 Foundry에서 지침·도구와 실제 응답을 확인합니다. 데이터 전송·호출은 승인된 범위에서 한 번씩 수행합니다.</p>
</div>

### 모델과 정책 검색을 확인합니다 {#agent-knowledge}

```bash
python -m lab --config .lab/lab-ko/.env smoke --run-id model-smoke --confirm
python -m lab --config .lab/lab-ko/.env iq prepare --confirm
python -m lab --config .lab/lab-ko/.env iq probe --confirm
```

첫 명령은 실제 모델 응답을 확인합니다. 두 번째는 [합성 정책 8개](../data/knowledge/documents.json)를 embedding·검색 인덱스·knowledge base·프로젝트 MCP 연결로 준비합니다. 세 번째는 실제 검색을 수행합니다.

`smoke`의 `status: completed`, 지식 준비의 `uploaded_documents: 8`, 검색의 **`status: retrieval_verified`**와 비어 있지 않은 출처를 확인합니다. 생성만 성공한 `created_not_retrieval_tested`는 검색 성공이 아닙니다. Search가 준비되는 동안 오류가 발생하면 기록을 지우지 않고 [검색 오류 해결](troubleshooting.md#knowledge)을 확인합니다.

포털에서도 **Build → Knowledge → Knowledge bases**를 열고 Connection과 생성된 지식 베이스·Knowledge sources를 확인합니다. 목록의 지식 베이스 한 개가 정책 문서 한 개를 뜻하지는 않습니다.

<figure class="portal-shot" id="portal-policy-connection">
<img src="../web/assets/portal/26-knowledge-base.png" alt="Knowledge Foundry IQ에서 Connection·지식 베이스·Knowledge sources·Active 상태를 확인하는 화면입니다." width="1440" height="374" loading="lazy">
<figcaption><strong>정책 연결이 있는지 확인합니다.</strong> Connection 선택과 해당 지식 베이스의 Knowledge sources·Active를 확인합니다. Active는 등록 상태이며 실제 검색 성공은 <code>iq probe</code>로 확인합니다. 무료 검색 배너는 전체 실습이 무료라는 뜻이 아니며, 준비 확인을 위해 요금제 변경 버튼을 누르지 않습니다. <a href="../web/assets/portal/26-knowledge-base.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

### 같은 조건으로 평가할 v1을 만듭니다 {#agent-create}

```bash
python -m lab --config .lab/lab-ko/.env native-agent --version 1 --confirm
```

이 명령은 `prompts/baseline.txt`, 방금 확인한 정책 도구, 엄격한 네 필드 JSON 형식으로 **`lab-ko-iq` 버전 `1`**을 만듭니다. 출력의 `agent_name`, `version`, `receipt`를 기록합니다. 같은 소유 환경·동일 구성이면 기존 v1을 재사용하며, 이름만 같은 다른 Agent를 인수하거나 v3를 만들지 않습니다.

<figure class="portal-shot" id="portal-agent-configuration">
<img src="../web/assets/portal/27-agent-configuration.png" alt="Agent Playground에서 Version·Model·Instructions·Knowledge와 Chat을 확인하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>버전·지침·Knowledge를 확인합니다.</strong> 위쪽 Version을 1로 선택하고 왼쪽 Model·Instructions와 아래쪽 Knowledge를 확인합니다. 정책 MCP 연결은 Knowledge에 표시되며 오른쪽 Chat에서 질문을 입력합니다. <a href="../web/assets/portal/27-agent-configuration.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

포털에서 **Build → Agents → lab-ko-iq → 버전 1**을 엽니다. 표시 이름은 명령 출력이 기준입니다. **Test/Playground**에서 다음 질문을 한 번 보냅니다.

> 2026년 9월에 처음 월 구독을 결제했습니다. 환불 신청 조건이 궁금합니다.

답변에 `answer`, `citations`, `route`, `needs_human`이 있는지 확인하고, 실행 상세에서 **`knowledge_base_retrieve`의 실제 호출·응답**을 확인합니다. `ATLAS-*` 정책 ID와 답변 근거를 대조합니다. 직접 검색이 성공했어도 Agent의 관리 ID 권한이 다르면 도구 호출은 실패할 수 있습니다.

**완료 기준:** 자신의 v1이 실제 질문에 응답하고 정책 도구 호출이 확인됩니다. JSON 형식이나 연결 성공만으로 품질이 검증됐다고 표시하지 않습니다. 다른 구성 요소를 수정하는 실습은 추가하지 않으며 다음 단계부터 관리형 평가에 집중합니다.

<p class="step-next no-print"><a href="#start" data-next-step>다음: 04. 데이터셋 등록 →</a></p>

## 04. 데이터셋을 등록합니다 {#start}

<a id="demo"></a><a id="understand"></a><a id="data"></a>

<div class="lab-concept" data-learning-frame="start">
<p><strong>이 단계에서 하는 일:</strong> 같은 질문으로 비교할 수 있도록 한국어 dev12 파일을 한 번 등록합니다.</p>
<p><strong>중요한 이유:</strong> 질문이나 참고 답변이 달라지면 지침 변경의 효과를 분리할 수 없습니다. 참고 답변을 Agent에게 미리 주어도 공정한 비교가 아닙니다.</p>
<p><strong>진행 방법·위치:</strong> 터미널에서 행 수·해시를 확인하고 Foundry 평가 마법사에서 원본 파일을 등록하거나 같은 버전을 재사용합니다.</p>
</div>

**[data/optimizer/dev.jsonl](../data/optimizer/dev.jsonl)**의 **JSONL 12행**을 변경 없이 사용합니다. JSONL은 한 줄에 JSON 객체 하나가 있는 파일입니다. Excel·CSV·JSON 배열로 변환하지 않습니다.

```bash
python -c "import hashlib,pathlib; p=pathlib.Path('data/optimizer/dev.jsonl'); print('rows =',len(p.read_text(encoding='utf-8').splitlines())); print('sha256 =',hashlib.sha256(p.read_bytes()).hexdigest())"
```

`rows = 12`와 SHA-256 값을 기록합니다. 이후 기준선·최적화·재평가에서 같은 파일과 등록 버전을 사용합니다.

| 열 | 형식 | 용도 |
|---|---|---|
| `query` | 문자열 | Agent에 보내는 유일한 입력 |
| `context` | 문자열 | 지원 평가기와 사례 검토용 정책 참고 자료 |
| `ground_truth` | JSON 문자열 | 구조화 참고 답변이며 생성 프롬프트가 아닙니다. |

12행 전체, 등록·버전과 SHA-256을 기록합니다. 기준선·최적화·재평가에서 같은 바이트를 유지합니다. 원본의 나머지 분할은 이번 필수 실습에 포함하지 않습니다.

응답은 정확히 `answer`, `citations`, `route`, `needs_human`입니다. 한국어 실습의 answer는 한국어, 인용은 근거 정책 ID, route는 `answer/clarify/escalate/refuse`, 불리언 needs_human은 `escalate`일 때만 true입니다. Agent는 제출·환불·삭제·권한 부여를 실제 수행하지 않습니다.

**Foundry New experience → Build → Evaluations → Create → Create new evaluation**을 엽니다. 대상 유형 **Agent**에서 앞에서 만든 **`lab-ko-iq`**를 선택하고 기준선을 **v1로 명시 고정**한 뒤 대상 한 개가 체크됐는지 확인합니다. 최신이 실제 v1일 때만 **Pin currently latest**를 사용하며 버전 변경으로 해제된 체크박스는 다시 선택합니다.

**Individual turns**, **One time**을 선택합니다. 새 프로젝트에서는 **Upload new dataset → Browse**에서 저장소의 `data/optimizer/dev.jsonl`을 고릅니다. 데이터셋 이름은 **`lab-ko-dev12`**, 첫 버전은 **`1`**로 지정하고 업로드·등록이 끝날 때까지 기다립니다. 이미 등록되어 있으면 **Existing dataset**에서 그 이름과 버전을 재사용합니다. 미리 보기가 5행이어도 전체는 12행입니다.

<figure class="portal-shot" id="portal-evaluation-dataset">
<img src="../web/assets/portal/15-evaluation-dataset.png" alt="Foundry 평가의 데이터셋 선택과 query·context·ground_truth 열 미리 보기입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>한국어 데이터셋을 선택합니다.</strong> 등록 이름·버전을 원본과 대조하고 query·context·ground_truth 열을 확인합니다. 5행 미리 보기를 전체 건수로 해석하지 않으며 원본은 12행이어야 합니다. <a href="../web/assets/portal/15-evaluation-dataset.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**완료 기준:** 명시적 v1과 변경 없는 12행 데이터셋을 선택하고 건수·버전·해시를 기록했습니다. [데이터 계약](../data/README.md#schema).

<p class="step-next no-print"><a href="#prepare" data-next-step>다음: 05. 평가 기준 선택 →</a></p>

## 05. 평가 기준을 선택합니다 {#prepare}

<a id="calibration"></a>

<div class="lab-concept" data-learning-frame="prepare">
<p><strong>이 단계에서 하는 일:</strong> Relevance·TaskAdherence와 실제 Judge 배포를 선택합니다.</p>
<p><strong>중요한 이유:</strong> 점수의 척도·통과 기준·입력 매핑을 먼저 정해야 결과를 본 뒤 기준을 바꾸는 일을 피할 수 있습니다. 두 평가기는 척도가 서로 다릅니다.</p>
<p><strong>진행 방법·위치:</strong> Foundry의 Criteria에서 평가기별 설정을 열고 임계값과 Judge를 확인합니다. Agent에는 query만 전달합니다.</p>
</div>

**Configure agents**의 custom prompt override는 비워 둡니다. 입력은 **`{{item.query}}`만**이며 context·ground_truth를 붙이지 않습니다. 필드 매핑 화면이 나타나면 query → query를 사용합니다.

관리형 평가자는 정확히 두 개만 남깁니다.

| 평가기 | 의미 | 설정 |
|---|---|---|
| Relevance | 질문에 관련된 답변인지, **1–5점** | **Threshold 4** |
| TaskAdherence | 과제 지시를 따르는지, **이진 0/1 Pass/Fail** | **통과 1**이며 임계값 4가 아닙니다. |

**Criteria → Add evaluators**에서 두 평가기를 선택합니다. 각 행의 설정을 열어 임계값을 입력하고 **Apply**합니다. **Evaluation model/Judge**에는 자신의 `.env`에 기록된 `JUDGE_DEPLOYMENT` 값을 선택합니다. Agent 배포나 Optimizer 배포와 혼동하지 않습니다.

서비스 생성 매핑을 유지합니다. Relevance는 `response={{sample.output_text}}`, TaskAdherence는 `response={{sample.output_items}}`입니다. 이전 UI 값으로 덮어쓰지 말고 정의의 Raw JSON을 확인합니다.

| 역할 | 모델·버전 | 배포 |
|---|---|---|
| Agent | **gpt-6-sol / 2026-09-22** | 자신의 `MODEL_DEPLOYMENT` 값입니다. |
| 평가 Judge | **gpt-6-luna / 2026-09-22** | 자신의 `JUDGE_DEPLOYMENT` 값입니다. |
| Optimizer 생성 | **gpt-5.5 / 2026-04-24** | 자신의 `OPTIMIZER_DEPLOYMENT` 값입니다. |

Agent·Judge·Optimizer는 역할별 지원 모델이 다릅니다. [Optimizer 지원 목록](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)을 확인하고 각 역할에 준비한 배포를 선택합니다.

<figure class="portal-shot" id="portal-evaluation-criteria">
<img src="../web/assets/portal/16-evaluation-criteria.png" alt="평가 Criteria에서 Relevance·TaskAdherence와 Judge 배포를 설정하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>두 평가기와 Judge를 구분합니다.</strong> Relevance 임계값은 4, TaskAdherence 통과 기준은 1로 설정합니다. Judge는 자신의 <code>JUDGE_DEPLOYMENT</code>에 해당하는 배포를 선택합니다. <a href="../web/assets/portal/16-evaluation-criteria.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**완료 기준:** 두 평가기 척도·임계값·매핑·실제 Judge를 기록했습니다. 오래된 로컬 환경 기본값이 아니라 저장된 원격 정의가 Judge를 결정합니다.

<p class="step-next no-print"><a href="#baseline" data-next-step>다음: 06. Foundry Evaluation 실행 →</a></p>

## 06. Foundry Evaluation을 실행합니다 {#baseline}

<div class="lab-concept" data-learning-frame="baseline">
<p><strong>이 단계에서 하는 일:</strong> 고정된 v1의 실제 답변을 생성하고 관리형 평가 점수·이유를 수집합니다.</p>
<p><strong>중요한 이유:</strong> 이후 후보와 비교할 출발점이 필요합니다. Completed는 처리가 끝났다는 뜻이지 모든 답변이 정확하다는 뜻은 아닙니다.</p>
<p><strong>진행 방법·위치:</strong> Foundry에서 검토 후 한 번 제출하고 전체 12건을 확인합니다. 터미널의 읽기 전용 조회로 실제 evaluation ID와 run ID를 기록합니다.</p>
</div>

**v1 + 원본 dev12 + query 전용 입력 + 두 평가기 + 자신의 Luna Judge**를 검토합니다. 새 평가 이름은 **`lab-ko-learning-loop`**, 기준선 run 이름을 지정할 수 있으면 **`baseline-v1`**로 입력합니다. 준비된 수업은 운영자가 지정한 이름을 사용합니다. 기준선 run이 이미 완료되어 있으면 다시 제출하지 않고 해당 결과를 사용합니다.

새 승인 수업은 **Review → Submit**으로 한 번 제출하고 실제 evaluation ID·run ID를 기록합니다. 완료를 기다리고 오류·누락까지 전체 12건을 확인합니다. 초안 구성·HTTP 생성 응답·모델 연결 확인이 평가 완료를 뜻하지 않습니다.

<figure class="portal-shot" id="portal-evaluation-review">
<img src="../web/assets/portal/17-evaluation-review.png" alt="Foundry 평가 Review에서 Agent·버전·데이터셋·평가기 설정을 검토하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>Submit 전에 설정을 검토합니다.</strong> Agent 버전 1, 같은 dev12, query 전용 입력, 두 평가기와 Judge가 맞는지 확인합니다. 승인된 범위에서 한 번 제출한 뒤 run 상태를 확인합니다. <a href="../web/assets/portal/17-evaluation-review.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**Evaluations → 방금 지정한 평가 이름 → Evaluation runs → 기준선 run**을 엽니다. 상태가 Running이면 해당 run을 새로고침하며 기다립니다. 30분이 지나도 끝나지 않으면 현재 상태·오류를 기록하고 강사에게 전달합니다. 기다림을 중단해도 원격 작업은 자동 취소되지 않습니다.

다음 **읽기 전용 명령**으로 이름이 같은 평가의 실제 ID·run 목록을 확인합니다. 이름이 다르면 `--name`을 자신이 입력한 정확한 이름으로 바꿉니다.

```bash
python -m lab --config .lab/lab-ko/.env native-evals --name lab-ko-learning-loop
```

출력의 `evaluation_id`와 **`agent_version: "1"`, `status: completed`인 run의 `run_id`**를 기록합니다. evaluation ID는 `eval_...`, run ID는 `evalrun_...` 형태이며 둘은 다릅니다. 같은 이름의 평가가 여러 개면 포털의 생성 시각·Agent·run을 대조하여 자신의 실행을 선택합니다. 이 명령은 새 평가를 제출하지 않습니다.

**완료 기준:** 실제 Foundry run이 Completed이고 결과 12건을 확인할 수 있습니다. `result_counts`의 오류·실패도 기록합니다. 실패·부분 실행을 그대로 보존하며 관리형 Evaluation을 자체 로컬 Judge로 대신하지 않습니다.

<p class="step-next no-print"><a href="#analyze" data-next-step>다음: 07. 점수와 이유 읽기 →</a></p>

## 07. 점수와 이유를 읽습니다 {#analyze}

<a id="score-rubric"></a><a id="worked-evaluation"></a>

<div class="lab-concept" data-learning-frame="analyze">
<p><strong>이 단계에서 하는 일:</strong> 점수 뒤의 실제 답변과 평가 이유를 정책 근거에 연결합니다.</p>
<p><strong>중요한 이유:</strong> 평균만 보면 특정 날짜·인용·분류 오류가 가려집니다. 무엇이 잘못됐는지 설명해야 바꿀 지침도 정할 수 있습니다.</p>
<p><strong>진행 방법·위치:</strong> Foundry의 상세 지표·User view와 원본 정책을 나란히 읽고 notes.md에 개선 가설과 유지할 행동을 기록합니다.</p>
</div>

요약과 **Detailed metrics result**의 **`Relevance.reason`**, **`TaskAdherence.reason`**을 읽습니다. `conversation_id → User view`는 실제 질문·응답이며 인라인 Judge 이유 패널이 아닙니다.

실패 또는 최저점 사례와 잘한 사례를 골라 **질문 → 실제 응답 → 점수·이유 → 정책·참고 답변**을 연결합니다. 실패가 없으면 그 사실을 말하며 사례를 만들려고 기준선을 약화하지 않습니다.

<figure class="portal-shot" id="portal-evaluation">
<img src="../web/assets/portal/11-evaluation-results.png" alt="Foundry 평가 결과의 요약 점수와 질문별 상세 지표를 확인하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>질문별 점수와 이유를 읽습니다.</strong> 요약의 통과·실패·오류 건수를 확인하고 Detailed metrics result에서 Relevance.reason과 TaskAdherence.reason을 읽습니다. 평균만 보지 않고 개별 사례를 확인합니다. <a href="../web/assets/portal/11-evaluation-results.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

Relevance 4/5를 정확도 80%로 해석하지 않습니다. TaskAdherence 1은 통과이지 낮은 5점 척도 점수가 아닙니다. 누락은 0점이나 성공 행이 아니며 범용 평가기가 모든 업무 규칙을 인증하지는 않습니다.

<figure class="portal-shot" id="portal-evaluation-case">
<img src="../web/assets/portal/19-evaluation-case.png" alt="User view에서 질문과 Agent의 JSON 응답을 나란히 확인하는 화면입니다." width="1440" height="440" loading="lazy">
<figcaption><strong>응답을 정책과 대조합니다.</strong> User view에서 질문과 JSON 응답을 읽고 정책의 날짜·조건·인용과 비교합니다. 채점 이유는 Detailed metrics result로 돌아가 확인하며 오류가 있는 답변을 정답으로 사용하지 않습니다. <a href="../web/assets/portal/19-evaluation-case.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

날짜 경계 오류, 불필요한 가정, 정책 ID 대신 숫자 검색 ID, 사람 검토 분류 오류, 실행 완료 주장과 근거 없는 확신을 확인합니다. 정직한 불확실성을 높은 점수를 위한 허위 사실로 바꾸지 않습니다.

편집기에서 `.lab/lab-ko/notes.md`를 만들고 다음 표를 자신의 결과로 채웁니다. 원본 응답·이유는 별도 원본 파일로 보관하며 표에는 식별 가능한 run·행과 짧은 관측을 남깁니다.

| 기록 항목 | 작성 방법 |
|---|---|
| 기준선 | 실제 evaluation ID, run ID, Agent 버전, 데이터 해시를 기록합니다. |
| 평가 결과 | 전체 12건 중 지표별 통과·실패·오류 건수를 기록합니다. |
| 문제 사례 | 질문, 실제 답변에서 문제가 되는 문장, 평가 이유, 해당 정책 ID를 기록합니다. |
| 개선 가설 | 예를 들어 날짜 경계를 빠뜨렸다면 발효일·포함 경계를 먼저 확인하도록 지침을 보완합니다. 정답 자체를 넣지 않습니다. |
| 유지할 행동 | 이미 잘하는 근거 인용·불확실성 표현·실행 경계를 기록합니다. |

<p class="share-checkpoint" id="share-baseline"><strong>공유:</strong> 실제 run ID·지표별 척도·통과 건수와 문제 응답을 제시하고 어떤 지침 행동을 개선할지 설명합니다.</p>

**완료 기준:** 평균만이 아니라 실제 약점과 근거 있는 개선 가설을 설명할 수 있습니다.

<p class="step-next no-print"><a href="#optimize" data-next-step>다음: 08. Agent Optimizer로 지침 개선 →</a></p>

## 08. Agent Optimizer로 지침을 개선합니다 {#optimize}

<a id="tune"></a>

<div class="lab-concept" data-learning-frame="optimize">
<p><strong>이 단계에서 하는 일:</strong> Agent Optimizer로 지침 개선 후보를 만들고 변경 내용을 검토합니다.</p>
<p><strong>중요한 이유:</strong> 후보 생성은 개선을 보장하지 않습니다. 내부 순위가 높아도 정책을 꾸미거나 도구·모델 조건을 바꿨다면 그대로 채택할 수 없습니다.</p>
<p><strong>진행 방법·위치:</strong> Foundry에서 Instruction only로 실행하고 View changes를 읽습니다. 검토한 지침 전체와 실제 출처를 비공개 파일에 보관합니다.</p>
</div>

**Build → Agents → lab-ko-iq → Optimize Preview/Optimize → Agent**를 엽니다. Cost가 아닙니다. 새 작업에서는 **Create an optimization run** 또는 **Create optimization run**을 선택합니다. Preview 제공 여부와 모델 지원이 구독별로 다르면 [Optimizer 오류 해결](troubleshooting.md#optimizer)을 확인합니다.

| 설정 | 선택 |
|---|---|
| Agent version | 명시적 기준선 **1** |
| Choose targets | **Instruction only**, Model·Tool description 끄기 |
| Max candidates | 운영자 승인 한도. 이번 작업은 최대 **2**이며 정식 버전 수와 다름 |
| Optimization model | 자신의 `OPTIMIZER_DEPLOYMENT` / gpt-5.5 |
| Evaluation model | 자신의 `JUDGE_DEPLOYMENT` / gpt-6-luna |
| Dataset | 같은 언어의 등록 dev12·같은 버전 |
| Criteria | Relevance 4, TaskAdherence 이진 통과 1 |

<figure class="portal-shot" id="portal-optimizer-target">
<img src="../web/assets/portal/07-optimizer-target.png" alt="Agent Optimizer에서 기준선 버전·Instruction only·후보 수·모델 역할을 선택하는 화면입니다." width="1210" height="968" loading="lazy">
<figcaption><strong>최적화 범위와 모델 역할을 구분합니다.</strong> 기준선 버전 1과 Instruction only를 선택하고 후보 수를 승인 한도 안으로 설정합니다. Optimization model과 Evaluation model에는 각 역할에 준비한 배포를 지정합니다. <a href="../web/assets/portal/07-optimizer-target.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

Criteria가 **No custom evaluators available**이면 **Custom only OFF** 또는 **View built-in evaluators**를 선택합니다. 각 기본 평가기의 임계값을 설정하고 Apply합니다. 필터를 우회하려고 다른 평가기를 만들지 않습니다.

<figure class="portal-shot" id="portal-optimizer-data">
<img src="../web/assets/portal/08-optimizer-dataset.png" alt="Agent Optimizer에서 등록된 데이터셋을 선택하는 목록입니다." width="1210" height="968" loading="lazy">
<figcaption><strong>같은 한국어 데이터를 재사용합니다.</strong> 기준선 평가에 사용한 dev12와 같은 등록 버전을 선택하고 12행 전체를 사용합니다. 파일을 수정하거나 새로 생성하면 비교 조건이 달라집니다. <a href="../web/assets/portal/08-optimizer-dataset.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**Review**에서 Agent·버전·데이터셋·평가기와 예상 비용을 확인한 뒤 승인된 비용 범위에서 한 번 **Submit**합니다. 예상 비용은 청구 상한이 아닙니다. **Optimization runs**의 해당 작업에서 최대 60분 기다린 뒤 실제 상태를 남깁니다. 재개 시 기존 job ID를 사용합니다. 작업 하나에도 여러 내부 호출이 포함됩니다.

원본·후보 결과와 **View changes**를 읽습니다. 내부 **0–1 순위**는 별도 관리형 Evaluation 평균·통과율과 다릅니다. 모델·도구·추론·출력 스키마를 유지하며 함수 도구 export가 비었다고 MCP 정책 연결을 제거하지 않습니다.

<figure class="portal-shot" id="portal-optimizer-results">
<img src="../web/assets/portal/09-optimizer-results.png" alt="Agent Optimizer 결과에서 기준선과 후보별 점수·순위를 비교하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>순위뿐 아니라 후보를 확인합니다.</strong> 기준선과 후보의 평가기별 점수를 비교하고 지침 변경 내용을 검토합니다. 타당한 개선 후보가 없으면 v1을 유지하고 그 이유를 기록합니다. <a href="../web/assets/portal/09-optimizer-results.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-optimizer-diff">
<img src="../web/assets/portal/10-optimizer-changes.png" alt="View changes에서 기준선과 후보 지침의 차이를 확인하는 대화상자입니다." width="1038" height="622" loading="lazy">
<figcaption><strong>지침의 차이를 읽습니다.</strong> View changes에서 어떤 응답 행동이 바뀌는지 확인합니다. 허위 정책·근거 없는 확신·지침 외 설정 변경을 거부하며, 길이보다 내용과 효과를 검토합니다. <a href="../web/assets/portal/10-optimizer-changes.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**후보를 다음 단계로 가져옵니다.** 결과의 후보를 선택하고 **View changes**에서 변경 후의 지침 전체를 복사합니다. 편집기에서 `.lab/lab-ko/candidate.txt`에 UTF-8 일반 텍스트로 저장합니다. diff의 `+`·`-`, 화면 설명, 평가 점수는 넣지 않습니다. 직접 수정한 부분과 변경 이유는 `notes.md`에 기록합니다. 다음 단계에는 이 파일을 사용하고 저장소의 `prompts/candidate.txt`로 대체하지 않습니다.

**v3·v4 등 정식 버전을 계속 만들지 않습니다.** 다음 단계의 CLI로 v2를 한 번 생성하여 비교하므로 **Promote candidate와 CLI 생성을 둘 다 실행하지 않습니다.** 새 버전 생성과 운영용 게시·활성화 승인은 다릅니다.

<p class="share-checkpoint" id="share-optimizer"><strong>공유:</strong> 검토한 후보를 제시하고 달라진 지침 행동과 개선·회귀 가능성을 설명합니다.</p>

**완료 기준:** 실제 job/candidate ID, 검토한 지침 파일과 변경 이유를 기록합니다. 유지할 후보가 없으면 “v1 유지·개선 미관측”으로 기록하고 10으로 이동합니다. 개선을 만들기 위해 같은 작업을 반복하지 않습니다.

<p class="step-next no-print"><a href="#decision" data-next-step>다음: 09. 재평가·v1/v2 비교 →</a></p>

## 09. 재평가하고 v1/v2를 비교합니다 {#decision}

<a id="review"></a><a id="operate"></a>

<div class="lab-concept" data-learning-frame="decision">
<p><strong>이 단계에서 하는 일:</strong> 지침만 다른 후보를 같은 정의로 재평가하고 v1 유지·v2 채택·판단 보류 중 하나를 기록합니다.</p>
<p><strong>중요한 이유:</strong> 버전 이름이 v2라는 사실은 개선 근거가 아닙니다. 품질뿐 아니라 실제 오류, 지연·토큰 증가와 통계적 불확실성도 함께 봐야 합니다.</p>
<p><strong>진행 방법·위치:</strong> 터미널에서 명시적 v2와 같은 평가 정의의 run을 준비한 뒤 Foundry의 Compare runs에서 전체 사례를 비교합니다. 운영에는 게시하지 않습니다.</p>
</div>

모델·도구·데이터·평가기·Judge를 유지한 채 검토한 파일로 같은 Agent의 v2를 한 번 생성합니다. v1은 보존합니다.

```bash
python -m lab --config .lab/lab-ko/.env native-agent --version 2 --prompt .lab/lab-ko/candidate.txt --confirm
```

`agent_name: lab-ko-iq`, `version: "2"`를 확인합니다. 다른 내용의 v2가 이미 있거나 모델 배포가 바뀌었으면 중단하고 기존 기록을 보존합니다. 새 버전이 있다는 사실만으로 개선이 입증되지 않습니다.

**같은 Foundry 평가 정의**에 후보 run을 추가합니다. 아래 Azure AI Projects/OpenAI Evals helper는 기준선의 데이터와 평가기를 재사용하여 관리형 평가를 실행합니다.

| 자리표시자 | 실제 값을 찾는 곳 |
|---|---|
| `YOUR_PROJECT_ENDPOINT` | `.lab/lab-ko/.env`의 `AZURE_AI_PROJECT_ENDPOINT` 값입니다. |
| `YOUR_SUBSCRIPTION_ID` | 01의 구독 ID 또는 같은 `.env`의 `AZURE_SUBSCRIPTION_ID` 값입니다. |
| `YOUR_EVALUATION_ID` | 06의 `native-evals` 출력에서 선택한 `evaluation_id`입니다. |
| `YOUR_BASELINE_RUN_ID` | 같은 평가에서 완료된 버전 1의 `run_id`입니다. Optimizer job ID가 아닙니다. |

네 값을 교체하고 다음 한 줄 명령을 실행합니다. 새 run 제출에는 비용이 발생합니다.

```bash
python scripts/add_foundry_eval_run.py --endpoint "YOUR_PROJECT_ENDPOINT" --subscription "YOUR_SUBSCRIPTION_ID" --evaluation "YOUR_EVALUATION_ID" --baseline "YOUR_BASELINE_RUN_ID" --version 2 --name candidate-v2 --out .lab/lab-ko/artifacts/foundry-evaluations/candidate-v2.json
```

`status: completed`와 전체 12건을 확인합니다. 기본 대기 30분을 넘으면 종료 코드 2와 Still running 안내가 나옵니다. receipt에 run ID가 있는 경우 **같은 명령·같은 `--out`**으로 수집을 재개합니다. run ID가 없는 결과 불명 상태나 같은 이름의 원격 run이 있으면 [중복 제출 방지 절차](troubleshooting.md#evaluation)를 따릅니다. 파일을 삭제하거나 이름을 바꾸어 다시 제출하지 않습니다.

helper는 임계값·Judge·매핑과 각 결과 행의 Agent 버전·지침을 확인합니다.

**Evaluation runs**에서 두 행을 선택하고 **Compare runs**를 엽니다. **Baseline을 v1으로 명시 선택**하며 행 선택 순서 때문에 비교 방향이 바뀌지 않게 합니다.

<figure class="portal-shot" id="portal-evaluation-comparison">
<img src="../web/assets/portal/20-evaluation-comparison.png" alt="Compare runs에서 기준선과 후보의 점수·평균·통계 결과를 비교하는 화면입니다." width="1440" height="520" loading="lazy">
<figcaption><strong>비교 방향과 결과를 함께 확인합니다.</strong> Baseline을 v1으로 선택하고 두 run의 점수·통과 건수·통계 결과를 비교합니다. Inconclusive는 차이가 입증되지 않았다는 뜻이며 동등성의 증거로 해석하지 않습니다. <a href="../web/assets/portal/20-evaluation-comparison.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

12건 전체의 응답·점수·이유를 나란히 비교합니다. 전체 기준 통과와 각 지표의 통과 건수·평균이 낮아지지 않고 하나 이상이 명확히 개선되어야 합니다. 사실·분류·응답 형식도 확인하며 지연·토큰·통계 결과를 함께 기록합니다.

<p class="share-checkpoint" id="share-optimized"><strong>결과 설명:</strong> 실제 개선, 같은 평가 기준, 회귀와 남은 불확실성을 설명합니다. 관측된 개선이 향후 모든 확률적 실행의 개선을 보장하지는 않습니다.</p>

`notes.md`에 v1/v2의 지표별 통과 건수·평균, 오류, 지연·토큰, 통계 결과와 최종 판단을 나란히 기록합니다. 개선 조건을 만족하지 않으면 **v1 유지 또는 판단 보류**로 기록합니다. 범용 평가가 통과했어도 실제 정책 오류가 있으면 채택하지 않습니다.

**완료 기준:** 실제 두 run ID와 같은 조건의 전체 비교, 채택·유지·보류 이유를 기록합니다. 정식 버전을 누적하지 않습니다. 운영 승인·독립적 일반화는 별개이며 dev12 실습으로 부여되지 않습니다.

<p class="step-next no-print"><a href="#cleanup" data-next-step>다음: 10. 결과 보관·리소스 삭제 →</a></p>

## 10. 결과를 보관하고 리소스를 삭제합니다 {#cleanup}

<a id="troubleshooting"></a><a id="sources"></a>

<div class="lab-concept" data-learning-frame="cleanup">
<p><strong>이 단계에서 하는 일:</strong> 결과를 보관한 뒤 자신의 실습 자원을 삭제하거나 승인된 보존 담당자에게 인계합니다.</p>
<p><strong>중요한 이유:</strong> 브라우저를 닫아도 Search·로그 등은 남을 수 있습니다. 반대로 공유 그룹을 잘못 삭제하면 다른 사람의 자원도 잃을 수 있습니다.</p>
<p><strong>진행 방법·위치:</strong> Azure Portal과 터미널에서 정확한 대상·소유권·승인을 확인하고 삭제 후 부재를 검증합니다.</p>
</div>

**브라우저 종료·Agent 삭제·`cleanup` 실행만으로 리소스 그룹 전체의 과금이 멈추지는 않습니다.**

### 삭제 전에 기록을 보관합니다 {#cleanup-records}

1. `notes.md`에 실제 프로젝트·Agent·데이터셋 버전·해시, 평가/run/job ID와 최종 판단을 남깁니다.
2. 평가·Optimizer 화면에서 제공하는 **Download/Export**로 결과를 받습니다. 메뉴가 없으면 보관한 receipt와 상세 결과를 사용하며, 받을 수 없는 결과를 받았다고 기록하지 않습니다.
3. `.lab/lab-ko/`의 계획·manifest·승인·실행 기록을 조직이 허용한 비공개 위치에 보관합니다. 인증 정보·쿠키·서명된 URL·계정 정보가 있는 원본을 Git에 올리지 않습니다. 공개용 기록에는 필요한 합성 사례·점수·이유만 남깁니다.
4. Evaluations와 Optimization runs에서 실행 중인 작업을 확인합니다. 지원되는 **Cancel**을 사용하고 종료 상태를 확인합니다. 종료되지 않은 작업이 있으면 삭제 담당자에게 인계합니다.

### 자신의 환경과 공유 환경을 구분합니다 {#cleanup-scope}

| 환경 | 정리 범위 |
|---|---|
| 02에서 자신만을 위해 만든 전용 리소스 그룹 | 아래 전용 그룹 삭제 절차를 사용합니다. 그룹 안에 다른 업무 자원이 없고 삭제 승인을 받았는지 다시 확인합니다. |
| 운영자가 제공한 공유 프로젝트 | **리소스 그룹·Foundry·공유 모델·Search 서비스를 삭제하지 않습니다.** 자신에게 할당된 객체만 정리하고 운영자에게 남은 자원을 인계합니다. |
| 생성·실습 중간에 중단한 환경 | `config.json`·manifest와 Azure의 실제 자원을 대조합니다. 실패했다고 자원이 없다고 가정하지 않습니다. |

공유 환경에서 로컬 소유 기록이 있다면 먼저 다음 명령으로 **삭제 계획만** 확인합니다.

```bash
python -m lab --config .lab/lab-ko/.env cleanup
```

`mode: LOCAL_PLAN_ONLY`, `actions`, `never_deleted`, `manual_follow_up`를 읽습니다. 삭제 대상의 이름·프로젝트·소유자를 확인하고 해당 범위의 삭제 승인을 받은 경우에만 다음을 실행합니다. 자신의 환경 이름이 다르면 prefix도 동일하게 바꿉니다.

```bash
python -m lab --config .lab/lab-ko/.env cleanup --confirm-prefix lab-ko
```

`OWNED_OBJECTS_ABSENT`인지 확인합니다. 이 도구는 기록된 Agent 버전·검색 객체·연결 등을 삭제하지만 **리소스 그룹·모델 배포·Search 서비스·로그·RBAC는 삭제하지 않습니다.** 포털에서 만든 데이터셋·평가·Optimizer 작업·Playground 대화와 모델 smoke 응답도 전부 자동 정리하지 않습니다. 승인된 항목은 해당 화면에서 개별 삭제하고, 삭제 기능이 없는 항목은 운영자에게 보존·프로젝트 정리 여부를 인계합니다.

### 전용 리소스 그룹을 삭제하고 부재를 확인합니다 {#cleanup-delete}

`YOUR_LAB_RESOURCE_GROUP`을 `config.json`의 **`names.resource_group`**으로 교체합니다. 이름의 prefix만 보고 판단하지 않고 구독·소유 태그·목록 전체를 확인합니다.

```bash
az group show --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP" --query "{name:name,location:location,tags:tags}" -o json
az resource list --subscription "YOUR_SUBSCRIPTION_ID" --resource-group "YOUR_LAB_RESOURCE_GROUP" --query "[].{name:name,type:type}" -o table
```

**그룹 전체 삭제는 되돌릴 수 없으며 그룹 안의 Foundry·모델·Search·모니터링 자원이 함께 삭제됩니다.** 보관이 끝났고 정확한 그룹 전체를 삭제하도록 승인받은 경우에만 다음 두 방법 중 하나를 선택합니다.

1. **포털 방법:** Azure Portal → Resource groups → 정확한 그룹 → **Delete resource group**을 선택합니다. 삭제 목록을 읽고 요구하는 그룹 이름을 직접 입력한 뒤 확인합니다.
2. **CLI 방법:** 다음 명령을 실행하고 확인 질문에서 이름·범위를 다시 확인한 뒤 동의합니다. `--yes`를 붙여 확인을 생략하지 않습니다.

<figure class="portal-shot" id="portal-delete-review">
<img src="../web/assets/portal/28-delete-review.png" alt="리소스 그룹 삭제 확인 창의 대상 목록, 그룹 이름 입력란과 Delete·Cancel 버튼입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>삭제 예정 목록과 확인란을 먼저 읽습니다.</strong> 그룹 이름과 전체 자원 목록을 대조합니다. 승인받은 경우에만 확인란에 그룹 이름을 입력하고 Delete로 진행합니다. 대상이 다르거나 승인되지 않았다면 Cancel로 닫습니다. <a href="../web/assets/portal/28-delete-review.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

```bash
az group delete --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP"
```

삭제 요청 수락은 완료가 아닙니다. 포털 알림과 그룹 상태를 확인하고 다음 명령이 성공적으로 **`false`**를 출력하는지 확인합니다.

```bash
az group exists --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP"
```

권한 오류·네트워크 오류는 `false`가 아니며 삭제 성공으로 처리하지 않습니다. `true`이면 삭제 진행 상태를 확인합니다. **Locks**, 권한, 다른 그룹의 종속 자원 때문에 실패하면 [삭제 문제 해결](troubleshooting.md#cleanup)을 따릅니다. 조직이 설정한 잠금을 임의로 제거하지 않습니다.

삭제 뒤 **Cost Management → Cost analysis**에서 해당 구독·기간·리소스 그룹을 확인합니다. 청구 반영에는 지연이 있으며 기존 사용 요금은 사라지지 않습니다. 별도 그룹의 로그·저장소나 서비스별 soft-delete 보존 항목은 따로 확인합니다. 영구 삭제/purge는 조직 정책과 별도 승인이 있을 때만 수행합니다.

**최종 완료 기준:** 전용 그룹의 부재를 확인하고 삭제 시각을 기록했거나, 공유 자원의 남은 항목·이유·담당자·보존 종료일을 기록하여 인계했습니다. `.lab` 기록을 먼저 지워 소유권 근거를 잃지 않습니다. [운영자 정리표](admin-setup.md#cleanup) · [삭제 문제 해결](troubleshooting.md#cleanup)을 참고합니다.
