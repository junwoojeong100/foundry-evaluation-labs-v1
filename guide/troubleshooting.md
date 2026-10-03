# 실행 중 발견한 문제와 해결 기록 {#issue-guide}

[처음부터 진행하는 가이드](handbook.md#setup) · [운영자 승인·인수](admin-setup.md#approval) · [실제 품질 측정](verification.md)

**막힌 위치에서 증상·원인·해결·확인 순서로 읽는 문서입니다.** 과거 Azure 실측, 이번 읽기 전용 확인, 로컬 검사를 구분합니다. 해결 방법을 작성했다는 사실만으로 새 클라우드 실행에 성공했다고 표시하지 않습니다.

## 기록 범위와 사용 방법 {#start}

| 구분 | 근거와 한계 |
|---|---|
| 이전 서비스 실행 | 기존 가이드·포털 캡처와 `evidence/latest.json`에 기록된 2026-10-01 기준 리허설입니다. 공개 품질 수치는 영어 실행입니다. |
| 2026-10-03 읽기 전용 확인 | 기존 실습의 CLI 사용자·테넌트·구독 일치를 확인했습니다. `native-evals`로 같은 평가의 v1·v2와 초안 run 상태를 조회했습니다. |
| 2026-10-03 문서·코드 개선 | 처음 준비하는 경로, 네이티브 Agent 생성 명령, ID 조회, 삭제 경계와 국문 문체를 보완합니다. 검사 방법과 범위는 [마지막 절](#verification)에 기록합니다. |
| 이번에 수행하지 않은 작업 | 새 Azure 리소스 생성·역할 변경·데이터 업로드·유료 평가·Optimizer 재실행·실제 클라우드 삭제입니다. 기존 측정을 새 한국어 실행으로 표시하지 않습니다. |

새 문제가 발생하면 비공개 `notes.md`에 **시각·단계·명령·오류 코드·대상 ID·수정 내용·재확인 결과**를 기록합니다. 공개할 때는 구독·계정 식별자, 토큰, 쿠키, 서명된 URL을 제거합니다. 실패한 응답과 불리한 평가 결과는 숨기지 않습니다.

## 환경·로그인·로컬 파일 문제를 해결합니다 {#environment}

| 증상 | 원인과 해결 | 다음 단계로 진행할 기준 |
|---|---|---|
| 가이드가 이미 준비된 프로젝트·Agent부터 시작합니다. | 이전 참가자 가이드는 6단계 평가 경로만 있었고 관리자 준비도 기존 환경을 전제했습니다. 새 [01–03](handbook.md#setup)에 계정·설치·생성·검색·Agent 준비를 연결했습니다. | 자신의 프로젝트·Agent·실제 도구 응답을 확인합니다. 문서 링크 검사 성공만으로 준비 완료라고 보지 않습니다. |
| `.venv/bin/activate` 또는 `Activate.ps1`이 없습니다. | 먼저 저장소 폴더에서 가상환경을 생성합니다. Windows와 macOS/Linux 활성화 경로가 다릅니다. [설치 순서](handbook.md#setup-local)를 따릅니다. | 가상환경의 `python -m pip --version`과 `python -m lab --help`가 성공합니다. |
| `ModuleNotFoundError`가 나옵니다. | 다른 Python을 사용하거나 잠금 의존성을 설치하지 않은 상태입니다. 가상환경의 Python으로 `python -m pip install -r requirements.lock`을 실행합니다. | 같은 Python으로 데이터 검사와 필요한 명령을 실행합니다. |
| PowerShell 활성화가 정책으로 차단됩니다. | 정책을 임의로 변경하지 않고 `.\.venv\Scripts\python.exe`로 명령을 실행합니다. | 정책 변경 없이 해당 Python의 실행을 확인합니다. |
| 포털에는 구독이 있지만 CLI에서는 다른 계정이 나옵니다. | 브라우저와 CLI는 독립적으로 로그인합니다. 디렉터리·구독 필터와 `az account show`의 사용자·tenant·subscription을 대조합니다. | 승인한 세 값이 모두 일치합니다. 다른 신원으로 자동 전환하지 않습니다. |
| `AzureCliCredential`에서 tenant와 subscription을 동시에 전달한 인증이 실패합니다. | Azure CLI의 두 인자를 함께 쓰는 인증 경로가 호환되지 않습니다. `lab/auth.py`는 tenant 일치를 먼저 확인하고 credential에는 subscription만 전달합니다. | 신원 확인을 통과한 동일 구독으로 호출합니다. tenant 검증을 삭제하지 않습니다. |
| 한국어 실행이 영어 artifacts 또는 반대 경로에 기록됩니다. | `LAB_LANGUAGE`와 `LAB_ARTIFACTS_DIR`를 Python 시작 전에 설정해야 합니다. `.env`를 읽는 것만으로 이미 import된 artifacts 경로가 바뀌지 않습니다. | 언어별 폴더와 workspace의 언어가 일치합니다. 기존 기록을 덮어쓰지 않습니다. |

첫 번째 두 항목은 이번 원문 점검에서 확인한 안내 누락입니다. 인증 인자와 언어 분리는 기존 구현·회귀 검사로 확인한 제약이며, 이번에 새로운 인증 실패나 새 유료 호출을 만들지는 않았습니다.

## 생성·승인·할당량 문제를 해결합니다 {#provisioning}

| 증상 | 조치 | 확인 방법 |
|---|---|---|
| plan 결과가 `BLOCKED_AWAITING_APPROVAL`입니다. | 로컬 계획은 생성됐지만 지출은 미승인 상태입니다. `plan_status`와 `mutations_performed`를 구분합니다. | `CREATED_LOCAL_ONLY`·`false`를 확인하고 [승인서 작성](admin-setup.md#approval)을 진행합니다. |
| `approved: true`인데 승인 오류입니다. | hash/model 불일치, 다른 승인자, 과거·미래·시간대 없는 시각, 누락된 예산·동의가 원인일 수 있습니다. `approval_reason`을 읽고 실제 승인 범위만 수정합니다. | preflight의 readiness READY와 승인 READY_FOR_APPROVED_APPLY를 모두 확인합니다. |
| Provider가 Registered가 아닙니다. | 구독 관리자가 해당 공급자를 조직 절차에 따라 등록합니다. bootstrap은 자동 등록하지 않습니다. | 네 공급자의 등록 완료 후 같은 preflight를 실행합니다. |
| Contributor인데 role assignment에서 막힙니다. | 자원 생성과 역할 할당 권한은 별개입니다. 이미 승인된 프로비저닝 담당자가 실행하도록 합니다. | 필요한 유효 권한을 확인합니다. 구독 Owner를 새로 부여하는 우회는 사용하지 않습니다. |
| 모델/SKU/버전/지역 용량·할당량 오류입니다. | `config.json`의 역할별 요청과 preflight `reason`을 확인합니다. 지원되는 대체 모델이 필요하면 역할별 지원을 검토하고 새 계획·승인을 받습니다. | 카탈로그·quota·capacity 확인 후 실제 Agent와 도구 호출까지 확인합니다. |
| apply가 시간 초과 또는 결과 불명입니다. | 원래 config·manifest·deployment ID를 보존하고 `bootstrap status`와 Azure Portal의 그룹 **Deployments**에서 상태를 읽습니다. | 진행 중이면 기다립니다. 실패·결과 불명이 해소되기 전 새 환경이나 재제출을 만들지 않습니다. |
| 이미 있는 환경이라고 나옵니다. | 기존 계획을 덮어쓰지 않는 보호 동작입니다. 원래 config로 status를 확인합니다. | 같은 실습은 원본으로 재개하고 별도 실습만 새로운 승인 범위로 만듭니다. |
| 기존 실패 복구 문서의 명령 이름이 맞지 않습니다. | 실제 CLI는 `repair-dependencies`, `repair-trace-routing`입니다. 이전 인프라 설명의 다른 명칭을 정정했습니다. | `python -m lab.bootstrap --help`와 대조합니다. 이 명령은 일반 재시도가 아니며 일치하는 실패 증거와 별도 승인 절차가 필요합니다. |

`--retry`는 확인된 소유 배포의 **종료된 실패**와 명시적 재시도 승인 한도에만 사용합니다. unknown 상태의 POST를 다시 보내는 옵션이 아닙니다. `APPLIED`는 인프라 생성 완료이며 모델 품질·운영 승인·로그 수집 성공의 증거는 아닙니다.

## 정책 검색과 Agent 준비 문제를 해결합니다 {#knowledge}

| 증상 | 조치 | 확인 방법 |
|---|---|---|
| 카탈로그에는 있지만 실제 Agent가 실패합니다. | 배포 성공과 Agent 런타임 지원은 다릅니다. 실제 API 오류·모델·버전·도구 경로를 기록합니다. | [03의 smoke와 실제 Agent 호출](handbook.md#agent)을 확인합니다. |
| `created_not_retrieval_tested`에서 멈춥니다. | 생성만 완료된 상태입니다. `iq probe`를 실행하고 응답·references·activity를 확인합니다. | `retrieval_verified`와 실제 출처를 확인합니다. |
| 직접 검색은 성공하지만 Agent 도구는 403입니다. | 직접 검색은 사용자 CLI 신원, Agent 연결은 프로젝트 관리 ID를 사용합니다. 프로젝트 ID의 Search 읽기·모델 호출 권한과 연결 audience를 확인합니다. | Agent 실행 안에서 `knowledge_base_retrieve`의 성공 응답을 확인합니다. |
| 영어·한국어 검색 결과가 일관되지 않습니다. | `lab/knowledge.py`는 선택 언어의 `en.microsoft` 또는 `ko.microsoft` analyzer를 사용합니다. 원래 언어·인덱스·문서 hash를 유지합니다. | 언어별 회귀 검사와 실제 검색을 구분합니다. 이름만 바꾸어 기존 인덱스를 재사용하지 않습니다. |
| Agent 생성 방법이 함수 이름만 있고 실행 명령이 없습니다. | 이번에 `native-agent --version 1/2`를 기존 `ensure_fixed_release`에 연결했습니다. 정책 MCP와 엄격한 JSON, 소유권·모델 snapshot도 함께 사용합니다. | 로컬 회귀 검사를 수행합니다. 신규 환경의 실제 생성·도구 응답은 실습자가 별도로 확인합니다. |
| 기존 v2와 지침이 다르거나 모델이 바뀌었습니다. | 고정 비교 보호 동작입니다. 다른 v2를 덮어쓰거나 v3를 만들지 않고 기록을 보존합니다. | 같은 소유 Agent·모델·도구·출력 설정과 의도한 지침을 대조합니다. |
| `PublicNetworkAccess=Disabled` 또는 사설망 연결 timeout입니다. | 승인된 VNet/VPN/조직 실행 환경을 사용합니다. 방화벽·private endpoint를 해제하지 않습니다. | 네트워크 소유자와 DNS·연결을 확인한 뒤 같은 endpoint로 재확인합니다. |

## Foundry 평가와 재개 문제를 해결합니다 {#evaluation}

### 포털 Add run에서 item-schema 오류가 발생했습니다 {#evaluation-add-run}

**이전 실습에서 관측한 메시지입니다.**

```text
Unable to create data source configuration from item schema
```

포털의 Add run이 기존 Agent 대상 data source를 다시 구성하지 못한 사례입니다. 서비스 전체 장애나 모든 구독의 동일 현상으로 일반화하지 않습니다.

**해결:** [09의 `scripts/add_foundry_eval_run.py`](handbook.md#decision)를 사용하여 완료된 기준선의 원격 data source를 복사하고 명시적 후보 버전만 바꿉니다. 같은 managed evaluation 정의에 실제 run을 제출합니다. 로컬 Judge, 수정된 JSONL, 새 평가 기준으로 대신하지 않습니다.

**확인:** 같은 evaluation ID, 원본 데이터 등록, Relevance 4·TaskAdherence 1, 같은 Judge·응답 매핑을 확인하고 전체 12건의 실제 버전·지침을 확인합니다. 이전 완료된 v1·v2 run은 이번 읽기 전용 조회에서도 확인했습니다. 이번에 오류를 재현하기 위해 새 유료 run을 제출하지는 않았습니다.

### 잘못된 ID와 중복 제출을 방지합니다 {#evaluation-resume}

| 증상 | 해결 |
|---|---|
| evaluation ID·run ID를 어디서 찾는지 모릅니다. | `native-evals --name`으로 실제 목록을 조회합니다. evaluation은 `eval_...`, baseline run은 완료된 버전 1의 `evalrun_...`입니다. |
| 같은 evaluation 이름이 여러 개입니다. | 포털의 시각·Agent·데이터·run과 대조합니다. 이름만으로 임의 선택하지 않습니다. |
| helper가 Still running으로 종료했습니다. | receipt에 run ID가 있으면 같은 명령·동일 out 경로로 수집을 재개합니다. |
| receipt가 있지만 run ID가 없습니다. | 제출 수락 여부가 불명입니다. 원본을 보존하고 포털·서비스 상태를 확인합니다. receipt 삭제·다른 run 이름·자동 재제출을 사용하지 않습니다. |
| 같은 이름의 원격 run이 이미 있습니다. | 기존 run을 열거나 원래 receipt를 복구합니다. 새 이름으로 중복 실행하지 않습니다. |
| v1 선택 후 대상 체크가 사라집니다. | 명시적 v1을 고른 뒤 Agent 체크박스를 다시 선택하고 대상이 한 개인지 확인합니다. |
| 데이터 미리 보기가 5행입니다. | 미리 보기 제한일 수 있습니다. 원본 12행·등록 버전·실제 결과 전체 건수를 대조합니다. |
| TaskAdherence 1이 낮은 점수처럼 보입니다. | 이 평가기는 이진 0/1이며 1은 통과입니다. Relevance의 1–5 척도와 섞지 않습니다. |
| 화면에서 이유가 보이지 않습니다. | `conversation_id → User view`는 질문·답변입니다. 이유는 **Detailed metrics result**의 `Relevance.reason`·`TaskAdherence.reason`에서 읽습니다. |
| 결과 행이나 점수가 빠졌습니다. | 실패·누락을 그대로 기록하고 분모 12를 줄이지 않습니다. 점수를 0 또는 성공으로 만들어 넣지 않습니다. |

## Agent Optimizer와 결과 해석 문제를 해결합니다 {#optimizer}

| 관측 또는 증상 | 해결과 확인 |
|---|---|
| 이전 UI에서 **No custom evaluators available**이 보였습니다. | **Custom only OFF** 또는 **View built-in evaluators**를 사용했습니다. 필터를 해결하기 위해 다른 custom evaluator를 만들 필요는 없습니다. |
| Optimize가 없거나 지정 모델이 선택되지 않습니다. | New Foundry, prompt Agent, 프로젝트 권한, Preview 제공 여부, 역할별 지원 모델을 확인합니다. 공개 문서와 테넌트 지원이 다르면 제공 상태를 기록하고 중단합니다. |
| 후보가 모델·도구 설명도 바꿨습니다. | **Choose targets → Instruction only**와 모델 비교 끄기를 확인합니다. 지침 외 설정이 다르면 같은 조건의 비교로 표시하지 않습니다. |
| 실제 Optimizer가 기존 v1을 유지했습니다. | `evidence/latest.json`의 기존 실행은 강한 기준선을 선택했습니다. 이를 실패로 숨기거나 자동 후보 승격으로 바꾸어 기록하지 않습니다. |
| 지침을 사람이 추가로 수정했습니다. | “Optimizer 이후 운영자 검토”로 출처를 기록하고 같은 관리형 평가를 별도로 수행합니다. 기존 공개 v2도 이 경우입니다. |
| 순위는 올랐지만 재평가 결과가 다릅니다. | Optimizer 내부 0–1 순위와 별도 평가 평균·통과율은 다릅니다. 전체 응답·정책 오류·회귀를 함께 확인합니다. |
| 평균은 좋아졌지만 통계가 Inconclusive입니다. | 기존 비교는 Relevance 4.8333 → 4.9167이며 서비스 PairedTTest는 Inconclusive입니다. 유의성이나 동등성으로 바꾸어 해석하지 않습니다. |
| 품질과 함께 지연·토큰도 증가했습니다. | 기존 v2의 p95는 10.97 → 42.97초, Agent 토큰은 46,167 → 55,858입니다. 개선 판단에서 이 상충 관계를 함께 보고합니다. |

원본 점수·응답·채점 이유와 실제 실행 ID는 [최신 품질 보고서](verification.md#status)에 있습니다. 개발에 재사용한 합성 12건은 독립적 일반화나 운영 안전을 입증하지 않습니다.

## 삭제와 비용 종료 문제를 해결합니다 {#cleanup}

| 증상 | 해결과 확인 |
|---|---|
| 이전 가이드가 결과 인계에서 끝났습니다. | [10의 실제 삭제 절차](handbook.md#cleanup)에 전용/공유 환경 분기, 대상 확인, 승인, 그룹 삭제와 부재 확인을 추가했습니다. |
| cleanup 성공 뒤에도 Search 비용이 남습니다. | `cleanup`은 소유 객체만 정리하며 Search 서비스·모델·그룹·로그는 남깁니다. 전용 그룹 전체 삭제 또는 운영자의 보존 계획을 확인합니다. |
| workspace 또는 `.env`가 없어 cleanup을 실행할 수 없습니다. | 실패한 setup의 config·manifest와 Azure 인벤토리로 대상부터 확인합니다. 로컬 상태를 만들어 소유권을 꾸미지 않습니다. |
| 그룹 삭제가 Locks/권한/종속성 때문에 실패합니다. | Azure Portal의 **Locks**, **Activity log**, 실패한 삭제 작업을 확인합니다. 잠금 소유자에게 해당 범위 조치를 요청하고 임의 해제하지 않습니다. |
| 삭제 요청은 수락됐지만 그룹이 남아 있습니다. | 비동기 진행을 확인합니다. 성공한 `az group exists`가 `false`인 경우에만 그룹 부재로 기록합니다. |
| 그룹은 없어졌지만 비용 화면에 금액이 있습니다. | 과거 사용 요금과 집계 지연은 정상적으로 남을 수 있습니다. 기간·리소스·잔여 외부 자원을 확인합니다. |
| soft-delete 보존 항목이 있습니다. | 서비스별 보존 정책을 확인합니다. 영구 삭제/purge가 필요한지 담당자가 판단하고 별도로 승인합니다. |

[Azure 리소스 그룹 삭제 문서](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group)를 기준으로 확인합니다. 그룹 삭제는 되돌릴 수 없으며 일부 개별 서비스의 복구 기능이 그룹 복구를 보장하지 않습니다.

## Portal 그림과 설명 형식을 보완했습니다 {#portal-captures}

2026-10-03에 사용자가 로그인한 뒤 **Playwright Headless**로 신규 화면 파일 14개를 촬영했습니다. 로그인용 임시 브라우저와 인증된 Headless 컨텍스트는 작업 후 닫았으며 인증 상태를 별도 파일로 내보내지 않았습니다. 그림에는 불투명 가림과 자르기만 적용하고 실제 상태·실패 이력·지침은 바꾸지 않았습니다.

| 보완 단계 | 추가한 그림과 읽는 방법 |
|---|---|
| 01 환경·권한 | 구독 Essentials와 Check access의 공통 화면 2개입니다. 상태·역할·Scope를 구분합니다. |
| 02 생성 확인 | 언어별 리소스 목록·기존 프로젝트 선택·project endpoint 화면 3개입니다. 프로젝트 선택은 추가 생성이 아닙니다. |
| 03 정책·Agent | 언어별 Knowledge 연결과 고정 v1 설정 화면 2개입니다. Active·Save 비활성 상태와 실제 검색·평가 성공을 구분합니다. |
| 10 정리 | 언어별 삭제 전 확인 창 1개입니다. 예정 자원 목록·빈 확인란·비활성 Delete를 확인하고 촬영 후 Cancel로 닫았습니다. |

언어마다 기존 12개에 새 화면 8개를 연결하여 전체 가이드의 그림은 20개입니다. 공통 그림 2개를 두 번 복제하지 않으므로 실제 신규 파일은 14개입니다. 한국어·영어 Agent와 지식 화면은 각 언어의 기존 프로젝트에서 별도로 촬영했습니다.

| 실제로 확인한 차이·문제 | 반영한 해결 |
|---|---|
| 제공된 참고 URL의 `.htm`이 404였습니다. | 같은 저장소의 실제 `index.ko.html`을 확인했습니다. 목표·개념·준비·실행·완료·문제 해결의 형식만 참고하고 데이터·채점 방법은 가져오지 않았습니다. |
| 포털 상태는 Active인데 CLI는 Enabled입니다. | 같은 정상 구독의 표기 차이를 01과 캡션에 명시했습니다. 서로 같은 문자열을 찾도록 안내하지 않습니다. |
| 최신 IAM은 View my access 대신 Check access입니다. | 실제 활성 할당과 Scope 위치를 촬영하고 두 UI 명칭을 함께 안내합니다. |
| New Foundry 토글이 곧바로 체크되지 않았습니다. | 기존 프로젝트 선택 대화상자와 Let's go가 먼저 필요했습니다. 단순 체크박스 완료로 처리하지 않고 실제 선택 화면을 안내합니다. |
| 자원 목록·삭제 창이 별도 React iframe에 있습니다. | 바깥 문서뿐 아니라 iframe 안의 구독·식별 정보도 가린 뒤 그림을 확인했습니다. |
| 삭제 창에 “resources being deleted”가 보입니다. | 실제 삭제 진행이 아닌 예정 목록임을 설명합니다. 확인란·Delete 버튼 상태와 실제 그룹 부재는 별도로 확인합니다. |
| Knowledge에 무료 검색 배너가 있습니다. | 전체 실습 무료 또는 요금제 변경 필요로 해석하지 않도록 설명합니다. 요금제 변경은 수행하지 않았습니다. |

**촬영 전후 실제 확인 결과입니다.** 자원 ID, Agent별 버전 목록, 평가와 run ID 목록을 읽기 전용으로 대조했습니다.

| 환경 | 자원 수 전/후 | Agent·버전 수 전/후 | 평가·run 수 전/후 |
|---|---|---|---|
| 기존 한국어 실습 | 5 / 5 | Agent 3 / 3, 버전 4 / 4 | 평가 2 / 2, run 7 / 7 |
| 기존 영어 실습 | 6 / 6 | Agent 6 / 6, 버전 10 / 10 | 평가 6 / 6, run 23 / 23 |

새 리소스·Agent 버전·평가·Optimizer 작업을 만들거나 삭제하지 않았고 채팅·검색 질문도 제출하지 않았습니다. 영문 Agent의 표시된 v1 지침 해시는 저장소 기준선과 같았습니다. 한국어 그림은 문체 개정 이전 원격 v1 지침을 있는 그대로 보여 주며 이를 새 실행으로 표시하지 않습니다.

해시·크기·가림 범위와 상태는 [한국어 촬영 명세](../web/assets/portal/captures.json), [영어 명세](../web/assets/portal/en/captures.json), [공통 관리 화면 명세](../web/assets/portal/shared/captures.json)에 기록합니다. 기존 사진·평가 데이터·실측 JSON은 그대로 보존합니다.

**보완판 확인:** 자동 검사 582개를 통과했습니다. 두 언어의 1440px 데스크톱·390px 모바일에서 개요 카드 4개, 단계별 설명 10개, 본문 그림 18개와 운영자 참고 그림 2개를 확인했습니다. 새 그림 위치의 언어 전환, 읽음·테마 유지, 원본 이미지 열기와 JavaScript 없는 탐색이 동작했고 화면 전체 가로 넘침·페이지 오류는 없었습니다.

## 앞선 10단계 개편의 검사 기록입니다 {#verification}

아래 579개 검사와 그림 12개씩을 포함한 PDF 확인은 **추가 촬영 전에 완료한 10단계 개편 당시의 기록**입니다. 이후 Portal 그림·형식 보완은 위 절과 촬영 명세에서 구분합니다. 이전 확인 수치를 새 파일의 검사 결과로 바꾸어 표시하지 않습니다.

**실제 확인한 읽기 전용 결과입니다.** 2026-10-03에 기존 승인 환경의 CLI 신원 세 값과 Enabled 상태를 확인했습니다. `native-evals`는 기존 `contoso-en-sol-learning-loop`에서 v1·v2 각각 12건의 completed 결과와 별도 초안 run을 조회했습니다. 공개 보고서의 v1 11/12, v2 12/12와 일치했습니다. 새 평가·최적화·Agent·삭제 요청은 보내지 않았습니다.

**로컬 재현 명령입니다.** 가상환경에서 실행하며 새 Azure 자원을 만들지 않습니다.

이번 자동 검사에서는 `--help`가 정상 종료 코드 0의 `SystemExit`를 반환하는 점과 macOS 임시 경로의 `/var` 심볼릭 링크를 확인했습니다. 검사 코드는 정상 도움말 종료를 구분하고 임시 디렉터리를 실제 경로로 변환하도록 수정했습니다. bootstrap의 심볼릭 링크 차단을 해제하거나 사용자 파일을 이동하지 않았습니다.

| 이번에 수행한 확인 | 확인 결과 |
|---|---|
| 로컬 실행 | 양쪽 가이드의 계획 생성·미승인 apply 차단·행 수/해시 명령을 실행했습니다. 전체 자동 검사 579개가 통과했습니다. |
| 브라우저 | 두 언어를 1440px 데스크톱과 390px 모바일에서 확인했습니다. 10단계 탐색·언어 전환·읽음 기록·테마 유지와 JavaScript 없는 탐색이 동작했습니다. 화면 전체 가로 넘침과 페이지 오류는 없었습니다. |
| 인쇄본·PDF | 두 언어의 통합본에 각각 언어에 맞는 포털 그림 12개를 포함했습니다. 필수 본문·로컬 경로 링크·페이지 밖 텍스트·거의 빈 페이지 검사를 통과했습니다. |
| 플랫폼 범위 | 실제 실행 환경은 macOS입니다. Windows PowerShell 명령은 별도로 제공하지만 Windows에서 실행 완료했다고 주장하지 않습니다. |

```bash
python scripts/build_datasets.py --language ko --check
python scripts/build_datasets.py --language en --check
python scripts/build_guide.py --check
python -m unittest discover -s tests -q
```

PDF 검사 첫 직접 실행에서 `ModuleNotFoundError: pymupdf`를 관측했습니다. 선택한 가상환경에서 import와 버전을 다시 확인하고 다음 모듈 진입점으로 두 파일을 정상 검사했습니다. import 실패의 원인을 확정하지 않았으므로 패키지 불량으로 단정하지 않습니다. PDF 검사 패키지가 실제로 없다면 유지보수 환경에만 `requirements-verification.lock`을 설치합니다.

```bash
python -m scripts.verify_pdf docs/Foundry-Learning-Loop-Lab-KO.pdf --language ko --out .lab/verification/pdf-ko.json
python -m scripts.verify_pdf docs/Foundry-Learning-Loop-Lab-EN.pdf --language en --out .lab/verification/pdf-en.json
```

검사는 양쪽 HTML의 10단계·대응 앵커·링크·명령 인자, 고정 Agent의 소유권·구성 불변성, 읽기 전용 ID 조회와 중복 제출 보호를 확인합니다. 로컬 mock은 새로운 Azure 생성·과금·삭제 성공의 증거가 아닙니다. 신규 실습은 본문 각 단계의 실제 완료 기준까지 직접 확인합니다.

한국어 작성 지침의 문체도 정리하므로 기준선 지침·보조 생성 자료의 시스템 메시지와 관련 manifest 해시가 갱신됩니다. **정책·질문·참고 답변·평가용 dev12와 과거 실측 원문은 그대로 보존합니다.** 이전 실행을 재현할 때는 그 실행의 지침 snapshot을 사용하며 새 지침의 해시를 과거 기록에 덮어쓰지 않습니다.

공식 참고 자료는 [프로젝트 생성](https://learn.microsoft.com/azure/foundry/how-to/create-projects), [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry), [Agent Optimizer](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent), [리소스 그룹 삭제](https://learn.microsoft.com/azure/azure-resource-manager/management/delete-resource-group)입니다.
