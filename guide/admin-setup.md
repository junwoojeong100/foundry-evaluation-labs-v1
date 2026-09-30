# 운영자 안내 · 새 NCUS 환경과 안전한 재개

[참가자 경로로 돌아가기](handbook.md#environment) · [인프라 계약](../infra/README.md) · [검증 상태](verification.md)

**기존 실습 계정/리소스를 재사용하지 않습니다.** 개인 식별값은 비공개 계획 파일에만 입력하고 소스 문서에는 넣지 않습니다. 새 환경의 소유 manifest와 원격 상태를 확인한 뒤에만 참가자에게 진행을 안내합니다.

> **현재 관측과 복구 순서**
>
> 초안 검증 후 발생한 폐기 모델 거절, 프로젝트/모델 동시 생성 충돌, 관측 연결 메타데이터 누락을 실제 응답으로 확인하고 복구했습니다. 같은 신규 NCUS RG에서 ARM `Succeeded`와 25개 소유 기록을 확인했습니다. 모델은 응답 생성 전에 gpt-4.1-mini / 2025-04-14 / Standard로 명시 선택했으며 다른 리전이나 기존 자원을 재사용하지 않았습니다. [검증 기록](verification.md)에서 생성·데이터 평면·품질 결과를 구분합니다.

## 승인·소유·준비는 서로 다른 상태 {#scope}

| 확인 | 이번 작업의 범위 |
|---|---|
| 리전·대상 | `northcentralus`의 새 RG와 신규 리소스만 |
| 금액 | 사용자가 **금액 상한 없음을 명시 승인**. 이전 USD50을 차단 조건으로 사용하지 않음 |
| 작업 | 모델/Judge/planner 합계 최대 300회, Optimizer별 1작업·최대 2후보, SFT 1작업·56 train/12 validation·1 epoch, fresh12, 작업당 최대 60분 대기 |
| 데이터·처리 | 승인된 합성 자료의 GlobalStandard/Global/Developer 처리. 실제 고객 자료로 확대 금지 |
| 권한 | 신규 리소스에 필요한 최소 RBAC만. 기존/공유 범위의 권한·정책 변경 금지 |
| 보존 | 새 RG와 근거는 사용자 검토를 위해 보존. 삭제 승인 없음 |

이 승인은 **이번 운영 범위**에만 해당합니다. 패키지를 받은 다른 고객/참가자의 비용·테넌트 접근까지 승인한 것이 아닙니다. 승인 원문·서명/승인 파일은 비공개로 보관하며 HTML/PDF/ZIP에 넣지 않습니다.

인프라 실패 기록을 나중의 성공으로 덮어쓰지 않습니다. 비용 승인 부재로 실제 서비스 오류를 설명하지 않습니다. 다만 특정 새 계획에 유효한 승인 파일이 없으면 도구의 `BLOCKED_AWAITING_APPROVAL`은 정당한 상태입니다. 실제 사용 동의와 그 계획을 결속하는 기계 읽기 기록은 별도입니다.

## A1–A6. 한 번만 준비하고 같은 환경으로 이어가기 {#bootstrap}

### A1. 의도한 계정과 구독 확인

**목적:** CLI·SDK·브라우저가 다른 계정으로 조용히 바뀌지 않게 합니다.

**할 일:** Python 3.11 이상과 Azure CLI를 로컬에 준비합니다. 아래 값은 자리표시자이며 실제 값은 터미널/비공개 파일에서만 사용합니다.

**복사 명령:**

```bash
export AZURE_SUBSCRIPTION_ID="YOUR_SUBSCRIPTION_ID"
export AZURE_TENANT_ID="YOUR_TENANT_ID"
export EXPECTED_AZURE_USER="operator@example.invalid"
az login --tenant "$AZURE_TENANT_ID"
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
az account show --query "{user:user.name,tenant:tenantId,subscription:id}" -o json
```

**완료 신호:** 실제 로그인 사용자·테넌트·구독이 승인 범위와 일치합니다. 브라우저에서도 같은 계정을 확인합니다. bootstrap은 실제 사용자 object ID를 별도 확인합니다.

**오류/복구:** 잘못된 계정·서비스 principal·권한 부족을 다른 캐시 자격 증명으로 우회하지 않습니다. 토큰·키·암호를 문서에 복사하지 않습니다.

**재개:** 로그인 만료 때만 다시 인증합니다. 이번 실제 점검에서는 Azure MCP의 구독 조회가 맞았지만 **Foundry MCP의 데이터 평면 토큰은 다른 테넌트**여서 요청이 거부되었습니다. 이 경로로 변경하지 않았고 올바른 사용자·테넌트를 검증한 CLI/SDK 및 브라우저를 사용했습니다. MCP의 구독 목록만으로 principal·데이터 평면 인증이 같다고 단정하지 않습니다.

**다음:** A2. 이미 비공개 계획이 있다면 새 계획을 만들지 않고 그 경로를 사용합니다.

### A2. 신규 계획을 로컬에 생성

**목적:** 생성할 이름·모델·용량·처리 범위·소유 표식을 원격 변경 전에 고정합니다.

**할 일:** 처음 시작하는 환경에서만 실행합니다. 아래는 표준 라이브러리 경로이며 Azure에 접속하지 않습니다.

**복사 명령:**

```bash
python3 -S -m lab.bootstrap plan --subscription "$AZURE_SUBSCRIPTION_ID" --tenant "$AZURE_TENANT_ID" --expected-user "$EXPECTED_AZURE_USER" --environment lab-training --agent-sku Standard --root .lab --location northcentralus
```

`--environment`는 `lab-training`처럼 **소문자 영문자로 시작**하는 유효한 이름을 사용합니다. 날짜 숫자만으로 시작하는 환경명은 현재 검증에 맞지 않습니다. 환경명과 RG 이름은 다른 필드입니다. 오류를 없애려고 이미 만들어진 RG나 기존 계획을 임의로 이름 변경하지 않습니다.

**완료 신호:** `plan_status: CREATED_LOCAL_ONLY`, `mutations_performed: false`. 기본 `.lab/lab-training/` 아래에 다음이 생깁니다.

현재 새 agent/SFT 기반 권장값은 **gpt-4.1-mini / 2025-04-14 / Standard**입니다. 출력의 실제 모델/버전을 확인합니다. 이전 gpt-4o-mini가 들어 있는 계획은 적용하지 말고 새 계획을 준비합니다. `--agent-sku`는 SKU 선택이지 모델 이름/버전을 바꾸는 우회 옵션이 아닙니다.

| 파일/폴더 | 용도 |
|---|---|
| `config.json`, `template.json` | 정확한 신규 리소스·배포·템플릿 해시 |
| `manifest.json` | 대상 ID와 생성 의도·소유·단계 기록 |
| `approval.example.json` | **승인되지 않은** 형식 예시 |
| `group-authorization.example.json` | RG만 따로 만드는 경우의 미승인 예시 |
| `cost-ledger.json` | SKU·소유 대상·알 수 없는 비용을 구분한 원장 |
| `artifacts/`, `evidence/` | 해당 환경만의 비공개 실행/관측 기록 |
| `.gitignore` | 해당 환경 디렉터리의 기록을 Git에서 제외 |

`.env`는 계획 단계에 생성되지 않습니다. 전체 배포·소유 확인 후에만 생성됩니다. 비공개 디렉터리를 복사해 고객용 ZIP에 넣지 않습니다.

**오류/복구:** 같은 환경 디렉터리가 있으면 덮어쓰기 대신 원래 계획을 찾습니다. 리소스 충돌을 해결하려고 기존 RG를 지우거나 태그를 복사하지 않습니다.

**재개:** 이후 모든 명령은 같은 `config.json`을 사용합니다. 기본 모델·이름·용량·보존 설정을 바꾸려면 원래 상태를 보존한 별도 승인 계획이 필요합니다.

**다음:** A3.

#### 선택: 후속 SFT에 맞는 기반 배포 계획 {#sft-base}

현재 bootstrap의 새 agent 기본 후보는 **gpt-4.1-mini / 2025-04-14 / Standard**이며 SFT도 같은 기반 계열/버전을 사용합니다. 명시적 `--agent-sku Standard`는 이 SKU를 고정하고 기본 요청 capacity는 ARM 단위 20입니다. Judge/planner/embedding은 기존의 승인된 역할 모델을 유지합니다.

아직 계획이 없다면 A2에서 이 새 후보를 확인합니다. **이전 gpt-4o-mini 또는 GlobalStandard-agent 계획이 있고 이번 새 RG가 아직 비어 있다면**, 실패/이전 계획을 수정하지 않고 별도 로컬 환경으로 새 계획을 만듭니다. 아래 RG 값은 원래 비공개 기록의 **같은 새 RG 이름**으로 바꿉니다.

```bash
export NEW_RESOURCE_GROUP="YOUR_EXISTING_EMPTY_NEW_LAB_RESOURCE_GROUP"
python3 -S -m lab.bootstrap plan --subscription "$AZURE_SUBSCRIPTION_ID" --tenant "$AZURE_TENANT_ID" --expected-user "$EXPECTED_AZURE_USER" --environment lab-training-sft --root .lab --resource-group "$NEW_RESOURCE_GROUP" --agent-sku Standard
```

이후 A3의 환경 디렉터리를 실제 새 `lab-training-sft` 경로로 선택하고 새 scope에 맞는 완전한 승인 파일을 준비합니다. A5에서 원래 intent/creation receipt로 읽기 전용 결속을 확인한 뒤 **선택한 새 계획만** 적용합니다. 실패한 gpt-4o-mini 계획이나 이전 GlobalStandard 계획을 자동 전환하거나 함께 apply하지 않습니다. 해당 로컬 디렉터리가 이미 있으면 다른 새 이름을 사용하며 덮어쓰지 않습니다. RG에 이미 자원이 생겼다면 이 빈-RG 절차를 억지로 적용하지 않습니다.

새 Standard 기반 quota의 정확한 이름은 **`OpenAI.Standard.gpt4.1-mini`**, 별도 tuned quota는 **`OpenAI.Standard.gpt4.1-mini-finetune`**입니다. 모델 이름 `gpt-4.1-mini`와 달리 usageName의 `gpt` 뒤에는 하이픈이 없습니다. GlobalStandard quota나 이전 모델 이름을 가공해 추정하지 않습니다. 운영자가 읽은 여유는 기반 5000, 별도 fine-tuned 500이지만 관측 시점의 ARM/quota 단위이며 무료 사용량이나 성공 보장이 아닙니다. 실제 tuned Standard 배포는 성공한 SFT 작업 이후의 별도 단계입니다.

### A3. 읽기 전용 사전 점검

**목적:** 올바른 신원·리전·공급자·권한·모델 버전·쿼터를 확인하되 배포하지 않습니다.

**할 일:** 자신의 실제 디렉터리에 맞게 첫 줄을 설정합니다. 기존 계획이 다른 위치에 있으면 그 경로를 사용합니다.

**SDK-free와 offline은 다릅니다.** `plan`과 도움말/로컬 schema 읽기는 Azure 호출이 없지만, `preflight`와 `status`는 Azure CLI 로그인과 네트워크가 필요한 **읽기 전용 Azure 조회**입니다. `-S`를 붙였다고 모든 bootstrap 명령이 오프라인 또는 비용 없는 작업이 되는 것은 아닙니다.

**복사 명령:**

```bash
export LAB_ENV_DIR="$PWD/.lab/lab-training"
export LAB_BOOTSTRAP_CONFIG="$LAB_ENV_DIR/config.json"
export LAB_COST_APPROVAL_FILE="$LAB_ENV_DIR/approval.json"
python3 -S -m lab.bootstrap preflight --config "$LAB_BOOTSTRAP_CONFIG"
python3 -S -m lab.bootstrap status --config "$LAB_BOOTSTRAP_CONFIG"
```

**완료 신호:** 읽기 전용 보고서에 신원·NCUS·정확한 모델/버전/SKU·쿼터 family·regional capacity가 명시됩니다. 승인 파일을 아직 전달하지 않았다면 최상위 승인 차단 상태와 `readiness_status`를 따로 읽습니다. `READY`나 `OBSERVED`는 추론 검증이 아닙니다.

| 출력 | 정확한 해석 |
|---|---|
| `CREATED_LOCAL_ONLY` | 계획 파일 생성. 기본 승인 예제는 미승인 |
| `BLOCKED_AWAITING_APPROVAL` + 준비 `READY` | 기술적 준비와 **그 계획의 유효한 승인 파일**은 별개 |
| `READY_FOR_APPROVED_APPLY` / `APPROVED` / `PENDING_EXECUTION` | 승인·읽기 전용 준비 확인. 이 출력만으로 apply 또는 실제 서비스 실행 완료를 판단할 수 없음 |
| `OBSERVED` / `NOT_CHECKED_BY_STATUS` | status는 원격 관측이며 전체 readiness를 다시 검사한 것이 아님 |
| `BLOCKED` | 기술/범위 오류. 다른 리전·계정·권한으로 자동 우회하지 않음 |

모델 배포 기본 후보는 [인프라 문서](../infra/README.md)와 계획 파일이 정합니다. 현재 역할별 카탈로그 예시는 다음과 같으며 성공 보장이 아닙니다.

| 역할 | 모델·버전 | 주의 |
|---|---|---|
| agent / 동일 기반 SFT | gpt-4.1-mini / 2025-04-14 / Standard | 명시적 새 후보. catalog `Legacy`, fineTune 지원 표식 관측; 실제 생성/학습 지원은 새로 검증 |
| judge | gpt-5.4-mini / 2026-03-17 | 실제 평가 요청 지원·권한은 별도 |
| planner / optimizer | gpt-5.5 / 2026-04-24 | 역할 공유 가능. 다른 모델로 자동 대체하지 않음 |
| embedding | text-embedding-3-small / 1 | 인덱스 차원과 실제 응답을 이후 확인 |

ARM `capacity`는 모델/SKU별 단위입니다. 모든 값에 “×1,000 TPM”을 적용하지 않습니다. 카탈로그 minimum/step이 `null`이면 임의 숫자로 보충하지 않습니다. 기반 모델의 정확한 `usageName`과 `-finetune` quota를 구별합니다.

**오류/복구:** 현재 신원에 공급자 조회·생성·역할 할당 권한이 없으면 운영자가 승인된 권한 경로를 확인합니다. 도구는 공급자 등록·공유 권한 수정·다른 리전 전환을 자동 수행하지 않습니다.

**실제로 관측한 첫 실패:** 이전 gpt-4o-mini / 2024-07-18은 catalog의 `Deprecating`·fineTune 표식·쿼터와 달리 Azure validate에서 **2026-03-31부터의 폐기**를 이유로 `ServiceModelDeprecated`가 반환되었습니다. 첫 생성 요청의 거절과 하위 자원 0건·ARM 배포 404 원본을 보존합니다. 모델 응답 전에 새 후보로 교체한 환경 복구이며 모델 품질 개선 실험이 아닙니다. 새 후보도 metadata만으로 성공 처리하지 않습니다.
**재개:** 같은 계획으로 read-only preflight/status만 다시 확인합니다. 쿼터 여유는 무료 호출이나 배포 성공이 아닙니다.

**다음:** A4.

### A4. 실제 승인과 계획을 결속 {#approval}

**목적:** 범위가 다른 승인이나 단순 예제 파일로 유료 변경을 시작하지 않게 합니다.

**할 일:** 승인된 운영자가 실제 승인 근거를 사용해 해당 계획의 비공개 승인 파일을 준비합니다. [승인 스키마](../infra/approval.schema.json)와 계획이 만든 예시를 확인합니다. 참가자나 AI가 승인을 대신 만들어 넣지 않습니다.

실제 신원/승인 내용을 노출하지 않고 공개 형식만 확인하려면 다음을 사용합니다.

```bash
python3 -S -m json.tool infra/plan.schema.json
python3 -S -m json.tool infra/approval.schema.json
```

**복사 명령 — 작성된 승인 기록 검증만:**

```bash
python3 -S -m lab.bootstrap preflight --config "$LAB_BOOTSTRAP_CONFIG" --approval "$LAB_COST_APPROVAL_FILE"
```

확인할 내용은 계획/템플릿 해시·모델·범위, 승인자와 기간, 실제 보존 설정, Global 처리, 호출·후보·epoch·작업/대기 제한, 자원 생성과 RBAC의 각각의 승인입니다. 모델 수명주기 조건과 지속 호스팅·미확정 비용도 별도로 확인합니다. 제공자가 폐기 사유로 거부한 모델은 단순한 수용 체크로 다시 허용되지 않습니다.

**범위 요약과 완전한 승인 파일을 구분합니다.** 원래 비공개 범위 요약의 `budget_cap: null`을 bootstrap에 그대로 넘기는 것이 아닙니다. `approval_template(config)` 또는 해당 계획의 예시를 기준으로, 승인된 운영자가 실제 동의를 완전한 schema에 기록합니다.

이번 무상한 승인의 bootstrap 필드는 `budget_policy: NO_MONETARY_CAP_EXPLICITLY_APPROVED`, `budget_amount: null`, `acknowledge_no_monetary_cap: true`와 **비어 있지 않은 비공개 `request_evidence`**입니다. 이와 별개로 실제 승인자/시각/기간·USD 통화·정확한 scope/모델·생성/RBAC/Global 처리·보존·유한한 작업 제한도 모두 검증해야 합니다. 이 필드 설명은 승인 파일 자체도, 다른 사용자의 지출 승인도 아닙니다.

`null`은 승인 누락·0원·무료가 아닙니다. 과거 USD50 제안으로 현재 승인을 차단하거나 편의를 위해 임의의 숫자 승인을 만들지 않습니다. 유한 금액 정책은 별도로 선택·승인된 다른 범위에서 사용할 수 있지만, 이번 작업에 조용히 되살리지 않습니다.

로그 보존의 기술적 최소값과 사용자가 승인한 보존 조건은 별개입니다. 예시의 30일을 승인 사실로 옮기지 않습니다. 다른 실습은 해당 고객의 실제 비용/처리/보존 승인을 사용합니다.

**완료 신호:** 정확한 scope의 승인 검증이 통과하고 별도 준비 상태가 정상입니다. 이것만으로 리소스가 생성되거나 모델이 실행되지는 않습니다.

**오류/복구:** 실제 승인과 schema/코드가 맞지 않으면 승인 내용을 왜곡하지 말고 통합 계약을 수정·검증합니다. 무상한 승인을 유한 금액으로 바꾸거나 승인 파일을 다른 계획에 재사용하지 않습니다.

**재개:** 원본 승인 기록을 보존합니다. 환경 `.env`에 기록된 최초 승인 경로를 몰래 덮어쓰지 말고 현재 사용할 승인은 명시적으로 전달합니다.

**다음:** A5. 가이드 검토 이후에도 새 계획의 유효한 승인·현재 준비·제공자 검증을 확인한 뒤에만 적용합니다.

### A5. 같은 신규 환경을 한 번만 적용

**목적:** 소유가 확인된 신규 RG에만 승인된 리소스를 만들고 부분 실행을 안전하게 이어갑니다.

**할 일:** 다른 운영자/프로세스가 같은 환경을 적용하고 있지 않은지 확인합니다. **이 단계는 Azure 변경과 과금 자원 생성을 수행합니다. 이번 통합은 실패 기록을 보존한 복구 뒤 실제 `APPLIED`를 확인했습니다.**

**이미 RG만 만든 이번 통합은 먼저 결속 확인:** 통합 운영자가 **생성 전 원본 의도와 실제 생성 결과**를 가지고 다음 읽기 전용 결속을 수행할 수 있습니다. 각 경로는 원래 비공개 기록으로 바꾸며 예시 JSON을 새로 만들어 과거 생성 사실을 주장하지 않습니다. 아직 RG도 만들지 않은 일반 신규 계획은 이 결속 단계를 건너뛰고 아래 apply에서 소유 의도를 먼저 기록합니다.

```bash
export RG_INTENT_FILE="YOUR_PRIVATE_PRECREATION_INTENT_JSON"
export RG_CREATED_FILE="YOUR_PRIVATE_CREATION_RECEIPT_JSON"
python3 -S -m lab.bootstrap bind-group --config "$LAB_BOOTSTRAP_CONFIG" --intent "$RG_INTENT_FILE" --created "$RG_CREATED_FILE"
```

이 경로도 실제 새 RG의 scope·원래 태그·생성 근거가 일치해야 합니다. 일반 참가자는 이름만 같은 그룹을 채택하지 않습니다. `prepare-group`는 외부 RG 생성 **전**, `confirm-group`는 그 원래 의도의 읽기 전용 확인입니다. `bind-group`도 태그/권한을 나중에 맞추거나 기존 리소스를 변경하는 동작이 아닙니다.

**복사 명령 — 승인·소유 확인 후 운영자만:**

```bash
python3 -S -m lab.bootstrap apply --config "$LAB_BOOTSTRAP_CONFIG" --approval "$LAB_COST_APPROVAL_FILE"
python3 -S -m lab.bootstrap status --config "$LAB_BOOTSTRAP_CONFIG" --approval "$LAB_COST_APPROVAL_FILE"
```

bootstrap은 의도 ID를 저장한 뒤 대상 소유를 확인하고 RG 범위의 Incremental 배포를 사용합니다. 기존 RG/리소스·다른 환경을 이름만 보고 채택하지 않습니다. 알려지지 않은 대상·모델 변경·권한 범위 변경은 중단 사유입니다.

**완료 신호:** 실제 ARM 배포가 완료되고 manifest/inventory가 일치하며 `.env`가 생성됩니다. 이 bootstrap의 `APPLIED`는 `data_plane_verified: false` / `live_status: NOT_VERIFIED`와 함께 보고됩니다. 인프라 확인은 모델 추론·MCP·교정·trace 수집 성공이 아닙니다.

**오류/복구:** 타임아웃을 리소스 부재로 해석하지 않습니다. 저장된 배포 ID·원장·원격 상태를 확인합니다. 자동 rollback/delete/권한 복구로 공유 환경을 변경하지 않습니다.

**재개:** 같은 config와 유효한 승인으로 `apply`를 이어가며 먼저 `status`를 확인합니다. stale lock은 기록된 PID가 종료되었고 다른 작업이 없는지 확인하기 전 제거하지 않습니다. 자원을 보존하려고 잠금만 임의로 무력화하지 않습니다.

bootstrap apply에는 `--confirm`, `--resume`, `--force`, `--adopt`, `--delete`를 붙이지 않습니다. 별도 배치 명령의 `run --resume`와 구분합니다. 이미 소유가 확인된 RG에서만 `apply --what-if`로 읽기 전용 비교를 할 수 있으며, 결과는 `WHAT_IF_ONLY`입니다. what-if를 위해 RG를 생성하거나 비용 승인·실제 배포 성공으로 해석하지 않습니다.

**다음:** A6.

### A6. 런타임 환경 연결 후 참가자 경로로 복귀

**목적:** 생성된 정확한 신규 배포·검색·관측 endpoint를 사용하고 환경별 근거를 분리합니다.

**할 일:** private `.env`의 배포 이름·endpoint가 실제 manifest와 맞는지 읽습니다. `.env.example`의 자리표시자나 이전 실습 값으로 바꾸지 않습니다. `.env`를 셸로 실행하지 않습니다.

**복사 명령:**

```bash
export LAB_ENV_FILE="$LAB_ENV_DIR/.env"
export LAB_ARTIFACTS_DIR="$LAB_ENV_DIR/artifacts"
python -m lab --config "$LAB_ENV_FILE" preflight
python -m lab validate
```

`LAB_ARTIFACTS_DIR`는 각 Python 프로세스의 **시작 전 환경**에 있어야 합니다. 새 터미널·작업 프로세스에서는 export를 다시 적용합니다. Python 안에서 모듈을 import한 뒤 뒤늦게 경로를 바꾸어 다른 환경의 근거를 섞지 않습니다.

**완료 신호:** `preflight: PASS`, 데이터 100건 유지, 올바른 실제 환경. `.env`에는 `EMBEDDING_DEPLOYMENT`, `LAB_ARTIFACTS_DIR`, 같은 계획을 가리키는 `LAB_BOOTSTRAP_CONFIG`와 `BOOTSTRAP_CONFIG`, 최초 `LAB_COST_APPROVAL_FILE`, 신규 관측 리소스 ID도 기록됩니다. 키/암호를 요구하지 않습니다.

bootstrap 이후 main CLI의 `--confirm` 호출과 SFT 배포는 `BOOTSTRAP_CONFIG`를 사용해 완료된 bootstrap 소유 근거와 실제 새 RG/계정을 확인합니다. 이 소유 확인은 현재 작업 승인을 부여하지 않으므로 별도 private approval·호출/작업 제한을 함께 검증합니다. 예전 환경 값이나 위조한 hash/receipt로 통과시키지 않습니다.

**오류/복구:** 환경 밖 경로를 `.relative_to(ROOT)`로 강제하는 코드가 있다면 `artifact_reference` 계약을 사용하도록 수정해야 합니다. 파일을 저장소 안으로 억지 복사해 문제를 숨기지 않습니다.

**재개:** 터미널을 다시 열면 같은 `.venv`와 환경 변수만 복원합니다. 재설치·재배포·새 RG 생성부터 반복하지 않습니다.

**다음:** [본문 04. 평가 계약](handbook.md#data). 이후 모델 연결 smoke 1회와 별도의 baseline Agent 3건을 순서대로 수행하며 운영자가 모든 참가자의 결과를 미리 만들어 놓지 않습니다. 연결 확인을 에이전트 품질 평가로 세지 않습니다.

## 어떤 주체에게 어떤 권한인가 {#rbac}

이 표는 **신규 리소스에만 적용할 계획**입니다. 실제 역할 정의와 API 작업을 사전 점검해야 하며 표를 읽은 것이 역할 할당의 증거가 아닙니다.

| 주체 | 작업 | 최소 범위를 검토할 역할 |
|---|---|---|
| 운영자/실습 사용자 | Foundry 계정 데이터 작업·모델 호출 | 신규 계정의 작업별 Azure AI Developer / Cognitive Services OpenAI User |
| 운영자/실습 사용자 | 현재 Agent Service 프로젝트 작업 | 신규 프로젝트의 Foundry User. Azure AI Developer 이름만 보고 Agent CRUD까지 된다고 가정하지 않음 |
| 운영자/실습 사용자 | Search 스키마·콘텐츠 준비 | 신규 Search의 Search Service Contributor + Search Index Data Contributor |
| 프로젝트 MI | IQ의 검색 읽기 | 신규 Search의 Search Index Data Reader |
| 프로젝트 MI | 모델/관측 접근 | 신규 계정의 해당 모델 역할과 새 관측 자원의 발행 권한 |
| Search MI | LLM 검색 계획·vectorizer 모델 접근 | 신규 Foundry 계정의 Cognitive Services User를 현재 공식 문서와 대조 |
| 관측 사용자 | trace 읽기 | 새 Application Insights/Log Analytics의 작업별 읽기 역할 |

역할 할당 권한 자체는 별도의 관리 권한입니다. 참가자에게 구독 Owner/Contributor를 새로 부여하는 방식으로 단순화하지 않습니다. Search MI와 프로젝트 MI를 서로 바꿔 지정하지 않습니다.

Cognitive Services User에는 key-list 작업이 포함될 수 있습니다. 이는 키 인증을 사용하라는 뜻이 아닙니다. bootstrap의 Entra 인증·local-auth 비활성화 경계를 유지하며 키를 읽거나 배포하지 않습니다.

참고: [Foundry RBAC](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) · [Search RBAC](https://learn.microsoft.com/en-us/azure/search/search-security-rbac) · [Search MI의 모델 기반 Knowledge base 접근](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-create-knowledge-base#configure-access)

### 공식 구현 계약 참고 {#references}

다음은 인프라 담당자가 확인해 전달한 공식 계약입니다. **계획의 근거**이며 실제 역할 할당·배포·서비스 실행을 완료했다는 증거가 아닙니다.

| 확인할 계약 | 공식 참조 |
|---|---|
| Foundry 계정/프로젝트 시스템 ID·프로젝트 속성 | [accounts/projects · 2025-06-01](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-06-01/accounts/projects) |
| 고정 모델 버전·NoAutoUpgrade·SKU·태그 | [accounts/deployments · 2025-06-01](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-06-01/accounts/deployments) |
| Search MI·Basic·disableLocalAuth | [searchServices · 2025-05-01](https://learn.microsoft.com/en-us/azure/templates/microsoft.search/2025-05-01/searchservices) |
| 새 리소스에만 extension-role scope 지정 | [ARM extension resource scope](https://learn.microsoft.com/en-us/azure/azure-resource-manager/templates/scope-extension-resources) |
| 프로젝트 연결의 AAD 인증 | [accounts/projects/connections · 2025-06-01](https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/2025-06-01/accounts/projects/connections) |
| Log Analytics 요금제·보존 | [workspaces · 2023-09-01](https://learn.microsoft.com/en-us/azure/templates/microsoft.operationalinsights/2023-09-01/workspaces) |
| Workspace 기반 Application Insights | [components · 2020-02-02](https://learn.microsoft.com/en-us/azure/templates/microsoft.insights/2020-02-02/components) |

Search에서 `disableLocalAuth: true`를 사용할 때 호환되지 않는 `authOptions`를 함께 넣지 않습니다. 이것은 키를 읽거나 기존 Search 설정을 고치라는 안내가 아닙니다. 새 template과 해당 API 계약을 검증하는 항목입니다.

## 비용·보존·새 기능 접근 {#cost}

| 비용 종류 | 읽는 방법 |
|---|---|
| Search Basic | NCUS의 읽기 전용 가격 참고는 0.101 USD/시간, 24시간 약 2.424 USD, 730시간 약 73.73 USD. 현재 청구액이나 총 실습 비용 아님 |
| 모델/Judge/planner/embedding | 각각의 실제 요청/토큰. quota 여유를 무료 할당으로 해석하지 않음 |
| Optimizer | 후보·에이전트·도구·평가 사용량. 포털이 숨기는 내부 호출 수까지 단순히 “1 API”라고 축소하지 않음 |
| SFT | 학습 + 기반/학습 모델 추론 + 학습 모델의 지속 호스팅을 분리 |
| 로그/보존 | 수집·보존 비용. ingestion cap은 엄격한 금전 차단기가 아님 |
| 미집계/알 수 없음 | `UNKNOWN_NOT_ZERO` 또는 관측 대기. 0원으로 채우지 않음 |

비용 상한이 없어도 불필요한 반복·중복 요청을 하지 않습니다. 정해 둔 호출/후보/작업/대기 한도를 넘는 확장은 별도 판단 대상입니다. 현재는 **보존**이 원칙이고 삭제를 비용 통제의 자동 수단으로 사용하지 않습니다.

Prompt Optimizer, prompt-agent Agent Optimizer, SFT, Frontier, trace 수집은 각각 따로 확인합니다. Frontier는 현재 직접 일치하는 공식 API/지원 경로가 `NOT_VERIFIED`이며 존재하지 않는다고 단정하지 않습니다. Agent Optimizer는 prompt-agent 포털 wizard가 공식 경로이며 hosted 구조로 바꿀 필요가 없습니다.

## 이 단계의 인수 체크리스트 {#handoff}

- [ ] 실제 신원·구독·테넌트·NCUS와 신규 자원 scope가 확인되었다.
- [ ] 원본 의도·소유 manifest로 같은 RG/환경을 재개할 수 있다.
- [ ] 승인 예제와 실제 승인 기록이 구분되고 비공개로 보관된다.
- [ ] 금액 무상한 승인과 유한한 작업 범위를 함께 반영했다.
- [ ] 모델 수명주기·정확한 usageName·capacity 단위·역할 전파의 한계를 설명했다.
- [ ] `.env`·실행 자료를 소스/배포 ZIP에 넣지 않는다.
- [ ] 전체 배포/실제 추론/품질/관측의 상태를 각각 기록했다.
- [ ] 이번 RG를 보존하며 삭제 명령은 실행하지 않는다.
