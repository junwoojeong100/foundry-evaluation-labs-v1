# 실습 문제 해결 {#issue-guide}

[실습 10단계](handbook.md#setup) · [권한·승인·설정 참고](admin-setup.md#approval)

**막힌 단계에서 증상·조치·진행 기준을 확인합니다.** 오류를 해결하기 위해 데이터·평가기·모델을 조용히 바꾸거나 새 이름으로 같은 작업을 중복 제출하지 않습니다.

실행할 명령은 **터미널에서 실행** 상자에 있습니다. 각 단계의 **실행 순서** 링크로 명령·포털 절차를 찾습니다. **선택 · 내부 동작** 안의 코드·포털 대응표와 구현 원문은 참고용이며 직접 실행하거나 오류를 숨기려고 수정하지 않습니다.

| 현재 증상 | 확인할 곳 |
|---|---|
| HTML에서 설명만 보이고 실행 명령을 찾을 수 없습니다. | 단계 상단의 **실행 순서**를 사용합니다. 선택 설명을 펼칠 필요는 없습니다. [로그인 명령](handbook.md#setup-login) · [런타임 검사](handbook.md#resources-runtime-check). |
| 용어·설치·로그인·파일 경로가 어렵습니다. | [기본 용어](handbook.md#basics) · [Codespaces](#codespaces) · [환경·로그인](#environment) |
| 승인·권한·모델 용량 때문에 생성할 수 없습니다. | [생성 준비](#provisioning) |
| 정책 검색이나 Agent 응답이 실패합니다. | [정책·Agent](#knowledge) |
| 평가가 끝나지 않거나 점수·이유가 보이지 않습니다. | [평가·결과 조회](#evaluation) |
| Optimize가 없거나 후보를 선택하기 어렵습니다. | [Optimizer](#optimizer) |
| 삭제가 안 되거나 자원을 보존해야 합니다. | [정리·보존](#cleanup) |

## 사용 방법 {#start}

오류 시각·단계·명령·대상 ID·오류 코드와 조치를 자신의 메모에 남깁니다. 원본 응답·receipt를 보관하고 실패를 성공으로 고쳐 쓰지 않습니다. 실행별 검증 로그와 결과는 재사용 가이드에 추가하지 않습니다.

## 환경·로그인·로컬 파일 {#environment}

Python·Git·Microsoft Azure CLI 설치와 PATH 문제는 Microsoft Azure 로그인 전에 해결합니다.

| 증상 | 조치 | 진행 기준 |
|---|---|---|
| `py`·`python3.13`·`git`·`az`가 `command not found` 또는 `not recognized`입니다. | [01의 운영체제별 설치](handbook.md#setup-local)를 마치고 터미널을 모두 닫았다가 다시 엽니다. VS Code도 재시작합니다. 계속 실패하면 설치 경로의 PATH 등록을 담당자와 확인하며 Windows는 `Get-Command py, git, az`, macOS/Linux는 `command -v git az`로 경로를 확인합니다. | [세 도구의 버전 확인](handbook.md#setup-verify)이 같은 새 터미널에서 성공합니다. |
| `winget` 또는 `brew`가 없습니다. | Windows는 [공식 설치 파일 경로](handbook.md#setup-windows)를 사용합니다. macOS는 [Homebrew 설치와 Next steps](handbook.md#setup-macos)의 PATH 설정을 완료합니다. | 설치 방법 하나로 필요한 도구를 준비하고 버전을 확인합니다. 조직의 설치 제한을 우회하지 않습니다. |
| Python 대신 Microsoft Store가 열리거나 `py`가 없습니다. | Windows의 일반 Python 설치에서 Launcher·pip·PATH 옵션을 확인하고 새 PowerShell에서 `py -3.13 --version`을 실행합니다. 다른 지원 버전을 설치했다면 해당 번호를 사용합니다. | Store 바로가기가 아닌 설치한 Python 3.11–3.14가 실행됩니다. |
| Python 버전이 3.11–3.14 밖이거나 다른 Python으로 `.venv`를 만들었습니다. | 시스템 Python을 교체하지 말고 지원 버전을 별도로 선택합니다. `py -3.13` 또는 `python3.13` 등 [버전을 확인한 같은 명령](handbook.md#setup-venv)으로 실습용 환경을 준비합니다. 기존 `.venv`는 소유 작업과 보관 필요성을 먼저 확인합니다. | 가상환경의 `python --version`이 지원 범위이고 `python -m pip --version`의 경로가 그 `.venv` 안입니다. |
| Linux에서 `No module named venv` 또는 `ensurepip is not available`입니다. | [Ubuntu 설치 순서](handbook.md#setup-linux)의 `python3-venv`를 설치합니다. 버전 지정 Python이면 해당 버전에 맞는 venv 패키지를 담당자와 확인합니다. | 선택한 Python으로 `.venv` 생성과 pip 확인이 성공합니다. |
| 다운로드·설치가 설치 권한·프록시·인증서 오류로 막힙니다. | 공식 다운로드 주소·오류와 조직의 허용 설치 경로를 확인합니다. 필요한 설치·네트워크 승인을 확보하고 TLS 검증·보안 도구·조직 정책을 해제하지 않습니다. | 승인된 경로로 설치하고 세 도구의 버전 확인이 성공합니다. |
| `.venv/bin/activate` 또는 `Activate.ps1`이 없습니다. | 저장소 폴더에서 가상환경을 먼저 만들고 자신의 OS에 맞는 [설치 순서](handbook.md#setup-local)를 따릅니다. | 같은 Python의 `python -m pip --version`과 `python -m lab --help`가 성공합니다. |
| `ModuleNotFoundError`가 나옵니다. | 사용할 가상환경을 확인하고 그 Python으로 `python -m pip install -r requirements.lock`을 실행합니다. | 같은 환경에서 필요한 import와 데이터 검사가 성공합니다. |
| PowerShell 활성화가 정책으로 차단됩니다. | 조직 정책을 바꾸지 않고 `.\.venv\Scripts\python.exe`로 명령을 실행합니다. | 정책 변경 없이 Python을 실행할 수 있습니다. |
| 새 터미널을 열었더니 이전 설정이 적용되지 않습니다. | [재개 절차](handbook.md#setup-resume)로 기존 가상환경을 활성화하고 명령의 원래 `--config` 경로를 사용합니다. 언어·기록 변수 설정과 clone·plan·apply를 반복하지 않습니다. | `az account show`로 원래 신원을, 읽기 전용 재개 확인으로 마지막 완료 단계를 확인하고 같은 기록으로 이어갑니다. |
| `agents/`·`knowledge/` 실행 기록 파일을 찾을 수 없습니다. | [기록 폴더 안내](handbook.md#resources-notes)에 따라 해당 환경의 `artifacts/` 아래에서 찾습니다. `data/`·`scripts/`는 저장소 폴더 아래입니다. | 예시 경로가 아닌 자신의 언어·환경 기록을 엽니다. |
| 포털과 CLI의 계정이 다릅니다. | 브라우저와 CLI는 별도 로그인입니다. [01의 로그인·조회 명령](handbook.md#setup-login)으로 사용자·tenant·subscription을 포털과 대조하고 본인 인증은 직접 완료합니다. | 승인한 세 값이 모두 일치합니다. 다른 신원이나 토큰 복사로 우회하지 않습니다. |
| `AzureCliCredential`의 tenant·subscription 동시 지정이 실패합니다. | tenant 일치를 먼저 확인한 뒤 credential에는 subscription을 지정하는 저장소 인증 경로를 사용합니다. | tenant 확인을 생략하지 않고 같은 구독으로 호출합니다. |
| 다른 언어 또는 환경의 기록이 선택됩니다. | 명령의 `--config`가 원래 `.lab/lab-ko/.env`를 가리키는지 확인합니다. [언어·기록 위치는 이 설정에서 자동 적용](handbook.md#setup-language)되며 터미널 변수로 바꾸지 않습니다. | 데이터·설정·workspace·결과가 같은 환경입니다. 기존 기록을 덮어쓰지 않습니다. |
| 과거 기록이 저장소의 공통 `artifacts/`에 있습니다. | 이전 실행의 설정·언어·소유권을 확인하고 기록을 그대로 보관합니다. 다른 폴더로 자동 이동하거나 새 기록으로 대체하지 않으며 [설정 참고](admin-setup.md#runtime-settings)를 확인합니다. | 원래 기록의 위치를 확인하기 전에는 유료 작업을 다시 제출하지 않습니다. |

## GitHub Codespaces {#codespaces}

| 증상 | 조치와 진행 기준 |
|---|---|
| Create codespace가 없거나 사용 한도를 초과했습니다. | 계정·조직의 허용 정책과 Codespaces 비용 한도를 확인합니다. 허용되지 않으면 [내 PC 경로](handbook.md#setup-local-install)를 사용하며 조직 정책을 우회하지 않습니다. |
| 초기 준비 중 `az`·`.venv`·패키지가 없습니다. | 컨테이너의 생성 로그에서 `.devcontainer/devcontainer.json`과 의존성 설치 실패를 확인합니다. 준비가 완료될 때까지 생성 명령을 실행하지 않습니다. 기존 Codespace에 새 구성을 적용해야 한다면 비공개 기록을 보관한 뒤 명령 팔레트의 **Codespaces: Rebuild Container**를 사용합니다. `.lab`을 지우지 않습니다. |
| device-code 로그인이 차단됩니다. | 조직이 허용한 인증·실행 환경을 확인합니다. 승인된 내 PC에서 `az login`의 브라우저 로그인으로 진행할 수 있으며, 코드를 타인에게 보내거나 보안 정책을 바꾸지 않습니다. |
| 포털 Browse에서 `dev.jsonl`이 보이지 않습니다. | Browse는 내 PC 파일을 고릅니다. [Codespaces Explorer에서 Download](handbook.md#dataset-download)한 원본 파일을 선택합니다. |
| `candidate.txt`를 만들었는데 찾을 수 없습니다. | 내 PC가 아니라 **실습 터미널과 같은 Codespace**의 `.lab` 아래에 저장했는지 [후보 저장 절차](handbook.md#optimizer-candidate)로 확인합니다. |
| 사설망 자원에 연결할 수 없습니다. | Codespaces가 해당 VNet/VPN에 연결됐다고 가정하지 않습니다. 승인된 네트워크의 실행 환경을 사용하며 public access나 방화벽을 임의로 바꾸지 않습니다. |
| 명령이 실행되는 동안 Codespace가 중지되거나 연결이 끊어졌습니다. | [내 Codespaces](https://github.com/codespaces)에서 다시 시작하고 **Terminal → New Terminal**을 연 뒤 [재개 절차](handbook.md#setup-resume)를 따릅니다. 먼저 상태를 조회합니다. 생성은 [`bootstrap status`](handbook.md#resources-status), 평가는 [`native-evals`](handbook.md#baseline-identifiers), 재평가는 [09의 재개 규칙](handbook.md#decision-run)을 사용합니다. `apply`를 반복하거나 이름을 바꿔 다시 제출하지 않습니다. 중지된 Codespace를 사용하지 않고 두면 기본 30일 뒤 자동 삭제되므로 [`.lab/` 백업](handbook.md#cleanup-codespaces)을 보관합니다. |
| 재개 또는 삭제할 Codespace를 모르겠습니다. | 원래 저장소·Codespace와 그 안의 `.lab/<환경 이름>/` 폴더를 대조합니다. [백업·중지·삭제 순서](handbook.md#cleanup-codespaces)를 따르며 새 Codespace를 만들고 Microsoft Azure 자원까지 중복 생성하지 않습니다. |

## 생성·승인·할당량 {#provisioning}

| 증상 | 조치 | 진행 기준 |
|---|---|---|
| `setup`을 취소했거나 입력 오류로 끝났습니다. | 자원이 생성되기 전이라면 같은 환경 이름으로 `bootstrap setup`을 다시 실행해 원래 계획을 사용합니다. 실제 승인값을 입력하며 잘못된 금액·시간·빈 승인 근거를 임의로 채우지 않습니다. | 마지막 `CREATE ...` 확인 전에 Microsoft Azure 변경은 없습니다. 기존 생성 기록이 있으면 조회만 수행합니다. |
| `setup requires an interactive terminal`입니다. | VS Code의 **Terminal → New Terminal**에서 직접 실행합니다. 셸 파이프·자동 작업은 [개별 계획·승인 경로](handbook.md#resources-plan)를 사용합니다. | 비대화형 실행이 자동으로 승인되지 않습니다. |
| 기존 `approval.json`이 만료됐거나 범위가 다릅니다. | 원본을 보존하고 [승인 작성표](admin-setup.md#approval)로 실제 재승인 범위와 시각을 확인합니다. setup은 승인 파일을 덮어쓰거나 만료를 연장하지 않습니다. | 현재 유효하고 정확한 계획에 연결된 승인만 사용합니다. |
| plan이 `BLOCKED_AWAITING_APPROVAL`입니다. | `plan_status`와 `mutations_performed`를 확인하고 [실제 승인서](admin-setup.md#approval)를 준비합니다. | 로컬 계획 생성과 Microsoft Azure 생성 완료를 구분합니다. |
| `approved: true`인데 승인 오류입니다. | 해시·모델·승인자·유효기간·예산·동의 항목과 `approval_reason`을 확인합니다. | readiness가 READY이고 승인이 READY_FOR_APPROVED_APPLY입니다. |
| Provider가 Registered가 아닙니다. | [공급자 등록 절차](admin-setup.md#rbac)에서 본인의 등록 권한·승인을 확인하고 필요한 공급자만 등록합니다. | 네 공급자가 Registered가 된 뒤 같은 preflight를 실행합니다. |
| Contributor인데 역할 할당이 막힙니다. | 자원 생성과 역할 할당은 별도 권한입니다. 본인이 이 실습을 수행할 수 있도록 필요한 실행 범위의 승인을 확보합니다. | 필요한 유효 권한을 확인한 뒤 같은 계획으로 재개합니다. 구독 전체 Owner를 새로 부여해 우회하지 않습니다. |
| 모델·SKU·버전·quota·capacity 오류입니다. | 계획의 역할별 요청과 preflight 이유를 확인합니다. 대체가 필요하면 별도 계획·승인을 받습니다. | 지원 모델과 할당량을 확인하고 실제 호출까지 확인합니다. |
| 런타임 `*_tpm` 항목이 BLOCKED입니다. | [모델별 TPM 설정](admin-setup.md#throughput)에서 실제 배포 한도를 확인합니다. | 다섯 TPM 항목과 전체 preflight가 PASS입니다. |
| 생성 후 `unknown resource`가 나옵니다. | 자신의 Application Insights에 연결된 기본 Smart Detection인지, 다른 업무 자원이나 변경된 수신자인지 확인합니다. 생성 중이면 연결 전파를 기다립니다. | 같은 `bootstrap status`로 확인합니다. 경고 삭제나 manifest 편집으로 우회하지 않습니다. |
| apply가 시간 초과 또는 결과 불명입니다. | 원래 config·manifest·deployment ID를 보관하고 [02의 `bootstrap status` 명령](handbook.md#resources-status)과 그룹의 Deployments를 읽습니다. `apply`는 다시 실행하지 않습니다. | 진행 중이면 기다리며 결과 불명 상태에서 다시 제출하지 않습니다. |
| 같은 로컬 환경이 이미 있습니다. | 같은 실습은 원본 config로 재개합니다. 별도 실습만 새 환경 이름과 승인을 사용합니다. | 기존 계획·설정·자원을 임의로 인수하거나 덮어쓰지 않습니다. |

`--retry`는 확인된 소유 배포의 종료된 실패와 별도 재시도 승인 한도에만 사용합니다. `repair-dependencies`, `repair-trace-routing`도 일치하는 실패 근거와 해당 범위의 승인이 필요한 복구 명령입니다. `APPLIED`는 인프라 상태이며 품질·운영 승인·로그 수집 성공을 뜻하지 않습니다.

## 정책 검색·Agent 준비 {#knowledge}

| 증상 | 조치와 진행 기준 |
|---|---|
| 배포는 있지만 모델 호출이 실패합니다. | 카탈로그·배포와 런타임 지원은 다릅니다. API 오류와 역할별 지원을 확인하고 [03의 실제 응답](handbook.md#agent)을 확인합니다. |
| `created_not_retrieval_tested`에서 멈춥니다. | 생성만 완료된 상태입니다. [03의 `iq probe` 명령](handbook.md#agent-search-probe)에서 `retrieval_verified`와 실제 출처를 확인합니다. |
| 직접 검색은 되지만 Agent 도구가 403입니다. | 프로젝트 관리 ID의 Search 읽기·모델 호출 권한과 연결 audience를 확인합니다. 사용자 검색 성공만으로 판단하지 않습니다. |
| `native-agent` 실행 후 구성 불일치 오류입니다. | receipt와 원격 버전을 먼저 조회합니다. MCP 도구 목록의 동등한 표현은 정규화하지만, 다른 도구·권한·모델·출력 설정은 허용하지 않습니다. receipt를 지우거나 새 버전을 만들어 우회하지 않습니다. |
| 기존 v2와 지침 또는 모델이 다릅니다. | 고정 비교 보호 동작입니다. v2를 덮어쓰거나 v3를 만들지 않고 원래 소유 환경·지침·모델 snapshot을 대조합니다. |
| 언어별 검색 결과가 다릅니다. | 선택 언어의 원본 문서·인덱스·analyzer·해시를 확인합니다. 이름만 바꾸어 다른 언어의 인덱스를 재사용하지 않습니다. |
| 사설망 또는 `PublicNetworkAccess=Disabled` 오류입니다. | 승인된 VNet/VPN/실행 환경과 DNS를 확인합니다. 방화벽·private endpoint를 해제하지 않습니다. |

## Microsoft Foundry 평가·재개 {#evaluation}

### Add run의 item-schema 오류 {#evaluation-add-run}

다음 메시지가 나오면 기존 평가의 Agent 대상 data source 구성을 확인합니다.

**오류 메시지 예시 · 실행하지 않습니다.**
{: .output-label}

```text
Unable to create data source configuration from item schema
```

[09의 `scripts/add_foundry_eval_run.py`](handbook.md#decision)는 완료된 기준선의 원격 data source를 복사하고 명시적 후보 버전만 바꿉니다. 같은 evaluation ID·데이터 등록·Judge·임계값·응답 매핑과 전체 12건의 실제 버전·지침을 확인합니다. 새 데이터나 로컬 Judge로 대신하지 않습니다.

### ID와 중복 제출 {#evaluation-resume}

| 증상 | 조치 |
|---|---|
| evaluation ID·run ID를 모릅니다. | [06의 전체 `native-evals` 명령](handbook.md#baseline-identifiers)으로 조회합니다. evaluation은 `eval_...`, 기준선은 완료된 버전 1의 `evalrun_...`입니다. |
| 같은 이름의 평가가 여러 개입니다. | 생성 시각·Agent·데이터·run을 대조합니다. 이름만으로 임의 선택하지 않습니다. |
| helper가 Still running으로 끝났습니다. | receipt에 run ID가 있으면 같은 명령으로 수집을 재개합니다. |
| receipt에 run ID가 없거나 같은 이름의 원격 run이 있습니다. | 원본을 보관하고 제출 수락 여부와 실제 run을 확인합니다. receipt 삭제·이름 변경·자동 재제출을 하지 않습니다. |
| 버전 선택 뒤 체크가 사라집니다. | 명시적 v1을 선택한 뒤 체크박스를 다시 선택하고 대상 하나를 확인합니다. |
| 데이터 미리 보기가 5행입니다. | 원본 12행·등록 버전·실제 결과 전체 건수를 대조합니다. 미리 보기만으로 판단하지 않습니다. |
| 점수나 이유가 보이지 않습니다. | 실제 답변은 `conversation_id → User view`, 이유는 Detailed metrics result의 `Relevance.reason`·`TaskAdherence.reason`에서 읽습니다. |
| 필수 response 칸이 Unassigned입니다. | [매핑 점검](admin-setup.md#evaluation-mapping)에서 Agent 대상·query 열·서비스 생성 응답 매핑을 대조합니다. JSONL에 정답을 response 열로 추가하지 않으며 해결 전에는 제출하지 않습니다. |
| 결과 행·점수가 빠졌습니다. | 실패·누락을 보관하고 분모 12를 줄이지 않습니다. 점수를 0이나 통과로 만들어 넣지 않습니다. |

## Agent Optimizer·결과 해석 {#optimizer}

| 증상 | 조치와 진행 기준 |
|---|---|
| No custom evaluators available입니다. | **Custom only OFF** 또는 **View built-in evaluators**를 사용합니다. 필터 때문에 새 custom evaluator를 만들지 않습니다. |
| Optimize나 지정 모델이 없습니다. | New Foundry, prompt Agent, 프로젝트 권한, Preview와 [역할별 모델 지원](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)을 확인합니다. |
| 승인한 대기 시간이 지났는데 작업이 실행 중입니다. | Optimization runs에서 같은 job ID의 상태·오류·사용량을 확인하고 이후 조회 계획을 기록합니다. 기다림 종료는 취소가 아닙니다. 새 작업으로 다시 제출하지 않습니다. |
| 작업이 Failed/Canceled이거나 결과가 일부만 있습니다. | 실제 상태·job ID·오류를 보관합니다. 완료한 후보가 있는 것처럼 기록하거나 같은 요청을 이름만 바꾸어 반복하지 않습니다. |
| View changes에 일부 diff만 있고 전체 지침을 복사할 수 없습니다. | 접힌 변경 후 구간·후보 상세와 제공되는 Download/Export를 확인합니다. 전체 지침을 확보하지 못하면 v2를 만들지 않고 “v1 유지·전체 지침 확인 불가”를 기록한 뒤 10으로 진행합니다. |
| 후보가 모델·도구 설명도 바꿉니다. | **Instruction only**와 모델 비교 끄기를 확인합니다. 지침 외 설정 변경을 같은 조건의 비교로 표시하지 않습니다. |
| 후보에 정책 날짜·수치·평가 정답 예시가 들어갑니다. | 원본 서비스 출력을 보관하고 내장된 정답을 제거하거나 후보를 거부합니다. 직접 수정한 부분·이유·출처를 기록하고 별도로 재평가합니다. |
| 다른 후보 없이 기준선만 선택됐습니다. | v1 유지 이유를 기록하고 10으로 이동합니다. 없는 v2를 만들거나 개선을 위해 같은 작업을 반복하지 않습니다. |
| 내부 순위와 재평가 결과가 다릅니다. | 내부 0–1 순위와 별도 평가 점수·통과율은 다릅니다. 실제 응답·정책 오류·회귀도 확인합니다. |
| TaskAdherence가 1입니다. | 이진 척도의 통과입니다. Relevance의 1–5점 척도와 혼동하지 않습니다. |
| 통계가 Inconclusive입니다. | 차이가 입증되지 않았다는 뜻입니다. 유의성이나 동등성의 증거로 바꾸어 해석하지 않습니다. |
| 품질과 함께 지연·토큰도 증가합니다. | 상충 관계를 함께 기록합니다. 미확인 청구액을 0원으로 표시하지 않습니다. |

## 정리·보존·지속 비용 {#cleanup}

| 증상 | 조치와 진행 기준 |
|---|---|
| 리소스를 보존하도록 승인받았습니다. | 삭제 명령을 실행하지 않습니다. 실제 목록·보존 이유·비용 책임·보존 검토일·후속 삭제 계획을 기록하고 재접속에 필요한 소유권·설정을 유지합니다. |
| cleanup 뒤에도 Search 비용이 남습니다. | `cleanup`은 기록된 객체만 정리하며 서비스·모델·그룹·로그는 남깁니다. [10의 승인된 정리 또는 보존](handbook.md#cleanup)을 확인합니다. |
| `.env`나 workspace가 없습니다. | config·manifest와 실제 Microsoft Azure 목록으로 대상을 확인합니다. 소유권 기록을 임의로 만들어 삭제하지 않습니다. |
| 그룹 안의 모니터링이 다른 그룹과 연결됩니다. | 공유 Action group 등 종속성을 담당자와 확인합니다. 전용 그룹이라는 이유만으로 공유 자원을 삭제하지 않습니다. |
| 삭제가 Locks·권한·종속성 때문에 실패합니다. | Locks·Activity log와 실패 작업을 읽습니다. 본인에게 허용된 조치 범위를 확보한 뒤 재개하며 조직 잠금을 임의로 해제하지 않습니다. 삭제가 막힌 상태를 완료로 표시하지 않습니다. |
| 삭제 요청 후에도 그룹이 남습니다. | 비동기 진행을 확인하고 [10의 부재 확인 명령](handbook.md#cleanup-verify)을 실행합니다. 성공한 `az group exists`가 `false`인 경우에만 부재로 기록합니다. |
| 삭제 뒤에도 비용이 표시됩니다. | 사용 기간과 청구 반영 지연, 외부 그룹의 잔여 자원을 확인합니다. 과거 사용 요금은 사라지지 않습니다. |

서비스별 soft-delete 보존 항목과 영구 삭제/purge는 별도 정책·승인 대상입니다. [리소스 그룹 삭제 문서](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group)를 참고합니다.
