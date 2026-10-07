# 고객지원 AI를 평가하고 개선합니다 · v1 {#좋은-에이전트는-평가에서-시작된다-v1}

<p class="eyebrow">CONTOSO ATLAS CLOUD · 하나의 실습 경로</p>

**고객지원 AI에 질문 12개를 보내 채점하고, 지침을 고친 뒤 같은 질문으로 다시 비교합니다.** Azure·Foundry 사용 경험은 필요하지 않습니다. 다만 PC에 도구를 설치하고, 사용 권한과 비용 승인을 받은 Azure 환경이 필요합니다.

**Azure**는 Microsoft의 클라우드 서비스입니다. **Microsoft Foundry**는 Azure에서 AI 모델과 Agent를 만들고 평가하는 개발 플랫폼입니다. **Agent(에이전트)**는 모델에 지침과 도구를 연결한 AI입니다. 여기서는 가상의 **Contoso Atlas Cloud 고객지원 Agent**가 정책 문서를 검색해 답하게 합니다.

<div class="hero-summary" aria-label="실습의 목적과 결과">
<div><strong>실습 목표</strong><span>정책에 근거해 답하는 고객지원 Agent를 만듭니다.</span></div>
<div><strong>중요한 이유</strong><span>그럴듯한 답변 하나가 아니라 12건의 답변과 채점 이유로 품질을 판단합니다.</span></div>
<div><strong>진행 방식</strong><span>같은 질문·모델·채점 기준을 유지하고 지침만 바꿉니다.</span></div>
<div><strong>완료 산출물</strong><span>변경 전후 비교, 최종 판단, 사용한 자원의 정리 기록을 남깁니다.</span></div>
</div>

<p class="step-next no-print"><a href="#setup">01부터 시작하기 →</a></p>

**모든 실습 참여자가 처음부터 끝까지 직접 수행합니다.** 본인 계정과 PC로 환경·Agent·데이터셋·평가를 준비하고 개선과 정리까지 진행합니다. 미리 만들어진 환경을 전제로 하지 않으며, 참고 문서는 필요한 설정을 확인할 때만 엽니다.

**처음이면 01부터, 중단 후 재개라면 자신의 기록부터 확인합니다.** 같은 실습의 `config.json`·manifest·receipt로 이미 완료한 작업을 확인하고 중복 생성·제출을 피합니다. 다른 사람의 설정·로그인 세션·소유권 기록을 복사하지 않습니다.

**시간·비용:** 처음부터 준비한다면 반나절 정도의 여유를 확보합니다. 권한·할당량 승인 대기와 서비스 실행 시간은 별도입니다. 모델 호출·Search·로그에는 비용이 발생할 수 있습니다. **브라우저를 닫아도 과금이 끝나지 않으므로 10의 정리까지 진행합니다.** 중간에 실습을 중단하더라도 생성한 자원이 있다면 10의 보관·정리를 수행합니다.

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

여기서 **학습은 평가 결과를 읽고 지침을 개선하는 과정**이며 모델 가중치를 다시 학습시키는 과정은 아닙니다. 제공된 합성 정책·질문만 사용합니다. 고객 원본 자료를 업로드하거나 평가 질문의 정답을 지침에 넣지 않습니다.

| 실행 위치 | 여기에서 하는 일 |
|---|---|
| [Azure Portal](https://portal.azure.com) | 계정·구독·권한, 실제 리소스 목록과 삭제 범위를 확인합니다. |
| 내 PC의 터미널 | 실습 파일을 준비하고 제공된 명령을 실행하는 창입니다. 여는 방법은 01에서 안내합니다. |
| [Microsoft Foundry](https://ai.azure.com) | 프로젝트·Agent·정책 도구를 확인하고 평가·Optimizer·비교 결과를 읽습니다. |

**읽는 방법:** 각 단계 상단의 **실행 순서** 링크로 이동하고, 해당 작업 뒤 **완료 기준**을 확인합니다. **터미널에서 실행** 상자만 내 PC에 입력하며, 포털 작업은 안내된 화면에서 수행합니다. Azure Portal과 Foundry는 별도 탭에 열어 둡니다. **그림의 계정·프로젝트 이름 대신 자신의 값을 사용합니다.**

**구현 코드는 필요할 때만 펼칩니다.** **실제 구현 코드 · 읽기 전용** 패널은 명령 내부의 함수·설정 원문이며 직접 실행할 대상이 아닙니다. 패널을 열지 않아도 실습을 진행할 수 있습니다. **코드 ↔ 포털** 표의 **실행 위치** 링크로 실제 명령·화면을 찾고, 내부 동작이 궁금하면 소스를 읽습니다.

**포털로 이미 생성된 항목을 다시 만들지 않습니다.** 코드로 생성하는 단계는 포털에서 결과를 확인하고, 평가·Optimizer처럼 포털에서 제출하는 단계는 그 화면에서 한 번만 수행합니다. 포털 내부 구현을 추측한 SDK 코드로 대신하지 않습니다.

01–03은 환경 준비, 04–09는 평가·개선, 10은 정리입니다. **04–06은 같은 평가 생성 화면에서 이어집니다.** 중간에 새 평가를 만들지 않습니다. 읽음 표시는 개인 책갈피일 뿐 실제 작업 완료 표시는 아닙니다.

**v1은 변경 전 Agent, v2는 지침을 바꾼 비교 후보입니다.** 두 번호는 Agent 전체 구성의 버전입니다. 모델·도구·출력 형식은 유지합니다. 개선이 없어서 v1을 유지해도 올바른 실습 결과이며, v2 생성은 운영용 게시 승인이 아닙니다.

## 01. 계정·PC·권한을 확인합니다 {#setup}

<a id="environment"></a><a id="sdk-prerequisites"></a>

<div class="lab-concept" data-learning-frame="setup">
<p><strong>이 단계에서 하는 일:</strong> 사용할 Azure 구독·권한과 로컬 실행 환경을 확인합니다.</p>
<p><strong>중요한 이유:</strong> 브라우저와 CLI가 다른 계정이나 구독을 사용하면 권한 오류가 나거나 잘못된 환경에 자원을 만들 수 있습니다.</p>
<p><strong>진행 방법·위치:</strong> Azure Portal에서 구독과 접근 권한을 확인한 뒤 터미널에서 도구·로그인·언어 설정을 대조합니다. 아직 Azure 리소스는 생성하지 않습니다.</p>
</div>

**실행 순서:** [Azure Portal · 계정·권한](#setup-account) → [터미널 · 도구 준비](#setup-local) → [터미널 · 로그인](#setup-login) → [터미널 · 언어 설정](#setup-language).
{: .step-route}

<div class="concept-primer" id="basics" role="group" aria-label="처음 사용하는 Azure 용어">
<p><strong>화면을 열기 전에 알아둘 여섯 가지입니다.</strong> 외울 필요 없이, 아래 역할만 구분합니다.</p>
<dl>
<div><dt>테넌트 · Tenant / Directory</dt><dd>로그인할 조직의 사용자·권한을 관리하는 경계입니다. 같은 계정으로 여러 조직에 접근할 수 있어 조직도 확인합니다.</dd></div>
<div><dt>구독 · Subscription</dt><dd>Azure 자원의 사용량과 요금이 묶이는 단위입니다. 실습 비용을 어느 구독에 청구할지 확인합니다.</dd></div>
<div><dt>리소스 그룹 · Resource group</dt><dd>함께 관리할 Azure 자원을 묶는 그룹입니다. 실습 전용 그룹을 쓰면 종료 시 삭제 범위를 확인하기 쉽습니다.</dd></div>
<div><dt>프로젝트 · Project</dt><dd>Foundry 안에서 Agent·데이터·평가 작업을 구분하는 공간입니다. 이후 실습은 같은 프로젝트에서 진행합니다.</dd></div>
<div><dt>모델 · Model</dt><dd>답변을 생성하는 AI입니다. 모델을 호출할 수 있게 준비하는 작업을 배포(Deploy), 그 배포에 붙인 이름을 배포 이름이라고 합니다.</dd></div>
<div><dt>권한 · Role / Scope</dt><dd>Role은 할 수 있는 일, Scope는 그 권한이 적용되는 범위입니다. 로그인 성공만으로 생성·평가·삭제 권한이 모두 생기지는 않습니다.</dd></div>
</dl>
</div>

### Azure 계정과 구독을 확인합니다 {#setup-account}

1. [Azure Portal](https://portal.azure.com)에 **본인의 실습용 계정**으로 로그인합니다. 사용할 계정·구독이 없다면 [Azure 계정 안내](https://azure.microsoft.com/pricing/purchase-options/azure-account)를 따라 준비합니다. 조직 구독은 본인이 사용할 범위의 접근·비용 승인을 먼저 확보합니다. 무료·체험 구독이라고 필요한 모델의 할당량까지 보장되지는 않습니다.
2. 상단 검색창에 **Subscriptions**를 입력하고 사용할 구독을 엽니다. 포털 상태가 **Active**인지 확인하고 **Subscription ID**와 **Directory/Tenant ID**를 기록합니다. 같은 정상 구독은 CLI에서 **Enabled**로 표시합니다. 구독이 보이지 않으면 우측 상단 계정의 디렉터리·구독 필터를 확인합니다.
3. **Access control (IAM, 권한 관리) → Check access**에서 본인의 역할과 적용 범위를 확인합니다. 이전 UI에서는 **View my access**로 표시할 수 있습니다. 이 실습은 본인이 리소스를 생성하고 리소스 범위 역할을 할당하므로 **생성 권한과 역할 할당 권한이 모두 필요합니다.** Contributor만으로는 역할 할당이 가능하지 않습니다. [작업별 필요 권한·공급자 등록](admin-setup.md#rbac)을 확인합니다.
4. 비용 한도, 사용 종료 시각, 전용 리소스 그룹의 삭제 또는 보존 범위를 정합니다. 권한·구독·비용 승인이 부족하면 조직 절차에 따라 본인에게 허용된 실행 범위를 확보한 뒤 계속합니다. 다른 사람에게 이후 실습을 대신 실행하게 하거나 구독 전체 Owner·보안 정책 해제로 우회하지 않습니다.

<figure class="portal-shot" id="portal-subscription-overview" data-capture-scope="shared">
<img src="../web/assets/portal/shared/21-subscription-overview.png" alt="Azure 구독 Overview의 Essentials에서 Subscription ID·Directory·Status·My role을 확인하는 화면입니다." width="1440" height="347" loading="lazy">
<figcaption><strong>구독과 상태를 확인합니다.</strong> Essentials에서 Subscription ID, Directory, Status, My role을 찾습니다. 포털의 <strong>Active</strong>와 CLI의 <strong>Enabled</strong>는 같은 정상 사용 상태를 나타냅니다. <a href="../web/assets/portal/shared/21-subscription-overview.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-check-access" data-capture-scope="shared">
<img src="../web/assets/portal/shared/22-check-access.png" alt="Access control IAM의 Check access에서 활성 역할과 Scope를 확인하는 화면입니다." width="1440" height="850" loading="lazy">
<figcaption><strong>역할 이름과 Scope를 함께 읽습니다.</strong> Access control (IAM) → Check access에서 자신의 활성 할당을 확인합니다. 역할 이름만 보지 않고 적용 범위를 대조하며 필요한 범위보다 큰 권한을 추가하지 않습니다. <a href="../web/assets/portal/shared/22-check-access.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

### 도구와 실습 파일을 준비합니다 {#setup-local}

[Python](https://www.python.org/downloads/) **3.11–3.14**, [Git](https://git-scm.com/downloads), [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)를 설치합니다. Python은 제공된 프로그램 실행용, Git은 실습 파일 내려받기용, Azure CLI는 `az` 명령으로 Azure에 로그인·조회하는 도구입니다. 회사 PC에서 설치가 제한되면 담당자에게 요청합니다.

**이미 설치했다면 [설치 확인](#setup-verify)부터 진행하고, 정상인 도구는 다시 설치하지 않습니다.** Windows·macOS의 아래 예시는 지원 범위를 벗어난 최신 Python이 선택되지 않도록 **3.13**을 지정합니다. 이미 다른 지원 버전을 사용한다면 `py -3.13`·`python3.13`을 해당 버전의 명령으로 바꾸고, 버전 확인과 가상환경 생성에 같은 Python을 사용합니다. 3.10 이하·3.15 이상은 이 실습의 지원 범위가 아닙니다.

먼저 **내 PC의 터미널**을 엽니다. Windows는 시작 메뉴에서 **PowerShell**, macOS는 Spotlight에서 **Terminal(터미널)**, Linux는 앱 메뉴에서 터미널을 검색합니다. Azure Portal의 Cloud Shell이나 `>>>`가 보이는 Python 입력창은 이 가이드의 실행 위치가 아닙니다.

**명령 읽는 법:** **한 명령씩** 실행하고 끝난 뒤 다음 명령으로 이동합니다. 긴 명령이 화면에서 여러 줄로 보이더라도 명령 중간에 줄바꿈을 넣지 않습니다.

복사 버튼은 **상자 전체**를 복사합니다. 여러 명령이 들어 있다면 편집기에 먼저 붙여넣고 한 명령씩 실행합니다. `YOUR_...`는 자신의 값으로 바꾸고 바깥 큰따옴표는 유지합니다.

`공통 터미널`은 모든 운영체제에서 사용합니다. `macOS/Linux`·`PowerShell` 상자는 바로 위 설명을 읽고 **자신의 운영체제에 해당하는 것만** 실행합니다. **오류가 나면 다음 명령으로 넘어가지 않고** 해당 단계의 문제 해결을 확인합니다.

[Windows 설치](#setup-windows) · [macOS 설치](#setup-macos) · [Linux 설치](#setup-linux) 중 하나를 마친 뒤 [설치 확인](#setup-verify)으로 이동합니다.

#### Windows · PowerShell에서 설치합니다 {#setup-windows}

PowerShell에서 `winget --version`을 실행합니다. 버전이 나오면 Windows 패키지 관리 도구인 **WinGet**으로 아래 명령을 한 줄씩 실행합니다. 설치 동의나 설치 권한 요청은 조직의 승인 범위에서 직접 확인합니다.

```powershell
winget install --exact --id Python.Python.3.13 --source winget
winget install --exact --id Git.Git --source winget
winget install --exact --id Microsoft.AzureCLI --source winget
```

**WinGet이 없거나 사용할 수 없다면 공식 설치 파일을 사용합니다.** 두 방법을 모두 실행할 필요는 없습니다.

| 도구 | 다운로드와 설치 화면에서 확인할 항목 |
|---|---|
| Python | [Windows 다운로드](https://www.python.org/downloads/windows/)에서 **Python 3.13의 최신 패치 버전**과 PC에 맞는 installer를 선택합니다. embeddable package가 아닌 일반 설치 파일에서 **Add python.exe to PATH**를 선택하고 **pip·Python Launcher**를 포함하여 설치합니다. |
| Git | [Git for Windows](https://git-scm.com/install/windows)에서 PC에 맞는 설치 파일을 받습니다. PATH 선택 화면의 **Git from the command line and also from 3rd-party software**를 유지하여 PowerShell에서도 사용할 수 있게 합니다. |
| Azure CLI | [Windows 공식 설치 안내](https://learn.microsoft.com/cli/azure/install-azure-cli-windows?pivots=msi)의 **Microsoft Installer (MSI)**를 사용합니다. 일반적인 x64 PC는 64-bit MSI를 선택합니다. |

설치 후 [새 터미널에서 세 도구 확인](#setup-verify)으로 이동합니다. `py`가 인식되지 않으면 Python 설치의 Launcher 옵션을 확인합니다.

#### macOS · Homebrew로 설치합니다 {#setup-macos}

터미널에서 `brew --version`을 실행합니다. 명령이 없으면 [Homebrew 공식 설치 안내](https://brew.sh/)를 따라 설치하고, 마지막에 표시되는 **Next steps**의 PATH 설정까지 마친 뒤 새 터미널에서 다시 확인합니다. 회사 PC의 설치·Command Line Tools 승인 절차를 우회하지 않습니다.

```bash
brew update
brew install python@3.13 git azure-cli
```

Python은 [Homebrew의 버전 지정 패키지](https://formulae.brew.sh/formula/python@3.13), Azure CLI는 [Microsoft의 macOS 설치 안내](https://learn.microsoft.com/cli/azure/install-azure-cli-macos)를 따릅니다. **이 경로에서는 `python3.13`을 사용합니다.** 기존 `python3`는 macOS 기본 Python이나 다른 버전을 가리킬 수 있으므로 시스템 Python을 덮어쓰거나 강제로 연결하지 않습니다.

#### Linux · Ubuntu 24.04 LTS 예시입니다 {#setup-linux}

다음은 기본 Python 3.12를 제공하는 **Ubuntu 24.04 LTS** 기준입니다. 다른 배포판은 해당 배포판의 Python·[Git 설치 안내](https://git-scm.com/install/linux)와 [Azure CLI 공식 설치 안내](https://learn.microsoft.com/cli/azure/install-azure-cli-linux)를 따릅니다. Python 버전이 지원 범위 밖이면 시스템 Python을 교체하지 말고 담당자에게 지원되는 실행 환경을 요청합니다.

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git curl
curl -fsSL 'https://azurecliprod.blob.core.windows.net/$root/deb_install.sh' -o install-azure-cli.sh
```

마지막 명령은 [Microsoft의 Ubuntu/Debian용 설치 스크립트](https://learn.microsoft.com/cli/azure/install-azure-cli-linux?pivots=apt)를 **내려받기만** 합니다. `install-azure-cli.sh`를 편집기로 열어 내용을 확인하고 필요한 시스템 설치 권한과 승인이 있는 경우에만 다음을 실행합니다. `sudo` 권한이 없으면 승인된 설치 경로를 확보한 뒤 진행합니다.

```bash
sudo bash install-azure-cli.sh
```

#### 새 터미널에서 설치를 확인합니다 {#setup-verify}

**설치가 끝나면 열려 있던 터미널 창을 모두 닫고 다시 엽니다.** PATH는 명령을 찾는 경로 목록이며, 기존 창에는 새 설치 경로가 반영되지 않을 수 있습니다. VS Code의 터미널을 사용한다면 VS Code도 종료한 뒤 다시 엽니다.

**Windows PowerShell:**

```powershell
py -3.13 --version
git --version
az version
```

**macOS · 위 Homebrew 설치 경로:**

```bash
python3.13 --version
git --version
az version
```

**Linux · 위 Ubuntu 설치 경로:**

```bash
python3 --version
git --version
az version
```

| 확인 항목 | 정상 출력과 진행 기준 |
|---|---|
| 실습용 Python | `Python 3.13.x` 같은 버전이 나옵니다. `x`는 실제 패치 번호이며 **3.11·3.12·3.13·3.14** 중 하나여야 합니다. |
| Git | `git version 2.x...`처럼 설치된 버전이 나옵니다. |
| Azure CLI | JSON에 `"azure-cli": "2.x..."`처럼 버전이 나옵니다. **이 확인에는 Azure 로그인이 필요하지 않습니다.** |

`az version`에 표시되는 Python은 Azure CLI 자체의 실행 환경이며, 실습용 Python 설치 확인을 대신하지 않습니다. **세 명령이 모두 성공한 뒤에만** 파일 다운로드·가상환경 생성으로 진행합니다. `command not found`, `not recognized`, Python 대신 Microsoft Store가 열리는 경우는 [설치·PATH 문제 해결](troubleshooting.md#environment)을 확인합니다.

#### 실습 파일을 내려받습니다 {#setup-download}

```sh
git clone https://github.com/junwoojeong100/foundry-evaluation-labs-v1.git
cd foundry-evaluation-labs-v1
```

이미 내려받았다면 clone을 반복하지 않고 해당 폴더로 이동합니다. GitHub의 **Code → Download ZIP**으로 받은 경우 먼저 압축을 풀고 `pyproject.toml`과 `requirements.lock`이 있는 폴더를 엽니다. HTML 파일 한 개만 내려받으면 코드·데이터·그림이 누락됩니다.

#### 확인한 Python으로 가상환경을 만듭니다 {#setup-venv}

이후 명령은 **`pyproject.toml`과 `requirements.lock`이 있는 실습 폴더**에서 실행합니다. `.venv`는 이 실습만의 Python 패키지 공간입니다. 앞에서 버전을 확인한 **같은 Python**으로 만들며, 아래 세 경로 중 자신의 운영체제에 맞는 하나만 실행합니다.

**macOS · 위 Homebrew 설치 경로:**

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

**Linux · 위 Ubuntu 설치 경로:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell에서는 다음을 실행합니다.**

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

PowerShell 실행 정책 때문에 활성화가 차단되면 조직 정책을 변경하지 않습니다. 이후 명령의 `python`을 `.\.venv\Scripts\python.exe`로 바꾸어 실행합니다. 기존 `.venv`가 있다면 다른 작업의 환경인지 확인하고 임의로 덮어쓰지 않습니다.

**가상환경을 준비한 뒤 다음 공통 명령을 실행합니다.** 첫 두 명령에서 Python 3.11–3.14와 `.venv` 안의 pip 경로를 확인한 뒤 패키지를 설치합니다.

```sh
python --version
python -m pip --version
python -m pip install -r requirements.lock
python -m lab --help
python scripts/build_datasets.py --language ko --check
```

명령 목록과 데이터 검사 성공을 확인합니다. `ModuleNotFoundError`가 나오면 `python -m pip --version`으로 `.venv`의 Python을 사용하는지 확인합니다. 시스템 Python에 임의로 패키지를 설치하지 않습니다.

### CLI 로그인과 언어를 고정합니다 {#setup-login}

먼저 아래 `YOUR_SUBSCRIPTION_ID`를 앞에서 기록한 구독 ID로 교체합니다. `az login`이 여는 브라우저에서 **같은 계정**으로 로그인한 뒤 터미널로 돌아옵니다.

```sh
az login
az account list --query "[].{name:name,id:id,state:state}" -o table
az account set --subscription "YOUR_SUBSCRIPTION_ID"
az account show --query "{user:user.name,tenant:tenantId,subscription:id,state:state}" -o json
```

마지막 출력의 **`state`가 `Enabled`인지 확인**하고 `user`, `tenant`, `subscription`을 포털과 대조하여 기록합니다. 브라우저와 CLI의 로그인은 별개입니다. 다른 디렉터리가 선택됐다면 승인된 디렉터리로 `az login --tenant "YOUR_TENANT_ID"`를 실행합니다.

#### 언어와 실행 기록 폴더를 지정합니다 {#setup-language}

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

**새 터미널에서는 실습 폴더로 먼저 이동**한 뒤 [가상환경 활성화](#setup-venv)와 이 두 변수를 다시 지정합니다. `LAB_LANGUAGE`를 바꾸면서 기존 실행 폴더를 재사용하지 않습니다.

**같은 실습을 재개하는 경우:** 가상환경·언어 변수·계정을 다시 확인하고 자신의 원래 실행 기록을 사용합니다. 환경 생성 상태는 [02의 조회·검사](#resources-create)에서 확인합니다. 01에서는 Azure 환경을 생성하거나 SDK를 호출하지 않습니다.
{: .note}

#### 코드 ↔ 포털 · 로그인과 로컬 설정을 확인합니다 {#setup-code-portal}

**실행 위치:** 위의 [터미널 로그인 명령](#setup-login)과 [언어·기록 폴더 설정](#setup-language)을 실행합니다. 이 단계에서는 명령 출력과 포털 값을 직접 대조합니다.
{: .execution-guide}

| 실행한 명령·설정값 | 지금 확인하는 내용 | 포털 조작·확인 위치 |
|---|---|---|
| `az login`, `az account set`, `az account show` | 로그인 계정·테넌트·구독을 기록하고 `state: Enabled`를 확인합니다. | Azure Portal 우측 상단 계정의 Directory와 **Subscriptions → 사용할 구독 → Overview**의 ID·상태를 직접 대조합니다. |
| `LAB_LANGUAGE`, `LAB_ARTIFACTS_DIR` | 현재 터미널의 데이터 언어와 실행 기록 경로를 지정합니다. | 포털에 없는 로컬 설정입니다. 한국어 실습은 `ko`와 `.lab/lab-ko/artifacts`를 사용합니다. |

**완료 기준:** Python 3.11–3.14·Git·Azure CLI의 버전을 확인했고, 같은 사용자·테넌트·구독을 사용하며, 가상환경의 Python 명령과 한국어 데이터 검사가 성공합니다. 문제가 있으면 [환경 오류 해결](troubleshooting.md#environment)을 확인합니다.
{: .completion-check}

<p class="step-next no-print"><a href="#resources" data-next-step>다음: 02. Foundry 환경 생성 →</a></p>

## 02. Foundry 환경을 생성합니다 {#resources}

<a id="first-infrastructure-failure"></a>

<div class="lab-concept" data-learning-frame="resources">
<p><strong>이 단계에서 하는 일:</strong> 전용 리소스 그룹 안에 Foundry 프로젝트·모델·Search·모니터링 기반을 준비합니다.</p>
<p><strong>중요한 이유:</strong> 리소스 그룹은 비용과 정리 범위를 묶고, 프로젝트는 Agent·평가를 구분합니다. 빈 프로젝트 하나만으로 정책 검색까지 준비되지는 않습니다.</p>
<p><strong>진행 방법·위치:</strong> 본인의 터미널에서 계획·승인·생성을 순서대로 수행한 뒤 두 포털에서 결과를 대조합니다. 재개할 때는 같은 계획과 실제 상태를 확인합니다.</p>
</div>

**실행 순서:** [터미널 · 계획](#resources-plan) → [TPM 요구량 확인](#resources-tpm) → [승인·준비 검사](#resources-approval) → [터미널 · 생성](#resources-create) → [포털·런타임 확인](#resources-runtime-check).
{: .step-route}

**처음에는 아래 계획부터 만듭니다.** 자신의 같은 실습 계획이 이미 있다면 `plan`을 반복하지 않고 원래 `config.json`으로 `bootstrap status`를 조회합니다. 생성이 끝난 경우에도 이 단계의 포털·런타임 검사를 확인한 뒤 03으로 진행합니다.
{: .note}

<figure class="concept-flow" id="resource-map" aria-label="Azure에서 Foundry 프로젝트까지의 포함 관계">
<ol>
<li><strong>Azure 구독</strong><span>사용량·비용 관리</span></li>
<li><strong>리소스 그룹</strong><span>이번 실습의 자원 묶음</span></li>
<li><strong>Foundry 리소스</strong><span>AI 서비스와 모델 배포</span></li>
<li><strong>프로젝트</strong><span>Agent·데이터·평가 작업</span></li>
</ol>
<figcaption>앞 항목이 다음 항목을 포함합니다. 같은 실습 그룹에 <strong>Azure AI Search</strong>(정책 검색)와 <strong>Application Insights·Log Analytics</strong>(실행 기록)도 준비합니다.</figcaption>
</figure>

**Endpoint(엔드포인트)**는 프로그램이 서비스에 연결할 때 쓰는 주소입니다. 이 실습은 프로젝트의 **Project endpoint**를 사용합니다. 옆에 있는 Azure OpenAI endpoint와 서로 바꾸어 사용하지 않습니다.

### 로컬 생성 계획을 만듭니다 {#resources-plan}

01에서 기록한 값을 아래 표대로 교체합니다. **ID는 이름이 아니라 자원을 식별하는 값**입니다. 구독의 표시 이름을 ID 자리에 넣지 않습니다.

| 교체할 부분 | 가져올 값 |
|---|---|
| `YOUR_SUBSCRIPTION_ID` | `az account show`의 `subscription` |
| `YOUR_TENANT_ID` | 같은 출력의 `tenant` |
| `YOUR_SIGN_IN_NAME` | 같은 출력의 `user` |

이 명령은 내 PC의 `.lab/lab-ko/`에 계획·미승인 승인서 예시만 만들고 Azure를 호출하지 않습니다.

```sh
python -m lab bootstrap plan --subscription "YOUR_SUBSCRIPTION_ID" --tenant "YOUR_TENANT_ID" --expected-user "YOUR_SIGN_IN_NAME" --environment lab-ko --location northcentralus
```

`plan_status: CREATED_LOCAL_ONLY`, `mutations_performed: false`와 `config_path`를 확인합니다. `BLOCKED_AWAITING_APPROVAL`은 아직 비용 승인이 없다는 뜻이며 생성 실패나 Azure 생성 완료가 아닙니다.

| 생성 파일 | 확인할 내용 |
|---|---|
| `.lab/lab-ko/config.json` | 구독·테넌트·사용자, 자동 생성 리소스 이름, 모델·버전·용량입니다. 직접 수정하지 않습니다. |
| `.lab/lab-ko/approval.example.json` | 아직 승인되지 않은 비용·변경 범위입니다. |
| `.lab/lab-ko/manifest.json` | 생성·소유권·중단 상태를 추적하는 기록입니다. 보존합니다. |
| `.lab/lab-ko/.env` | 아직 없습니다. 실제 생성이 완료된 뒤 만들어지는 런타임 설정입니다. |

파일은 텍스트 편집기의 **파일 열기**로 확인합니다. `.lab`는 실습 기록 폴더이며 운영체제에 따라 숨김 폴더로 보일 수 있습니다. JSON은 설정을 `이름: 값`으로 저장하는 형식입니다. Word 문서로 변환하거나 파일 확장자를 바꾸지 않습니다.

이제 같은 편집기에서 **`.lab/lab-ko/notes.md`**를 만들고 [실습 기록표](admin-setup.md#handoff)에 01의 계정 값과 계획 경로를 적습니다. `.md`는 일반 텍스트 메모 파일입니다. 이후 단계에서 실제 배포 이름·Agent·데이터·run ID·최종 판단을 이 파일에 이어서 기록합니다.

**구현 참고:** `plan()`은 이름·모델·해시를 정하고 로컬 파일만 씁니다. **Azure 생성 호출은 없습니다.** `plan` 뒤 포털에 자원이 나타나지 않는 것은 정상입니다.

<!-- source-code: lab/bootstrap.py:plan -->

모델 역할은 **답변 생성(Agent), 채점(Judge), 지침 제안·검색 계획(Optimizer/planner), 검색용 숫자 변환(embedding)**으로 나눕니다. 여기서 모델 자체를 직접 개발하지는 않습니다.

이 저장소의 기본 생성 지역은 **North Central US (`northcentralus`)**입니다. 기본 배포는 Agent `gpt-6-sol`, Judge `gpt-6-luna`, Optimizer/검색 planner `gpt-5.5`, embedding `text-embedding-3-small`입니다. 정확한 버전·SKU(배포 유형)·요청 용량은 [모델 표](admin-setup.md#prepare)와 계획 파일에서 확인합니다. 다른 지역·모델로 조용히 대체하지 않습니다.

### 모델별 최소 권장 TPM을 확보합니다 {#resources-tpm}

**TPM(Tokens Per Minute)은 배포별 분당 토큰 처리 한도**이며, 모델의 최대 입력 길이나 실제 처리 속도와는 다릅니다. 아래는 **한 환경에서 평가·Optimizer를 한 번에 하나씩 실행하는 12문항 실습**의 시작 기준입니다. 모든 요청에서 입증된 절대 최소치나 429 오류가 없다는 보장이 아니라, 평가기·검색 호출을 고려한 여유 포함 최소 권장값입니다.

| 역할·모델 | 실습 시작 최소 권장 TPM | 새 기본 계획의 ARM 용량 |
|---|---:|---:|
| Agent · `gpt-6-sol` | **100,000** | 100 |
| Judge · `gpt-6-luna` | **100,000** | 100 |
| Optimizer / 검색 planner · `gpt-5.5` | **100,000** | 100, 두 역할이 같은 배포를 공유 |
| Embedding · `text-embedding-3-small` | **10,000** | 10 |

새 `bootstrap plan`은 이 용량으로 계획을 만듭니다. **ARM 용량은 모델·SKU별 단위**이므로 다른 모델에 무조건 1,000을 곱하지 않습니다. 생성 후 실제 배포의 TPM을 아래 runtime preflight로 확인합니다. 구독에 남은 할당량이 있어도 해당 배포에 충분히 할당되지 않았다면 준비 완료가 아닙니다.

기존 계획·배포는 자동으로 상향되지 않습니다. 자신의 실제 배포와 승인 범위는 [TPM 설정 참고](admin-setup.md#throughput)로 확인합니다. `config.json`·승인서·manifest를 직접 고쳐 검사를 우회하지 않습니다.

**여러 사용자가 같은 배포를 공유하거나 작업을 겹치면 추가 용량이 필요합니다.** Azure는 실제 청구 토큰뿐 아니라 입력·최대 출력 설정으로 추정한 토큰을 제한에 반영하며, 별도의 **RPM(분당 요청 수)**·짧은 구간의 요청 집중도도 제한합니다. [공식 TPM·RPM 설명](https://learn.microsoft.com/azure/foundry/openai/how-to/quota#understanding-rate-limits)을 참고합니다.

### 준비 상태와 비용 승인을 확인합니다 {#resources-approval}

```sh
python -m lab bootstrap preflight --config .lab/lab-ko/config.json
```

**Preflight는 실행 전 준비 상태 검사**입니다. `readiness_status: READY`인지 확인합니다. 할당량(quota)은 구독에 허용된 사용 한도, 용량(capacity)은 해당 지역의 실제 제공 여력입니다. 막히면 `reason`을 읽고 [생성 오류 대응](troubleshooting.md#provisioning)으로 이동합니다. 아직 승인서가 없으므로 READY여도 전체 상태는 승인 대기일 수 있습니다. 지역이나 환경 이름을 바꾸어 반복 생성하지 않습니다.

원문에서 `cognitiveservices model list`, `usage list`, ARM의 `modelCapacities`를 조회하는 부분을 읽습니다. 이 검사는 모델을 호출하거나 배포하는 코드가 아닙니다.

<!-- source-code: lab/bootstrap.py:_preflight -->

본인이 사용할 비용·변경 범위의 승인을 확인한 뒤 `.lab/lab-ko/approval.example.json`을 편집기에서 열고 **다른 이름으로 저장**하여 `.lab/lab-ko/approval.json`을 만듭니다. 본인 소유 구독에서 지출을 결정할 권한이 있다면 한도를 직접 정하고 기록합니다. 조직 구독에서는 실제 승인 절차를 따릅니다. 원본 `scope_sha256`, `models`, `retention_days`는 유지하고 **[승인서 작성표](admin-setup.md#approval)의 모든 필드**를 채웁니다.

`approved_by`에는 계획의 `expected_user`와 같은 **본인 로그인 이름**을 적습니다. 이 값은 실행 신원을 연결하는 필드이지 조직 승인자의 전자서명이 아닙니다. 실제 승인 근거·현재 유효한 시작/만료 시각·통화/예산·대기/보관 한도·생성/RBAC/Global 처리 동의를 확인합니다. `approved: true`만 바꾸면 완료되지 않으며, 예산 숫자는 Azure의 자동 과금 차단 장치가 아닙니다.

```sh
python -m lab bootstrap preflight --config .lab/lab-ko/config.json --approval .lab/lab-ko/approval.json
```

**`readiness_status: READY`와 `status: READY_FOR_APPROVED_APPLY`를 모두 확인한 뒤에만 다음 생성 명령을 실행합니다.**

### 승인한 환경을 생성하고 포털에서 확인합니다 {#resources-create}

```sh
python -m lab bootstrap apply --config .lab/lab-ko/config.json --approval .lab/lab-ko/approval.json
python -m lab bootstrap status --config .lab/lab-ko/config.json --approval .lab/lab-ko/approval.json
```

첫 명령은 리소스·모델·연결·리소스 범위 역할을 실제로 생성합니다. 시간이 걸릴 수 있으므로 다른 창에서 같은 `apply`를 실행하지 않습니다. `apply`의 **APPLIED**, `.lab/lab-ko/.env` 생성, `status`의 `phase: succeeded`와 대상 리소스의 존재를 확인합니다. 대기 초과이면 `status`부터 확인하며 [재개 절차](troubleshooting.md#provisioning)를 따릅니다.

**여기서 생성된 `.env`가 이후 명령의 연결 설정입니다.** 사용자·테넌트·구독과 실제 프로젝트·모델 배포 값이 들어 있습니다. 설정 파일이므로 `source`나 PowerShell 스크립트로 실행하지 않고, 명령의 `--config`로 지정합니다. 아직 없다면 `.env.example`을 복사해 생성 완료로 간주하지 않습니다.

#### 코드 ↔ 포털 · 생성한 자원과 배포를 확인합니다 {#resources-code-portal}

**실행 위치:** 승인 후 [위의 `bootstrap apply`·`status` 명령](#resources-create)을 실행하고 [아래의 포털·런타임 검사](#resources-runtime-check)로 확인합니다. 포털에서는 생성 결과를 조회하며 같은 자원을 다시 만들지 않습니다.
{: .execution-guide}

| 코드·입력값 | 실제 동작 | 포털 조작·확인 위치 |
|---|---|---|
| `config["names"]`, ARM `PUT`의 `location`·`tags` | 이름 충돌을 검사하고 새 전용 리소스 그룹을 생성합니다. | Azure Portal → **Resource groups → 해당 그룹 → Overview**에서 이름·지역·Tags를 확인합니다. 같은 이름으로 새 그룹을 만들지 않습니다. |
| `deployment group create`, `template.json`, `_parameters(...)` | [실제 ARM 템플릿](../infra/bootstrap.json)에 정의된 Foundry·프로젝트·Search·관측 자원·모델·연결·역할을 배포합니다. | 그룹의 **Deployments → 해당 배포 → Deployment details/Inputs/Outputs**를 열어 템플릿 입력과 생성 항목을 대조합니다. |
| `config["models"]`의 모델·버전·SKU·capacity | 네 모델 배포를 계획 그대로 생성합니다. | Foundry **Home → View deployments → 배포 → Details**에서 모델·버전·배포 유형·Tokens per Minute Rate Limit을 확인합니다. |
| `bootstrap status`의 기존 그룹·배포·리소스 조회 | 같은 계획의 실제 상태를 읽고 로컬 기록과 대조합니다. 새 ARM 배포를 제출하지 않습니다. | 같은 그룹 **Deployments → 기존 배포**와 실제 자원 목록을 새로고침합니다. Create로 다시 제출하지 않습니다. |
| `.env`의 `AZURE_AI_PROJECT_ENDPOINT` | 생성 완료 후 실제 프로젝트 연결 설정을 저장합니다. | Foundry **Home → Project endpoint**를 대조합니다. Azure OpenAI endpoint를 대신 쓰지 않습니다. |
| 역할 할당과 프로젝트·Search 관리 ID | 사용자와 서비스에 서로 다른 범위의 권한을 설정합니다. | Azure Portal의 해당 자원 **Identity**, **Access control (IAM) → Check access**에서 신원·Scope를 확인합니다. 이 확인을 위해 역할을 다시 추가하지 않습니다. |

아래 `apply()`에서 **그룹 생성 → ARM 검증·배포 → 완료 상태 조회 → 인벤토리 대조 → .env 저장** 순서를 읽습니다. `bounded(...)`는 승인 유효기간·대기 한도를 확인한 뒤 원문에 표시된 Azure CLI 인자를 실행합니다. 로컬 파일·재개·소유권 보호도 실제 구현의 일부이므로 생략하지 않습니다.

<!-- source-code: lab/bootstrap.py:apply -->

ARM 템플릿에 전달하는 실제 입력도 확인합니다. `names`·`models`·사용자 ID·리소스 범위 역할·tags·보존 기간이 이 객체로 전달됩니다.

<!-- source-code: lab/bootstrap.py:_parameters -->

`status()` 원문도 함께 확인합니다. `apply`가 대기 초과됐을 때 어떤 원격 상태를 다시 읽는지 볼 수 있습니다.

<!-- source-code: lab/bootstrap.py:status -->

### 생성된 환경과 런타임 설정을 확인합니다 {#resources-runtime-check}

1. [Azure Portal](https://portal.azure.com) → **Resource groups**에서 `config.json`의 `names.resource_group`을 검색합니다. 구독·지역·리소스 목록을 확인합니다.
2. [Foundry](https://ai.azure.com)를 열고 **New Foundry**를 사용합니다. **Select a project to continue**가 나타나면 `names.project`와 같은 프로젝트를 선택하고 **Let's go**를 누릅니다. 환영 안내가 나타나면 읽고 **Close**로 닫습니다. 이미 New Foundry라면 좌측 상단 프로젝트 선택을 사용합니다. Classic의 hub 기반 프로젝트와 혼동하지 않습니다.
3. 프로젝트의 **Home**(일부 UI의 Overview)에서 **Project endpoint**를 확인합니다. `.env`의 `AZURE_AI_PROJECT_ENDPOINT`와 같은 `https://계정명.services.ai.azure.com/api/projects/프로젝트명` 형식이어야 합니다.
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

#### 터미널에서 신원·배포·TPM을 검사합니다 {#resources-preflight}

환경 생성이 완료되어 `.lab/lab-ko/.env`가 있을 때 다음 읽기 전용 명령을 실행합니다. 신원 확인도 이 명령 안에서 수행합니다.

```sh
python -m lab --config .lab/lab-ko/.env preflight
```

`checks`의 `agent_tpm`, `judge_tpm`, `optimizer_tpm`, `iq_planner_tpm`, `embedding_tpm`을 확인합니다. 각 항목의 `observed`가 실제 배포 TPM, `expected`가 위 최소 권장값입니다. 부족하거나 토큰 제한을 확인할 수 없으면 `BLOCKED`이며 다음 호출 단계로 진행하지 않습니다. 설정을 준비한 뒤 같은 읽기 전용 preflight를 다시 실행합니다.

#### 코드 ↔ 포털 · 생성된 설정과 실행 신원을 대조합니다 {#runtime-code-portal}

**실행 위치:** 위의 [런타임 검사 명령](#resources-preflight)을 실행합니다. 프로그램이 생성된 설정 파일과 현재 CLI 신원을 비교하므로, 신원 검사 함수를 별도로 입력하지 않습니다.
{: .execution-guide}

| 명령·설정값 | 실제 동작 | 포털 확인 위치 |
|---|---|---|
| `--config .lab/lab-ko/.env`의 `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `EXPECTED_AZURE_USER` | 생성된 환경에 기록한 구독·테넌트·사용자를 읽습니다. | 01에서 확인한 Azure Portal 계정의 Directory와 구독 Overview를 대조합니다. |
| `check_identity()`의 `az account show --subscription ...` | 설정값과 CLI의 사용자·테넌트·구독·Enabled 상태를 자동 대조합니다. 불일치하면 자원 조회를 진행하지 않고 중단합니다. | 같은 계정·구독인지 확인합니다. 로그인 성공만으로 다른 신원을 허용하지 않습니다. |

아래 함수가 이 명령 안에서 수행하는 신원 검사입니다. 구독 선택만으로 테넌트 확인을 대신하지 않습니다. 이 검사는 SDK 토큰 요청이나 모델 호출이 아닙니다.

<!-- source-code: lab/preflight.py:check_identity -->

아래 런타임 `run_preflight()`는 `.env`의 대상 자원·배포를 조회합니다. `rateLimits`의 `key: token`을 읽거나 원시 ARM 메타데이터를 다시 조회하는 부분을 포털의 TPM 표시와 연결합니다. **구독 할당량 확인과 배포의 실제 TPM 확인은 다른 검사**입니다.

<!-- source-code: lab/preflight.py:run_preflight -->

**완료 기준:** 런타임 preflight 전체와 다섯 TPM 항목이 `PASS`이고, 자신의 프로젝트와 역할별 배포를 확인합니다. 이는 읽기 전용 구성 확인이며 실제 모델 응답 성공은 다음 단계에서 확인합니다.
{: .completion-check}

<p class="step-next no-print"><a href="#agent" data-next-step>다음: 03. 정책 연결·Agent 생성 →</a></p>

## 03. 정책을 연결하고 Agent를 생성합니다 {#agent}

<a id="model-smoke"></a><a id="iq"></a>

<div class="lab-concept" data-learning-frame="agent">
<p><strong>이 단계에서 하는 일:</strong> 합성 정책을 검색하는 읽기 전용 도구와 비교 기준인 v1 Agent를 연결합니다.</p>
<p><strong>중요한 이유:</strong> 모델이 기억으로 답하는 것과 실제 정책을 검색해 답하는 것은 다릅니다. 검색이 사용자 권한으로 성공해도 Agent의 관리 ID 권한은 별도로 확인해야 합니다.</p>
<p><strong>진행 방법·위치:</strong> 터미널에서 모델·검색·Agent를 준비하고 Foundry에서 지침·도구와 실제 응답을 확인합니다. 데이터 전송·호출은 승인된 범위에서 한 번씩 수행합니다.</p>
</div>

**실행 순서:** [터미널 · 모델 확인](#agent-smoke) → [정책 업로드](#agent-search-prepare) → [검색 확인](#agent-search-probe) → [v1 생성](#agent-create) → [Foundry · 응답 확인](#agent-playground).
{: .step-route}

### 모델과 정책 검색을 확인합니다 {#agent-knowledge}

**이 세 명령은 실제 업로드·모델 호출을 수행하며 비용이 발생할 수 있습니다.** 본인이 각 명령의 정상 결과를 확인한 뒤 다음 명령으로 이동합니다. 재개할 때는 자신의 기록에서 이미 완료한 작업을 확인하고 불필요한 호출을 반복하지 않습니다.
{: .note .warning}

#### 1. 모델이 실제로 응답하는지 확인합니다 {#agent-smoke}

`smoke`는 짧은 동작 확인입니다.

먼저 [02의 TPM 검사](#resources-tpm)를 통과해야 합니다. 짧은 응답 한 번의 성공만으로 전체 평가에 필요한 처리량을 확보했다고 판단하지 않습니다.

```sh
python -m lab --config .lab/lab-ko/.env smoke --run-id model-smoke --confirm
```

출력의 **`status: completed`**를 확인합니다.

#### 코드 ↔ 포털 · 확인한 CLI 신원으로 SDK를 연결합니다 {#sdk-code-portal}

**실행 위치:** 위의 [모델 연결 확인 명령](#agent-smoke)을 실행합니다. 아래 인증 함수는 실제 SDK 호출 안에서 자동으로 사용되며, 별도 터미널 명령이 아닙니다.
{: .execution-guide}

| 실제 코드 | 실제 동작 | 포털 확인 위치 |
|---|---|---|
| `credential_for()`의 `AzureCliCredential(subscription=...)` | 02의 설정으로 CLI 신원을 다시 확인하고 자격 증명 객체를 만듭니다. SDK가 서비스를 호출할 때 그 신원으로 토큰을 요청합니다. API key나 다른 자격 증명으로 전환하지 않습니다. | Foundry 우측 상단 로그인 계정과 프로젝트의 구독을 설정값과 대조합니다. 토큰을 포털에 붙여넣는 작업은 없습니다. |

아래 첫 함수는 SDK에 전달할 자격 증명을 만들고, 다음 함수는 실제 모델 요청을 보냅니다. 인증 연결과 모델 응답 확인은 이 단계에서 함께 수행합니다.

<!-- source-code: lab/auth.py:credential_for -->

`smoke_model()` 안의 `client.responses.create(model=config.model, ...)`가 실제 Sol 모델 호출입니다. Agent를 아직 생성하지 않고 짧은 입력·최대 출력 128토큰으로 연결을 확인하며, 호출 전에 기록을 써서 결과 불명인 요청을 반복하지 않습니다.

<!-- source-code: lab/agents.py:smoke_model -->

#### 2. 정책 검색을 준비합니다 {#agent-search-prepare}

제공된 [합성 정책 8개](../data/knowledge/documents.json)를 검색 서비스에 올립니다.

```sh
python -m lab --config .lab/lab-ko/.env iq prepare --confirm
```

출력의 **`uploaded_documents: 8`**을 확인합니다. 프로그램이 검색 인덱스(검색용 문서 모음), knowledge base(지식 베이스), MCP 연결을 준비합니다. **MCP(Model Context Protocol)는 Agent와 도구를 연결하는 규약**입니다. 여기서는 정책을 읽는 검색 도구만 연결하며 내부 코드를 수정할 필요는 없습니다.

#### 코드 ↔ 포털 · 정책 검색을 구성합니다 {#knowledge-code-portal}

**실행 위치:** 터미널에서 [위의 `iq prepare`](#agent-search-prepare) 다음 [아래의 `iq probe`](#agent-search-probe)를 실행합니다. 아래 패널은 두 명령의 내부 구현이며 별도로 실행하지 않습니다.
{: .execution-guide}

| 실제 코드·설정 | 실제 동작 | 포털 조작·확인 위치 |
|---|---|---|
| `knowledge_payloads()["index"]`의 `fields`, `vectorSearch`, `semantic` | 정책 필드·1536차원 벡터·HNSW·embedding·semantic 설정을 정의합니다. | Azure Portal → 해당 Search → **Indexes → 생성된 인덱스 → Fields/JSON**에서 필드와 검색 구성을 확인합니다. 인덱스를 다시 만들지 않습니다. |
| `embed()`의 `client.embeddings.create(...)` | 8개 정책의 제목·내용을 실제 embedding 배포에 보냅니다. | Foundry **View deployments → embedding 배포 → Details**에서 모델·배포 이름을 확인합니다. 벡터 값 자체는 Search 인덱스에 저장되며 Agent Playground에 표시되는 설정이 아닙니다. |
| `prepare_knowledge()`의 `PUT`·`POST` | 인덱스 생성, 문서 업로드, knowledge source·knowledge base·프로젝트 연결을 순서대로 생성합니다. | Search의 **Indexes**, Foundry **Build → Knowledge → Knowledge bases**에서 이름·Knowledge sources를 대조합니다. |
| `connection.authType`, `audience`, `target` | 프로젝트 관리 ID로 Search의 MCP endpoint에 접근하는 연결입니다. | Foundry Knowledge의 **Connection**을 확인합니다. UI에 authType·audience 편집란이 없다면 `knowledge/config-snapshot.json`을 읽으며 임의 값을 넣지 않습니다. |
| `probe_knowledge()`의 `/retrieve`·`references`·`activity` | 실제 질문으로 정책 검색을 확인합니다. | 포털의 Active 상태와 구분합니다. 실제 검색 결과는 probe 출력·기록이고, Agent 경유 호출은 아래 Playground에서 별도로 확인합니다. |

먼저 **서비스에 보내는 설정 객체 전체**, 이어서 **그 설정을 만들고 업로드하는 실제 코드**를 읽습니다. `config.*`는 02의 `.env`, `names`는 자신의 기록에 있는 실제 객체 이름입니다.

<!-- source-code: lab/knowledge.py:knowledge_payloads -->

다음 짧은 함수가 실제 **GET → 생성 전용 PUT → 소유 기록 저장**입니다. 이어지는 `prepare_knowledge()`가 인덱스·source·base·connection에 이 동작을 적용합니다.

<!-- source-code: lab/knowledge.py:_ensure_created -->

<!-- source-code: lab/knowledge.py:prepare_knowledge -->

embedding 호출도 감춰진 로컬 점수 계산이 아닙니다. 다음 함수가 Azure OpenAI의 embedding API를 호출하고 원본 응답·입력 해시·모델·토큰 사용량을 보관합니다.

<!-- source-code: lab/embeddings.py:embed -->

#### 3. 질문으로 정책이 검색되는지 확인합니다 {#agent-search-probe}

```sh
python -m lab --config .lab/lab-ko/.env iq probe --confirm
```

**`status: retrieval_verified`**와 비어 있지 않은 출처를 확인합니다. `created_not_retrieval_tested`는 생성만 성공했다는 뜻입니다. 오류가 발생하면 기록을 지우지 않고 [검색 오류 해결](troubleshooting.md#knowledge)을 확인합니다.

아래 `POST .../retrieve`의 질문·출처 요청과 실제 응답 검사를 읽습니다. **직접 검색 성공은 로그인한 사용자 경로의 근거**이며, 프로젝트 관리 ID의 Agent 도구 호출 근거와 같지 않습니다.

<!-- source-code: lab/knowledge.py:probe_knowledge -->

포털에서도 **Build → Knowledge → Knowledge bases**를 열고 Connection과 생성된 지식 베이스·Knowledge sources를 확인합니다. 목록의 지식 베이스 한 개가 정책 문서 한 개를 뜻하지는 않습니다.

<figure class="portal-shot" id="portal-policy-connection">
<img src="../web/assets/portal/26-knowledge-base.png" alt="Knowledge Foundry IQ에서 Connection·지식 베이스·Knowledge sources·Active 상태를 확인하는 화면입니다." width="1440" height="374" loading="lazy">
<figcaption><strong>정책 연결이 있는지 확인합니다.</strong> Connection 선택과 해당 지식 베이스의 Knowledge sources·Active를 확인합니다. Active는 등록 상태이며 실제 검색 성공은 <code>iq probe</code>로 확인합니다. 무료 검색 배너는 전체 실습이 무료라는 뜻이 아니며, 준비 확인을 위해 요금제 변경 버튼을 누르지 않습니다. <a href="../web/assets/portal/26-knowledge-base.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

### 같은 조건으로 평가할 v1을 만듭니다 {#agent-create}

```sh
python -m lab --config .lab/lab-ko/.env native-agent --version 1 --confirm
```

이 명령은 `prompts/baseline.txt`의 지침과 방금 확인한 정책 도구로 **`lab-ko-iq` 버전 `1`**을 만듭니다. 출력의 `agent_name`, `version`, `receipt`를 기록합니다. **Receipt는 실행 결과를 저장한 기록 파일**입니다. 같은 소유 환경·동일 구성이면 기존 v1을 재사용하며, 다른 Agent를 인수하거나 v3를 만들지 않습니다.

#### 코드 ↔ 포털 · Agent의 전체 구성을 확인합니다 {#agent-code-portal}

**실행 위치:** [위의 v1 생성 명령](#agent-create)을 실행한 뒤 [아래의 Foundry Playground](#agent-playground)에서 버전·설정·실제 응답을 확인합니다. 포털에서 다시 생성하거나 새 버전으로 저장하지 않습니다.
{: .execution-guide}

| 실제 코드·설정 | 포털 조작·확인 위치 |
|---|---|
| `definition["model"] = config.model` | **Build → Agents → 실제 Agent → Version 1 → Model**에서 같은 배포를 확인합니다. |
| `definition["instructions"] = prompt.read_text(...)` | 같은 화면의 **Instructions**를 [원본 지침](../prompts/baseline.txt)과 대조합니다. 확인 중 Save/새 버전을 누르지 않습니다. |
| `knowledge_tool()`의 MCP endpoint·`allowed_tools`·`project_connection_id` | **Knowledge/Tools**에서 정책 연결을 확인합니다. 허용 도구는 `knowledge_base_retrieve`이며 도구가 실제 실행됐는지는 응답의 실행 상세에서 확인합니다. |
| `native_response_format()`의 `json_schema`, `strict` | 생성된 Agent의 구조화 출력 설정입니다. UI가 전체 스키마를 보여주지 않으면 `agents/native-v1.json`의 `agent.definition.text`를 읽습니다. 자연어 지침으로 같은 설정을 추측해 다시 만들지 않습니다. |
| `project.agents.create_version(...)`, `draft=False` | 생성 후 포털의 **Version**에서 실제 `1`을 확인합니다. 새 버전 생성은 운영용 게시가 아닙니다. |

먼저 연결한 도구와 Agent 정의를 읽고, 다음 함수의 **실제 `project.agents.create_version` 호출**까지 확인합니다. 두 함수 사이의 고정 버전·소유권·같은 구성 재사용 검사도 실제 동작입니다.

<!-- source-code: lab/knowledge.py:knowledge_tool -->

<!-- source-code: lab/agents.py:create_native_agent -->

<!-- source-code: lab/agents.py:ensure_fixed_release -->

### Foundry에서 v1의 응답과 도구 호출을 확인합니다 {#agent-playground}

<figure class="portal-shot" id="portal-agent-configuration">
<img src="../web/assets/portal/27-agent-configuration.png" alt="Agent Playground에서 Version·Model·Instructions·Knowledge와 Chat을 확인하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>버전·지침·Knowledge를 확인합니다.</strong> 위쪽 Version을 1로 선택하고 왼쪽 Model·Instructions와 아래쪽 Knowledge를 확인합니다. 정책 MCP 연결은 Knowledge에 표시되며 오른쪽 Chat에서 질문을 입력합니다. <a href="../web/assets/portal/27-agent-configuration.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

포털에서 **Build → Agents → lab-ko-iq → 버전 1**을 엽니다. 표시 이름은 명령 출력이 기준입니다. 이 단계에서는 Model·Instructions·Knowledge를 편집하거나 새 버전으로 저장하지 않습니다. **Test/Playground**에서 다음 질문을 한 번 보냅니다.

> 2026년 9월에 처음 월 구독을 결제했습니다. 환불 신청 조건이 궁금합니다.

답변은 일반 채팅 문장 대신 **네 항목의 JSON**으로 표시됩니다. 화면에 중괄호와 따옴표가 보여도 오류가 아닙니다.

| 응답 항목 | 읽는 방법 |
|---|---|
| `answer` | 사용자에게 전달할 한국어 답변입니다. |
| `citations` | 답변 근거인 `ATLAS-*` 정책 ID 목록입니다. |
| `route` | `answer` 답변, `clarify` 추가 질문, `escalate` 사람에게 인계, `refuse` 거절 중 하나입니다. |
| `needs_human` | 사람 인계가 필요한지 나타내는 `true`/`false`입니다. `route`가 `escalate`일 때만 `true`입니다. |

실행 상세에서 **`knowledge_base_retrieve`의 실제 호출·응답**을 확인하고 정책 ID와 답변 근거를 대조합니다. Agent의 **관리 ID는 Azure 서비스가 사용하는 신원**으로, 로그인한 본인의 신원과 다릅니다. 직접 검색이 성공해도 Agent의 검색 권한은 별도로 확인합니다.

**완료 기준:** 자신의 v1이 실제 질문에 응답하고 정책 도구 호출이 확인됩니다. JSON 형식이나 연결 성공만으로 품질이 검증됐다고 표시하지 않습니다. 다른 구성 요소를 수정하는 실습은 추가하지 않으며 다음 단계부터 관리형 평가에 집중합니다.
{: .completion-check}

<p class="step-next no-print"><a href="#start" data-next-step>다음: 04. 데이터셋 등록 →</a></p>

## 04. 데이터셋을 등록합니다 {#start}

<a id="demo"></a><a id="understand"></a><a id="data"></a>

<div class="lab-concept" data-learning-frame="start">
<p><strong>이 단계에서 하는 일:</strong> 같은 질문으로 비교할 수 있도록 한국어 dev12 파일을 한 번 등록합니다.</p>
<p><strong>중요한 이유:</strong> 질문이나 참고 답변이 달라지면 지침 변경의 효과를 분리할 수 없습니다. 참고 답변을 Agent에게 미리 주어도 공정한 비교가 아닙니다.</p>
<p><strong>진행 방법·위치:</strong> 터미널에서 행 수·해시를 확인하고 Foundry 평가 마법사에서 원본 파일을 등록하거나 같은 버전을 재사용합니다.</p>
</div>

**실행 순서:** [터미널 · 원본 확인](#dataset-check) → [Foundry · 등록·선택](#dataset-register) → [05 · 같은 화면에서 기준 설정](#prepare).
{: .step-route}

<p class="wizard-context" data-wizard-step="1"><strong>같은 평가 생성 과정의 1/3입니다.</strong> 04 데이터 선택 → 05 채점 기준 설정 → 06 제출 순서입니다. 이 단계에서는 아직 Submit을 누르지 않습니다.</p>

**데이터셋은 평가에 사용할 질문 묶음**입니다. 이 실습에서는 **[data/optimizer/dev.jsonl](../data/optimizer/dev.jsonl)**의 **JSONL 12행**을 사용하며, 이를 줄여 **dev12**라고 부릅니다. 한 줄이 질문 한 건인 JSON 형식입니다. 편집하거나 Excel·CSV·JSON 배열로 변환하지 않습니다.

### 터미널에서 원본의 행 수와 해시를 확인합니다 {#dataset-check}

```sh
python -c "import hashlib,pathlib; p=pathlib.Path('data/optimizer/dev.jsonl'); print('rows =',len(p.read_text(encoding='utf-8').splitlines())); print('sha256 =',hashlib.sha256(p.read_bytes()).hexdigest())"
```

`rows = 12`와 SHA-256 값을 개인 메모에 기록합니다. **SHA-256(해시)은 파일 내용의 지문**으로, 이후에도 같은 파일인지 확인하는 값입니다. 외우거나 직접 입력할 필요 없이 출력된 값을 복사해 둡니다.

#### 코드 ↔ 포털 · 파일 확인과 등록을 구분합니다 {#dataset-code-portal}

**실행 위치:** [위의 터미널 명령](#dataset-check)은 행 수·해시만 확인합니다. 실제 업로드·선택은 [아래의 Foundry 등록 절차](#dataset-register)에서 수행합니다.
{: .execution-guide}

| 명령의 실제 코드 | 실제 동작 | 포털 조작·확인 위치 |
|---|---|---|
| `pathlib.Path('data/optimizer/dev.jsonl')` | 내 PC에서 업로드할 원본 파일을 선택합니다. | 아래 **Upload new dataset → Browse**에서 정확히 같은 파일을 고릅니다. |
| `p.read_text(...).splitlines()`, `len(...)` | 로컬 JSONL의 전체 행 수를 셉니다. | 업로드 Preview는 일부 행만 보여줄 수 있습니다. 등록 파일과 실행 범위는 원본 12행이어야 합니다. |
| `hashlib.sha256(p.read_bytes()).hexdigest()` | 파일 바이트의 지문을 계산합니다. | 포털에 SHA-256 확인란이 없으면 자신의 `notes.md`로 비교 조건을 보존합니다. 화면에 없는 해시를 확인했다고 표시하지 않습니다. |
| 이후 포털의 Upload/Existing dataset | 실제 데이터셋 등록·선택은 포털에서 수행합니다. | 자신의 프로젝트에 `lab-ko-dev12` 버전 `1`을 한 번 등록합니다. 위 Python 명령은 업로드나 평가 제출을 하지 않습니다. |

| 열 | 형식 | 용도 |
|---|---|---|
| `query` | 문자열 | Agent에 보내는 유일한 입력 |
| `context` | 문자열 | 지원 평가기와 사례 검토용 정책 참고 자료 |
| `ground_truth` | JSON 문자열 | 구조화 참고 답변이며 생성 프롬프트가 아닙니다. |

질문만 Agent에 전달하고, `context`·`ground_truth`는 지원 평가기와 사람의 사례 검토에 사용합니다. 제공된 나머지 데이터 파일은 이번 필수 실습에서 사용하지 않습니다.

<figure class="concept-flow" id="evaluation-flow" aria-label="질문부터 응답과 채점까지의 흐름">
<ol>
<li><strong>질문 · query</strong><span>데이터 한 행씩 전달</span></li>
<li><strong>Agent</strong><span>모델 + 지침 + 정책 검색</span></li>
<li><strong>실제 답변</strong><span>answer 등 네 항목</span></li>
<li><strong>평가기 + Judge</strong><span>점수와 채점 이유</span></li>
</ol>
<figcaption>정책 문서는 Agent가 도구로 검색합니다. 데이터의 참고 답변을 Agent 입력에 붙이지 않습니다. Agent는 안내만 하며 실제 환불·제출·삭제·권한 부여는 하지 않습니다.</figcaption>
</figure>

### Foundry에서 데이터셋을 등록하거나 선택합니다 {#dataset-register}

자신의 프로젝트에서 다음 순서로 선택합니다. 환경 이름을 바꾸었다면 예시 `lab-ko-iq` 대신 03의 명령이 출력한 실제 Agent 이름을 사용합니다.

1. **Build → Evaluations → Create → Create new evaluation**을 엽니다. 메뉴가 단수 **Evaluation**으로 보이면 같은 평가 메뉴입니다.
2. 대상 유형 **Agent**에서 **`lab-ko-iq`**, 버전 **1**을 선택합니다. **Pin currently latest**는 최신 버전이 실제로 1일 때만 사용합니다. 버전을 바꾼 뒤 대상 체크가 풀렸다면 다시 체크하고 **대상 한 개**인지 확인합니다.
3. **Individual turns(질문별 응답 평가)**, **One time(일회성 실행)**을 선택합니다. 새 질문을 생성하는 Synthetic data는 선택하지 않습니다.
4. **Upload new dataset → Browse**에서 **내 PC의 실습 폴더** 안에 있는 `data/optimizer/dev.jsonl`을 고릅니다. 이름은 **`lab-ko-dev12`**, 첫 버전은 **`1`**로 지정하고 등록 완료를 기다립니다. 이미 등록되어 있으면 **Existing dataset**에서 같은 이름·버전을 선택합니다.
5. `query`, `context`, `ground_truth` 열을 확인합니다. **5행 미리 보기는 전체 건수가 아닙니다.** 원본은 12행이며, 데이터셋 이름·버전을 메모한 뒤 같은 생성 화면에서 05로 이어갑니다.

<figure class="portal-shot" id="portal-evaluation-dataset">
<img src="../web/assets/portal/15-evaluation-dataset.png" alt="Foundry 평가의 데이터셋 선택과 query·context·ground_truth 열 미리 보기입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>한국어 데이터셋을 선택합니다.</strong> 등록 이름·버전을 원본과 대조하고 query·context·ground_truth 열을 확인합니다. 5행 미리 보기를 전체 건수로 해석하지 않으며 원본은 12행이어야 합니다. <a href="../web/assets/portal/15-evaluation-dataset.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

**완료 기준:** 명시적 v1과 변경 없는 12행 데이터셋을 선택하고 건수·버전·해시를 기록했습니다. [데이터 계약](../data/README.md#schema).
{: .completion-check}

<p class="step-next no-print"><a href="#prepare" data-next-step>다음: 05. 평가 기준 선택 →</a></p>

## 05. 평가 기준을 선택합니다 {#prepare}

<a id="calibration"></a>

<div class="lab-concept" data-learning-frame="prepare">
<p><strong>이 단계에서 하는 일:</strong> Relevance·TaskAdherence와 실제 Judge 배포를 선택합니다.</p>
<p><strong>중요한 이유:</strong> 점수의 척도·통과 기준·입력 매핑을 먼저 정해야 결과를 본 뒤 기준을 바꾸는 일을 피할 수 있습니다. 두 평가기는 척도가 서로 다릅니다.</p>
<p><strong>진행 방법·위치:</strong> Foundry의 Criteria에서 평가기별 설정을 열고 임계값과 Judge를 확인합니다. Agent에는 query만 전달합니다.</p>
</div>

**실행 순서:** [Foundry · 입력·평가기 설정](#criteria-configure) → [두 기준·Judge 확인](#portal-evaluation-criteria) → [06 · 검토·제출](#baseline-submit).
{: .step-route}

<p class="wizard-context" data-wizard-step="2"><strong>같은 평가 생성 과정의 2/3입니다.</strong> 04에서 열어 둔 화면을 이어서 사용합니다. 아직 새 평가를 만들거나 Submit을 누르지 않습니다.</p>

**평가기(Evaluator)는 채점 기준**, **Judge는 그 기준으로 채점하는 AI 모델**입니다. **관리형 평가**는 내 PC가 아니라 Foundry 서비스가 실행·결과를 관리한다는 뜻입니다.

### 같은 생성 화면에서 입력과 채점 기준을 설정합니다 {#criteria-configure}

1. **Configure agents**에서 지침을 덮어쓰는 custom prompt override는 비워 둡니다. 사용자 입력은 **`{{item.query}}`만** 사용합니다. 이는 각 행의 질문을 넣는 템플릿이므로 **중괄호까지 그대로 두고**, 자신의 질문이나 참고 답변으로 바꾸지 않습니다.
2. 필드 매핑 화면이 나타나면 입력 `query`를 데이터의 `query` 열과 연결합니다. 매핑은 **입력 칸과 데이터 열의 짝을 정하는 설정**입니다. `context`·`ground_truth`를 Agent 입력에 붙이지 않습니다.
3. **Criteria → Add evaluators**에서 아래 두 평가기만 남기고 다른 기본 선택은 해제합니다. TaskAdherence는 **Task Adherence**로 표시될 수도 있습니다.
4. 각 평가기의 설정을 열어 아래 기준을 적용하고 **Apply**를 누릅니다. **Evaluation model/Judge**에는 자신의 `.lab/lab-ko/.env`에서 **`JUDGE_DEPLOYMENT`에 해당하는 배포 이름**을 선택합니다.

| 평가기 | 의미 | 설정 |
|---|---|---|
| Relevance | 질문에 관련된 답변인지, **1–5점** | **Threshold 4**: 4·5점은 통과, 1–3점은 미통과입니다. |
| TaskAdherence | 과제 지시를 따르는지, **이진 0/1 Pass/Fail** | **통과 1**, 미통과 0입니다. 임계값 4가 아닙니다. |

응답(`response`)의 서비스 자동 매핑은 그대로 유지합니다. 응답 칸이 **Unassigned**이거나 자신의 Judge가 목록에 없다면 [매핑 점검](admin-setup.md#evaluation-mapping)과 [평가 문제 해결](troubleshooting.md#evaluation)을 따라 Agent·데이터 열·배포를 직접 대조합니다. 해결 전에는 임의 값을 넣거나 제출하지 않습니다.

#### 코드 ↔ 포털 · 채점 설정을 연결합니다 {#criteria-code-portal}

**실행 위치:** [위의 Foundry 설정 절차](#criteria-configure)를 수행합니다. **이 단계에는 별도 터미널 명령이 없습니다.** 아래 함수는 09의 재평가 helper에서 자동 호출되는 검증 코드입니다.
{: .execution-guide}

| 코드의 원격 평가 필드 | 포털에서 정하는 값 |
|---|---|
| `evaluator_name: builtin.relevance`, `threshold: 4` | **Criteria → Relevance → Threshold 4 → Apply** |
| `evaluator_name: builtin.task_adherence`, `threshold: 1` | **Criteria → TaskAdherence → 이진 통과 1 → Apply** |
| `initialization_parameters.deployment_name` | 각 평가기의 **Evaluation model/Judge**에 자신의 `JUDGE_DEPLOYMENT` 배포를 선택합니다. |
| `data_mapping.query = {{item.query}}` | **Configure agents → User input**에서 query만 전달합니다. |
| Relevance의 `{{sample.output_text}}`, TaskAdherence의 `{{sample.output_items}}` | 서비스 생성 응답 매핑입니다. 두 번째 값에는 지침·도구 호출 등 대화 항목이 포함됩니다. JSONL에 같은 이름의 열을 만들지 않습니다. |

**이 단계는 포털 설정이며 아래 함수를 실행하지 않습니다.** 원문은 09의 helper가 이미 저장된 원격 정의를 검증하는 코드입니다. UI에서 정한 값이 어떻게 `testing_criteria`·Judge·매핑으로 검사되는지 보여주며, 로컬 Judge나 별도 평가 생성 코드가 아닙니다.

<!-- source-code: scripts/add_foundry_eval_run.py:evaluation_contract -->

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

**완료 기준:** 아직 제출하지 않은 같은 생성 화면에서 두 평가기 척도·임계값·매핑·실제 Judge를 확인하고 기록했습니다. 원격 평가 정의는 06에서 제출한 뒤 생성됩니다. 이후 재평가는 그 저장된 정의를 사용합니다.
{: .completion-check}

<p class="step-next no-print"><a href="#baseline" data-next-step>다음: 06. Foundry Evaluation 실행 →</a></p>

## 06. Foundry Evaluation을 실행합니다 {#baseline}

<div class="lab-concept" data-learning-frame="baseline">
<p><strong>이 단계에서 하는 일:</strong> 고정된 v1의 실제 답변을 생성하고 관리형 평가 점수·이유를 수집합니다.</p>
<p><strong>중요한 이유:</strong> 이후 후보와 비교할 출발점이 필요합니다. Completed는 처리가 끝났다는 뜻이지 모든 답변이 정확하다는 뜻은 아닙니다.</p>
<p><strong>진행 방법·위치:</strong> Foundry에서 검토 후 한 번 제출하고 전체 12건을 확인합니다. 터미널의 읽기 전용 조회로 실제 evaluation ID와 run ID를 기록합니다.</p>
</div>

**실행 순서:** [Foundry · 검토·제출](#baseline-submit) → [12건·완료 상태 확인](#baseline-results) → [터미널 · ID 조회](#baseline-identifiers).
{: .step-route}

<p class="wizard-context" data-wizard-step="3"><strong>같은 평가 생성 과정의 3/3입니다.</strong> 04–05에서 정한 설정을 검토하고 여기서 한 번만 Submit합니다. 제출하면 실제 모델 호출 비용이 발생합니다.</p>

**Evaluation은 저장된 평가 설정**, **run은 그 설정으로 수행한 한 번의 실행**입니다. v1의 첫 실행을 **기준선(baseline)**으로 삼습니다.

### Foundry에서 검토하고 한 번 제출합니다 {#baseline-submit}

1. **Review**에서 **v1 + 원본 dev12 + query 전용 입력 + 두 평가기 + 자신의 Luna Judge**를 확인합니다.
2. 평가 이름은 **`lab-ko-learning-loop`**, run 이름을 지정할 수 있으면 **`baseline-v1`**로 입력합니다. 다른 이름을 선택했다면 `notes.md`에 기록하고 이후 조회에도 같은 이름을 사용합니다. 자신의 기준선 run이 이미 완료됐다면 다시 제출하지 않고 그 결과를 엽니다.
3. 아직 실행하지 않은 승인된 작업만 **Submit**으로 한 번 제출합니다. 단추를 누른 직후가 아니라 아래의 **Completed와 결과 12건**을 확인해야 실행 완료입니다.

<figure class="portal-shot" id="portal-evaluation-review">
<img src="../web/assets/portal/17-evaluation-review.png" alt="Foundry 평가 Review에서 Agent·버전·데이터셋·평가기 설정을 검토하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>Submit 전에 설정을 검토합니다.</strong> Agent 버전 1, 같은 dev12, query 전용 입력, 두 평가기와 Judge가 맞는지 확인합니다. 승인된 범위에서 한 번 제출한 뒤 run 상태를 확인합니다. <a href="../web/assets/portal/17-evaluation-review.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

### 같은 run의 완료 상태와 12건을 확인합니다 {#baseline-results}

**Evaluations → 방금 지정한 평가 이름 → Evaluation runs → 기준선 run**을 엽니다.

| 화면 상태 | 다음 행동 |
|---|---|
| Running / In Progress | 같은 run을 새로고침하며 기다립니다. 새로 제출하지 않습니다. |
| Completed | 전체 12건과 오류 건수를 확인한 뒤 07로 진행합니다. 모든 답변이 정답이라는 뜻은 아닙니다. |
| Failed / Partial 또는 결과 누락 | 오류와 run ID를 보존하고 [평가 문제 해결](troubleshooting.md#evaluation)을 확인합니다. 완료로 표시하지 않습니다. |

30분 또는 승인한 대기 한도 중 짧은 시간이 지나도 끝나지 않으면 현재 상태·run ID·오류를 기록하고 [평가 재개 절차](troubleshooting.md#evaluation-resume)를 확인합니다. 이는 상태를 점검할 시점이지 서비스의 완료 보장 시간이 아닙니다. 기다림을 중단해도 원격 작업은 자동 취소되지 않습니다.

### 터미널에서 실제 evaluation ID와 run ID를 조회합니다 {#baseline-identifiers}

다음 **읽기 전용 명령**으로 이름이 같은 평가의 실제 ID·run 목록을 확인합니다. 이름이 다르면 `--name`을 자신이 입력한 정확한 이름으로 바꿉니다.

```sh
python -m lab --config .lab/lab-ko/.env native-evals --name lab-ko-learning-loop
```

출력의 `evaluation_id`와 **`agent_version: "1"`, `status: completed`인 run의 `run_id`**를 기록합니다. evaluation ID는 `eval_...`, run ID는 `evalrun_...` 형태이며 둘은 다릅니다. 같은 이름의 평가가 여러 개면 포털의 생성 시각·Agent·run을 대조하여 자신의 실행을 선택합니다. 이 명령은 새 평가를 제출하지 않습니다.

#### 코드 ↔ 포털 · 제출과 조회를 구분합니다 {#baseline-code-portal}

**실행 위치:** [Foundry Submit](#baseline-submit)으로 제출하고, [위의 `native-evals` 명령](#baseline-identifiers)으로 ID를 조회합니다. 조회 명령은 평가를 새로 제출하지 않습니다.
{: .execution-guide}

| 실제 동작·코드 | 포털 조작·확인 위치 |
|---|---|
| 기준선 실행은 포털의 **Submit** | 04–05의 같은 생성 화면에서 **Review → Submit**을 한 번 누릅니다. 아래 조회 코드가 대신 제출하는 것은 아닙니다. |
| `client.evals.list(...)`, 평가 이름 비교 | **Build → Evaluations → 자신의 평가 이름**과 대조합니다. 이름이 같은 다른 평가를 섞지 않습니다. |
| `client.evals.runs.list(eval_id=...)` | 같은 평가의 **Evaluation runs**에서 버전·run 이름·상태를 대조합니다. |
| `run.id`, `target.version`, `result_counts` | 실제 v1 run ID, 완료 상태, 전체 12건·오류 수를 기록합니다. 결과의 질과 실행 완료는 다른 값입니다. |

아래가 `native-evals --name ...`의 실제 SDK 조회 구현입니다. `list`만 있고 `create`가 없다는 점을 확인합니다.

<!-- source-code: lab/managed_eval.py:list_native_evaluations -->

**완료 기준:** 실제 Foundry run이 Completed이고 결과 12건을 확인할 수 있습니다. `result_counts`의 오류·실패도 기록합니다. 실패·부분 실행을 그대로 보존하며 관리형 Evaluation을 자체 로컬 Judge로 대신하지 않습니다.
{: .completion-check}

<p class="step-next no-print"><a href="#analyze" data-next-step>다음: 07. 점수와 이유 읽기 →</a></p>

## 07. 점수와 이유를 읽습니다 {#analyze}

<a id="score-rubric"></a><a id="worked-evaluation"></a>

<div class="lab-concept" data-learning-frame="analyze">
<p><strong>이 단계에서 하는 일:</strong> 점수 뒤의 실제 답변과 평가 이유를 정책 근거에 연결합니다.</p>
<p><strong>중요한 이유:</strong> 평균만 보면 특정 날짜·인용·분류 오류가 가려집니다. 무엇이 잘못됐는지 설명해야 바꿀 지침도 정할 수 있습니다.</p>
<p><strong>진행 방법·위치:</strong> Foundry의 상세 지표·User view와 원본 정책을 나란히 읽고 notes.md에 개선 가설과 유지할 행동을 기록합니다.</p>
</div>

**실행 순서:** [Foundry · 답변·이유 확인](#analysis-details) → [편집기 · 개선 가설 기록](#analysis-notes). 별도 모델 호출은 하지 않습니다.
{: .step-route}

### Foundry에서 답변·점수·정책을 대조합니다 {#analysis-details}

1. 06에서 완료된 기준선 run을 열고 요약의 통과·미통과·오류 건수를 확인합니다.
2. **Detailed metrics result**에서 실패 또는 최저점 행을 선택하고 **`Relevance.reason`**, **`TaskAdherence.reason`**을 읽습니다. `reason`은 왜 그 점수를 줬는지 설명하는 항목입니다.
3. 그 행의 **`conversation_id → User view`**로 실제 질문·응답을 엽니다. 채점 이유는 앞의 상세 지표 화면에 있으므로 두 화면을 오가며 대조합니다.
4. 응답의 정책 ID를 [정책 원문](../data/knowledge/documents.json)에서 찾습니다. 잘한 사례도 같은 순서로 읽습니다. 실패가 없다면 그 사실을 기록하며 실패를 만들려고 v1을 약화하지 않습니다.

<figure class="portal-shot" id="portal-evaluation">
<img src="../web/assets/portal/11-evaluation-results.png" alt="Foundry 평가 결과의 요약 점수와 질문별 상세 지표를 확인하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>질문별 점수와 이유를 읽습니다.</strong> 요약의 통과·실패·오류 건수를 확인하고 Detailed metrics result에서 Relevance.reason과 TaskAdherence.reason을 읽습니다. 평균만 보지 않고 개별 사례를 확인합니다. <a href="../web/assets/portal/11-evaluation-results.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

Relevance 4/5를 정확도 80%로 해석하지 않습니다. TaskAdherence 1은 통과이지 낮은 5점 척도 점수가 아닙니다. 누락은 0점이나 성공 행이 아니며 범용 평가기가 모든 업무 규칙을 인증하지는 않습니다.

#### 코드 ↔ 포털 · 응답 구조와 품질을 함께 읽습니다 {#analysis-code-portal}

**실행 위치:** [위의 Foundry 결과 확인](#analysis-details) 후 [아래의 기록표](#analysis-notes)를 채웁니다. **이 단계에는 별도 터미널 명령이나 로컬 채점이 없습니다.**
{: .execution-guide}

| 실제 설정·결과 | 포털 조작·확인 위치 |
|---|---|
| `answer`, `citations`, `route`, `needs_human` | 행의 **conversation_id → User view**에서 네 항목의 실제 응답을 읽습니다. |
| `Relevance.reason`, `TaskAdherence.reason` | **Detailed metrics result**에서 채점 이유를 읽습니다. JSON 스키마에 정의된 필드가 아닙니다. |
| `native_response_format()`의 `strict: True` | Agent 생성 시 지정한 JSON 출력 제한입니다. 형식이 유효해도 정책 사실이 맞다는 뜻은 아닙니다. |
| 원본 스키마의 `uniqueItems`, `allOf` | 인용 중복·route/needs_human 일관성 계약입니다. 아래 변환 코드가 생성 SDK의 지원 범위와 구분하는 부분을 읽습니다. |

다음은 03에서 실제 사용하는 출력 설정 변환과 [원본 응답 계약](../schemas/response.schema.json)입니다. **07은 포털에서 결과를 읽는 단계**이며 이 코드를 다시 실행하거나 로컬 채점 결과로 대신하지 않습니다.

<!-- source-code: lab/agents.py:native_response_format -->

<!-- source-code: schemas/response.schema.json -->

**점수 읽기 예시입니다. 실제 실행 결과가 아닙니다.**

| 한 답변의 예시 점수 | 이렇게 해석합니다 |
|---|---|
| Relevance **3**, TaskAdherence **1** | 과제 지시는 따랐지만 관련성 기준 4에는 미달했습니다. 두 기준을 모두 통과한 답변은 아닙니다. |
| Relevance **5**, TaskAdherence **1** | 두 채점 기준은 통과했습니다. 그래도 사람이 정책 날짜·조건·인용의 정확성을 확인합니다. |
| 점수가 비어 있음 | 채점 오류·누락 여부를 확인합니다. 0점이나 통과로 바꾸어 기록하지 않습니다. |

<figure class="portal-shot" id="portal-evaluation-case">
<img src="../web/assets/portal/19-evaluation-case.png" alt="User view에서 질문과 Agent의 JSON 응답을 나란히 확인하는 화면입니다." width="1440" height="440" loading="lazy">
<figcaption><strong>응답을 정책과 대조합니다.</strong> User view에서 질문과 JSON 응답을 읽고 정책의 날짜·조건·인용과 비교합니다. 채점 이유는 Detailed metrics result로 돌아가 확인하며 오류가 있는 답변을 정답으로 사용하지 않습니다. <a href="../web/assets/portal/19-evaluation-case.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

날짜 경계 오류, 불필요한 가정, 정책 ID 대신 숫자 검색 ID, 사람 검토 분류 오류, 실행 완료 주장과 근거 없는 확신을 확인합니다. 정직한 불확실성을 높은 점수를 위한 허위 사실로 바꾸지 않습니다.

### 편집기에서 개선 가설과 유지할 행동을 기록합니다 {#analysis-notes}

02에서 만든 **`.lab/lab-ko/notes.md`**를 편집기로 열고 다음 표를 자신의 결과로 채웁니다. 01–06의 기록에 분석을 이어서 적습니다. 원본 응답·이유는 별도로 보관하고 표에는 해당 run·행과 짧은 관측을 남깁니다.

| 기록 항목 | 작성 방법 |
|---|---|
| 기준선 | 실제 evaluation ID, run ID, Agent 버전, 데이터 해시를 기록합니다. |
| 평가 결과 | 전체 12건 중 지표별 통과·실패·오류 건수를 기록합니다. |
| 문제 사례 | 질문, 실제 답변에서 문제가 되는 문장, 평가 이유, 해당 정책 ID를 기록합니다. |
| 개선 가설 | 예를 들어 날짜 경계를 빠뜨렸다면 발효일·포함 경계를 먼저 확인하도록 지침을 보완합니다. 정답 자체를 넣지 않습니다. |
| 유지할 행동 | 이미 잘하는 근거 인용·불확실성 표현·실행 경계를 기록합니다. |

<p class="share-checkpoint" id="share-baseline"><strong>공유:</strong> 실제 run ID·지표별 척도·통과 건수와 문제 응답을 제시하고 어떤 지침 행동을 개선할지 설명합니다.</p>

**완료 기준:** 실제 사례를 근거로 무엇을 바꾸려는지, 또는 왜 현재 지침을 유지하려는지 설명할 수 있습니다. 평균 점수만 적고 끝내지 않습니다.
{: .completion-check}

<p class="step-next no-print"><a href="#optimize" data-next-step>다음: 08. Agent Optimizer로 지침 개선 →</a></p>

## 08. Agent Optimizer로 지침을 개선합니다 {#optimize}

<a id="tune"></a>

<div class="lab-concept" data-learning-frame="optimize">
<p><strong>이 단계에서 하는 일:</strong> Agent Optimizer로 지침 개선 후보를 만들고 변경 내용을 검토합니다.</p>
<p><strong>중요한 이유:</strong> 후보 생성은 개선을 보장하지 않습니다. 내부 순위가 높아도 정책을 꾸미거나 도구·모델 조건을 바꿨다면 그대로 채택할 수 없습니다.</p>
<p><strong>진행 방법·위치:</strong> Foundry에서 Instruction only로 실행하고 View changes를 읽습니다. 검토한 지침 전체와 실제 출처를 비공개 파일에 보관합니다.</p>
</div>

**실행 순서:** [Foundry · 최적화 설정](#optimizer-configure) → [제출·결과 확인](#optimizer-results) → [편집기 · 전체 후보 지침 저장](#optimizer-candidate).
{: .step-route}

**Agent Optimizer는 더 나은 지침을 제안하고 시험하는 기능**입니다. **후보(candidate)**는 아직 채택하지 않은 지침 개선안입니다. 모델을 다시 학습시키는 기능으로 이해하지 않습니다.

#### 코드 ↔ 포털 · Optimizer는 포털에서 실행합니다 {#optimizer-code-portal}

**실행 위치:** [아래의 Foundry 최적화 절차](#optimizer-configure)를 수행하고 [후보 파일 저장](#optimizer-candidate)까지 진행합니다. **이 단계에는 터미널의 최적화 제출 명령이 없습니다.**
{: .execution-guide}

| 포털에서 조작하는 항목 | 기존 코드와의 연결 |
|---|---|
| **Agent version 1**, **Instruction only**, 모델·도구 변경 끄기 | 03에서 만든 고정 Agent 정의가 원본입니다. 다음 단계의 코드가 지침 외 구성이 같은지 다시 확인합니다. |
| **Optimization model**, **Evaluation model**, dev12·Criteria | 자신의 `.env` 배포와 04–05의 데이터·기준을 선택합니다. 로컬 프로그램이 최적화 작업을 제출하는 단계가 아닙니다. |
| **Review → Submit**, **Optimization runs** | 실제 Optimizer 실행·job 상태·후보 순위는 Foundry 서비스가 처리합니다. 터미널에서 같은 작업을 다시 제출하지 않습니다. |
| **View changes**에서 전체 지침 저장 | `.lab/lab-ko/candidate.txt`가 09의 `prompt.read_text(encoding="utf-8")` 입력이 됩니다. 원본·후보·직접 수정한 부분을 구분합니다. |
| **Promote candidate** | 이번 경로에서는 누르지 않습니다. 09의 기존 명령이 소유권·전체 구성을 확인하며 v2를 만듭니다. |

최적화는 Foundry 서비스에서 실행됩니다. 여기서 검토·저장한 지침 전체를 09의 명령에 입력으로 사용합니다.

### Foundry에서 지침만 최적화하도록 설정합니다 {#optimizer-configure}

1. **Build → Agents → lab-ko-iq → Optimize Preview/Optimize**를 엽니다.
2. **Agent / Cost** 선택 화면이 나타나면 **Agent**를 선택합니다. 비용 최적화인 **Cost**는 이번 실습 대상이 아닙니다.
3. 작업 목록의 **Optimize** 또는 **Create an optimization run / Create optimization run**을 선택하고 아래 표대로 설정합니다. **Preview는 정식 출시 전 기능**이라는 뜻입니다. 메뉴나 모델이 없다면 [Optimizer 오류 해결](troubleshooting.md#optimizer)을 확인하고 중단합니다.

| 설정 | 선택 |
|---|---|
| Agent version | 명시적 기준선 **1** |
| Choose targets | **Instruction only(지침만 변경)**, Model·Tool description·Compare across models 끄기 |
| Max candidates | 승인 범위 안에서 **2**로 요청합니다. 정식 Agent 버전 수나 모델 호출 한도가 아닙니다. |
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

### 한 번 제출하고 같은 작업의 결과를 확인합니다 {#optimizer-results}

**Review**에서 Agent·버전·데이터셋·평가기와 예상 비용을 확인한 뒤 승인된 비용 범위에서 한 번 **Submit**합니다. 예상 비용과 후보 수 설정은 청구 상한이 아닙니다.

**Optimization runs**에서 같은 job을 엽니다. 60분 또는 승인한 대기 한도 중 짧은 시간까지 확인하고, 끝나지 않으면 상태·job ID를 기록하여 [재개 절차](troubleshooting.md#optimizer)를 따릅니다. 기다림을 중단해도 작업은 자동 취소되지 않습니다.

작업 하나에도 여러 Agent·Judge·검색 호출이 포함됩니다. **Completed/Succeeded**인 작업에서 실제 생성 후보 수와 제공되는 **Token usage**를 확인합니다. 토큰 사용량은 최종 청구액이 아니며, 값이 없다고 무료였던 것은 아닙니다.

원본·후보 결과와 **View changes**를 읽습니다. 내부 **0–1 순위**는 별도 관리형 Evaluation 평균·통과율과 다릅니다. 모델·도구·추론·출력 스키마를 유지하며 함수 도구 export가 비었다고 MCP 정책 연결을 제거하지 않습니다.

<figure class="portal-shot" id="portal-optimizer-results">
<img src="../web/assets/portal/09-optimizer-results.png" alt="Agent Optimizer 결과에서 기준선과 후보별 점수·순위를 비교하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>순위뿐 아니라 후보를 확인합니다.</strong> 기준선과 후보의 평가기별 점수를 비교하고 지침 변경 내용을 검토합니다. 타당한 개선 후보가 없으면 v1을 유지하고 그 이유를 기록합니다. <a href="../web/assets/portal/09-optimizer-results.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

<figure class="portal-shot" id="portal-optimizer-diff">
<img src="../web/assets/portal/10-optimizer-changes.png" alt="View changes에서 기준선과 후보 지침의 차이를 확인하는 대화상자입니다." width="1038" height="622" loading="lazy">
<figcaption><strong>지침의 차이를 읽습니다.</strong> View changes에서 어떤 응답 행동이 바뀌는지 확인합니다. 허위 정책·근거 없는 확신·지침 외 설정 변경을 거부하며, 길이보다 내용과 효과를 검토합니다. <a href="../web/assets/portal/10-optimizer-changes.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

### 검토한 후보의 전체 지침을 파일로 저장합니다 {#optimizer-candidate}

검토한 후보가 있을 때만 다음을 수행합니다.

1. 결과의 후보를 선택하고 **View changes(변경 내용)**에서 수정된 행동을 확인합니다. 정책에 없는 조건이나 근거 없는 확신을 추가한 후보는 사용하지 않습니다.
2. **View changes**의 변경 후 지침에서 접힌 구간을 펼쳐 **지침 전체**를 복사합니다. 일부 변경 줄만 보인다면 제공되는 후보 상세·Download/Export에서 전체 내용을 확인합니다. 전체 지침을 확인할 수 없으면 [후보 파일 문제 해결](troubleshooting.md#optimizer)을 따르며 일부 diff만으로 파일을 만들지 않습니다.
3. 편집기에서 `.lab/lab-ko/candidate.txt`에 **UTF-8 일반 텍스트**로 저장합니다. Word/서식 있는 텍스트는 사용하지 않으며 파일명이 `candidate.txt.txt`가 아닌지 확인합니다. diff(변경 비교)의 `+`·`-` 표시, 화면 설명, 평가 점수는 넣지 않습니다.
4. 실제 job/candidate ID와 직접 수정한 부분·이유를 `notes.md`에 기록합니다. 다음 단계에는 이 파일을 사용하고 저장소의 `prompts/candidate.txt`로 대체하지 않습니다.

**이 실습에서는 Promote candidate를 누르지 않습니다.** 09의 CLI가 본인의 소유권 기록과 고정 구성을 확인하며 v2를 한 번 생성합니다. 포털에서 먼저 승격하면 이 경로의 소유권 확인이 맞지 않을 수 있습니다. v3·v4 등 정식 버전을 계속 만들지 않으며 새 버전 생성과 운영용 게시·활성화 승인은 구분합니다.

<p class="share-checkpoint" id="share-optimizer"><strong>공유:</strong> 검토한 후보를 제시하고 달라진 지침 행동과 개선·회귀 가능성을 설명합니다.</p>

**완료 기준:** 실제 job/candidate ID, 검토한 지침 파일과 변경 이유를 기록합니다. 유지할 후보가 없거나 전체 지침을 확보하지 못했다면 **v1 유지와 구체적인 이유**를 기록하고 10으로 이동합니다. 09를 수행하지 않았다면 별도 재평가도 미실행으로 기록합니다. 개선을 만들기 위해 같은 작업을 반복하지 않습니다.
{: .completion-check}

<p class="step-next no-print"><a href="#decision" data-next-step>검토한 후보 있음: 09 재평가 →</a> <a href="#cleanup">후보 없음: 10 정리 →</a></p>

## 09. 재평가하고 v1/v2를 비교합니다 {#decision}

<a id="review"></a><a id="operate"></a>

<div class="lab-concept" data-learning-frame="decision">
<p><strong>이 단계에서 하는 일:</strong> 지침만 다른 후보를 같은 정의로 재평가하고 v1 유지·v2 채택·판단 보류 중 하나를 기록합니다.</p>
<p><strong>중요한 이유:</strong> 버전 이름이 v2라는 사실은 개선 근거가 아닙니다. 품질뿐 아니라 실제 오류, 지연·토큰 증가와 통계적 불확실성도 함께 봐야 합니다.</p>
<p><strong>진행 방법·위치:</strong> 터미널에서 명시적 v2와 같은 평가 정의의 run을 준비한 뒤 Foundry의 Compare runs에서 전체 사례를 비교합니다. 운영에는 게시하지 않습니다.</p>
</div>

**실행 순서:** [터미널 · v2 생성](#decision-agent) → [같은 평가에 run 추가](#decision-run) → [Foundry · v1/v2 비교](#decision-compare).
{: .step-route}

**01–03에서 만든 자신의 환경과 08에서 저장한 후보 파일을 사용합니다.** 버전 생성은 본인 계정·로컬 소유 기록·원격 Agent 구성을 대조합니다. 불일치하면 [Agent 문제 해결](troubleshooting.md#knowledge)을 확인하며 다른 사람의 설정에서 사용자 이름만 바꾸어 우회하지 않습니다.
{: .note}

### 1. 터미널에서 검토한 지침으로 v2를 생성합니다 {#decision-agent}

모델·도구·데이터·평가기·Judge는 유지하고 v1은 보존합니다.

```sh
python -m lab --config .lab/lab-ko/.env native-agent --version 2 --prompt .lab/lab-ko/candidate.txt --confirm
```

`agent_name: lab-ko-iq`, `version: "2"`를 확인합니다. 다른 내용의 v2가 이미 있거나 모델 배포가 바뀌었으면 중단하고 기존 기록을 보존합니다. 새 버전이 있다는 사실만으로 개선이 입증되지 않습니다.

### 2. 터미널에서 같은 평가에 v2의 run을 추가합니다 {#decision-run}

아래 helper는 이 저장소가 제공하는 Python 보조 프로그램입니다. 공식 Azure AI Projects/OpenAI SDK로 기준선의 데이터·평가기 설정을 재사용합니다. 다른 평가를 새로 만드는 것이 아닙니다.

| 자리표시자 | 실제 값을 찾는 곳 |
|---|---|
| `YOUR_PROJECT_ENDPOINT` | `.lab/lab-ko/.env`의 `AZURE_AI_PROJECT_ENDPOINT` 값입니다. |
| `YOUR_SUBSCRIPTION_ID` | 01의 구독 ID 또는 같은 `.env`의 `AZURE_SUBSCRIPTION_ID` 값입니다. |
| `YOUR_EVALUATION_ID` | 06의 `native-evals` 출력에서 선택한 `evaluation_id`입니다. |
| `YOUR_BASELINE_RUN_ID` | 같은 평가에서 완료된 버전 1의 `run_id`입니다. Optimizer job ID가 아닙니다. |

네 값을 교체하고 다음 한 줄 명령을 실행합니다. 새 run 제출에는 비용이 발생합니다.

```sh
python scripts/add_foundry_eval_run.py --endpoint "YOUR_PROJECT_ENDPOINT" --subscription "YOUR_SUBSCRIPTION_ID" --evaluation "YOUR_EVALUATION_ID" --baseline "YOUR_BASELINE_RUN_ID" --version 2 --name candidate-v2 --out .lab/lab-ko/artifacts/foundry-evaluations/candidate-v2.json
```

기본 대기는 30분입니다. 승인한 한도가 더 짧다면 `--wait-seconds`와 초 단위 값을 추가합니다. 완료되면 `status: completed`, `result_counts.total: 12`와 결과 12건을 확인합니다.

대기 한도를 넘으면 종료 코드 2와 **Still running** 안내가 나오며 원격 작업은 계속될 수 있습니다. receipt에 run ID가 있으면 **같은 명령·같은 `--out`**으로 수집을 재개합니다. run ID가 없거나 같은 이름의 원격 run이 있으면 [중복 제출 방지 절차](troubleshooting.md#evaluation)를 따릅니다. receipt를 삭제하거나 이름을 바꾸어 다시 제출하지 않습니다.

helper는 임계값·Judge·매핑과 각 결과 행의 Agent 버전·지침을 확인합니다.

#### 코드 ↔ 포털 · 같은 평가에 v2 실행을 추가합니다 {#decision-code-portal}

**실행 위치:** [위의 v2 생성](#decision-agent)과 [run 추가 명령](#decision-run)을 실행한 뒤 [아래의 Foundry 비교](#decision-compare)를 수행합니다. 코드로 제출한 run을 포털 Add run으로 다시 제출하지 않습니다.
{: .execution-guide}

| 실제 코드·필드 | 포털 조작·확인 위치 |
|---|---|
| `native-agent --version 2`, `prompt.read_text(...)` | **Build → Agents → 같은 Agent → Version 2 → Instructions**에서 검토한 전체 후보 지침을 확인합니다. 구현은 03에 표시한 두 함수와 같습니다. |
| `candidate_source()`가 기준선 `data_source`를 복사하고 `target["version"]`만 변경 | 같은 평가·등록된 데이터·query 전용 입력을 유지합니다. 새 데이터나 평가를 만들지 않습니다. |
| `project.agents.get_version(...)`와 지침 외 구성 비교 | v1·v2의 Model·Knowledge/Tools·출력 설정이 같아야 합니다. SDK가 읽은 전체 정의가 비교 근거입니다. |
| `client.evals.runs.create(**saved["request"])` | 같은 평가의 **Evaluation runs**에 `candidate-v2`가 생깁니다. 코드로 제출했으므로 포털 Add run을 다시 누르지 않습니다. |
| `runs.retrieve(...)`, `output_items.list(...)` | 해당 run의 완료 상태·전체 12건을 확인합니다. 저장된 receipt의 run ID로 조회를 재개합니다. |
| 두 실제 run ID | **Evaluation runs → v1·v2 선택 → Compare runs → Baseline v1**로 비교합니다. |

아래 첫 함수는 **바뀌는 데이터 소스 필드**, 두 번째는 **실제 SDK 제출과 중복 방지**, 마지막은 **SDK 연결·대기·전체 결과 수집**입니다. 실행할 것은 위 helper 명령 하나이며 원문을 독립적으로 다시 실행하지 않습니다.

<!-- source-code: scripts/add_foundry_eval_run.py:candidate_source -->

<!-- source-code: scripts/add_foundry_eval_run.py:submit_or_resume -->

<!-- source-code: scripts/add_foundry_eval_run.py:main -->

### 3. Foundry에서 같은 평가의 v1/v2를 비교합니다 {#decision-compare}

같은 평가의 **Evaluation runs**에서 v1·v2 두 행을 선택하고 **Compare runs**를 엽니다. **Baseline을 v1으로 명시 선택**하며 행 선택 순서 때문에 비교 방향이 바뀌지 않게 합니다.

<figure class="portal-shot" id="portal-evaluation-comparison">
<img src="../web/assets/portal/20-evaluation-comparison.png" alt="Compare runs에서 기준선과 후보의 점수·평균·통계 결과를 비교하는 화면입니다." width="1440" height="520" loading="lazy">
<figcaption><strong>비교 방향과 결과를 함께 확인합니다.</strong> Baseline을 v1으로 선택하고 두 run의 점수·통과 건수·통계 결과를 비교합니다. Inconclusive는 차이가 입증되지 않았다는 뜻이며 동등성의 증거로 해석하지 않습니다. <a href="../web/assets/portal/20-evaluation-comparison.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

12건 전체의 응답·점수·이유를 나란히 비교합니다. 전체 기준 통과와 각 지표의 통과 건수·평균이 낮아지지 않고 하나 이상이 명확히 개선되어야 합니다. 사실·분류·응답 형식도 확인하며 지연·토큰·통계 결과를 함께 기록합니다.

<p class="share-checkpoint" id="share-optimized"><strong>결과 설명:</strong> 실제 개선, 같은 평가 기준, 회귀와 남은 불확실성을 설명합니다. 관측된 개선이 향후 모든 확률적 실행의 개선을 보장하지는 않습니다.</p>

`notes.md`에 v1/v2의 지표별 통과 건수·평균, 오류, 지연·토큰, 통계 결과와 최종 판단을 나란히 기록합니다. 개선 조건을 만족하지 않으면 **v1 유지 또는 판단 보류**로 기록합니다. 범용 평가가 통과했어도 실제 정책 오류가 있으면 채택하지 않습니다.

**지연(latency)**은 응답을 기다린 시간, **토큰(tokens)**은 모델이 처리한 텍스트 양의 단위입니다. 점수가 조금 좋아져도 시간·비용 부담이 커질 수 있습니다.

| 최종 판단 | 선택할 때 |
|---|---|
| v2 채택 후보 | 같은 조건의 12건에서 품질이 나빠지지 않고 하나 이상 개선됐으며, 정책 오류가 없고 지연·토큰의 부담도 검토했습니다. 운영용 게시 승인은 별도입니다. |
| v1 유지 | 개선이 없거나 기존에 잘하던 동작이 나빠졌습니다. 이것도 정상적인 학습 결과입니다. |
| 판단 보류 | 실패·누락·비교 조건 차이로 아직 공정하게 판단할 수 없습니다. 부족한 근거를 기록합니다. |

**완료 기준:** 실제 두 run ID와 같은 조건의 전체 비교, 채택·유지·보류 이유를 기록합니다. 정식 버전을 누적하지 않습니다. 운영 승인·독립적 일반화는 별개이며 dev12 실습으로 부여되지 않습니다.
{: .completion-check}

<p class="step-next no-print"><a href="#cleanup" data-next-step>다음: 10. 결과 보관·리소스 삭제 →</a></p>

## 10. 결과를 보관하고 리소스를 삭제합니다 {#cleanup}

<a id="troubleshooting"></a><a id="sources"></a>

<div class="lab-concept" data-learning-frame="cleanup">
<p><strong>이 단계에서 하는 일:</strong> 결과를 보관한 뒤 자신이 만든 전용 실습 자원을 삭제합니다. 보존을 승인받은 경우에만 남은 자원과 비용 관리 계획을 기록합니다.</p>
<p><strong>중요한 이유:</strong> 브라우저를 닫아도 Search·로그 등은 남을 수 있습니다. 반대로 공유 그룹을 잘못 삭제하면 다른 사람의 자원도 잃을 수 있습니다.</p>
<p><strong>진행 방법·위치:</strong> Azure Portal과 터미널에서 정확한 대상·소유권·승인을 확인하고 삭제 후 부재를 검증합니다.</p>
</div>

**실행 순서:** [결과 보관](#cleanup-records) → [삭제·보존 범위 확인](#cleanup-scope) → [승인된 전용 그룹 삭제](#cleanup-delete) → [터미널 · 부재 확인](#cleanup-verify). 보존 승인된 환경은 삭제하지 않습니다.
{: .step-route}

**브라우저 종료·Agent 삭제·`cleanup` 실행만으로 리소스 그룹 전체의 과금이 멈추지는 않습니다.**

### 삭제 전에 기록을 보관합니다 {#cleanup-records}

1. `notes.md`에 실제 프로젝트·Agent·데이터셋 버전·해시, 평가/run/job ID와 최종 판단을 남깁니다.
2. 평가·Optimizer 화면에서 제공하는 **Download/Export**로 결과를 받습니다. 메뉴가 없으면 보관한 receipt와 상세 결과를 사용하며, 받을 수 없는 결과를 받았다고 기록하지 않습니다.
3. `.lab/lab-ko/`의 계획·manifest·승인·실행 기록을 조직이 허용한 비공개 위치에 보관합니다. 인증 정보·쿠키·서명된 URL·계정 정보가 있는 원본을 Git에 올리지 않습니다. 공개용 기록에는 필요한 합성 사례·점수·이유만 남깁니다.
4. Evaluations와 Optimization runs에서 실행 중인 작업을 확인합니다. 지원되는 **Cancel**을 사용하고 종료 상태를 확인합니다. 종료되지 않은 작업의 ID·상태와 후속 확인 계획을 기록하며 취소 요청만으로 종료됐다고 표시하지 않습니다.

### 삭제할 대상과 보존 여부를 확인합니다 {#cleanup-scope}

| 환경 | 정리 범위 |
|---|---|
| 02에서 본인이 만든 전용 리소스 그룹 · 기본 경로 | 아래 전용 그룹 삭제 절차를 사용합니다. 그룹 안에 다른 업무 자원이 없고 삭제가 승인된 범위인지 다시 확인합니다. |
| 보존하도록 승인받은 전용 환경 · 예외 | 삭제 명령을 실행하지 않습니다. 실제 남은 자원·보존 이유·비용 책임·보존 검토일과 이후 삭제 계획을 기록합니다. |
| 삭제 목록에 공유·외부 자원이 포함됩니다. | **해당 자원은 삭제하지 않습니다.** 실습 범위를 벗어난 종속성을 확인하고 승인된 처리 범위가 정해질 때까지 그룹 삭제를 중단합니다. |
| 생성·실습 중간에 중단한 환경 | `config.json`·manifest와 Azure의 실제 자원을 대조합니다. 실패했다고 자원이 없다고 가정하지 않습니다. |

**기본 경로는 자신의 전용 그룹 전체 삭제입니다.** 보관·대상 확인이 끝나면 [다음 절](#cleanup-delete)로 진행합니다. 그룹 전체를 삭제할 때 개별 객체를 먼저 삭제할 필요는 없습니다. 아래 `cleanup`은 **그룹을 보존하면서 기록된 객체만 정리할 때** 사용하는 별도 선택 사항입니다.

#### 선택 사항 · 그룹을 보존하면서 기록된 객체만 정리합니다 {#cleanup-objects}

자신의 `.env`와 로컬 소유 기록이 있는 경우 다음 명령으로 **삭제 계획만** 확인할 수 있습니다. 생성 도중 중단되어 `.env`가 없다면 객체 정리 명령을 실행하지 않고 `config.json`·manifest로 실제 그룹을 확인합니다.

```sh
python -m lab --config .lab/lab-ko/.env cleanup
```

`mode: LOCAL_PLAN_ONLY`, `actions`, `never_deleted`, `manual_follow_up`를 읽습니다. 삭제 대상의 이름·프로젝트·소유자를 확인하고 해당 범위의 삭제 승인을 받은 경우에만 다음을 실행합니다. 자신의 환경 이름이 다르면 prefix도 동일하게 바꿉니다.

```sh
python -m lab --config .lab/lab-ko/.env cleanup --confirm-prefix lab-ko
```

`mode: OWNED_OBJECTS_ABSENT`인지 확인합니다. 이 도구는 기록된 Agent 버전·검색 객체·연결 등을 삭제하지만 **리소스 그룹·모델 배포·Search 서비스·로그·RBAC는 삭제하지 않습니다.** 포털에서 만든 데이터셋·평가·Optimizer 작업·Playground 대화와 모델 smoke 응답도 전부 자동 정리하지 않습니다. 승인된 항목은 해당 화면에서 개별 삭제합니다. 삭제 기능이 없는 항목은 남은 목록과 보존 이유를 기록하고, 전용 그룹 전체 삭제 여부를 별도로 결정합니다.

#### 코드 ↔ 포털 · 객체 정리와 그룹 삭제를 구분합니다 {#cleanup-code-portal}

**실행 위치:** 기본 경로는 [전용 그룹 삭제](#cleanup-delete) 후 [부재 확인](#cleanup-verify)입니다. 보존 승인된 그룹에서 객체만 지울 때에만 [위의 선택 사항 `cleanup`](#cleanup-objects)을 사용합니다. 두 경로를 모두 수행할 필요는 없습니다.
{: .execution-guide}

| 기존 명령·실제 구현 | 포털 조작·확인 위치 |
|---|---|
| `cleanup_plan()`의 `actions`, `never_deleted`, `manual_follow_up` | 로컬 소유 기록에서 만든 계획입니다. 해당 Agent 버전·Search 객체·프로젝트 연결 이름을 포털과 대조합니다. 출력에 다른 라이브러리 경로의 후속 안내가 있어도 이번 실습에 그 작업을 추가하지 않습니다. |
| `cleanup()`의 `delete_version`, REST `DELETE`, 이후 `GET` | 확인한 기록 객체만 삭제하고 부재를 조회합니다. 개별 삭제도 승인 범위에서만 수행하며 포털 삭제와 중복 실행하지 않습니다. |
| 아래의 `az group show`, `az resource list` | Azure Portal **Resource groups → 자신의 그룹 → Overview/Resources**에서 전체 인벤토리와 태그를 읽습니다. |
| 아래의 `az group delete` | 포털 **Delete resource group**과 같은 그룹 전체 삭제 경로입니다. 둘 중 한 방법만 실행합니다. |
| `az group exists`의 성공한 `false` | 삭제 후의 실제 부재 확인입니다. 포털 알림·그룹 목록과 대조합니다. 오류를 false로 해석하지 않습니다. |

원문에서 **확인 인자가 없으면 계획 반환**, **원격 소유권·etag 확인**, **개별 DELETE**, **다시 조회하여 remaining 검사** 순서를 읽습니다. 그룹 전체 삭제는 이 함수 안에 없고 다음 절의 기존 Azure CLI 명령 또는 포털에서 별도로 수행합니다.

<!-- source-code: lab/cleanup.py:cleanup_plan -->

<!-- source-code: lab/cleanup.py:cleanup -->

### 전용 리소스 그룹을 삭제하고 부재를 확인합니다 {#cleanup-delete}

`YOUR_LAB_RESOURCE_GROUP`을 `config.json`의 **`names.resource_group`**으로 교체합니다. 이름의 prefix만 보고 판단하지 않고 구독·소유 태그·목록 전체를 확인합니다.

```sh
az group show --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP" --query "{name:name,location:location,tags:tags}" -o json
az resource list --subscription "YOUR_SUBSCRIPTION_ID" --resource-group "YOUR_LAB_RESOURCE_GROUP" --query "[].{name:name,type:type}" -o table
```

**그룹 전체 삭제는 되돌릴 수 없으며 그룹 안의 Foundry·모델·Search·모니터링 자원이 함께 삭제됩니다.** 보관이 끝났고 정확한 그룹 전체를 삭제하도록 승인받은 경우에만 다음 두 방법 중 하나를 선택합니다.

Application Insights의 기본 Smart Detection Action group은 다른 그룹의 경고에서도 공유할 수 있습니다. 전용 실습 그룹이라는 이유만으로 모든 항목이 독립적이라고 가정하지 않습니다. 공유 연결이 있으면 담당자와 종속성을 먼저 정리하거나 해당 그룹을 보존하며, 확인을 위해 경고·권한·잠금을 임의로 삭제하지 않습니다.

1. **포털 방법:** Azure Portal → Resource groups → 정확한 그룹 → **Delete resource group**을 선택합니다. 삭제 목록을 읽고 요구하는 그룹 이름을 직접 입력한 뒤 확인합니다.
2. **CLI 방법:** 다음 명령을 실행하고 확인 질문에서 이름·범위를 다시 확인한 뒤 동의합니다. `--yes`를 붙여 확인을 생략하지 않습니다.

<figure class="portal-shot" id="portal-delete-review">
<img src="../web/assets/portal/28-delete-review.png" alt="리소스 그룹 삭제 확인 창의 대상 목록, 그룹 이름 입력란과 Delete·Cancel 버튼입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>삭제 예정 목록과 확인란을 먼저 읽습니다.</strong> 그룹 이름과 전체 자원 목록을 대조합니다. 승인받은 경우에만 확인란에 그룹 이름을 입력하고 Delete로 진행합니다. 대상이 다르거나 승인되지 않았다면 Cancel로 닫습니다. <a href="../web/assets/portal/28-delete-review.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

```sh
az group delete --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP"
```

### 터미널에서 삭제 후 부재를 확인합니다 {#cleanup-verify}

삭제 요청 수락은 완료가 아닙니다. 포털 알림과 그룹 상태를 확인하고 다음 명령이 성공적으로 **`false`**를 출력하는지 확인합니다.

```sh
az group exists --subscription "YOUR_SUBSCRIPTION_ID" --name "YOUR_LAB_RESOURCE_GROUP"
```

권한 오류·네트워크 오류는 `false`가 아니며 삭제 성공으로 처리하지 않습니다. `true`이면 삭제 진행 상태를 확인합니다. **Locks**, 권한, 다른 그룹의 종속 자원 때문에 실패하면 [삭제 문제 해결](troubleshooting.md#cleanup)을 따릅니다. 조직이 설정한 잠금을 임의로 제거하지 않습니다.

삭제 뒤 **Cost Management → Cost analysis**에서 해당 구독·기간·리소스 그룹을 확인합니다. 청구 반영에는 지연이 있으며 기존 사용 요금은 사라지지 않습니다. 별도 그룹의 로그·저장소나 서비스별 soft-delete 보존 항목은 따로 확인합니다. 영구 삭제/purge는 조직 정책과 별도 승인이 있을 때만 수행합니다.

**최종 완료 기준:** 삭제 승인된 자신의 전용 그룹에 대해 `az group exists`의 `false`와 확인 시각을 기록했습니다. 보존 승인된 경우에는 실제 남은 항목·이유·비용 책임·보존 검토일과 후속 삭제 계획을 기록했습니다. 둘 중 자신의 승인 범위에 맞는 상태를 확인하고 `.lab` 기록을 먼저 지워 소유권 근거를 잃지 않습니다. [정리 체크리스트](admin-setup.md#cleanup) · [삭제 문제 해결](troubleshooting.md#cleanup)을 참고합니다.
{: .completion-check}
