# 운영자 사전 준비 · 다른 고객 환경에 배포할 때

**기본 실습 계정에는 본문 02장의 NCUS 리소스가 이미 존재합니다. 이 문서 때문에 중복 생성하지 마세요.**

다른 고객의 구독에서 진행할 때만 운영자가 수업 전에 아래 준비를 완료합니다. 참가자의 본 경로는 준비된 `.env`로 `python -m lab preflight`부터 시작합니다. 이 문서는 리소스 생성·역할 부여·과금을 자동 실행하지 않습니다.

## 1. 대상과 데이터 처리 조건을 합의

고객의 테넌트, 구독, 리소스 그룹, 비용 승인자, 허용 리전을 기록합니다. 이 패키지는 `northcentralus`만 허용합니다.

Global 배포·Global 학습과 지역 배포·지역 학습의 처리 조건은 다릅니다. NCUS 리소스만 생성해 두고 “모든 데이터가 NCUS에서만 처리된다”고 약속하지 않습니다.

## 2. Foundry 리소스와 프로젝트 생성

[공식 Foundry 리소스 생성 Quickstart](https://learn.microsoft.com/azure/foundry/tutorials/quickstart-create-foundry-resources)를 사용해 **새 Foundry 프로젝트**를 생성합니다. Foundry classic Hub 프로젝트가 아니라 본문이 사용하는 Foundry projects 2.x API의 프로젝트여야 합니다.

생성 전에 포털 요약에서 리전 `North Central US`와 대상 구독을 확인합니다. 생성 후 프로젝트 endpoint가 다음 형태인지 확인합니다.

```text
https://<account>.services.ai.azure.com/api/projects/<project>
```

정책상 사설 연결이 필요한 고객은 승인된 네트워크에서 실습합니다. 가이드를 실행하려고 네트워크 정책을 완화하지 않습니다.

## 3. 모델 배포 준비

Agent Service/Responses 호환 답변 모델, 품질 평가에 지원되는 평가 모델, Optimizer가 요구하는 모델을 각각 확인합니다. 모델 카탈로그의 지원과 고객 구독의 실제 쿼터는 별개의 조건입니다.

**IQ 검색 계획용 역할도 필요합니다.** 현재 코드의 `IQ_PLANNER_DEPLOYMENT`는 기반 모델 이름이 정확히 `gpt-5.5`인 배포를 요구합니다. 이 역할은 `OPTIMIZER_DEPLOYMENT`와 같은 gpt-5.5 배포를 재사용할 수 있지만, 답변 모델이나 다른 모델을 임의로 지정하면 사전 점검에서 중단합니다.

본문 프로파일의 `workshop-chat`, `workshop-judge`, `workshop-optimizer`는 **배포 이름**입니다. 다른 고객의 환경에서 동일한 이름을 쓰거나, `.env`에 실제 배포 이름을 넣습니다. 해당 이름의 모델이 자동 생성되지는 않습니다.

특정 새 모델을 모든 테넌트에서 쓸 수 있다고 가정하지 않습니다. 답변 모델을 바꿨다면 새 기준선을 만드세요. judge 모델을 바꾸었다면 기준선과 후보를 모두 같은 judge로 다시 평가해야 합니다.

## 4. Azure AI Search 준비

NCUS에 Azure AI Search 서비스를 준비합니다. 본문은 기존 **Basic** 서비스, Microsoft Entra ID 인증, 실제 지식 베이스 API를 사용하는 경로입니다.

[Azure AI Search 생성](https://learn.microsoft.com/azure/search/search-create-service-portal)과 [RBAC 사용](https://learn.microsoft.com/azure/search/search-security-rbac)을 확인합니다. 서비스 설정·데이터 업로드·질의의 역할이 다릅니다. 본문 IQ 역할표대로 필요한 주체만 필요한 범위에 권한을 부여합니다.

이 경로는 **semantic ranker 활성화**와 **Knowledge retrieval의 Free 요금제 사용 가능 상태**를 전제로 합니다. Azure portal의 Search 서비스 **Settings → Premium features**에서 두 항목을 각각 확인합니다. `semanticSearch`와 `knowledgeRetrieval`은 별도 설정이며, 무료 허용량이 소진되었다면 대기/별도 승인 없이 Standard로 자동 변경하지 않습니다.

새 서비스의 고정 용량 비용은 모델을 호출하지 않을 때도 발생할 수 있습니다. 전체 서비스 삭제는 기존 공유 실습의 정리와 별개의 관리자 작업입니다.

## 5. 기능별 접근과 관측 준비

평가, IQ, Optimizer, Frontier Tuning, Control Plane의 접근을 각각 확인합니다. Foundry 프로젝트가 생성되었다고 모든 Preview 기능이 자동 승인되는 것은 아닙니다.

실제 Frontier Tuning을 포함하는 수업이면 **수업 전에** 승인된 기능 화면·지원 모델·리전·작업 생성 경로를 확인합니다. 미승인 상태를 참가자가 몇 시간 뒤 발견하게 만들지 않습니다.

Control Plane의 tracing/monitoring에 필요한 Application Insights 연결, 데이터 수집 설정, 보존 정책과 역할도 미리 확인합니다. 감시 서비스 연결이 없는데 추적 화면에 데이터가 나타날 것이라고 가정하지 않습니다.

## 6. 프로파일 교체와 작은 실제 시험

`.env.example`을 복사해 새 `.env`를 만들고 다음을 고객의 값으로 교체합니다.

| 묶음 | 필드 |
|---|---|
| 로그인 범위 | `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `EXPECTED_AZURE_USER` |
| Foundry | 리소스 그룹·계정·프로젝트 이름, 프로젝트 endpoint, OpenAI endpoint |
| Search | 서비스 이름, Search endpoint |
| 배포 | `MODEL_DEPLOYMENT`, `JUDGE_DEPLOYMENT`, `OPTIMIZER_DEPLOYMENT`, `IQ_PLANNER_DEPLOYMENT` (gpt-5.5) |
| 참가자 | 고유한 `LAB_PREFIX` |

계정·endpoint를 바꾼 기존 `artifacts/`를 재사용하지 않습니다. 다른 디렉터리에 패키지를 새로 풀어 고객별 결과를 분리하세요.

```bash
python -m lab preflight
python -m lab validate
```

관리자는 비용 승인 후 본문에 따라 **새 baseline 에이전트와 3건 smoke**를 실제 수행합니다. 모든 참가자에게 미리 유료 호출을 대신 실행하지 않습니다. 문제를 해결한 후 같은 구성의 고객용 패키지를 전달합니다.
