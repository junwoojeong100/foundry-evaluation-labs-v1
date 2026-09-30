# 참고 원본 → v1 통합·마이그레이션 결정

**조사 기준: 2026-09-30 KST. 이 문서는 구현 완료나 LIVE 실행 보고서가 아니라, 고정한 두 소스의 비교와 통합 요구조건입니다.**

참고 원본의 장점은 설치 전에 문제를 발견하게 하고, 작은 실험을 끝까지 실행·판단·재개할 수 있게 만든 점입니다. 통합 대상의 장점은 Contoso 데이터 계약, 실제 Agent Service 버전, MCP 기반 IQ, 엄격한 근거 처리와 오프라인 웹·인쇄 제작 체계입니다. **원본의 학습·실행 패턴을 Contoso에 맞게 새로 구현하고, 통합 대상의 기반을 대체하지 않습니다.**

**이름 안내:** 현재 유지보수 저장소와 실제 디렉터리는 `foundry-evaluation-labs-v1`이며, 가이드 표기는 **v1**입니다. 이 문서의 **참고 원본**은 `foundry-evaluation-labs-v0.9`에 보관된 과거 소스를 뜻합니다. 옛 로컬 경로는 가상환경과 동결 기록의 절대 경로를 유지하는 호환용 링크로 남기며, 실습 데이터·평가기준·Azure 리소스는 바꾸지 않습니다.

## 1. 소스·범위·판정 용어

| 대상 | 고정 소스 | 이번 작업의 경계 |
|---|---|---|
| 현재 가이드 v1 | [`junwoojeong100/foundry-evaluation-labs-v1`](https://github.com/junwoojeong100/foundry-evaluation-labs-v1), 통합 시작 커밋 `8ea5d3aedb2aeef0727d16031033969f30c2d0b0` | PRIVATE 유지. 문서 표기는 v1으로 통일하며 실습 내용·환경은 변경하지 않음 |
| 읽기 전용 참고 원본 | [`junwoojeong100/foundry-evaluation-labs-v0.9`][v1-root], 커밋 `93bc07e31373c4cfc278a2dc3757785946404cf2` | 현재 PRIVATE·Archived로 보관되어 있음. 이번 이름 변경에서 원본 파일·브랜치·가시성·보관 상태는 변경하지 않음 |
| 최초 산출물 | `guide/integration-migration.md` | 구현 전에 비교·계약을 먼저 저장하고 형제 구현 담당자에게 전달 |
| 후속 문서 범위 | `README.md`, `README.en.md`, `guide/*.md`의 지정 원문 | 가이드 우선 순서로 참가자·운영자·강사·SFT·검증·이관 문서를 통합. HTML/PDF/스크립트/코드는 각 소유 담당자가 처리 |

시작 시 로컬/원격 HEAD 일치와 두 작업 트리의 청결은 통합 담당자의 사전 확인 기록입니다. 초기 비교 조사는 로컬 HEAD와 추적 파일을 읽는 방식이었습니다. 이후 이름 변경에서는 GitHub 저장소의 동일 ID·현재 이름·비공개/보관 상태와 원본 커밋의 존재를 별도로 확인했으며, Azure 리소스는 변경하지 않았습니다. 아래 **기존**은 통합 대상 시작 커밋의 동작이고 통합 경로는 현재 추가한 소스에 연결합니다. 설계 시의 **제안**과 현재 구현/로컬 검사/실제 실행 상태는 구별합니다. 이 표 자체는 LIVE 완료 증거가 아닙니다.

- **KEEP**: 통합 대상에 이미 있는 기반·경계를 유지합니다.
- **REINFORCE**: 참고 원본에서 확인한 패턴을 독자적으로 구현하거나 기존 동작을 보강합니다.
- **EXCLUDE**: 도메인·제품·권한·증거 계약이 다른 내용은 가져오지 않습니다.
- 표의 상대 링크는 **실제로 존재하는 현재 가이드의 통합 지점**입니다. 새 산출물 경로 예시는 별도로 **제안**이라고 표시하며, 존재하는 실행 명령처럼 안내하지 않습니다.

## 2. 기능 단위 결정 매트릭스

### 2-1. KEEP — 유지할 통합 대상의 기반

| ID / 기능 | 참고 원본에서 확인한 비교점 | 현재 가이드의 기존 경로·통합 지점 | 결정 이유와 유지 조건 |
|---|---|---|---|
| K01 · Contoso 시나리오·출력 계약 | [v1 README][v1-readme]는 다른 업무 도메인과 필드를 사용 | [정책](../data/knowledge/documents.json), [데이터 계약](../data/README.md), [응답 스키마](../schemas/response.schema.json) | **KEEP.** Contoso Atlas Cloud와 `answer`·`citations`·`route`·`needs_human` 유지. 업무 실행 도구가 없다는 경계도 유지 |
| K02 · 원본 100건·분할 | [입문][v1-intro]의 dev/holdout 분리 원리는 유용하지만 규모·구조는 다름 | [원본](../data/cases.jsonl), [분할 매니페스트](../data/manifest.json), [생성기](../scripts/build_datasets.py), [검사](../tests/test_datasets.py) | **KEEP.** train 56 / validation 12 / dev 12 / test 20, 상황 그룹과 기존 레이블을 보존. 새 DEMO·교정·fresh holdout으로 원본을 교체하지 않음 |
| K03 · 실제 에이전트 버전 | [v1 모델 클라이언트][v1-client]의 직접 모델 호출은 Agent Service 실행이 아님 | [에이전트](../lab/agents.py), [실행](../lab/batch.py), [검사](../tests/test_agent_run.py) | **KEEP.** `agent_reference.name/version`, 프롬프트 스냅샷, 실행 전후 모델 구성 확인 유지. 직접 채팅으로 바꾸고 에이전트 실습이라 부르지 않음 |
| K04 · MCP IQ 연결 | [v1 검색 모듈][v1-retrieval]은 직접 검색 증거를 제공 | [IQ](../lab/knowledge.py), [캡처](../lab/batch.py), [검사](../tests/test_knowledge.py) | **KEEP.** Search → knowledge source/base → 프로젝트 MCP 연결 → 버전 에이전트의 도구 호출을 보존. 직접 검색 probe는 에이전트 관리 ID의 도구 실행 증거를 대신하지 않음 |
| K05 · 실패를 포함한 평가 | [v1 평가][v1-evaluation]는 누락·중요 실패·개별 회귀를 차단 | [근거 엔진](../lab/evidence.py), [게이트](../config/gates.json), [관리형 평가](../lab/managed_eval.py), [검사](../tests/test_evidence.py) | **KEEP.** 오류 행을 분모에서 제거하지 않고, 미완료·누락·잘못된 점수·critical 실패는 보류. 새 지표에도 같은 원칙 적용 |
| K06 · 공개 설정과 내부 서비스 버전 구분 | [v1 참고][v1-reference]는 평가기·모델 계약과 작은 표본의 한계를 설명 | [관리형 평가](../lab/managed_eval.py), [검증 범위](verification.md), [run 스키마](../schemas/run.schema.json) | **KEEP.** catalog selector와 공개 설정 해시는 비공개 judge 프롬프트·서비스 내부 릴리스의 고정 증명이 아님. 해시는 전자서명이나 독립 감사가 아님 |
| K07 · 제품 경계·운영 루프 | [v1 진행자 가이드][v1-facilitator]는 교육 완료와 출시 판단을 구별 | [본문](handbook.md), [강사](facilitator.md), [인수 파일](../lab/handoffs.py), [SFT 부록](sft-appendix.md) | **KEEP.** Prompt/Agent Optimizer, Frontier/SFT, 준비/실행/학습 완료/개선을 구분. 운영 실패를 다음 데이터로 돌리는 흐름 유지 |
| K08 · 안전한 로컬 출판·실행 범위 | [v1 준비][v1-setup]의 복사·완료 확인·재개 안내가 보완점 | [웹 빌더](../scripts/build_guide.py), [인쇄 빌더](../scripts/build_print.py), [웹 동작](../web/app.js), [정리](../lab/cleanup.py) | **KEEP.** 오프라인 읽기, 원문 그대로 코드 복사, 명령 자동 실행 없음, 휴대 가능한 PDF 링크, 소유 기록 기반 정리. 가이드를 읽거나 DEMO로 전환했다고 공유 자원을 변경하지 않음 |

### 2-2. REINFORCE — 참고 원본의 장점을 새로 구현할 부분

| ID / 기능 | 구체적인 원본 근거 | 현재 가이드의 기존 경로·제안 통합 지점 | 시작 커밋의 차이와 완료 조건 |
|---|---|---|---|
| R01 · 설치 전 그럴듯한 오답 | [DEMO 0장][v1-offline], [입문 0장][v1-intro]의 먼저 선택하고 규정으로 확인하는 구성 | [본문](handbook.md), [Contoso 정책](../data/knowledge/documents.json), [강사](facilitator.md) | **REINFORCE.** 설명만 읽는 도입을 짧은 Contoso 판단 활동으로 보강. 작성 예시를 실제 기준선 실패로 표시하지 않음. 예시는 3절 참고 |
| R02 · 진짜 오프라인 authored DEMO | [DEMO][v1-offline], [`demo_entries`와 지연 import][v1-cli], [fixture 매니페스트][v1-demo-manifest] | [통합 DEMO](../lab/demo.py), [CLI](../lab/cli.py), [파일 계약](../lab/files.py), [CLI 검사](../tests/test_cli.py) | **REINFORCE.** 시작 커밋은 가이드만 오프라인이고 실행 DEMO가 없으며 CLI가 SDK를 최상위 import. 통합 경로는 `python3 -S -m lab demo`로 분리하며 계정·설정·SDK·네트워크 없는 검사를 요구 |
| R03 · 행동→명령→증거→다음 단계 | [입문 진행표][v1-intro], [재개 표][v1-setup], [진행자 체크포인트][v1-facilitator] | [본문](handbook.md), [강사](facilitator.md), [문서 명령 검사](../tests/test_documentation.py) | **REINFORCE.** 각 단계에 열 파일·행 ID·예상 상태·중단 이유·다음 동작을 명시. 정상 대기, 실행 오류, 유효한 품질 보류를 구별하고 점수를 맞추려고 재실행시키지 않음 |
| R04 · 업무 전용 버전 평가기·교정 | [`register`, `contract`, `calibration_cases`][v1-advanced-evaluation], [업무 rubric][v1-policy-rubric], [교정 설명][v1-complete] | [통합 교정/Judge](../lab/calibration.py), [16개 fixtures](../data/calibration/fixtures.jsonl), [업무 정의](../config/evaluators/policy-correctness.v1.json), [게이트](../config/gates.json) | **REINFORCE.** 기존의 두 내장 지표·일반 rubric만으로 업무 의미를 검증했다고 할 수 없음. Contoso 전용 정의/버전/해시·모델·입력 매핑·척도와 **10건 이상(현재 16건)**의 교정 사례를 결속. fixtures 자체와 실제 Judge 교정 실행은 별도 상태 |
| R05 · 검색 근거성 ≠ 정책·업무 정확성 | [v1 검색 문맥 평가][v1-reference], [업무 평가 입력][v1-advanced-evaluation] | [캡처](../lab/batch.py), [통합 평가 입력](../lab/calibration.py), [검색 근거성 정의](../config/evaluators/retrieval-groundedness.v1.json), [근거 엔진](../lab/evidence.py) | **REINFORCE.** 시작 커밋의 `groundedness`는 고정 정책 `context`에 매핑되고 `retrieved_context`는 보관만 함. 과거 점수를 새 의미로 재사용하지 말고, 관측 검색 문맥과 참조 정책/기대 행동을 별도 입력·지표·설명으로 제공 |
| R06 · AI 보조 검토와 사람 판단 | [`review_command`][v1-cli], [`review_problems`][v1-evaluation], [검토 유형 설명][v1-reference] | [통합 governance](../lab/governance.py), [CLI](../lab/cli.py), [파일 계약](../lab/files.py), [본문](handbook.md) | **REINFORCE.** 기존 문서의 권고를 응답 해시·사례·판정·이유·시각·검토 주체에 묶인 추가 기록으로 보강. AI 기록만으로 사람 검토/운영 승인을 충족하지 않으며 외부 human 주장도 `external_unverified`로 보존 |
| R07 · 실행 가능한 freeze→fresh holdout | [`freeze_command`, `create_holdout_command`, `register_holdout_command`][v1-advanced-cli], [6–7장][v1-complete] | [통합 governance](../lab/governance.py), [fresh12 계약](../config/evaluators/fresh-holdout-gates.v1.json), [실행](../lab/batch.py), [근거 엔진](../lab/evidence.py), [본문](handbook.md) | **REINFORCE.** 기존은 동결 체크리스트와 이미 작성된 test20. 변경을 거부하는 동결과 **이후 생성·등록한 별도 holdout**을 추가. 원본 100건/분할·test20 게이트는 보존하고 fresh12를 별도 버전 계약으로 결속 |
| R08 · 실제 embeddings/vector/hybrid/IQ 계획 | [`embed`, `vector_index`, `retrieve`][v1-retrieval], [벡터·계획 확인][v1-complete] | [통합 임베딩](../lab/embeddings.py), [IQ](../lab/knowledge.py), [설정](../lab/config.py), [검사](../tests/test_knowledge.py) | **REINFORCE.** 시작 커밋은 텍스트/semantic 인덱스와 `embedding_model: null`. 실제 임베딩·벡터 필드·차원·vector-only/hybrid 요청과 반환 청크, IQ `modelQueryPlanning`/하위 질의 증거를 각각 확인해야 함 |
| R09 · 명시적 후속 발언과 최종 답 | [`run_command`의 대화 프로토콜][v1-advanced-cli], [개발용 후속 발언][v1-followups], [대화 검사 안내][v1-complete] | [버전 에이전트 실행](../lab/batch.py), [응답 스키마](../schemas/response.schema.json), [근거 엔진](../lab/evidence.py), [실행 검사](../tests/test_agent_run.py) | **REINFORCE.** 기존은 독립 단일 질문. `clarify` → **사용자 입력 또는 출처가 명시된 scripted-user 발언** → 최종 답을 캡처. 에이전트가 누락 정보를 스스로 만들어 넣지 않으며, 첫 응답의 위험을 최종 정답으로 지우지 않음 |
| R10 · 멱등 재개와 중복 호출 방지 | [입문 `run`/`judge` 재사용][v1-cli], [단계별 pending 저장][v1-advanced-cli], [재개 한계][v1-setup] | [배치](../lab/batch.py), [관리형 평가](../lab/managed_eval.py), [파일 계약](../lab/files.py), [배치 검사](../tests/test_batch.py) | **REINFORCE.** 기존 배치는 디렉터리가 있으면 새 run-id를 요구함. 같은 계약의 완료 결과는 검증 후 재사용, 부분 결과는 저장된 행을 건너뛰고 이어감. 입력 변경·손상·원격 제출 여부 불명확 시 자동 재호출하지 않음 |
| R11 · 통제 비교와 원인 설명 | [동일 초기 문맥 replay와 planned-dev 구분][v1-complete], [개별 회귀 검사][v1-evaluation] | [비교](../lab/evidence.py), [본문 03–06단계](handbook.md), [인수 파일](../lab/handoffs.py) | **REINFORCE.** IQ 추가 효과와 지시 개선 효과를 분리하는 기존 설계를 유지하며 사례별 전후 근거를 쉽게 읽게 함. 대화 절차까지 바꾸면 “프롬프트 문구만의 효과”로 주장하지 않음. 평균 상승으로 critical 회귀를 상쇄하지 않음 |
| R12 · 비용·데이터·보존의 승인 상태 | [준비/비용/DEMO 전환][v1-setup], [보존 우선 정리][v1-cleanup] | [통합 bootstrap](../lab/bootstrap.py), [승인 스키마](../infra/approval.schema.json), [환경 준비](admin-setup.md), [정리](../lab/cleanup.py) | **REINFORCE.** `--confirm`은 동작 확인이지 전체 승인 대체물이 아님. 명시적 무상한 금액 정책과 유한한 호출/작업·대상·보존·처리 범위를 구분하고 승인 밖의 변경은 차단 |

### 2-3. EXCLUDE — 그대로 가져오지 않을 내용

| ID / 제외 대상 | 참고 원본 소스 | 현재 가이드에 적용할 경계 | 이유 |
|---|---|---|---|
| X01 · 출장 도메인 데이터·프롬프트·필드 | [v1 데이터/규정][v1-root], [업무 rubric][v1-policy-rubric], [후속 발언][v1-followups] | [Contoso 데이터](../data/README.md), [프롬프트](../prompts/baseline.txt), [응답 스키마](../schemas/response.schema.json) 유지 | 도메인 규정·금액·정답·ID를 섞으면 하나의 Contoso 실험이 아니게 됨. 교정/DEMO/대화 모두 Contoso 근거로 새로 작성 |
| X02 · 과거 LIVE 답변·점수·영상 | [기록 fixture][v1-recorded], [실행 기록 설명][v1-complete], [미디어 설명][v1-media] | [검증 기록](verification.md), [패키징](../scripts/package_lab.py) | 이전 환경의 관측값이지 현재 가이드의 새 실행 증거가 아님. `recorded-live`를 `live`/`authored-demo`로 바꿔 가져오거나 성공 숫자를 전사하지 않음 |
| X03 · 원본 모델·리전·리소스 기본값 | [설정/SDK 계약][v1-reference], [검색 설정][v1-retrieval] | [설정](../lab/config.py), [환경 템플릿](../.env.example), [사전 점검](../lab/preflight.py) | 원본의 모델명·차원·planner·리전 고정값은 현재 NCUS 경로의 지원 증명이 아님. 통합 대상 시작 커밋의 기존 리소스 프로파일도 실행에 재사용하지 않음. 새 승인 범위의 비공개 환경만 사용 |
| X04 · 여러 독립 runner 통째로 이식 | [입문 CLI][v1-cli], [완결형 CLI][v1-advanced-cli] | [기존 진입점](../lab/__main__.py), [CLI](../lab/cli.py), [SDK 계약](../pyproject.toml) | 파일 복사는 중복 상태·의존성·서로 다른 데이터 계약을 낳음. 필요한 기능만 기존 `python -m lab` 구조에 통합하고 DEMO 의존성은 분리 |
| X05 · 다른 과제의 합격선·강제 실패 | [원본 acceptance][v1-acceptance], [`freeze_command`][v1-advanced-cli] | [기존 게이트](../config/gates.json), [근거 엔진](../lab/evidence.py) | 8건·100% 또는 입문 80%를 근거 없이 이식하지 않음. 원본 완결형의 “기준선 실패가 있어야 freeze” 조건 때문에 현재 실습의 LIVE 실패를 조작하지 않음. 필수 지표를 빼거나 기준을 낮춰 통과시키지 않음 |
| X06 · 과도한 검증/권한 주장 | [초기 필드 검사 한계][v1-complete], [legacy reviewer 처리][v1-reference] | [근거 엔진](../lab/evidence.py), [관리형 평가](../lab/managed_eval.py), [검증 기록](verification.md) | 초기 JSON 필드 통과 ≠ 초기 설명의 의미 안전성. 검토 유형 자기신고 ≠ 신원 인증. 새 기록에서 누락 reviewer를 사람으로 추정하지 않음. 로컬 mock 통과 ≠ 클라우드 가용성 |
| X07 · 무허가 본문·코드·그림 재배포 | [v1 고정 트리][v1-root] | 이 문서의 5절, [배포 패키징](../scripts/package_lab.py) | 명시적 라이선스를 찾지 못함. 공개 저장소라는 이유로 복사·수정·재배포 권리가 있다고 가정하지 않음. 출처 표시는 사용 허가를 대신하지 않음 |

## 3. 통합 구현의 증거 계약

아래는 통합에 적용하는 증거 계약입니다. 현재 참가자용 명령은 실제 CLI parser와 [본문](handbook.md)에 맞춰 확인했습니다. 새 CLI 이름·파일 형식을 추가할 때도 구현과 테스트를 함께 버전 관리하며, 명령의 존재를 실제 LIVE 성공으로 확대하지 않습니다.

### 3-1. Contoso 도입과 오프라인 DEMO

설치 전 질문 예시는 **9월 문의라고 과거 구매의 환불 기한도 바뀌는가**로 구성할 수 있습니다. `ATLAS-REF-001`에는 9월 1일 이전 최초 월 구매의 7일 기한과 이후 구매의 14일 기한이 분리되어 있습니다.

- **작성 질문 예시:** 8월 28일 10:00 KST에 최초 월 구독을 구매했고 유료 작업·크레딧 사용 없이 9월 6일 10:00에 환불을 문의한다.
- **의도적으로 틀린 작성 답변 예시:** “9월 문의이므로 14일 규정으로 환불을 승인했습니다.”
- **학습자가 확인할 점:** 구매 시점에 따른 기존 7일 기한이며, 신청 자격·승인·실제 처리는 다르다. 도우미가 승인했다는 근거도 없다. 규정 설명과 실행 권한을 각각 판단한다.

이 예시는 원본 100건을 편집하거나 LIVE 실패를 만들기 위한 것이 아닙니다. DEMO의 답변·점수·이유는 모두 **작성 예제**로 표시하며 작성 주체도 정직하게 남깁니다. AI가 작성한 fixture를 사람이 검토한 실행 기록으로 표시하지 않습니다.

DEMO는 로컬 데이터·해시 검증과 결과 읽기만 수행해야 합니다. Azure 인증, `.env` 로딩, SDK import, DNS/HTTP 연결, 원격 평가 제출이 없어야 합니다. 네트워크·자격 증명 호출을 실패시키는 검사와 외부 패키지 없는 Python 검사로 확인합니다. 예를 들어 **제안 경로** `artifacts/demo/<run-id>/`에 LIVE와 분리하고, authored 점수로 운영 준비나 실제 성능 향상을 선언하는 상태는 반환하지 않습니다.

**통합 브랜치의 로컬 진입점:** [새 DEMO 모듈](../lab/demo.py)은 다음 명령으로 실행합니다. `-S`는 site-packages 자동 로딩 없이 실행하는 Python 옵션이며 Azure SDK나 dotenv 설치를 요구하지 않는 경로를 확인하는 데 사용합니다.

```bash
python3 -S -m lab demo
```

기본은 표준 출력이며, `--out FILE`을 명시하면 새 파일에 작성 결과를 저장합니다. 이미 있는 출력 파일은 덮어쓰지 않습니다. `AUTHORED_DEMO_NOT_LIVE`, `DEMO_COMPLETED`, `NOT_EVALUATED_LIVE`의 구분을 읽고 사람 검토·운영 승인이 생기지 않았음을 확인합니다. 이 진입점의 존재는 R02의 모든 수업·재개 요구조건이나 다른 클라우드 기능의 구현 완료를 뜻하지 않습니다.

**환경별 산출물 경로:** 통합된 [파일 도구](../lab/files.py)는 `LAB_ARTIFACTS_DIR`가 있으면 그 경로, 없으면 저장소의 `artifacts/`를 사용합니다. 이 문서의 `artifacts/...`는 논리적 예시이며 실행 환경이 저장소 밖이면 실제 경로는 달라집니다. 런타임 경로를 기록하는 코드는 `.relative_to(ROOT)`를 강제하지 말고 `artifact_reference(path)`로 저장소 상대 경로 또는 외부 절대 경로를 안전하게 표현해야 합니다. 환경별 `.env`·승인 기록·실행 결과는 비공개로 유지하고 이전 환경 프로파일을 복사해 운영하지 않습니다.

### 3-2. 평가 축과 교정

| 축 | 허용 입력 | 해석·누락 처리 |
|---|---|---|
| 규칙 검사 | 응답 전체 JSON, 기대 route/인용/사람 필요 여부, 금지 주장 | 결정적 필드 검사와 문자열 검사의 범위만 주장. 자연어 전체 의미 검사로 부르지 않음 |
| 검색 근거성 | 그 응답을 생성할 때 **실제로 관측한** 검색 문맥·질문·답변 | 관련 문서 ID가 있다는 것만으로 통과하지 않음. 문맥/검색 실패가 있으면 측정 불가 또는 실패이며 만점으로 채우지 않음 |
| 정책·업무 정확성 | 고정 정책 참조, 기대 행동, 실제 응답/대화 | 업무 전용 버전 rubric으로 시점·자격·권한·허위 완료·확인 질문 판단. 기대 행동은 평가자용이며 에이전트 입력에는 넣지 않음 |
| 관련성 | 질문 또는 명시적으로 완성된 대화와 응답 | 불편한 점수를 숨기려고 기존 필수 Relevance를 제외하지 않음. 초기 확인 질문과 최종 업무 완료의 평가 단위를 명시 |
| 사람 검토 | 실제 응답과 근거, AI 점수와 분리한 판단·이유 | assistant 기록은 보조 기록. 사람이 실제로 검토하기 전에는 사람 승인 대기 |

기존 `groundedness`의 정책 참조 의미를 유지할지 새 이름으로 분리할지는 스키마 버전 변경에서 결정해야 합니다. **과거 점수를 새 의미의 지표로 재사용해서는 안 됩니다.** `retrieved_context`를 고정 정책으로 바꾸거나 정답을 생성 입력에 넣어서 검색 실패를 숨기지도 않습니다.

Contoso 교정 fixtures는 **10건 이상**, 정상과 오답을 모두 포함합니다. 예를 들어 올바른 일반 안내·기한 경계·확인 질문·사람 이관·거절과, 규정 시점 오류·가짜 인용·허위 환불 완료·필드/설명 모순·judge 지시 주입을 대조합니다. 동일 응답에 단순히 통과 라벨을 붙여 반복하는 것이 아니라 도메인 실패를 구별하게 합니다.

교정 기록에는 fixture/정책/rubric 해시, 기대 판정, 실제 점수·이유, 불일치, 평가기 버전·모델 관측값을 묶습니다. 레이블은 judge에 주지 않으며, 불일치가 남거나 점수가 없으면 교정 완료가 아닙니다. 로컬 작성 점수는 실제 클라우드 교정 결과가 아니고, 업무 평가기의 교정 통과는 모든 내장 지표의 정확성이나 holdout 성능을 보증하지 않습니다.

### 3-3. 동결 후 새 평가와 멱등 재개

1. dev에서 후보를 선택하고 원본 100건·기존 split 해시가 유지되는지 확인합니다.
2. 실행 가능한 freeze가 프롬프트, Agent Service 이름/버전, 생성 설정, 관측 모델 버전, 정책/인덱스/임베딩/planner 계약, evaluator/rubric/교정, gate, 대화 프로토콜을 결속합니다. 공개되지 않은 서비스 내부 버전은 미확인으로 남깁니다.
3. 동결 이후 별도 fresh holdout을 생성·등록하고 동결 해시·생성 근거·생성 시각·ID/질문/상황 그룹 중복 검사·평가용 후속 발언을 기록합니다. **제안 경로**는 `artifacts/governance/` 아래 별도 holdout 데이터와 등록 기록입니다. 기존 `data/cases.jsonl`이나 `data/splits/test.jsonl`을 덮어쓰지 않습니다.
4. 승인된 새 holdout은 **12건의 별도 평가 계약**으로 사전에 정의합니다. 기존 `minimum_test_rows: 20` 게이트를 몰래 낮추거나 12건으로 그 게이트를 통과했다고 표시하지 않습니다. 새 계약의 표본·coverage·critical·지표 요구조건도 동결하고 누락과 critical 실패는 허용하지 않습니다. 부족한 표본을 맞추려고 기존 test 일부를 새 질문으로 재명명하지 않으며 템플릿 변형을 광범위한 일반화 검증이라고 과장하지 않습니다.
5. 같은 동결 계약의 baseline/candidate를 실행·채점·검토하고 실패를 포함한 결과를 보존합니다. 동결 후 변경, 중복·누락·오류·불완전한 judge·critical 실패는 **HOLD**입니다. 최종 통과도 사람의 운영 승인이 아닙니다.
6. 완료된 결과를 재호출하지 않고 검증 후 읽으며, 부분 실행은 같은 계약의 저장 행과 단계부터 재개합니다. 원격 요청 성공 후 로컬 저장 전 장애가 있었다면 정확히 한 번 실행/과금됨을 보장하지 않습니다. 원격 ID가 불명확하면 복구·확인 전 자동 재제출을 막습니다.

holdout을 읽고 후보/rubric/기준을 수정했다면 기존 holdout은 더 이상 미노출이 아닙니다. 이전 실패를 보존하고 새 실험·새 holdout으로 넘어갑니다. 보류를 없애기 위한 재추출·재채점 반복은 재개가 아닙니다.

### 3-4. 검색과 대화의 추가 증거

임베딩은 실제 제공자 응답, 모델·버전/차원, 코퍼스 해시와 연결된 캐시를 요구합니다. 벡터가 유한한 숫자이며 차원이 맞는지 확인하고, vector-only 요청에는 텍스트 검색이 없었는지, hybrid에는 텍스트와 벡터가 함께 있었는지 따로 남깁니다. IQ 계획은 일반 `activity`가 비어 있지 않다는 사실만으로 인정하지 않고 실제 계획 유형·하위 질의·반환 청크를 확인합니다. **이 문서 작성 중에는 어느 것도 실행하지 않았습니다.**

통합 `iq vectors`의 직접 vector/hybrid 진단은 **에이전트가 제공받은 context의 증거가 아닙니다.** `iq probe`의 계획·출처 증거와 실제 Agent Service+MCP의 사례별 출력도 각각 구분하며, 진단 파일로 응답의 `retrieved_context`를 대체하지 않습니다.

통합 [설정](../lab/config.py)의 선택적 `embedding` / `EMBEDDING_DEPLOYMENT` 필드는 배포 이름을 전달하는 계약입니다. 필드가 생겼거나 값이 채워졌다는 것만으로 실제 임베딩·벡터 업로드·검색이 검증되지는 않습니다. 필수 배포가 없으면 실제 벡터 실행은 중단하고 텍스트 검색을 벡터 성공으로 바꾸어 표시하지 않습니다.

대화는 초기 질문 → `clarify` 응답 → 실제 사용자 또는 명시된 scripted-user 후속 발언 → 최종 응답을 각각 저장합니다. 대화·검색·기대 행동의 해시와 출처를 연결하고, 에이전트가 사용자의 날짜·권한·사용 이력을 생성한 것을 사용자 응답으로 저장하지 않습니다. 초기 필드만 검사했다면 그 한계를 표시하며, 초기 설명의 위험까지 확인하기 전 전체 대화가 안전하다고 결론 내리지 않습니다.

## 4. 실행 승인과 현재 상태

**현재 상태: 신규 NCUS 인프라, 실제 모델/Agent/MCP/검색/평가, 두 Optimizer 및 SFT 학습·배포·paired 평가를 실행했습니다. 품질 판단은 HOLD입니다.** 초기 `ServiceModelDeprecated`, 생성 충돌, 관측 연결 오류와 이후 복구를 각각 보존했습니다. 최종 결과는 [검증 기록](verification.md)과 [신규 LIVE 증거](../evidence/integration-20260930/live-summary.json)에 있습니다.

초기에는 승인 대기였고, 이어 RG 생성만 허용되었습니다. 이후 사용자가 통합 담당자의 구체적인 제한 계획을 참조하여 사용을 승인했으며, 후속 확인으로 **금액 상한을 명시적으로 해제**했습니다. 호출·후보·학습 epoch·대기 시간과 신규 리소스 범위의 제한은 유지합니다. **이제 예산 승인을 기다리는 상태와 서비스 실행을 기다리는 상태를 혼동하지 않습니다.** 다만 승인 자체는 모델 가용성·권한 적용·Preview 접근·학습 성공을 보장하지 않습니다.

**클라우드 변경·유료 실행은 통합 담당자가 승인 범위에서 수행했습니다.** 분담 에이전트는 정해진 파일 구현·검사와 읽기 전용 조사를 수행했습니다. 가이드 초안 검증 뒤 첫 생성 시도에서 하위 자원 0건·ARM 조회 404의 실패가 있었고, 응답 생성 전에 gpt-4.1-mini / 2025-04-14 / Standard를 명시 선택했습니다. 이후 같은 새 RG에서 실제 인프라와 실습을 완료했으며 실패 원본도 보존합니다. 삭제 승인은 없습니다.

원문 승인 대화와 기계가 읽는 승인 기록은 비공개 운영 자료로 보관합니다. 웹·PDF·ZIP에 복사하지 않으며 여기에는 **승인 범위 요약과 실행 상태**만 남깁니다. 로컬 DEMO·mock 검사도 여전히 실제 LIVE 결과를 대신하지 않습니다.

| 승인 항목 | 이번 통합에서의 상태 | 실행 전에 필요한 결정 |
|---|---|---|
| 금액 상한 | **금액 상한 없음 — 명시 승인됨** | 이전 `50 USD` 제한으로 실행을 차단하지 않음. 아래 호출/작업·리소스 범위는 유지하고 실제 비용과 지속 자원 비용을 관측 |
| 리소스·작업·RBAC 범위 | **해당 새 RG와 신규 리소스의 최소 RBAC만 승인** | 기존/공유 리소스·공유 정책·다른 리전을 변경하지 않음. 계획과 소유 기록에 묶인 대상만 사용 |
| 데이터 처리 | **합성 데이터의 GlobalStandard 및 Global/Developer 처리 승인** | 계획에 명시한 합성 자료만 사용. 실제 고객 데이터로 확장하지 않으며 NCUS 리소스를 NCUS 전용 처리로 표시하지 않음 |
| 보존·삭제 | **새 RG를 사용자 검토까지 보존; 삭제 미승인** | 운영 기록은 비공개로 보관. 보존은 과금 중단이 아니며 임의 삭제로 승인 범위를 넓히지 않음 |
| 사람의 운영 승인 | **미승인** | 실제 검토자의 판단·근거와 조직 승인 절차. AI가 자신의 검토를 human으로 등록하지 않음 |

`--confirm`, Azure Budget 알림, 로컬 mock 테스트, 과거 작성자 결과 중 어느 것도 범위 확대의 승인을 대신하지 않습니다. 통합 담당자도 아래 한도 밖의 호출·작업을 실행하지 않습니다. Feature 접근이 없거나 작업이 미완료이면 해당 기능의 별도 차단/대기 상태를 기록하고, 다른 제품을 실행한 결과로 성공을 대체하지 않습니다. 기존 공유 자원과 v1 저장소는 그대로 둡니다.

### 초기 읽기 전용 조사와 후속 실행의 구분

다음은 2026-09-30 초기 조사와 복구 판단의 기록입니다. 이후 실제 생성/모델/학습 결과와는 시점을 구별합니다.

| 항목 | 전달받은 관측 | 해석의 경계 |
|---|---|---|
| RG/첫 시도 관측 | 첫 거절 당시 하위 인벤토리 `0`건, ARM 조회 `404` | 당시 실패 기록. 이후 `Succeeded`한 같은 새 RG의 인프라와 섞거나 실패를 삭제하지 않음 |
| Search Basic · NCUS | `0.101 USD/시간`; 24시간 약 `2.424 USD`, 730시간 약 `73.73 USD` | 시간 단가에 따른 계획용 계산. 전체 실습 비용이나 무료 할당이 아니며 모델·평가·기타 비용과 구분 |
| 선택한 버전 | agent/SFT 기반: **`gpt-4.1-mini` / `2025-04-14` / Standard**. Judge `gpt-5.4-mini` / `2026-03-17`, planner `gpt-5.5` / `2026-04-24`, embedding `text-embedding-3-small` / `1` | 이 고정 설정으로 신규 배포와 LIVE 호출 확인. 처음 모델 선택을 바꾼 일은 튜닝 효과로 세지 않음 |
| 거부된 이전 후보 | gpt-4o-mini / 2024-07-18은 catalog `Deprecating`·fineTune·쿼터가 있어도 Azure validate에서 **2026-03-31 폐기**의 `ServiceModelDeprecated`로 거부됨 | 메타데이터·quota·로컬 검사와 제공자의 실제 생성 검증을 구분하는 첫 실패 교훈. 원본 실패를 삭제하거나 다른 성공으로 대체하지 않음 |
| 새 후보의 상태/쿼터 | catalog `Legacy`, fineTune 지원 표식. 정확한 기반 usageName **`OpenAI.Standard.gpt4.1-mini`**에 여유 5000, 별도 fine-tuned 여유 500 관측 | `gpt-4.1-mini` 모델 이름과 quota 식별자의 하이픈 차이를 임의로 합치지 않음. 여유는 무료 가격·생성·학습 지원 보장이 아님 |
| 배포 capacity 단위 | 관측한 capacity 메타데이터의 minimum/step은 `null` | ARM 정수 capacity 단위를 그대로 보존. 누락값을 근거 없이 보충하거나 모든 모델/SKU의 capacity를 일률적으로 TPM이라 표시하지 않음 |
| CLI / SDK / 브라우저 / Azure MCP | CLI·SDK·브라우저의 실제 사용자/테넌트 확인. Azure MCP의 관리 조회와 별개로 Foundry 데이터 평면 호출에서 다른 테넌트 오류가 관측됨 | 해당 MCP 호출로 변경하지 않음. 실제 Agent 내부 Search MCP의 프로젝트 MI는 별도이며 정상 호출을 검증 |

### 제품별 현재 확인 범위

공식 문서 지원과 실제 실행 근거를 함께 남기되, 서비스 완료와 품질 합격은 구분합니다.

| 기능 | 확인 범위와 경로 | 가이드에서 유지할 경계 |
|---|---|---|
| Prompt Optimizer | [공식 안내](https://learn.microsoft.com/azure/foundry/observability/how-to/prompt-optimizer)의 포털 경로로 실제 후보/변경 이유를 생성 | 후보 3건 재평가는 형식 실패. 영구 job ID가 없는 응답에 ID를 만들어 넣지 않음 |
| Agent Optimizer | [공식 prompt-agent wizard](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-optimize-prompt-agent)에서 실제 job succeeded, native baseline/candidate 각12건 수집 | 순위0.677→0.708과 실습 로컬 규칙의 중요 실패4→4를 함께 보고. MCP/Agent Service를 유지 |
| Frontier | 통합 담당자의 Learn 키워드·웹 검색에서 직접 일치하는 공식 API/지원 결과를 찾지 못한 범위는 **`NOT_VERIFIED`** | 검색에서 확인하지 못했다는 이유로 제품/API가 존재하지 않는다고 단정하지 않음. 실제 접근·지원 경로를 확인할 때까지 미확인으로 남기고 SFT로 성공을 대신하지 않음 |

### 승인된 제한 계획과 실행 구분

| 범위 | 승인된 상한·실행 구분 |
|---|---|
| 예산 | **금액 상한 없음.** 비공개 범위 요약의 `budget_cap: null`과 bootstrap의 완전한 승인 파일은 구분. 후자는 [승인 계약](admin-setup.md#approval)의 `budget_policy`·`budget_amount`·명시적 확인/근거 필드를 검증하며 승인 누락이나 무료를 뜻하지 않음 |
| 모델/Judge/planner 요청 | 합계 최대 `300`회; 재시도·교정·계획 호출도 무제한 반복하지 않음 |
| Prompt Optimizer | `1` job, 최대 `2` candidates; 서비스 접근/실행 결과는 별도 확인 |
| Agent Optimizer | `1` job, 최대 `2` candidates; Prompt Optimizer 성공으로 대신 완료 처리하지 않음 |
| SFT | `1` job, 기존 train `56` / validation `12`, `1` epoch; Frontier 성공으로 표시하지 않음 |
| fresh holdout | 동결 후 새로 생성한 `12`건; 기존 `minimum_test_rows: 20`과 별도 계약 |
| 작업 대기 | job당 최대 `60`분; 시간 초과를 성공으로 처리하거나 무제한 재제출하지 않음 |

12건 계획이 승인되어도 기존 20건 게이트를 자동 완화하지 않습니다. 새 fresh-holdout 계약의 목적·표본 한계·coverage·게이트를 결과를 보기 전에 별도로 고정하고 기존 test 20건과 구분합니다. 원래 게이트 그대로 12건만 제출하면 통과로 표시할 수 없습니다. 작업 상한에 도달하거나 승인 범위를 벗어나면 통합 담당자는 실행을 멈추고 상태를 기록합니다. 사용 승인과 실제 사람의 품질 검토·운영 출시는 여전히 다른 결정입니다.

이번 fresh12는 동결 후 생성/등록과 누출 검사를 마쳤지만 **교정 HOLD로 최종 추론 전 차단**됐습니다. SFT는 실제 학습·배포·paired 평가까지 끝났고 중요 실패가 남았습니다. 이 보류 결과를 아카이브 준비를 위해 성공으로 바꾸지 않습니다.

## 5. 출처·계보·라이선스

### 확인한 사실

- v1 고정 트리의 README(영문/국문), DEMO/입문/완결형/공통 준비/참고/강사 문서와 관련 CLI·평가·검색 코드, authored fixture 매니페스트 및 과거 LIVE fixture 메타데이터를 직접 읽었습니다.
- v1의 `examples/manifest.json`은 `source: authored-demo`와 프롬프트/질문/문맥/fixture 해시를 갖습니다. 반면 `advanced-rag/fixtures/recorded-v1.json`은 `source: recorded-live`, 캡처 시각 `2026-09-27T21:53:22.399772+00:00`, 원본 근거 해시와 모델 스냅샷을 갖습니다. **서로 다른 출처이며 이 기록의 실제 클라우드 실행을 이번 조사에서 재검증하지 않았습니다.**
- 원본 문서의 2026-09-28 실행 기록은 특정 이전 환경의 관측 설명입니다. 통합 대상의 [기존 검증 문서](verification.md)는 2026-09-29의 로컬/모의 검사와 읽기 전용 메타데이터 관찰을 구분하고 유료 실습 미실행을 명시합니다. 둘을 하나의 실행 이력으로 합치지 않습니다.
- **두 시작 커밋 모두 추적 트리에서 LICENSE/LICENCE, COPYING, NOTICE, COPYRIGHT 파일을 찾지 못했습니다.** 추적된 Markdown/Python/TOML/텍스트/JSON의 license·copyright·SPDX 표기도 확인되지 않았고 통합 대상 `pyproject.toml`에도 라이선스 선언이 없습니다. 이는 저장소 외부 권리 관계가 없다는 증명은 아닙니다.

### 통합 원칙

1. 공개 열람 가능성과 수정·재배포 라이선스를 구별합니다. 같은 계정 소유의 저장소처럼 보여도 명시적 사용 허가를 추정하지 않습니다.
2. 이번 문서는 기능·설계 판단을 독자적으로 작성하고 커밋 고정 링크로 영향 관계를 남깁니다. **v1 본문·코드·데이터·영상·그림을 복사하지 않습니다.**
3. 후속 단계에서 실제 내용을 가져와야 한다면 먼저 권리자의 허가/라이선스와 해당 파일의 권리 범위를 확인합니다. 허용될 때 원본 저장소·커밋·파일·변경 범위·필요한 고지와 라이선스 사본을 기록합니다. 저작자 표시만으로 허가 부족이 해결되지는 않습니다.
4. 외부 Microsoft 문서·저자 글은 개념/API 참고 출처입니다. 제품 그림·본문·영상 재배포 허가로 해석하지 않으며, 두 저장소에 이미 있는 1차 출처 표기를 제거하지 않습니다. 이 조사에서 외부 링크를 새로 조회하거나 최신 서비스 지원을 재검증하지 않았습니다.
5. 향후 ZIP/PDF 배포 시 자체 문서/코드의 배포 권한과 포함 의존성의 라이선스 의무도 따로 확인합니다. 이 비교는 법률 검토나 패키지 전체의 라이선스 인증이 아닙니다.

## 6. 후속 가이드 편집·빌드 계약

### 원문과 산출물

[웹 빌더](../scripts/build_guide.py)의 `DOCUMENTS`가 다음 매핑의 단일 원본입니다. 시작 커밋은 여섯 문서였으며 통합 브랜치의 출판 등록에는 migration·영문 문서가 추가되었습니다. 등록 상태와 실제 산출물 재생성 완료는 구분합니다.

| 편집할 원문 | 생성 파일 |
|---|---|
| `guide/handbook.md` | `index.html` |
| `guide/facilitator.md` | `facilitator.html` |
| `guide/admin-setup.md` | `admin.html` |
| `guide/sft-appendix.md` | `sft.html` |
| `guide/verification.md` | `verification.html` |
| `data/README.md` | `data-guide.html` |
| `guide/integration-migration.md` | `migration.html` |
| `README.en.md` | `english.html` |

기본 빌드는 위 여덟 페이지와 `print.html`을 함께 렌더링합니다. [인쇄 빌더](../scripts/build_print.py)의 `BOOK_ORDER`는 본문 → SFT → 강사 → 관리자 → 검증 → 데이터 → migration → 영문 순서입니다. **이 migration 문서는 통합 브랜치에서 매핑/인쇄 목차에 등록**되었지만, 소스 등록만으로 새 HTML/PDF가 자동 생성되지는 않습니다. 모든 등록 원문이 준비된 뒤 출판 담당자가 전체 빌드를 수행합니다.

- 생성 HTML을 직접 편집하지 않습니다. 원문 경로 기준 링크는 빌더가 루트 HTML로 재배치하고 등록된 문서 링크를 매핑합니다.
- `{#start}` 같은 기존 안정 앵커와 고유한 문서 ID를 유지합니다. 브라우저의 진행 상태는 문서 ID별이며 새 페이지 추가 시 중복시키지 않습니다.
- 참가자 안내는 기존 15개 장을 **예시 이해 → 환경 연결 → 기준선 평가 → IQ → Agent Optimizer → 최종 판정·종료**의 6단계로 묶었습니다. 리소스·모델·데이터·게이트와 기존 LIVE 증거는 변경하지 않습니다. Prompt Optimizer·별도 managed 평가는 강사 참고로, SFT·Frontier는 심화 부록으로 유지합니다. 확장된 단계에 이전 장의 읽음 표시가 잘못 적용되지 않도록 참가자 학습 기록만 별도 revision으로 저장하며 원래 브라우저 기록은 삭제하지 않습니다.
- Markdown은 신뢰된 로컬 저자 입력을 전제로 합니다. 모델/사용자 응답을 원시 HTML이나 실행 가능한 script로 삽입하지 않습니다. 코드 블록은 escape·복사 원문을 보존하고 템플릿 토큰처럼 다시 해석하지 않습니다.
- `print.html`은 script·복사 버튼 없는 정적 통합 문서입니다. 문서 앵커는 `book-...`로 구분하고, 패키지 파일 링크는 읽을 수 있는 파일 경로로 바꿉니다. localhost/file URI를 PDF에 남기지 않습니다.
- 시작 커밋의 `BUILD_DATE`는 `2026-09-29`였고 통합 브랜치는 `2026-09-30`을 사용합니다. 이 통합 제작일을 모든 공식 문서·서비스의 새 검증일로 해석하지 않습니다. 실제 확인 범위·관측 시각과 관련 검사를 함께 유지합니다.

### 검증 순서

다음은 **후속 문서 통합 담당자의 로컬 제작 순서**입니다. 새 기능 설명은 실제 parser/상태/파일과 맞춘 뒤 실행 블록으로 공개합니다.

```bash
python scripts/build_guide.py
python scripts/build_guide.py --check
python -m unittest discover -s tests -p 'test_documentation.py' -v
python -m unittest discover -s tests -p 'test_guide_build.py' -v
python -m unittest discover -s tests -p 'test_print_build.py' -v
```

[문서 검사](../tests/test_documentation.py)는 등록된 HTML의 로컬 링크·앵커와 `guide/*.md`의 `python -m lab`/`lab.sft` 명령 문법을 검사합니다. [웹 검사](../tests/test_guide_build.py)는 결정적 렌더링·링크·코드 보존·문서별 상태를, [인쇄 검사](../tests/test_print_build.py)는 목차·앵커·휴대 가능한 링크·정적 출력 계약을 검사합니다. **이 검사들은 실제 Azure 실행을 하지 않습니다.**

PDF는 두 빌더가 생성하지 않습니다. 통합 HTML 확인 뒤 승인된 로컬 인쇄 절차로 별도 제작하고 [PDF 검사](../scripts/verify_pdf.py)로 한국어 텍스트·필수 내용·빈 페이지·본문 넘침·로컬 머신 링크를 확인해야 합니다. 기존 PDF를 새 본문에 대한 검증 결과로 재사용하지 않습니다. 검사 도구의 의존성은 참가자 DEMO의 필수 조건이 아닙니다.

[패키징](../scripts/package_lab.py)은 원문 디렉터리를 포함하므로 이 migration 문서도 소스 ZIP 대상입니다. 통합 브랜치에는 migration/영문 HTML과 `infra`·`evidence` 소스 범위도 등록되었습니다. `.env`·가상환경·`artifacts/` 제외 계약을 유지하고, 배포용 `evidence`에는 승인된 비밀 없는 자료만 포함해야 합니다. 원격 계정 정보·실제 대화·LIVE 결과·인증 정보를 이름만 바꿔 그곳에 넣지 않습니다. 새 최상위 HTML을 배포하려면 페이지 등록·인쇄 포함 여부·문서 검사 페이지 목록·패키지 파일 목록을 함께 검토합니다.

### 후속 편집에 전달할 완료 조건

- 도입의 Contoso 오답 활동과 credential/network-free DEMO가 실제 경로에 연결되어야 합니다.
- Judge 전 최초 판단, AI 보조 검토, 실제 사람 판단, 운영 승인의 차이가 단계와 산출물에 드러나야 합니다.
- 업무 교정·실제 검색·대화·동결/새 holdout·재개는 각각 **무엇이 구현/로컬 검증/승인 대기/LIVE 미실행인지** 표시해야 합니다.
- 기존 100건과 제품·증거·안전 경계를 보존해야 하며, 작성 예시·mock·과거 기록을 새 LIVE 성공으로 채우지 않아야 합니다.

## 7. 이관 완료·아카이브 준비 체크리스트

**이 절은 아카이브 준비 지침이지 저장소의 archive/visibility 상태를 변경하는 승인이나 실행이 아닙니다.** 보관 원본의 접근·보관 상태와 현재 v1 저장소의 PRIVATE 상태를 변경하지 않습니다.

| 검토 | 완료로 볼 조건 | 하지 않을 일 |
|---|---|---|
| 자기완결성 | 이 패키지의 README/코드/데이터/문서만으로 DEMO·준비·주 경로를 이해하고 실행 가능 | v1 실행 파일·설정·README 설치를 필수 단계로 요구 |
| 출처/권리 | 고정 커밋·파일 영향 관계와 라이선스 미확인 상태 보존 | 공개 저장소이므로 자유 복사 가능하다고 간주 |
| 시나리오/데이터 | Contoso, 원본 100건·원래 분할·응답 스키마 보존 | 다른 도메인의 사례·정답·과거 LIVE 점수를 섞음 |
| 소스/출판 일치 | 원문과 여덟 HTML/통합 인쇄본/PDF를 같은 변경에서 재생성·검사 | 예전 PDF/브라우저 성공 기록으로 새 원문 검증을 대체 |
| 비공개 경계 | 실제 계정·환경·승인 원문/JSON·실행 근거를 출판 묶음에서 제외 | 사용자 이메일/구독 ID/기존 리소스 기본값을 남김 |
| 실행 계보 | authored/mock/metadata/LIVE/품질/사람 승인 상태를 별도 보존 | 계획·파일 생성·RG 생성만으로 기능 전체 완료 선언 |
| 저장소 상태 | 권리·배포·보존 검토 후 별도 소유자 결정에 필요한 근거만 준비 | v1 수정/커밋/삭제, 가시성 전환 또는 archive 실행 |
| Azure 보존 | 신규 RG/리소스·원장·다음 비용 확인 책임을 유지 | 이관 또는 수업 종료를 이유로 삭제 실행 |

미확인 라이선스, 기능 접근, 실제 실행 또는 사람 검토가 남아 있으면 그 상태를 남깁니다. 저장소를 보관할 준비가 되었다는 판단과 실제 보관/공개 변경은 별도의 권한 있는 결정입니다.

### 남은 의존성과 승인

| 항목 | 현재 경계 |
|---|---|
| v1 실행 의존성 | 없음. 독립 ZIP을 새 폴더에 풀어 Azure SDK·네트워크·하위 프로세스 없이 DEMO를 실행하고 원본 100건 검사를 통과함 |
| 출처 참조 | 이 문서의 v1 커밋/파일 링크만 남음. 링크를 읽지 않아도 설치·DEMO·LIVE 명령을 실행할 수 있음 |
| LIVE 외부 의존성 | Azure 로그인·서비스 지원·쿼터·역할·처리 위치/비용 승인. Python 의존성은 이 패키지의 잠금 파일 사용 |
| 실제 실행 증거 | 신규 환경의 성공·실패·접근 차단 기록을 [검증 기록](verification.md)과 함께 확인. 과거 v1 결과를 승계하지 않음 |
| 아카이브·공유 | 참고 원본은 현재 v0.9에서 PRIVATE·Archived 상태. 이번 이름 변경에서 원본의 보관/접근 상태나 두 저장소의 권한은 변경하지 않음 |

### 전환 안내 문안 — 소유자 검토용 초안 {#transition-notice}

다음 문안은 **v1에 게시하거나 아카이브를 실행한 기록이 아닙니다.** 전환일·접근 방법을 소유자가 확정한 뒤 별도로 사용합니다.

> Foundry 평가 실습의 대표 유지보수 저장소는 **foundry-evaluation-labs-v1**이며, 가이드 표기도 **v1**입니다. 전체 패키지에서 `index.html`을 열어 시작해 주세요.
>
> v1 가이드는 Contoso 고객지원 시나리오에서 오답 발견 → 무료 작성형 DEMO → 실습 환경 연결 → 실제 평가·검색·개선 → 동결·새 보류 평가 → 사람 검토·운영 관측을 하나의 경로로 안내합니다. 코드·데이터·설치·재개에 참고 원본의 실행 파일은 필요하지 않습니다.
>
> 참고 원본의 과거 자료는 **foundry-evaluation-labs-v0.9**에서 보관되어 있습니다. 과거 점수·실행 화면은 현재 가이드의 신규 LIVE 결과가 아닙니다.
>
> 현재 저장소는 비공개입니다. 승인된 저장소 접근 또는 배포 패키지를 사용하고, Azure 실행·비용·데이터 처리 승인은 각 실습 환경에서 확인해 주세요. 품질 점수와 사람의 운영 승인은 별개입니다.

[v1-root]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/tree/93bc07e31373c4cfc278a2dc3757785946404cf2
[v1-readme]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/README.ko.md
[v1-offline]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/docs/offline.md
[v1-intro]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/docs/intro-lab.md
[v1-setup]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/docs/setup.md
[v1-reference]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/docs/reference.md
[v1-complete]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/docs/complete-lab.md
[v1-facilitator]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/docs/facilitator.md
[v1-cleanup]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/docs/cleanup.md
[v1-cli]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/lab.py
[v1-client]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/foundry_client.py
[v1-evaluation]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/evaluation.py
[v1-advanced-cli]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/advanced_lab.py
[v1-advanced-evaluation]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/advanced_evaluation.py
[v1-retrieval]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/advanced_retrieval.py
[v1-policy-rubric]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/advanced-rag/policy-task-success.txt
[v1-followups]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/advanced-rag/dev-followups.json
[v1-acceptance]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/advanced-rag/acceptance.json
[v1-demo-manifest]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/examples/manifest.json
[v1-recorded]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/advanced-rag/fixtures/recorded-v1.json
[v1-media]: https://github.com/junwoojeong100/foundry-evaluation-labs-v0.9/blob/93bc07e31373c4cfc278a2dc3757785946404cf2/docs/media/complete-rag/README.md
