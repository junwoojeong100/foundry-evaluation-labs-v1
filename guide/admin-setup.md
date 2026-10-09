# 환경 설정 참고 · 권한·승인·정리 {#operator-guide}

[처음부터 진행하는 10단계](handbook.md#setup) · [실습 체크리스트](facilitator.md#prepare) · [문제 해결](troubleshooting.md)

이 문서는 **본인이 수행하는 02 환경 생성, 03 Agent 준비, 10 정리**의 설정 참고 자료입니다. [실습 가이드](handbook.md#setup)를 순서대로 진행하면서 필요한 절만 엽니다. 실제 값과 완료 상태는 자신의 `.lab/lab-ko/notes.md`에 기록합니다.

**실행 명령 바로가기:** [Codespaces 준비](handbook.md#setup-codespaces) · [CLI 로그인](handbook.md#setup-login) · [빠른 환경 생성](handbook.md#resources-quickstart) · [정책·Agent 준비](handbook.md#agent-knowledge) · [평가 ID 조회](handbook.md#baseline-identifiers) · [재평가](handbook.md#decision-run) · [그룹 삭제·확인](handbook.md#cleanup-delete). 모든 명령은 선택한 실습 폴더의 터미널에서 실행하며, 이미 완료한 작업은 반복하지 않습니다.
{: .execution-guide}

명령을 바꾸지 않고 안쪽 동작을 읽으려면 [02 생성 코드·포털](handbook.md#resources-code-portal), [03 검색 코드·포털](handbook.md#knowledge-code-portal), [Agent 구성](handbook.md#agent-code-portal), [09 제출·조회](handbook.md#decision-code-portal), [10 정리 범위](handbook.md#cleanup-code-portal)를 엽니다. 함수 원문은 읽기용이며 별도 실행이나 포털 중복 생성 지시가 아닙니다.

## 자신의 전용 실습 환경을 준비합니다 {#start}

| 상황 | 진행 방법 |
|---|---|
| 처음 시작합니다. | [01 계정·Codespaces 준비](handbook.md#setup) 후 [02의 `bootstrap setup`](handbook.md#resources-quickstart)으로 생성합니다. 계획·검사·승인·생성을 한 명령이 안내합니다. |
| 본인의 같은 실습을 재개합니다. | 원래 config·manifest·receipt와 실제 상태를 [기록표](#handoff)로 대조합니다. 완료한 생성·제출을 반복하지 않습니다. |
| 다른 업무의 공유 프로젝트만 있습니다. | 이 실습은 기존 그룹을 인수하지 않습니다. 본인이 전용 환경을 만들 수 있는 구독·권한·비용 범위를 확보한 뒤 진행합니다. |

CLI·SDK·포털의 계정·테넌트·구독을 각각 확인하고 같은 본인 신원으로 진행합니다. 다른 사람의 토큰·로그인 세션·설정·소유권 기록을 사용하지 않습니다. 생성부터 ID 조회·v2 생성·재평가·정리까지 본인이 실행합니다.

**모든 실습 참여자는 자신의 전용 환경과 Agent를 사용합니다.** 여러 사람이 같은 Agent의 v2를 만들거나 같은 유료 작업을 제출하는 경로는 사용하지 않습니다. 각 PC에서 같은 예시 환경 이름을 써도 생성되는 Microsoft Azure 자원 이름에는 고유 suffix가 붙습니다.

권한·비용 승인은 생략할 수 없는 시작 조건입니다. 부족하면 조직 절차에 따라 본인에게 허용된 범위를 확보합니다. 이것은 이후 실습을 다른 사람에게 맡기는 별도 경로가 아닙니다.

기본 Agent 이름은 한국어 **`lab-ko-iq`**, 영어 **`lab-en-iq`**입니다. 환경 이름을 바꾼 경우 CLI가 출력한 실제 이름을 사용하고 기록표에 적습니다.

### 언어·기록 설정은 프로그램이 읽습니다 {#runtime-settings}

기본 실습에는 환경 변수 입력이 없습니다. `bootstrap setup --environment lab-ko`는 한국어, `lab-en`은 영어를 계획에 저장하며 `lab-ko-02`·`lab-en-02`도 지원합니다. 생성된 `.env`의 `LAB_LANGUAGE`·`LAB_ARTIFACTS_DIR`를 이후 명령의 `--config`가 읽습니다. 상대 기록 경로는 설정 파일이 있는 폴더 기준입니다.

이전 `.env`에 언어 항목이 없으면 `LAB_PREFIX`의 `lab-ko`·`lab-en` 규칙으로 판별하며 파일·계획 해시를 다시 쓰지 않습니다. 그 규칙에 해당하지 않는 기존 사용자 지정 환경과 설정 파일을 사용하지 않는 별도 도구만 기존 환경 변수·기본값을 유지합니다. 기본 실습에 해당 변수 설정을 추가할 필요는 없습니다.

**기존 기록은 자동으로 이동하거나 합치지 않습니다.** 과거에 공통 `artifacts/` 또는 별도 경로를 사용했다면 원래 설정과 `workspace.json`의 프로젝트·prefix·언어를 먼저 대조합니다. 경로가 다른 상태에서 유료 작업을 새로 실행하지 않으며, 원본 `.env`·manifest를 편집해 소유권 검사를 우회하지 않습니다.

<figure class="portal-shot" id="portal-resource-group">
<img src="../web/assets/portal/01-project-overview.png" alt="Microsoft Foundry 프로젝트 홈에서 프로젝트 선택과 endpoint를 확인하는 화면입니다." width="1440" height="1000" loading="lazy">
<figcaption><strong>실습 프로젝트를 확인합니다.</strong> 프로젝트 이름과 endpoint를 자신의 생성 기록과 대조합니다. 리소스 그룹은 Microsoft Azure Portal의 Resource groups에서 같은 구독과 그룹 이름으로 확인합니다. <a href="../web/assets/portal/01-project-overview.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

## 모델 역할과 실제 배포를 확인합니다 {#prepare}

| 역할 | 설정 키 | 기본 모델·버전 |
|---|---|---|
| Agent | `MODEL_DEPLOYMENT` | **`gpt-6-sol` / `2026-09-22`**, GlobalStandard 100입니다. |
| 관리형 평가 Judge | `JUDGE_DEPLOYMENT` | **`gpt-6-luna` / `2026-09-22`**, GlobalStandard 100입니다. |
| Optimizer·검색 planner | `OPTIMIZER_DEPLOYMENT`·`IQ_PLANNER_DEPLOYMENT` | **`gpt-5.5` / `2026-04-24`**, 같은 GlobalStandard 100 배포를 사용합니다. |
| 정책 embedding | `EMBEDDING_DEPLOYMENT` | **`text-embedding-3-small` / `1`**, GlobalStandard 10입니다. |

숫자는 ARM 요청 용량 단위이며 모든 모델에서 같은 TPM을 뜻하지 않습니다. 이것은 사용 가능한지 확인해야 할 기본 계획이지 모든 구독의 배포 보장이 아닙니다. Microsoft Foundry의 **Models + endpoints/Build → Models**에서 배포 이름·모델·버전·상태를 대조합니다. `.env`에는 모델 제품명이 아니라 실제 배포 이름이 들어갑니다.

**관측 리소스의 추가 항목을 구분합니다.** Application Insights는 [기본 Failure Anomalies 경고와 Smart Detection Action group](https://learn.microsoft.com/azure/azure-monitor/alerts/proactive-failure-diagnostics#alert-rule-creation)을 자동으로 추가할 수 있습니다. bootstrap은 경고가 자신의 Application Insights만 대상으로 하는지, 연결된 Action group이 기본 역할 수신자만 사용하는지 읽기 전용으로 확인합니다. 이름만 같은 항목을 인수하지 않으며, 다른 그룹의 공유 Action group도 변경·삭제하지 않습니다. 생성 중 연결이 아직 확인되지 않으면 같은 `bootstrap status`로 다시 확인하고 manifest를 편집하거나 경고를 삭제하여 우회하지 않습니다.

### TPM을 설정한 뒤 호출을 시작합니다 {#throughput}

[02의 최소 권장값](handbook.md#resources-tpm)은 Agent·Judge·Optimizer/planner 배포별 **100,000 TPM**, embedding **10,000 TPM**입니다. 한 환경에서 작업을 순차 실행하는 기준이며 모델·SKU·지역별 할당량은 별개입니다. 여러 전용 환경을 함께 준비한다면 모델별 총 할당량을 합산합니다. 같은 환경에서 Optimizer와 planner가 공유하는 배포는 한 번만 계산합니다.

1. **새 전용 환경:** 최신 코드의 `bootstrap plan`에서 생성 배포 용량 100·embedding 10을 확인하고 그 정확한 계획으로 승인·생성을 진행합니다. 과거 계획은 자동 변경되지 않습니다. 아직 생성하지 않은 낮은 용량의 계획이 있다면 직접 편집하지 말고 새 환경 이름으로 계획·승인을 준비합니다.
2. **실제 배포 확인:** Microsoft Foundry **Build → Models → Deployments → 배포 이름 → Details**에서 **Tokens per Minute Rate Limit**을 읽습니다. 천 토큰 단위의 용량과 최종 TPM 표시를 구분합니다. **이 실습의 bootstrap 환경은 포털의 Edit으로만 용량을 바꾸면 계획과 불일치합니다.** 부족하면 계획·실제 한도·승인 범위를 확인하고, 필요한 경우 충분한 용량으로 새로 승인한 전용 환경을 준비합니다. 해시·승인서 편집으로 우회하지 않습니다.
3. **설정 확인:** 해당 환경의 `.env`와 언어별 artifacts 경로로 다음 읽기 전용 검사를 실행합니다. `*_tpm`의 `observed`·`expected`와 `reason`을 확인합니다.

```sh
python -m lab --config .lab/lab-ko/.env preflight
```

전체 `status: PASS`와 다섯 TPM 항목의 `PASS` 뒤에만 03의 smoke·검색 및 이후 평가·Optimizer로 진행합니다. 검사기는 실제 배포의 `rateLimits` 중 `key: token`을 읽습니다. CLI가 이름표를 생략한 경우 같은 배포의 원시 ARM 메타데이터를 읽으며, 요청 수나 `sku.capacity`를 TPM으로 추정하지 않습니다. 확인 불가도 `BLOCKED`입니다.

TPM은 청구된 평균 토큰과 다르게 추정되며 **RPM과 버스트 제한**도 적용됩니다. 입력·최대 출력 길이, 공유 사용자, 평가·최적화 동시 실행이 늘면 추가 여유를 산정합니다. 이 최소 권장값은 429 없는 실행을 보장하지 않습니다. [공식 제한 설명](https://learn.microsoft.com/azure/foundry/openai/how-to/quota#understanding-rate-limits).

[03의 실제 응답 확인](handbook.md#agent)으로 Agent와 `knowledge_base_retrieve` 호출을 확인합니다. Optimizer는 별도 [지원 모델 목록](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)을 따릅니다. Agent나 Judge로 동작한다고 최적화 생성 모델로 지원된다고 가정하지 않습니다.

<figure class="portal-shot" id="portal-models">
<img src="../web/assets/portal/02-model-deployments.png" alt="Microsoft Foundry 모델 배포 목록의 배포 이름·모델·버전·상태를 확인하는 화면입니다." width="1270" height="750" loading="lazy">
<figcaption><strong>모델·버전·상태를 확인합니다.</strong> 각 배포를 역할 표의 Agent·Judge·Optimizer·embedding과 대조합니다. 배포 이름은 <code>.env</code>와 같아야 하며, 준비된 배포의 실제 호출도 확인합니다. <a href="../web/assets/portal/02-model-deployments.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

## Agent를 실제로 준비합니다 {#bootstrap}

[01의 Codespaces 경로](handbook.md#setup-codespaces)는 **Python 3.11–3.14 지원 범위의 3.12·Git·Microsoft Azure CLI**와 가상환경을 준비합니다. 내 PC를 선택한 경우에만 [운영체제별 설치](handbook.md#setup-local-install)와 [새 터미널 버전 확인](handbook.md#setup-verify)을 수행합니다. 로그인 후 [빠른 생성](handbook.md#resources-quickstart)을 실행하면 언어·기록 위치도 자동으로 정해집니다. `.env.example`의 가짜 식별자를 실환경으로 사용하지 않습니다.

한국어 기준선은 `prompts/baseline.txt`, 영어는 `prompts/en/baseline.txt`입니다. 지침을 약화하여 개선 폭을 만들지 않습니다. [정책 업로드](handbook.md#agent-search-prepare)와 [검색 확인](handbook.md#agent-search-probe)이 완료된 뒤 다음 명령으로 정책 도구를 연결한 v1을 만듭니다.

```sh
python -m lab --config .lab/lab-ko/.env native-agent --version 1 --confirm
```

`native-agent`는 `ensure_fixed_release`를 사용하여 **1·2만 허용**하고, 소유 workspace를 원격 metadata와 대조합니다. 같은 구성은 재사용하며 다른 v2를 덮어쓰거나 v3를 만들지 않습니다. 모델 배포 snapshot도 보관하고 변경 시 비교를 차단합니다. `agents/native-v1.json`, `agents/native-v2.json`, `agents/native-model.json`은 해당 환경의 artifacts 폴더에 기록됩니다.

`native_response_format()`은 공통 스키마를 엄격한 생성 스키마의 지원 범위로 변환합니다. 인용 중복과 `needs_human`·route 일관성은 생성 후에도 확인합니다. 유효한 JSON만으로 정책 정확성이 보장되지는 않습니다.

<a id="sdk-prerequisites"></a>

**v2 생성은 평가 완료가 아닙니다.** [08에서 검토한 전체 지침](handbook.md#optimize)으로 v2를 한 번 만들고 [09의 같은 관리형 평가](handbook.md#decision)를 수행한 뒤 채택 여부를 판단합니다. 정식 v1/v2만 사용하며 별도 `draft-…` 실험은 이 실습에 포함하지 않습니다. 생성한 v2는 운영에 게시하지 않습니다.

```sh
python -m lab --config .lab/lab-ko/.env native-agent --version 2 --prompt .lab/lab-ko/candidate.txt --confirm
```

이 실습에서는 포털 Promote를 사용하지 않고 09의 CLI로 v2를 생성합니다. 포털에서 먼저 승격하면 CLI의 로컬·원격 소유권 확인과 맞지 않을 수 있습니다. v1·v2는 Agent 전체 구성 버전이며 같은 Agent·모델·도구·출력 설정에서 지침만 달라야 합니다.

평가 ID는 [06의 전체 조회 명령](handbook.md#baseline-identifiers)으로 찾습니다. `.env` 경로와 정확한 평가 이름을 포함한 명령을 사용합니다. 재평가 helper는 기준선 data source를 복사하고 **원격** 계약을 검증합니다. 오래된 로컬 `JUDGE_DEPLOYMENT`로 원격 정의를 바꾸지 않습니다.

## 비교 조건을 고정합니다 {#scope}

| 항목 | 고정 조건 |
|---|---|
| 데이터 | 선택한 언어의 같은 dev12 바이트·등록·버전·질문·참고 답변입니다. |
| Relevance | 관리형 `builtin.relevance`, 1–5점, 임계값 **4** |
| TaskAdherence | 관리형 `builtin.task_adherence`, 이진 0/1, 통과 **1** |
| Judge | 두 평가기 정의에 같은 명시적 Luna 배포 |
| Agent | 같은 Sol 모델·버전, 도구, 추론, 엄격한 출력 스키마 |
| 변경 대상 | 지침만 변경, 정식 버전은 v1/v2 |
| Optimizer | Instruction만 선택, 모델·도구 설명 변경 끄기, 후보 수 제한 |
| 실습 기록 | 같은 조건의 v1·후보와 12건 전체 결과를 비공개 실행 폴더에 보관하며 재사용 가이드와 분리 |

카탈로그 평가기 버전은 비공개 서비스 루브릭이 완전히 고정됐다는 증거가 아닙니다. 실제 정의·설정과 이 한계를 남깁니다. 재사용 dev12의 개선은 향후 점수·독립적 일반화·운영 승인을 보장하지 않습니다.

**필수 비교는 [09의 Microsoft Foundry Compare runs](handbook.md#decision-compare)에서 수행합니다.** `scripts/compare_foundry_eval.py`는 선택 사항인 독립 비교 도구이며 이 경로에서 추가 실행하지 않습니다. 별도로 사용할 때는 이 도구의 `--language ko`/`--language en`으로 보고서 언어와 기본 dev12를 선택하고, 직접 지정한 데이터셋과 언어를 일치시킵니다.

### 평가 응답 매핑을 점검합니다 {#evaluation-mapping}

[05에서 두 평가기·Judge를 선택](handbook.md#prepare)하고 자동 매핑을 유지합니다. 아래 표는 누락·불일치가 있을 때의 점검 기준입니다. 정상적인 생성 흐름에서 SDK 내부 필드를 추측해 직접 입력할 필요는 없습니다.

| 확인할 설정 | 유지할 값 |
|---|---|
| Agent 사용자 입력 | `{{item.query}}`만 사용하고 지침 override는 비웁니다. |
| Relevance 응답 | `response={{sample.output_text}}` |
| TaskAdherence 응답 | `response={{sample.output_items}}` |
| Judge·임계값 | 실제 `JUDGE_DEPLOYMENT`, Relevance 4·TaskAdherence 이진 통과 1 |

필수 항목이 **Unassigned**이면 대상이 Dataset이 아닌 **Agent**인지, query 열과 실제 Agent 응답의 연결이 맞는지 대조합니다. 제출 전에는 생성 화면을 확인하고, 제출 후에는 저장된 원격 정의를 확인합니다. 참고 답변을 response에 넣거나 이전 UI의 매핑을 복사하지 않습니다. [공식 포털 평가 안내](https://learn.microsoft.com/azure/foundry/how-to/evaluate-generative-ai-app)와 [응답 매핑 설명](https://learn.microsoft.com/azure/foundry/concepts/evaluation-evaluators/agent-evaluators#using-agent-evaluators)을 참고합니다. 해결 전에는 제출하지 않습니다. 09의 helper도 원격 계약을 검사합니다.

## 실제 승인에 맞춰 승인서를 작성합니다 {#approval}

**빠른 `bootstrap setup`은 같은 승인 파일을 입력 안내로 만듭니다.** 이미 생성했다면 아래 표는 검토용이며 파일을 다시 만들거나 수정할 필요가 없습니다. 개별 명령 경로를 선택했거나 다른 실제 승인 한도가 필요할 때만 직접 작성합니다.

`.lab/lab-ko/approval.example.json`을 편집기에서 열어 **같은 폴더의 approval.json으로 따로 저장**합니다. 본인에게 지출·변경을 결정할 권한이 있으면 한도를 직접 정하고, 조직 구독은 승인 절차를 따릅니다. 실제 승인 근거를 비공개로 보관합니다. 다음 표나 JSON 파일 자체가 독립적인 승인·서명 증명은 아닙니다. JSON 문자열에는 큰따옴표를 사용하고 숫자·true·false·null에는 따옴표를 붙이지 않습니다.

| 필드 | 작성 방법 |
|---|---|
| `schema_version`, `scope_sha256`, `models`, `retention_days` | 생성된 값을 그대로 유지합니다. `models` 배열이나 계획을 편집하면 기존 승인은 유효하지 않습니다. |
| `approved` | 실제 승인 후에만 `true`로 변경합니다. |
| `approved_by` | `config.json`의 `expected_user`와 같은 본인 로그인 이름입니다. 실행 신원 연결용이며 조직 승인자의 전자서명이 아닙니다. |
| `approved_at`, `expires_at` | 실제 승인 시작·만료 시각입니다. `2026-10-03T09:00:00+09:00` 형식의 시간대 포함 ISO 8601을 사용합니다. 예시 날짜를 그대로 복사하지 않습니다. 현재 시각이 두 시각 사이여야 합니다. |
| `currency`, `budget_amount`, `budget_policy` | 승인 통화의 세 글자 코드와 양수 예산입니다. 예산 정책은 `BOUNDED`로 유지하고 실제 허용된 금액을 적습니다. |
| `acknowledge_no_monetary_cap` | `false`로 유지합니다. 이 실습에서 무제한 지출을 기본으로 설정하지 않습니다. |
| `max_hosting_hours` | 승인된 양의 정수 시간입니다. 예를 들어 8이면 승인 시작부터 만료까지도 8시간 이하여야 합니다. |
| `max_wait_seconds` | 양의 정수 대기 한도입니다. 예를 들어 3600입니다. 대기 종료는 원격 작업 취소가 아닙니다. |
| `max_calls`, `max_candidates` | 승인된 호출·후보 한도입니다. 08의 요청 후보 수는 2입니다. 내부 Agent·Judge·검색 호출을 고려합니다. 이 필드가 포털의 모든 호출·비용을 자동 제한하지는 않습니다. |
| `allow_global_inference` | GlobalStandard의 처리 경계를 승인한 경우 `true`입니다. NCUS 내부 처리만 보장하지 않습니다. |
| `allow_resource_creation`, `allow_rbac_assignments` | 해당 계획의 리소스 생성·리소스 범위 역할 할당을 승인한 경우 각각 `true`입니다. |
| `acknowledge_continuous_hosting`, `acknowledge_unknown_cost` | 지속 과금 가능성과 확정되지 않은 총비용을 확인한 경우 각각 `true`입니다. |
| `allow_training`, `allow_global_training` | 이 경로는 `false`입니다. |
| `max_epochs`, `max_training_jobs` | 이 경로는 `0`입니다. |
| `accept_deprecated_models` | 기본 `false`입니다. 서비스가 지원 종료를 알리면 별도 검토 없이 바꾸지 않습니다. |

[02의 `bootstrap preflight --config ... --approval ...`](handbook.md#resources-approval)로 파일을 검증합니다. 오류가 있으면 `approval_reason`을 확인합니다. 한 파일의 승인은 정확한 계획 해시·모델·보존 범위에만 적용되며 다른 실습·재시도·삭제 승인을 포함하지 않습니다.

**강제 범위를 구분합니다.** bootstrap은 승인 유효기간·생성 범위·대기 시간을 검사하지만 JSON 예산과 호출 한도가 Microsoft Azure Portal·Optimizer 전체의 지출을 자동 차단하지 않습니다. 비용 알림도 차단 장치가 아닙니다. 본인이 실제 사용량을 확인하고 승인된 범위에서 작업을 취소하거나 자원을 정리합니다.

## 권한과 공급자 등록을 확인합니다 {#rbac}

[현재 Microsoft Foundry RBAC 안내](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry)를 기준으로 권한을 확인합니다. **Foundry User/Owner/Account Owner/Project Manager**는 이전 **Azure AI User/Owner/Account Owner/Project Manager** 이름으로 보일 수 있습니다.

포털의 **Access control (IAM) → Check access**에서 활성 할당과 Scope를 확인합니다. 이전 UI의 View my access와 위치가 다를 수 있습니다. [01의 실제 구독·권한 그림](handbook.md#portal-check-access)은 기존 권한을 읽는 예시이며 역할 추가 안내가 아닙니다.

| 작업·연결 | 확인할 권한과 범위 |
|---|---|
| 본인의 새 환경 생성 | bootstrap은 구독 범위의 그룹·배포·자원 생성과 `Microsoft.Authorization/roleAssignments/write` 유효 권한을 확인합니다. Contributor만으로는 역할 할당이 안 됩니다. 구독 quota 조회 권한도 필요합니다. |
| 본인의 Agent·평가 실행 | 자신의 프로젝트에 Foundry User 등 필요한 데이터 평면 권한이 있어야 합니다. Microsoft Azure의 Contributor/Owner만으로 이 권한이 생기지는 않습니다. |
| 본인의 정책 준비 | 자신의 Search에 Search Service Contributor와 Search Index Data Contributor 등 스키마·업로드 권한이 필요합니다. |
| 프로젝트 관리 ID | 해당 Search의 Search Index Data Reader, 모델 호출과 해당 관측 리소스 전송 권한입니다. |
| Search 관리 ID | 해당 Microsoft Foundry 리소스의 모델 호출 권한입니다. |
| 본인의 로그 확인 | 자신의 Application Insights·Log Analytics를 읽는 권한입니다. 구독 전체 로그 접근을 기본으로 요구하지 않습니다. |

**새 자원의 실행 권한은 승인된 bootstrap이 해당 자원 범위에 할당합니다.** 구독 전체 역할을 새로 부여하지 않습니다. 생성 후에는 본인과 서비스의 관리 ID가 서로 다른 신원임을 구분하고 03의 실제 도구 호출로 전파·데이터 평면 접근을 확인합니다.

공급자는 Microsoft Azure 서비스 종류를 구독에서 사용할 수 있게 하는 등록 항목입니다. [공식 공급자 등록 안내](https://learn.microsoft.com/azure/azure-resource-manager/management/resource-providers-and-types#azure-portal)에 따라 다음을 확인합니다.

1. Microsoft Azure Portal → **Subscriptions → 사용할 구독 → Resource providers**를 엽니다.
2. `Microsoft.CognitiveServices`, `Microsoft.Search`, `Microsoft.OperationalInsights`, `Microsoft.Insights`를 각각 검색하여 **Registered**인지 확인합니다.
3. 미등록 항목은 본인에게 해당 `/register/action` 권한과 등록 승인이 있는 경우에만 선택하여 **Register**를 누릅니다. 필요한 네 항목 외 공급자를 일괄 등록하지 않습니다.
4. 등록 완료·전파 후 같은 preflight를 다시 실행합니다. 등록 권한이 없으면 승인된 실행 범위를 확보한 뒤 재개합니다. bootstrap은 공급자를 자동 등록하거나 권한을 확대하지 않습니다.

등록·역할 전파를 기다린 뒤 같은 preflight를 다시 실행합니다. `403`이 계속되면 계정·역할 scope·네트워크를 대조합니다. 편의를 위해 구독 Owner를 새로 부여하거나 네트워크 제한·조직 정책을 해제하거나 토큰을 옮기지 않습니다.

## 비용과 운영 경계를 정합니다 {#cost}

평가는 Agent·Judge를 호출하고 최적화에는 추가 내부 호출이 있습니다. Search·모니터링은 실습 화면을 닫아도 비용이 남을 수 있습니다. 관측 토큰·예상 비용·실제 청구를 구분하고 미확인 비용을 0원으로 표시하지 않습니다.

| 비용 구성 | 청구 방식 | 해야 할 일 |
|---|---|---|
| Microsoft Azure AI Search(Basic, 복제 1개) | 존재하는 동안 유휴 상태에서도 시간 단위로 청구됩니다. 이 가이드를 준비할 때 North Central US 기준 시간당 약 US$0.10이었습니다. 현재 [AI Search 가격](https://azure.microsoft.com/pricing/details/search/)을 확인합니다. | 가장 큰 지속 비용입니다. 끝나는 대로 10단계처럼 그룹을 삭제합니다. |
| 모델 배포(Agent·Judge·Optimizer/planner·embedding) | GlobalStandard는 사용한 토큰 기준으로 청구되며, 유휴 배포는 토큰 비용을 추가하지 않습니다. | 평가·Optimizer·검색 호출이 토큰을 사용합니다. "다시 시도"하려고 같은 작업을 재제출하지 않습니다. |
| Application Insights·Log Analytics | 수집·보존한 데이터량 기준입니다. 빠른 경로는 로그를 30일 보관합니다. | 이 실습에서는 보통 작지만 그룹 삭제 시 함께 삭제됩니다. |
| GitHub Codespaces | GitHub의 별도 청구입니다. 실행 중에는 컴퓨팅, 존재하는 동안에는 저장소 비용이 듭니다. | 10단계에 따라 중지하거나 삭제합니다. |

Microsoft Azure Portal → **Cost Management → Cost analysis**에서 구독·리소스 그룹·기간을 확인합니다. 필요하면 승인된 비용 알림을 설정하지만 이것은 강제 상한이 아닙니다. 실제 허용 예산·종료 시각·삭제/보존 계획을 기록표에 적습니다.

## 실제 값과 완료 근거를 기록합니다 {#handoff}

02에서 생성 계획을 만든 뒤 다음 표를 자신의 **`.lab/lab-ko/notes.md`**에 복사합니다. 아직 실행하지 않은 항목은 **미실행**으로 표시하고 각 단계가 끝날 때 실제 값으로 채웁니다. “준비됨”이라는 문장만으로 완료를 표시하지 않습니다.

| 필수 항목 | 기록할 실제 값·완료 근거 |
|---|---|
| 로그인 범위 | 사용자, tenant ID, subscription ID입니다. 비밀번호·토큰은 포함하지 않습니다. |
| 로컬 경로 | 본인의 환경 이름, bootstrap config 경로, 런타임 `.env` 경로입니다. 언어·기록 폴더는 자동 설정되며 `.env`는 생성 완료 후 기록합니다. |
| Microsoft Azure 환경 | 리소스 그룹·Microsoft Foundry account·project·project endpoint·Search 이름입니다. |
| 모델 | 네 배포의 실제 이름·제품명·버전·SKU·용량입니다. |
| 정책 검색 | 정책 원본·언어, 업로드 8건, knowledge base·connection 이름, `retrieval_verified`입니다. |
| Agent | 실제 이름, 고정 버전 1, 엄격한 출력 형식, 실제 Agent 도구 호출 확인입니다. |
| 데이터 | JSONL 경로, 12행, SHA-256, 등록 이름·버전입니다. |
| 평가 | Relevance 4·TaskAdherence 1, Judge 배포, query 전용 입력입니다. 첫 평가 뒤 실제 evaluation ID·v1 run ID도 추가합니다. |
| 승인 | 계획 해시, 승인 만료·예산·후보 한도·보존 기간입니다. |
| 종료 | 삭제가 승인된 정확한 그룹/객체와 예정 시각, 또는 보존 이유·비용 책임·검토일·후속 삭제 계획입니다. 공유·외부 종속성도 구분합니다. |

원본 영어·한국어 데이터와 비공개 실습 기록을 분리하며 다른 언어의 결과를 새 실행으로 바꾸어 표시하지 않습니다.

원본 서비스 파일에는 계정 메타데이터·토큰·서명된 URL이 포함될 수 있어 로컬에서 보관합니다. **합성 평가 결과 자체가 비밀인 것은 아닙니다.** 성공·실패를 모두 포함한 허용 필드만 공개하고, 불리한 결과가 아니라 자격 증명을 제외합니다. 과거 시도는 원본 감사 기록으로 보존하되 현재 버전 보고서에 계속 누적하지 않습니다.

## 삭제와 보존을 확인합니다 {#cleanup}

[10의 삭제 절차](handbook.md#cleanup)를 종료 체크리스트로 사용합니다. 생성 승인은 삭제 승인이 아니며 실습 자료만으로 타인의 자원을 삭제하지 않습니다.
{: .print-with-table}

| 대상 | 삭제 또는 보존 확인 |
|---|---|
| 실행 중인 평가·Optimizer | 취소 가능 여부, 실제 종료 상태, 남은 job ID를 기록합니다. |
| 로컬 소유 객체 | `cleanup` 계획의 정확한 대상과 실행 후 부재 상태를 확인합니다. |
| 포털 생성 객체 | 데이터셋·평가·대화·Optimizer·남은 빈 Agent 항목을 개별 확인합니다. |
| 전용 리소스 그룹 | 기본 경로입니다. 전체 인벤토리와 승인을 확인한 뒤 삭제하고 성공한 `az group exists`의 `false`를 기록합니다. |
| 보존·공유·외부 자원 | 삭제하지 않은 항목의 이름·이유·비용 책임·보존 검토일과 후속 계획을 기록합니다. |
| 비용·soft delete | 청구 지연과 이미 발생한 요금을 확인하고, 서비스별 보존·영구 삭제 정책을 별도로 적용합니다. |
| 증빙 | 결과와 실패 기록을 필요한 기간 비공개로 보관하며 로컬 `.lab`부터 삭제하지 않습니다. |
