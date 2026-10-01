# 운영자 사전 준비 · 고정된 Sol v1/v2 비교 {#operator-guide}

[참가자 가이드](handbook.md#start) · [강사 안내](facilitator.md#prepare) · [최신 v2 검증](verification.md)

환경은 수업 전에 준비합니다. 참가자 실습은 **데이터셋 → 평가기 → Foundry Evaluation → 사례 분석 → Agent Optimizer → 재평가**이며 인프라 구축은 추가 필수 실습이 아닙니다.

## 기존 격리 프로젝트 사용 {#start}

운영자가 소유한 North Central US 프로젝트, 기존 정책 연결과 승인된 합성 Contoso 데이터를 사용합니다. CLI·SDK·포털의 계정·테넌트·구독을 각각 확인합니다. 다른 신원이 로그인됐다고 자원을 재생성하거나 운영 트래픽을 사용하거나 공유 권한을 확대하지 않습니다.

영어 대상은 **`contoso-eval-en-sol`**입니다. 영어·한국어 원본 데이터는 분리하며 한국어 가이드가 새로운 한국어 서비스 실행을 입증하지는 않습니다.

<figure class="portal-shot" id="portal-resource-group">
<img src="../web/assets/portal/01-project-overview.png" alt="이전 한국어 실습의 Foundry 프로젝트 홈. 프로젝트 선택과 엔드포인트 위치 예시이며 현재 검증 결과가 아님" width="1440" height="1000" loading="lazy">
<figcaption><strong>한국어 실습 프로젝트 위치 예시입니다.</strong> 이전 프로젝트 홈이며 리소스 그룹 화면이나 현재 v2 결과가 아닙니다. 메뉴는 원래 영문입니다. 실제 프로젝트·리소스 그룹·현재 상태는 운영자 인수 정보로 확인합니다. <a href="../web/assets/portal/01-project-overview.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

## 세 모델 역할 확인 {#prepare}

| 역할 | 실제 배포 | 모델·버전 |
|---|---|---|
| Agent | `lab-agent-sol-dea3cec5` | **`gpt-6-sol` / `2026-09-22`** |
| 관리형 평가 Judge | `lab-judge-luna-dea3cec5` | **`gpt-6-luna` / `2026-09-22`** |
| Agent Optimizer 지시 생성 | `lab-planner-dea3cec5` | **`gpt-5.5` / `2026-04-24`** |

Sol은 카탈로그 표시뿐 아니라 고정된 Foundry 프롬프트 Agent 호출과 `knowledge_base_retrieve` 성공으로 확인했습니다. 응답은 네 필드 JSON 계약을 사용했습니다. 두 버전의 모델·읽기 전용 도구·추론 설정·구조화 출력 스키마를 동일하게 유지합니다.

Optimizer는 별도 역할이며 [지원 모델 목록](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-optimizer-overview#models)을 따릅니다. Agent나 Judge로 동작한다고 최적화 생성 모델로도 지원된다고 가정하지 않습니다.

<figure class="portal-shot" id="portal-models">
<img src="../web/assets/portal/02-model-deployments.png" alt="이전 한국어 실습 프로젝트의 모델 배포 목록. 이름·버전 확인 위치 예시이며 현재 Sol 배포 증거가 아님" width="1270" height="750" loading="lazy">
<figcaption><strong>모델·버전 열의 위치 예시입니다.</strong> 한국어 실습의 Sol 배포 이전 캡처이므로 현재 역할 표와 기록된 API 관측을 사용합니다. 이전 화면을 런타임 성공 근거로 사용하지 않습니다. <a href="../web/assets/portal/02-model-deployments.png" target="_blank" rel="noopener">원본 크기로 보기</a></figcaption>
</figure>

## 충분히 강한 v1과 통제된 v2 준비 {#bootstrap}

영어 기준선은 **`prompts/en/baseline.txt`**입니다. 정책 근거, 날짜, 분류, 불확실성과 실행 경계를 포함합니다. 개선을 크게 보이게 하려고 v1을 약화하지 않습니다.

**v1·v2는 지침 파일 번호가 아니라 Foundry Agent 전체 구성의 버전**입니다. 이번 비교에서는 지침만 다릅니다. 모델·도구·추론·출력 스키마가 달라지면 같은 조건의 실험을 새로 구성해야 하며 이전 모델 점수를 재사용하지 않습니다.

정식 버전은 변경할 수 없습니다. `lab/agents.py`의 `ensure_fixed_release`는 **1·2만 허용**하고 같은 구성의 기존 버전을 재사용하며, 다른 구성을 덮어쓰거나 v3를 조용히 만들지 않습니다. 개발에는 명시적으로 고정한 **`draft-…`**를 사용합니다. 이번 구독에서 초안 지원을 확인했지만 다른 구독은 초안 요청이 정식 버전으로 처리될 수 있으므로 별도 확인이 필요합니다.

`native_response_format()`은 공통 응답 스키마를 엄격한 생성 스키마의 지원 범위로 변환합니다. 인용 중복과 `needs_human`·route 일관성은 생성 후에도 확인합니다. 유효한 JSON 형식만으로 정책 정확성이 보장되지는 않습니다.

등록된 영어 **`contoso-eval-en-dev12` 버전 `1`**, `data/en/optimizer/dev.jsonl`의 12행과 원본 SHA-256을 유지합니다. Agent 입력은 **`query`만**이며 참고 열을 생성 입력으로 주입하지 않습니다.

<a id="sdk-prerequisites"></a>

Python 3.11–3.14, Azure CLI, 저장소 코드와 `requirements.lock`을 준비합니다. 다른 사용자의 환경 대신 별도로 준비한 실습 환경을 사용합니다.

```bash
source .venv/bin/activate
python -m pip install -r requirements.lock
az login
az account show --query "{user:user.name,tenant:tenantId,subscription:id}" -o json
```

출력 값을 승인된 프로젝트와 대조합니다. 운영자는 endpoint·구독·현재 evaluation ID·완료된 기준선 run ID를 제공합니다. 과거 리허설 ID를 복사하거나 Optimizer job ID를 evaluation ID로 사용하지 않습니다.

재평가 helper는 기준선 data source를 복사하고 **원격** 평가 계약을 검증합니다. 오래된 로컬 `JUDGE_DEPLOYMENT`로 실제 평가 정의의 Judge를 바꾸면 안 됩니다.

## 비교 조건과 비용 범위 고정 {#scope}

<a id="approval"></a>

| 항목 | 고정 조건 |
|---|---|
| 데이터 | 같은 영어 dev12 바이트·등록·버전·질문·참고 답변 |
| Relevance | 관리형 `builtin.relevance`, 1–5점, 임계값 **4** |
| TaskAdherence | 관리형 `builtin.task_adherence`, 이진 0/1, 통과 **1** |
| Judge | 두 평가기 정의에 같은 명시적 Luna 배포 |
| Agent | 같은 Sol 모델·버전, 도구, 추론, 엄격한 출력 스키마 |
| 변경 대상 | 지침만 변경, 정식 버전은 v1/v2 |
| Optimizer | Instruction만 선택, 모델·도구 설명 변경 끄기, 후보 수 제한 |
| 공개 보고 | 최신 v2·고정 v1 대조군과 12건 전체의 민감정보 제거 결과 |

카탈로그 평가기 버전은 비공개 서비스 루브릭이 완전히 고정됐다는 증거가 아닙니다. 실제 정의·설정과 이 한계를 남깁니다. 재사용 dev12의 개선은 향후 점수·독립적 일반화·운영 승인을 보장하지 않습니다.

## 최소 권한 확인 {#rbac}

[현재 Foundry RBAC 안내](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry)에 따라 승인된 프로젝트 작업만 허용합니다. 역할 할당 권한과 모델·평가 사용 권한은 별개입니다.

정책 도구는 읽기 전용으로 유지합니다. 편의를 위해 구독 Owner를 부여하거나 네트워크 제한·조직 정책을 해제하거나 사용자 간 토큰을 옮기지 않습니다.

## 비용과 운영 경계 {#cost}

평가는 Agent·Judge를 호출하고 최적화에는 추가 내부 호출이 있습니다. 할당량은 무료 사용량이 아니고 GlobalStandard는 NCUS 내 처리 보장이 아닙니다. 관측 토큰과 실제 청구액을 구분하며 미확인 비용을 0원으로 표시하지 않습니다.

비용·정리 담당자를 지정합니다. Optimizer 순위 상승만으로 운영용 게시나 후보 활성화를 하지 않습니다. 실측 결정과 승인된 운영 검토가 없다면 원본을 유지합니다. 브라우저를 닫아도 과금은 멈추지 않습니다.

## 현재 비교 쌍 인수 {#handoff}

현재 Agent·버전 ID, 역할별 배포, dev12 해시, 평가 설정, SDK 환경, 승인 범위와 [최신 검증 기록](verification.md)을 전달합니다. 영문 보고서는 모든 사례의 실제 응답·점수·채점 이유를 공개합니다.

원본 서비스 파일에는 계정 메타데이터·토큰·서명된 URL이 포함될 수 있어 로컬에서 보관합니다. **합성 평가 결과 자체가 비밀인 것은 아닙니다.** 성공·실패를 모두 포함한 허용 필드만 공개하고, 불리한 결과가 아니라 자격 증명을 제외합니다. 과거 시도는 원본 감사 기록으로 보존하되 현재 버전 보고서에 계속 누적하지 않습니다.
